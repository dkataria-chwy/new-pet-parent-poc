# slot_viewer_gradio.py
# Viewer for planned/enriched slots + Candidate products per slot
# Now includes a "Final Bundle" tab showing selected items + reasoning.

from __future__ import annotations
from typing import List, Dict, Any, Tuple, Optional

import gradio as gr

# your modules
from nppState import nppState, SlotSpec, CandidateProduct  # models
from slot_planner_agent import plan_slots_agent            # imported but not used directly here
from enrich_queries_agent import enrich_queries_agent      # imported but not used directly here
from slot_candidates_agent import slot_candidates_agent    # planner→enricher→candidates happens in build_graph
from candidate_eval_agent import candidate_eval_agent      # fills CandidateProduct.reasoning + rerank scores
from bundle_creator_agent import bundle_creator_agent      # builds the final ProposedBundle on state
from load_pet_state import load_pet_state
from npp_agents_orchestrator import build_graph

# ---------- small helpers for the pet card ----------
def _life_stage(species: str, age_months: int) -> str:
    s = (species or "").lower()
    if s == "dog":
        if age_months < 12: return "puppy"
        if age_months >= 96: return "senior"
        return "adult"
    # cat
    if age_months < 12: return "kitten"
    if age_months >= 120: return "senior"
    return "adult"

def _size_class(species: str, weight_lb: float) -> str:
    s = (species or "").lower()
    w = float(weight_lb or 0)
    if s == "dog":
        if w < 10: return "xs"
        if w < 20: return "s"
        if w < 50: return "m"
        if w < 90: return "l"
        return "xl"
    # cats
    if w < 7: return "s"
    if w < 15: return "m"
    return "l"

def _format_pet_markdown(pet) -> str:
    species = getattr(pet, "species", "") or "—"
    breed = getattr(pet, "breed", "") or "—"
    gender = getattr(pet, "gender", "") or "—"
    age_m = int(getattr(pet, "age_months", 0) or 0)
    weight = getattr(pet, "weight_lb", None)
    weight_s = f"{weight:.1f} lb" if isinstance(weight, (int, float)) else "—"
    zipc = getattr(pet, "location_zip", "") or "—"
    habits = getattr(pet, "habits", []) or []
    conditions = getattr(pet, "recent_conditions", []) or []
    geo = getattr(pet, "geo_eventcondition", []) or []

    years, months = divmod(max(age_m, 0), 12)
    stage = _life_stage(species, age_m)
    sizec = _size_class(species, weight or 0)

    habits_s = ", ".join(habits) if habits else "—"
    cond_s = ", ".join(conditions) if conditions else "—"
    geo_s = ", ".join(geo) if geo else "—"

    return (
        "### 🐾 Pet Profile\n\n"
        f"**Species:** {species.title()} &nbsp;|&nbsp; **Breed:** {breed} &nbsp;|&nbsp; **Gender:** {gender}\n\n"
        f"**Age:** {years}y {months}m ({stage}) &nbsp;|&nbsp; **Weight:** {weight_s} (size: {sizec})\n\n"
        f"**ZIP:** {zipc}\n\n"
        f"**Habits:** {habits_s}\n\n"
        f"**Recent conditions:** {cond_s}\n\n"
        f"**Geo events:** {geo_s}\n"
    )

# ---------- slots & candidates extraction ----------
def _extract_slots(out) -> List[Dict[str, Any]]:
    if hasattr(out, "slots"):
        slots_obj = out.slots
    elif isinstance(out, dict) and "slots" in out:
        slots_obj = out["slots"]
    else:
        raise ValueError("Output state does not contain 'slots'")

    norm = []
    for s in slots_obj:
        if hasattr(s, "model_dump"):
            norm.append(s.model_dump())
        elif isinstance(s, dict):
            norm.append(s)
        else:
            norm.append({k: getattr(s, k) for k in dir(s) if not k.startswith("_")})
    return norm

def _slot_label(s: Dict[str, Any], idx: int) -> str:
    return f"{idx:02d} | {s.get('slot_id','?')} | {s.get('name','')}"

_CAND_HEADERS = [
    "#", "sku", "title", "price", "brand", "rating", "reviews",
    "score_fused", "score_vector", "score_rerank", "score_rerank2",
    "category", "reasoning_preview"
]

def _normalize_candidates(slot: Dict[str, Any]) -> Tuple[List[List[Any]], List[str], List[Dict[str, Any]]]:
    raw = slot.get("candidates", []) or []
    rows: List[List[Any]] = []
    labels: List[str] = []
    norm_items: List[Dict[str, Any]] = []

    for i, c in enumerate(raw):
        if hasattr(c, "model_dump"):
            d = c.model_dump()
        elif isinstance(c, dict):
            d = c
        else:
            d = {k: getattr(c, k) for k in dir(c) if not k.startswith("_")}
        norm_items.append(d)

        title = (d.get("title") or "")[:64]
        price = d.get("price")
        sku = d.get("sku")
        fused = d.get("score_fused")
        rerank = d.get("score_rerank")
        label_score = rerank if rerank is not None else fused
        lab = f"{i:02d} | {sku} | {title} | ${price if price is not None else '—'} | score {label_score if label_score is not None else '—'}"
        labels.append(lab)

        reason_prev = (d.get("reasoning") or "")
        if reason_prev:
            reason_prev = (reason_prev.replace("\n", " ").strip())[:120]

        rows.append([
            i,
            sku,
            d.get("title"),
            d.get("price"),
            d.get("brand"),
            d.get("rating"),
            d.get("review_count"),
            d.get("score_fused"),
            d.get("score_vector"),
            d.get("score_rerank"),
            d.get("score_rerank2"),
            d.get("category"),
            reason_prev or "—",
        ])
    return rows, labels, norm_items

# ---------- bundle extraction ----------
BUNDLE_HEADERS = [
    "#", "slot_id", "slot_name", "sku", "title", "price", "score", "score_type", "reasoning_preview"
]
REMOVED_HEADERS = [
    "#", "slot_id", "slot_name", "reason", "best_candidate_sku", "best_title", "best_score", "best_score_type"
]

def _normalize_bundle(state: nppState):
    pb = getattr(state, "proposed_bundle", None)
    items_rows: List[List[Any]] = []
    items_labels: List[str] = []
    items_norm: List[Dict[str, Any]] = []
    removed_rows: List[List[Any]] = []
    subtotal_str = "Subtotal: —"

    if pb:
        # Items
        for i, it in enumerate(pb.items or []):
            d = it.model_dump() if hasattr(it, "model_dump") else dict(it)
            items_norm.append(d)
            rp = (d.get("reasoning") or "")
            rp = (rp.replace("\n", " ").strip())[:120] if rp else "—"
            lab = f"{i:02d} | {d.get('slot_id')} | {d.get('sku')} | { (d.get('title') or '')[:48] } | ${d.get('price','—')} | score {d.get('score','—')}"
            items_labels.append(lab)
            items_rows.append([
                i,
                d.get("slot_id"),
                d.get("slot_name"),
                d.get("sku"),
                d.get("title"),
                d.get("price"),
                d.get("score"),
                d.get("score_type"),
                rp
            ])
        # Removed
        for i, rs in enumerate(pb.removed_slots or []):
            d = rs.model_dump() if hasattr(rs, "model_dump") else dict(rs)
            bc = d.get("best_candidate") or {}
            removed_rows.append([
                i,
                d.get("slot_id"),
                d.get("slot_name"),
                d.get("reason"),
                bc.get("sku"),
                bc.get("title"),
                bc.get("score"),
                bc.get("score_type"),
            ])
        # Subtotal
        currency = getattr(pb, "currency", "USD")
        subtotal = getattr(pb, "subtotal", None)
        if subtotal is not None:
            subtotal_str = f"Subtotal: ${subtotal:,.2f} {currency}"

    return items_rows, items_labels, items_norm, removed_rows, subtotal_str

# ---------- pipeline ----------
def run_pipeline(example_id: int, do_eval: bool):
    """
    Returns UI-ready tuples for slots and final bundle.
    """
    try:
        state = load_pet_state(int(example_id))
        app = build_graph()           # plan → enrich → candidates (per orchestrator)
        out = app.invoke(state)

        slots = _extract_slots(out)
        pet_md = _format_pet_markdown(state.pet)

        # Prepare initial slot/candidate views
        labels = [_slot_label(s, i) for i, s in enumerate(slots)]
        sel_idx = 0 if labels else 0
        sel_label = labels[sel_idx] if labels else None
        selected_slot = slots[sel_idx] if slots else {}

        # Prepare bundle views
        b_rows, b_labels, b_items, r_rows, subtotal_str = _normalize_bundle(out)
        b_sel_idx = 0 if b_labels else 0
        b_sel_item = b_items[b_sel_idx] if b_items else {}
        b_reason = b_sel_item.get("reasoning") or ""

        # Prepare candidate table for selected slot
        rows, cand_labels, norm_items = _normalize_candidates(selected_slot)
        sel_c_idx = 0 if cand_labels else 0
        sel_cand = norm_items[sel_c_idx] if norm_items else {}
        sel_reason = sel_cand.get("reasoning") or ""

        status_text = f"OK • {len(slots)} slots • {len(b_rows)} bundle items • {len(r_rows)} removed"
        return (
            # Pet + status
            pet_md, status_text,
            # Slots tab (top)
            len(slots), gr.update(choices=labels, value=sel_label),
            # Hidden slots state
            slots, labels, sel_idx,
            # Slot details + candidates
            selected_slot, len(rows),
            gr.update(choices=cand_labels, value=(cand_labels[sel_c_idx] if cand_labels else None)),
            rows, sel_c_idx, sel_cand, sel_reason,
            # Bundle tab
            subtotal_str, len(b_rows),
            gr.update(choices=b_labels, value=(b_labels[b_sel_idx] if b_labels else None)),
            b_rows, b_sel_idx, b_sel_item, b_reason,
            r_rows
        )
    except Exception as e:
        return (
            "### 🐾 Pet Profile\n\n_(unavailable)_", f"Error: {e}",
            0, gr.update(choices=[], value=None),
            [], [], 0,
            {}, 0, gr.update(choices=[], value=None), [], 0, {}, "",
            "Subtotal: —", 0, gr.update(choices=[], value=None), [], 0, {}, "", []
        )

def on_select(label: str, slots: List[Dict[str, Any]]):
    if not slots or not label:
        return 0, {}, 0, gr.update(choices=[], value=None), [], {}, ""
    try:
        idx = int(label.split("|", 1)[0])
    except Exception:
        idx = 0
    idx = max(0, min(idx, len(slots) - 1))
    slot = slots[idx]
    rows, cand_labels, norm_items = _normalize_candidates(slot)
    sel_c_idx = 0 if cand_labels else 0
    sel_cand = norm_items[sel_c_idx] if norm_items else {}
    sel_reason = sel_cand.get("reasoning") or ""
    return idx, slot, len(rows), gr.update(choices=cand_labels, value=(cand_labels[sel_c_idx] if cand_labels else None)), rows, sel_cand, sel_reason

def on_cand_select(cand_label: str, slots: List[Dict[str, Any]], slot_idx: int):
    if not slots or slot_idx is None or slot_idx < 0 or slot_idx >= len(slots):
        return 0, {}, ""
    slot = slots[slot_idx]
    _, cand_labels, norm_items = _normalize_candidates(slot)
    try:
        c_idx = int(cand_label.split("|", 1)[0])
    except Exception:
        c_idx = 0
    c_idx = max(0, min(c_idx, len(norm_items) - 1))
    sel = (norm_items[c_idx] if norm_items else {})
    return c_idx, sel, sel.get("reasoning") or ""

def cand_nav_prev(cur_idx: int, slots: List[Dict[str, Any]], slot_idx: int):
    slot = slots[slot_idx] if slots and 0 <= slot_idx < len(slots) else {}
    rows, cand_labels, norm_items = _normalize_candidates(slot)
    if not cand_labels:
        return 0, gr.update(value=None), {}, ""
    new_idx = (cur_idx - 1) % len(cand_labels)
    sel = (norm_items[new_idx] if norm_items else {})
    return new_idx, gr.update(value=cand_labels[new_idx]), sel, sel.get("reasoning") or ""

def cand_nav_next(cur_idx: int, slots: List[Dict[str, Any]], slot_idx: int):
    slot = slots[slot_idx] if slots and 0 <= slot_idx < len(slots) else {}
    rows, cand_labels, norm_items = _normalize_candidates(slot)
    if not cand_labels:
        return 0, gr.update(value=None), {}, ""
    new_idx = (cur_idx + 1) % len(cand_labels)
    sel = (norm_items[new_idx] if norm_items else {})
    return new_idx, gr.update(value=cand_labels[new_idx]), sel, sel.get("reasoning") or ""

def nav_prev(cur_idx: int, slots: List[Dict[str, Any]], labels: List[str]):
    if not slots:
        return 0, gr.update(value=None), {}, 0, gr.update(choices=[], value=None), [], {}, ""
    new_idx = (cur_idx - 1) % len(slots)
    slot = slots[new_idx]
    rows, cand_labels, norm_items = _normalize_candidates(slot)
    sel_c_idx = 0 if cand_labels else 0
    sel = norm_items[sel_c_idx] if norm_items else {}
    return (
        new_idx,
        gr.update(value=labels[new_idx]),
        slot,
        len(rows),
        gr.update(choices=cand_labels, value=(cand_labels[sel_c_idx] if cand_labels else None)),
        rows,
        sel,
        sel.get("reasoning") or "",
    )

def nav_next(cur_idx: int, slots: List[Dict[str, Any]], labels: List[str]):
    if not slots:
        return 0, gr.update(value=None), {}, 0, gr.update(choices=[], value=None), [], {}, ""
    new_idx = (cur_idx + 1) % len(slots)
    slot = slots[new_idx]
    rows, cand_labels, norm_items = _normalize_candidates(slot)
    sel_c_idx = 0 if cand_labels else 0
    sel = norm_items[sel_c_idx] if norm_items else {}
    return (
        new_idx,
        gr.update(value=labels[new_idx]),
        slot,
        len(rows),
        gr.update(choices=cand_labels, value=(cand_labels[sel_c_idx] if cand_labels else None)),
        rows,
        sel,
        sel.get("reasoning") or "",
    )

# ----- bundle tab handlers -----
def on_bundle_select(label: str, bundle_items: List[Dict[str, Any]]):
    if not bundle_items or not label:
        return 0, {}, ""
    try:
        idx = int(label.split("|", 1)[0])
    except Exception:
        idx = 0
    idx = max(0, min(idx, len(bundle_items) - 1))
    item = bundle_items[idx]
    return idx, item, item.get("reasoning") or ""

def bundle_nav_prev(cur_idx: int, bundle_items: List[Dict[str, Any]], bundle_labels: List[str]):
    if not bundle_items:
        return 0, gr.update(value=None), {}, ""
    new_idx = (cur_idx - 1) % len(bundle_items)
    return new_idx, gr.update(value=bundle_labels[new_idx] if bundle_labels else None), bundle_items[new_idx], bundle_items[new_idx].get("reasoning") or ""

def bundle_nav_next(cur_idx: int, bundle_items: List[Dict[str, Any]], bundle_labels: List[str]):
    if not bundle_items:
        return 0, gr.update(value=None), {}, ""
    new_idx = (cur_idx + 1) % len(bundle_items)
    return new_idx, gr.update(value=bundle_labels[new_idx] if bundle_labels else None), bundle_items[new_idx], bundle_items[new_idx].get("reasoning") or ""

# ---------- UI ----------
with gr.Blocks() as demo:
    gr.Markdown("## 🐶 New Pet Parent — Slots, Candidates & Final Bundle")

    with gr.Row():
        example_id = gr.Number(value=1, precision=0, label="Demo Pet State ID")
        run_eval = gr.Checkbox(value=True, label="Run LLM reranker + reasoning (recommended)")
        run_btn = gr.Button("Run Planner → Enricher → Candidates → Bundle", variant="primary")

    with gr.Row():
        pet_card = gr.Markdown("### 🐾 Pet Profile\n\n_(run to load pet)_")
        status = gr.Markdown("Status: _idle_")

    with gr.Tabs():
        # --------- TAB 1: Slots & Candidates ----------
        with gr.Tab("Slots & Candidates"):
            with gr.Row():
                slot_count = gr.Number(value=0, label="# Slots", interactive=False)
                slot_selector = gr.Dropdown(choices=[], label="Select a Slot", interactive=True)
            with gr.Row():
                prev_btn = gr.Button("◀ Prev Slot")
                next_btn = gr.Button("Next Slot ▶")
            slot_json = gr.JSON(label="Slot Details (JSON)")

            gr.Markdown("### 🎯 Candidates in Selected Slot")
            with gr.Row():
                cand_count = gr.Number(value=0, label="# Candidates", interactive=False)
                cand_selector = gr.Dropdown(choices=[], label="Select a Candidate", interactive=True)
            with gr.Row():
                cand_prev_btn = gr.Button("◀ Prev Candidate")
                cand_next_btn = gr.Button("Next Candidate ▶")
            cand_table = gr.Dataframe(headers=_CAND_HEADERS, row_count=5, wrap=True, interactive=False, label="Candidates (table)")
            cand_json = gr.JSON(label="Selected Candidate (JSON)")
            cand_reasoning = gr.Textbox(
                label="Reasoning for Selected Candidate",
                lines=6,
                interactive=False,
                show_copy_button=True,
                placeholder="Enable 'Run LLM reranker + reasoning' to populate this."
            )

        # --------- TAB 2: Final Bundle ----------
        with gr.Tab("Final Bundle"):
            subtotal_md = gr.Markdown("Subtotal: —")
            with gr.Row():
                bundle_count = gr.Number(value=0, label="# Items in Bundle", interactive=False)
                bundle_selector = gr.Dropdown(choices=[], label="Select a Bundle Item", interactive=True)
            with gr.Row():
                bundle_prev_btn = gr.Button("◀ Prev Bundle Item")
                bundle_next_btn = gr.Button("Next Bundle Item ▶")
            bundle_table = gr.Dataframe(headers=BUNDLE_HEADERS, row_count=5, wrap=True, interactive=False, label="Bundle Items (table)")
            bundle_json = gr.JSON(label="Selected Bundle Item (JSON)")
            bundle_reasoning = gr.Textbox(
                label="Reasoning for Selected Bundle Item",
                lines=6,
                interactive=False,
                show_copy_button=True,
                placeholder="If empty, run with 'LLM reranker + reasoning' enabled."
            )

            gr.Markdown("### 🚫 Excluded Slots")
            removed_table = gr.Dataframe(headers=REMOVED_HEADERS, row_count=4, wrap=True, interactive=False, label="Removed Slots")

    # Hidden states
    st_slots = gr.State([])          # list of slot dicts
    st_labels = gr.State([])         # slot labels
    st_index = gr.State(0)           # current slot index
    st_cand_index = gr.State(0)      # current candidate index within slot
    st_bundle_items = gr.State([])   # list of bundle item dicts
    st_bundle_labels = gr.State([])  # labels for bundle items
    st_bundle_index = gr.State(0)    # current bundle item index

    # Single-step run → update both tabs
    def run_and_update(example_id, do_eval):
        (
            pet_md, status_text,
            # slots top
            slots_cnt, slot_sel, slots, labels, idx,
            # slot details + candidates
            slot_json_val, cand_cnt, cand_sel, cand_rows, cidx, cand_json_val, cand_reason,
            # bundle tab
            subtotal_str, b_cnt, b_sel, b_rows, b_idx, b_json_val, b_reason, r_rows
        ) = run_pipeline(example_id, do_eval)

        return (
            # pet + status
            pet_md, status_text,
            # slots
            slots_cnt, slot_sel, slots, labels, idx,
            slot_json_val, cand_cnt, cand_sel, cand_rows, cidx, cand_json_val, cand_reason,
            # bundle
            subtotal_str, b_cnt, b_sel, b_rows, b_json_val, b_reason, r_rows,
            # hidden bundle states
            b_rows,  # not used directly but keeps parity
            b_idx,
        )

    run_btn.click(
        fn=run_and_update,
        inputs=[example_id, run_eval],
        outputs=[
            # pet + status
            pet_card, status,
            # slots
            slot_count, slot_selector, st_slots, st_labels, st_index,
            slot_json, cand_count, cand_selector, cand_table, st_cand_index, cand_json, cand_reasoning,
            # bundle
            subtotal_md, bundle_count, bundle_selector, bundle_table, bundle_json, bundle_reasoning, removed_table,
            # hidden (bundle)
            st_bundle_items, st_bundle_index,
        ],
    )

    # Slots tab handlers
    slot_selector.change(
        fn=on_select,
        inputs=[slot_selector, st_slots],
        outputs=[st_index, slot_json, cand_count, cand_selector, cand_table, cand_json, cand_reasoning],
    )
    prev_btn.click(
        fn=nav_prev,
        inputs=[st_index, st_slots, st_labels],
        outputs=[st_index, slot_selector, slot_json, cand_count, cand_selector, cand_table, cand_json, cand_reasoning],
    )
    next_btn.click(
        fn=nav_next,
        inputs=[st_index, st_slots, st_labels],
        outputs=[st_index, slot_selector, slot_json, cand_count, cand_selector, cand_table, cand_json, cand_reasoning],
    )
    cand_selector.change(
        fn=on_cand_select,
        inputs=[cand_selector, st_slots, st_index],
        outputs=[st_cand_index, cand_json, cand_reasoning],
    )
    cand_prev_btn.click(
        fn=cand_nav_prev,
        inputs=[st_cand_index, st_slots, st_index],
        outputs=[st_cand_index, cand_selector, cand_json, cand_reasoning],
    )
    cand_next_btn.click(
        fn=cand_nav_next,
        inputs=[st_cand_index, st_slots, st_index],
        outputs=[st_cand_index, cand_selector, cand_json, cand_reasoning],
    )

    # Bundle tab handlers
    bundle_selector.change(
        fn=on_bundle_select,
        inputs=[bundle_selector, st_bundle_items],
        outputs=[st_bundle_index, bundle_json, bundle_reasoning],
    )
    bundle_prev_btn.click(
        fn=bundle_nav_prev,
        inputs=[st_bundle_index, st_bundle_items, st_bundle_labels],
        outputs=[st_bundle_index, bundle_selector, bundle_json, bundle_reasoning],
    )
    bundle_next_btn.click(
        fn=bundle_nav_next,
        inputs=[st_bundle_index, st_bundle_items, st_bundle_labels],
        outputs=[st_bundle_index, bundle_selector, bundle_json, bundle_reasoning],
    )

if __name__ == "__main__":
    demo.launch()
