#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Agente de clarificação e desambiguação
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Agente de clarificação e desambiguação
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class ClarificationNeeded:
    """Represents a clarification request"""
    original_query: str
    ambiguity_type: str  # 'temporal', 'multiple_options', 'missing_info'
    question: str
    options: List[str]
    confidence: float

class ClarificationAgent:
    """
    Agent that detects ambiguous queries and requests clarification.
    
    Example:
    User: "Qual a pauta?"
    Agent detects: Multiple pautas available (última vs próxima)
    Response: "Você quer saber sobre a pauta da última reunião ou da próxima?"
    """
    
    def __init__(self):
        pass
    
    def check_for_ambiguity(
        self,
        user_query: str,
        search_results: List[Dict],
        conversation_history: List[Dict]
    ) -> Optional[ClarificationNeeded]:
        """
        Check if query is ambiguous and needs clarification.
        
        Returns ClarificationNeeded if ambiguous, None otherwise.
        """
        query_lower = user_query.lower()
        
        # Check for temporal ambiguity (última vs próxima)
        if self._is_temporal_query(query_lower):
            return self._check_temporal_ambiguity(user_query, search_results)
        
        # Check for multiple documents of same type
        if self._has_multiple_similar_docs(search_results):
            return self._check_multiple_docs_ambiguity(user_query, search_results)
        
        return None
    
    def _is_temporal_query(self, query: str) -> bool:
        """Check if query has temporal ambiguity"""
        temporal_words = ['pauta', 'ata', 'reunião', 'reuniao']
        vague_words = ['qual', 'quando', 'onde']
        
        has_temporal = any(word in query for word in temporal_words)
        has_vague = any(word in query for word in vague_words)
        no_specific = not any(word in query for word in ['última', 'ultima', 'próxima', 'proxima', 'número', 'numero', r'\d+'])
        
        return has_temporal and has_vague and no_specific
    
    def _check_temporal_ambiguity(
        self,
        user_query: str,
        search_results: List[Dict]
    ) -> Optional[ClarificationNeeded]:
        """Check for temporal ambiguity (última vs próxima)"""
        
        # Extract document types and dates
        doc_info = []
        for result in search_results[:5]:
            doc_info.append({
                'titulo': result.get('titulo', ''),
                'tipo': result.get('tipo', ''),
                'numero': result.get('numero', ''),
                'data': result.get('data', ''),
            })
        
        # Check if we have both past and future documents
        # For now, assume we only have past documents
        # In a real system, we'd check dates
        
        if len(doc_info) > 0:
            tipo = doc_info[0]['tipo']
            
            # Check if there are multiple documents of this type
            unique_docs = set(d['titulo'] for d in doc_info)
            
            if len(unique_docs) > 1:
                return ClarificationNeeded(
                    original_query=user_query,
                    ambiguity_type='temporal',
                    question=f"Você quer saber sobre a {tipo} da **última** reunião ou da **próxima** reunião?",
                    options=['última', 'próxima'],
                    confidence=0.8
                )
        
        return None
    
    def _has_multiple_similar_docs(self, search_results: List[Dict]) -> bool:
        """Check if there are multiple similar documents"""
        if len(search_results) < 2:
            return False
        
        # Check if top results are from different documents
        unique_docs = set(r.get('titulo', '') for r in search_results[:5])
        return len(unique_docs) > 1
    
    def _check_multiple_docs_ambiguity(
        self,
        user_query: str,
        search_results: List[Dict]
    ) -> Optional[ClarificationNeeded]:
        """Check for multiple documents ambiguity"""
        
        # Group by document
        docs_by_title = {}
        for result in search_results[:8]:
            titulo = result.get('titulo', '')
            if titulo not in docs_by_title:
                docs_by_title[titulo] = []
            docs_by_title[titulo].append(result)
        
        if len(docs_by_title) > 1:
            # Multiple documents found
            doc_list = list(docs_by_title.keys())[:3]  # Top 3
            
            return ClarificationNeeded(
                original_query=user_query,
                ambiguity_type='multiple_options',
                question=f"Encontrei {len(docs_by_title)} documentos. Sobre qual você quer saber?",
                options=doc_list,
                confidence=0.7
            )
        
        return None

# Singleton instance
_clarification_agent = None

def get_clarification_agent() -> ClarificationAgent:
    """Get or create clarification agent singleton"""
    global _clarification_agent
    if _clarification_agent is None:
        _clarification_agent = ClarificationAgent()
    return _clarification_agent
