from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    checkpoint_id: Optional[str] = None


class ApprovalRequest(BaseModel):
    approved: bool


class CreateSessionRequest(BaseModel):
    name: Optional[str] = None


class BranchRequest(BaseModel):
    checkpoint_id: str
    new_thread_id: Optional[str] = None


class ReplayRequest(BaseModel):
    checkpoint_id: str


class MessageResponse(BaseModel):
    id: Optional[str] = None
    type: str  # human, ai, tool
    content: str
    tool_calls: Optional[list] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


class SessionResponse(BaseModel):
    thread_id: str
    message_count: int
    preview: str


class HistoryResponse(BaseModel):
    checkpoint_id: str
    node: str
    step: int
    message_count: int
    next_nodes: List[str]
    preview: str
