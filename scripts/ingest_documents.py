#!/usr/bin/env python
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
"""
Script to ingest documents into the vector database
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.document_processor import DocumentProcessor
from src.services.vector_store import get_vector_store

def main():
    """Ingest all documents from the data/documentos directory"""
    print("=" * 60)
    print("SECS Chatbot - Document Ingestion")
    print("=" * 60)
    
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(base_dir, "data", "documentos")
    
    if not os.path.exists(docs_dir):
        print(f"ERROR: Documents directory not found: {docs_dir}")
        return 1
    
    print(f"\nProcessing documents from: {docs_dir}\n")
    
    # Initialize processor and vector store
    processor = DocumentProcessor()
    vector_store = get_vector_store()
    
    # Ingest documents
    print("Step 1: Reading documents...")
    documents = processor.ingest_directory(docs_dir)
    print(f"Found {len(documents)} documents\n")
    
    if not documents:
        print("No documents found to process.")
        return 0
    
    # Process each document
    print("Step 2: Chunking documents...")
    all_chunks = []
    for doc in documents:
        chunks = processor.chunk_document(doc)
        all_chunks.append(chunks)
        print(f"  - {doc.titulo}: {len(chunks)} chunks")
    
    print(f"\nTotal chunks: {sum(len(c) for c in all_chunks)}\n")
    
    # Add to vector store
    print("Step 3: Generating embeddings and storing...")
    vector_store.add_documents(documents, all_chunks)
    
    # Show stats
    print("\n" + "=" * 60)
    print("Ingestion Complete!")
    print("=" * 60)
    stats = vector_store.get_stats()
    print(f"\nDatabase Statistics:")
    print(f"  Total documents: {stats['num_documentos']}")
    print(f"  Total chunks: {stats['num_chunks']}")
    print(f"\nDocuments by type:")
    for tipo, count in stats['documentos_por_tipo'].items():
        print(f"  - {tipo}: {count}")
    
    print("\n✅ Documents successfully ingested into the database!")
    print(f"Database location: {vector_store.db_path}\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
