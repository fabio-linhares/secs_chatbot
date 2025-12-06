#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Controle de taxa de requisições
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Controle de taxa de requisições
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Tuple
from dataclasses import dataclass
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    max_requests: int
    window_seconds: int
    
    def __str__(self) -> str:
        return f"{self.max_requests} requests per {self.window_seconds}s"


class RateLimiter:
    """Rate limiter with sliding window"""
    
    # Default configs by role
    DEFAULT_CONFIGS = {
        'publico': RateLimitConfig(max_requests=20, window_seconds=60),
        'secs': RateLimitConfig(max_requests=50, window_seconds=60),
        'admin': RateLimitConfig(max_requests=100, window_seconds=60),
    }
    
    def __init__(self, configs: Dict[str, RateLimitConfig] = None):
        self.configs = configs or self.DEFAULT_CONFIGS
        self.requests: Dict[str, List[datetime]] = defaultdict(list)
    
    def is_allowed(self, user_id: str, role: str = 'publico') -> Tuple[bool, str]:
        """
        Check if request is allowed for user.
        
        Args:
            user_id: User identifier
            role: User role
            
        Returns:
            (allowed, message) tuple
            
        Example:
            allowed, msg = rate_limiter.is_allowed("user123", "publico")
            if not allowed:
                return error_response(msg)
        """
        config = self.configs.get(role, self.DEFAULT_CONFIGS['publico'])
        now = datetime.now()
        window_start = now - timedelta(seconds=config.window_seconds)
        
        # Limpar requisições antigas
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if req_time > window_start
        ]
        
        # Verificar limite
        current_count = len(self.requests[user_id])
        
        if current_count >= config.max_requests:
            remaining_time = int(
                (self.requests[user_id][0] - window_start).total_seconds()
            )
            
            logger.warning(
                "Rate limit exceeded",
                user_id=user_id,
                role=role,
                count=current_count,
                limit=config.max_requests
            )
            
            return False, (
                f"Limite de {config.max_requests} requisições por "
                f"{config.window_seconds}s atingido. "
                f"Tente novamente em {remaining_time}s."
            )
        
        # Adicionar requisição
        self.requests[user_id].append(now)
        
        logger.debug(
            "Rate limit check passed",
            user_id=user_id,
            role=role,
            count=current_count + 1,
            limit=config.max_requests
        )
        
        return True, "OK"
    
    def get_usage(self, user_id: str, role: str = 'publico') -> Dict[str, int]:
        """
        Get current usage for user.
        
        Returns:
            Dictionary with current, limit, and remaining
        """
        config = self.configs.get(role, self.DEFAULT_CONFIGS['publico'])
        now = datetime.now()
        window_start = now - timedelta(seconds=config.window_seconds)
        
        # Limpar requisições antigas
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if req_time > window_start
        ]
        
        current = len(self.requests[user_id])
        
        return {
            'current': current,
            'limit': config.max_requests,
            'remaining': max(0, config.max_requests - current),
            'window_seconds': config.window_seconds
        }
    
    def reset(self, user_id: str):
        """Reset rate limit for user (admin only)"""
        if user_id in self.requests:
            del self.requests[user_id]
            logger.info("Rate limit reset", user_id=user_id)


# Global rate limiter instance
_rate_limiter = None

def get_rate_limiter() -> RateLimiter:
    """Get or create rate limiter singleton"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
