from hybrid_pipeline_v2 import HybridPipelineFinal

pipeline = HybridPipelineFinal()

# # Should hit structured_path → direct_reports
# response = pipeline.handle_query("Who reports to James Thornton?")
# print("\n--- FINAL ANSWER ---\n")
# print(response["answer"])

# # Should hit structured_path → team_lookup  
# response = pipeline.handle_query("List all members of the DevOps team")
# print("\n--- FINAL ANSWER ---\n")
# print(response["answer"])

# # Should hit structured_path → blocked_tickets
# response = pipeline.handle_query("Show me all blocked tickets")
# print("\n--- FINAL ANSWER ---\n")
# print(response["answer"])

# Should hit semantic
response = pipeline.handle_query("What is our remote work policy?")
print("\n--- FINAL ANSWER ---\n")
print(response["answer"])

# Should hit hybrid
response = pipeline.handle_query("What security policies apply to StreamAPI?")
print("\n--- FINAL ANSWER ---\n")
print(response["answer"])

