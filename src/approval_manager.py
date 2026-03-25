from __future__ import annotations
import asyncio
from typing import Dict, List, Optional


class ApprovalManager:
    """Per-thread approval state machine using asyncio.Event."""

    def __init__(self):
        self._pending: Dict[str, dict] = {}

    def request_approval(self, thread_id: str, tools: List[dict]):
        """Create a pending approval for a thread."""
        event = asyncio.Event()
        self._pending[thread_id] = {
            "event": event,
            "tools": tools,
            "approved": None,
        }

    async def wait_for_decision(self, thread_id: str, timeout: float = 300) -> Optional[bool]:
        """Wait for the user to approve or reject. Returns True/False or None on timeout."""
        pending = self._pending.get(thread_id)
        if not pending:
            return None
        try:
            await asyncio.wait_for(pending["event"].wait(), timeout=timeout)
            return pending["approved"]
        except asyncio.TimeoutError:
            self.cleanup(thread_id)
            return None

    def resolve(self, thread_id: str, approved: bool) -> bool:
        """Resolve a pending approval. Returns False if no pending approval exists."""
        pending = self._pending.get(thread_id)
        if not pending:
            return False
        pending["approved"] = approved
        pending["event"].set()
        return True

    def cleanup(self, thread_id: str):
        """Remove pending approval state for a thread."""
        self._pending.pop(thread_id, None)

    def has_pending(self, thread_id: str) -> bool:
        return thread_id in self._pending
