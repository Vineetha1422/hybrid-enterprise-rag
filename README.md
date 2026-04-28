# Hybrid Enterprise RAG System  
📌 Project Type: AI System Design + Retrieval-Augmented Generation  

---

## 🔍 Overview  
This project builds a hybrid RAG system for enterprise knowledge bases by combining structured (CSV) and unstructured (Markdown) data.  

Supports:
- Structured queries (employee hierarchy, ticket lookup)  
- Unstructured queries (policies, documentation)  
- Hybrid queries (cross-referencing both)  

---

## 🛠️ Tech Stack  

### 📦 Data & Storage  
- Pandas  
- ChromaDB  

### 🔎 Retrieval  
- HuggingFace Embeddings (all-mpnet-base-v2)  
- BM25 (keyword search)  
- Cross-Encoder (reranking)  
- Reciprocal Rank Fusion (RRF)  

### 🧠 LLM  
- Ollama (llama3.2)  

### ⚙️ Processing  
- Python 3.11  
- LangChain (chunking)  

---

## 📂 Dataset  
Synthetic enterprise knowledge base:
- Employee Directory (CSV)  
- Jira Tickets (CSV)  
- 8+ Markdown documents (Engineering, Data, HR, DevOps, Security)  

Includes metadata:
- Department  
- Owner  
- Version  
- Related tickets  

---

## 📂 Workflow  

### 1. Structured Layer  
- Employee hierarchy  
- Ticket filtering  
- Dependency tracking  

### 2. Unstructured Ingestion  
- Markdown parsing + metadata  
- Header-based chunking  
- Embedding → ChromaDB  

### 3. Retrieval Pipeline  
- Vector search + BM25  
- RRF fusion  
- Cross-encoder reranking  

### 4. Response Generation  
- Context building  
- LLM-based answer (Ollama)  

---

## 📈 Key Learnings  
- Hybrid retrieval > pure vector search  
- Chunking impacts performance heavily  
- Reranking improves precision  
- Metadata enables better filtering  

---

## 🚀 Future Work  
- UI (Streamlit)  
- Logging + evaluation improvements  
- Better query classification  
