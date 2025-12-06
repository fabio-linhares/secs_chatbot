#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Gerenciador de Migração de Embeddings
============================================================================
Versão: 7.1
Data: 2025-12-04
Descrição: Detecta mudanças de embedding e migra automaticamente
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import sqlite3
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings


class EmbeddingMigrationManager:
    """
    Gerencia migrações automáticas de embeddings.
    
    Detecta quando o provider/modelo de embedding mudou e
    reprocessa documentos automaticamente.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.db_path_resolved
        self.metadata_table = "embedding_metadata"
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def _ensure_metadata_table(self):
        """Create metadata table if not exists"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.metadata_table} (
                id INTEGER PRIMARY KEY,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                dimension INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                num_documents INTEGER DEFAULT 0,
                num_chunks INTEGER DEFAULT 0
            )
        """)
        
        conn.commit()
        conn.close()
    
    def get_current_metadata(self) -> Optional[Dict]:
        """Get current embedding metadata from database"""
        self._ensure_metadata_table()
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT provider, model, dimension, num_documents, num_chunks, created_at
            FROM {self.metadata_table}
            ORDER BY id DESC
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'provider': row[0],
                'model': row[1],
                'dimension': row[2],
                'num_documents': row[3],
                'num_chunks': row[4],
                'created_at': row[5]
            }
        return None
    
    def save_metadata(self, num_documents: int = 0, num_chunks: int = 0):
        """Save current embedding configuration to database"""
        self._ensure_metadata_table()
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"""
            INSERT INTO {self.metadata_table} 
            (provider, model, dimension, num_documents, num_chunks)
            VALUES (?, ?, ?, ?, ?)
        """, (
            settings.embedding_provider,
            settings.embedding_model,
            settings.embedding_dimension,
            num_documents,
            num_chunks
        ))
        
        conn.commit()
        conn.close()
    
    def needs_migration(self) -> tuple[bool, str]:
        """
        Check if migration is needed.
        
        Returns:
            (needs_migration, reason)
        """
        current = self.get_current_metadata()
        
        if not current:
            return False, "Primeira inicialização - sem migração necessária"
        
        # Check provider change
        if current['provider'] != settings.embedding_provider:
            return True, (
                f"Provider mudou: {current['provider']} → {settings.embedding_provider}"
            )
        
        # Check model change
        if current['model'] != settings.embedding_model:
            return True, (
                f"Modelo mudou: {current['model']} → {settings.embedding_model}"
            )
        
        # Check dimension change
        if current['dimension'] != settings.embedding_dimension:
            return True, (
                f"Dimensão mudou: {current['dimension']} → {settings.embedding_dimension}"
            )
        
        return False, "Configuração de embedding não mudou"
    
    def backup_database(self) -> str:
        """Create backup of database"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(self.db_path).parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        backup_path = backup_dir / f"app_backup_{timestamp}.db"
        
        import shutil
        shutil.copy2(self.db_path, backup_path)
        
        return str(backup_path)
    
    def clear_embeddings(self) -> int:
        """
        Clear all embeddings from database.
        
        Returns:
            Number of chunks deleted
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get count before deletion
        cursor.execute("SELECT COUNT(*) FROM chunks")
        count = cursor.fetchone()[0]
        
        # Delete all chunks
        cursor.execute("DELETE FROM chunks")
        
        conn.commit()
        conn.close()
        
        return count
    
    def reprocess_documents(self) -> Dict:
        """
        Reprocess all documents with new embedding configuration.
        
        Returns:
            Statistics about reprocessing
        """
        from services.document_processor import DocumentProcessor
        from services.embeddings import get_embedding_service
        from services.vector_store import get_vector_store
        
        print("🔄 Iniciando reprocessamento de documentos...")
        
        # Get document processor
        processor = DocumentProcessor()
        embedding_service = get_embedding_service()
        vector_store = get_vector_store()
        
        # Get all unique documents
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Note: This assumes documents are stored somewhere
        # You may need to adjust based on your actual storage
        cursor.execute("""
            SELECT DISTINCT source_file 
            FROM chunks 
            WHERE source_file IS NOT NULL
        """)
        
        documents = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if not documents:
            print("⚠️  Nenhum documento encontrado para reprocessar")
            return {
                'documents_processed': 0,
                'chunks_created': 0,
                'errors': 0
            }
        
        stats = {
            'documents_processed': 0,
            'chunks_created': 0,
            'errors': 0
        }
        
        for doc_path in documents:
            try:
                print(f"📄 Processando: {doc_path}")
                
                # Process document
                chunks = processor.process_document(doc_path)
                
                # Generate embeddings and store
                for chunk in chunks:
                    embedding = embedding_service.generate_embedding(chunk['content'])
                    vector_store.add_chunk(
                        content=chunk['content'],
                        embedding=embedding,
                        metadata=chunk.get('metadata', {})
                    )
                    stats['chunks_created'] += 1
                
                stats['documents_processed'] += 1
                
            except Exception as e:
                print(f"❌ Erro ao processar {doc_path}: {e}")
                stats['errors'] += 1
        
        return stats
    
    def migrate(self, auto_confirm: bool = False) -> bool:
        """
        Execute full migration process.
        
        Args:
            auto_confirm: If True, skip confirmation prompts
            
        Returns:
            True if migration successful, False otherwise
        """
        needs_mig, reason = self.needs_migration()
        
        if not needs_mig:
            print(f"✅ {reason}")
            return True
        
        print(f"\n⚠️  MIGRAÇÃO NECESSÁRIA")
        print(f"   Motivo: {reason}")
        print(f"\n   Configuração Atual:")
        
        current = self.get_current_metadata()
        if current:
            print(f"   - Provider: {current['provider']}")
            print(f"   - Modelo: {current['model']}")
            print(f"   - Dimensão: {current['dimension']}")
            print(f"   - Documentos: {current['num_documents']}")
            print(f"   - Chunks: {current['num_chunks']}")
        
        print(f"\n   Nova Configuração:")
        print(f"   - Provider: {settings.embedding_provider}")
        print(f"   - Modelo: {settings.embedding_model}")
        print(f"   - Dimensão: {settings.embedding_dimension}")
        
        if not auto_confirm:
            response = input("\n   Continuar com migração? (s/n): ")
            if response.lower() != 's':
                print("❌ Migração cancelada")
                return False
        
        try:
            # 1. Backup
            print("\n1️⃣ Criando backup...")
            backup_path = self.backup_database()
            print(f"   ✅ Backup criado: {backup_path}")
            
            # 2. Clear old embeddings
            print("\n2️⃣ Limpando embeddings antigos...")
            deleted = self.clear_embeddings()
            print(f"   ✅ {deleted} chunks removidos")
            
            # 3. Reprocess documents
            print("\n3️⃣ Reprocessando documentos...")
            stats = self.reprocess_documents()
            print(f"   ✅ Documentos processados: {stats['documents_processed']}")
            print(f"   ✅ Chunks criados: {stats['chunks_created']}")
            if stats['errors'] > 0:
                print(f"   ⚠️  Erros: {stats['errors']}")
            
            # 4. Save new metadata
            print("\n4️⃣ Salvando nova configuração...")
            self.save_metadata(
                num_documents=stats['documents_processed'],
                num_chunks=stats['chunks_created']
            )
            print("   ✅ Metadados atualizados")
            
            print("\n🎉 Migração concluída com sucesso!")
            return True
            
        except Exception as e:
            print(f"\n❌ Erro durante migração: {e}")
            print(f"   Restaure o backup: {backup_path}")
            return False


def check_and_migrate(auto_confirm: bool = False) -> bool:
    """
    Check if migration is needed and execute if necessary.
    
    This function should be called at application startup.
    
    Args:
        auto_confirm: If True, skip confirmation prompts
        
    Returns:
        True if no migration needed or migration successful
    """
    manager = EmbeddingMigrationManager()
    
    needs_mig, reason = manager.needs_migration()
    
    if not needs_mig:
        # Save metadata if first time
        current = manager.get_current_metadata()
        if not current:
            print("📝 Primeira inicialização - salvando configuração de embedding")
            manager.save_metadata()
        return True
    
    # Migration needed
    return manager.migrate(auto_confirm=auto_confirm)


if __name__ == "__main__":
    # Allow running as standalone script
    import argparse
    
    parser = argparse.ArgumentParser(description="Gerenciador de Migração de Embeddings")
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Executar migração automaticamente sem confirmação"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Apenas verificar se migração é necessária"
    )
    
    args = parser.parse_args()
    
    manager = EmbeddingMigrationManager()
    
    if args.check_only:
        needs_mig, reason = manager.needs_migration()
        print(f"Migração necessária: {needs_mig}")
        print(f"Motivo: {reason}")
        sys.exit(0 if not needs_mig else 1)
    
    success = check_and_migrate(auto_confirm=args.auto)
    sys.exit(0 if success else 1)
