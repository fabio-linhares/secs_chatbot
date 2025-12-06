#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Extração de fatos derivados de chunks
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Extração de fatos derivados de chunks
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import re
from typing import List, Dict, Any


class CountHelper:
    """Derives numerical facts from document chunks"""
    
    @staticmethod
    def derive_counts(question: str, chunks: List[Dict[str, Any]]) -> List[str]:
        """
        Derive facts from chunks based on question.
        
        Args:
            question: User's question
            chunks: Retrieved document chunks
            
        Returns:
            List of derived facts as strings
        """
        facts = []
        q_lower = question.lower()
        
        # Check if question is about voting
        if any(term in q_lower for term in ['votacao', 'votação', 'voto', 'aprovad', 'resultado']):
            voting_facts = CountHelper._derive_voting_counts(chunks)
            facts.extend(voting_facts)
        
        # Check if question is about participants
        if any(term in q_lower for term in ['participantes', 'presenca', 'presença', 'quem', 'quantos']):
            participant_facts = CountHelper._derive_participant_counts(chunks)
            facts.extend(participant_facts)
        
        # Check if question is about quorum
        if 'quorum' in q_lower or 'quórum' in q_lower:
            quorum_facts = CountHelper._derive_quorum_info(chunks)
            facts.extend(quorum_facts)
        
        return facts
    
    @staticmethod
    def _derive_voting_counts(chunks: List[Dict[str, Any]]) -> List[str]:
        """Extract voting information from chunks"""
        facts = []
        
        for chunk in chunks:
            content = chunk.get('conteudo', '')
            
            # Pattern: "X votos a favor, Y contra, Z abstenções"
            pattern = r'(\d+)\s+votos?\s+(?:a\s+)?favor.*?(\d+)\s+contra.*?(\d+)\s+absten'
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                favor, contra, abstencoes = match.groups()
                total = int(favor) + int(contra) + int(abstencoes)
                facts.append(f"Votação: {favor} a favor, {contra} contra, {abstencoes} abstenções (total: {total})")
            
            # Pattern: "aprovado por unanimidade"
            if re.search(r'aprovad[oa]\s+por\s+unanimidade', content, re.IGNORECASE):
                facts.append("Aprovado por unanimidade")
            
            # Pattern: "aprovado por maioria"
            if re.search(r'aprovad[oa]\s+por\s+maioria', content, re.IGNORECASE):
                facts.append("Aprovado por maioria")
        
        return facts
    
    @staticmethod
    def _derive_participant_counts(chunks: List[Dict[str, Any]]) -> List[str]:
        """Extract participant information from chunks"""
        facts = []
        participants = set()
        
        for chunk in chunks:
            content = chunk.get('conteudo', '')
            
            # Pattern: "Presentes: X, Y, Z"
            if 'presentes:' in content.lower():
                # Extract names after "Presentes:"
                match = re.search(r'presentes:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
                if match:
                    names_text = match.group(1)
                    # Split by common separators
                    names = re.split(r'[,;]', names_text)
                    for name in names:
                        name = name.strip()
                        if name and len(name) > 3:  # Filter out noise
                            participants.add(name)
            
            # Pattern: "X participantes"
            match = re.search(r'(\d+)\s+participantes?', content, re.IGNORECASE)
            if match:
                count = match.group(1)
                facts.append(f"Total de participantes: {count}")
        
        if participants:
            facts.append(f"Participantes identificados: {len(participants)}")
        
        return facts
    
    @staticmethod
    def _derive_quorum_info(chunks: List[Dict[str, Any]]) -> List[str]:
        """Extract quorum information from chunks"""
        facts = []
        
        for chunk in chunks:
            content = chunk.get('conteudo', '')
            
            # Pattern: "quórum de X"
            match = re.search(r'qu[oó]rum\s+de\s+(\d+)', content, re.IGNORECASE)
            if match:
                quorum = match.group(1)
                facts.append(f"Quórum: {quorum}")
            
            # Pattern: "quórum atingido"
            if re.search(r'qu[oó]rum\s+atingido', content, re.IGNORECASE):
                facts.append("Quórum atingido")
            
            # Pattern: "sem quórum"
            if re.search(r'sem\s+qu[oó]rum', content, re.IGNORECASE):
                facts.append("Sem quórum")
        
        return facts


# Singleton
_count_helper = None

def get_count_helper() -> CountHelper:
    """Get or create count helper singleton"""
    global _count_helper
    if _count_helper is None:
        _count_helper = CountHelper()
    return _count_helper
