#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Teste de busca vetorial
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Script de depuração para busca vetorial
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.vector_store import get_vector_store
from src.agents.query_enhancer import get_query_enhancer

def test_search():
    print("=" * 60)
    print("Vector Search Debug Test")
    print("=" * 60)
    
    vector_store = get_vector_store()
    query_enhancer = get_query_enhancer()
    
    # Test queries
    queries = [
        "Qual a pauta?",
        "pauta reunião CONSUNI",
        "ordem do dia reunião",
        "itens pauta CONSUNI",
    ]
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        
        # Try query enhancement
        try:
            enhanced = query_enhancer.enhance_query(query, [])
            print(f"Enhanced: {enhanced.enhanced_query}")
            print(f"Confidence: {enhanced.confidence:.2%}")
            search_query = enhanced.enhanced_query
        except Exception as e:
            print(f"Enhancement error: {e}")
            search_query = query
        
        # Search
        results = vector_store.search(search_query, k=5)
        
        print(f"\nTop 5 Results:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['titulo']} ({result['tipo']})")
            print(f"   Similarity: {result['similarity']:.4f}")
            print(f"   Número: {result.get('numero', 'N/A')}")
            print(f"   Preview: {result['conteudo'][:200]}...")

if __name__ == "__main__":
    test_search()
