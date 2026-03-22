import asyncio
from langchain_core.messages import ToolMessage

async def parallel_tools_node(state):
    last_msg = state["messages"][-1]
    tool_calls = last_msg.tool_calls

    from tools.tools import tools
    tool_map = {t.name: t for t in tools}

    async def execute_tool(tool_call):
        tool_fn = tool_map[tool_call["name"]]
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, tool_fn.invoke, tool_call["args"])
        return ToolMessage(content=str(result), tool_call_id=tool_call["id"])

    results = await asyncio.gather(*[execute_tool(tc) for tc in tool_calls])
    return {"messages": results}
