#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Teste de embeddings via OpenRouter
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Script para testar geração de embeddings via OpenRouter
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import sys
sys.path.insert(0, 'src')

print("🧪 Testando embeddings via OpenRouter...\n")

try:
    from services.embeddings import get_embedding_service
    
    service = get_embedding_service()
    print(f"✅ Serviço inicializado:")
    print(f"  Provider: {service.provider}")
    print(f"  Model: {service.model_name}")
    print(f"  Dimension: {service.dimension}")
    
    # Testar embedding
    test_text = "Como o colegiado do PPGMCC se reúne?"
    print(f"\n🔢 Gerando embedding para: '{test_text}'")
    
    emb = service.generate_embedding(test_text)
    
    print(f"\n✅ Embedding gerado:")
    print(f"  Dimensão: {len(emb)}")
    print(f"  Tamanho: {len(emb.tobytes())} bytes")
    print(f"  Tipo: {emb.dtype}")
    print(f"  Primeiros 5 valores: {emb[:5]}")
    
    # Verificar compatibilidade
    expected_size = 1536 * 4  # 1536 dims * 4 bytes (float32)
    if len(emb.tobytes()) == expected_size:
        print(f"\n✅ PERFEITO! Embeddings compatíveis com documentos existentes!")
        print(f"   Dimensão: 1536 (igual aos docs base)")
        print(f"   Agora upload de PDFs vai funcionar!")
    else:
        print(f"\n⚠️ Tamanho inesperado (esperado: {expected_size})")
        
except Exception as e:
    print(f"\n❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    
    print("\n💡 Dicas:")
    print("  1. Verifique se atualizou o .env corretamente")
    print("  2. Confirme que LLM_API_KEY está configurada")
    print("  3. Teste a chave OpenRouter em: https://openrouter.ai/")
