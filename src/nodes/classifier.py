from langchain_core.messages import HumanMessage


async def classifier_node(state, model):
    """LLM-based router for rag, subagent, or direct agent execution."""
    query = state["messages"][-1].content

    if state.get("subagent_depth", 0) > 0:
        return {"route": "agent"}

    prompt = f"""You are a task router classifier. Return only one of these words:
rag
subagent_coordinator
agent

User query: {query}

Routing rules:
1. rag
- The query asks to recall conversation history.
- The query should retrieve from the internal paper or document knowledge base.

2. subagent_coordinator
- The query clearly requires several independent items to be processed in parallel.
- Examples include comparing multiple papers, products, or files.

3. agent
- The query needs current information, tools, calculation, or normal general handling.
- Use this as the default when the query does not strongly fit the first two.

Return only one word and nothing else.
"""

    response = await model.ainvoke([HumanMessage(content=prompt)])
    route = response.content.strip()
    print(route)
    return {"route": route}
