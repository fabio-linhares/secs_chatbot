#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Wizard de Primeiro Usuário
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Wizard para criar primeiro usuário administrador
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import streamlit as st
from services.user_service import get_user_service


def first_user_wizard() -> bool:
    """
    Wizard para criar o primeiro usuário (admin).
    
    Exibido apenas quando não há usuários no sistema.
    
    Returns:
        True se usuário foi criado com sucesso
    """
    st.title("🎉 Bem-vindo ao SECS Chatbot!")
    st.markdown("---")
    
    st.info("""
    ### 👋 Primeira Configuração
    
    Parece que esta é a primeira vez que você usa o sistema.
    Vamos criar sua conta de administrador!
    """)
    
    st.markdown("### 🔐 Criar Conta de Administrador")
    
    with st.form("first_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input(
                "Nome de usuário *",
                placeholder="admin",
                help="Escolha um nome de usuário único"
            )
        
        with col2:
            password = st.text_input(
                "Senha *",
                type="password",
                help="Mínimo 6 caracteres"
            )
            
            password_confirm = st.text_input(
                "Confirmar senha *",
                type="password"
            )
        
        st.markdown("---")
        
        col_info, col_submit = st.columns([3, 1])
        
        with col_info:
            st.caption("⚠️ Esta conta terá privilégios de administrador")
            st.caption("✅ Você poderá criar outros usuários depois")
        
        with col_submit:
            submitted = st.form_submit_button(
                "🚀 Criar Conta",
                type="primary",
                use_container_width=True
            )
    
    if submitted:
        # Validações
        errors = []
        
        if not username or len(username) < 3:
            errors.append("Nome de usuário deve ter pelo menos 3 caracteres")
        
        if not password or len(password) < 6:
            errors.append("Senha deve ter pelo menos 6 caracteres")
        
        if password != password_confirm:
            errors.append("Senhas não coincidem")
        
        if errors:
            for error in errors:
                st.error(f"❌ {error}")
            return False
        
        # Criar usuário
        try:
            user_service = get_user_service()
            user_service.create_user(
                username=username,
                password=password,
                role="admin"
            )
            
            st.success(f"""
            ✅ **Conta criada com sucesso!**
            
            - Usuário: {username}
            - Role: Administrador
            
            Agora você pode fazer login com suas credenciais.
            """)
            
            st.balloons()
            
            # Aguardar um pouco antes de recarregar
            import time
            time.sleep(2)
            st.rerun()
            
            return True
            
        except Exception as e:
            st.error(f"❌ Erro ao criar usuário: {e}")
            return False
    
    return False


def check_first_user() -> bool:
    """
    Verifica se existe pelo menos um usuário no sistema.
    
    Returns:
        True se há usuários, False se não há
    """
    try:
        user_service = get_user_service()
        users = user_service.list_users()
        return len(users) > 0
    except:
        return False
