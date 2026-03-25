from __future__ import annotations
import json
from typing import AsyncGenerator, List, Optional

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from utils import get_sensitive_tools
from approval_manager import ApprovalManager


def _sse_event(event_type: str, data: dict) -> str:
    """Format a server-sent event."""
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _serialize_tool_calls(tool_calls: list) -> List[dict]:
    return [
        {"id": tc.get("id", ""), "name": tc.get("name", ""), "args": tc.get("args", {})}
        for tc in tool_calls
    ]


async def stream_chat(
    graph,
    thread_id: str,
    message: Optional[str],
    checkpoint_id: Optional[str],
    approval_mgr: ApprovalManager,
) -> AsyncGenerator[str, None]:
    """Stream chat as SSE events.

    Wraps graph.astream with approval flow for sensitive tools.
    """
    config = {"configurable": {"thread_id": thread_id}}
    if checkpoint_id:
        config["configurable"]["checkpoint_id"] = checkpoint_id

    inputs = None if (checkpoint_id and not message) else {"messages": [("user", message)]}

    try:
        while True:
            step = 0
            async for update in graph.astream(inputs, config=config, stream_mode="updates"):
                for node_name, output in update.items():
                    if node_name == "__interrupt__":
                        continue
                    step += 1
                    yield _sse_event("node_start", {"node": node_name, "step": step})

                    messages = output.get("messages", [])
                    for msg in messages:
                        if isinstance(msg, AIMessage):
                            if msg.tool_calls:
                                for tc in msg.tool_calls:
                                    yield _sse_event("tool_call", {
                                        "id": tc.get("id", ""),
                                        "name": tc.get("name", ""),
                                        "args": tc.get("args", {}),
                                    })
                            if msg.content:
                                yield _sse_event("message_complete", {
                                    "content": msg.content,
                                    "role": "ai",
                                })
                        elif isinstance(msg, ToolMessage):
                            content = msg.content
                            if isinstance(content, list):
                                content = json.dumps(content, ensure_ascii=False)
                            status = "error" if msg.status == "error" else "completed"
                            yield _sse_event("tool_result", {
                                "id": msg.tool_call_id or "",
                                "name": msg.name or "",
                                "result": content,
                                "status": status,
                            })
                        elif isinstance(msg, HumanMessage):
                            pass  # skip echoed user input

            # Check if graph is waiting at an interrupt
            snapshot = await graph.aget_state(config)
            if not snapshot.next:
                break

            sensitive = get_sensitive_tools(snapshot.values)
            if not sensitive:
                inputs = None
                continue

            # Sensitive tools → wait for approval
            approval_mgr.request_approval(thread_id, sensitive)
            yield _sse_event("approval_required", {
                "tools": _serialize_tool_calls(sensitive),
            })

            approved = await approval_mgr.wait_for_decision(thread_id)
            approval_mgr.cleanup(thread_id)

            if approved is None:
                yield _sse_event("error", {"message": "Approval timed out"})
                break

            yield _sse_event("approval_resolved", {"approved": approved})

            if approved:
                inputs = None
                continue
            else:
                break

        yield _sse_event("complete", {"thread_id": thread_id})

    except Exception as e:
        yield _sse_event("error", {"message": str(e)})
