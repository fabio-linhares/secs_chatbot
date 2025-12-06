#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Aplicação Streamlit com todas as funcionalidades
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Aplicação Streamlit com todas as funcionalidades
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import streamlit as st
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.llm import llm_service
from config import get_settings
from utils.prompts import WELCOME_MESSAGE, GUARDRAIL_MESSAGES, check_scope

# Authentication and Admin
from components.auth_panel import auth_panel
from components.first_user_wizard import first_user_wizard, check_first_user
from services.user_service import get_user_service

# Initialize settings
settings = get_settings()

# Initialize user service
user_service = get_user_service()

# Import all services
try:
    from services.vector_store import get_vector_store
    from services.cache_service import get_cache_service
    from services.audit import get_audit_logger, AuditRecord
    from services.count_helper import get_count_helper
    from services.prompt_enricher import get_prompt_enricher
    from agents.query_enhancer import get_query_enhancer
    from agents.semantic_rewriter import get_semantic_rewriter
    from agents.focal_agent import get_focal_agent
    from agents.clarification_agent import get_clarification_agent
    
    vector_store = get_vector_store()
    cache_service = get_cache_service()
    audit_logger = get_audit_logger()
    count_helper = get_count_helper()
    prompt_enricher = get_prompt_enricher()
    query_enhancer = get_query_enhancer()
    semantic_rewriter = get_semantic_rewriter(llm_service)
    focal_agent = get_focal_agent(vector_store)
    clarification_agent = get_clarification_agent()
    
    ALL_SERVICES_AVAILABLE = True
except Exception as e:
    print(f"Warning: Some services not available: {e}")
    ALL_SERVICES_AVAILABLE = False

# Check if first user needs to be created
if not check_first_user():
    st.set_page_config(
        page_title="SECS Chatbot - Setup",
        page_icon="🏛️",
        layout="wide"
    )
    first_user_wizard()
    st.stop()

# Page Config
st.set_page_config(
    page_title="SECS Chatbot",
    page_icon="🏛️",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_id" not in st.session_state:
    st.session_state.user_id = "anon"
if "last_cache_source" not in st.session_state:
    st.session_state.last_cache_source = None
if "last_enrichment" not in st.session_state:
    st.session_state.last_enrichment = None
if "last_retrieved" not in st.session_state:
    st.session_state.last_retrieved = []
if "last_derived_facts" not in st.session_state:
    st.session_state.last_derived_facts = []
if "last_agent_tool" not in st.session_state:
    st.session_state.last_agent_tool = None
if "use_hyde" not in st.session_state:
    st.session_state.use_hyde = True
if "last_hyde" not in st.session_state:
    st.session_state.last_hyde = None

# Sidebar
with st.sidebar:
    st.title("🏛️ SECS/UFAL")
    st.markdown("**Secretaria dos Conselhos Superiores**")
    st.markdown("Universidade Federal de Alagoas")
    st.markdown("---")
    
    # Authentication Panel
    if not auth_panel(user_service):
        st.info("🔐 Faça login ou cadastre-se para acessar o chat.")
        st.stop()
    
    st.markdown("---")
    
    # User info
    st.caption(f"👤 Usuário: **{st.session_state.get('user_id', 'anon')}**")
    st.caption(f"🎭 Role: **{st.session_state.get('role', 'publico')}**")
    
    st.markdown("---")
    
    if st.button("🗑️ Limpar Conversa", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_cache_source = None
        st.session_state.last_enrichment = None
        st.session_state.last_retrieved = []
        st.session_state.last_derived_facts = []
        st.session_state.last_agent_tool = None
        st.rerun()
    
    st.markdown("---")
    
    # Quick stats
    if st.session_state.last_retrieved:
        st.markdown("### � Última Consulta")
        st.metric("Trechos RAG", len(st.session_state.last_retrieved))
        
        if st.session_state.last_cache_source:
            st.caption(f"⚡ Cache: {st.session_state.last_cache_source}")
        
        if st.session_state.last_enrichment:
            st.caption("✨ Reescrita semântica ativa")
            enr = st.session_state.last_enrichment
            if hasattr(enr, 'heuristics') and enr.heuristics:
                st.caption(f"**Termos**: {', '.join(enr.heuristics[:3])}")
    
    # Show derived facts
    if st.session_state.last_derived_facts:
        st.markdown("---")
        st.markdown("### 📊 Fatos Derivados")
        for fact in st.session_state.last_derived_facts[:3]:
            st.caption(f"• {fact}")

# Main content area
st.title("💬 SECS Chatbot")
st.caption(f"Modelo: {settings.llm_model}")
st.caption(f"Ambiente: {settings.environment}")

# Main App - Tabs
tabs = st.tabs(["💬 Chat", "📤 Meus Documentos", "📊 Auditoria", "📈 Estatísticas", "📚 Documentação", "⚙️ Admin"])

# ===== TAB 1: CHAT =====
with tabs[0]:
    st.title("Assistente Virtual - Conselhos Superiores")
    st.markdown("*Secretaria dos Conselhos Superiores (SECS) - UFAL*")
    
    # Real-time metrics
    if ALL_SERVICES_AVAILABLE:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            num_chunks = len(st.session_state.last_retrieved)
            st.metric("📚 Trechos RAG", num_chunks)
        
        with col2:
            enrichment = st.session_state.last_enrichment
            st.metric("🔍 Reescrita", "Sim" if enrichment else "Não")
        
        with col3:
            cache_source = st.session_state.last_cache_source
            st.metric("⚡ Cache", cache_source or "Miss")
        
        with col4:
            agent_tool = st.session_state.last_agent_tool
            st.metric("🤖 Agente", agent_tool or "Nenhum")
        
        st.markdown("---")
    
    # Display chat history
    if not st.session_state.messages:
        with st.chat_message("assistant"):
            st.markdown(WELCOME_MESSAGE)
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message and message["sources"]:
                with st.expander("📚 Fontes consultadas"):
                    for source in message["sources"]:
                        st.caption(f"• {source}")
    
    # Chat input
    if prompt := st.chat_input("Digite sua mensagem..."):
        # Check scope
        if not check_scope(prompt):
            st.chat_message("user").markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("assistant"):
                st.markdown(GUARDRAIL_MESSAGES["fora_escopo"])
            st.session_state.messages.append({
                "role": "assistant",
                "content": GUARDRAIL_MESSAGES["fora_escopo"]
            })
        else:
            # Display user message
            st.chat_message("user").markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Process with assistant
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                sources = []
                
                # Check cache first
                if ALL_SERVICES_AVAILABLE:
                    cached = cache_service.get_user_answer(st.session_state.user_id, prompt)
                    if cached and not cache_service.should_bypass_cache(cached):
                        full_response = cached
                        message_placeholder.markdown(full_response)
                        st.caption("⚡ Resposta do cache (usuário)")
                        st.session_state.last_cache_source = "user"
                        
                        if ALL_SERVICES_AVAILABLE:
                            audit_logger.log(AuditRecord(
                                user=st.session_state.user_id,
                                role="publico",
                                input_text=prompt,
                                output_text=full_response,
                                metadata={"cache_hit": "user"}
                            ))
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": full_response,
                            "sources": []
                        })
                        st.rerun()
                
                # If not cached, process with RAG
                if not full_response and ALL_SERVICES_AVAILABLE:
                    try:
                        # 1. Semantic rewriting
                        enrichment = semantic_rewriter.enrich(prompt, use_llm=True)
                        st.session_state.last_enrichment = enrichment
                        
                        # 2. Focal agent search with user permissions
                        agent_result = focal_agent.run(
                            enrichment.rewritten,
                            k=5,
                            user_id=st.session_state.user_id
                        )
                        st.session_state.last_agent_tool = agent_result.tool
                        
                        # 3. Regular RAG search (fallback) with user permissions
                        search_results = vector_store.search(
                            enrichment.rewritten, 
                            k=5,
                            user_id=st.session_state.user_id
                        )
                        
                        # Combine results
                        all_chunks = agent_result.chunks if agent_result.chunks else search_results
                        st.session_state.last_retrieved = all_chunks
                        
                        # 4. Derive facts
                        derived_facts = count_helper.derive_counts(prompt, all_chunks)
                        st.session_state.last_derived_facts = derived_facts
                        
                        # 5. Check clarification
                        clarification = clarification_agent.check_for_ambiguity(prompt, all_chunks, st.session_state.messages)
                        
                        if clarification and clarification.confidence > 0.7:
                            # Ask for clarification
                            full_response = f"🤔 {clarification.question}\n\n"
                            if clarification.options:
                                full_response += "**Opções:**\n"
                                for opt in clarification.options:
                                    full_response += f"- {opt}\n"
                            full_response += "\nPor favor, seja mais específico."
                            message_placeholder.markdown(full_response)
                        else:
                            # 6. Enrich prompt
                            enriched = prompt_enricher.enrich(
                                user_question=prompt,
                                chunks=all_chunks,
                                history=st.session_state.messages[-10:],  # Last 10 messages
                                semantic_enrichment=enrichment,
                                derived_facts=derived_facts,
                                agent_tool=agent_result.tool
                            )
                            
                            # 7. Call LLM
                            stream = llm_service.get_response(enriched.messages)
                            
                            for chunk in stream:
                                if chunk.choices[0].delta.content:
                                    full_response += chunk.choices[0].delta.content
                                    message_placeholder.markdown(full_response + "▌")
                            
                            message_placeholder.markdown(full_response)
                            
                            # Show sources
                            if all_chunks:
                                sources = [f"{c.get('titulo', 'Doc')} ({c.get('similarity', 0):.1%})" 
                                          for c in all_chunks[:5]]
                                with st.expander("📚 Fontes consultadas"):
                                    for source in sources:
                                        st.caption(f"• {source}")
                        
                        # Cache response
                        if not cache_service.should_bypass_cache(full_response):
                            cache_service.set_user_answer(st.session_state.user_id, prompt, full_response)
                            cache_service.set_global_answer(prompt, full_response)
                        
                        # Audit log
                        if ALL_SERVICES_AVAILABLE:
                            audit_logger.log(AuditRecord(
                                user=st.session_state.user_id,
                                role="publico",
                                input_text=prompt,
                                output_text=full_response,
                                metadata={
                                    "cache_hit": None,
                                    "num_chunks": len(all_chunks),
                                    "agent_tool": agent_result.tool,
                                    "derived_facts": len(derived_facts)
                                }
                            ))
                        
                    except Exception as e:
                        full_response = f"Erro ao processar: {str(e)}"
                        message_placeholder.error(full_response)
                
                # Add to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response,
                    "sources": sources
                })
                st.rerun()

# ===== TAB 2: MEUS DOCUMENTOS =====
with tabs[1]:
    try:
        from components.document_upload import render_document_upload
        
        render_document_upload()
        
    except Exception as e:
        st.error(f"Erro ao carregar upload de documentos: {e}")
        import traceback
        st.code(traceback.format_exc())

# ===== TAB 3: AUDITORIA =====
with tabs[2]:
    st.subheader("📊 Auditoria de Conversas")
    
    if ALL_SERVICES_AVAILABLE:
        try:
            # Filters
            col1, col2 = st.columns([3, 1])
            with col1:
                search_term = st.text_input("🔍 Buscar", placeholder="Digite para buscar...")
            with col2:
                limit = st.number_input("Limite", min_value=10, max_value=100, value=50)
            
            # Get records
            if search_term:
                records = audit_logger.search(search_term, limit=limit)
            else:
                records = audit_logger.list_recent(limit=limit)
            
            st.caption(f"Mostrando {len(records)} registros")
            
            # Display records
            for record in records:
                with st.expander(
                    f"{record.created_at.strftime('%d/%m/%Y %H:%M')} | {record.user} | {record.role}",
                    expanded=False
                ):
                    st.markdown(f"**Pergunta:** {record.input_text}")
                    st.markdown(f"**Resposta:** {record.output_text[:500]}...")
                    
                    if record.metadata:
                        st.json(record.metadata)
        except Exception as e:
            st.error(f"Erro ao carregar auditoria: {e}")
    else:
        st.info("Sistema de auditoria não disponível")

# ===== TAB 4: ESTATÍSTICAS =====
with tabs[3]:
    st.subheader("📈 Estatísticas do Sistema")
    
    if ALL_SERVICES_AVAILABLE:
        try:
            # Vector store stats
            vs_stats = vector_store.get_stats()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📚 Documentos", vs_stats.get('num_documentos', 0))
            with col2:
                st.metric("📄 Chunks", vs_stats.get('num_chunks', 0))
            with col3:
                avg_size = vs_stats.get('avg_chunk_size', 0)
                st.metric("📏 Tamanho Médio", f"{avg_size:.0f} chars")
            
            # Cache stats
            if ALL_SERVICES_AVAILABLE:
                st.markdown("---")
                st.markdown("### ⚡ Cache")
                cache_stats = cache_service.get_stats()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Cache Usuário", cache_stats.get('user_cache_entries', 0))
                with col2:
                    st.metric("Cache Global", cache_stats.get('global_cache_entries', 0))
                with col3:
                    st.metric("Total", cache_stats.get('total_entries', 0))
            
            # Audit stats
            if ALL_SERVICES_AVAILABLE:
                st.markdown("---")
                st.markdown("### 📊 Auditoria")
                audit_stats = audit_logger.get_stats()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Interações", audit_stats.get('total_interactions', 0))
                with col2:
                    st.metric("Usuários Únicos", audit_stats.get('unique_users', 0))
                with col3:
                    st.metric("Últimas 24h", audit_stats.get('last_24h', 0))
                
                # By role
                if audit_stats.get('by_role'):
                    st.markdown("**Por Role:**")
                    for role, count in audit_stats['by_role'].items():
                        st.caption(f"• {role}: {count}")
            
            # Documents by type
            if vs_stats.get('documentos_por_tipo'):
                st.markdown("---")
                st.markdown("### 📁 Documentos por Tipo")
                st.bar_chart(vs_stats['documentos_por_tipo'])
            
        except Exception as e:
            st.error(f"Erro ao carregar estatísticas: {e}")
    else:
        st.info("Estatísticas não disponíveis")

# ===== TAB 5: DOCUMENTAÇÃO =====
with tabs[4]:
    try:
        from components.documentation_viewer import render_documentation_tab
        from pathlib import Path
        
        render_documentation_tab(Path.cwd())
        
    except Exception as e:
        st.error(f"Erro ao carregar documentação: {e}")
        st.info("Verifique se os arquivos de documentação estão no diretório raiz do projeto")

# ===== TAB 6: ADMIN =====
with tabs[5]:
    try:
        from components.admin_panel import render_admin_panel
        
        render_admin_panel()
        
    except Exception as e:
        st.error(f"Erro ao carregar painel de administração: {e}")
        import traceback
        st.code(traceback.format_exc())
