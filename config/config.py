import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def _get_required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


MODEL_NAME = os.getenv("MODEL_NAME", "qwen3-vl-235b-a22b-thinking")
OPENAI_API_BASE = os.getenv(
    "OPENAI_API_BASE",
    "https://dashscope.aliyuncs.com/compatible-mode/v1",
)


llm = ChatOpenAI(
    openai_api_key=_get_required_env("OPENAI_API_KEY"),
    openai_api_base=OPENAI_API_BASE,
    model_name=MODEL_NAME,
)


BASE_SYSTEM_PROMPT = """You are my AI assistant. Answer the user's query as accurately as possible.
For time-sensitive queries, call `get_current_time` first, then construct the search query with that date context.
When using the `search` tool, the query must be in English.
Prefer official sources when using `navigate_to_url`.
The knowledge base is stored in `./chroma_db/documents`. Use `list_knowledge_base` when the user asks about available papers."""
