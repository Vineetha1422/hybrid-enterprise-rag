from structured_store import StructuredStore

store = StructuredStore("knowledge_base")

print("\nDirect reports of Daniel Cruz:")
print(store.get_direct_reports("Daniel Cruz"))

print("\nCritical tickets:")
print(store.get_critical_tickets()[["ticket_id", "title", "status"]])

print("\nBlocked tickets:")
print(store.get_blocked_tickets()[["ticket_id", "title"]])