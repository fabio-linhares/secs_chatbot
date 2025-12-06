#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Serviço de auditoria e logging de interações
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Serviço de auditoria e logging de interações
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import sqlite3
import json
from datetime import datetime
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AuditRecord:
    """Represents a single audit log entry"""
    user: str
    role: str
    input_text: str
    output_text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


class AuditLogger:
    """Logs chat interactions to SQLite database"""
    
    def __init__(self, db_path: str, enabled: bool = True):
        self.db_path = db_path
        self.enabled = enabled
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_tables()
    
    def _init_tables(self):
        """Initialize audit log table"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT NOT NULL,
                role TEXT NOT NULL,
                input_text TEXT NOT NULL,
                output_text TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_log(created_at)"
        )
        
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user)"
        )
        
        self.conn.commit()
    
    def log(self, record: AuditRecord) -> None:
        """
        Log an interaction.
        
        Args:
            record: AuditRecord with interaction details
        """
        if not self.enabled:
            return
        
        meta_json = json.dumps(record.metadata or {}, ensure_ascii=False)
        
        self.conn.execute("""
            INSERT INTO audit_log (user, role, input_text, output_text, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            record.user,
            record.role,
            record.input_text,
            record.output_text,
            meta_json,
            record.created_at.isoformat()
        ))
        
        self.conn.commit()
    
    def list_recent(self, limit: int = 50, user: Optional[str] = None) -> List[AuditRecord]:
        """
        List recent audit records.
        
        Args:
            limit: Maximum number of records to return
            user: Optional user filter
            
        Returns:
            List of AuditRecord objects
        """
        if user:
            query = """
                SELECT user, role, input_text, output_text, metadata, created_at
                FROM audit_log 
                WHERE user = ?
                ORDER BY created_at DESC 
                LIMIT ?
            """
            params = (user, limit)
        else:
            query = """
                SELECT user, role, input_text, output_text, metadata, created_at
                FROM audit_log 
                ORDER BY created_at DESC 
                LIMIT ?
            """
            params = (limit,)
        
        cur = self.conn.execute(query, params)
        rows = cur.fetchall()
        
        records = []
        for row in rows:
            user, role, input_text, output_text, metadata, created_at = row
            meta_dict = json.loads(metadata) if metadata else {}
            
            records.append(AuditRecord(
                user=user,
                role=role,
                input_text=input_text,
                output_text=output_text,
                metadata=meta_dict,
                created_at=datetime.fromisoformat(created_at)
            ))
        
        return records
    
    def get_stats(self) -> Dict[str, Any]:
        """Get audit statistics"""
        total = self.conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
        
        # Unique users
        unique_users = self.conn.execute(
            "SELECT COUNT(DISTINCT user) FROM audit_log"
        ).fetchone()[0]
        
        # Interactions by role
        by_role = self.conn.execute("""
            SELECT role, COUNT(*) 
            FROM audit_log 
            GROUP BY role
        """).fetchall()
        
        # Recent activity (last 24 hours)
        recent = self.conn.execute("""
            SELECT COUNT(*) 
            FROM audit_log 
            WHERE created_at > datetime('now', '-1 day')
        """).fetchone()[0]
        
        return {
            'total_interactions': total,
            'unique_users': unique_users,
            'by_role': dict(by_role),
            'last_24h': recent
        }
    
    def search(self, query: str, limit: int = 20) -> List[AuditRecord]:
        """
        Search audit logs by text.
        
        Args:
            query: Search term
            limit: Maximum results
            
        Returns:
            List of matching AuditRecord objects
        """
        cur = self.conn.execute("""
            SELECT user, role, input_text, output_text, metadata, created_at
            FROM audit_log 
            WHERE input_text LIKE ? OR output_text LIKE ?
            ORDER BY created_at DESC 
            LIMIT ?
        """, (f'%{query}%', f'%{query}%', limit))
        
        rows = cur.fetchall()
        
        records = []
        for row in rows:
            user, role, input_text, output_text, metadata, created_at = row
            meta_dict = json.loads(metadata) if metadata else {}
            
            records.append(AuditRecord(
                user=user,
                role=role,
                input_text=input_text,
                output_text=output_text,
                metadata=meta_dict,
                created_at=datetime.fromisoformat(created_at)
            ))
        
        return records


# Singleton instance
_audit_logger = None

def get_audit_logger(db_path: str = None, enabled: bool = True) -> AuditLogger:
    """Get or create audit logger singleton"""
    global _audit_logger
    if _audit_logger is None:
        if db_path is None:
            from src.config import settings
            db_path = settings.db_path_resolved
        _audit_logger = AuditLogger(db_path, enabled)
    return _audit_logger
