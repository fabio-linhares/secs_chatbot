#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
Script para limpar chunks com embeddings incompatíveis
"""

import sqlite3
import sys

def clean_incompatible_chunks():
    """Remove chunks do documento PPGMCC com embeddings incompatíveis"""
    
    db_path = "data/app.db"
    
    print("🔍 Verificando chunks incompatíveis...\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar tamanho dos embeddings
    cursor.execute("""
        SELECT documento_id, COUNT(*) as total, LENGTH(embedding) as emb_size
        FROM chunks
        GROUP BY documento_id, LENGTH(embedding)
        ORDER BY documento_id
    """)
    
    print("📊 Tamanhos de embeddings por documento:")
    print("-" * 60)
    
    incompatible_docs = []
    for row in cursor.fetchall():
        doc_id, count, emb_size = row
        expected_size = 384 * 4  # sentence-transformers: 384 dims * 4 bytes
        
        status = "✅" if emb_size == expected_size else "❌"
        print(f"{status} Doc ID {doc_id}: {count} chunks, {emb_size} bytes/embedding")
        
        if emb_size != expected_size:
            incompatible_docs.append(doc_id)
    
    print("-" * 60)
    
    if not incompatible_docs:
        print("\n✅ Todos os embeddings são compatíveis!")
        conn.close()
        return
    
    print(f"\n⚠️ Encontrados {len(incompatible_docs)} documento(s) com embeddings incompatíveis")
    print(f"   IDs: {incompatible_docs}")
    
    # Perguntar confirmação
    print("\n🗑️ Deseja excluir os chunks incompatíveis?")
    print("   (Você poderá fazer upload novamente com embeddings corretos)")
    
    response = input("\nDigite 'sim' para confirmar: ").strip().lower()
    
    if response != 'sim':
        print("❌ Operação cancelada")
        conn.close()
        return
    
    # Excluir chunks incompatíveis
    total_deleted = 0
    for doc_id in incompatible_docs:
        cursor.execute("SELECT COUNT(*) FROM chunks WHERE documento_id = ?", (doc_id,))
        count = cursor.fetchone()[0]
        
        cursor.execute("DELETE FROM chunks WHERE documento_id = ?", (doc_id,))
        total_deleted += count
        
        print(f"  🗑️ Excluídos {count} chunks do documento ID {doc_id}")
    
    # Também marcar documentos como não processados
    for doc_id in incompatible_docs:
        cursor.execute("""
            UPDATE documents 
            SET processed = 0, num_chunks = 0, status = 'pending'
            WHERE id = ?
        """, (doc_id,))
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Total de {total_deleted} chunks excluídos!")
    print("\n📤 Agora você pode:")
    print("   1. Ir em 'Meus Documentos'")
    print("   2. Excluir o documento PPGMCC")
    print("   3. Fazer upload novamente")
    print("   4. Os novos embeddings serão compatíveis!")

if __name__ == "__main__":
    try:
        clean_incompatible_chunks()
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
