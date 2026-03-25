import os

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

DB_PATH = "./checkpoints/checkpoints.db"


def get_checkpointer():
    """返回 AsyncSqliteSaver 实例，作为 async context manager 使用。

    Usage:
        async with get_checkpointer() as checkpointer:
            app = build_graph(checkpointer)
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return AsyncSqliteSaver.from_conn_string(DB_PATH)
