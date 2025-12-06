#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Painel de documentos e permissões (Admin)
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Painel Streamlit para gerenciamento de documentos e permissões
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import streamlit as st
import sqlite3
from services.document_manager import get_document_manager


def render_document_permissions_panel():
    """Painel completo de gerenciamento de documentos e permissões"""
    
    st.title("📚 Gerenciamento de Documentos e Permissões")
    st.markdown("Gerencie documentos, permissões e visualize estatísticas")
    st.markdown("---")
    
    doc_manager = get_document_manager()
    
    # Estatísticas Gerais
    st.markdown("### 📊 Estatísticas Gerais")
    
    conn = sqlite3.connect("data/app.db")
    
    # Métricas
    cursor = conn.execute("SELECT COUNT(*) FROM documents")
    total_docs = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM documents WHERE is_global = 1")
    global_docs = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM documents WHERE is_global = 0")
    private_docs = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM documents WHERE processed = 1")
    processed_docs = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT SUM(file_size) FROM documents")
    total_size = cursor.fetchone()[0] or 0
    total_mb = total_size / (1024 * 1024)
    
    # Documentos por usuário
    cursor = conn.execute("""
        SELECT user_id, COUNT(*), SUM(file_size)
        FROM documents
        GROUP BY user_id
        ORDER BY COUNT(*) DESC
    """)
    docs_by_user = cursor.fetchall()
    
    conn.close()
    
    # Mostrar métricas
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total", total_docs)
    with col2:
        st.metric("🌍 Globais", global_docs)
    with col3:
        st.metric("🔒 Privados", private_docs)
    with col4:
        st.metric("✅ Processados", processed_docs)
    with col5:
        st.metric("Armazenamento", f"{total_mb:.1f} MB")
    
    st.markdown("---")
    
    # Documentos por usuário
    st.markdown("### 👥 Documentos por Usuário")
    
    for user_id, count, size in docs_by_user:
        size_mb = (size or 0) / (1024 * 1024)
        with st.expander(f"👤 {user_id} - {count} documento(s) ({size_mb:.1f} MB)"):
            # Listar documentos do usuário
            conn = sqlite3.connect("data/app.db")
            cursor = conn.execute("""
                SELECT id, original_name, is_global, processed, num_chunks, file_size, upload_date
                FROM documents
                WHERE user_id = ?
                ORDER BY upload_date DESC
            """, (user_id,))
            
            user_docs = cursor.fetchall()
            conn.close()
            
            for doc_id, name, is_global, processed, chunks, fsize, upload_date in user_docs:
                permission_badge = "🌍 Global" if is_global else "🔒 Privado"
                status_icon = "✅" if processed else "⏳"
                
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.caption(f"{status_icon} {permission_badge} | {name}")
                    st.caption(f"   {fsize/1024:.1f} KB | {chunks} chunks | {upload_date[:10]}")
                
                with col2:
                    # Toggle permissão
                    new_is_global = st.toggle(
                        "Global",
                        value=bool(is_global),
                        key=f"perm_{doc_id}",
                        help="Marque para tornar global"
                    )
                    
                    if new_is_global != bool(is_global):
                        conn = sqlite3.connect("data/app.db")
                        conn.execute(
                            "UPDATE documents SET is_global = ? WHERE id = ?",
                            (new_is_global, doc_id)
                        )
                        conn.execute(
                            "UPDATE documentos SET is_global = ? WHERE user_id = ? AND titulo LIKE ?",
                            (new_is_global, user_id, f"%{name.replace('.pdf', '')}%")
                        )
                        conn.commit()
                        conn.close()
                        st.success("✅ Atualizado!")
                        st.rerun()
                
                with col3:
                    if st.button("🗑️", key=f"del_admin_{doc_id}", help="Excluir documento"):
                        if doc_manager.delete_document(doc_id, user_id, is_admin=True):
                            st.success("✅ Excluído!")
                            st.rerun()
    
    st.markdown("---")
    
    # Operações em Massa
    st.markdown("### ⚙️ Operações em Massa")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🌍 Tornar Todos Globais", help="Torna TODOS os documentos visíveis para todos"):
            conn = sqlite3.connect("data/app.db")
            conn.execute("UPDATE documents SET is_global = 1")
            conn.execute("UPDATE documentos SET is_global = 1")
            conn.commit()
            conn.close()
            st.success("✅ Todos os documentos agora são globais!")
            st.rerun()
    
    with col2:
        if st.button("🔒 Tornar Todos Privados", help="Torna TODOS os documentos privados"):
            conn = sqlite3.connect("data/app.db")
            conn.execute("UPDATE documents SET is_global = 0")
            conn.execute("UPDATE documentos SET is_global = 0")
            conn.commit()
            conn.close()
            st.success("✅ Todos os documentos agora são privados!")
            st.rerun()
    
    st.markdown("---")
    
    # Filtros e Busca
    st.markdown("### 🔍 Buscar e Filtrar Documentos")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_term = st.text_input("Buscar por nome", placeholder="Digite parte do nome do arquivo...")
    
    with col2:
        filter_type = st.selectbox(
            "Filtrar por",
            ["Todos", "Globais", "Privados", "Processados", "Pendentes"]
        )
    
    if search_term or filter_type != "Todos":
        conn = sqlite3.connect("data/app.db")
        
        query = "SELECT id, original_name, user_id, is_global, processed, num_chunks FROM documents WHERE 1=1"
        params = []
        
        if search_term:
            query += " AND original_name LIKE ?"
            params.append(f"%{search_term}%")
        
        if filter_type == "Globais":
            query += " AND is_global = 1"
        elif filter_type == "Privados":
            query += " AND is_global = 0"
        elif filter_type == "Processados":
            query += " AND processed = 1"
        elif filter_type == "Pendentes":
            query += " AND processed = 0"
        
        query += " ORDER BY upload_date DESC LIMIT 50"
        
        cursor = conn.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        if results:
            st.caption(f"Encontrados: {len(results)} documento(s)")
            
            for doc_id, name, user_id, is_global, processed, chunks in results:
                permission_badge = "🌍" if is_global else "🔒"
                status_icon = "✅" if processed else "⏳"
                st.caption(f"{status_icon} {permission_badge} {name} - {user_id} ({chunks} chunks)")
        else:
            st.info("Nenhum documento encontrado")


if __name__ == "__main__":
    # Para testar standalone
    render_document_permissions_panel()
