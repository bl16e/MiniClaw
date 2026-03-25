import uuid

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Send

from config import llm


async def subagent_coordinator_node(state):
    """Extract subtasks and store them in state."""
    content = state["messages"][-1].content
    subtasks = extract_subtasks(content)
    tasks = [{"task": task, "task_id": str(uuid.uuid4())[:8]} for task in subtasks]
    print("subtasks:", tasks)
    return {"subagent_tasks": tasks}


async def subagent_executor_node(state, app):
    """Execute a single subtask with subagent depth protection."""
    task = state["task"]
    task_id = state["task_id"]
    subagent_state = {"messages": [HumanMessage(content=task)], "subagent_depth": 1}
    config = {"configurable": {"thread_id": f"subagent_{task_id}"}}

    while True:
        result = await app.ainvoke(subagent_state, config=config)
        snapshot = await app.aget_state(config)
        if not snapshot.next:
            break
        subagent_state = None

    return {
        "subagent_results": [
            {"task_id": task_id, "result": result["messages"][-1].content}
        ]
    }


def continue_to_subagents(state):
    """Generate Send objects for each extracted subtask."""
    tasks = state.get("subagent_tasks", [])
    return [
        Send("subagent_executor", {"task": task["task"], "task_id": task["task_id"]})
        for task in tasks
    ]


async def subagent_aggregator_node(state):
    """Combine subagent results back into a single assistant message."""
    subagent_results = state.get("subagent_results", [])
    print("subagent_results:", subagent_results)
    combined = "\n\n".join(
        [
            f"Subtask {index + 1} (ID: {result['task_id']}):\n{result['result']}"
            for index, result in enumerate(subagent_results)
        ]
    )
    return {"messages": [AIMessage(content=f"Parallel execution completed:\n{combined}")]}


def extract_subtasks(content: str) -> list:
    """Extract objects to analyze in parallel."""
    prompt = f"""Analyze this task and extract the objects that need to be processed independently.

Task: {content}

Rules:
- If comparing or analyzing multiple items, return one subtask per item.
- Each subtask should be phrased like "Analyze [item]" or "Summarize [item]".
- Do not split by analysis dimensions.
- Return only the subtasks, one per line, with no numbering.

Examples:
Task: "Compare paper A and paper B"
Analyze paper A
Analyze paper B

Task: "Analyze the pros and cons of products X, Y, and Z"
Analyze product X
Analyze product Y
Analyze product Z
"""

    response = llm.invoke([HumanMessage(content=prompt)])
    subtasks = [
        line.strip()
        for line in response.content.strip().split("\n")
        if line.strip() and len(line.strip()) > 10
    ]
    return subtasks if subtasks else [content]
