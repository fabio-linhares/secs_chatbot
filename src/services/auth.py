#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Módulo auth.py
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Módulo auth.py
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from src.config import settings
from src.models.user import User

class AuthService:
    """Handles authentication and session management"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.db_path_resolved
        self._init_db()
        self._create_default_users()
    
    def _init_db(self):
        """Initialize authentication tables"""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            
            # Users table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT,
                    email TEXT,
                    role TEXT NOT NULL CHECK(role IN ('public', 'secs', 'admin')),
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            """)
            
            # Sessions table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Index for faster lookups
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_token 
                ON sessions(session_token)
            """)
            
            conn.commit()
    
    def _create_default_users(self):
        """Create default users if they don't exist"""
        default_users = [
            ('admin', 'admin123', 'Administrador', 'admin@ufal.br', 'admin'),
            ('secs', 'secs123', 'Secretaria SECS', 'secs@ufal.br', 'secs'),
            ('publico', 'publico123', 'Usuário Público', 'publico@ufal.br', 'public'),
        ]
        
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            
            for username, password, full_name, email, role in default_users:
                # Check if user exists
                cur.execute("SELECT id FROM users WHERE username = ?", (username,))
                if not cur.fetchone():
                    password_hash = self._hash_password(password)
                    cur.execute("""
                        INSERT INTO users (username, password_hash, full_name, email, role)
                        VALUES (?, ?, ?, ?, ?)
                    """, (username, password_hash, full_name, email, role))
            
            conn.commit()
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def login(self, username: str, password: str) -> Optional[tuple[User, str]]:
        """
        Authenticate user and create session.
        Returns (User, session_token) if successful, None otherwise.
        """
        password_hash = self._hash_password(password)
        
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            
            # Find user
            cur.execute("""
                SELECT id, username, full_name, email, role, active, created_at, last_login
                FROM users
                WHERE username = ? AND password_hash = ? AND active = 1
            """, (username, password_hash))
            
            row = cur.fetchone()
            if not row:
                return None
            
            # Create user object
            user = User(
                id=row[0],
                username=row[1],
                full_name=row[2],
                email=row[3],
                role=row[4],
                active=bool(row[5]),
                created_at=row[6],
                last_login=row[7]
            )
            
            # Create session
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=24)
            
            cur.execute("""
                INSERT INTO sessions (user_id, session_token, expires_at)
                VALUES (?, ?, ?)
            """, (user.id, session_token, expires_at))
            
            # Update last login
            cur.execute("""
                UPDATE users SET last_login = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (user.id,))
            
            conn.commit()
            
            return user, session_token
    
    def logout(self, session_token: str):
        """Invalidate session"""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM sessions WHERE session_token = ?", (session_token,))
            conn.commit()
    
    def get_user_by_session(self, session_token: str) -> Optional[User]:
        """Get user from session token"""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            
            # Find valid session
            cur.execute("""
                SELECT u.id, u.username, u.full_name, u.email, u.role, u.active, u.created_at, u.last_login
                FROM users u
                JOIN sessions s ON u.id = s.user_id
                WHERE s.session_token = ? AND s.expires_at > CURRENT_TIMESTAMP AND u.active = 1
            """, (session_token,))
            
            row = cur.fetchone()
            if not row:
                return None
            
            return User(
                id=row[0],
                username=row[1],
                full_name=row[2],
                email=row[3],
                role=row[4],
                active=bool(row[5]),
                created_at=row[6],
                last_login=row[7]
            )
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP")
            conn.commit()

# Singleton instance
_auth_service = None

def get_auth_service() -> AuthService:
    """Get or create auth service singleton"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
