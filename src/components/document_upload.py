#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Interface de Upload de Documentos
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Interface para usuários fazerem upload de PDFs
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import streamlit as st
from services.document_manager import get_document_manager
from utils.pdf_processor import process_document
from services.vector_store import get_vector_store


def render_document_upload():
    """Renderiza interface de upload de documentos"""
    
    st.title("📤 Meus Documentos")
    st.markdown("Faça upload de PDFs para enriquecer a base de conhecimento")
    st.markdown("---")
    
    doc_manager = get_document_manager()
    user_id = st.session_state.get("user_id", "anon")
    role = st.session_state.get("role", "publico")
    
    # Obter quota
    quota = doc_manager.get_user_quota(user_id, role)
    
    # Mostrar quota
    st.markdown("### 📊 Sua Quota de Armazenamento")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Usado", f"{quota.used_mb:.1f} MB")
    with col2:
        st.metric("Limite", f"{quota.quota_mb} MB")
    with col3:
        percent = (quota.used_mb / quota.quota_mb * 100) if quota.quota_mb > 0 else 0
        st.metric("Utilização", f"{percent:.0f}%")
    
    # Progress bar
    progress = min(quota.used_mb / quota.quota_mb, 1.0) if quota.quota_mb > 0 else 0
    st.progress(progress)
    
    if percent > 90:
        st.warning("⚠️ Você está próximo do limite de armazenamento!")
    
    st.markdown("---")
    
    # Upload
    st.markdown("### 📤 Upload de Documento")
    
    # Permission option (admin only)
    is_global = False
    if role == "admin":
        st.markdown("#### 🔐 Permissões de Acesso")
        is_global = st.checkbox(
            "🌍 Tornar documento global (visível para todos os usuários)",
            value=False,
            help="Se marcado, todos os usuários poderão ver este documento. Caso contrário, apenas você terá acesso."
        )
        
        if is_global:
            st.info("ℹ️ Este documento será visível para **todos os usuários** do sistema.")
        else:
            st.info("ℹ️ Este documento será **privado** e visível apenas para você.")
        
        st.markdown("---")
    
    uploaded_file = st.file_uploader(
        "Selecione um arquivo PDF",
        type=["pdf"],
        help="Apenas arquivos PDF são aceitos"
    )
    
    if uploaded_file:
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        
        st.info(f"📄 **{uploaded_file.name}** ({file_size_mb:.2f} MB)")
        
        # Verificar se cabe na quota
        if quota.used_mb + file_size_mb > quota.quota_mb:
            st.error(f"""
            ❌ **Quota excedida!**
            
            - Arquivo: {file_size_mb:.2f} MB
            - Disponível: {quota.quota_mb - quota.used_mb:.2f} MB
            
            Exclua alguns documentos ou solicite aumento de quota ao administrador.
            """)
        else:
            if st.button("📤 Fazer Upload", type="primary"):
                with st.spinner("Fazendo upload..."):
                    # Upload
                    doc = doc_manager.upload_document(
                        file=uploaded_file,
                        original_name=uploaded_file.name,
                        user_id=user_id,
                        role=role,
                        is_global=is_global
                    )
                    
                    if doc:
                        st.success(f"✅ Upload concluído! Documento ID: {doc.id}")
                        
                        # Processar em background
                        with st.spinner("Processando documento..."):
                            try:
                                # Determinar path
                                from pathlib import Path
                                doc_path = Path("data/documents/users") / user_id / doc.filename
                                
                                # Processar PDF
                                chunks_data = process_document(str(doc_path))
                                
                                # Preparar chunks com metadata
                                chunks_with_metadata = [
                                    {
                                        "text": chunk["text"],
                                        "page": chunk.get("page", 0),
                                        "metadata": {
                                            "source": doc.original_name,
                                            "doc_id": doc.id,
                                            "user_id": user_id,
                                            "is_global": False
                                        }
                                    }
                                    for chunk in chunks_data
                                ]
                                
                                # Adicionar ao vector store
                                from utils.vector_store_helper import add_chunks_to_vector_store
                                add_chunks_to_vector_store(chunks_with_metadata)
                                
                                # Atualizar status
                                doc_manager.update_document_status(
                                    doc.id,
                                    status="processed",
                                    processed=True,
                                    num_chunks=len(chunks_data)
                                )
                                
                                st.success(f"✅ Documento processado! {len(chunks_data)} chunks criados.")
                                st.balloons()
                                st.rerun()
                                
                            except Exception as e:
                                doc_manager.update_document_status(doc.id, status=f"error: {str(e)}")
                                st.error(f"❌ Erro ao processar: {e}")
                    else:
                        st.error("❌ Erro ao fazer upload")
    
    st.markdown("---")
    
    # Lista de documentos
    st.markdown("### 📚 Meus Documentos")
    
    docs = doc_manager.list_user_documents(user_id)
    user_docs = [d for d in docs if d.user_id == user_id]
    
    # Filtros
    if user_docs:
        col1, col2 = st.columns([2, 1])
        with col1:
            filter_type = st.selectbox(
                "Filtrar por:",
                ["Todos", "Privados", "Globais", "Processados", "Pendentes"],
                key="doc_filter"
            )
        with col2:
            st.caption(f"Total: {len(user_docs)} documento(s)")
        
        # Aplicar filtros
        filtered_docs = user_docs
        if filter_type == "Privados":
            filtered_docs = [d for d in user_docs if not d.is_global]
        elif filter_type == "Globais":
            filtered_docs = [d for d in user_docs if d.is_global]
        elif filter_type == "Processados":
            filtered_docs = [d for d in user_docs if d.processed]
        elif filter_type == "Pendentes":
            filtered_docs = [d for d in user_docs if not d.processed]
        
        for doc in filtered_docs:
            # Badge de permissão
            permission_badge = "🌍 Global" if doc.is_global else "🔒 Privado"
            status_icon = "✅" if doc.processed else "⏳"
            
            with st.expander(f"{status_icon} {permission_badge} | {doc.original_name}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Tamanho**: {doc.file_size / 1024:.1f} KB")
                    st.write(f"**Upload**: {doc.upload_date[:19]}")
                    st.write(f"**Permissão**: {permission_badge}")
                    
                    if doc.processed:
                        st.write(f"**Status**: ✅ Processado ({doc.num_chunks} chunks)")
                    else:
                        st.write(f"**Status**: ⏳ {doc.status}")
                
                with col2:
                    # Toggle de permissão (admin only)
                    if role == "admin":
                        new_is_global = st.toggle(
                            "Global",
                            value=doc.is_global,
                            key=f"toggle_{doc.id}",
                            help="Marque para tornar visível a todos"
                        )
                        
                        if new_is_global != doc.is_global:
                            # Atualizar permissão no banco
                            import sqlite3
                            conn = sqlite3.connect("data/app.db")
                            
                            # Atualizar documents
                            conn.execute(
                                "UPDATE documents SET is_global = ? WHERE id = ?",
                                (new_is_global, doc.id)
                            )
                            
                            # Atualizar documentos (se existir)
                            conn.execute(
                                "UPDATE documentos SET is_global = ? WHERE user_id = ? AND titulo LIKE ?",
                                (new_is_global, user_id, f"%{doc.original_name.replace('.pdf', '')}%")
                            )
                            
                            conn.commit()
                            conn.close()
                            
                            st.success(f"✅ Permissão atualizada!")
                            st.rerun()
                    
                    st.markdown("")  # Spacing
                    if st.button("🗑️ Excluir", key=f"del_{doc.id}"):
                        if doc_manager.delete_document(doc.id, user_id, is_admin=(role=="admin")):
                            st.success("✅ Documento excluído!")
                            st.rerun()
                        else:
                            st.error("❌ Erro ao excluir")
    else:
        st.info("Você ainda não fez upload de nenhum documento.")
    
    # Documentos globais de outros usuários
    global_docs = [d for d in docs if d.is_global and d.user_id != user_id]
    if global_docs:
        st.markdown("---")
        st.markdown("### 🌐 Documentos Globais (Outros Usuários)")
        st.caption(f"{len(global_docs)} documento(s) compartilhado(s)")
        
        for doc in global_docs[:10]:  # Mostrar até 10
            status_icon = "✅" if doc.processed else "⏳"
            st.caption(f"{status_icon} 🌍 {doc.original_name} ({doc.num_chunks} chunks) - por {doc.user_id}")
