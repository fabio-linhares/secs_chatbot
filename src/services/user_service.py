#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Serviço de gerenciamento de usuários
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Serviço de gerenciamento de usuários
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import sqlite3
import hashlib
import base64
import os
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class User:
    """User model"""
    username: str
    role: str


class UserService:
    """Manages user authentication and authorization"""
    
    VALID_ROLES = ["publico", "secs", "admin"]
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_tables()
    
    def _init_tables(self):
        """Initialize users table"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)"
        )
        
        self.conn.commit()
    
    def _hash_password(self, password: str, salt: bytes) -> str:
        """
        Hash password using PBKDF2.
        
        Args:
            password: Plain text password
            salt: Random salt bytes
            
        Returns:
            Base64 encoded hash
        """
        dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100_000)
        return base64.b64encode(dk).decode('utf-8')
    
    def create_user(self, username: str, password: str, role: str = "publico") -> User:
        """
        Create new user.
        
        Args:
            username: Username (will be lowercased)
            password: Plain text password
            role: User role (publico, secs, admin)
            
        Returns:
            Created User object
            
        Raises:
            ValueError: If username/password invalid or user exists
        """
        username = username.strip().lower()
        
        if not username or not password:
            raise ValueError("Usuário e senha são obrigatórios")
        
        if role not in self.VALID_ROLES:
            raise ValueError(f"Role inválido. Use: {', '.join(self.VALID_ROLES)}")
        
        # Generate salt and hash
        salt = os.urandom(16)
        password_hash = self._hash_password(password, salt)
        salt_b64 = base64.b64encode(salt).decode('utf-8')
        
        try:
            self.conn.execute(
                "INSERT INTO users (username, password_hash, salt, role) VALUES (?, ?, ?, ?)",
                (username, password_hash, salt_b64, role)
            )
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError("Usuário já existe") from e
        
        return User(username=username, role=role)
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user.
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            User object if authenticated, None otherwise
        """
        username = username.strip().lower()
        
        row = self.conn.execute(
            "SELECT password_hash, salt, role FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        
        if not row:
            return None
        
        stored_hash, salt_b64, role = row
        salt = base64.b64decode(salt_b64)
        
        # Verify password
        candidate_hash = self._hash_password(password, salt)
        
        if candidate_hash == stored_hash:
            return User(username=username, role=role)
        
        return None
    
    def get_user(self, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            username: Username
            
        Returns:
            User object if found, None otherwise
        """
        username = username.strip().lower()
        
        row = self.conn.execute(
            "SELECT role FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        
        if not row:
            return None
        
        return User(username=username, role=row[0])
    
    def list_users(self) -> List[User]:
        """
        List all users.
        
        Returns:
            List of User objects
        """
        cur = self.conn.execute(
            "SELECT username, role FROM users ORDER BY created_at DESC"
        )
        
        return [User(username=u, role=r) for u, r in cur.fetchall()]
    
    def update_role(self, username: str, new_role: str) -> bool:
        """
        Update user role.
        
        Args:
            username: Username
            new_role: New role
            
        Returns:
            True if updated, False if user not found
        """
        if new_role not in self.VALID_ROLES:
            raise ValueError(f"Role inválido. Use: {', '.join(self.VALID_ROLES)}")
        
        username = username.strip().lower()
        
        cursor = self.conn.execute(
            "UPDATE users SET role = ? WHERE username = ?",
            (new_role, username)
        )
        self.conn.commit()
        
        return cursor.rowcount > 0
    
    def delete_user(self, username: str) -> bool:
        """
        Delete user.
        
        Args:
            username: Username
            
        Returns:
            True if deleted, False if user not found
        """
        username = username.strip().lower()
        
        cursor = self.conn.execute(
            "DELETE FROM users WHERE username = ?",
            (username,)
        )
        self.conn.commit()
        
        return cursor.rowcount > 0


# Singleton
_user_service = None

def get_user_service(db_path: str = None) -> UserService:
    """Get or create user service singleton"""
    global _user_service
    if _user_service is None:
        if db_path is None:
            from src.config import get_settings
            db_path = str(get_settings().db_path_resolved)
        _user_service = UserService(db_path)
    return _user_service
