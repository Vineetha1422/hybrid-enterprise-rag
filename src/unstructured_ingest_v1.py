import os
import chromadb
from pathlib import Path 
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

import yaml
import re
from datetime import date, datetime

class UnstructuredIngestion:

    def __init__(self, kb_path : str, persist_dir : str = "vector_store"):
        self.kb_path = Path(kb_path)
        self.persist_dir = persist_dir

        #Load embedding model
        self.embedding_model = SentenceTransformer("all-mpnet-base-v2")

        #Chroma Client
        self.chroma_client = chromadb.Client(
            settings = chromadb.config.Settings(
                persist_directory = self.persist_dir,
                is_persistent = True
            )
        )

        #Reset collection to avoid duplicates
        try:
            self.chroma_client.delete_collection("enterprise_kb")
        except:
            pass
        
        #create new collection
        self.collection = self.chroma_client.create_collection(
            name = "enterprise_kb"
        )
        
        #Two stage chunking splitter (token aware)
        self.secondary_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100
        )
    
    def extract_metadata(self, text):
        pattern = r"^---\n(.*?)\n---\n"
        match = re.search(pattern, text, re.DOTALL)

        if match:
            metadata_block = match.group(1)
            metadata = yaml.safe_load(metadata_block)
            content = text[match.end():]
            return metadata, content

        return {}, text
    
    def normalize_metadata(self, metadata: dict):
        normalized = {}

        for key, value in metadata.items():
            if isinstance(value, (date, datetime)):
                normalized[key] = value.isoformat()
            elif isinstance(value, list):
                # Ensure list items are simple types
                normalized[key] = [
                    v.isoformat() if isinstance(v, (date, datetime)) else v
                    for v in value
                ]
            else:
                normalized[key] = value

        return normalized
    
    def infer_document_category(self, filename: str):
        name = filename.lower()

        if "policy" in name:
            return "policy"
        if "architecture" in name:
            return "architecture"
        if "roadmap" in name:
            return "roadmap"
        if "runbook" in name or "sop" in name:
            return "operations"
        if "metrics" in name:
            return "analytics"
        return "general"

    
    # def chunk_content(self, text: str, chunk_size: int = 800, overlap: int = 100):
    #     chunks = []
    #     start = 0

    #     while start < len(text):
    #         end = start + chunk_size
    #         chunk = text[start:end]
    #         chunks.append(chunk)
    #         start += chunk_size - overlap

    #     return chunks

    def chunk_markdown(self, text:str):
        headers_to_split_on = [
            ('#', "document title"),
            ('##', 'section'),
            ('###', 'subsection'),
            ('####', 'subsubsection')
        ]

        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on = headers_to_split_on
        )

        splits = splitter.split_text(text)
        chunks  = []
        for split in splits:
            section_text = split.page_content
            section_metadata = split.metadata
            sub_chunks = self.secondary_splitter.split_text(section_text)

            for sub_chunk in sub_chunks:
                chunks.append({
                    "content": sub_chunk,
                    "metadata": section_metadata
                })
        
        return chunks


    def ingest(self):
        base_path = self.kb_path / "unstructured"
        doc_id = 0

        for root, _, files in os.walk(base_path):
            for file in files:
                if file.endswith(".md"):
                    file_path = Path(root) / file

                    with open(file_path, "r", encoding = "utf-8") as f:
                        raw_text = f.read()
                    
                    #Extract document metadata                       
                    metadata, content = self.extract_metadata(raw_text)
                    document_category = self.infer_document_category(file)
                    
                    document_metadata = {
                        **metadata,
                        "document_category" : document_category,
                        "source" : file,
                        "file_path" : str(file_path)
                    }
                    document_metadata = self.normalize_metadata(document_metadata)

                    #Basic Chunking
                    chunks = self.chunk_markdown(content)

                    #Embedding using HF
                    texts = [c["content"] for c in chunks]
                    embeddings = self.embedding_model.encode(texts)

                    #Store in collection
                    for chunk, embedding in zip(chunks, embeddings):
                        metadata = {
                            **document_metadata,
                            **chunk["metadata"]  # section metadata
                        }
                        self.collection.add(
                            documents = [chunk['content']],
                            embeddings = [embedding.tolist()],
                            metadatas = [metadata],
                            ids = [f"doc_{doc_id}"]
                        )
                        doc_id += 1

        print(f"Ingestion complete. {doc_id} chunks are stored.")            