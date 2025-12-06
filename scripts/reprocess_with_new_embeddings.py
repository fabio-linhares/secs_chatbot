#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Reprocessamento com novos embeddings
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Script para reprocessar documentos com novos embeddings
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import sqlite3
import sys

def reprocess_documents():
    """Limpa embeddings antigos e marca documentos para reprocessamento"""
    
    db_path = "data/app.db"
    
    print("🔄 Reprocessando documentos com novos embeddings...\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Contar chunks atuais
    cursor.execute("SELECT COUNT(*) FROM chunks")
    total_chunks = cursor.fetchone()[0]
    
    print(f"📊 Chunks atuais: {total_chunks}")
    
    # Perguntar confirmação
    print("\n⚠️ ATENÇÃO: Isso vai:")
    print("  1. Excluir TODOS os chunks existentes")
    print("  2. Marcar documentos para reprocessamento")
    print("  3. Você precisará reprocessar os documentos base")
    print("  4. E fazer upload novamente dos documentos do usuário")
    
    response = input("\nDigite 'CONFIRMAR' para continuar: ").strip()
    
    if response != 'CONFIRMAR':
        print("❌ Operação cancelada")
        conn.close()
        return
    
    # Excluir todos os chunks
    print("\n🗑️ Excluindo chunks antigos...")
    cursor.execute("DELETE FROM chunks")
    deleted = cursor.rowcount
    print(f"  ✅ {deleted} chunks excluídos")
    
    # Marcar documentos como não processados
    print("\n📝 Marcando documentos para reprocessamento...")
    cursor.execute("""
        UPDATE documents 
        SET processed = 0, num_chunks = 0, status = 'pending'
    """)
    updated = cursor.rowcount
    print(f"  ✅ {updated} documentos marcados")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Reprocessamento preparado!")
    print("\n📋 Próximos passos:")
    print("  1. Reprocessar documentos base:")
    print("     python src/scripts/ingest_documents.py")
    print("\n  2. Fazer upload novamente dos PDFs do usuário:")
    print("     - Ir em 'Meus Documentos'")
    print("     - Fazer upload dos PDFs")
    print("\n  3. Testar busca:")
    print("     - Perguntar sobre PPGMCC no chat")
    print("     - Verificar se documento aparece nas fontes")

if __name__ == "__main__":
    try:
        reprocess_documents()
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
