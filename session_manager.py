from __future__ import annotations
import uuid
from datetime import datetime


def _short_id():
    return str(uuid.uuid4())[:8]


def _get_last_message_preview(values, max_len=60):
    """获取最后一条消息的预览文本。"""
    messages = values.get("messages", [])
    if not messages:
        return "(empty)"
    last = messages[-1]
    content = getattr(last, "content", str(last))
    if isinstance(content, list):
        content = str(content)
    if len(content) > max_len:
        content = content[:max_len] + "..."
    return content


# ── 会话管理 ──────────────────────────────────────────────


async def list_sessions(app) -> list[dict]:
    """查询 checkpointer 中所有不同的 thread_id，返回摘要列表。"""
    sessions = {}
    async for checkpoint_tuple in app.checkpointer.alist(None):
        tid = checkpoint_tuple.config["configurable"]["thread_id"]
        if tid not in sessions:
            # 取该 thread 最新的 checkpoint 信息
            state = checkpoint_tuple.checkpoint
            messages = state.get("channel_values", {}).get("messages", [])
            sessions[tid] = {
                "thread_id": tid,
                "message_count": len(messages),
                "preview": _get_last_message_preview({"messages": messages}),
            }
    return list(sessions.values())


def create_session(name: str = None) -> str:
    """生成新的 thread_id。"""
    if name:
        return name
    return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{_short_id()}"


async def delete_session(app, thread_id: str):
    """删除指定 thread_id 的所有检查点。"""
    config = {"configurable": {"thread_id": thread_id}}
    checkpoints_deleted = 0
    async for checkpoint_tuple in app.checkpointer.alist(config):
        await app.checkpointer.adelete(checkpoint_tuple.config)
        checkpoints_deleted += 1
    return checkpoints_deleted


async def get_session_summary(app, thread_id: str) -> dict:
    """返回指定会话的摘要信息。"""
    config = {"configurable": {"thread_id": thread_id}}
    try:
        state = await app.aget_state(config)
        messages = state.values.get("messages", [])
        return {
            "thread_id": thread_id,
            "message_count": len(messages),
            "preview": _get_last_message_preview(state.values),
            "next_nodes": list(state.next) if state.next else [],
        }
    except Exception:
        return {"thread_id": thread_id, "message_count": 0, "preview": "(no state)"}


# ── Time Travel ───────────────────────────────────────────


def _count_user_messages(messages) -> int:
    """统计 human 消息数量。"""
    return sum(1 for m in messages if getattr(m, "type", None) == "human")


async def get_state_history(app, thread_id: str, limit: int = 20) -> list:
    """返回该会话的检查点历史列表。

    只保留用户消息数量发生变化的关键检查点（即每轮用户交互的边界），
    而不是每个内部节点执行都显示一条。
    """
    config = {"configurable": {"thread_id": thread_id}}
    history = []
    prev_user_count = -1

    # aget_state_history 返回从最新到最旧的检查点
    all_states = []
    async for state in app.aget_state_history(config):
        all_states.append(state)

    # 从旧到新遍历，找出用户消息数量变化的边界点
    key_checkpoints = []
    for state in reversed(all_states):
        messages = state.values.get("messages", [])
        user_count = _count_user_messages(messages)
        if user_count != prev_user_count:
            key_checkpoints.append(state)
            prev_user_count = user_count

    # 再反转为从新到旧的顺序展示
    for state in reversed(key_checkpoints):
        messages = state.values.get("messages", [])
        history.append({
            "checkpoint_id": state.config["configurable"]["checkpoint_id"],
            "node": state.metadata.get("source", "unknown"),
            "step": state.metadata.get("step", 0),
            "message_count": len(messages),
            "next_nodes": list(state.next) if state.next else [],
            "preview": _get_last_message_preview(state.values),
        })
        if len(history) >= limit:
            break
    return history


async def replay_from_checkpoint(app, thread_id: str, checkpoint_id: str):
    """构建从指定检查点继续执行的 config。"""
    config = {
        "configurable": {
            "thread_id": thread_id,
            "checkpoint_id": checkpoint_id,
        }
    }
    # 验证该 checkpoint 存在
    state = await app.aget_state(config)
    if state.values is None:
        raise ValueError(f"Checkpoint {checkpoint_id} not found for thread {thread_id}")
    return config


# ── 会话分支 ──────────────────────────────────────────────


async def branch_from_checkpoint(app, source_thread_id: str, checkpoint_id: str, new_thread_id: str = None) -> str:
    """从某个检查点创建分支会话。"""
    source_config = {
        "configurable": {
            "thread_id": source_thread_id,
            "checkpoint_id": checkpoint_id,
        }
    }
    state = await app.aget_state(source_config)
    if state.values is None:
        raise ValueError(f"Checkpoint {checkpoint_id} not found for thread {source_thread_id}")

    if not new_thread_id:
        new_thread_id = f"{source_thread_id}_branch_{_short_id()}"

    new_config = {"configurable": {"thread_id": new_thread_id}}
    await app.aupdate_state(new_config, state.values)

    return new_thread_id
