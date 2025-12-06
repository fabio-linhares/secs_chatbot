#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Framework de tratamento de erros
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Framework de tratamento de erros
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

from functools import wraps
from typing import Callable, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)


# Custom Exceptions
class SECSChatbotError(Exception):
    """Base exception for all chatbot errors"""
    pass


class ServiceError(SECSChatbotError):
    """Error in a service operation"""
    pass


class DatabaseError(ServiceError):
    """Database operation error"""
    pass


class ValidationError(SECSChatbotError):
    """Input validation error"""
    pass


class AuthenticationError(SECSChatbotError):
    """Authentication/authorization error"""
    pass


class QuotaExceededError(SECSChatbotError):
    """User quota exceeded"""
    pass


class RateLimitError(SECSChatbotError):
    """Rate limit exceeded"""
    pass


class DocumentProcessingError(ServiceError):
    """Document processing error"""
    pass


# Error Handler Decorator
def handle_errors(
    default_return: Any = None,
    log_errors: bool = True,
    raise_errors: bool = True
):
    """
    Decorator for handling errors in functions.
    
    Args:
        default_return: Value to return on error (if not raising)
        log_errors: Whether to log errors
        raise_errors: Whether to re-raise errors
        
    Example:
        @handle_errors(default_return=[], log_errors=True)
        def get_items():
            # ... code that might fail
            return items
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ValidationError as e:
                if log_errors:
                    logger.warning(
                        f"Validation error in {func.__name__}",
                        error=str(e),
                        args=str(args)[:100]
                    )
                if raise_errors:
                    raise
                return default_return
            
            except (DatabaseError, ServiceError) as e:
                if log_errors:
                    logger.error(
                        f"Service error in {func.__name__}",
                        exc_info=True,
                        error=str(e)
                    )
                if raise_errors:
                    raise
                return default_return
            
            except Exception as e:
                if log_errors:
                    logger.critical(
                        f"Unexpected error in {func.__name__}",
                        exc_info=True,
                        error=str(e),
                        error_type=type(e).__name__
                    )
                if raise_errors:
                    raise ServiceError(f"Erro inesperado: {str(e)}") from e
                return default_return
        
        return wrapper
    return decorator


# Database Error Handler
def handle_db_errors(func: Callable) -> Callable:
    """
    Decorator specifically for database operations.
    
    Example:
        @handle_db_errors
        def get_user(user_id):
            return db.query(...)
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            import sqlite3
            if isinstance(e, sqlite3.Error):
                logger.error(
                    f"Database error in {func.__name__}",
                    exc_info=True,
                    error=str(e)
                )
                raise DatabaseError(f"Erro ao acessar banco de dados: {str(e)}") from e
            raise
    
    return wrapper


# Context Manager for Error Handling
class ErrorContext:
    """
    Context manager for error handling.
    
    Example:
        with ErrorContext("Processing document"):
            process_document(doc)
    """
    def __init__(self, operation: str, raise_errors: bool = True):
        self.operation = operation
        self.raise_errors = raise_errors
    
    def __enter__(self):
        logger.debug(f"Starting: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            logger.debug(f"Completed: {self.operation}")
            return True
        
        logger.error(
            f"Error in {self.operation}",
            exc_info=True,
            error_type=exc_type.__name__,
            error=str(exc_val)
        )
        
        if self.raise_errors:
            return False  # Re-raise exception
        
        return True  # Suppress exception
