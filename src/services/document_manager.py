#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Gerenciador de Documentos
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Gerenciamento de upload e processamento de documentos com quotas
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, BinaryIO
import hashlib
from dataclasses import dataclass

from config import get_settings

settings = get_settings()


@dataclass
class Document:
    """Modelo de documento"""
    id: int
    filename: str
    original_name: str
    user_id: str
    is_global: bool
    file_size: int
    upload_date: str
    processed: bool
    num_chunks: int
    status: str


@dataclass
class UserQuota:
    """Modelo de quota de usuário"""
    user_id: str
    quota_mb: int
    used_mb: float
    last_updated: str


class DocumentManager:
    """Gerenciador de documentos com quotas"""
    
    # Quotas padrão por role (em MB)
    DEFAULT_QUOTAS = {
        "publico": 10,
        "secs": 50,
        "admin": 500
    }
    
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or settings.db_path_resolved
        self.docs_dir = Path("data/documents")
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Inicializa tabelas do banco"""
        conn = sqlite3.connect(self.db_path)
        
        # Tabela de documentos
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                original_name TEXT NOT NULL,
                user_id TEXT NOT NULL,
                is_global BOOLEAN DEFAULT 0,
                file_size INTEGER NOT NULL,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed BOOLEAN DEFAULT 0,
                num_chunks INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending'
            )
        """)
        
        # Tabela de quotas
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_quotas (
                user_id TEXT PRIMARY KEY,
                quota_mb INTEGER NOT NULL,
                used_mb REAL DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def get_user_quota(self, user_id: str, role: str = "publico") -> UserQuota:
        """Obtém quota do usuário"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT user_id, quota_mb, used_mb, last_updated FROM user_quotas WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return UserQuota(*row)
        else:
            # Criar quota padrão baseada no role
            default_quota = self.DEFAULT_QUOTAS.get(role, 10)
            self._create_user_quota(user_id, default_quota)
            return UserQuota(user_id, default_quota, 0.0, datetime.now().isoformat())
    
    def _create_user_quota(self, user_id: str, quota_mb: int):
        """Cria quota para usuário"""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO user_quotas (user_id, quota_mb, used_mb) VALUES (?, ?, 0)",
            (user_id, quota_mb)
        )
        conn.commit()
        conn.close()
    
    def update_user_quota(self, user_id: str, new_quota_mb: int):
        """Atualiza quota do usuário (admin only)"""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "UPDATE user_quotas SET quota_mb = ?, last_updated = CURRENT_TIMESTAMP WHERE user_id = ?",
            (new_quota_mb, user_id)
        )
        conn.commit()
        conn.close()
    
    def _update_used_quota(self, user_id: str):
        """Atualiza espaço usado pelo usuário"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT SUM(file_size) FROM documents WHERE user_id = ? AND is_global = 0",
            (user_id,)
        )
        total_bytes = cursor.fetchone()[0] or 0
        used_mb = total_bytes / (1024 * 1024)
        
        conn.execute(
            "UPDATE user_quotas SET used_mb = ?, last_updated = CURRENT_TIMESTAMP WHERE user_id = ?",
            (used_mb, user_id)
        )
        conn.commit()
        conn.close()
    
    def upload_document(
        self,
        file: BinaryIO,
        original_name: str,
        user_id: str,
        role: str = "publico",
        is_global: bool = False
    ) -> Optional[Document]:
        """
        Faz upload de documento.
        
        Returns:
            Document se sucesso, None se excedeu quota
        """
        # Ler arquivo
        file_content = file.read()
        file_size = len(file_content)
        file_size_mb = file_size / (1024 * 1024)
        
        # Verificar quota (apenas para documentos não-globais)
        if not is_global:
            quota = self.get_user_quota(user_id, role)
            if quota.used_mb + file_size_mb > quota.quota_mb:
                return None  # Quota excedida
        
        # Gerar nome único
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_hash = hashlib.md5(file_content).hexdigest()[:8]
        filename = f"{timestamp}_{file_hash}_{original_name}"
        
        # Determinar diretório
        if is_global:
            doc_dir = self.docs_dir / "global"
        else:
            doc_dir = self.docs_dir / "users" / user_id
        
        doc_dir.mkdir(parents=True, exist_ok=True)
        file_path = doc_dir / filename
        
        # Salvar arquivo
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Registrar no banco
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            """INSERT INTO documents 
            (filename, original_name, user_id, is_global, file_size, status)
            VALUES (?, ?, ?, ?, ?, 'pending')""",
            (filename, original_name, user_id, is_global, file_size)
        )
        doc_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Atualizar quota
        if not is_global:
            self._update_used_quota(user_id)
        
        # Retornar documento
        return self.get_document(doc_id)
    
    def delete_document(self, doc_id: int, user_id: str, is_admin: bool = False) -> bool:
        """Exclui documento"""
        doc = self.get_document(doc_id)
        if not doc:
            return False
        
        # Verificar permissão
        if not is_admin and doc.user_id != user_id:
            return False
        
        # Determinar path
        if doc.is_global:
            file_path = self.docs_dir / "global" / doc.filename
        else:
            file_path = self.docs_dir / "users" / doc.user_id / doc.filename
        
        # Excluir arquivo
        if file_path.exists():
            file_path.unlink()
        
        # Excluir do banco
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()
        conn.close()
        
        # Atualizar quota
        if not doc.is_global:
            self._update_used_quota(doc.user_id)
        
        return True
    
    def get_document(self, doc_id: int) -> Optional[Document]:
        """Obtém documento por ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            """SELECT id, filename, original_name, user_id, is_global, file_size,
            upload_date, processed, num_chunks, status
            FROM documents WHERE id = ?""",
            (doc_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Document(*row)
        return None
    
    def list_user_documents(self, user_id: str) -> List[Document]:
        """Lista documentos do usuário"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            """SELECT id, filename, original_name, user_id, is_global, file_size,
            upload_date, processed, num_chunks, status
            FROM documents WHERE user_id = ? OR is_global = 1
            ORDER BY upload_date DESC""",
            (user_id,)
        )
        docs = [Document(*row) for row in cursor.fetchall()]
        conn.close()
        return docs
    
    def list_all_documents(self) -> List[Document]:
        """Lista todos os documentos (admin only)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            """SELECT id, filename, original_name, user_id, is_global, file_size,
            upload_date, processed, num_chunks, status
            FROM documents ORDER BY upload_date DESC"""
        )
        docs = [Document(*row) for row in cursor.fetchall()]
        conn.close()
        return docs
    
    def update_document_status(self, doc_id: int, status: str, processed: bool = False, num_chunks: int = 0):
        """Atualiza status do documento após processamento"""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "UPDATE documents SET status = ?, processed = ?, num_chunks = ? WHERE id = ?",
            (status, processed, num_chunks, doc_id)
        )
        conn.commit()
        conn.close()
    
    def get_stats(self) -> Dict:
        """Obtém estatísticas gerais"""
        conn = sqlite3.connect(self.db_path)
        
        # Total de documentos
        cursor = conn.execute("SELECT COUNT(*) FROM documents")
        total_docs = cursor.fetchone()[0]
        
        # Total de espaço usado
        cursor = conn.execute("SELECT SUM(file_size) FROM documents")
        total_bytes = cursor.fetchone()[0] or 0
        total_mb = total_bytes / (1024 * 1024)
        
        # Documentos por usuário
        cursor = conn.execute(
            "SELECT user_id, COUNT(*) FROM documents WHERE is_global = 0 GROUP BY user_id"
        )
        docs_by_user = dict(cursor.fetchall())
        
        # Documentos globais
        cursor = conn.execute("SELECT COUNT(*) FROM documents WHERE is_global = 1")
        global_docs = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_documents": total_docs,
            "total_mb": round(total_mb, 2),
            "documents_by_user": docs_by_user,
            "global_documents": global_docs,
            "active_users": len(docs_by_user)
        }


def get_document_manager() -> DocumentManager:
    """Factory function"""
    return DocumentManager()
