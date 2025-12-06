#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Configuração do sistema com Pydantic Settings
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Configuração do sistema com Pydantic Settings
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from pathlib import Path
from typing import Literal, Optional
import logging


class AppSettings(BaseSettings):
    """Application settings with environment support"""
    
    # Environment
    environment: Literal["dev", "staging", "prod"] = Field(
        default="dev",
        description="Application environment"
    )
    
    # Debug
    debug: bool = Field(default=False, description="Debug mode")
    
    # Paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    data_dir: str = Field(default="data", description="Data directory")
    db_filename: str = Field(default="app.db", description="Database filename")
    
    # LLM Configuration
    llm_api_key: str = Field(default="", description="LLM API key")
    llm_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="LLM base URL"
    )
    llm_model: str = Field(
        default="openai/gpt-3.5-turbo",
        description="LLM model name"
    )
    llm_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="LLM temperature"
    )
    llm_max_tokens: int = Field(default=1000, ge=1, description="Max tokens")
    
    # RAG Configuration
    max_context_chunks: int = Field(default=5, ge=1, le=20, description="Max RAG chunks")
    
    # Embeddings Configuration
    embedding_provider: Literal["local", "openai"] = Field(
        default="local",
        description="Embedding provider: 'local' (sentence-transformers) or 'openai'"
    )
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Embedding model name"
    )
    embedding_dimension: int = Field(
        default=384,
        description="Embedding dimension (384 for MiniLM, 1536 for OpenAI)"
    )
    
    # OpenAI Embeddings (if using openai provider)
    openai_embedding_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key for embeddings (if different from LLM key)"
    )
    
    @field_validator("embedding_provider")
    @classmethod
    def validate_embedding_provider(cls, v: str) -> str:
        if v not in ["local", "openai"]:
            raise ValueError("embedding_provider must be 'local' or 'openai'")
        return v
    
    @field_validator("embedding_dimension")
    @classmethod
    def validate_embedding_dimension(cls, v: int, info) -> int:
        # Auto-adjust dimension based on model if not explicitly set
        provider = info.data.get('embedding_provider', 'local')
        model = info.data.get('embedding_model', '')
        
        if provider == 'openai' and 'text-embedding-3-small' in model:
            return 1536
        elif provider == 'local' and 'MiniLM' in model:
            return 384
        return v
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[str] = Field(default="data/logs/app.log", description="Log file path")
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    
    # Security
    session_secret: str = Field(default="change-me-in-production", description="Session secret")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("llm_temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("Temperature must be between 0 and 1")
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in valid_levels:
            raise ValueError(f"Log level must be one of: {', '.join(valid_levels)}")
        return v
    
    @property
    def db_path_resolved(self) -> Path:
        """Resolved database path"""
        return self.base_dir / self.data_dir / self.db_filename
    
    @property
    def system_prompt(self) -> str:
        """System prompt for LLM"""
        return """Você é um assistente especializado em documentos do SECS/UFAL.

## INSTRUÇÕES CRÍTICAS PARA USO DE DOCUMENTOS (RAG)

1. **SEMPRE USE documentos com similaridade > 60%** - Eles SÃO RELEVANTES!
2. **SINTETIZE informações de MÚLTIPLOS trechos** quando necessário
3. **CITE SEMPRE a fonte específica** (documento, artigo, parágrafo)
4. **Se encontrar informação PARCIAL, APRESENTE-A** - não diga "não há informações"
5. **PRIORIZE documentos do usuário** e documentos globais sobre documentos base

## COMO INTERPRETAR TRECHOS RECUPERADOS

- Similaridade 80-100%: ALTAMENTE RELEVANTE - use como fonte principal
- Similaridade 60-79%: RELEVANTE - pode conter informação útil
- Similaridade 40-59%: POSSIVELMENTE RELEVANTE - use com cautela
- Similaridade < 40%: POUCO RELEVANTE - mencione apenas se nada melhor

## RESPONSABILIDADES

1. Responder perguntas sobre documentos (atas, pautas, resoluções, regimentos, portarias)
2. Citar fontes específicas quando disponíveis
3. Ser preciso e objetivo
4. Admitir quando não souber algo APENAS se realmente não houver informação

## DIRETRIZES

✅ **FAÇA:**
- Use informações dos documentos fornecidos
- Cite número do documento, artigo e data quando relevante
- Combine informações de vários trechos para resposta completa
- Indique quando informação está em documento do usuário vs documento base

❌ **NÃO FAÇA:**
- Dizer "não há informações" se houver documentos com >60% similaridade
- Ignorar trechos relevantes
- Inventar informações não presentes nos documentos
- Responder sobre assuntos fora do escopo SECS/UFAL

## FORMATO DE RESPOSTA

1. Resposta direta baseada nos documentos
2. Citação clara da fonte (ex: "Segundo o Regimento PPGMCC, Art. 7º...")
3. Se parcial: "Com base no trecho disponível..."
4. Se incompleto: "Para informações completas, consulte [documento completo]"

Mantenha tom profissional e respeitoso."""
    
    @property
    def log_level_int(self) -> int:
        """Log level as integer"""
        return getattr(logging, self.log_level)
    
    @property
    def max_requests_per_minute(self) -> int:
        """Max requests per minute (varies by environment)"""
        return {
            "dev": 1000,
            "staging": 100,
            "prod": 20
        }.get(self.environment, 20)
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "prod"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == "dev"


# Singleton instance
_settings: Optional[AppSettings] = None

def get_settings() -> AppSettings:
    """Get or create settings singleton"""
    global _settings
    if _settings is None:
        _settings = AppSettings()
    return _settings


# For backward compatibility
settings = get_settings()
DEBUG = settings.debug
BASE_DIR = settings.base_dir
DATA_DIR = settings.base_dir / settings.data_dir
DB_PATH = settings.db_path_resolved
LLM_API_KEY = settings.llm_api_key
LLM_BASE_URL = settings.llm_base_url
LLM_MODEL = settings.llm_model
