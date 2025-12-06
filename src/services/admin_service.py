#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Serviço administrativo do sistema
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Serviço administrativo do sistema
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import sqlite3
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class SystemStats:
    """System statistics"""
    total_users: int
    total_documents: int
    total_chunks: int
    total_storage_mb: float
    users_by_role: Dict[str, int]
    top_users_by_storage: List[tuple[str, float]]


class AdminService:
    """Administrative service"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
    
    def get_all_users_with_stats(self) -> List[Dict[str, Any]]:
        """Get all users with their statistics"""
        cursor = self.conn.execute("""
            SELECT 
                u.username,
                u.role,
                u.created_at,
                COALESCE(q.current_storage_mb, 0) as storage_mb,
                COALESCE(q.max_storage_mb, 100) as max_storage_mb,
                COALESCE(q.current_documents, 0) as num_documents,
                COALESCE(q.max_documents, 50) as max_documents
            FROM users u
            LEFT JOIN user_quotas q ON u.username = q.user_id
            ORDER BY u.created_at DESC
        """)
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'username': row[0],
                'role': row[1],
                'created_at': row[2],
                'storage_mb': row[3],
                'max_storage_mb': row[4],
                'num_documents': row[5],
                'max_documents': row[6],
                'storage_percentage': (row[3] / row[4] * 100) if row[4] > 0 else 0
            })
        
        return users
    
    def get_system_stats(self) -> SystemStats:
        """Get overall system statistics"""
        # Total users
        total_users = self.conn.execute(
            "SELECT COUNT(*) FROM users"
        ).fetchone()[0]
        
        # Total documents
        total_documents = self.conn.execute(
            "SELECT COUNT(*) FROM user_documents"
        ).fetchone()[0]
        
        # Total chunks
        total_chunks = self.conn.execute(
            "SELECT COUNT(*) FROM user_chunks"
        ).fetchone()[0]
        
        # Total storage
        total_storage = self.conn.execute(
            "SELECT COALESCE(SUM(current_storage_mb), 0) FROM user_quotas"
        ).fetchone()[0]
        
        # Users by role
        cursor = self.conn.execute(
            "SELECT role, COUNT(*) FROM users GROUP BY role"
        )
        users_by_role = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Top users by storage
        cursor = self.conn.execute("""
            SELECT user_id, current_storage_mb
            FROM user_quotas
            ORDER BY current_storage_mb DESC
            LIMIT 10
        """)
        top_users = [(row[0], row[1]) for row in cursor.fetchall()]
        
        return SystemStats(
            total_users=total_users,
            total_documents=total_documents,
            total_chunks=total_chunks,
            total_storage_mb=total_storage,
            users_by_role=users_by_role,
            top_users_by_storage=top_users
        )
    
    def delete_user_documents(self, user_id: str) -> int:
        """Delete all documents for a user (admin only)"""
        # Get document IDs
        cursor = self.conn.execute(
            "SELECT id FROM user_documents WHERE user_id = ?",
            (user_id,)
        )
        doc_ids = [row[0] for row in cursor.fetchall()]
        
        if not doc_ids:
            return 0
        
        # Delete chunks
        placeholders = ','.join('?' * len(doc_ids))
        self.conn.execute(
            f"DELETE FROM user_chunks WHERE document_id IN ({placeholders})",
            doc_ids
        )
        
        # Delete documents
        self.conn.execute(
            "DELETE FROM user_documents WHERE user_id = ?",
            (user_id,)
        )
        
        # Reset quota
        self.conn.execute(
            """UPDATE user_quotas 
               SET current_storage_mb = 0, current_documents = 0
               WHERE user_id = ?""",
            (user_id,)
        )
        
        self.conn.commit()
        
        return len(doc_ids)
    
    def get_user_activity(self, user_id: str) -> Dict[str, Any]:
        """Get detailed activity for a user"""
        # Documents
        docs = self.conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(file_size), 0) FROM user_documents WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        
        # Preferences
        prefs_count = self.conn.execute(
            "SELECT COUNT(*) FROM user_preferences WHERE user_id = ?",
            (user_id,)
        ).fetchone()[0]
        
        # Audit logs
        interactions = self.conn.execute(
            "SELECT COUNT(*) FROM audit_log WHERE user = ?",
            (user_id,)
        ).fetchone()[0]
        
        # Cache entries
        cache_entries = self.conn.execute(
            "SELECT COUNT(*) FROM qa_user_cache WHERE user = ?",
            (user_id,)
        ).fetchone()[0]
        
        return {
            'num_documents': docs[0],
            'total_file_size': docs[1],
            'num_preferences': prefs_count,
            'num_interactions': interactions,
            'num_cache_entries': cache_entries
        }


# Singleton
_admin_service = None

def get_admin_service(db_path: str = None) -> AdminService:
    """Get or create admin service singleton"""
    global _admin_service
    if _admin_service is None:
        if db_path is None:
            from src.config import get_settings
            db_path = str(get_settings().db_path_resolved)
        _admin_service = AdminService(db_path)
    return _admin_service
