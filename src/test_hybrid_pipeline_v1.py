from hybrid_pipeline_v1 import HybridPipeline

pipeline = HybridPipeline()

query = "Which documents reference TECH-42? Need the document name and the section information"
response = pipeline.handle_query(query)

print("\n--- FINAL ANSWER ---\n")
print(response["answer"])