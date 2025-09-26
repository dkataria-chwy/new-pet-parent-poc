from langgraph.graph import StateGraph, END
from nppState import nppState
from enrich_queries_agent import enrich_queries_agent
import json

from slot_planner_agent import plan_slots_agent
from enrich_queries_agent import enrich_queries_agent
from slot_candidates_agent import slot_candidates_agent
from candidate_eval_agent import candidate_eval_agent
from bundle_creator_agent import bundle_creator_agent
from load_pet_state import load_pet_state

def build_graph():
    graph = StateGraph(nppState)
    graph.add_node("plan_slots_agent", plan_slots_agent)
    graph.add_node("enrich_queries_agent", enrich_queries_agent)
    graph.add_node("slot_candidates_agent", slot_candidates_agent)
    graph.add_node("candidate_eval_agent", candidate_eval_agent)
    graph.add_node("bundle_creator_agent", bundle_creator_agent)

    graph.set_entry_point("plan_slots_agent")
    graph.add_edge("plan_slots_agent", "enrich_queries_agent")
    graph.add_edge("enrich_queries_agent", "slot_candidates_agent")
    graph.add_edge("slot_candidates_agent", "candidate_eval_agent")
    graph.add_edge("candidate_eval_agent", "bundle_creator_agent")
    graph.add_edge("bundle_creator_agent", END)
    return graph.compile()

if __name__ == "__main__":

    if load_pet_state is None:
        raise SystemExit("load_pet_state.py not available in path for demo run.")

    # Load example state and run the planner
    state = load_pet_state(1)
    app = build_graph()
    out: nppState = app.invoke(state)  # type: ignore[assignment]

    
    print(json.dumps([s.model_dump() for s in out["slots"]], indent=2))
