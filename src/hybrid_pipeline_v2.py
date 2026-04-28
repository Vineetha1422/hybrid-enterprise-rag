from retriever_v1 import SemanticRetreiver
from bm25_retriever import BM25RetrieverCustom
from structured_store import StructuredStore
from answer_generator import AnswerGenerator
from reranker import Reranker
from router_v2 import ClassifyQuery

import re

class HybridPipelineFinal:

    def __init__(self):
        self.structured_store = StructuredStore("knowledge_base")
        self.vector_retriever = SemanticRetreiver()
        self.bm25_retriever = BM25RetrieverCustom()
        self.generator = AnswerGenerator()
        self.reranker = Reranker()
        self.router = ClassifyQuery()

    def _extract_ticket_id(self, query):
        match = re.search(r"TECH-\d+", query.upper())
        return match.group(0) if match else None

    def _extract_name(self, query: str) -> str | None:
        # Match two consecutive capitalised words - e.g. "James Thornton"
        match = re.search(r"[A-Z][a-z]+\s[A-Z][a-z]+", query)
        return match.group(0) if match else None
    
    def get_cross_team_tickets(self):
        return self.tickets[
            self.tickets["title"].str.contains("Cross-team|Cross-product", case=False, na=False)
        ]
    
    def structured_path(self, query: str):
        q = query.lower()

        # Ticket ID lookup
        if "tech-" in q:
            ticket_id = self._extract_ticket_id(query)
            data = self.structured_store.get_ticket_by_id(ticket_id)
            if data.empty:
                return {"type": "structured", "query_intent": "ticket_lookup",
                        "data": f"No ticket with ID '{ticket_id}' found."}
            return {"type": "structured", "query_intent": "ticket_lookup",
                    "data": data.to_dict(orient="records")}

        # Direct reports
        if "reports to" in q or "direct reports" in q:
            name = self._extract_name(query)
            if not name:
                return {"type": "structured", "query_intent": "direct_reports",
                        "data": "Could not identify a name in your query."}
            data = self.structured_store.get_direct_reports(name)
            if data.empty:
                return {"type": "structured", "query_intent": "direct_reports",
                        "data": f"No employee named '{name}' found, or they have no direct reports."}
            return {"type": "structured", "query_intent": "direct_reports",
                    "data": data.to_dict(orient="records")}

        # Team members
        if "team" in q and any(t in q for t in ["engineering", "data", "product", "hr", "devops"]):
            for team in ["engineering", "data", "product", "hr", "devops"]:
                if team in q:
                    data = self.structured_store.get_team_members(team)
                    if data.empty:
                        return {"type": "structured", "query_intent": "team_lookup",
                                "data": f"No employees found in the '{team}' team."}
                    return {"type": "structured", "query_intent": "team_lookup",
                            "data": data.to_dict(orient="records")}

        # Critical tickets
        if "critical" in q:
            data = self.structured_store.get_critical_tickets()
            if data.empty:
                return {"type": "structured", "query_intent": "priority_filter",
                        "data": "No critical tickets found."}
            return {"type": "structured", "query_intent": "priority_filter",
                    "data": data.to_dict(orient="records")}

        # Blocked tickets
        if "blocked" in q:
            data = self.structured_store.get_blocked_tickets()
            if data.empty:
                return {"type": "structured", "query_intent": "blocked_tickets",
                        "data": "No blocked tickets found."}
            # Only send essential fields to avoid overwhelming the LLM
            trimmed = data[["ticket_id", "title", "priority", "assignee", "team", "dependencies"]].to_dict(orient="records")
            return {"type": "structured", "query_intent": "blocked_tickets", "data": trimmed}
        
        #Cross team tickets
        if "cross-team" in q or "cross team" in q:
            data = self.structured_store.get_cross_team_tickets()
            if data.empty:
                return {"type": "structured", "query_intent": "cross_team",
                        "data": "No cross-team tickets found."}
            trimmed = data[["ticket_id", "title", "priority", "assignee", "team"]].to_dict(orient="records")
            return {"type": "structured", "query_intent": "cross_team", "data": trimmed}

        # Priority filter
        for priority in ["high", "medium", "low"]:
            if priority in q:
                data = self.structured_store.get_tickets_by_priority(priority)
                if data.empty:
                    return {"type": "structured", "query_intent": "priority_filter",
                            "data": f"No '{priority}' priority tickets found."}
                return {"type": "structured", "query_intent": "priority_filter",
                        "data": data.to_dict(orient="records")}

        # Employee by name
        name = self._extract_name(query)
        if name:
            data = self.structured_store.get_employee_by_name(name)
            if data.empty:
                return {"type": "structured", "query_intent": "employee_lookup",
                        "data": f"No employee named '{name}' found in the directory."}
            return {"type": "structured", "query_intent": "employee_lookup",
                    "data": data.to_dict(orient="records")}

        return {"type": "structured", "query_intent": "unknown",
                "data": "Could not match your query to any structured data pattern."}

    def hybrid_retrieve(self, query):
        vector_results = self.vector_retriever.semanticSearch(query, top_k=15)
        bm25_results = self.bm25_retriever.search(query)

        fused_scores = {}
        k = 60

        # vector ranking
        for rank, r in enumerate(vector_results):
            key = r["document"]

            if key not in fused_scores:
                fused_scores[key] = {"data": r, "score": 0}

            fused_scores[key]["score"] += 1 / (k + rank + 1)

        # bm25 ranking
        for rank, r in enumerate(bm25_results):
            key = r["document"]

            if key not in fused_scores:
                fused_scores[key] = {"data": r, "score": 0}

            fused_scores[key]["score"] += 1 / (k + rank + 1)

        fused = sorted(
            fused_scores.values(),
            key=lambda x: x["score"],
            reverse=True
        )

        return [f["data"] for f in fused[:20]]

    def retrieve_and_rerank(self, query):
        results = self.hybrid_retrieve(query)

        if not results:
            return []

        ticket = self._extract_ticket_id(query)

        if ticket:
            for r in results:
                if ticket in r["document"]:
                    r["score"] = r.get("score",0) + 1
        reranked = self.reranker.rerank(query, results)
        return reranked[:5]
    
    def handle_query(self, query: str, format_output: bool = True):
        query_type = self.router.classify_query(query)
        print(f"[Router] Query classified as: {query_type}")

        if query_type == "structured":
            result = self.structured_path(query)
            if hasattr(result["data"], "to_dict"):
                result["data"] = result["data"].to_dict(orient="records")

            if format_output:
                # Send through LLM for natural language response
                context = [f"Structured data result: {result['data']}"]
                return self.generator.generate(query, context)
            
            # Return raw data directly
            return result

        results = self.retrieve_and_rerank(query)
        if not results:
            return {
                "prompt_used": None,
                "answer": "No relevant documents found for your query."
            }
        context = [
            f"[Source: {r['metadata'].get('source', 'unknown')} | "
            f"Section: {r['metadata'].get('section', 'N/A')}]\n{r['document']}"
            for r in results
        ]
        return self.generator.generate(query, context)


