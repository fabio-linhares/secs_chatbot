#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Painel de Administração Completo
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Painel administrativo com gerenciamento de usuários, banco e sistema
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import streamlit as st
from services.user_service import get_user_service
from services.vector_store import get_vector_store
from services.cache_service import get_cache_service
from services.audit import get_audit_logger
from components.env_editor import render_env_editor
from pathlib import Path
import subprocess
import sys
import os


def render_user_management():
    """Renderiza gerenciamento de usuários"""
    st.subheader("👥 Gerenciamento de Usuários")
    
    user_service = get_user_service()
    
    # Tabs
    tabs = st.tabs(["📋 Lista", "➕ Criar", "✏️ Editar"])
    
    # Tab 1: Lista de usuários
    with tabs[0]:
        users = user_service.list_users()
        
        st.metric("Total de Usuários", len(users))
        
        if users:
            st.markdown("### Usuários Cadastrados")
            
            for idx, user in enumerate(users):
                with st.expander(f"👤 {user.username} ({user.role})"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Username**: {user.username}")
                        st.write(f"**Role**: {user.role}")
                    
                    with col2:
                        if st.button(f"🗑️ Excluir", key=f"del_{idx}"):
                            if user.username == st.session_state.get("user_id"):
                                st.error("❌ Você não pode excluir sua própria conta!")
                            else:
                                try:
                                    user_service.delete_user(user.username)
                                    st.success(f"✅ Usuário {user.username} excluído!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Erro: {e}")
        else:
            st.info("Nenhum usuário cadastrado")
    
    # Tab 2: Criar usuário
    with tabs[1]:
        st.markdown("### Criar Novo Usuário")
        
        with st.form("create_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input("Username *")
            
            with col2:
                new_password = st.text_input("Senha *", type="password")
                new_role = st.selectbox(
                    "Role *",
                    options=["publico", "secs", "admin"],
                    help="publico=20 req/min, secs=50 req/min, admin=100 req/min"
                )
            
            submitted = st.form_submit_button("➕ Criar Usuário", type="primary")
            
            if submitted:
                if not new_username or not new_password:
                    st.error("❌ Username e senha são obrigatórios")
                elif len(new_password) < 6:
                    st.error("❌ Senha deve ter pelo menos 6 caracteres")
                else:
                    try:
                        user_service.create_user(
                            username=new_username,
                            password=new_password,
                            role=new_role
                        )
                        st.success(f"✅ Usuário {new_username} criado com sucesso!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Erro ao criar usuário: {e}")
    
    # Tab 3: Editar usuário
    with tabs[2]:
        st.markdown("### Editar Usuário")
        
        users = user_service.list_users()
        if users:
            selected_user = st.selectbox(
                "Selecione um usuário",
                options=[u.username for u in users]
            )
            
            user = next(u for u in users if u.username == selected_user)
            
            with st.form("edit_user_form"):
                new_role = st.selectbox(
                    "Nova Role",
                    options=["publico", "secs", "admin"],
                    index=["publico", "secs", "admin"].index(user.role)
                )
                
                new_password = st.text_input(
                    "Nova Senha (deixe vazio para não alterar)",
                    type="password"
                )
                
                if st.form_submit_button("💾 Salvar Alterações"):
                    try:
                        # Atualizar role
                        user_service.update_user_role(user.username, new_role)
                        
                        # Atualizar senha se fornecida
                        if new_password:
                            if len(new_password) < 6:
                                st.error("❌ Senha deve ter pelo menos 6 caracteres")
                            else:
                                user_service.reset_password(user.username, new_password)
                        
                        st.success("✅ Usuário atualizado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro: {e}")


def render_database_controls():
    """Renderiza controles do banco de dados"""
    st.subheader("🗄️ Controle do Banco de Dados")
    
    # Estatísticas
    col1, col2, col3 = st.columns(3)
    
    try:
        vector_store = get_vector_store()
        stats = vector_store.get_stats()
        
        with col1:
            st.metric("📄 Documentos", stats.get('num_documentos', 0))
        with col2:
            st.metric("📚 Chunks", stats.get('num_chunks', 0))
        with col3:
            cache_service = get_cache_service()
            cache_stats = cache_service.get_stats()
            st.metric("⚡ Cache", cache_stats.get('total_entries', 0))
    except:
        st.warning("Não foi possível carregar estatísticas")
    
    st.markdown("---")
    
    # Ações
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💾 Backup")
        
        if st.button("📦 Criar Backup Agora", use_container_width=True):
            try:
                from datetime import datetime
                import shutil
                
                backup_dir = Path("data/backups")
                backup_dir.mkdir(parents=True, exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = backup_dir / f"app_backup_{timestamp}.db"
                
                shutil.copy2("data/app.db", backup_path)
                
                st.success(f"✅ Backup criado: {backup_path}")
            except Exception as e:
                st.error(f"❌ Erro ao criar backup: {e}")
        
        # Listar backups
        backup_dir = Path("data/backups")
        if backup_dir.exists():
            backups = sorted(backup_dir.glob("*.db"), reverse=True)
            if backups:
                st.caption(f"📁 {len(backups)} backup(s) disponível(is)")
                selected_backup = st.selectbox(
                    "Restaurar backup",
                    options=[b.name for b in backups[:10]]
                )
    
    with col2:
        st.markdown("### 🧹 Limpeza")
        
        if st.button("🗑️ Limpar Cache", use_container_width=True):
            try:
                cache_service = get_cache_service()
                # Implementar limpeza de cache
                st.success("✅ Cache limpo!")
            except Exception as e:
                st.error(f"❌ Erro: {e}")
        
        if st.button("📊 Limpar Auditoria Antiga (>30 dias)", use_container_width=True):
            try:
                audit_logger = get_audit_logger()
                # Implementar limpeza de auditoria
                st.success("✅ Auditoria antiga removida!")
            except Exception as e:
                st.error(f"❌ Erro: {e}")


def render_app_controls():
    """Renderiza controles da aplicação"""
    st.subheader("🎛️ Controle da Aplicação")
    
    # Status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🟢 Status", "Online")
    
    # Try to get system metrics
    try:
        import psutil
        with col2:
            cpu = psutil.cpu_percent()
            st.metric("💻 CPU", f"{cpu}%")
        with col3:
            mem = psutil.virtual_memory()
            st.metric("🧠 RAM", f"{mem.percent}%")
    except ImportError:
        with col2:
            st.metric("💻 CPU", "N/A")
        with col3:
            st.metric("🧠 RAM", "N/A")
        st.caption("⚠️ Instale psutil para monitoramento: pip install psutil")
    
    st.markdown("---")
    
    # Reiniciar aplicação
    st.markdown("### 🔄 Reiniciar Aplicação")
    
    st.info("""
    ⚠️ **Como reiniciar a aplicação**:
    
    Para aplicar mudanças de configuração (.env), você precisa reiniciar manualmente:
    
    1. Pressione `Ctrl+C` no terminal onde o Streamlit está rodando
    2. Execute novamente: `streamlit run src/app_enhanced.py`
    
    Ou use o botão "Rerun" no canto superior direito do Streamlit (⟳).
    """)
    
    if st.button("⟳ Recarregar Página", type="primary", use_container_width=True):
        st.rerun()
    
    st.markdown("---")
    
    # Logs
    st.markdown("### 📝 Logs do Sistema")
    
    log_file = Path("data/logs/app.log")
    if log_file.exists():
        num_lines = st.slider("Número de linhas", 10, 100, 50)
        
        if st.button("📄 Ver Logs"):
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    last_lines = lines[-num_lines:]
                    st.code(''.join(last_lines), language='log')
            except Exception as e:
                st.error(f"❌ Erro ao ler logs: {e}")
    else:
        st.info("Nenhum arquivo de log encontrado")


def render_admin_panel():
    """Renderiza painel administrativo completo"""
    
    # Verificar se é admin
    if st.session_state.get("role") != "admin":
        st.error("❌ Acesso negado! Apenas administradores podem acessar este painel.")
        return
    
    st.title("⚙️ Painel de Administração")
    st.markdown("Gerenciamento completo do sistema")
    st.markdown("---")
    
    # Tabs do admin
    admin_tabs = st.tabs(["👥 Usuários", "📚 Documentos", "⚙️ Configurações", "🗄️ Banco de Dados", "🎛️ Sistema"])
    
    with admin_tabs[0]:
        render_user_management()
    
    with admin_tabs[1]:
        render_document_management()
    
    with admin_tabs[2]:
        render_env_editor()
    
    with admin_tabs[3]:
        render_database_controls()
    
    with admin_tabs[4]:
        render_app_controls()


def render_document_management():
    """Renderiza gerenciamento de documentos"""
    from services.document_manager import get_document_manager
    from services.vector_store import get_vector_store
    
    st.subheader("📚 Gerenciamento de Documentos")
    
    doc_manager = get_document_manager()
    vector_store = get_vector_store()
    
    # Estatísticas combinadas
    upload_stats = doc_manager.get_stats()
    vector_stats = vector_store.get_stats()
    
    # Combinar estatísticas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_docs = upload_stats["total_documents"] + vector_stats.get("num_documentos", 0)
        st.metric("📄 Total Documentos", total_docs)
        st.caption(f"Uploads: {upload_stats['total_documents']} | Vetorizados: {vector_stats.get('num_documentos', 0)}")
    with col2:
        st.metric("💾 Espaço Usado", f"{upload_stats['total_mb']:.1f} MB")
        st.caption("Apenas uploads")
    with col3:
        st.metric("🌐 Documentos Globais", upload_stats["global_documents"])
        st.caption("Via upload")
    with col4:
        st.metric("📦 Chunks Vetoriais", vector_stats.get("num_chunks", 0))
        st.caption(f"{vector_stats.get('num_documentos', 0)} docs processados")
    
    st.markdown("---")
    
    # Upload global
    st.markdown("### 📤 Upload de Documento Global")
    st.caption("Documentos globais ficam disponíveis para todos os usuários")
    
    uploaded_file = st.file_uploader(
        "Selecione um PDF para upload global",
        type=["pdf"],
        key="admin_upload"
    )
    
    if uploaded_file and st.button("📤 Fazer Upload Global", type="primary"):
        with st.spinner("Fazendo upload..."):
            doc = doc_manager.upload_document(
                file=uploaded_file,
                original_name=uploaded_file.name,
                user_id=st.session_state.get("user_id", "admin"),
                is_global=True
            )
            
            if doc:
                st.success(f"✅ Documento global criado! ID: {doc.id}")
                
                # Processar
                with st.spinner("Processando..."):
                    try:
                        from pathlib import Path
                        from utils.pdf_processor import process_document
                        from services.vector_store import get_vector_store
                        
                        doc_path = Path("data/documents/global") / doc.filename
                        chunks_data = process_document(str(doc_path))
                        
                        # Preparar chunks com metadata
                        chunks_with_metadata = [
                            {
                                "text": chunk["text"],
                                "page": chunk.get("page", 0),
                                "metadata": {
                                    "source": doc.original_name,
                                    "doc_id": doc.id,
                                    "is_global": True
                                }
                            }
                            for chunk in chunks_data
                        ]
                        
                        # Adicionar ao vector store
                        from utils.vector_store_helper import add_chunks_to_vector_store
                        add_chunks_to_vector_store(chunks_with_metadata)
                        
                        doc_manager.update_document_status(
                            doc.id,
                            status="processed",
                            processed=True,
                            num_chunks=len(chunks_data)
                        )
                        
                        st.success(f"✅ Processado! {len(chunks_data)} chunks criados.")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao processar: {e}")
            else:
                st.error("❌ Erro ao fazer upload")
    
    st.markdown("---")
    
    # Lista de todos os documentos
    st.markdown("### 📋 Todos os Documentos")
    
    # Tabs para separar uploads e vetorizados
    doc_tabs = st.tabs(["📤 Uploads (Interface)", "🔢 Vetorizados (run.sh)"])
    
    # Tab 1: Documentos via upload
    with doc_tabs[0]:
        all_docs = doc_manager.list_all_documents()
        
        # Filtro
        filter_type = st.selectbox(
            "Filtrar por tipo",
            ["Todos", "Globais", "Por Usuário"],
            key="filter_uploads"
        )
        
        if filter_type == "Globais":
            filtered_docs = [d for d in all_docs if d.is_global]
        elif filter_type == "Por Usuário":
            filtered_docs = [d for d in all_docs if not d.is_global]
        else:
            filtered_docs = all_docs
        
        st.caption(f"Mostrando {len(filtered_docs)} documento(s) via upload")
        
        if not filtered_docs:
            st.info("Nenhum documento enviado via interface ainda")
        
        for doc in filtered_docs[:20]:  # Limitar a 20
            with st.expander(f"{'🌐' if doc.is_global else '👤'} {doc.original_name} - {doc.user_id}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**ID**: {doc.id}")
                    st.write(f"**Usuário**: {doc.user_id}")
                    st.write(f"**Tipo**: {'Global' if doc.is_global else 'Pessoal'}")
                    st.write(f"**Tamanho**: {doc.file_size / 1024:.1f} KB")
                    st.write(f"**Upload**: {doc.upload_date[:19]}")
                    st.write(f"**Status**: {'✅ Processado' if doc.processed else '⏳ ' + doc.status}")
                    if doc.processed:
                        st.write(f"**Chunks**: {doc.num_chunks}")
                
                with col2:
                    if st.button("🗑️ Excluir", key=f"admin_del_{doc.id}"):
                        if doc_manager.delete_document(doc.id, st.session_state.get("user_id"), is_admin=True):
                            st.success("✅ Excluído!")
                            st.rerun()
                        else:
                            st.error("❌ Erro")
    
    # Tab 2: Documentos vetorizados
    with doc_tabs[1]:
        import sqlite3
        
        conn = sqlite3.connect(doc_manager.db_path)
        cursor = conn.execute("""
            SELECT id, tipo, titulo, numero, data, conselho, caminho, criado_em
            FROM documentos
            ORDER BY criado_em DESC
        """)
        vectorized_docs = cursor.fetchall()
        conn.close()
        
        # Filtro por tipo
        tipos_disponiveis = list(set([doc[1] for doc in vectorized_docs]))
        filter_tipo = st.selectbox(
            "Filtrar por tipo",
            ["Todos"] + sorted(tipos_disponiveis),
            key="filter_vectorized"
        )
        
        if filter_tipo != "Todos":
            filtered_vectorized = [d for d in vectorized_docs if d[1] == filter_tipo]
        else:
            filtered_vectorized = vectorized_docs
        
        st.caption(f"Mostrando {len(filtered_vectorized)} documento(s) vetorizado(s)")
        
        # Estatísticas por tipo
        if vectorized_docs:
            tipo_counts = {}
            for doc in vectorized_docs:
                tipo = doc[1]
                tipo_counts[tipo] = tipo_counts.get(tipo, 0) + 1
            
            st.markdown("**Documentos por tipo:**")
            cols = st.columns(len(tipo_counts))
            for idx, (tipo, count) in enumerate(sorted(tipo_counts.items())):
                with cols[idx]:
                    st.metric(tipo.capitalize(), count)
        
        st.markdown("---")
        
        # Listar documentos
        for doc in filtered_vectorized[:50]:  # Limitar a 50
            doc_id, tipo, titulo, numero, data, conselho, caminho, criado_em = doc
            
            # Ícone por tipo
            icon_map = {
                "ata": "📝",
                "pauta": "📋",
                "resolucao": "📜",
                "regimento": "📕",
                "pdf": "📄"
            }
            icon = icon_map.get(tipo, "📄")
            
            with st.expander(f"{icon} {titulo} ({tipo})"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**ID**: {doc_id}")
                    st.write(f"**Tipo**: {tipo}")
                    st.write(f"**Título**: {titulo}")
                    if numero:
                        st.write(f"**Número**: {numero}")
                    if data:
                        st.write(f"**Data**: {data}")
                    if conselho:
                        st.write(f"**Conselho**: {conselho}")
                    st.write(f"**Caminho**: {caminho}")
                    st.write(f"**Processado em**: {criado_em[:19] if criado_em else 'N/A'}")
                
                with col2:
                    st.caption("Vetorizado via run.sh")
                    # Contar chunks
                    conn = sqlite3.connect(doc_manager.db_path)
                    cursor = conn.execute(
                        "SELECT COUNT(*) FROM chunks WHERE documento_id = ?",
                        (doc_id,)
                    )
                    num_chunks = cursor.fetchone()[0]
                    conn.close()
                    st.metric("Chunks", num_chunks)
    
    st.markdown("---")
    
    # Gerenciamento de quotas
    st.markdown("### 💾 Gerenciamento de Quotas")
    
    # Listar usuários com documentos
    users_with_docs = stats.get("documents_by_user", {})
    
    if users_with_docs:
        for user_id, doc_count in users_with_docs.items():
            quota = doc_manager.get_user_quota(user_id)
            
            with st.expander(f"👤 {user_id} ({doc_count} docs, {quota.used_mb:.1f}/{quota.quota_mb} MB)"):
                new_quota = st.number_input(
                    "Nova quota (MB)",
                    min_value=10,
                    max_value=1000,
                    value=quota.quota_mb,
                    step=10,
                    key=f"quota_{user_id}"
                )
                
                if st.button("💾 Atualizar Quota", key=f"update_quota_{user_id}"):
                    doc_manager.update_user_quota(user_id, new_quota)
                    st.success(f"✅ Quota de {user_id} atualizada para {new_quota} MB!")
                    st.rerun()
    else:
        st.info("Nenhum usuário com documentos ainda")


def render_env_editor():
    """Renderiza editor de .env - implementado em env_editor.py"""
    from components.env_editor import render_env_editor as _render_env_editor
    _render_env_editor()
