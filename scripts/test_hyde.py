#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Teste HyDE (Hypothetical Document Embeddings)
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Script de teste para HyDE (Hypothetical Document Embeddings)
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import sys
sys.path.insert(0, 'src')

from services.hyde_query_expander import get_hyde_expander
from services.vector_store import get_vector_store

def test_hyde():
    """Test HyDE with the problematic query"""
    
    print("="*70)
    print("🔬 Testando HyDE (Hypothetical Document Embeddings)")
    print("="*70)
    
    # Initialize services
    hyde = get_hyde_expander()
    vs = get_vector_store()
    
    # Test query
    query = "como o conselho da pós de modelagem se reune?"
    
    print(f"\n📝 Pergunta original: {query}")
    print("\n" + "-"*70)
    
    # 1. Standard search (baseline)
    print("\n1️⃣ BUSCA PADRÃO (Baseline):")
    print("-"*70)
    
    standard_results = vs.search(query, k=5, user_id='admin')
    
    print(f"\n📊 Top 5 resultados:")
    for i, r in enumerate(standard_results, 1):
        is_ppgmcc = 'PPGMCC' in r.get('titulo', '')
        marker = "🎯" if is_ppgmcc else "  "
        print(f"{marker} {i}. {r['similarity']:.1%} - {r.get('titulo', 'N/A')[:50]}")
    
    # 2. HyDE search
    print("\n\n2️⃣ BUSCA COM HyDE:")
    print("-"*70)
    
    # Generate hypothesis
    print("\n🔄 Gerando hipótese...")
    hyde_result = hyde.expand_query(query, conversation_history=None)
    
    print(f"\n📋 Análise de contexto:")
    print(f"   Conselho: {hyde_result.analysis.get('conselho', 'N/A')}")
    print(f"   Tipo doc: {hyde_result.analysis.get('tipo_documento', 'N/A')}")
    print(f"   Confiança: {hyde_result.confidence:.1%}")
    
    print(f"\n💡 Resposta hipotética gerada:")
    print(f"   {hyde_result.hypothetical_answer[:200]}...")
    
    # Search using hypothesis embedding
    hyde_results = vs.search_by_embedding(
        hyde_result.answer_embedding,
        k=5,
        user_id='admin'
    )
    
    print(f"\n📊 Top 5 resultados (HyDE):")
    for i, r in enumerate(hyde_results, 1):
        is_ppgmcc = 'PPGMCC' in r.get('titulo', '')
        marker = "🎯" if is_ppgmcc else "  "
        print(f"{marker} {i}. {r['similarity']:.1%} - {r.get('titulo', 'N/A')[:50]}")
    
    # 3. Comparison
    print("\n\n3️⃣ COMPARAÇÃO:")
    print("-"*70)
    
    # Find PPGMCC in results
    standard_ppgmcc = [r for r in standard_results if 'PPGMCC' in r.get('titulo', '')]
    hyde_ppgmcc = [r for r in hyde_results if 'PPGMCC' in r.get('titulo', '')]
    
    print(f"\n📈 PPGMCC encontrado:")
    print(f"   Padrão: {'✅ Sim' if standard_ppgmcc else '❌ Não'}")
    if standard_ppgmcc:
        print(f"   Similaridade: {standard_ppgmcc[0]['similarity']:.1%}")
    
    print(f"\n   HyDE:   {'✅ Sim' if hyde_ppgmcc else '❌ Não'}")
    if hyde_ppgmcc:
        print(f"   Similaridade: {hyde_ppgmcc[0]['similarity']:.1%}")
    
    # Calculate improvement
    if standard_ppgmcc and hyde_ppgmcc:
        improvement = hyde_ppgmcc[0]['similarity'] - standard_ppgmcc[0]['similarity']
        print(f"\n📊 Melhoria: {improvement:+.1%}")
        
        if improvement > 0:
            print(f"   🎉 HyDE melhorou a busca em {improvement:.1%}!")
        else:
            print(f"   ⚠️ HyDE não melhorou neste caso")
    
    print("\n" + "="*70)
    print("✅ Teste concluído!")
    print("="*70)

if __name__ == "__main__":
    test_hyde()
