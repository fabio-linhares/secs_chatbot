#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - User
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: User
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

"""
User Model
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    """User model"""
    id: int
    username: str
    full_name: str
    email: str
    role: str  # 'public', 'secs', 'admin'
    active: bool = True
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    def has_permission(self, action: str) -> bool:
        """Check if user has permission for an action"""
        permissions = {
            'public': ['view_public_docs', 'chat'],
            'secs': ['view_public_docs', 'view_all_docs', 'chat', 'export'],
            'admin': ['view_public_docs', 'view_all_docs', 'chat', 'export', 'view_logs', 'manage_users']
        }
        return action in permissions.get(self.role, [])
    
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == 'admin'
    
    def is_secs(self) -> bool:
        """Check if user is SECS staff"""
        return self.role in ['secs', 'admin']
