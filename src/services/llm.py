#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Serviço de integração com LLM (OpenAI/OpenRouter)
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Serviço de integração com LLM (OpenAI/OpenRouter)
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

from openai import OpenAI
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings

class LLMService:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url
        )
        self.model = settings.llm_model

    def get_response(self, messages):
        """
        Get response from LLM.
        messages: list of dicts [{'role': 'user', 'content': '...'}, ...]
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                stream=True # Enable streaming for better UX
            )
            return response
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return None

llm_service = LLMService()
