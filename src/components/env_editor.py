#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Editor de Configurações .env
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Interface para editar configurações do arquivo .env
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import streamlit as st
from pathlib import Path
from datetime import datetime
import os
import shutil


class EnvEditor:
    """Editor de configurações do arquivo .env"""
    
    def __init__(self, env_path: Path = None):
        self.env_path = env_path or Path(".env")
        self.env_example_path = Path(".env.example")
    
    def read_env(self) -> dict:
        """Lê arquivo .env e retorna dicionário"""
        env_vars = {}
        
        if self.env_path.exists():
            with open(self.env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        
        return env_vars
    
    def write_env(self, env_vars: dict) -> bool:
        """Escreve dicionário no arquivo .env"""
        try:
            # Backup primeiro
            self.backup_env()
            
            # Escrever novo .env
            with open(self.env_path, 'w') as f:
                f.write("# SECS Chatbot - Configurações\n")
                f.write(f"# Última atualização: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("#\n\n")
                
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
            
            return True
        except Exception as e:
            st.error(f"Erro ao salvar .env: {e}")
            return False
    
    def backup_env(self):
        """Cria backup do .env"""
        if self.env_path.exists():
            backup_dir = Path("data/backups")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f".env.backup_{timestamp}"
            
            shutil.copy2(self.env_path, backup_path)
            return backup_path
    
    def render(self):
        """Renderiza interface de edição"""
        st.subheader("⚙️ Configurações do Sistema")
        st.caption("Edite as variáveis de ambiente do arquivo .env")
        
        # Avisos
        st.warning("""
        ⚠️ **Atenção**:
        - Alterações requerem reiniciar a aplicação
        - Um backup será criado automaticamente
        - Valores inválidos podem quebrar o sistema
        """)
        
        # Ler configurações atuais
        env_vars = self.read_env()
        
        # Tabs por categoria
        tabs = st.tabs([
            "🤖 LLM",
            "🔢 Embeddings",
            "📊 Sistema",
            "🔐 Segurança",
            "📝 Avançado"
        ])
        
        new_env_vars = {}
        
        # Tab 1: LLM
        with tabs[0]:
            st.markdown("### Configurações do LLM")
            
            new_env_vars['LLM_API_KEY'] = st.text_input(
                "API Key",
                value=env_vars.get('LLM_API_KEY', ''),
                type="password",
                help="Chave de API para o LLM (OpenRouter/OpenAI)"
            )
            
            new_env_vars['LLM_BASE_URL'] = st.text_input(
                "Base URL",
                value=env_vars.get('LLM_BASE_URL', 'https://openrouter.ai/api/v1'),
                help="URL base da API"
            )
            
            new_env_vars['LLM_MODEL'] = st.selectbox(
                "Modelo",
                options=[
                    "openai/gpt-3.5-turbo",
                    "openai/gpt-4",
                    "anthropic/claude-3-haiku",
                    "meta-llama/llama-2-70b-chat"
                ],
                index=0 if env_vars.get('LLM_MODEL') == 'openai/gpt-3.5-turbo' else 0
            )
            
            new_env_vars['LLM_TEMPERATURE'] = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=float(env_vars.get('LLM_TEMPERATURE', '0.7')),
                step=0.1,
                help="Criatividade do modelo (0=determinístico, 2=muito criativo)"
            )
        
        # Tab 2: Embeddings
        with tabs[1]:
            st.markdown("### Configurações de Embeddings")
            
            new_env_vars['EMBEDDING_PROVIDER'] = st.radio(
                "Provider",
                options=["local", "openai"],
                index=0 if env_vars.get('EMBEDDING_PROVIDER') == 'local' else 1,
                help="Local (grátis) ou OpenAI (pago, melhor qualidade)"
            )
            
            if new_env_vars['EMBEDDING_PROVIDER'] == 'local':
                new_env_vars['EMBEDDING_MODEL'] = st.text_input(
                    "Modelo",
                    value=env_vars.get('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
                )
                new_env_vars['EMBEDDING_DIMENSION'] = st.number_input(
                    "Dimensão",
                    value=int(env_vars.get('EMBEDDING_DIMENSION', '384')),
                    min_value=128,
                    max_value=2048
                )
            else:
                new_env_vars['EMBEDDING_MODEL'] = 'text-embedding-3-small'
                new_env_vars['EMBEDDING_DIMENSION'] = '1536'
                new_env_vars['OPENAI_EMBEDDING_API_KEY'] = st.text_input(
                    "OpenAI API Key",
                    value=env_vars.get('OPENAI_EMBEDDING_API_KEY', ''),
                    type="password"
                )
        
        # Tab 3: Sistema
        with tabs[2]:
            st.markdown("### Configurações do Sistema")
            
            new_env_vars['APP_ENVIRONMENT'] = st.selectbox(
                "Ambiente",
                options=["dev", "staging", "prod"],
                index=["dev", "staging", "prod"].index(env_vars.get('APP_ENVIRONMENT', 'dev'))
            )
            
            new_env_vars['DEBUG'] = st.checkbox(
                "Modo Debug",
                value=env_vars.get('DEBUG', 'false').lower() == 'true'
            )
            
            new_env_vars['LOG_LEVEL'] = st.selectbox(
                "Nível de Log",
                options=["DEBUG", "INFO", "WARNING", "ERROR"],
                index=["DEBUG", "INFO", "WARNING", "ERROR"].index(env_vars.get('LOG_LEVEL', 'INFO'))
            )
        
        # Tab 4: Segurança
        with tabs[3]:
            st.markdown("### Configurações de Segurança")
            
            new_env_vars['SESSION_SECRET'] = st.text_input(
                "Session Secret",
                value=env_vars.get('SESSION_SECRET', ''),
                type="password",
                help="Chave secreta para sessões (mínimo 32 caracteres)"
            )
            
            if st.button("🔄 Gerar Nova Chave"):
                import secrets
                new_key = secrets.token_hex(32)
                new_env_vars['SESSION_SECRET'] = new_key
                st.success(f"Nova chave gerada: {new_key[:20]}...")
            
            new_env_vars['RATE_LIMIT_ENABLED'] = st.checkbox(
                "Rate Limiting",
                value=env_vars.get('RATE_LIMIT_ENABLED', 'true').lower() == 'true',
                help="Limitar requisições por usuário"
            )
        
        # Tab 5: Avançado
        with tabs[4]:
            st.markdown("### Configurações Avançadas")
            
            new_env_vars['MAX_CONTEXT_CHUNKS'] = st.number_input(
                "Max Context Chunks (RAG)",
                value=int(env_vars.get('MAX_CONTEXT_CHUNKS', '5')),
                min_value=1,
                max_value=20
            )
            
            new_env_vars['DB_FILENAME'] = st.text_input(
                "Nome do Banco de Dados",
                value=env_vars.get('DB_FILENAME', 'app.db')
            )
            
            new_env_vars['DATA_DIR'] = st.text_input(
                "Diretório de Dados",
                value=env_vars.get('DATA_DIR', 'data')
            )
        
        # Botões de ação
        st.markdown("---")
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.caption("💾 Backup será criado automaticamente antes de salvar")
        
        with col2:
            if st.button("🔄 Restaurar Padrões", use_container_width=True):
                st.warning("Funcionalidade em desenvolvimento")
        
        with col3:
            if st.button("💾 Salvar Alterações", type="primary", use_container_width=True):
                # Converter booleanos para string
                for key in ['DEBUG', 'RATE_LIMIT_ENABLED']:
                    if isinstance(new_env_vars.get(key), bool):
                        new_env_vars[key] = str(new_env_vars[key]).lower()
                
                # Converter números para string
                for key in ['LLM_TEMPERATURE', 'MAX_CONTEXT_CHUNKS', 'EMBEDDING_DIMENSION']:
                    if key in new_env_vars:
                        new_env_vars[key] = str(new_env_vars[key])
                
                if self.write_env(new_env_vars):
                    st.success("""
                    ✅ **Configurações salvas com sucesso!**
                    
                    ⚠️ **Ação necessária**: Reinicie a aplicação para aplicar as mudanças.
                    
                    Use o botão "🔄 Reiniciar Aplicação" na seção de controle.
                    """)
                    st.balloons()


def render_env_editor():
    """Renderiza o editor de .env"""
    editor = EnvEditor()
    editor.render()
