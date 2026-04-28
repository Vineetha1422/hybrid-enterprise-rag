import requests
from answer_generator import AnswerGenerator
from hybrid_pipeline_v1 import HybridPipeline

#Test Ollama
response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "llama3.2",
        "prompt": "Say hello in one sentence.",
        "stream": False
    }
)

print(response.json()['response'])

#Test Answer Generator
generator = AnswerGenerator()

query = "What is the raw data retention period?"

context_blocks = [
    """
    Tier 1 Raw Layer Retention: 5 years.
    Tier 2 Raw Layer Retention: 3 years.
    """
]

response = generator.generate(query, context_blocks)

print("\n--- ANSWER ---\n")
print(response["answer"])

#Test Hybrid Pipeline
pipeline = HybridPipeline()

query = "What are the data retention policies?"

response = pipeline.handle_query(query)

print("\n--- FINAL ANSWER ---\n")
print(response["answer"])