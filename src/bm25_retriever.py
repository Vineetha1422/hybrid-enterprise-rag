from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
import chromadb


class BM25RetrieverCustom:

    def __init__(self, persist_dir="vector_store"):

        client = chromadb.Client(
            settings=chromadb.config.Settings(
                persist_directory=persist_dir,
                is_persistent=True
            )
        )

        collection = client.get_collection("enterprise_kb")

        data = collection.get()

        documents = data["documents"]
        metadatas = data["metadatas"]

        docs = [
            Document(page_content=d, metadata=m)
            for d, m in zip(documents, metadatas)
        ]

        self.retriever = BM25Retriever.from_documents(docs)
        self.retriever.k = 15

    def search(self, query):
        results = self.retriever.invoke(query)
        formatted = []

        for r in results:
            formatted.append({
                "document": r.page_content,
                "metadata": r.metadata
            })

        return formatted