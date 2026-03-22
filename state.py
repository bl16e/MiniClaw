from typing import Annotated, Sequence, TypedDict, List, Dict, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


def add_subagent_results(existing, new):
    """Accumulate subagent results"""
    if existing is None:
        existing = []
    if new is None:
        return existing
    if isinstance(new, list):
        return existing + new
    return existing + [new]


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    task_plan: Optional[List[Dict]]
    retrieved_context: Optional[str]
    active_subagents: Optional[List[str]]
    skill_route: Optional[str]
    route: Optional[str]
    subagent_tasks: Optional[List[Dict]]
    subagent_results: Annotated[Optional[List[Dict]], add_subagent_results]
    subagent_depth: Optional[int]
