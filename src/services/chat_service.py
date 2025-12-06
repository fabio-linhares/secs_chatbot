#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Orquestrador do pipeline de chat completo
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Orquestrador do pipeline de chat completo
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
from src.utils.advanced_disambiguation import get_disambiguator


@dataclass
class ChatMessage:
    """Chat message model"""
    role: str
    content: str


@dataclass
class ChatResponse:
    """Complete chat response with metadata"""
    message: ChatMessage
    sources: List[str]
    metadata: Dict[str, Any]


class ChatService:
    """Orchestrates the complete chat pipeline"""
    
    def __init__(
        self,
        llm_service,
        vector_store=None,
        cache_service=None,
        audit_logger=None,
        semantic_rewriter=None,
        focal_agent=None,
        count_helper=None,
        prompt_enricher=None,
        clarification_agent=None
    ):
        """
        Initialize chat service with all dependencies.
        
        Args:
            llm_service: LLM service for generation
            vector_store: Vector store for RAG
            cache_service: Cache service
            audit_logger: Audit logger
            semantic_rewriter: Semantic rewriter
            focal_agent: Focal agent
            count_helper: Count helper
            prompt_enricher: Prompt enricher
            clarification_agent: Clarification agent
        """
        self.llm = llm_service
        self.vector_store = vector_store
        self.cache = cache_service
        self.audit = audit_logger
        self.rewriter = semantic_rewriter
        self.agent = focal_agent
        self.counter = count_helper
        self.enricher = prompt_enricher
        self.clarifier = clarification_agent
    
    def answer(
        self,
        user_message: str,
        history: Optional[List[ChatMessage]] = None,
        user_id: str = "anon",
        role: str = "publico"
    ) -> ChatResponse:
        """
        Process user message and generate response.
        
        Complete pipeline:
        1. Check cache (user → global)
        2. Semantic rewriting
        3. Focal agent search
        4. Count helper (derive facts)
        5. Clarification check
        6. Prompt enrichment
        7. LLM generation
        8. Cache storage
        9. Audit logging
        
        Args:
            user_message: User's message
            history: Conversation history
            user_id: User identifier
            role: User role
            
        Returns:
            ChatResponse with message, sources, and metadata
        """
        history = history or []
        metadata = {
            "user_id": user_id,
            "role": role,
            "cache_hit": None,
            "agent_tool": None,
            "num_chunks": 0,
            "num_facts": 0
        }
        
        # 1. Check cache
        if self.cache:
            # Try user cache
            cached = self.cache.get_user_answer(user_id, user_message)
            if cached and not self._is_negative(cached):
                metadata["cache_hit"] = "user"
                self._log_audit(user_id, role, user_message, cached, metadata)
                
                return ChatResponse(
                    message=ChatMessage(role="assistant", content=cached),
                    sources=[],
                    metadata=metadata
                )
            
            # Try global cache
            cached_global = self.cache.get_global_answer(user_message)
            if cached_global and not self._is_negative(cached_global):
                metadata["cache_hit"] = "global"
                self._log_audit(user_id, role, user_message, cached_global, metadata)
                
                return ChatResponse(
                    message=ChatMessage(role="assistant", content=cached_global),
                    sources=[],
                    metadata=metadata
                )
        
        # 2. Semantic rewriting
        enrichment = None
        if self.rewriter:
            enrichment = self.rewriter.enrich(user_message, use_llm=True)
            search_query = enrichment.rewritten
        else:
            search_query = user_message
        
        # 3. Focal agent search
        chunks = []
        agent_tool = None
        
        if self.agent and self.vector_store:
            agent_result = self.agent.run(search_query, k=5)
            chunks = agent_result.chunks
            agent_tool = agent_result.tool
            metadata["agent_tool"] = agent_tool
        elif self.vector_store:
            # Fallback to regular search
            chunks = self.vector_store.search(search_query, k=5)
        
        metadata["num_chunks"] = len(chunks)
        
        # 4. Count helper (derive facts)
        derived_facts = []
        if self.counter and chunks:
            derived_facts = self.counter.derive_counts(user_message, chunks)
            metadata["num_facts"] = len(derived_facts)
        
        # 5. Clarification check
        clarification = None
        if self.clarifier and chunks:
            clarification = self.clarifier.check_clarification(user_message, chunks)
        
        # If needs clarification, return clarification message
        if clarification and clarification.confidence > 0.7:
            clarification_text = f"🤔 {clarification.question}\n\n"
            if clarification.options:
                clarification_text += "**Opções:**\n"
                for opt in clarification.options:
                    clarification_text += f"- {opt}\n"
            clarification_text += "\nPor favor, seja mais específico."
            
            metadata["clarification"] = True
            self._log_audit(user_id, role, user_message, clarification_text, metadata)
            
            return ChatResponse(
                message=ChatMessage(role="assistant", content=clarification_text),
                sources=[],
                metadata=metadata
            )
        
        # 6. Prompt enrichment
        if self.enricher:
            enriched = self.enricher.enrich(
                user_question=user_message,
                chunks=chunks,
                history=history[-10:] if history else [],  # Last 10 messages
                semantic_enrichment=enrichment,
                derived_facts=derived_facts,
                agent_tool=agent_tool
            )
            messages = enriched.messages
        else:
            # Fallback: simple messages
            from src.config import get_settings
            messages = [
                {"role": "system", "content": get_settings().system_prompt},
                {"role": "user", "content": user_message}
            ]
        
        # 7. LLM generation
        response_text = ""
        try:
            stream = self.llm.get_response(messages)
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    response_text += chunk.choices[0].delta.content
        except Exception as e:
            response_text = f"Erro ao gerar resposta: {str(e)}"
            metadata["error"] = str(e)
        
        # 8. Cache storage
        if self.cache and response_text and not self._is_negative(response_text):
            self.cache.set_user_answer(user_id, user_message, response_text)
            self.cache.set_global_answer(user_message, response_text)
        
        # 9. Audit logging
        self._log_audit(user_id, role, user_message, response_text, metadata)
        
        # Build sources
        sources = []
        if chunks:
            sources = [
                f"{c.get('titulo', 'Documento')[:50]} ({c.get('similarity', 0):.1%})"
                for c in chunks[:5]
            ]
        
        # Add enrichment and facts to metadata for UI
        metadata["enrichment"] = enrichment
        metadata["derived_facts"] = derived_facts
        metadata["chunks"] = chunks
        
        return ChatResponse(
            message=ChatMessage(role="assistant", content=response_text),
            sources=sources,
            metadata=metadata
        )
    
    def _is_negative(self, answer: str) -> bool:
        """
        Check if answer is negative/uncertain.
        
        Negative answers should not be cached as they may become
        outdated when new documents are added.
        """
        signals = [
            "não encontrei",
            "nao encontrei",
            "não há base",
            "nao ha base",
            "sem base documental",
            "não tenho certeza",
            "nao tenho certeza",
            "sem informação",
            "sem informacao"
        ]
        
        answer_lower = answer.lower()
        return any(signal in answer_lower for signal in signals)
    
    def _log_audit(
        self,
        user: str,
        role: str,
        input_text: str,
        output_text: str,
        metadata: Dict[str, Any]
    ):
        """Log interaction to audit"""
        if self.audit:
            from src.services.audit import AuditRecord
            self.audit.log(AuditRecord(
                user=user,
                role=role,
                input_text=input_text,
                output_text=output_text,
                metadata=metadata
            ))


# Singleton
_chat_service = None

def get_chat_service(
    llm_service=None,
    vector_store=None,
    cache_service=None,
    audit_logger=None,
    semantic_rewriter=None,
    focal_agent=None,
    count_helper=None,
    prompt_enricher=None,
    clarification_agent=None
) -> ChatService:
    """Get or create chat service singleton"""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService(
            llm_service=llm_service,
            vector_store=vector_store,
            cache_service=cache_service,
            audit_logger=audit_logger,
            semantic_rewriter=semantic_rewriter,
            focal_agent=focal_agent,
            count_helper=count_helper,
            prompt_enricher=prompt_enricher,
            clarification_agent=clarification_agent
        )
    return _chat_service
