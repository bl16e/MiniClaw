import os

from langchain_core.messages import AIMessage, HumanMessage

SENSITIVE_TOOLS = {"send_email", "download_file", "run_python_code"}

SOUL_CONTENT = ""
USER_CONTENT = ""
EXPERIENCE_CONTENT = ""

if os.path.exists("SOUL.md"):
    with open("SOUL.md", "r", encoding="utf-8") as file:
        SOUL_CONTENT = file.read().strip()

if os.path.exists("USER.md"):
    with open("USER.md", "r", encoding="utf-8") as file:
        USER_CONTENT = file.read().strip()

if os.path.exists("EXPERIENCE.md"):
    with open("EXPERIENCE.md", "r", encoding="utf-8") as file:
        EXPERIENCE_CONTENT = file.read().strip()


def is_sensitive_tool_call(tool_call):
    """Check if a tool call requires approval."""
    tool_name = tool_call.get("name")
    if tool_name == "filesystem":
        return tool_call.get("args", {}).get("operation") == "write"
    return tool_name in SENSITIVE_TOOLS


def get_sensitive_tools(state):
    """Extract sensitive tool calls from the last message."""
    last_msg = state["messages"][-1]
    if not hasattr(last_msg, "tool_calls") or not last_msg.tool_calls:
        return []
    return [tool_call for tool_call in last_msg.tool_calls if is_sensitive_tool_call(tool_call)]


def should_reflect(messages):
    """Determine if reflection is needed based on recent conversation complexity."""
    if len(messages) < 10:
        return False

    has_tool_calls = any(hasattr(message, "tool_calls") and message.tool_calls for message in messages[-10:])
    has_errors = any(
        "error" in str(message.content).lower() or "failed" in str(message.content).lower()
        for message in messages[-10:]
        if hasattr(message, "content")
    )
    return has_tool_calls or has_errors


async def reflect_and_save_experience(messages, llm):
    """Reflect on the conversation and save one learning."""
    conversation = "\n".join([f"{message.type}: {message.content}" for message in messages[-10:]])
    prompt = f"""Reflect on this conversation and extract one key learning that could help in future interactions.

Conversation:
{conversation}

Return only a single concise sentence (max 100 words) in the format "- [Learning]".
If there is no meaningful learning, return "NONE".
"""

    response = await llm.ainvoke([HumanMessage(content=prompt)])
    experience = response.content.strip()

    if experience and experience != "NONE":
        with open("EXPERIENCE.md", "a", encoding="utf-8") as file:
            file.write(f"\n{experience}")
        await maintain_experience(llm)


async def maintain_experience(llm):
    """Keep at most 10 distilled experiences."""
    if not os.path.exists("EXPERIENCE.md"):
        return

    with open("EXPERIENCE.md", "r", encoding="utf-8") as file:
        content = file.read().strip()

    experiences = [line.strip() for line in content.split("\n") if line.strip().startswith("-")]

    if len(experiences) > 10:
        prompt = f"""Compress these {len(experiences)} experiences into the 10 most important and reusable learnings.

Experiences:
{chr(10).join(experiences)}

Return exactly 10 lines, each starting with "- ".
"""
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        with open("EXPERIENCE.md", "w", encoding="utf-8") as file:
            file.write(response.content.strip())


async def summarize_if_needed(state, llm):
    """Compress message history if it becomes too long."""
    messages = state["messages"]
    if len(messages) <= 30:
        return state

    from rag import ingest_conversation_history

    ingest_conversation_history(messages[:-10])
    conversation = "\n".join(
        [
            f"{message.type}: {message.content[:500]}"
            for message in messages[:-10]
            if hasattr(message, "content") and message.content
        ]
    )

    prompt = f"""Summarize the following conversation history concisely, capturing key points, decisions, and context.

{conversation}

Provide a brief summary in at most 200 words.
"""

    summary_response = await llm.ainvoke([HumanMessage(content=prompt)])
    summary = summary_response.content.strip()
    new_messages = [AIMessage(content=f"[Previous conversation summary: {summary}]"), *messages[-10:]]
    return {"messages": new_messages}
