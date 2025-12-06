#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Agente de melhoria de queries
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Agente de melhoria de queries
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import re
from typing import List, Dict
from dataclasses import dataclass
from src.services.llm import llm_service

@dataclass
class EnhancedQuery:
    """Result of query enhancement"""
    original_query: str
    enhanced_query: str
    detected_context: Dict
    confidence: float

class QueryEnhancerAgent:
    """
    Agent that enhances vague queries by analyzing conversation context.
    
    Example:
    User: "Qual o resultado da votação?"
    Context: Last message mentioned "Resolução 24"
    Enhanced: "Qual foi o resultado da votação da Resolução CONSUNI nº 024/2024? 
               Foi aprovada ou rejeitada? Por unanimidade ou maioria?"
    """
    
    def __init__(self):
        self.system_prompt = """Você é um agente especializado em melhorar queries de busca sobre Conselhos Superiores da UFAL.

Sua tarefa é analisar perguntas vagas do usuário e expandi-las usando o contexto da conversa.

DOMÍNIO: Conselhos Superiores da UFAL (CONSUNI, CEPE)
- Atas de reuniões
- Resoluções
- Pautas
- Regimentos
- Votações, deliberações, participantes

REGRAS:
1. Identifique informações faltantes na pergunta
2. Use o contexto da conversa para preencher lacunas
3. Expanda a pergunta com termos relevantes para busca
4. Seja ESPECÍFICO sobre datas, números, tipos de documento
5. Quando o usuário diz "última", "próxima", "recente", especifique o que está buscando

EXEMPLOS:

Pergunta vaga: "Qual a pauta?"
Contexto: Nenhum
Query melhorada: "Qual a pauta da próxima reunião do CONSUNI? Quais são os itens da ordem do dia? Quando será a reunião?"

Pergunta vaga: "Quem votou na última?"
Contexto: Nenhum
Query melhorada: "Quem votou na última reunião do CONSUNI? Quais foram os conselheiros presentes? Qual foi o resultado da votação?"

Pergunta vaga: "qual o resumo da última ata?"
Contexto: Nenhum  
Query melhorada: "Qual o resumo da última ata do CONSUNI? Quais foram os principais assuntos deliberados? Quais resoluções foram aprovadas?"

Pergunta vaga: "última"
Contexto: Conversa sobre "pauta"
Query melhorada: "Qual a pauta da última reunião do CONSUNI? Quando foi realizada? Quais foram os itens discutidos?"

Pergunta vaga: "Foi aprovado?"
Contexto: Conversa sobre "Resolução 24"
Query melhorada: "A Resolução CONSUNI nº 024/2024 foi aprovada? Qual foi o resultado da votação? Quantos votos favoráveis e contrários?"

FORMATO DE SAÍDA:
Retorne APENAS a query melhorada, sem explicações adicionais.

IMPORTANTE: Se a pergunta original menciona um tipo de documento (pauta, ata, resolução), 
MANTENHA essa palavra na query melhorada."""
    
    def enhance_query(
        self, 
        user_query: str, 
        conversation_history: List[Dict],
        max_context_messages: int = 5
    ) -> EnhancedQuery:
        """
        Enhance a user query using conversation context.
        
        Args:
            user_query: The vague query from the user
            conversation_history: Recent conversation messages
            max_context_messages: How many recent messages to consider
        
        Returns:
            EnhancedQuery with improved query and metadata
        """
        # Extract relevant context
        context_info = self._extract_context(conversation_history, max_context_messages)
        
        # Build prompt for LLM
        context_str = self._format_context(context_info)
        
        prompt = f"""Contexto da conversa:
{context_str}

Pergunta vaga do usuário: "{user_query}"

Melhore esta pergunta para uma busca mais efetiva, considerando o contexto acima."""
        
        # Call LLM to enhance query
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = llm_service.get_response(messages)
            
            enhanced_query = ""
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    enhanced_query += chunk.choices[0].delta.content
            
            enhanced_query = enhanced_query.strip()
            
            # Calculate confidence based on context availability
            confidence = self._calculate_confidence(context_info, user_query)
            
            return EnhancedQuery(
                original_query=user_query,
                enhanced_query=enhanced_query,
                detected_context=context_info,
                confidence=confidence
            )
        
        except Exception as e:
            print(f"Error enhancing query: {e}")
            # Fallback: return original query
            return EnhancedQuery(
                original_query=user_query,
                enhanced_query=user_query,
                detected_context={},
                confidence=0.0
            )
    
    def _extract_context(self, conversation_history: List[Dict], max_messages: int) -> Dict:
        """Extract relevant context from conversation history"""
        context = {
            'mentioned_documents': [],
            'mentioned_numbers': [],
            'mentioned_councils': [],
            'mentioned_topics': []
        }
        
        # Analyze recent messages
        recent_messages = conversation_history[-max_messages:] if conversation_history else []
        
        for msg in recent_messages:
            content = msg.get('content', '').lower()
            
            # Extract document numbers
            if 'resolução' in content or 'resolucao' in content:
                # Try to extract number
                numbers = re.findall(r'\b\d{2,3}/\d{4}\b|\b\d{2,3}\b', content)
                context['mentioned_numbers'].extend(numbers)
                context['mentioned_documents'].append('resolucao')
            
            if 'ata' in content:
                numbers = re.findall(r'\b\d{1,2}\b', content)
                context['mentioned_numbers'].extend(numbers)
                context['mentioned_documents'].append('ata')
            
            # Extract councils
            if 'consuni' in content:
                context['mentioned_councils'].append('CONSUNI')
            if 'cepe' in content:
                context['mentioned_councils'].append('CEPE')
            
            # Extract topics
            if 'votação' in content or 'votacao' in content:
                context['mentioned_topics'].append('votacao')
            if 'aprovação' in content or 'aprovacao' in content:
                context['mentioned_topics'].append('aprovacao')
        
        # Deduplicate
        context['mentioned_documents'] = list(set(context['mentioned_documents']))
        context['mentioned_numbers'] = list(set(context['mentioned_numbers']))
        context['mentioned_councils'] = list(set(context['mentioned_councils']))
        context['mentioned_topics'] = list(set(context['mentioned_topics']))
        
        return context
    
    def _format_context(self, context_info: Dict) -> str:
        """Format context information for the prompt"""
        parts = []
        
        if context_info['mentioned_documents']:
            parts.append(f"Documentos mencionados: {', '.join(context_info['mentioned_documents'])}")
        
        if context_info['mentioned_numbers']:
            parts.append(f"Números mencionados: {', '.join(context_info['mentioned_numbers'])}")
        
        if context_info['mentioned_councils']:
            parts.append(f"Conselhos mencionados: {', '.join(context_info['mentioned_councils'])}")
        
        if context_info['mentioned_topics']:
            parts.append(f"Tópicos mencionados: {', '.join(context_info['mentioned_topics'])}")
        
        return '\n'.join(parts) if parts else "Nenhum contexto específico detectado."
    
    def _calculate_confidence(self, context_info: Dict, query: str) -> float:
        """Calculate confidence in the enhancement"""
        score = 0.5  # Base score
        
        # Increase confidence if we found relevant context
        if context_info['mentioned_documents']:
            score += 0.2
        if context_info['mentioned_numbers']:
            score += 0.2
        if context_info['mentioned_councils']:
            score += 0.1
        
        # Decrease confidence for very vague queries
        vague_indicators = ['isso', 'aquilo', 'ele', 'ela', 'qual']
        if any(word in query.lower() for word in vague_indicators):
            score -= 0.1
        
        return min(1.0, max(0.0, score))

# Singleton instance
_query_enhancer = None

def get_query_enhancer() -> QueryEnhancerAgent:
    """Get or create query enhancer singleton"""
    global _query_enhancer
    if _query_enhancer is None:
        _query_enhancer = QueryEnhancerAgent()
    return _query_enhancer
