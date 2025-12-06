#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Serviço de gestão de quotas de armazenamento
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Serviço de gestão de quotas de armazenamento
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import sqlite3
from dataclasses import dataclass
from typing import Optional


@dataclass
class UserQuota:
    """User quota model"""
    user_id: str
    max_storage_mb: int
    max_documents: int
    current_storage_mb: float
    current_documents: int
    
    @property
    def storage_percentage(self) -> float:
        """Get storage usage percentage"""
        if self.max_storage_mb == 0:
            return 0.0
        return (self.current_storage_mb / self.max_storage_mb) * 100
    
    @property
    def documents_percentage(self) -> float:
        """Get documents usage percentage"""
        if self.max_documents == 0:
            return 0.0
        return (self.current_documents / self.max_documents) * 100
    
    @property
    def can_upload(self) -> bool:
        """Check if user can upload more documents"""
        return (
            self.current_storage_mb < self.max_storage_mb and
            self.current_documents < self.max_documents
        )


class QuotaService:
    """Manages user storage quotas"""
    
    DEFAULT_MAX_STORAGE_MB = 100
    DEFAULT_MAX_DOCUMENTS = 50
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_tables()
    
    def _init_tables(self):
        """Initialize user_quotas table"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS user_quotas (
                user_id TEXT PRIMARY KEY,
                max_storage_mb INTEGER DEFAULT 100,
                max_documents INTEGER DEFAULT 50,
                current_storage_mb REAL DEFAULT 0,
                current_documents INTEGER DEFAULT 0
            )
        """)
        self.conn.commit()
    
    def get_quota(self, user_id: str) -> UserQuota:
        """
        Get user quota, creating default if not exists.
        
        Args:
            user_id: User identifier
            
        Returns:
            UserQuota object
        """
        row = self.conn.execute(
            """SELECT user_id, max_storage_mb, max_documents, 
                      current_storage_mb, current_documents
               FROM user_quotas WHERE user_id = ?""",
            (user_id,)
        ).fetchone()
        
        if not row:
            # Create default quota
            self.conn.execute(
                """INSERT INTO user_quotas (user_id, max_storage_mb, max_documents)
                   VALUES (?, ?, ?)""",
                (user_id, self.DEFAULT_MAX_STORAGE_MB, self.DEFAULT_MAX_DOCUMENTS)
            )
            self.conn.commit()
            
            return UserQuota(
                user_id=user_id,
                max_storage_mb=self.DEFAULT_MAX_STORAGE_MB,
                max_documents=self.DEFAULT_MAX_DOCUMENTS,
                current_storage_mb=0.0,
                current_documents=0
            )
        
        return UserQuota(
            user_id=row[0],
            max_storage_mb=row[1],
            max_documents=row[2],
            current_storage_mb=row[3],
            current_documents=row[4]
        )
    
    def update_quota_limits(
        self,
        user_id: str,
        max_storage_mb: Optional[int] = None,
        max_documents: Optional[int] = None
    ) -> bool:
        """
        Update user quota limits (admin only).
        
        Args:
            user_id: User identifier
            max_storage_mb: New max storage in MB
            max_documents: New max documents
            
        Returns:
            True if updated
        """
        # Ensure quota exists
        self.get_quota(user_id)
        
        updates = []
        params = []
        
        if max_storage_mb is not None:
            updates.append("max_storage_mb = ?")
            params.append(max_storage_mb)
        
        if max_documents is not None:
            updates.append("max_documents = ?")
            params.append(max_documents)
        
        if not updates:
            return False
        
        params.append(user_id)
        
        self.conn.execute(
            f"UPDATE user_quotas SET {', '.join(updates)} WHERE user_id = ?",
            params
        )
        self.conn.commit()
        
        return True
    
    def add_usage(
        self,
        user_id: str,
        storage_mb: float,
        num_documents: int = 1
    ) -> bool:
        """
        Add to user's current usage.
        
        Args:
            user_id: User identifier
            storage_mb: Storage to add in MB
            num_documents: Number of documents to add
            
        Returns:
            True if added, False if would exceed quota
        """
        quota = self.get_quota(user_id)
        
        new_storage = quota.current_storage_mb + storage_mb
        new_documents = quota.current_documents + num_documents
        
        # Check limits
        if new_storage > quota.max_storage_mb:
            return False
        
        if new_documents > quota.max_documents:
            return False
        
        self.conn.execute(
            """UPDATE user_quotas 
               SET current_storage_mb = current_storage_mb + ?,
                   current_documents = current_documents + ?
               WHERE user_id = ?""",
            (storage_mb, num_documents, user_id)
        )
        self.conn.commit()
        
        return True
    
    def remove_usage(
        self,
        user_id: str,
        storage_mb: float,
        num_documents: int = 1
    ):
        """
        Remove from user's current usage.
        
        Args:
            user_id: User identifier
            storage_mb: Storage to remove in MB
            num_documents: Number of documents to remove
        """
        self.conn.execute(
            """UPDATE user_quotas 
               SET current_storage_mb = MAX(0, current_storage_mb - ?),
                   current_documents = MAX(0, current_documents - ?)
               WHERE user_id = ?""",
            (storage_mb, num_documents, user_id)
        )
        self.conn.commit()
    
    def check_can_upload(
        self,
        user_id: str,
        file_size_mb: float
    ) -> tuple[bool, str]:
        """
        Check if user can upload a file.
        
        Args:
            user_id: User identifier
            file_size_mb: File size in MB
            
        Returns:
            (can_upload, message)
        """
        quota = self.get_quota(user_id)
        
        if quota.current_documents >= quota.max_documents:
            return False, f"Limite de documentos atingido ({quota.max_documents})"
        
        if quota.current_storage_mb + file_size_mb > quota.max_storage_mb:
            available = quota.max_storage_mb - quota.current_storage_mb
            return False, f"Espaço insuficiente. Disponível: {available:.1f}MB, Necessário: {file_size_mb:.1f}MB"
        
        return True, "OK"


# Singleton
_quota_service = None

def get_quota_service(db_path: str = None) -> QuotaService:
    """Get or create quota service singleton"""
    global _quota_service
    if _quota_service is None:
        if db_path is None:
            from src.config import get_settings
            db_path = str(get_settings().db_path_resolved)
        _quota_service = QuotaService(db_path)
    return _quota_service
