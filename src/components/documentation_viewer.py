#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Visualizador de documentação técnica
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Visualizador de documentação técnica
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import streamlit as st
from pathlib import Path


class DocumentationViewer:
    """Visualizador de documentação técnica do projeto"""
    
    # Documentos disponíveis com metadados
    DOCUMENTS = {
        "ARTIGO_TECNICO.md": {
            "title": "📖 Artigo Técnico",
            "icon": "📖",
            "path": "ARTIGO_TECNICO.md",
            "category": "Técnico"
        },
        "README.md": {
            "title": "📘 README",
            "icon": "📘",
            "path": "README.md",
            "category": "Geral"
        },
        "JUSTIFICATIVA_MODELOS.md": {
            "title": "🎯 Justificativa de Modelos",
            "icon": "🎯",
            "path": "docs/guides/JUSTIFICATIVA_MODELOS.md",
            "category": "Técnico"
        },
        "REQUISITOS_HARDWARE.md": {
            "title": "⚙️ Requisitos de Hardware",
            "icon": "⚙️",
            "path": "REQUISITOS_HARDWARE.md",
            "category": "Técnico"
        },
        "FUNCIONALIDADES_AVANCADAS.md": {
            "title": "🚀 Funcionalidades Avançadas",
            "icon": "🚀",
            "path": "docs/guides/FUNCIONALIDADES_AVANCADAS.md",
            "category": "Features"
        },
        "GUIA_DE_USO.md": {
            "title": "📚 Guia de Uso",
            "icon": "📚",
            "path": "GUIA_DE_USO.md",
            "category": "Guias"
        },
        "COMO_ADICIONAR_PDFS.md": {
            "title": "📄 Como Adicionar PDFs",
            "icon": "📄",
            "path": "COMO_ADICIONAR_PDFS.md",
            "category": "Guias"
        },
        "MCP_SERVER.md": {
            "title": "🔌 MCP Server",
            "icon": "🔌",
            "path": "MCP_SERVER.md",
            "category": "Técnico"
        },
        "requirements.txt": {
            "title": "📦 Dependências",
            "icon": "📦",
            "path": "requirements.txt",
            "category": "Técnico"
        },
        "LICENSE": {
            "title": "⚖️ Licença",
            "icon": "⚖️",
            "path": "LICENSE",
            "category": "Legal"
        },
        "MIGRACAO_AUTOMATICA.md": {
            "title": "🔄 Migração de Embeddings",
            "icon": "🔄",
            "path": "MIGRACAO_AUTOMATICA.md",
            "category": "Técnico"
        },
        "CONFIGURACAO_EMBEDDINGS.md": {
            "title": "🔢 Configuração de Embeddings",
            "icon": "🔢",
            "path": "CONFIGURACAO_EMBEDDINGS.md",
            "category": "Guias"
        },
    }
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
    
    def load_document(self, doc_key: str) -> str:
        """Carrega conteúdo de um documento"""
        try:
            doc = self.DOCUMENTS[doc_key]
            file_path = self.base_path / doc["path"]
            if file_path.exists():
                return file_path.read_text(encoding='utf-8')
            else:
                return f"⚠️ Documento não encontrado: {doc['path']}"
        except Exception as e:
            return f"❌ Erro ao carregar documento: {e}"
    
    def render(self):
        """Renderiza o visualizador de documentação"""
        st.title("📚 Documentação do Projeto")
        st.markdown("Acesse todos os documentos técnicos do SECS Chatbot")
        st.markdown("---")
        
        # Controles no topo
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Filtro por categoria
            categories = ["Todos"] + sorted(set(doc["category"] for doc in self.DOCUMENTS.values()))
            selected_category = st.selectbox(
                "Categoria",
                categories,
                key="doc_category_filter"
            )
        
        with col2:
            # Busca
            search_term = st.text_input(
                "🔍 Buscar nos documentos",
                placeholder="Digite para buscar...",
                key="doc_search"
            )
        
        # Filtrar documentos
        filtered_docs = {
            key: doc for key, doc in self.DOCUMENTS.items()
            if selected_category == "Todos" or doc["category"] == selected_category
        }
        
        # Estatísticas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📄 Documentos", len(filtered_docs))
        with col2:
            st.metric("📁 Categorias", len(set(doc["category"] for doc in filtered_docs.values())))
        with col3:
            total_size = sum(
                self.base_path.joinpath(doc["path"]).stat().st_size 
                for doc in filtered_docs.values() 
                if self.base_path.joinpath(doc["path"]).exists()
            )
            st.metric("💾 Tamanho Total", f"{total_size / 1024:.1f} KB")
        
        st.markdown("---")
        
        # Lista de documentos
        st.markdown("### 📑 Selecione um Documento")
        
        selected_doc = st.selectbox(
            "Selecione um documento",
            options=list(filtered_docs.keys()),
            format_func=lambda x: f"{filtered_docs[x]['icon']} {filtered_docs[x]['title']}",
            key="selected_document",
            label_visibility="collapsed"
        )
        
        if selected_doc:
            st.markdown("---")
            doc = filtered_docs[selected_doc]
            
            # Header do documento
            st.markdown(f"## {doc['icon']} {doc['title']}")
            st.caption(f"📁 `{doc['path']}` | 🏷️ {doc['category']}")
            st.markdown("---")
            
            # Conteúdo
            content = self.load_document(selected_doc)
            
            if doc['path'].endswith('.md'):
                st.markdown(content)
            elif doc['path'] == 'requirements.txt':
                st.code(content, language='text')
            elif doc['path'] == 'LICENSE':
                st.code(content, language='text')
            else:
                st.text(content)


def render_documentation_tab(docs_dir: Path):
    """
    Renderiza aba de documentação completa.
    
    Args:
        docs_dir: Diretório raiz dos documentos
    """
    viewer = DocumentationViewer(docs_dir)
    viewer.render()
