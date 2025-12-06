#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
Script para converter embeddings de documentos específicos
Converte apenas docs do usuário, mantém docs base intactos
"""

import sqlite3
import sys
import json

def convert_user_documents():
    """Converte embeddings de documentos do usuário para modelo local"""
    
    db_path = "data/app.db"
    
    print("🔄 Convertendo embeddings de documentos do usuário...\n")
    
    # Importar serviço
    sys.path.insert(0, 'src')
    from services.embeddings import get_embedding_service
    
    embedding_service = get_embedding_service()
    print(f"✅ Usando: {embedding_service.model_name}")
    print(f"   Dimensão: {embedding_service.embedding_dimension}\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Encontrar documentos do usuário (não globais, não base)
    cursor.execute("""
        SELECT id, original_name, user_id
        FROM documents
        WHERE is_global = 0 AND user_id != 'system'
        ORDER BY id
    """)
    
    user_docs = cursor.fetchall()
    
    if not user_docs:
        print("ℹ️ Nenhum documento de usuário encontrado")
        conn.close()
        return
    
    print(f"📄 Documentos do usuário encontrados: {len(user_docs)}\n")
    for doc_id, name, user_id in user_docs:
        print(f"  • Doc {doc_id}: {name} (user: {user_id})")
    
    print("\n⚠️ Isso vai:")
    print("  1. Excluir chunks desses documentos")
    print("  2. Reprocessar com embeddings locais")
    print("  3. Manter documentos base intactos")
    
    response = input("\nDigite 'sim' para continuar: ").strip().lower()
    
    if response != 'sim':
        print("❌ Operação cancelada")
        conn.close()
        return
    
    # Para cada documento do usuário
    for doc_id, doc_name, user_id in user_docs:
        print(f"\n🔄 Processando: {doc_name}")
        
        # Buscar chunks
        cursor.execute("""
            SELECT id, conteudo, metadata
            FROM chunks
            WHERE documento_id = ?
        """, (doc_id,))
        
        chunks = cursor.fetchall()
        print(f"  📊 {len(chunks)} chunks encontrados")
        
        if not chunks:
            continue
        
        # Excluir chunks antigos
        cursor.execute("DELETE FROM chunks WHERE documento_id = ?", (doc_id,))
        print(f"  🗑️ Chunks antigos excluídos")
        
        # Gerar novos embeddings
        print(f"  🔢 Gerando novos embeddings...")
        new_chunks = []
        
        for i, (chunk_id, conteudo, metadata_json) in enumerate(chunks):
            if i % 10 == 0:
                print(f"    Chunk {i+1}/{len(chunks)}...")
            
            # Gerar embedding
            emb = embedding_service.generate_embedding(conteudo)
            emb_blob = emb.tobytes()
            
            # Preparar para inserção
            metadata = json.loads(metadata_json) if metadata_json else {}
            new_chunks.append((doc_id, conteudo, emb_blob, metadata_json, metadata.get('posicao', 0)))
        
        # Inserir novos chunks
        cursor.executemany("""
            INSERT INTO chunks (documento_id, conteudo, embedding, metadata, posicao)
            VALUES (?, ?, ?, ?, ?)
        """, new_chunks)
        
        print(f"  ✅ {len(new_chunks)} chunks com novos embeddings inseridos")
        
        # Atualizar status do documento
        cursor.execute("""
            UPDATE documents
            SET processed = 1, num_chunks = ?, status = 'processed'
            WHERE id = ?
        """, (len(new_chunks), doc_id))
    
    conn.commit()
    conn.close()
    
    print("\n✅ Conversão completa!")
    print("\n📋 Próximos passos:")
    print("  1. Testar busca no chat")
    print("  2. Perguntar sobre PPGMCC")
    print("  3. Verificar se documento aparece nas fontes")

if __name__ == "__main__":
    try:
        convert_user_documents()
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
