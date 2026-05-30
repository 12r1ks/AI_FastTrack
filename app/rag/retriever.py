from llama_index.core import StorageContext, load_index_from_storage, Settings
from llama_index.vector_stores.faiss import FaissVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

PERSIST_DIR = "app/db/faiss_vector_store/"

def load_index(persist_dir: str = PERSIST_DIR):
    Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    vector_store = FaissVectorStore.from_persist_dir(persist_dir)
    storage_context = StorageContext.from_defaults(
        vector_store=vector_store,
        persist_dir=persist_dir,
    )
    return load_index_from_storage(storage_context=storage_context)

_index = None

def _get_index():
    global _index
    if _index is None:
        _index = load_index()
    return _index

def retrieve(query: str, top_k: int = 4) -> list[str]:
    retriever = _get_index().as_retriever(similarity_top_k=top_k)
    return [f"Retrieved Result {i}: {node.node.get_content()}" for i, node in enumerate(retriever.retrieve(query), start=1)]



if __name__ == "__main__":
    s = retrieve("Where can I park near the city center?")
    print(s)