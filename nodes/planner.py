import json
import os
import re

from langchain_core.messages import AIMessage

SKILLS_CONTENT = ""
if os.path.exists("skills/skill.md"):
    with open("skills/skill.md", "r", encoding="utf-8") as file:
        SKILLS_CONTENT = file.read()


def extract_skill_sop(skill_name):
    """Extract a specific skill SOP section from skills/skill.md."""
    if not skill_name or not SKILLS_CONTENT:
        return ""

    pattern = rf"## \d+\. {skill_name}.*?(?=## \d+\.|$)"
    match = re.search(pattern, SKILLS_CONTENT, re.DOTALL)
    return match.group(0) if match else ""


async def planner_node(state, model):
    """Decompose a task into 3-5 executable steps."""
    query = state["messages"][-1].content
    skill_route = state.get("skill_route")
    skill_sop = extract_skill_sop(skill_route) if skill_route else ""
    skill_section = f"Reference SOP:\n{skill_sop}\n\n" if skill_sop else ""

    planning_prompt = f"""Break the user request into 3 to 5 concrete executable steps.

{skill_section}User request: {query}

Return JSON in this format:
{{
  "steps": [
    {{"step": 1, "action": "First action"}},
    {{"step": 2, "action": "Second action"}}
  ]
}}

Return only valid JSON.
"""

    response = await model.ainvoke([{"role": "user", "content": planning_prompt}])
    plan_data = json.loads(response.content)
    step_count = len(plan_data["steps"])
    return {
        "task_plan": plan_data["steps"],
        "messages": [AIMessage(content=f"Created a {step_count}-step plan and ready to start.")],
    }
