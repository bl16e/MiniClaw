from config import llm
from utils import get_sensitive_tools, reflect_and_save_experience, should_reflect


async def run_agent(app, query: str, thread_id: str = "default", checkpoint_id: str = None):
    """Run agent with human-in-the-loop approval for sensitive tools.

    Args:
        app: compiled LangGraph app
        query: user input (can be empty if resuming from checkpoint)
        thread_id: conversation thread id
        checkpoint_id: optional checkpoint to resume from
    """
    config = {"configurable": {"thread_id": thread_id}}
    if checkpoint_id:
        config["configurable"]["checkpoint_id"] = checkpoint_id

    # 如果有 checkpoint_id 且 query 为空，则从该检查点继续（不发送新消息）
    inputs = None if (checkpoint_id and not query) else {"messages": [("user", query)]}

    while True:
        async for state in app.astream(inputs, config=config, stream_mode="values"):
            message = state["messages"][-1]
            if hasattr(message, "pretty_print"):
                message.pretty_print()
            else:
                print(message)

        snapshot = await app.aget_state(config)
        if not snapshot.next:
            break

        sensitive = get_sensitive_tools(snapshot.values)
        if not sensitive:
            inputs = None
            continue

        print("\nAPPROVAL REQUIRED")
        for index, tool_call in enumerate(sensitive, 1):
            print(f"{index}. Tool: {tool_call['name']}")
            print(f"   Args: {tool_call['args']}")

        response = input("\nApprove execution? (yes/no): ").strip().lower()
        if response in ["yes", "y"]:
            inputs = None
        else:
            print("Execution rejected by user")
            break

    try:
        final_snapshot = await app.aget_state(config)
        messages = final_snapshot.values.get("messages", [])

        if messages and should_reflect(messages):
            await reflect_and_save_experience(messages, llm)
            print("\nExperience reflected and saved")
    except Exception as error:
        print(f"\nWarning: Failed to reflect - {error}")
