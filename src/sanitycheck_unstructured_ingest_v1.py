import chromadb

client = chromadb.Client(
    settings=chromadb.config.Settings(
        persist_directory="vector_store",
        is_persistent=True
    )
)

collection = client.get_collection("enterprise_kb")

results = collection.get(limit=1)

print("Sample document:\n")
print(results["documents"][0][:500])

print("\nSample metadata:\n")
print(results["metadatas"][0])