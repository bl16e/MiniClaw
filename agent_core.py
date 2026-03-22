import os
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from config import llm, BASE_SYSTEM_PROMPT
from tools.tools import tools
from state import AgentState
from utils import SOUL_CONTENT, USER_CONTENT, EXPERIENCE_CONTENT, summarize_if_needed
from nodes.classifier import classifier_node
from nodes.rag_retriever import rag_retriever_node
from nodes.parallel_tools import parallel_tools_node
from nodes.subagent import subagent_coordinator_node, subagent_executor_node, subagent_aggregator_node, continue_to_subagents


model = llm.bind_tools(tools)

SKILLS_CONTENT = ""
if os.path.exists("skills/skill.md"):
    with open("skills/skill.md", "r", encoding="utf-8") as f:
        SKILLS_CONTENT = f.read()


async def agent_node(state):
    """Agent with skill loading and plan execution"""
    state = await summarize_if_needed(state, llm)

    system_prompt = BASE_SYSTEM_PROMPT
    system_prompt += f"\nThere are some skills you can use: \n{SKILLS_CONTENT}\nIf you want to use a skill, you can access the specific file to get the skill SOP"

    if SOUL_CONTENT:
        system_prompt += f"\n\n## Agent Identity\n{SOUL_CONTENT}"
    if USER_CONTENT:
        system_prompt += f"\n\n## User Information\n{USER_CONTENT}"
    if EXPERIENCE_CONTENT:
        system_prompt += f"\n\n## Past Experience\n{EXPERIENCE_CONTENT}"

    if state.get("retrieved_context"):
        system_prompt += f"\n\nThe related context:\n{state['retrieved_context']}"

    response = await model.ainvoke([SystemMessage(content=system_prompt)] + list(state["messages"]))
    return {"messages": [response]}


async def should_continue(state):
    """Determine if tools should be called"""
    last_msg = state["messages"][-1]
    if not last_msg.tool_calls:
        return "end"
    return "parallel_tools" if len(last_msg.tool_calls) > 1 else "tools"


async def route_from_classifier(state):
    """Route based on classifier decision"""
    return state.get("route", "agent")


async def classifier_wrapper(state):
    return await classifier_node(state, llm)


async def subagent_executor_wrapper(state):
    return await subagent_executor_node(state, app)

# Build graph
def build_graph():
    """Build and compile the agent graph"""
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("classifier", classifier_wrapper)
    graph.add_node("rag_retriever", rag_retriever_node)
    graph.add_node("agent", agent_node)
    graph.add_node("parallel_tools", parallel_tools_node)
    graph.add_node("subagent_coordinator", subagent_coordinator_node)
    graph.add_node("subagent_executor", subagent_executor_wrapper)
    graph.add_node("subagent_aggregator", subagent_aggregator_node)

    tool_node = ToolNode(tools=tools)
    graph.add_node("tools", tool_node)

    # Set entry point
    graph.set_entry_point("classifier")

    # Classifier routing
    graph.add_conditional_edges(
        "classifier",
        route_from_classifier,
        {
            "rag": "rag_retriever",
            "subagent_coordinator": "subagent_coordinator",
            "agent": "agent"
        }
    )

    # Converge to agent
    graph.add_edge("rag_retriever", "agent")

    # Subagent flow
    graph.add_conditional_edges("subagent_coordinator", continue_to_subagents)
    graph.add_edge("subagent_executor", "subagent_aggregator")
    graph.add_edge("subagent_aggregator", "agent")

    # Agent tool routing
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "parallel_tools": "parallel_tools",
            "tools": "tools",
            "end": END
        }
    )

    # Tools back to agent
    graph.add_edge("parallel_tools", "agent")
    graph.add_edge("tools", "agent")

    # Compile with checkpointer and interrupts
    memory = MemorySaver()
    return graph.compile(
        checkpointer=memory,
        interrupt_before=["tools", "parallel_tools"]
    )


app = build_graph()
