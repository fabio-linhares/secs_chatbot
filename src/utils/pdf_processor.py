#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Utilitário de processamento de PDFs
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Wrapper para processar PDFs e retornar chunks
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

from pathlib import Path
from typing import List, Dict
from services.document_processor import DocumentProcessor


def process_document(file_path: str) -> List[Dict]:
    """
    Processa um documento e retorna chunks.
    
    Args:
        file_path: Caminho para o arquivo PDF
        
    Returns:
        Lista de dicts com 'text' e 'page'
    """
    processor = DocumentProcessor()
    
    # Processar arquivo
    doc = processor._process_file(file_path)
    
    if not doc:
        raise ValueError(f"Não foi possível processar: {file_path}")
    
    # Criar chunks
    chunks_obj = processor.chunk_document(doc, chunk_size=500, overlap=100)
    
    # Converter para formato esperado
    chunks = []
    for chunk in chunks_obj:
        chunks.append({
            "text": chunk.conteudo,
            "page": chunk.metadata.get("posicao", 0),
            "metadata": chunk.metadata
        })
    
    return chunks
