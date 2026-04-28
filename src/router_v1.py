class QueryRouter:

    def classify(self, query: str) -> str:
        query_lower = query.lower()

        structured_keywords = [
            "who", "list", "status", "assigned", "manager",
            "employee", "ticket", "department"
        ]

        hybrid_keywords = [
            "related", "reference", "associated",
            "impact", "affect", "linked"
        ]

        # Hybrid first (most specific)
        if any(word in query_lower for word in hybrid_keywords):
            return "hybrid"

        # Structured
        if any(word in query_lower for word in structured_keywords):
            return "structured"

        # Default to semantic
        return "semantic"