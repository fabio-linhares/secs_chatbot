# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
"""
Test script for new services: Count Helper, Prompt Enricher, Semantic Rewriter, Focal Agent
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.count_helper import CountHelper
from src.services.prompt_enricher import PromptEnricher
from src.agents.semantic_rewriter import SemanticRewriter
from src.agents.focal_agent import FocalAgent, TOOLS


def test_count_helper():
    """Test Count Helper"""
    print("=" * 60)
    print("Testing Count Helper")
    print("=" * 60)
    
    helper = CountHelper()
    
    # Test 1: Voting counts
    print("\n1. Testing voting counts...")
    chunks = [{
        'conteudo': 'Votação: 15 votos a favor, 2 contra, 1 abstenção. Aprovado por maioria.'
    }]
    facts = helper.derive_counts("Qual foi o resultado da votação?", chunks)
    assert len(facts) > 0, "Should derive voting facts"
    assert any('15' in f for f in facts), "Should find 15 votes"
    print(f"   ✅ Found {len(facts)} voting facts")
    
    # Test 2: Participants
    print("\n2. Testing participants...")
    chunks = [{
        'conteudo': 'Presentes: João Silva, Maria Santos, Pedro Oliveira'
    }]
    facts = helper.derive_counts("Quem participou?", chunks)
    assert len(facts) > 0, "Should derive participant facts"
    print(f"   ✅ Found {len(facts)} participant facts")
    
    # Test 3: Quorum
    print("\n3. Testing quorum...")
    chunks = [{
        'conteudo': 'Quórum de 20 membros. Quórum atingido.'
    }]
    facts = helper.derive_counts("Teve quórum?", chunks)
    assert len(facts) > 0, "Should derive quorum facts"
    print(f"   ✅ Found {len(facts)} quorum facts")
    
    print("\n" + "=" * 60)
    print("✅ All Count Helper tests passed!")
    print("=" * 60)


def test_prompt_enricher():
    """Test Prompt Enricher"""
    print("\n" + "=" * 60)
    print("Testing Prompt Enricher")
    print("=" * 60)
    
    enricher = PromptEnricher("You are a helpful assistant.")
    
    # Test 1: Context block
    print("\n1. Testing context block...")
    chunks = [
        {
            'titulo': 'Ata CONSUN 01/2024',
            'tipo': 'ata',
            'numero': '01',
            'data': '15/01/2024',
            'conteudo': 'Reunião ordinária...',
            'similarity': 0.95
        }
    ]
    context = enricher.build_context_block(chunks)
    assert 'Ata CONSUN' in context, "Should include title"
    assert '95' in context, "Should include similarity"
    print("   ✅ Context block built")
    
    # Test 2: Full enrichment
    print("\n2. Testing full enrichment...")
    enriched = enricher.enrich(
        user_question="Qual a pauta?",
        chunks=chunks,
        derived_facts=["Fato 1", "Fato 2"]
    )
    assert len(enriched.messages) > 0, "Should have messages"
    assert enriched.metadata['num_chunks'] == 1, "Should track chunks"
    assert enriched.metadata['num_facts'] == 2, "Should track facts"
    print(f"   ✅ Enriched with {len(enriched.messages)} messages")
    
    print("\n" + "=" * 60)
    print("✅ All Prompt Enricher tests passed!")
    print("=" * 60)


def test_semantic_rewriter():
    """Test Semantic Rewriter"""
    print("\n" + "=" * 60)
    print("Testing Semantic Rewriter")
    print("=" * 60)
    
    rewriter = SemanticRewriter()
    
    # Test 1: Heuristics extraction
    print("\n1. Testing heuristics extraction...")
    heuristics = rewriter.extract_heuristics("Qual a pauta da reunião?")
    assert len(heuristics) > 0, "Should extract heuristics"
    assert any('pauta' in h.lower() for h in heuristics), "Should find 'pauta'"
    print(f"   ✅ Extracted {len(heuristics)} heuristics: {heuristics[:3]}")
    
    # Test 2: Date extraction
    print("\n2. Testing date extraction...")
    heuristics = rewriter.extract_heuristics("Reunião de 15/01/2024")
    assert any('15/01/2024' in h for h in heuristics), "Should extract date"
    print("   ✅ Date extraction works")
    
    # Test 3: Enrichment (without LLM)
    print("\n3. Testing enrichment...")
    enrichment = rewriter.enrich("Qual a resolução?", use_llm=False)
    assert enrichment.rewritten, "Should have rewritten query"
    assert enrichment.heuristics, "Should have heuristics"
    print(f"   ✅ Enrichment: {enrichment.rewritten[:50]}...")
    
    print("\n" + "=" * 60)
    print("✅ All Semantic Rewriter tests passed!")
    print("=" * 60)


def test_focal_agent():
    """Test Focal Agent"""
    print("\n" + "=" * 60)
    print("Testing Focal Agent")
    print("=" * 60)
    
    # Test 1: Tool configuration
    print("\n1. Testing tool configuration...")
    assert len(TOOLS) == 7, "Should have 7 tools"
    tool_names = [t.name for t in TOOLS]
    assert 'pauta' in tool_names, "Should have pauta tool"
    assert 'ata' in tool_names, "Should have ata tool"
    assert 'votacao' in tool_names, "Should have votacao tool"
    print(f"   ✅ {len(TOOLS)} tools configured: {tool_names}")
    
    # Test 2: Tool selection (without vector store)
    print("\n2. Testing tool selection...")
    
    class MockVectorStore:
        def search(self, query, k=5):
            return []
        def search_with_filter(self, query, filters, k=5):
            return []
    
    agent = FocalAgent(MockVectorStore())
    
    tool = agent.pick_tool("Qual a pauta?")
    assert tool is not None, "Should pick a tool"
    assert tool.name == "pauta", "Should pick pauta tool"
    print(f"   ✅ Picked tool: {tool.name}")
    
    tool = agent.pick_tool("Quando foi a reunião?")
    assert tool is not None, "Should pick a tool"
    assert tool.name == "data_reuniao", "Should pick data_reuniao tool"
    print(f"   ✅ Picked tool: {tool.name}")
    
    print("\n" + "=" * 60)
    print("✅ All Focal Agent tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_count_helper()
        test_prompt_enricher()
        test_semantic_rewriter()
        test_focal_agent()
        
        print("\n" + "=" * 60)
        print("🎉 ALL NEW SERVICES TESTS PASSED! 🎉")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
