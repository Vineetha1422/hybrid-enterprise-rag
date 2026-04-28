from hybrid_pipeline_v2 import HybridPipelineFinal
from router_v2 import ClassifyQuery

import time

pipeline = HybridPipelineFinal()
router = ClassifyQuery()

# -------------------------------------------------------
# Test Set
# -------------------------------------------------------
TEST_CASES = [
    # Structured queries
    {
        "query": "List all members of the DevOps team",
        "query_type": "structured",
        "expected_docs": [],  # structured path doesn't retrieve docs
        "expected_keywords": ["Lucia Ferreira", "Omar Shaikh"]
    },
    {
        "query": "Show me all blocked tickets",
        "query_type": "structured",
        "expected_docs": [],
        "expected_keywords": ["TECH-13", "TECH-67", "TECH-69"]
    },
    {
        "query": "List all critical tickets",
        "query_type": "structured",
        "expected_docs": [],
        "expected_keywords": ["Critical"]
    },
    {
        "query": "Tell me about ticket TECH-42",
        "query_type": "structured",
        "expected_docs": [],
        "expected_keywords": ["TECH-42"]
    },

    # Semantic queries
    {
        "query": "What is our remote work policy?",
        "query_type": "semantic",
        "expected_docs": ["04_hr_remote_work_policy.md"],
        "expected_keywords": ["remote", "VPN", "policy"]
    },
    {
        "query": "What does the security policy say about access control?",
        "query_type": "semantic",
        "expected_docs": ["06_security_access_control_policy.md"],
        "expected_keywords": ["access", "security", "policy"]
    },
    {
        "query": "What are the engineering architecture decisions?",
        "query_type": "semantic",
        "expected_docs": ["01_engineering_architecture.md"],
        "expected_keywords": ["architecture", "engineering"]
    },
    {
        "query": "What metrics are defined in the analytics guide?",
        "query_type": "semantic",
        "expected_docs": ["08_analytics_metrics_definition_guide.md"],
        "expected_keywords": ["metrics", "analytics"]
    },

    # Hybrid queries
    {
        "query": "What security policies apply to StreamAPI?",
        "query_type": "hybrid",
        "expected_docs": ["06_security_access_control_policy.md"],
        "expected_keywords": ["StreamAPI", "security", "SEC-ACCESS-001"]
    },
    {
        "query": "What governance policies impact Snowflake usage?",
        "query_type": "hybrid",
        "expected_docs": ["02_data_governance_policy.md"],
        "expected_keywords": ["Snowflake", "governance", "data"]
    },
    {
        "query": "Which blocked tickets relate to cross-team initiatives?",
        "query_type": "hybrid",
        "expected_docs": [],
        "expected_keywords": ["TECH-67", "TECH-68", "cross-team"]
    },
    {
        "query": "What deployment procedures exist for DataLake Pro?",
        "query_type": "hybrid",
        "expected_docs": ["05_devops_runbook.md"],
        "expected_keywords": ["DataLake", "deployment"]
    },
]


# -------------------------------------------------------
# Scorers
# -------------------------------------------------------

def score_retrieval(results: list, expected_docs: list) -> float:
    """Check if expected docs appear in retrieved chunk metadata."""
    if not expected_docs:
        return 1.0  # structured path — no retrieval to score

    retrieved_sources = [
        r["metadata"].get("source", "") 
        for r in results
    ]

    found = sum(
        1 for doc in expected_docs
        if any(doc in source for source in retrieved_sources)
    )

    return round(found / len(expected_docs), 2)


def score_answer(answer: str, expected_keywords: list) -> float:
    """Check if expected keywords appear in the LLM answer."""
    if not expected_keywords:
        return 1.0

    answer_lower = answer.lower()
    found = sum(
        1 for kw in expected_keywords
        if kw.lower() in answer_lower
    )

    return round(found / len(expected_keywords), 2)


# -------------------------------------------------------
# Runner
# -------------------------------------------------------

def run_eval():
    print("\n" + "="*70)
    print("EVALUATION HARNESS — Hybrid Enterprise RAG")
    print("="*70)

    retrieval_scores = []
    answer_scores = []

    for i, test in enumerate(TEST_CASES):
        query = test["query"]
        print(f"\n[{i+1}/{len(TEST_CASES)}] {query}")
        print(f"  Type: {test['query_type']}")

        # Run pipeline
        #query_type = router.classify_query(query)

        # Use the labeled type from test case:
        query_type = test["query_type"]
        print(f"[Router] Using labeled type: {query_type}")
        
        # Get retrieval results for scoring (semantic/hybrid only)
        if query_type != "structured":
            raw_results = pipeline.retrieve_and_rerank(query)
            r_score = score_retrieval(raw_results, test["expected_docs"])
        else:
            raw_results = []
            r_score = 1.0  # no retrieval to evaluate

        # Get final answer
        result = pipeline.handle_query(query)
        answer = result.get("answer", "")
        print(f"  DEBUG answer preview: {answer[:100]}") 

        a_score = score_answer(answer, test["expected_keywords"])

        retrieval_scores.append(r_score)
        answer_scores.append(a_score)

        # Per query output
        print(f"  Retrieval Score : {r_score}")
        print(f"  Answer Score    : {a_score}")

        if r_score < 1.0:
            retrieved = [r["metadata"].get("source","?") for r in raw_results]
            print(f"Expected docs : {test['expected_docs']}")
            print(f"Got docs      : {retrieved}")

        if a_score < 1.0:
            missing = [
                kw for kw in test["expected_keywords"]
                if kw.lower() not in answer.lower()
            ]
            print(f"Missing keywords: {missing}")

        time.sleep(3)

    # -------------------------------------------------------
    # Final Report
    # -------------------------------------------------------
    avg_retrieval = round(sum(retrieval_scores) / len(retrieval_scores) * 100, 1)
    avg_answer = round(sum(answer_scores) / len(answer_scores) * 100, 1)

    print("\n" + "="*70)
    print("FINAL REPORT")
    print("="*70)
    print(f"  Retrieval Precision : {avg_retrieval}%")
    print(f"  Answer Quality      : {avg_answer}%")
    print(f"  Queries evaluated   : {len(TEST_CASES)}")

    # Breakdown by query type
    for qtype in ["structured", "semantic", "hybrid"]:
        indices = [i for i, t in enumerate(TEST_CASES) if t["query_type"] == qtype]
        r_avg = round(sum(retrieval_scores[i] for i in indices) / len(indices) * 100, 1)
        a_avg = round(sum(answer_scores[i] for i in indices) / len(indices) * 100, 1)
        print(f"\n  [{qtype.upper()}]")
        print(f"    Retrieval : {r_avg}%")
        print(f"    Answer    : {a_avg}%")

    print("\n" + "="*70)


if __name__ == "__main__":
    run_eval()