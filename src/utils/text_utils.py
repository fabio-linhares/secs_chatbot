#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Utilitários para processamento de texto
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Utilitários para processamento de texto
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import re
import unicodedata
from typing import List


def normalize_question(text: str) -> str:
    """
    Normalize question for comparison and caching.
    
    - Removes extra spaces
    - Converts to lowercase
    - Removes trailing punctuation
    - Removes accents/diacritics
    
    Args:
        text: Input text
        
    Returns:
        Normalized text
        
    Example:
        >>> normalize_question("Qual é a PAUTA??")
        "qual e a pauta"
    """
    # Remove accents
    nfkd = unicodedata.normalize('NFKD', text)
    text_no_accents = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    
    # Lowercase and strip
    cleaned = text_no_accents.strip().lower()
    
    # Normalize spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Remove trailing punctuation
    cleaned = cleaned.rstrip('?.!;:,')
    
    return cleaned


def extract_dates(text: str) -> List[str]:
    """
    Extract dates from text.
    
    Supports formats:
    - DD/MM/YYYY
    - MM/YYYY
    
    Args:
        text: Input text
        
    Returns:
        List of date strings found
        
    Example:
        >>> extract_dates("Reunião de 15/01/2024 e 02/2024")
        ['15/01/2024', '02/2024']
    """
    dates = []
    
    # DD/MM/YYYY
    dates.extend(re.findall(r'\b\d{2}/\d{2}/\d{4}\b', text))
    
    # MM/YYYY
    dates.extend(re.findall(r'\b\d{2}/\d{4}\b', text))
    
    return dates


def extract_numbers(text: str, min_digits: int = 3, max_digits: int = 4) -> List[str]:
    """
    Extract numbers from text.
    
    Args:
        text: Input text
        min_digits: Minimum number of digits
        max_digits: Maximum number of digits
        
    Returns:
        List of number strings found
        
    Example:
        >>> extract_numbers("Resolução 123 e portaria 4567")
        ['123', '4567']
    """
    pattern = rf'\b\d{{{min_digits},{max_digits}}}\b'
    return re.findall(pattern, text)


def clean_whitespace(text: str) -> str:
    """
    Clean excessive whitespace from text.
    
    Args:
        text: Input text
        
    Returns:
        Text with normalized whitespace
    """
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    
    # Replace multiple newlines with double newline
    text = re.sub(r'\n\n+', '\n\n', text)
    
    return text.strip()


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
        
    Example:
        >>> truncate_text("Very long text here", max_length=10)
        "Very lo..."
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def is_question(text: str) -> bool:
    """
    Check if text is a question.
    
    Args:
        text: Input text
        
    Returns:
        True if text appears to be a question
    """
    text_lower = text.lower().strip()
    
    # Ends with question mark
    if text.endswith('?'):
        return True
    
    # Starts with question words
    question_words = [
        'qual', 'quais', 'quando', 'onde', 'como', 'por que', 'porque',
        'quem', 'quanto', 'quantos', 'quantas', 'o que', 'que'
    ]
    
    return any(text_lower.startswith(word) for word in question_words)


def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """
    Extract potential keywords from text.
    
    Args:
        text: Input text
        min_length: Minimum keyword length
        
    Returns:
        List of keywords
    """
    # Remove punctuation and split
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Filter by length and remove common stopwords
    stopwords = {
        'o', 'a', 'os', 'as', 'um', 'uma', 'de', 'da', 'do', 'das', 'dos',
        'em', 'no', 'na', 'nos', 'nas', 'para', 'por', 'com', 'sem',
        'e', 'ou', 'mas', 'que', 'se', 'é', 'foi', 'ser', 'está'
    }
    
    keywords = [
        word for word in words
        if len(word) >= min_length and word not in stopwords
    ]
    
    return list(set(keywords))
