#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Sistema de logging estruturado
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Sistema de logging estruturado
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class StructuredLogger:
    """Structured logger with file and console output"""
    
    def __init__(
        self,
        name: str,
        level: int = logging.INFO,
        log_file: Optional[str] = None
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Evitar duplicação de handlers
        if self.logger.handlers:
            return
        
        # Formato estruturado
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (opcional)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        msg = f"{message} | {extra_info}" if extra_info else message
        self.logger.debug(msg)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        msg = f"{message} | {extra_info}" if extra_info else message
        self.logger.info(msg)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        msg = f"{message} | {extra_info}" if extra_info else message
        self.logger.warning(msg)
    
    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log error message"""
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        msg = f"{message} | {extra_info}" if extra_info else message
        self.logger.error(msg, exc_info=exc_info)
    
    def critical(self, message: str, exc_info: bool = True, **kwargs):
        """Log critical message"""
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        msg = f"{message} | {extra_info}" if extra_info else message
        self.logger.critical(msg, exc_info=exc_info)


def get_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> StructuredLogger:
    """
    Get or create a structured logger.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level
        log_file: Optional log file path
        
    Returns:
        StructuredLogger instance
        
    Example:
        logger = get_logger(__name__)
        logger.info("Processing request", user_id="123", action="chat")
    """
    return StructuredLogger(name, level, log_file)


# Default application logger
app_logger = get_logger("secs_chatbot", log_file="data/logs/app.log")
