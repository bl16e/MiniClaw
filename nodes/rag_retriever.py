import asyncio

from langchain_core.messages import SystemMessage


async def rag_retriever_node(state):
    query = state["messages"][-1].content

    from rag.chroma_db import get_vectorstore_documents, get_vectorstore_history

    results = await asyncio.gather(
        asyncio.to_thread(get_vectorstore_history().similarity_search, query, k=2),
        asyncio.to_thread(get_vectorstore_documents().similarity_search, query, k=2),
    )

    all_docs = [doc for result in results for doc in result]
    context = "\n\n".join(
        [
            f"[{doc.metadata.get('source', 'unknown')}]\n{doc.page_content}"
            for doc in all_docs
        ]
    )

    return {
        "retrieved_context": context,
        "messages": [SystemMessage(content=f"Retrieved context:\n{context}")],
    }
