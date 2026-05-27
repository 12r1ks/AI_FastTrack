import faiss

from pathlib import Path
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings, StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.faiss import FaissVectorStore

SEED_PATH = "app/rag/seed_parking_info.md"
INDEX_DIR = "app/db/faiss_vector_store/"

def load_documents(path: str):
    input_path = Path(path)
    if not input_path.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    return SimpleDirectoryReader(input_files=[str(input_path)]).load_data()

def chunk_documents(documents):
    return MarkdownNodeParser().get_nodes_from_documents(documents)

def build_store_index(nodes, persist_dir=INDEX_DIR):
    faiss_index = faiss.IndexFlatL2(384)
    vector_store = FaissVectorStore(faiss_index)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex(
        nodes=nodes,
        storage_context=storage_context,
    )
    index.storage_context.persist(persist_dir=persist_dir)
    return index

if __name__ == "__main__":
    Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    print("\nLoading documents...")
    documents = load_documents(SEED_PATH)
    print("\nChunking documents...")
    nodes = chunk_documents(documents)
    print(f"\nProcessing {len(nodes)} nodes...")
    print("\nBuilding index...")
    build_store_index(nodes)
    print("\nIndex built and persisted successfully.")


