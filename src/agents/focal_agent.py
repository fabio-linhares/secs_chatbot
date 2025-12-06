#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Agente com ferramentas focais especializadas
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Agente com ferramentas focais especializadas
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ToolConfig:
    """Configuration for a focal tool"""
    name: str
    detect_terms: List[str]
    filter_terms: List[str]
    description: str = ""


# Tool configurations
TOOLS = [
    ToolConfig(
        name="pauta",
        detect_terms=["pauta", "agenda", "ordem do dia"],
        filter_terms=["pauta", "agenda", "convocacao"],
        description="Busca pautas e agendas de reuniões"
    ),
    ToolConfig(
        name="ata",
        detect_terms=["ata", "sessao", "sessão", "reuniao", "reunião"],
        filter_terms=["ata"],
        description="Busca atas de reuniões"
    ),
    ToolConfig(
        name="votacao",
        detect_terms=["votacao", "votação", "resultado", "quorum", "voto", "aprovad"],
        filter_terms=["votacao", "ata"],
        description="Busca informações sobre votações"
    ),
    ToolConfig(
        name="participantes",
        detect_terms=["participantes", "presenca", "presença", "assinaturas", "quem participou"],
        filter_terms=["participantes", "assinaturas", "ata"],
        description="Busca lista de participantes"
    ),
    ToolConfig(
        name="resolucao",
        detect_terms=["resolucao", "resolução"],
        filter_terms=["resolucao"],
        description="Busca resoluções"
    ),
    ToolConfig(
        name="portaria",
        detect_terms=["portaria"],
        filter_terms=["portaria"],
        description="Busca portarias"
    ),
    ToolConfig(
        name="data_reuniao",
        detect_terms=["quando foi", "data da reuniao", "data da reunião", "que dia", "quando ocorreu"],
        filter_terms=["ata", "agenda", "pauta", "convocacao"],
        description="Busca datas de reuniões"
    ),
]


@dataclass
class AgentResult:
    """Result from focal agent"""
    tool: Optional[str]
    chunks: List
    enhanced_query: str = ""


class FocalAgent:
    """Agent with specialized tools for document retrieval"""
    
    def __init__(self, vector_store):
        self.vector_store = vector_store
        self.tools = TOOLS
    
    def pick_tool(self, question: str) -> Optional[ToolConfig]:
        """
        Select appropriate tool based on question.
        
        Args:
            question: User's question
            
        Returns:
            ToolConfig if match found, None otherwise
        """
        q = question.lower()
        
        for tool in self.tools:
            if any(term in q for term in tool.detect_terms):
                return tool
        
        return None
    
    def run(self, question: str, k: int = 5, user_id: Optional[str] = None) -> AgentResult:
        """
        Execute focal search with user permissions.
        
        Args:
            question: User's question
            k: Number of results to return
            user_id: User ID for permission filtering
            
        Returns:
            AgentResult with tool used and retrieved chunks
        """
        tool = self.pick_tool(question)
        
        if not tool:
            return AgentResult(tool=None, chunks=[], enhanced_query=question)
        
        # Enhance query for specific tools
        enhanced_query = question
        if tool.name == "data_reuniao":
            # Strengthen query with date-related terms
            enhanced_query = f"{question} data reunião sessão ata agenda pauta convocação"
        elif tool.name == "votacao":
            enhanced_query = f"{question} votação resultado quórum aprovada"
        elif tool.name == "participantes":
            enhanced_query = f"{question} participantes presença assinaturas lista"
        
        # Build filters
        filters = {}
        if tool.name in ['pauta', 'ata', 'resolucao', 'portaria']:
            filters['tipo'] = tool.name
        
        # Execute search with user_id for permissions
        try:
            if filters:
                results = self.vector_store.search_with_filter(enhanced_query, filters, k=k, user_id=user_id)
            else:
                # For tools without direct type filter, search all
                results = self.vector_store.search(enhanced_query, k=k, user_id=user_id)
                
                # Post-filter by keywords if needed
                if tool.filter_terms:
                    filtered = []
                    for r in results:
                        content_lower = r.get('conteudo', '').lower()
                        source_lower = r.get('titulo', '').lower()
                        if any(term in content_lower or term in source_lower 
                               for term in tool.filter_terms):
                            filtered.append(r)
                    results = filtered[:k]
            
            return AgentResult(
                tool=tool.name,
                chunks=results,
                enhanced_query=enhanced_query
            )
        except Exception as e:
            print(f"Focal agent error: {e}")
            return AgentResult(tool=tool.name, chunks=[], enhanced_query=enhanced_query)


# Singleton
_focal_agent = None

def get_focal_agent(vector_store=None) -> FocalAgent:
    """Get or create focal agent singleton"""
    global _focal_agent
    if _focal_agent is None and vector_store:
        _focal_agent = FocalAgent(vector_store)
    return _focal_agent
