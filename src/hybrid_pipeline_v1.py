from router_v1 import QueryRouter
from retriever_v1 import SemanticRetreiver
from structured_store import StructuredStore
from answer_generator import AnswerGenerator
from reranker import Reranker

import re

class HybridPipeline:

    def __init__(self):
        self.router = QueryRouter()
        self.retriever = SemanticRetreiver()
        self.structured_store = StructuredStore("knowledge_base")
        self.generator = AnswerGenerator()
        self.reranker = Reranker()

    def _extract_ticket_id(self, query):
        match = re.search(r"TECH-\d+", query.upper())
        return match.group(0) if match else None
    
    def structured_path(self, query:str):
        # example pattern
        if "tech-" in query.lower():
            ticket_id = self._extract_ticket_id(query)
            ticket_data = self.structured_store.get_ticket_by_id(ticket_id)

            return {
                "type": "structured",
                "data": ticket_data
            }

        return {"type": "structured", "data": "No match found."}

    def semantic_path(self, query:str):
        results = self.retriever.semanticSearch(query, top_k = 3)
        reranked = self.reranker.rerank(query, results)
        top_results = reranked[:5]
        return top_results

    def hybrid_path(self, query:str):
        ticket_id = self._extract_ticket_id(query)
        filters = None

        if ticket_id:
            filters = {
                "related_tickets": {
                    "$contains": ticket_id
                }
            }

        #Dense retrieval
        results = self.retriever.semanticSearch(
            query = query,
            top_k = 15,
            filters = filters)

        #Rerank
        reranked = self.reranker.rerank(query, results)

        #Top n
        return reranked[:5]

    def handle_query(self, query:str):
        query_type = self.router.classify(query)

        if query_type == "structured":
            result = self.structured_path(query)
            context = [str(result['data'])]
        
        elif query_type == "semantic":
            result = self.semantic_path(query)
            context = [f"Metadata : {r['metadata']}, Content : {r['document']}" for r in result]

        elif query_type == "hybrid":
            result = self.hybrid_path(query)
            context = [f"Metadata : {r['metadata']}, Content : {r['document']}" for r in result]
        
        return self.generator.generate(query, context)


