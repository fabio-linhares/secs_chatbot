#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Modelos Pydantic para validação de inputs
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Modelos Pydantic para validação de inputs
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

from pydantic import BaseModel, Field, validator, field_validator
from typing import Optional, List
import re


class UserPreferenceInput(BaseModel):
    """Validation for user preference input"""
    trigger: str = Field(min_length=1, max_length=100, description="Trigger phrase")
    interpretation: str = Field(min_length=1, max_length=500, description="Interpretation")
    
    @field_validator('trigger')
    @classmethod
    def trigger_must_be_clean(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('Trigger não pode ser vazio')
        if len(v) < 2:
            raise ValueError('Trigger deve ter pelo menos 2 caracteres')
        return v.lower()
    
    @field_validator('interpretation')
    @classmethod
    def interpretation_must_be_clean(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('Interpretação não pode ser vazia')
        return v


class ChatMessageInput(BaseModel):
    """Validation for chat message input"""
    message: str = Field(min_length=1, max_length=2000, description="User message")
    user_id: str = Field(min_length=1, max_length=100, description="User ID")
    
    @field_validator('message')
    @classmethod
    def message_must_be_clean(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('Mensagem não pode ser vazia')
        # Remove caracteres de controle
        v = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', v)
        return v


class DocumentUploadInput(BaseModel):
    """Validation for document upload"""
    filename: str = Field(min_length=1, max_length=255, description="Filename")
    description: Optional[str] = Field(None, max_length=500, description="Description")
    tags: Optional[str] = Field(None, max_length=200, description="Tags")
    file_size_mb: float = Field(gt=0, lt=100, description="File size in MB")
    
    @field_validator('filename')
    @classmethod
    def filename_must_be_valid(cls, v: str) -> str:
        v = v.strip()
        # Remover path traversal
        v = v.replace('..', '').replace('/', '').replace('\\', '')
        
        # Validar extensão
        allowed_extensions = ['.pdf', '.txt', '.docx', '.md']
        if not any(v.lower().endswith(ext) for ext in allowed_extensions):
            raise ValueError(f'Extensão não permitida. Use: {", ".join(allowed_extensions)}')
        
        return v
    
    @field_validator('tags')
    @classmethod
    def tags_must_be_clean(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        # Limitar número de tags
        tags = [t.strip() for t in v.split(',')]
        if len(tags) > 10:
            raise ValueError('Máximo de 10 tags permitidas')
        return ', '.join(tags[:10])


class UserRegistrationInput(BaseModel):
    """Validation for user registration"""
    username: str = Field(min_length=3, max_length=50, description="Username")
    password: str = Field(min_length=8, max_length=100, description="Password")
    role: str = Field(description="User role")
    
    @field_validator('username')
    @classmethod
    def username_must_be_valid(cls, v: str) -> str:
        v = v.strip().lower()
        # Apenas alfanuméricos e underscore
        if not re.match(r'^[a-z0-9_]+$', v):
            raise ValueError('Username deve conter apenas letras, números e underscore')
        return v
    
    @field_validator('password')
    @classmethod
    def password_must_be_strong(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Senha deve ter pelo menos 8 caracteres')
        
        # Verificar complexidade
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('Senha deve conter maiúsculas, minúsculas e números')
        
        return v
    
    @field_validator('role')
    @classmethod
    def role_must_be_valid(cls, v: str) -> str:
        valid_roles = ['publico', 'secs', 'admin']
        if v not in valid_roles:
            raise ValueError(f'Role inválido. Use: {", ".join(valid_roles)}')
        return v


class QuotaUpdateInput(BaseModel):
    """Validation for quota update (admin)"""
    user_id: str = Field(min_length=1, max_length=100)
    max_storage_mb: Optional[int] = Field(None, gt=0, lt=10000)
    max_documents: Optional[int] = Field(None, gt=0, lt=1000)
    
    @field_validator('max_storage_mb')
    @classmethod
    def storage_must_be_reasonable(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v > 5000:
            raise ValueError('Quota de storage muito alta (máximo 5000MB)')
        return v


class SearchQueryInput(BaseModel):
    """Validation for search queries"""
    query: str = Field(min_length=1, max_length=500, description="Search query")
    k: int = Field(default=5, ge=1, le=20, description="Number of results")
    
    @field_validator('query')
    @classmethod
    def query_must_be_clean(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('Query não pode ser vazia')
        # Remove caracteres de controle
        v = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', v)
        return v


# Helper function to validate input
def validate_input(model_class: type[BaseModel], data: dict) -> BaseModel:
    """
    Validate input data against a Pydantic model.
    
    Args:
        model_class: Pydantic model class
        data: Input data dictionary
        
    Returns:
        Validated model instance
        
    Raises:
        ValidationError: If validation fails
        
    Example:
        validated = validate_input(ChatMessageInput, {
            "message": "Hello",
            "user_id": "user123"
        })
    """
    from src.utils.error_handler import ValidationError as CustomValidationError
    from pydantic import ValidationError
    
    try:
        return model_class(**data)
    except ValidationError as e:
        # Convert Pydantic validation error to custom error
        errors = []
        for error in e.errors():
            field = error['loc'][0] if error['loc'] else 'unknown'
            msg = error['msg']
            errors.append(f"{field}: {msg}")
        
        raise CustomValidationError("; ".join(errors))
