#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Desambiguação avançada de queries
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Desambiguação avançada de queries
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import re
from typing import List, Optional
from dataclasses import dataclass
from src.utils.text_utils import normalize_question


@dataclass
class DisambiguationResult:
    """Result of disambiguation check"""
    needs_disambiguation: bool
    question: str
    suggestions: List[str]
    reason: str


class AdvancedDisambiguator:
    """Advanced disambiguation for vague questions"""
    
    @staticmethod
    def needs_date_disambiguation(question: str, history: Optional[List] = None) -> DisambiguationResult:
        """
        Check if question needs date disambiguation.
        
        Detects vague questions like "quando foi?" without explicit
        reference to council, date, or document.
        
        Args:
            question: User's question
            history: Conversation history
            
        Returns:
            DisambiguationResult with disambiguation info
        """
        normalized = normalize_question(question)
        tokens = normalized.split()
        
        # Only check short questions (likely vague)
        if len(tokens) > 5:
            return DisambiguationResult(
                needs_disambiguation=False,
                question="",
                suggestions=[],
                reason="Question is specific enough"
            )
        
        # Vague date phrases
        vague_phrases = [
            "quando",
            "quando foi",
            "quando foi a reuniao",
            "quando foi a reunião",
            "quando ocorreu",
            "quando aconteceu",
            "que dia foi",
            "que dia",
            "qual a data",
            "qual data",
            "data da reuniao",
            "data da reunião",
        ]
        
        # Check if question matches vague patterns
        is_vague = any(
            phrase == normalized or phrase in normalized
            for phrase in vague_phrases
        )
        
        if not is_vague:
            return DisambiguationResult(
                needs_disambiguation=False,
                question="",
                suggestions=[],
                reason="Not a vague date question"
            )
        
        # Check if has explicit date
        has_date = bool(re.search(r'\d{2}/\d{4}|\d{2}/\d{2}/\d{4}', normalized))
        if has_date:
            return DisambiguationResult(
                needs_disambiguation=False,
                question="",
                suggestions=[],
                reason="Has explicit date"
            )
        
        # Check if has context (council, document type)
        context_terms = [
            'consun', 'consuni', 'cepe', 'ata', 'pauta',
            'agenda', 'resolucao', 'resolução', 'portaria'
        ]
        has_context = any(term in normalized for term in context_terms)
        
        if has_context:
            return DisambiguationResult(
                needs_disambiguation=False,
                question="",
                suggestions=[],
                reason="Has contextual information"
            )
        
        # Needs disambiguation
        suggestions = [
            "CONSUN 12/11/2023",
            "CEPE 14/11/2024",
            "Última reunião do CONSUN",
            "Próxima reunião do CEPE"
        ]
        
        question_text = (
            "Para qual reunião você quer saber a data? "
            "Por favor, especifique o conselho (CONSUN, CEPE) e/ou a data aproximada."
        )
        
        return DisambiguationResult(
            needs_disambiguation=True,
            question=question_text,
            suggestions=suggestions,
            reason="Vague date question without context"
        )
    
    @staticmethod
    def last_assistant_requested_date(history: List) -> bool:
        """
        Check if last assistant message requested date clarification.
        
        Helps contextualize short responses like "CEPE" after
        the assistant asked which meeting.
        
        Args:
            history: Conversation history (list of dicts with 'role' and 'content')
            
        Returns:
            True if last assistant message requested date info
        """
        if not history:
            return False
        
        # Look at last few messages
        for msg in reversed(history[-5:]):
            if msg.get('role') != 'assistant':
                continue
            
            content_lower = msg.get('content', '').lower()
            
            # Check for date-related questions
            date_request_phrases = [
                'para qual reunião',
                'qual reunião',
                'escolher a reunião',
                'especifique o conselho',
                'qual conselho',
                'consun ou cepe'
            ]
            
            if any(phrase in content_lower for phrase in date_request_phrases):
                return True
            
            # Stop at first assistant message
            break
        
        return False
    
    @staticmethod
    def needs_council_disambiguation(question: str) -> DisambiguationResult:
        """
        Check if question needs council disambiguation.
        
        Args:
            question: User's question
            
        Returns:
            DisambiguationResult
        """
        normalized = normalize_question(question)
        
        # Generic council references
        generic_terms = ['conselho', 'reuniao', 'reunião', 'sessao', 'sessão']
        has_generic = any(term in normalized for term in generic_terms)
        
        # Specific council references
        specific_terms = ['consun', 'consuni', 'cepe']
        has_specific = any(term in normalized for term in specific_terms)
        
        if has_generic and not has_specific:
            return DisambiguationResult(
                needs_disambiguation=True,
                question="Você está se referindo ao CONSUN ou ao CEPE?",
                suggestions=["CONSUN", "CEPE"],
                reason="Generic council reference"
            )
        
        return DisambiguationResult(
            needs_disambiguation=False,
            question="",
            suggestions=[],
            reason="Has specific council or no council reference"
        )


# Singleton
_disambiguator = None

def get_disambiguator() -> AdvancedDisambiguator:
    """Get or create disambiguator singleton"""
    global _disambiguator
    if _disambiguator is None:
        _disambiguator = AdvancedDisambiguator()
    return _disambiguator
