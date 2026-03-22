import asyncio

from agent_core import app
from runner import run_agent


async def main():
    """Main entry point for the agent."""
    thread_id = "default"
    print("Agent started. Type 'exit' or 'quit' to end the conversation.\n")

    while True:
        try:
            query = input("You: ").strip()
            if query.lower() in ["exit", "quit", "q"]:
                print("Goodbye!")
                break
            if not query:
                continue

            await run_agent(app, query, thread_id)
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as error:
            print(f"\nError: {error}")


if __name__ == "__main__":
    asyncio.run(main())
