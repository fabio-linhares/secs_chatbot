#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Serviço de preferências personalizadas do usuário
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Serviço de preferências personalizadas do usuário
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import sqlite3
from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime


@dataclass
class UserPreference:
    """User preference model"""
    id: Optional[int]
    user_id: str
    trigger: str
    interpretation: str
    active: bool = True
    created_at: Optional[datetime] = None


class UserPreferencesService:
    """Manages user personalization preferences"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_tables()
    
    def _init_tables(self):
        """Initialize user_preferences table"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                trigger TEXT NOT NULL,
                interpretation TEXT NOT NULL,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, trigger)
            )
        """)
        
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_user_prefs_user ON user_preferences(user_id)"
        )
        
        self.conn.commit()
    
    def add_preference(
        self,
        user_id: str,
        trigger: str,
        interpretation: str
    ) -> UserPreference:
        """
        Add new user preference.
        
        Args:
            user_id: User identifier
            trigger: Trigger phrase (what user says)
            interpretation: How to interpret it
            
        Returns:
            Created UserPreference
            
        Raises:
            ValueError: If preference already exists
        """
        trigger = trigger.strip().lower()
        interpretation = interpretation.strip()
        
        if not trigger or not interpretation:
            raise ValueError("Trigger e interpretação são obrigatórios")
        
        try:
            cursor = self.conn.execute(
                """INSERT INTO user_preferences (user_id, trigger, interpretation)
                   VALUES (?, ?, ?)""",
                (user_id, trigger, interpretation)
            )
            self.conn.commit()
            
            return UserPreference(
                id=cursor.lastrowid,
                user_id=user_id,
                trigger=trigger,
                interpretation=interpretation,
                active=True,
                created_at=datetime.now()
            )
        except sqlite3.IntegrityError:
            raise ValueError(f"Preferência para '{trigger}' já existe")
    
    def get_user_preferences(
        self,
        user_id: str,
        active_only: bool = True
    ) -> List[UserPreference]:
        """
        Get all preferences for a user.
        
        Args:
            user_id: User identifier
            active_only: Only return active preferences
            
        Returns:
            List of UserPreference objects
        """
        query = """
            SELECT id, user_id, trigger, interpretation, active, created_at
            FROM user_preferences
            WHERE user_id = ?
        """
        
        if active_only:
            query += " AND active = 1"
        
        query += " ORDER BY created_at DESC"
        
        cursor = self.conn.execute(query, (user_id,))
        
        preferences = []
        for row in cursor.fetchall():
            preferences.append(UserPreference(
                id=row[0],
                user_id=row[1],
                trigger=row[2],
                interpretation=row[3],
                active=bool(row[4]),
                created_at=datetime.fromisoformat(row[5]) if row[5] else None
            ))
        
        return preferences
    
    def update_preference(
        self,
        preference_id: int,
        interpretation: Optional[str] = None,
        active: Optional[bool] = None
    ) -> bool:
        """
        Update preference.
        
        Args:
            preference_id: Preference ID
            interpretation: New interpretation (optional)
            active: New active status (optional)
            
        Returns:
            True if updated, False if not found
        """
        updates = []
        params = []
        
        if interpretation is not None:
            updates.append("interpretation = ?")
            params.append(interpretation.strip())
        
        if active is not None:
            updates.append("active = ?")
            params.append(1 if active else 0)
        
        if not updates:
            return False
        
        params.append(preference_id)
        
        cursor = self.conn.execute(
            f"UPDATE user_preferences SET {', '.join(updates)} WHERE id = ?",
            params
        )
        self.conn.commit()
        
        return cursor.rowcount > 0
    
    def delete_preference(self, preference_id: int) -> bool:
        """
        Delete preference.
        
        Args:
            preference_id: Preference ID
            
        Returns:
            True if deleted, False if not found
        """
        cursor = self.conn.execute(
            "DELETE FROM user_preferences WHERE id = ?",
            (preference_id,)
        )
        self.conn.commit()
        
        return cursor.rowcount > 0
    
    def build_context_prompt(self, user_id: str) -> str:
        """
        Build context prompt from user preferences.
        
        This is injected into the system prompt to personalize
        the assistant's understanding of the user's queries.
        
        Args:
            user_id: User identifier
            
        Returns:
            Context prompt string
        """
        preferences = self.get_user_preferences(user_id, active_only=True)
        
        if not preferences:
            return ""
        
        lines = ["\n## CONTEXTO PERSONALIZADO DO USUÁRIO\n"]
        lines.append("O usuário tem as seguintes preferências de interpretação:")
        
        for pref in preferences:
            lines.append(f"- Quando o usuário disser '{pref.trigger}', entenda como '{pref.interpretation}'")
        
        lines.append("\nUse estas preferências para interpretar as perguntas do usuário de forma mais precisa.\n")
        
        return "\n".join(lines)


# Singleton
_user_preferences_service = None

def get_user_preferences_service(db_path: str = None) -> UserPreferencesService:
    """Get or create user preferences service singleton"""
    global _user_preferences_service
    if _user_preferences_service is None:
        if db_path is None:
            from src.config import get_settings
            db_path = str(get_settings().db_path_resolved)
        _user_preferences_service = UserPreferencesService(db_path)
    return _user_preferences_service
