import asyncio

from agent_core import build_graph, set_app
from checkpointer import get_checkpointer
from runner import run_agent
from session_manager import (
    list_sessions,
    create_session,
    delete_session,
    get_session_summary,
    get_state_history,
    replay_from_checkpoint,
    branch_from_checkpoint,
)


def print_help():
    print("""
Available commands:
  /sessions              List all sessions
  /new [name]            Create and switch to a new session
  /switch <thread_id>    Switch to an existing session
  /delete <thread_id>    Delete a session
  /history [limit]       Show checkpoint history (default: 20)
  /replay <checkpoint_id>  Replay from a checkpoint
  /branch <checkpoint_id> [name]  Branch from a checkpoint
  /current               Show current session info
  /help                  Show this help message
  exit / quit / q        Exit the program
""")


async def handle_command(app, command: str, thread_id: str) -> str:
    """Handle slash commands. Returns the (possibly updated) thread_id."""
    parts = command.strip().split()
    cmd = parts[0].lower()

    if cmd == "/sessions":
        sessions = await list_sessions(app)
        if not sessions:
            print("No sessions found.")
        else:
            print(f"\n{'Thread ID':<40} {'Messages':<10} {'Preview'}")
            print("-" * 80)
            for s in sessions:
                marker = " <--" if s["thread_id"] == thread_id else ""
                print(f"{s['thread_id']:<40} {s['message_count']:<10} {s['preview']}{marker}")
        print()

    elif cmd == "/new":
        name = parts[1] if len(parts) > 1 else None
        new_id = create_session(name)
        thread_id = new_id
        print(f"Created and switched to session: {thread_id}\n")

    elif cmd == "/switch":
        if len(parts) < 2:
            print("Usage: /switch <thread_id>")
        else:
            target = parts[1]
            thread_id = target
            summary = await get_session_summary(app, thread_id)
            print(f"Switched to session: {thread_id} ({summary['message_count']} messages)\n")

    elif cmd == "/delete":
        if len(parts) < 2:
            print("Usage: /delete <thread_id>")
        else:
            target = parts[1]
            if target == thread_id:
                print("Cannot delete the current active session. Switch first.")
            else:
                count = await delete_session(app, target)
                print(f"Deleted {count} checkpoints for session: {target}\n")

    elif cmd == "/history":
        limit = int(parts[1]) if len(parts) > 1 else 20
        history = await get_state_history(app, thread_id, limit)
        if not history:
            print("No history found for this session.")
        else:
            print(f"\nCheckpoint history for [{thread_id}] (latest first):")
            print(f"{'#':<4} {'Checkpoint ID':<40} {'Step':<6} {'Node':<12} {'Msgs':<6} {'Next':<15} {'Preview'}")
            print("-" * 130)
            for i, h in enumerate(history):
                print(f"{i:<4} {h['checkpoint_id']:<40} {h['step']:<6} {h['node']:<12} {h['message_count']:<6} {str(h['next_nodes']):<15} {h['preview']}")
        print()

    elif cmd == "/replay":
        if len(parts) < 2:
            print("Usage: /replay <checkpoint_id>")
        else:
            checkpoint_id = parts[1]
            try:
                config = await replay_from_checkpoint(app, thread_id, checkpoint_id)
                print(f"Replaying from checkpoint: {checkpoint_id}")
                await run_agent(app, "", thread_id, checkpoint_id)
            except ValueError as e:
                print(f"Error: {e}")

    elif cmd == "/branch":
        if len(parts) < 2:
            print("Usage: /branch <checkpoint_id> [name]")
        else:
            checkpoint_id = parts[1]
            name = parts[2] if len(parts) > 2 else None
            try:
                new_id = await branch_from_checkpoint(app, thread_id, checkpoint_id, name)
                thread_id = new_id
                print(f"Branched and switched to: {thread_id}\n")
            except ValueError as e:
                print(f"Error: {e}")

    elif cmd == "/current":
        summary = await get_session_summary(app, thread_id)
        print(f"\nCurrent session: {thread_id}")
        print(f"  Messages: {summary['message_count']}")
        print(f"  Preview:  {summary['preview']}")
        if summary.get("next_nodes"):
            print(f"  Pending:  {summary['next_nodes']}")
        print()

    elif cmd == "/help":
        print_help()

    else:
        print(f"Unknown command: {cmd}. Type /help for available commands.")

    return thread_id


async def main():
    """Main entry point for the agent."""
    async with get_checkpointer() as checkpointer:
        app = build_graph(checkpointer)
        set_app(app)

        thread_id = "default"
        print("Agent started. Type '/help' for commands, 'exit' to quit.\n")

        while True:
            try:
                query = input(f"[{thread_id}] You: ").strip()
                if query.lower() in ["exit", "quit", "q"]:
                    print("Goodbye!")
                    break
                if not query:
                    continue

                if query.startswith("/"):
                    thread_id = await handle_command(app, query, thread_id)
                else:
                    await run_agent(app, query, thread_id)
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as error:
                print(f"\nError: {error}")


if __name__ == "__main__":
    asyncio.run(main())
