from sentence_transformers import CrossEncoder

class Reranker:
    def __init__(self):
        self.model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    def rerank(self, query, results):
        pairs = [[query, r["document"]] for r in results]

        scores = self.model.predict(pairs)

        for r, s in zip(results, scores):
            r["rerank_score"] = float(s)

        ranked = sorted(
            results,
            key=lambda x: x["rerank_score"],
            reverse=True
        )

        return ranked