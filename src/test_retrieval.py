from retriever_v1 import SemanticRetreiver
from reranker import Reranker

retriever = SemanticRetreiver()
reranker = Reranker()

query = "What are the data retention policies?"

results = retriever.semanticSearch(query, 15, None)

reranked_docs = reranker.rerank(query, results["documents"])

top_docs = reranked_docs[:5]
count = 0
for i in top_docs:
    print(f"Document {count} \n")
    print("-" * 30)
    print(i)
    count += 1

# for i, doc in enumerate(results["documents"]):
#     print("\n--- Result", i+1, "---")
#     print("Distance:", results["distances"][i])
#     print("Metadata:", results["metadatas"][i])
#     print("Preview:", doc[:400])