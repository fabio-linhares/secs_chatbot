#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Aplicação Streamlit básica
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Aplicação Streamlit básica
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import streamlit as st
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.llm import llm_service
from config import settings
from utils.prompts import (
    SYSTEM_PROMPT, 
    WELCOME_MESSAGE, 
    GUARDRAIL_MESSAGES,
    check_scope,
    build_messages_with_context
)

# RAG imports
try:
    from services.vector_store import get_vector_store
    from agents.query_enhancer import get_query_enhancer
    RAG_ENABLED = True
    vector_store = get_vector_store()
    query_enhancer = get_query_enhancer()
except Exception as e:
    RAG_ENABLED = False
    print(f"Warning: RAG not available: {e}")

# Cache and Audit imports
try:
    from services.cache_service import get_cache_service
    from services.audit import get_audit_logger, AuditRecord
    cache_service = get_cache_service()
    audit_logger = get_audit_logger()
    CACHE_ENABLED = True
    AUDIT_ENABLED = True
except Exception as e:
    CACHE_ENABLED = False
    AUDIT_ENABLED = False
    print(f"Warning: Cache/Audit not available: {e}")

# Page Config
st.set_page_config(
    page_title="Chatbot SECS/UFAL",
    page_icon="🏛️",
    layout="wide"
)

# Sidebar
with st.sidebar:
    st.title("🏛️ SECS/UFAL")
    st.markdown("**Secretaria dos Conselhos Superiores**")
    st.markdown("Universidade Federal de Alagoas")
    st.markdown("---")
    
    if st.button("🗑️ Limpar Conversa", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("### ℹ️ Sobre")
    st.caption("Este assistente fornece informações sobre regimentos, estatutos e resoluções dos Conselhos Superiores da UFAL.")
    
    # RAG status
    if RAG_ENABLED:
        try:
            stats = vector_store.get_stats()
            st.markdown("---")
            st.markdown("### 📚 Base de Conhecimento")
            st.caption(f"Documentos: {stats['num_documentos']}")
            st.caption(f"Chunks: {stats['num_chunks']}")
            with st.expander("Ver detalhes"):
                for tipo, count in stats.get('documentos_por_tipo', {}).items():
                    st.caption(f"• {tipo}: {count}")
        except:
            pass
    
    st.markdown("---")
    st.caption(f"Modelo: {settings.llm_model}")
    st.caption(f"Ambiente: {settings.environment}")
    if RAG_ENABLED:
        st.caption("✅ RAG Ativo")

# Main Chat Interface
st.title("Assistente Virtual - Conselhos Superiores")
st.markdown("*Secretaria dos Conselhos Superiores (SECS) - UFAL*")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Show welcome message
    with st.chat_message("assistant"):
        st.markdown(WELCOME_MESSAGE)

if "user_id" not in st.session_state:
    st.session_state.user_id = "anon"

if "last_cache_source" not in st.session_state:
    st.session_state.last_cache_source = None

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # Show sources if available
        if "sources" in message and message["sources"]:
            with st.expander("📚 Fontes consultadas"):
                for source in message["sources"]:
                    st.caption(f"• {source}")

# React to user input
if prompt := st.chat_input("Digite sua mensagem..."):
    # Check scope
    if not check_scope(prompt):
        # Display user message
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display out-of-scope message
        with st.chat_message("assistant"):
            st.markdown(GUARDRAIL_MESSAGES["fora_escopo"])
        st.session_state.messages.append({"role": "assistant", "content": GUARDRAIL_MESSAGES["fora_escopo"]})
    else:
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            sources_placeholder = st.empty()
            full_response = ""
            sources = []
            cache_source = None
            
            # === CACHE CHECK ===
            if CACHE_ENABLED:
                # Try user cache first
                cached = cache_service.get_user_answer(st.session_state.user_id, prompt)
                if cached and not cache_service.should_bypass_cache(cached):
                    cache_source = "user"
                    full_response = cached
                    message_placeholder.markdown(full_response)
                    st.caption("⚡ Resposta do cache (usuário)")
                    
                    # Log cache hit
                    if AUDIT_ENABLED:
                        audit_logger.log(AuditRecord(
                            user=st.session_state.user_id,
                            role="publico",
                            input_text=prompt,
                            output_text=full_response,
                            metadata={"cache_hit": "user", "history_length": len(st.session_state.messages)}
                        ))
                    
                    st.session_state.last_cache_source = cache_source
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": full_response,
                        "sources": []
                    })
                    st.rerun()
                
                # Try global cache
                if not cache_source:
                    cached_global = cache_service.get_global_answer(prompt)
                    if cached_global and not cache_service.should_bypass_cache(cached_global):
                        cache_source = "global"
                        full_response = cached_global
                        message_placeholder.markdown(full_response)
                        st.caption("⚡ Resposta do cache (global)")
                        
                        # Log cache hit
                        if AUDIT_ENABLED:
                            audit_logger.log(AuditRecord(
                                user=st.session_state.user_id,
                                role="publico",
                                input_text=prompt,
                                output_text=full_response,
                                metadata={"cache_hit": "global", "history_length": len(st.session_state.messages)}
                            ))
                        
                        st.session_state.last_cache_source = cache_source
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": full_response,
                            "sources": []
                        })
                        st.rerun()
            
            # === RAG PIPELINE ===
            search_query = prompt
            enhanced_info = None
            
            if RAG_ENABLED:
                # Step 1: Query Enhancement
                try:
                    enhanced_info = query_enhancer.enhance_query(
                        user_query=prompt,
                        conversation_history=st.session_state.messages[:-1]  # Exclude current message
                    )
                    search_query = enhanced_info.enhanced_query
                    
                    # Show enhancement if significant
                    if enhanced_info.confidence > 0.6 and search_query != prompt:
                        with st.expander("🔍 Query melhorada", expanded=False):
                            st.caption(f"Original: {prompt}")
                            st.caption(f"Melhorada: {search_query}")
                            st.caption(f"Confiança: {enhanced_info.confidence:.0%}")
                    
                    # DEBUG: Show search query
                    if settings.debug:
                        st.info(f"🔍 Buscando: {search_query}")
                        
                except Exception as e:
                    print(f"Query enhancement error: {e}")
                
                # Step 2: Vector Search
                try:
                    # Detect document type from BOTH original and enhanced query
                    original_lower = prompt.lower()
                    enhanced_lower = search_query.lower()
                    filters = {}
                    
                    # Check original query first (higher priority)
                    if 'pauta' in original_lower or 'pauta' in enhanced_lower:
                        filters['tipo'] = 'pauta'
                    elif 'ata' in original_lower or 'ata' in enhanced_lower:
                        filters['tipo'] = 'ata'
                    elif ('resolução' in original_lower or 'resolucao' in original_lower or 
                          'resolução' in enhanced_lower or 'resolucao' in enhanced_lower):
                        filters['tipo'] = 'resolucao'
                    elif ('regimento' in original_lower or 'estatuto' in original_lower or
                          'regimento' in enhanced_lower or 'estatuto' in enhanced_lower):
                        filters['tipo'] = 'regimento'
                    
                    # Search with or without filters
                    if filters:
                        # First try with filter
                        search_results = vector_store.search_with_filter(search_query, filters, k=8)
                        
                        # If no results, try without filter
                        if not search_results or len(search_results) < 3:
                            if settings.debug:
                                st.warning(f"⚠️ Poucos resultados com filtro {filters}, buscando sem filtro...")
                            search_results = vector_store.search(search_query, k=8)
                    else:
                        # No specific type detected, search all
                        search_results = vector_store.search(search_query, k=8)
                    
                    # DEBUG: Show all search results
                    if settings.debug and search_results:
                        with st.expander("🔬 Debug: Resultados da busca", expanded=False):
                            if filters:
                                st.caption(f"🎯 Filtro aplicado: {filters}")
                            for i, r in enumerate(search_results, 1):
                                st.caption(f"{i}. [{r['tipo']}] {r['titulo']} - Similaridade: {r['similarity']:.4f}")
                    
                    if search_results:
                        # === CLARIFICATION CHECK ===
                        from agents.clarification_agent import get_clarification_agent
                        
                        clarification_agent = get_clarification_agent()
                        clarification = clarification_agent.check_for_ambiguity(
                            user_query=prompt,
                            search_results=search_results,
                            conversation_history=st.session_state.messages[:-1]
                        )
                        
                        if clarification and clarification.confidence > 0.7:
                            # Ask for clarification instead of answering
                            full_response = f"🤔 {clarification.question}\n\n"
                            
                            if clarification.options:
                                full_response += "**Opções:**\n"
                                for opt in clarification.options:
                                    full_response += f"- {opt}\n"
                            
                            full_response += "\nPor favor, seja mais específico para que eu possa ajudá-lo melhor."
                            
                            message_placeholder.markdown(full_response)
                            
                            # Don't use sources for clarification
                            sources = []
                        else:
                            # Proceed with normal RAG response
                            # Build context from search results
                            context_parts = []
                            for i, result in enumerate(search_results[:5], 1):  # Top 5
                                context_parts.append(f"""
Fonte {i}: {result['titulo']} ({result['tipo']})
Número: {result.get('numero', 'N/A')} | Data: {result.get('data', 'N/A')}
Similaridade: {result['similarity']:.2%}

{result['conteudo'][:1500]}...
""")
                                sources.append(f"{result['titulo']} - {result['tipo']}")
                            
                            context = "\n\n".join(context_parts)
                            
                            # Update system prompt with RAG context
                            rag_system_prompt = f"""{SYSTEM_PROMPT}

## CONTEXTO RECUPERADO DA BASE DE CONHECIMENTO

{context}

INSTRUÇÕES IMPORTANTES:
1. Use PRIORITARIAMENTE as informações do contexto acima para responder
2. Se a informação está no contexto, responda com base nele
3. SEMPRE cite as fontes específicas (documento, artigo, seção)
4. Se a informação NÃO está no contexto, diga claramente que não encontrou
5. Não invente informações que não estão no contexto fornecido"""
                            
                            # Build messages with RAG context
                            api_messages = [{"role": "system", "content": rag_system_prompt}]
                            
                            # Add conversation history (last 5 exchanges)
                            for msg in st.session_state.messages[-10:-1]:
                                api_messages.append({"role": msg["role"], "content": msg["content"]})
                            
                            # Add current query
                            api_messages.append({"role": "user", "content": prompt})
                            
                            # Call LLM
                            stream = llm_service.get_response(api_messages)
                            
                            if stream:
                                try:
                                    for chunk in stream:
                                        if chunk.choices[0].delta.content is not None:
                                            full_response += chunk.choices[0].delta.content
                                            message_placeholder.markdown(full_response + "▌")
                                    message_placeholder.markdown(full_response)
                                    
                                    # Show sources
                                    if sources:
                                        with sources_placeholder.expander("📚 Fontes consultadas"):
                                            for source in sources:
                                                st.caption(f"• {source}")
                                    
                                except Exception as e:
                                    full_response = f"Desculpe, ocorreu um erro ao processar sua solicitação: {str(e)}"
                                    message_placeholder.error(full_response)
                            else:
                                full_response = "Desculpe, ocorreu um erro ao conectar com o modelo."
                                message_placeholder.error(full_response)
                    else:
                        # No results found
                        full_response = "Não encontrei informações relevantes nos documentos disponíveis."
                        message_placeholder.markdown(full_response)
                        
                except Exception as e:
                    print(f"Vector search error: {e}")
                    full_response = f"Erro na busca: {str(e)}"
                    message_placeholder.error(full_response)
            else:
                # RAG not available, use regular flow
                full_response = "Sistema RAG não disponível no momento."
                message_placeholder.warning(full_response)
                
        # Add assistant response to chat history with sources
        st.session_state.messages.append({
            "role": "assistant", 
            "content": full_response,
            "sources": sources
        })
        
        # === CACHE & AUDIT ===
        # Cache the response (if not from cache and not negative)
        if CACHE_ENABLED and not cache_source:
            if not cache_service.should_bypass_cache(full_response):
                cache_service.set_user_answer(st.session_state.user_id, prompt, full_response)
                cache_service.set_global_answer(prompt, full_response)
        
        # Audit log (if not already logged from cache hit)
        if AUDIT_ENABLED and not cache_source:
            audit_logger.log(AuditRecord(
                user=st.session_state.user_id,
                role="publico",
                input_text=prompt,
                output_text=full_response,
                metadata={
                    "cache_hit": None,
                    "history_length": len(st.session_state.messages),
                    "retrieved_chunks": len(sources),
                    "rag_enabled": RAG_ENABLED
                }
            ))
