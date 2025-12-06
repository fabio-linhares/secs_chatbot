#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Painel de autenticação Streamlit
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Painel de autenticação Streamlit
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import streamlit as st
from src.services.user_service import UserService


def auth_panel(user_service: UserService) -> bool:
    """
    Render authentication panel in sidebar.
    
    Args:
        user_service: UserService instance
        
    Returns:
        True if user is authenticated, False otherwise
    """
    # Initialize session state
    if "user_id" not in st.session_state:
        st.session_state.user_id = "anon"
    if "role" not in st.session_state:
        st.session_state.role = "publico"
    if "is_authenticated" not in st.session_state:
        st.session_state.is_authenticated = False
    
    with st.sidebar:
        st.markdown("---")
        
        if not st.session_state.is_authenticated:
            # Login form
            st.subheader("🔐 Login")
            
            username = st.text_input("Usuário", key="login_username")
            password = st.text_input("Senha", type="password", key="login_password")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Entrar", type="primary", use_container_width=True):
                    if username and password:
                        user = user_service.authenticate(username, password)
                        if user:
                            st.session_state.user_id = user.username
                            st.session_state.role = user.role
                            st.session_state.is_authenticated = True
                            st.success(f"Bem-vindo, {user.username}!")
                            st.rerun()
                        else:
                            st.error("Credenciais inválidas")
                    else:
                        st.warning("Preencha usuário e senha")
            
            # Registration form
            with st.expander("📝 Criar Conta"):
                new_username = st.text_input("Novo usuário", key="reg_username")
                new_password = st.text_input("Senha", type="password", key="reg_password")
                new_role = st.selectbox(
                    "Perfil",
                    ["publico", "secs", "admin"],
                    index=0,
                    key="reg_role",
                    help="publico: acesso básico | secs: acesso SECS | admin: acesso total"
                )
                
                if st.button("Cadastrar", use_container_width=True):
                    if new_username and new_password:
                        try:
                            user_service.create_user(new_username, new_password, new_role)
                            st.success(f"Usuário {new_username} criado! Faça login.")
                        except Exception as e:
                            st.error(str(e))
                    else:
                        st.warning("Preencha todos os campos")
        
        else:
            # Logged in - show user info
            st.success(f"👤 **{st.session_state.user_id}**")
            st.caption(f"Perfil: {st.session_state.role}")
            
            if st.button("🚪 Sair", use_container_width=True):
                st.session_state.user_id = "anon"
                st.session_state.role = "publico"
                st.session_state.is_authenticated = False
                st.rerun()
    
    return st.session_state.is_authenticated
