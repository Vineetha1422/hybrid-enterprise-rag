import requests

class ClassifyQuery:

    def classify_query(self, query: str) -> str:
        prompt = f"""You are a query classifier for an enterprise knowledge system.

    Classify the query into EXACTLY one of these three categories:

    - structured : asks about specific employees, ticket IDs, team members, 
               managers, direct reports, ticket priority/status,
               or cross-team ticket relationships
    - semantic   : asks about policies, documentation, architecture, 
                definitions, or procedures
    - hybrid     : requires BOTH employee/ticket data AND policy/documentation 
                (e.g. "what policies apply to the DevOps team?",
                     "which tickets relate to StreamAPI security?",
                     "what governance applies to DataLake Pro?", etc.)

    Reply with ONE word only. No explanation. No punctuation.

    Query: {query}
    """
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2",
                "prompt": prompt,
                "stream": False
            }
        )

        label = response.json()["response"].strip().lower()

        # Safety fallback - if LLM returns something unexpected
        if label not in ("structured", "semantic", "hybrid"):
            return "hybrid"
        
        return label
