#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - HyDE Query Expander
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Serviço de expansão de consultas com base em documentos hipotéticos
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""


from typing import Dict, List, Optional
import numpy as np
import json
from dataclasses import dataclass

from services.llm import LLMService
from services.embeddings import get_embedding_service
from utils.hyde_prompts import (
    CONTEXT_ANALYSIS_PROMPT,
    HYPOTHESIS_GENERATION_PROMPT,
    DOCUMENT_TYPE_PROMPTS
)


@dataclass
class HyDEResult:
    """Result from HyDE query expansion"""
    original_query: str
    hypothetical_answer: str
    query_embedding: np.ndarray
    answer_embedding: np.ndarray
    analysis: Dict
    confidence: float = 0.0


class HyDEQueryExpander:
    """
    Generates hypothetical answers for better RAG retrieval.
    
    Uses domain knowledge (SECS/Conselhos) to create realistic answers
    that match the style and structure of actual documents.
    """
    
    def __init__(self, llm_service=None, embedding_service=None):
        self.llm = llm_service or LLMService()
        self.embeddings = embedding_service or get_embedding_service()
        self.cache = {}  # Simple in-memory cache
    
    def expand_query(
        self, 
        query: str, 
        conversation_history: Optional[List] = None,
        use_cache: bool = True
    ) -> HyDEResult:
        """
        Main method: generates hypothetical answer and embeddings.
        
        Args:
            query: User's question
            conversation_history: Previous messages for context
            use_cache: Whether to use cached results
            
        Returns:
            HyDEResult with hypothesis and embeddings
        """
        # Check cache
        cache_key = self._get_cache_key(query, conversation_history)
        if use_cache and cache_key in self.cache:
            return self.cache[cache_key]
        
        # 1. Analyze context
        analysis = self._analyze_context(query, conversation_history)
        
        # 2. Generate hypothetical answer
        hypothesis = self._generate_hypothesis(query, analysis, conversation_history)
        
        # 3. Create embeddings
        query_emb = self.embeddings.generate_embedding(query)
        answer_emb = self.embeddings.generate_embedding(hypothesis)
        
        # 4. Calculate confidence
        confidence = self._calculate_confidence(analysis, hypothesis)
        
        result = HyDEResult(
            original_query=query,
            hypothetical_answer=hypothesis,
            query_embedding=query_emb,
            answer_embedding=answer_emb,
            analysis=analysis,
            confidence=confidence
        )
        
        # Cache result
        if use_cache:
            self.cache[cache_key] = result
        
        return result
    
    def _analyze_context(
        self, 
        query: str, 
        conversation_history: Optional[List] = None
    ) -> Dict:
        """
        Analyzes query context to identify domain, document type, etc.
        
        Returns:
            {
                'conselho': str,
                'tipo_documento': str,
                'topico': str,
                'formato_esperado': str
            }
        """
        # Format conversation history
        history_text = self._format_history(conversation_history)
        
        # Create prompt
        prompt = CONTEXT_ANALYSIS_PROMPT.format(
            query=query,
            history=history_text
        )
        
        try:
            # Get LLM analysis
            response = self.llm.generate(
                prompt,
                max_tokens=200,
                temperature=0.3  # Low temperature for consistent analysis
            )
            
            # Parse JSON response
            analysis = json.loads(response)
            
            # Validate and set defaults
            analysis.setdefault('conselho', 'indefinido')
            analysis.setdefault('tipo_documento', 'indefinido')
            analysis.setdefault('topico', query)
            analysis.setdefault('formato_esperado', 'resposta formal')
            
            return analysis
            
        except Exception as e:
            print(f"⚠️ Error in context analysis: {e}")
            # Return default analysis
            return {
                'conselho': 'indefinido',
                'tipo_documento': 'indefinido',
                'topico': query,
                'formato_esperado': 'resposta formal'
            }
    
    def _generate_hypothesis(
        self,
        query: str,
        analysis: Dict,
        conversation_history: Optional[List] = None
    ) -> str:
        """
        Generates hypothetical answer based on context analysis.
        
        Returns:
            Hypothetical answer string
        """
        # Format conversation history
        history_text = self._format_history(conversation_history)
        
        # Select appropriate prompt based on document type
        doc_type = analysis.get('tipo_documento', 'indefinido')
        
        if doc_type in DOCUMENT_TYPE_PROMPTS:
            # Use document-specific prompt
            prompt_template = DOCUMENT_TYPE_PROMPTS[doc_type]
            prompt = prompt_template.format(
                query=query,
                conselho=analysis.get('conselho', 'CONSUNI')
            )
        else:
            # Use general hypothesis prompt
            prompt = HYPOTHESIS_GENERATION_PROMPT.format(
                query=query,
                conselho=analysis.get('conselho', 'indefinido'),
                tipo_documento=doc_type,
                topico=analysis.get('topico', query),
                history=history_text
            )
        
        try:
            # Generate hypothesis
            hypothesis = self.llm.generate(
                prompt,
                max_tokens=300,
                temperature=0.5  # Moderate temperature for realistic variation
            )
            
            return hypothesis.strip()
            
        except Exception as e:
            print(f"⚠️ Error generating hypothesis: {e}")
            # Fallback: return enhanced query
            return f"Conforme documentos do {analysis.get('conselho', 'conselho')}, {query}"
    
    def _format_history(self, conversation_history: Optional[List] = None) -> str:
        """Formats conversation history for prompts"""
        if not conversation_history:
            return "Nenhum histórico disponível."
        
        # Take last 3 messages for context
        recent = conversation_history[-3:] if len(conversation_history) > 3 else conversation_history
        
        formatted = []
        for msg in recent:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            formatted.append(f"{role.upper()}: {content[:200]}")
        
        return "\n".join(formatted)
    
    def _calculate_confidence(self, analysis: Dict, hypothesis: str) -> float:
        """
        Calculates confidence score for the hypothesis.
        
        Returns:
            Float between 0.0 and 1.0
        """
        confidence = 0.5  # Base confidence
        
        # Increase confidence if we identified specific document type
        if analysis.get('tipo_documento') != 'indefinido':
            confidence += 0.2
        
        # Increase confidence if we identified specific council
        if analysis.get('conselho') != 'indefinido':
            confidence += 0.1
        
        # Increase confidence if hypothesis contains article references
        if any(term in hypothesis.lower() for term in ['art.', 'artigo', '§', 'inciso']):
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _get_cache_key(self, query: str, conversation_history: Optional[List] = None) -> str:
        """Generates cache key for query"""
        history_key = ""
        if conversation_history:
            # Use last message as part of key
            last_msg = conversation_history[-1] if conversation_history else {}
            history_key = last_msg.get('content', '')[:50]
        
        return f"{query}|{history_key}"
    
    def clear_cache(self):
        """Clears the hypothesis cache"""
        self.cache = {}


# Singleton
_hyde_expander = None

def get_hyde_expander() -> HyDEQueryExpander:
    """Get or create HyDE expander singleton"""
    global _hyde_expander
    if _hyde_expander is None:
        _hyde_expander = HyDEQueryExpander()
    return _hyde_expander
