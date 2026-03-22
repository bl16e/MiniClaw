# MiniClaw

MiniClaw is a modular LangGraph-based agent project with tool calling, lightweight RAG, subagent orchestration, and human approval for sensitive operations.

## Features

- Async LangGraph workflow with classifier, RAG retrieval, and tool execution
- Parallel tool execution for multi-tool model responses
- RAG over local documents and conversation history via Chroma
- Optional Gmail sending tool with explicit approval gate
- Subagent fan-out/fan-in flow for multi-item analysis
- Environment-based configuration suitable for publishing

## Project Structure

```text
.
├── agent_core.py          # Graph assembly and routing
├── config.py              # LLM configuration from environment variables
├── main.py                # CLI entry point
├── runner.py              # Streaming runner with approval flow
├── nodes/                 # Graph nodes
├── rag/                   # Chroma-backed retrieval helpers
├── tools/                 # Tool definitions
├── skills/                # Skill prompts and SOPs
├── docs/                  # Supporting documentation
└── chroma_db/             # Local vector store directory
```

## Requirements

- Python 3.10+
- A compatible OpenAI-style API endpoint
- Optional Gmail OAuth credentials if you want `send_email`

## Installation

```bash
pip install -r requirements.txt
```

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Required variables:

- `OPENAI_API_KEY`

Optional variables:

- `OPENAI_API_BASE`
- `MODEL_NAME`
- `HTTP_PROXY`
- `HTTPS_PROXY`
- `GMAIL_CREDENTIALS_FILE`
- `GMAIL_TOKEN_FILE`

## Usage

Run the CLI agent:

```bash
python main.py
```

Example:

```text
You: Summarize the papers in the knowledge base
```

## RAG Helpers

```python
from rag import ingest_agent_knowledge, ingest_local_files

ingest_local_files("./docs")
ingest_agent_knowledge("Important internal context.")
```

## Safety Notes

- Sensitive tools require approval in `runner.py`
- Secrets and local auth files are ignored by `.gitignore`
- Runtime Chroma index files are ignored; source documents can still be versioned explicitly

## Known Notes

- `search` and `navigate_to_url` use DuckDuckGo and plain HTTP requests, so results are best-effort
- Gmail sending requires a local OAuth flow on first use
