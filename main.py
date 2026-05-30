import asyncio
import uvicorn
from pathlib import Path


FAISS_DIR = Path("app/db/faiss_vector_store")
DB_PATH = Path("app/db/Dynamic_SQLite_DB.db")


def init_rag():
    if FAISS_DIR.exists() and any(FAISS_DIR.iterdir()):
        return print("RAG index existed")
    from llama_index.core import Settings
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from app.rag.indexing import load_documents, chunk_documents, build_store_index
    Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    nodes = chunk_documents(load_documents("app/rag/seed_parking_info.md"))
    build_store_index(nodes)
    print("RAG index built.")


async def init_sql():
    if DB_PATH.exists():
        return print("SQL existed")
    from app.SQLite.seed_db import reset_and_seed
    await reset_and_seed()
    print("Database created and seeded.")


if __name__ == "__main__":
    init_rag()
    asyncio.run(init_sql())
    uvicorn.run("app.app:app", host="0.0.0.0", port=8000, reload=True)