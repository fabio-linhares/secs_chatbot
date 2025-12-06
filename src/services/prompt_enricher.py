#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Enriquecimento de prompts com contexto
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Enriquecimento de prompts com contexto
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class EnrichedPrompt:
    """Result of prompt enrichment"""
    messages: List[Dict[str, str]]
    metadata: Dict[str, Any]
    context_summary: str


class PromptEnricher:
    """Enriches prompts with context and metadata"""
    
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
    
    def build_context_block(
        self,
        chunks: List[Dict[str, Any]],
        max_chunks: int = 5
    ) -> str:
        """
        Build context block from retrieved chunks.
        
        Args:
            chunks: Retrieved document chunks
            max_chunks: Maximum chunks to include
            
        Returns:
            Formatted context string
        """
        if not chunks:
            return ""
        
        context_parts = []
        for i, chunk in enumerate(chunks[:max_chunks], 1):
            titulo = chunk.get('titulo', 'Documento')
            tipo = chunk.get('tipo', 'N/A')
            numero = chunk.get('numero', 'N/A')
            data = chunk.get('data', 'N/A')
            conteudo = chunk.get('conteudo', '')
            similarity = chunk.get('similarity', 0.0)
            
            context_parts.append(f"""
Fonte {i}: {titulo} ({tipo})
Número: {numero} | Data: {data}
Similaridade: {similarity:.2%}
Conteúdo:
{conteudo}
""".strip())
        
        return "\n\n---\n\n".join(context_parts)
    
    def build_enrichment_info(
        self,
        semantic_enrichment: Optional[Any] = None,
        derived_facts: Optional[List[str]] = None,
        agent_tool: Optional[str] = None
    ) -> str:
        """
        Build enrichment information block.
        
        Args:
            semantic_enrichment: SemanticEnrichment object
            derived_facts: List of derived facts
            agent_tool: Tool used by focal agent
            
        Returns:
            Formatted enrichment info
        """
        parts = []
        
        if semantic_enrichment:
            parts.append(f"**Pergunta reescrita**: {semantic_enrichment.rewritten}")
            
            if semantic_enrichment.heuristics:
                parts.append(f"**Termos heurísticos**: {', '.join(semantic_enrichment.heuristics)}")
            
            if semantic_enrichment.alternates:
                parts.append(f"**Consultas alternativas**: {' | '.join(semantic_enrichment.alternates)}")
        
        if agent_tool:
            parts.append(f"**Ferramenta acionada**: {agent_tool}")
        
        if derived_facts:
            parts.append(f"**Fatos derivados**:\n" + "\n".join(f"- {fact}" for fact in derived_facts))
        
        return "\n\n".join(parts) if parts else ""
    
    def enrich(
        self,
        user_question: str,
        chunks: List[Dict[str, Any]],
        history: Optional[List[Dict[str, str]]] = None,
        semantic_enrichment: Optional[Any] = None,
        derived_facts: Optional[List[str]] = None,
        agent_tool: Optional[str] = None,
        max_chunks: int = 5
    ) -> EnrichedPrompt:
        """
        Complete prompt enrichment pipeline.
        
        Args:
            user_question: Original user question
            chunks: Retrieved document chunks
            history: Conversation history
            semantic_enrichment: Semantic enrichment result
            derived_facts: Derived facts from chunks
            agent_tool: Tool used by focal agent
            max_chunks: Maximum chunks to include
            
        Returns:
            EnrichedPrompt with messages and metadata
        """
        # Build context block
        context_block = self.build_context_block(chunks, max_chunks)
        
        # Build enrichment info
        enrichment_info = self.build_enrichment_info(
            semantic_enrichment,
            derived_facts,
            agent_tool
        )
        
        # Build system message
        system_content = self.system_prompt
        
        if context_block:
            system_content += "\n\n## FONTES DISPONÍVEIS\n\n"
            system_content += "Use EXCLUSIVAMENTE os trechos a seguir como evidência. "
            system_content += "Cite a fonte entre colchetes (ex: [Fonte 1]). "
            system_content += "Se nada for relevante, diga que não há base documental.\n\n"
            system_content += context_block
        
        if enrichment_info:
            system_content += "\n\n## INFORMAÇÕES ADICIONAIS\n\n"
            system_content += enrichment_info
        
        if derived_facts:
            system_content += "\n\n## FATOS DERIVADOS AUTOMATICAMENTE\n\n"
            system_content += "\n".join(f"- {fact}" for fact in derived_facts)
            system_content += "\n\nUse estes fatos para complementar sua resposta quando relevante."
        
        # Build messages
        messages = [{"role": "system", "content": system_content}]
        
        # Add history
        if history:
            messages.extend(history)
        
        # Add user question
        messages.append({"role": "user", "content": user_question})
        
        # Build metadata
        metadata = {
            "num_chunks": len(chunks),
            "num_facts": len(derived_facts) if derived_facts else 0,
            "agent_tool": agent_tool,
            "has_enrichment": semantic_enrichment is not None,
            "context_length": len(context_block)
        }
        
        # Build summary
        summary_parts = []
        if chunks:
            summary_parts.append(f"{len(chunks)} trechos")
        if derived_facts:
            summary_parts.append(f"{len(derived_facts)} fatos derivados")
        if agent_tool:
            summary_parts.append(f"ferramenta: {agent_tool}")
        
        context_summary = ", ".join(summary_parts) if summary_parts else "sem contexto"
        
        return EnrichedPrompt(
            messages=messages,
            metadata=metadata,
            context_summary=context_summary
        )


# Singleton
_prompt_enricher = None

def get_prompt_enricher(system_prompt: str = None) -> PromptEnricher:
    """Get or create prompt enricher singleton"""
    global _prompt_enricher
    if _prompt_enricher is None:
        if system_prompt is None:
            from src.config import get_settings
            system_prompt = get_settings().system_prompt
        _prompt_enricher = PromptEnricher(system_prompt)
    return _prompt_enricher
