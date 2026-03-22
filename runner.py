from config import llm
from utils import get_sensitive_tools, reflect_and_save_experience, should_reflect


async def run_agent(app, query: str, thread_id: str = "default"):
    """Run agent with human-in-the-loop approval for sensitive tools."""
    config = {"configurable": {"thread_id": thread_id}}
    inputs = {"messages": [("user", query)]}

    while True:
        async for state in app.astream(inputs, config=config, stream_mode="values"):
            message = state["messages"][-1]
            if hasattr(message, "pretty_print"):
                message.pretty_print()
            else:
                print(message)

        snapshot = app.get_state(config)
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
        final_snapshot = app.get_state(config)
        messages = final_snapshot.values.get("messages", [])

        if messages and should_reflect(messages):
            await reflect_and_save_experience(messages, llm)
            print("\nExperience reflected and saved")
    except Exception as error:
        print(f"\nWarning: Failed to reflect - {error}")
