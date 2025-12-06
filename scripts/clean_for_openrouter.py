#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
Script para limpar embeddings incompatíveis e preparar para OpenRouter
"""

import sqlite3
import shutil
from datetime import datetime
import sys

def clean_and_prepare():
    """Limpa embeddings incompatíveis e prepara para OpenRouter"""
    
    db_path = "data/app.db"
    
    print("🔄 Preparando migração para OpenRouter...\n")
    
    # 1. Fazer backup
    backup_path = f"data/app.db.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"📦 Fazendo backup: {backup_path}")
    shutil.copy2(db_path, backup_path)
    print(f"✅ Backup criado!\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 2. Verificar embeddings atuais
    cursor.execute("""
        SELECT LENGTH(embedding) as size, COUNT(*) as count
        FROM chunks
        WHERE embedding IS NOT NULL
        GROUP BY LENGTH(embedding)
    """)
    
    print("📊 Embeddings atuais:")
    print("-" * 50)
    total_chunks = 0
    incompatible = 0
    
    for row in cursor.fetchall():
        size, count = row
        total_chunks += count
        expected = 1536 * 4  # 6144 bytes para 1536 dims
        
        if size == expected:
            print(f"✅ {count:4d} chunks com {size:5d} bytes (1536 dims) - OK")
        else:
            dims = size // 4
            print(f"❌ {count:4d} chunks com {size:5d} bytes ({dims} dims) - INCOMPATÍVEL")
            incompatible += count
    
    print("-" * 50)
    print(f"Total: {total_chunks} chunks")
    print(f"Incompatíveis: {incompatible} chunks\n")
    
    if incompatible == 0:
        print("✅ Todos os embeddings já são compatíveis!")
        conn.close()
        return
    
    # 3. Confirmar limpeza
    print("⚠️ ATENÇÃO: Isso vai:")
    print(f"  1. Excluir TODOS os {total_chunks} chunks")
    print("  2. Marcar documentos para reprocessamento")
    print("  3. Você precisará:")
    print("     a) Reprocessar documentos base")
    print("     b) Fazer upload novamente dos PDFs do usuário")
    print(f"\n📦 Backup salvo em: {backup_path}")
    
    response = input("\nDigite 'LIMPAR' para continuar: ").strip()
    
    if response != 'LIMPAR':
        print("❌ Operação cancelada")
        conn.close()
        return
    
    # 4. Limpar chunks
    print("\n🗑️ Excluindo chunks...")
    cursor.execute("DELETE FROM chunks")
    deleted = cursor.rowcount
    print(f"✅ {deleted} chunks excluídos")
    
    # 5. Marcar documentos como não processados
    print("\n📝 Marcando documentos para reprocessamento...")
    cursor.execute("""
        UPDATE documents 
        SET processed = 0, num_chunks = 0, status = 'pending'
    """)
    updated = cursor.rowcount
    print(f"✅ {updated} documentos marcados")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Limpeza completa!")
    print("\n📋 PRÓXIMOS PASSOS:")
    print("\n1️⃣ Reprocessar documentos base:")
    print("   python3 src/scripts/ingest_documents.py")
    print("\n2️⃣ Fazer upload dos PDFs do usuário:")
    print("   - Abrir: streamlit run src/app_enhanced.py")
    print("   - Ir em 'Meus Documentos'")
    print("   - Upload do REGIMENTO - PPGMCC 2018.pdf")
    print("\n3️⃣ Testar busca:")
    print("   - Perguntar: 'Como o colegiado do PPGMCC se reúne?'")
    print("   - Verificar se PPGMCC aparece nas fontes")
    print(f"\n💾 Se algo der errado, restaure: cp {backup_path} {db_path}")

if __name__ == "__main__":
    try:
        clean_and_prepare()
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
