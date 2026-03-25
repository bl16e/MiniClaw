from __future__ import annotations
import json
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from api_models import (
    ChatRequest,
    ApprovalRequest,
    CreateSessionRequest,
    BranchRequest,
    ReplayRequest,
    MessageResponse,
    SessionResponse,
    HistoryResponse,
)
from checkpointer import get_checkpointer
from agent_core import build_graph, set_app
from approval_manager import ApprovalManager
from stream_handler import stream_chat
from session_manager import (
    list_sessions,
    create_session,
    delete_session,
    get_session_summary,
    get_state_history,
    replay_from_checkpoint,
    branch_from_checkpoint,
)

# Module-level references set during lifespan
_graph = None
_approval_mgr = ApprovalManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _graph
    async with get_checkpointer() as checkpointer:
        _graph = build_graph(checkpointer)
        set_app(_graph)
        yield


app = FastAPI(title="MiniClaw Agent Chat", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_graph():
    if _graph is None:
        raise HTTPException(status_code=503, detail="Graph not initialized")
    return _graph


# ── Chat ──────────────────────────────────────────────────


@app.post("/api/chat/{thread_id}")
async def chat(thread_id: str, req: ChatRequest):
    graph = _get_graph()
    return StreamingResponse(
        stream_chat(graph, thread_id, req.message, req.checkpoint_id, _approval_mgr),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/chat/{thread_id}/approve")
async def approve(thread_id: str, req: ApprovalRequest):
    if not _approval_mgr.has_pending(thread_id):
        raise HTTPException(status_code=404, detail="No pending approval for this thread")
    _approval_mgr.resolve(thread_id, req.approved)
    return {"status": "ok", "approved": req.approved}


# ── Sessions ──────────────────────────────────────────────


@app.get("/api/sessions", response_model=List[SessionResponse])
async def sessions_list():
    graph = _get_graph()
    return await list_sessions(graph)


@app.post("/api/sessions", response_model=SessionResponse)
async def sessions_create(req: CreateSessionRequest):
    thread_id = create_session(req.name)
    return SessionResponse(thread_id=thread_id, message_count=0, preview="(new session)")


@app.get("/api/sessions/{thread_id}")
async def sessions_get(thread_id: str):
    graph = _get_graph()
    return await get_session_summary(graph, thread_id)


@app.delete("/api/sessions/{thread_id}")
async def sessions_delete(thread_id: str):
    graph = _get_graph()
    count = await delete_session(graph, thread_id)
    return {"deleted_checkpoints": count}


# ── Messages ──────────────────────────────────────────────


def _serialize_message(msg) -> dict:
    """Convert a LangChain message to a JSON-serializable dict."""
    data = {
        "id": getattr(msg, "id", None),
        "type": msg.type,
        "content": msg.content if isinstance(msg.content, str) else json.dumps(msg.content, ensure_ascii=False),
    }
    if hasattr(msg, "tool_calls") and msg.tool_calls:
        data["tool_calls"] = [
            {"id": tc.get("id", ""), "name": tc.get("name", ""), "args": tc.get("args", {})}
            for tc in msg.tool_calls
        ]
    if hasattr(msg, "tool_call_id") and msg.tool_call_id:
        data["tool_call_id"] = msg.tool_call_id
    if hasattr(msg, "name") and msg.name:
        data["name"] = msg.name
    return data


@app.get("/api/sessions/{thread_id}/messages", response_model=List[MessageResponse])
async def messages_list(thread_id: str):
    graph = _get_graph()
    config = {"configurable": {"thread_id": thread_id}}
    try:
        state = await graph.aget_state(config)
        messages = state.values.get("messages", [])
        return [_serialize_message(m) for m in messages]
    except Exception:
        return []


# ── History (Time Travel) ─────────────────────────────────


@app.get("/api/sessions/{thread_id}/history", response_model=List[HistoryResponse])
async def history_list(thread_id: str, limit: int = 20):
    graph = _get_graph()
    return await get_state_history(graph, thread_id, limit)


@app.post("/api/sessions/{thread_id}/replay")
async def replay(thread_id: str, req: ReplayRequest):
    graph = _get_graph()
    return StreamingResponse(
        stream_chat(graph, thread_id, None, req.checkpoint_id, _approval_mgr),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/sessions/{thread_id}/branch")
async def branch(thread_id: str, req: BranchRequest):
    graph = _get_graph()
    try:
        new_id = await branch_from_checkpoint(
            graph, thread_id, req.checkpoint_id, req.new_thread_id
        )
        return {"thread_id": new_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
