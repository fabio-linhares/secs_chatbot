#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Serviço de feature flags por role
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Serviço de feature flags por role
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import sqlite3
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class FeatureFlag:
    """Feature flag model"""
    id: int
    feature_name: str
    enabled_for_publico: bool
    enabled_for_secs: bool
    enabled_for_admin: bool


class FeatureFlagsService:
    """Manages feature flags"""
    
    # Default features
    DEFAULT_FEATURES = {
        'cache': {'publico': True, 'secs': True, 'admin': True},
        'rag': {'publico': True, 'secs': True, 'admin': True},
        'semantic_rewriter': {'publico': True, 'secs': True, 'admin': True},
        'focal_agent': {'publico': True, 'secs': True, 'admin': True},
        'user_preferences': {'publico': True, 'secs': True, 'admin': True},
        'document_upload': {'publico': False, 'secs': True, 'admin': True},
        'audit_view': {'publico': False, 'secs': True, 'admin': True},
        'admin_panel': {'publico': False, 'secs': False, 'admin': True},
    }
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_tables()
        self._init_default_features()
    
    def _init_tables(self):
        """Initialize feature_flags table"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS feature_flags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_name TEXT UNIQUE NOT NULL,
                enabled_for_publico BOOLEAN DEFAULT 1,
                enabled_for_secs BOOLEAN DEFAULT 1,
                enabled_for_admin BOOLEAN DEFAULT 1
            )
        """)
        self.conn.commit()
    
    def _init_default_features(self):
        """Initialize default features if not exist"""
        for feature_name, roles in self.DEFAULT_FEATURES.items():
            try:
                self.conn.execute(
                    """INSERT INTO feature_flags 
                       (feature_name, enabled_for_publico, enabled_for_secs, enabled_for_admin)
                       VALUES (?, ?, ?, ?)""",
                    (
                        feature_name,
                        1 if roles['publico'] else 0,
                        1 if roles['secs'] else 0,
                        1 if roles['admin'] else 0
                    )
                )
                self.conn.commit()
            except sqlite3.IntegrityError:
                # Feature already exists
                pass
    
    def is_feature_enabled(self, feature_name: str, user_role: str) -> bool:
        """
        Check if feature is enabled for user role.
        
        Args:
            feature_name: Feature name
            user_role: User role (publico, secs, admin)
            
        Returns:
            True if enabled, False otherwise
        """
        role_column = f"enabled_for_{user_role}"
        
        row = self.conn.execute(
            f"SELECT {role_column} FROM feature_flags WHERE feature_name = ?",
            (feature_name,)
        ).fetchone()
        
        if not row:
            # Feature not found, default to enabled
            return True
        
        return bool(row[0])
    
    def get_all_features(self) -> List[FeatureFlag]:
        """
        Get all feature flags.
        
        Returns:
            List of FeatureFlag objects
        """
        cursor = self.conn.execute(
            """SELECT id, feature_name, enabled_for_publico, 
                      enabled_for_secs, enabled_for_admin
               FROM feature_flags ORDER BY feature_name"""
        )
        
        features = []
        for row in cursor.fetchall():
            features.append(FeatureFlag(
                id=row[0],
                feature_name=row[1],
                enabled_for_publico=bool(row[2]),
                enabled_for_secs=bool(row[3]),
                enabled_for_admin=bool(row[4])
            ))
        
        return features
    
    def update_feature_flag(
        self,
        feature_name: str,
        enabled_for_publico: bool = None,
        enabled_for_secs: bool = None,
        enabled_for_admin: bool = None
    ) -> bool:
        """
        Update feature flag.
        
        Args:
            feature_name: Feature name
            enabled_for_publico: Enable for publico role
            enabled_for_secs: Enable for secs role
            enabled_for_admin: Enable for admin role
            
        Returns:
            True if updated
        """
        updates = []
        params = []
        
        if enabled_for_publico is not None:
            updates.append("enabled_for_publico = ?")
            params.append(1 if enabled_for_publico else 0)
        
        if enabled_for_secs is not None:
            updates.append("enabled_for_secs = ?")
            params.append(1 if enabled_for_secs else 0)
        
        if enabled_for_admin is not None:
            updates.append("enabled_for_admin = ?")
            params.append(1 if enabled_for_admin else 0)
        
        if not updates:
            return False
        
        params.append(feature_name)
        
        cursor = self.conn.execute(
            f"UPDATE feature_flags SET {', '.join(updates)} WHERE feature_name = ?",
            params
        )
        self.conn.commit()
        
        return cursor.rowcount > 0
    
    def get_enabled_features_for_role(self, user_role: str) -> List[str]:
        """
        Get list of enabled features for a role.
        
        Args:
            user_role: User role
            
        Returns:
            List of enabled feature names
        """
        role_column = f"enabled_for_{user_role}"
        
        cursor = self.conn.execute(
            f"SELECT feature_name FROM feature_flags WHERE {role_column} = 1"
        )
        
        return [row[0] for row in cursor.fetchall()]


# Singleton
_feature_flags_service = None

def get_feature_flags_service(db_path: str = None) -> FeatureFlagsService:
    """Get or create feature flags service singleton"""
    global _feature_flags_service
    if _feature_flags_service is None:
        if db_path is None:
            from src.config import get_settings
            db_path = str(get_settings().db_path_resolved)
        _feature_flags_service = FeatureFlagsService(db_path)
    return _feature_flags_service
