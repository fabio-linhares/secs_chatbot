#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Componente de login
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Componente de login
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import streamlit as st
from src.services.auth import get_auth_service

def render_login():
    """Render login form"""
    st.markdown("### 🔐 Login")
    st.markdown("---")
    
    with st.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar", use_container_width=True)
        
        if submit:
            if not username or not password:
                st.error("Por favor, preencha todos os campos")
                return
            
            auth_service = get_auth_service()
            result = auth_service.login(username, password)
            
            if result:
                user, session_token = result
                st.session_state.user = user
                st.session_state.session_token = session_token
                st.success(f"Bem-vindo, {user.full_name}!")
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos")
    
    # Show default credentials
    with st.expander("ℹ️ Credenciais de teste"):
        st.caption("**Admin**: admin / admin123")
        st.caption("**SECS**: secs / secs123")
        st.caption("**Público**: publico / publico123")

def render_user_info(user):
    """Render logged-in user info"""
    role_icons = {
        'admin': '👑',
        'secs': '📋',
        'public': '👤'
    }
    
    role_names = {
        'admin': 'Administrador',
        'secs': 'SECS',
        'public': 'Público'
    }
    
    icon = role_icons.get(user.role, '👤')
    role_name = role_names.get(user.role, user.role)
    
    st.markdown(f"### {icon} {user.full_name}")
    st.caption(f"**Role**: {role_name}")
    st.caption(f"**Usuário**: {user.username}")
    st.markdown("---")
    
    if st.button("🚪 Sair", use_container_width=True):
        auth_service = get_auth_service()
        auth_service.logout(st.session_state.session_token)
        del st.session_state.user
        del st.session_state.session_token
        st.rerun()
