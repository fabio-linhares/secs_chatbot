#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Serviço de geração de embeddings (Local + OpenAI)
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Serviço de geração de embeddings com suporte a múltiplos provedores
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import numpy as np
from typing import List, Optional
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings


class EmbeddingService:
    """
    Generates embeddings using configurable providers.
    
    Supports:
    - local: sentence-transformers (default, free)
    - openai: OpenAI API (paid, higher quality)
    
    Provider is configured via .env file.
    """
    
    def __init__(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        """
        Initialize embedding service.
        
        Args:
            provider: 'local' or 'openai' (defaults to settings)
            model_name: Model name (defaults to settings)
        """
        self.provider = provider or settings.embedding_provider
        self.model_name = model_name or settings.embedding_model
        self.dimension = settings.embedding_dimension
        
        print(f"🔢 Initializing embeddings: {self.provider} / {self.model_name}")
        
        if self.provider == "local":
            self._init_local()
        elif self.provider == "openai":
            self._init_openai()
        else:
            raise ValueError(f"Unknown embedding provider: {self.provider}")
        
        print(f"✅ Embedding dimension: {self.dimension}")
    
    def _init_local(self):
        """Initialize sentence-transformers (local)"""
        try:
            from sentence_transformers import SentenceTransformer
            
            self.model = SentenceTransformer(self.model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            
            print(f"✅ Loaded local model: {self.model_name}")
        except Exception as e:
            print(f"❌ Error loading local model: {e}")
            raise
    
    def _init_openai(self):
        """Initialize OpenAI embeddings"""
        try:
            from openai import OpenAI
            
            # Use separate key if provided, otherwise use LLM key
            api_key = settings.openai_embedding_api_key or settings.llm_api_key
            
            if not api_key:
                raise ValueError(
                    "OpenAI embeddings require OPENAI_EMBEDDING_API_KEY or LLM_API_KEY"
                )
            
            # Check if using OpenRouter key
            if api_key.startswith('sk-or-'):
                print("⚠️  Detectada chave OpenRouter - usando base_url do OpenRouter")
                self.client = OpenAI(
                    api_key=api_key,
                    base_url="https://openrouter.ai/api/v1"
                )
            else:
                # Chave OpenAI real
                self.client = OpenAI(api_key=api_key)
            
            # Validate model name
            if "text-embedding" not in self.model_name:
                print(f"⚠️  Warning: Model name should be like 'text-embedding-3-small'")
            
            print(f"✅ Initialized OpenAI embeddings: {self.model_name}")
        except Exception as e:
            print(f"❌ Error initializing OpenAI: {e}")
            raise
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text
            
        Returns:
            Numpy array with embedding
        """
        if self.provider == "local":
            return self.model.encode(text, convert_to_numpy=True)
        
        elif self.provider == "openai":
            response = self.client.embeddings.create(
                model=self.model_name,
                input=text
            )
            # CRITICAL: Convert to float32 to ensure correct byte size
            # float64 would be 8 bytes/dim (12288 bytes for 1536 dims)
            # float32 is 4 bytes/dim (6144 bytes for 1536 dims)
            return np.array(response.data[0].embedding, dtype=np.float32)
    
    def batch_embed(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = True
    ) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts
            batch_size: Batch size for processing
            show_progress: Show progress bar (local only)
            
        Returns:
            List of numpy arrays with embeddings
        """
        if self.provider == "local":
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                batch_size=batch_size,
                show_progress_bar=show_progress
            )
            return [emb for emb in embeddings]
        
        elif self.provider == "openai":
            # OpenAI supports batches up to 2048 texts
            # Batch process
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                response = self.client.embeddings.create(
                    model=self.model_name,
                    input=batch
                )
                
                # CRITICAL: Convert to float32
                batch_embeddings = [
                    np.array(item.embedding, dtype=np.float32)
                    for item in response.data
                ]
                all_embeddings.extend(batch_embeddings)
                
                if show_progress:
                    print(f"Processed {min(i+batch_size, len(texts))}/{len(texts)} texts")
            
            return all_embeddings
    
    def get_info(self) -> dict:
        """Get embedding service information"""
        return {
            'provider': self.provider,
            'model': self.model_name,
            'dimension': self.dimension,
            'cost': 'Free' if self.provider == 'local' else 'Paid (OpenAI)'
        }


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None

def get_embedding_service(
    provider: Optional[str] = None,
    model_name: Optional[str] = None
) -> EmbeddingService:
    """
    Get or create embedding service singleton.
    
    Args:
        provider: Override provider from settings
        model_name: Override model from settings
        
    Returns:
        EmbeddingService instance
    """
    global _embedding_service
    
    if _embedding_service is None:
        _embedding_service = EmbeddingService(provider, model_name)
    
    return _embedding_service


# For backward compatibility
embedding_service = get_embedding_service()
