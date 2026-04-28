import chromadb
from sentence_transformers import SentenceTransformer

class SemanticRetreiver:
    
    def __init__(self, persist_dir = "vector_store"):
        self.embedding_model = SentenceTransformer("all-mpnet-base-v2")

        self.chroma_client = chromadb.Client(
            settings = chromadb.config.Settings(
                persist_directory = persist_dir,
                is_persistent = True
            )
        )

        try:
            self.collection = self.chroma_client.get_collection("enterprise_kb")
        except Exception:
            raise RuntimeError(
                "ChromaDB collection 'enterprise_kb' not found. "
                "Run unstructured_ingest_v1.py first to build the vector store."
            )

    def semanticSearch(self, query:str, top_k:int = 5, filters:dict = None):
        query_embedding = self.embedding_model.encode(query).tolist()

        results = self.collection.query(
            query_embeddings = [query_embedding],
            n_results = top_k,
            where = filters
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        structured_results = []

        for doc, meta, dist in zip(documents, metadatas, distances):
            structured_results.append({
                "document": doc,
                "metadata": meta,
                "score": 1 - dist   # convert distance → similarity
            })

        return structured_results