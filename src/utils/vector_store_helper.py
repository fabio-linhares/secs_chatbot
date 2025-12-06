#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Helper para adicionar chunks ao vector store
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Função auxiliar para adicionar chunks processados ao vector store
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import sqlite3
import json
import numpy as np
from typing import List, Dict
from pathlib import Path


def add_chunks_to_vector_store(chunks: List[Dict], db_path: str = "data/app.db"):
    """
    Adiciona chunks diretamente ao vector store.
    Usa o MESMO modelo de embeddings configurado no .env!
    
    Args:
        chunks: Lista de dicts com 'text' e metadata
        db_path: Caminho para o banco de dados
    """
    # Import aqui para evitar problemas de inicialização
    import sys
    import os
    
    # Garantir que src está no path
    src_path = os.path.join(os.getcwd(), 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    # Importar serviço de embeddings (usa configuração do .env)
    try:
        from services.embeddings import get_embedding_service
        
        print(f"🔢 Inicializando serviço de embeddings...")
        embedding_service = get_embedding_service()
        print(f"✅ Usando modelo: {embedding_service.model_name}")
        
    except Exception as e:
        print(f"❌ Erro ao inicializar embeddings: {e}")
        print("\n⚠️ Verifique se:")
        print("  1. O .env está configurado corretamente")
        print("  2. Se EMBEDDING_PROVIDER=local, instale: pip install sentence-transformers")
        print("  3. Se EMBEDDING_PROVIDER=openai, configure OPENAI_API_KEY")
        raise
    
    # Gerar embeddings
    print(f"🔢 Gerando embeddings para {len(chunks)} chunks...")
    embeddings = []
    
    for i, chunk in enumerate(chunks):
        if i % 10 == 0:
            print(f"  Processando chunk {i+1}/{len(chunks)}...")
        
        try:
            emb = embedding_service.generate_embedding(chunk["text"])
            embeddings.append(emb)
        except Exception as e:
            print(f"❌ Erro ao gerar embedding do chunk {i+1}: {e}")
            raise
    
    # Inserir no banco
    print(f"💾 Inserindo chunks no banco de dados...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for chunk, embedding in zip(chunks, embeddings):
        # Serializar embedding
        embedding_blob = embedding.tobytes()
        
        # Preparar metadata
        metadata = chunk.get("metadata", {})
        metadata_json = json.dumps(metadata, ensure_ascii=False)
        
        # Inserir chunk
        cursor.execute("""
            INSERT INTO chunks (documento_id, conteudo, embedding, metadata, posicao)
            VALUES (?, ?, ?, ?, ?)
        """, (
            metadata.get("doc_id", 0),
            chunk["text"],
            embedding_blob,
            metadata_json,
            chunk.get("page", 0)
        ))
    
    conn.commit()
    conn.close()
    print(f"✅ {len(chunks)} chunks adicionados com sucesso!")
