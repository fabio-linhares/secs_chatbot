#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Serviço de upload e gestão de documentos do usuário
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Serviço de upload e gestão de documentos do usuário
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import sqlite3
import os
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from pathlib import Path


@dataclass
class UserDocument:
    """User document model"""
    id: Optional[int]
    user_id: str
    filename: str
    description: str
    file_type: str
    file_size: int
    num_chunks: int
    tags: str
    uploaded_at: Optional[datetime] = None


class UserDocumentsService:
    """Manages user-uploaded documents"""
    
    def __init__(self, db_path: str, upload_dir: str = "data/user_uploads"):
        self.db_path = db_path
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_tables()
    
    def _init_tables(self):
        """Initialize user documents tables"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS user_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                description TEXT,
                file_type TEXT,
                file_size INTEGER,
                num_chunks INTEGER DEFAULT 0,
                tags TEXT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS user_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                user_id TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding BLOB,
                chunk_index INTEGER,
                metadata TEXT,
                FOREIGN KEY (document_id) REFERENCES user_documents(id) ON DELETE CASCADE
            )
        """)
        
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_user_docs_user ON user_documents(user_id)"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_user_chunks_user ON user_chunks(user_id)"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_user_chunks_doc ON user_chunks(document_id)"
        )
        
        self.conn.commit()
    
    def add_document(
        self,
        user_id: str,
        filename: str,
        file_content: bytes,
        description: str = "",
        tags: str = ""
    ) -> UserDocument:
        """
        Add new document for user.
        
        Args:
            user_id: User identifier
            filename: Original filename
            file_content: File content as bytes
            description: Document description
            tags: Comma-separated tags
            
        Returns:
            Created UserDocument
        """
        file_size = len(file_content)
        file_type = Path(filename).suffix.lower()
        
        # Save file
        user_dir = self.upload_dir / user_id
        user_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{filename}"
        file_path = user_dir / safe_filename
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Add to database
        cursor = self.conn.execute(
            """INSERT INTO user_documents 
               (user_id, filename, description, file_type, file_size, tags)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, filename, description, file_type, file_size, tags)
        )
        self.conn.commit()
        
        return UserDocument(
            id=cursor.lastrowid,
            user_id=user_id,
            filename=filename,
            description=description,
            file_type=file_type,
            file_size=file_size,
            num_chunks=0,
            tags=tags,
            uploaded_at=datetime.now()
        )
    
    def list_user_documents(self, user_id: str) -> List[UserDocument]:
        """Get all documents for a user"""
        cursor = self.conn.execute(
            """SELECT id, user_id, filename, description, file_type, 
                      file_size, num_chunks, tags, uploaded_at
               FROM user_documents WHERE user_id = ?
               ORDER BY uploaded_at DESC""",
            (user_id,)
        )
        
        documents = []
        for row in cursor.fetchall():
            documents.append(UserDocument(
                id=row[0],
                user_id=row[1],
                filename=row[2],
                description=row[3],
                file_type=row[4],
                file_size=row[5],
                num_chunks=row[6],
                tags=row[7],
                uploaded_at=datetime.fromisoformat(row[8]) if row[8] else None
            ))
        
        return documents
    
    def delete_document(self, document_id: int, user_id: str) -> bool:
        """Delete document and its chunks"""
        # Verify ownership
        row = self.conn.execute(
            "SELECT user_id FROM user_documents WHERE id = ?",
            (document_id,)
        ).fetchone()
        
        if not row or row[0] != user_id:
            return False
        
        # Delete chunks first (cascade should handle this, but explicit is better)
        self.conn.execute(
            "DELETE FROM user_chunks WHERE document_id = ?",
            (document_id,)
        )
        
        # Delete document
        self.conn.execute(
            "DELETE FROM user_documents WHERE id = ?",
            (document_id,)
        )
        
        self.conn.commit()
        return True
    
    def add_chunks(
        self,
        document_id: int,
        user_id: str,
        chunks: List[tuple[str, Optional[bytes]]]
    ):
        """
        Add chunks for a document.
        
        Args:
            document_id: Document ID
            user_id: User ID
            chunks: List of (content, embedding) tuples
        """
        for idx, (content, embedding) in enumerate(chunks):
            self.conn.execute(
                """INSERT INTO user_chunks 
                   (document_id, user_id, content, embedding, chunk_index)
                   VALUES (?, ?, ?, ?, ?)""",
                (document_id, user_id, content, embedding, idx)
            )
        
        # Update document chunk count
        self.conn.execute(
            "UPDATE user_documents SET num_chunks = ? WHERE id = ?",
            (len(chunks), document_id)
        )
        
        self.conn.commit()
    
    def search_user_chunks(
        self,
        user_id: str,
        query_embedding: bytes,
        k: int = 5
    ) -> List[dict]:
        """
        Search user's chunks (simplified - would need proper vector search).
        
        For now, returns recent chunks. In production, implement
        proper cosine similarity search.
        """
        cursor = self.conn.execute(
            """SELECT c.content, d.filename, d.description
               FROM user_chunks c
               JOIN user_documents d ON c.document_id = d.id
               WHERE c.user_id = ?
               ORDER BY d.uploaded_at DESC
               LIMIT ?""",
            (user_id, k)
        )
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'content': row[0],
                'source': row[1],
                'description': row[2],
                'similarity': 0.8  # Placeholder
            })
        
        return results


# Singleton
_user_documents_service = None

def get_user_documents_service(db_path: str = None) -> UserDocumentsService:
    """Get or create user documents service singleton"""
    global _user_documents_service
    if _user_documents_service is None:
        if db_path is None:
            from src.config import get_settings
            db_path = str(get_settings().db_path_resolved)
        _user_documents_service = UserDocumentsService(db_path)
    return _user_documents_service
