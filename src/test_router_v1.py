from router_v1 import QueryRouter

router = QueryRouter()

queries = [
    "Who manages Laura Hensley?",
    "What are the data retention policies?",
    "Which documents reference TECH-42?"
]

for q in queries:
    print(q, "→", router.classify(q))