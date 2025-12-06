#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Serviço de cache inteligente multinível
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Serviço de cache inteligente multinível
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import sqlite3
import re
import unicodedata
from typing import Optional
from pathlib import Path


class CacheService:
    """Manages Q&A caching with user and global levels"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_tables()
    
    def _init_tables(self):
        """Initialize cache tables"""
        # User-specific cache
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS qa_user_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT NOT NULL,
                normalized TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user, normalized)
            )
        """)
        
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_user_norm ON qa_user_cache(user, normalized)"
        )
        
        # Global cache (shared across users)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS qa_global_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                normalized TEXT UNIQUE NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
    
    def normalize_question(self, question: str) -> str:
        """
        Normalize question for cache lookup.
        
        Removes:
        - Accents/diacritics
        - Case sensitivity
        - Extra punctuation
        - Multiple spaces
        
        Example:
            "Qual é a PAUTA??" -> "qual e a pauta"
        """
        # Remove accents
        nfkd = unicodedata.normalize('NFKD', question)
        text = ''.join([c for c in nfkd if not unicodedata.combining(c)])
        
        # Lowercase
        text = text.lower().strip()
        
        # Remove punctuation (keep alphanumeric and spaces)
        text = re.sub(r'[^\w\s]', '', text)
        
        # Normalize spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def should_bypass_cache(self, answer: str) -> bool:
        """
        Check if answer should NOT be cached.
        
        Bypasses caching for negative/uncertain responses to allow
        re-querying when new documents are added.
        
        Args:
            answer: The response text
            
        Returns:
            True if should bypass cache, False otherwise
        """
        negative_signals = [
            "não encontrei",
            "nao encontrei",
            "não há base",
            "nao ha base",
            "sem base documental",
            "não tenho certeza",
            "nao tenho certeza",
            "não há evidência",
            "nao ha evidencia",
            "não sei",
            "nao sei",
        ]
        
        answer_lower = answer.lower()
        return any(signal in answer_lower for signal in negative_signals)
    
    def get_user_answer(self, user_id: str, question: str) -> Optional[str]:
        """
        Get cached answer for specific user.
        
        Args:
            user_id: User identifier
            question: User's question
            
        Returns:
            Cached answer if found, None otherwise
        """
        normalized = self.normalize_question(question)
        
        row = self.conn.execute(
            "SELECT answer FROM qa_user_cache WHERE user = ? AND normalized = ?",
            (user_id, normalized)
        ).fetchone()
        
        return row[0] if row else None
    
    def set_user_answer(self, user_id: str, question: str, answer: str) -> None:
        """
        Cache answer for specific user.
        
        Args:
            user_id: User identifier
            question: User's question
            answer: Response to cache
        """
        normalized = self.normalize_question(question)
        
        self.conn.execute("""
            INSERT INTO qa_user_cache (user, normalized, question, answer)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user, normalized) DO UPDATE SET 
                answer=excluded.answer,
                question=excluded.question,
                created_at=CURRENT_TIMESTAMP
        """, (user_id, normalized, question, answer))
        
        self.conn.commit()
    
    def get_global_answer(self, question: str) -> Optional[str]:
        """
        Get cached answer from global cache.
        
        Args:
            question: User's question
            
        Returns:
            Cached answer if found, None otherwise
        """
        normalized = self.normalize_question(question)
        
        row = self.conn.execute(
            "SELECT answer FROM qa_global_cache WHERE normalized = ?",
            (normalized,)
        ).fetchone()
        
        return row[0] if row else None
    
    def set_global_answer(self, question: str, answer: str) -> None:
        """
        Cache answer in global cache.
        
        Args:
            question: User's question
            answer: Response to cache
        """
        normalized = self.normalize_question(question)
        
        self.conn.execute("""
            INSERT INTO qa_global_cache (normalized, question, answer)
            VALUES (?, ?, ?)
            ON CONFLICT(normalized) DO UPDATE SET 
                answer=excluded.answer,
                question=excluded.question,
                created_at=CURRENT_TIMESTAMP
        """, (normalized, question, answer))
        
        self.conn.commit()
    
    def clear_user_cache(self, user_id: str) -> None:
        """Clear all cached answers for a specific user"""
        self.conn.execute("DELETE FROM qa_user_cache WHERE user = ?", (user_id,))
        self.conn.commit()
    
    def clear_global_cache(self) -> None:
        """Clear entire global cache"""
        self.conn.execute("DELETE FROM qa_global_cache")
        self.conn.commit()
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        user_count = self.conn.execute("SELECT COUNT(*) FROM qa_user_cache").fetchone()[0]
        global_count = self.conn.execute("SELECT COUNT(*) FROM qa_global_cache").fetchone()[0]
        
        return {
            'user_cache_entries': user_count,
            'global_cache_entries': global_count,
            'total_entries': user_count + global_count
        }


# Singleton instance
_cache_service = None

def get_cache_service(db_path: str = None) -> CacheService:
    """Get or create cache service singleton"""
    global _cache_service
    if _cache_service is None:
        if db_path is None:
            from src.config import settings
            db_path = settings.db_path_resolved
        _cache_service = CacheService(db_path)
    return _cache_service
