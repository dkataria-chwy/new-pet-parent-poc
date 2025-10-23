# Create Personalized Welcome Message

Generate a warm, conversational spoken welcome message for this pet parent's monthly selections.

---

## Pet Profile
{{pet_profile_json}}

**Current Month:** Month {{month_number}}

---

## This Month's Subscription Plan

The complete plan output below shows what's being recommended this month - use this to accurately reference the 2-3 broad themes you mention:

{{subscription_plan_json}}

---

## Your Task

Create a 100-120 word spoken welcome message following all guidelines from your system prompt. 

Focus on:
- The pet's life stage and what's happening developmentally
- Breed-specific fun facts and personality traits
- Developmental milestones pet parents are typically navigating at this age (socialization windows, fear periods, teething, training readiness)
- **Actionable health guidance** - If the pet is in a relevant age range, suggest checking with their vet:
  - 6-16 weeks: "Check with your vet about vaccine schedules" or "Chat with your vet about his vaccine series if you haven't already"
  - 6+ months: "Worth discussing spay/neuter timing with your vet"
  - 7+ years: "Good time for a senior wellness checkup with your vet"
  - Use friendly guidance language: "check with," "chat with," "worth discussing" - not medical directives
- What pet parents are experiencing day-to-day
- Environmental factors (weather, living situation)

Products are detailed below, so minimize product mentions - just briefly connect the plan to their needs if at all (1 sentence max).

Return ONLY the spoken text, no formatting or metadata.

