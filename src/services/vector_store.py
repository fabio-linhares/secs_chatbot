#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Armazenamento e busca vetorial
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Armazenamento e busca vetorial
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import sqlite3
import numpy as np
import json
from typing import List, Dict, Optional, Tuple
from src.config import settings
from src.services.document_processor import Document, Chunk
from src.services.embeddings import get_embedding_service

class VectorStore:
    """Stores and searches document chunks"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.db_path_resolved
        self.embedding_service = get_embedding_service()
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            
            # Documentos table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS documentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT NOT NULL,
                    titulo TEXT NOT NULL,
                    numero TEXT,
                    data TEXT,
                    conselho TEXT,
                    caminho TEXT NOT NULL,
                    hash_sha256 TEXT UNIQUE,
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Chunks table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    documento_id INTEGER NOT NULL,
                    conteudo TEXT NOT NULL,
                    embedding BLOB,
                    metadata TEXT,
                    posicao INTEGER,
                    FOREIGN KEY (documento_id) REFERENCES documentos(id)
                )
            """)
            
            # Index for faster searches
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_documento 
                ON chunks(documento_id)
            """)
            
            conn.commit()
    
    def add_documents(self, documents: List[Document], chunks_per_doc: List[List[Chunk]]):
        """Add documents and their chunks to the database"""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            
            for doc, chunks in zip(documents, chunks_per_doc):
                # Check if document already exists
                cur.execute(
                    "SELECT id FROM documentos WHERE hash_sha256 = ?",
                    (doc.hash_sha256,)
                )
                existing = cur.fetchone()
                
                if existing:
                    print(f"Document {doc.titulo} already exists, skipping...")
                    continue
                
                # Insert document
                cur.execute("""
                    INSERT INTO documentos (tipo, titulo, numero, data, conselho, caminho, hash_sha256)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (doc.tipo, doc.titulo, doc.numero, doc.data, doc.conselho, doc.caminho, doc.hash_sha256))
                
                doc_id = cur.lastrowid
                
                # Generate embeddings for chunks
                chunk_texts = [chunk.conteudo for chunk in chunks]
                embeddings = self.embedding_service.batch_embed(chunk_texts)
                
                # Insert chunks
                for chunk, embedding in zip(chunks, embeddings):
                    embedding_blob = embedding.tobytes()
                    metadata_json = json.dumps(chunk.metadata, ensure_ascii=False)
                    
                    cur.execute("""
                        INSERT INTO chunks (documento_id, conteudo, embedding, metadata, posicao)
                        VALUES (?, ?, ?, ?, ?)
                    """, (doc_id, chunk.conteudo, embedding_blob, metadata_json, chunk.posicao))
                
                print(f"Added document: {doc.titulo} with {len(chunks)} chunks")
            
            conn.commit()
    
    def search(self, query: str, k: int = 5, user_id: Optional[str] = None) -> List[Dict]:
        """
        Search for similar chunks with user-scoped permissions.
        
        Args:
            query: Search query
            k: Number of results to return
            user_id: User ID for permission filtering. If None, returns only global docs.
        
        Returns:
            List of chunks with similarity scores, filtered by permissions
        """
        # Generate query embedding
        query_embedding = self.embedding_service.generate_embedding(query)
        
        # Build query with permission filter
        if user_id:
            # User sees: global docs + their private docs
            permission_filter = """
                WHERE d.is_global = 1 OR d.user_id = ?
            """
            params = (user_id,)
        else:
            # No user: only global docs
            permission_filter = """
                WHERE d.is_global = 1
            """
            params = ()
        
        # Get all chunks with permission filter
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            query_sql = f"""
                SELECT c.id, c.conteudo, c.embedding, c.metadata, c.posicao,
                       d.tipo, d.titulo, d.numero, d.data, d.conselho,
                       d.user_id, d.is_global
                FROM chunks c
                JOIN documentos d ON c.documento_id = d.id
                {permission_filter}
            """
            
            cur.execute(query_sql, params)
            
            results = []
            for row in cur.fetchall():
                chunk_id, conteudo, embedding_blob, metadata_json, posicao, tipo, titulo, numero, data, conselho, doc_user_id, is_global = row
                
                # Deserialize embedding
                embedding = np.frombuffer(embedding_blob, dtype=np.float32)
                
                # Calculate cosine similarity
                similarity = np.dot(query_embedding, embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
                )
                
                metadata = json.loads(metadata_json) if metadata_json else {}
                
                results.append({
                    'chunk_id': chunk_id,
                    'conteudo': conteudo,
                    'similarity': float(similarity),
                    'metadata': metadata,
                    'tipo': tipo,
                    'titulo': titulo,
                    'numero': numero,
                    'data': data,
                    'conselho': conselho,
                    'posicao': posicao,
                    'user_id': doc_user_id,
                    'is_global': bool(is_global)
                })
            
            # Sort by similarity and return top k
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:k]
    
    def search_by_embedding(self, embedding: np.ndarray, k: int = 5, user_id: Optional[str] = None) -> List[Dict]:
        """
        Search using pre-computed embedding (for HyDE).
        
        Args:
            embedding: Pre-computed query embedding
            k: Number of results to return
            user_id: User ID for permission filtering
        
        Returns:
            List of chunks with similarity scores
        """
        # Build query with permission filter
        if user_id:
            permission_filter = """
                WHERE d.is_global = 1 OR d.user_id = ?
            """
            params = (user_id,)
        else:
            permission_filter = """
                WHERE d.is_global = 1
            """
            params = ()
        
        # Get all chunks with permission filter
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            query_sql = f"""
                SELECT c.id, c.conteudo, c.embedding, c.metadata, c.posicao,
                       d.tipo, d.titulo, d.numero, d.data, d.conselho,
                       d.user_id, d.is_global
                FROM chunks c
                JOIN documentos d ON c.documento_id = d.id
                {permission_filter}
            """
            
            cur.execute(query_sql, params)
            
            results = []
            for row in cur.fetchall():
                chunk_id, conteudo, embedding_blob, metadata_json, posicao, tipo, titulo, numero, data, conselho, doc_user_id, is_global = row
                
                # Deserialize embedding
                chunk_embedding = np.frombuffer(embedding_blob, dtype=np.float32)
                
                # Calculate cosine similarity with provided embedding
                similarity = np.dot(embedding, chunk_embedding) / (
                    np.linalg.norm(embedding) * np.linalg.norm(chunk_embedding)
                )
                
                metadata = json.loads(metadata_json) if metadata_json else {}
                
                results.append({
                    'chunk_id': chunk_id,
                    'conteudo': conteudo,
                    'similarity': float(similarity),
                    'metadata': metadata,
                    'tipo': tipo,
                    'titulo': titulo,
                    'numero': numero,
                    'data': data,
                    'conselho': conselho,
                    'posicao': posicao,
                    'user_id': doc_user_id,
                    'is_global': bool(is_global)
                })
            
            # Sort by similarity and return top k
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:k]
    
    def search_with_filter(self, query: str, filters: Dict, k: int = 5, user_id: Optional[str] = None) -> List[Dict]:
        """
        Search with metadata filters and user permissions.
        
        Args:
            query: Search query
            filters: Dict with filter criteria
            k: Number of results
            user_id: User ID for permission filtering
        """
        # Generate query embedding
        query_embedding = self.embedding_service.generate_embedding(query)
        
        # Build SQL query with filters
        where_clauses = []
        params = []
        
        # Permission filter
        if user_id:
            where_clauses.append("(d.is_global = 1 OR d.user_id = ?)")
            params.append(user_id)
        else:
            where_clauses.append("d.is_global = 1")
        
        # Type filters
        if 'tipo' in filters:
            where_clauses.append("d.tipo = ?")
            params.append(filters['tipo'])
        
        if 'conselho' in filters:
            where_clauses.append("d.conselho = ?")
            params.append(filters['conselho'])
        
        if 'numero' in filters:
            where_clauses.append("d.numero = ?")
            params.append(filters['numero'])
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(f"""
                SELECT c.id, c.conteudo, c.embedding, c.metadata, c.posicao,
                       d.tipo, d.titulo, d.numero, d.data, d.conselho,
                       d.user_id, d.is_global
                FROM chunks c
                JOIN documentos d ON c.documento_id = d.id
                WHERE {where_sql}
            """, params)
            
            results = []
            for row in cur.fetchall():
                chunk_id, conteudo, embedding_blob, metadata_json, posicao, tipo, titulo, numero, data, conselho, doc_user_id, is_global = row
                
                embedding = np.frombuffer(embedding_blob, dtype=np.float32)
                similarity = np.dot(query_embedding, embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
                )
                
                metadata = json.loads(metadata_json) if metadata_json else {}
                
                results.append({
                    'chunk_id': chunk_id,
                    'conteudo': conteudo,
                    'similarity': float(similarity),
                    'metadata': metadata,
                    'tipo': tipo,
                    'titulo': titulo,
                    'numero': numero,
                    'data': data,
                    'conselho': conselho,
                    'posicao': posicao,
                    'user_id': doc_user_id,
                    'is_global': bool(is_global)
                })
            
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:k]
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            
            cur.execute("SELECT COUNT(*) FROM documentos")
            num_docs = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM chunks")
            num_chunks = cur.fetchone()[0]
            
            cur.execute("SELECT tipo, COUNT(*) FROM documentos GROUP BY tipo")
            docs_by_type = dict(cur.fetchall())
            
            return {
                'num_documentos': num_docs,
                'num_chunks': num_chunks,
                'documentos_por_tipo': docs_by_type
            }

# Singleton instance
_vector_store = None

def get_vector_store() -> VectorStore:
    """Get or create vector store singleton"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
