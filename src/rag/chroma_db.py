import os

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface.embeddings import HuggingFaceEmbeddings

_embeddings = None
_vectorstore_history = None
_vectorstore_documents = None
_splitter = None


def _ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    return _embeddings


def get_splitter():
    global _splitter
    if _splitter is None:
        _splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    return _splitter


def get_vectorstore_history():
    global _vectorstore_history
    if _vectorstore_history is None:
        _vectorstore_history = Chroma(
            persist_directory=_ensure_dir("./chroma_db/history"),
            embedding_function=get_embeddings(),
        )
    return _vectorstore_history


def get_vectorstore_documents():
    global _vectorstore_documents
    if _vectorstore_documents is None:
        _vectorstore_documents = Chroma(
            persist_directory=_ensure_dir("./chroma_db/documents"),
            embedding_function=get_embeddings(),
        )
    return _vectorstore_documents


def ingest_conversation_history(messages):
    """Store conversation history in the history vector database."""
    history = "\n".join([f"{message.type}: {message.content}" for message in messages])
    get_vectorstore_history().add_texts([history])


def load_document(file_path: str) -> tuple[str, str]:
    suffix = os.path.splitext(file_path)[1].lower()
    if suffix == ".pdf":
        pages = PyPDFLoader(file_path).load()
        content = "\n".join(page.page_content for page in pages)
    else:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            content = file.read()
    return content, file_path


def ingest_downloaded_doc(file_path: str):
    """Store downloaded document content in the documents vector database."""
    try:
        content, source = load_document(file_path)
        chunks = get_splitter().split_text(content)
        batch_size = 100
        for index in range(0, len(chunks), batch_size):
            batch = chunks[index : index + batch_size]
            get_vectorstore_documents().add_texts(
                batch,
                metadatas=[{"source": source}] * len(batch),
            )

        return f"Document ingested: {len(chunks)} chunks"
    except Exception as error:
        return f"Error ingesting document: {error}"


def ingest_local_files(directory: str):
    """Ingest .txt, .md, and .pdf files from a local directory."""
    supported_suffixes = {".txt", ".md", ".pdf"}
    added_files = 0

    for root, _, files in os.walk(directory):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            if os.path.splitext(file_path)[1].lower() not in supported_suffixes:
                continue
            result = ingest_downloaded_doc(file_path)
            if result.startswith("Document ingested:"):
                added_files += 1

    return f"Ingested {added_files} files from {directory}"


def ingest_agent_knowledge(content: str):
    """Store free-form text in the documents vector database."""
    chunks = get_splitter().split_text(content)
    get_vectorstore_documents().add_texts(
        chunks,
        metadatas=[{"source": "agent_knowledge"}] * len(chunks),
    )
    return f"Knowledge ingested: {len(chunks)} chunks"
