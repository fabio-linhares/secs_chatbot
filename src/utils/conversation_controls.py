#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Controles de gerenciamento de conversa
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Controles de gerenciamento de conversa
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import streamlit as st
from datetime import datetime
from typing import List, Dict


def init_conversation_state():
    """Initialize conversation state in session"""
    if "conversation_active" not in st.session_state:
        st.session_state.conversation_active = True
    if "conversation_started_at" not in st.session_state:
        st.session_state.conversation_started_at = datetime.now()


def end_conversation():
    """End current conversation"""
    st.session_state.conversation_active = False


def start_new_conversation():
    """Start a new conversation, clearing all state"""
    st.session_state.messages = []
    st.session_state.conversation_active = True
    st.session_state.conversation_started_at = datetime.now()
    st.session_state.last_cache_source = None
    st.session_state.last_enrichment = None
    st.session_state.last_retrieved = []
    st.session_state.last_derived_facts = []
    st.session_state.last_agent_tool = None


def export_conversation(messages: List[Dict], format: str = "txt") -> str:
    """
    Export conversation to text format.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        format: Export format ('txt' or 'md')
        
    Returns:
        Formatted conversation string
    """
    if not messages:
        return "Nenhuma mensagem para exportar."
    
    lines = []
    
    # Header
    if format == "md":
        lines.append("# Conversa - Chatbot SECS/UFAL")
        lines.append(f"\n**Data**: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        lines.append(f"**Mensagens**: {len(messages)}\n")
        lines.append("---\n")
    else:
        lines.append("=" * 60)
        lines.append("CONVERSA - CHATBOT SECS/UFAL")
        lines.append(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        lines.append(f"Mensagens: {len(messages)}")
        lines.append("=" * 60)
        lines.append("")
    
    # Messages
    for i, msg in enumerate(messages, 1):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        sources = msg.get('sources', [])
        
        if format == "md":
            role_label = "👤 **Usuário**" if role == "user" else "🤖 **Assistente**"
            lines.append(f"### Mensagem {i} - {role_label}\n")
            lines.append(content)
            
            if sources:
                lines.append("\n**Fontes:**")
                for source in sources:
                    lines.append(f"- {source}")
            
            lines.append("\n---\n")
        else:
            role_label = "USUÁRIO" if role == "user" else "ASSISTENTE"
            lines.append(f"[{i}] {role_label}:")
            lines.append(content)
            
            if sources:
                lines.append("\nFontes:")
                for source in sources:
                    lines.append(f"  - {source}")
            
            lines.append("")
            lines.append("-" * 60)
            lines.append("")
    
    return "\n".join(lines)


def render_conversation_controls():
    """
    Render conversation control buttons.
    
    Returns:
        True if conversation is active, False otherwise
    """
    init_conversation_state()
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col2:
        if st.session_state.conversation_active:
            if st.button("🛑 Encerrar", use_container_width=True, help="Encerrar conversa atual"):
                end_conversation()
                st.rerun()
    
    with col3:
        if not st.session_state.conversation_active:
            if st.button("🆕 Nova", type="primary", use_container_width=True, help="Iniciar nova conversa"):
                start_new_conversation()
                st.rerun()
        else:
            # Export button
            if st.session_state.messages:
                export_text = export_conversation(st.session_state.messages, format="txt")
                st.download_button(
                    "📥 Export",
                    export_text,
                    file_name=f"conversa_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    help="Exportar conversa"
                )
    
    return st.session_state.conversation_active


def show_conversation_status():
    """Show conversation status message"""
    if not st.session_state.get('conversation_active', True):
        st.info("💬 **Conversa encerrada.** Clique em 'Nova' para iniciar uma nova conversa.")
        return False
    return True
