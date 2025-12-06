#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Agente de reescrita semântica híbrida
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Agente de reescrita semântica híbrida
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SemanticEnrichment:
    """Result of semantic enrichment"""
    rewritten: str
    heuristics: List[str]
    alternates: List[str]
    confidence: float = 0.8


class SemanticRewriter:
    """Rewrites queries using heuristics and LLM"""
    
    def __init__(self, llm_service=None):
        self.llm = llm_service
        self.keyword_map = {
            "pauta": ["pauta", "agenda", "ordem do dia", "calendário"],
            "ata": ["ata", "sessão", "reunião", "registros", "assinaturas"],
            "votação": ["votação", "resultado", "quórum", "aprovada", "unanimidade", "voto"],
            "votacao": ["votação", "resultado", "quórum", "aprovada", "unanimidade", "voto"],
            "resolução": ["resolução", "número", "vigência", "ementa", "deliberação"],
            "resolucao": ["resolução", "número", "vigência", "ementa", "deliberação"],
            "portaria": ["portaria", "turmas", "número da portaria"],
            "regimento": ["regimento", "estatuto", "normas", "regulamento"],
            "conselho": ["CONSUN", "CONSUNI", "CEPE", "Conselho Universitário"],
            "presidente": ["presidente da sessão", "quem presidiu", "reitor"],
            "convocação": ["convocação", "data da reunião", "envio"],
            "convocacao": ["convocação", "data da reunião", "envio"],
        }
    
    def extract_heuristics(self, question: str) -> List[str]:
        """Extract heuristic terms from question"""
        q = question.lower()
        terms = []
        
        # Keyword expansion
        for key, expansions in self.keyword_map.items():
            if key in q:
                terms.extend(expansions)
        
        # Extract dates (DD/MM/YYYY)
        dates = re.findall(r'\b\d{2}/\d{2}/\d{4}\b', q)
        terms.extend(dates)
        
        # Extract dates (MM/YYYY)
        dates_short = re.findall(r'\b\d{2}/\d{4}\b', q)
        terms.extend(dates_short)
        
        # Extract numbers
        numbers = re.findall(r'\b\d{3,4}\b', q)
        terms.extend(numbers)
        
        return sorted(set(terms))
    
    def llm_rewrite(self, question: str) -> Optional[str]:
        """Rewrite query using LLM"""
        if not self.llm:
            return None
        
        try:
            prompt = [{
                "role": "system",
                "content": (
                    "Reescreva perguntas vagas em consultas claras para busca vetorial. "
                    "Inclua tipo de documento (ata, resolução, pauta), "
                    "órgão (CONSUN, CEPE), datas, números e tema. "
                    "Seja conciso (máximo 2 frases)."
                )
            }, {
                "role": "user",
                "content": f"Pergunta: {question}\nReescreva:"
            }]
            
            # Get response from LLM
            response = self.llm.get_response(prompt)
            
            # Extract text from streaming response
            rewritten = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    rewritten += chunk.choices[0].delta.content
            
            return rewritten.strip()
        except Exception as e:
            print(f"LLM rewrite error: {e}")
            return None
    
    def generate_alternates(self, question: str, heuristics: List[str]) -> List[str]:
        """Generate alternate query variations"""
        alternates = []
        
        if heuristics:
            # Version with heuristic terms
            alternates.append(question + " " + " ".join(heuristics[:5]))
            
            # Version with just keywords
            if len(heuristics) >= 2:
                alternates.append(", ".join(heuristics[:4]))
        
        return alternates
    
    def enrich(self, question: str, use_llm: bool = True) -> SemanticEnrichment:
        """
        Complete enrichment pipeline.
        
        Args:
            question: Original user question
            use_llm: Whether to use LLM rewriting (slower but better)
            
        Returns:
            SemanticEnrichment with rewritten query and metadata
        """
        # 1. Extract heuristics (fast, no cost)
        heuristics = self.extract_heuristics(question)
        
        # 2. LLM rewrite (slow, has cost) - optional
        rewritten = question
        if use_llm and self.llm:
            llm_result = self.llm_rewrite(question)
            if llm_result:
                rewritten = llm_result
        
        # 3. Add heuristics to rewritten query
        if heuristics:
            rewritten = f"{rewritten}. Palavras-chave: {', '.join(heuristics[:5])}"
        
        # 4. Generate alternates
        alternates = self.generate_alternates(question, heuristics)
        
        # 5. Calculate confidence
        confidence = 0.9 if heuristics else 0.6
        if use_llm and llm_result:
            confidence = min(confidence + 0.1, 1.0)
        
        return SemanticEnrichment(
            rewritten=rewritten,
            heuristics=heuristics,
            alternates=alternates,
            confidence=confidence
        )


# Singleton
_semantic_rewriter = None

def get_semantic_rewriter(llm_service=None) -> SemanticRewriter:
    """Get or create semantic rewriter singleton"""
    global _semantic_rewriter
    if _semantic_rewriter is None:
        _semantic_rewriter = SemanticRewriter(llm_service)
    return _semantic_rewriter
