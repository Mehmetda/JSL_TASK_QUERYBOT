"""
Simple MCP-style service provider abstraction.

Centralizes access to: DB connection, security manager, retrieval (RAG),
logging and tracing, and LLM manager. This creates a light service layer
so the rest of the app depends on a single provider instead of scattered imports.
"""
from __future__ import annotations

from typing import Optional


class ServiceProvider:
    def __init__(self) -> None:
        # Lazy singletons to avoid heavy imports at module import time
        self._structured_logger = None
        self._trace_manager = None
        self._llm_manager = None

    # Database
    def get_connection(self):
        from app.db.connection import get_connection
        return get_connection()

    # Security
    def get_security_manager(self):
        from app.security.table_allowlist import TableAllowlistManager
        return TableAllowlistManager()

    # RAG / Retrieval helpers
    def get_relevant_schema(self, conn, question: str, top_k: int = 3, metadata_filters: Optional[dict] = None, use_ner_enhanced: bool = True) -> str:
        from app.agents.system_prompt import (
            get_ner_enhanced_hybrid_schema_snippets,
            get_hybrid_relevant_schema_snippets_with_metadata,
            get_relevant_schema_snippets,
        )
        if use_ner_enhanced:
            return get_ner_enhanced_hybrid_schema_snippets(conn, question, top_k)
        elif metadata_filters:
            return get_hybrid_relevant_schema_snippets_with_metadata(conn, question, metadata_filters, top_k)
        return get_relevant_schema_snippets(conn, question, top_k)

    # Logging
    def get_structured_logger(self):
        if self._structured_logger is None:
            from app.utils.logger import get_structured_logger
            self._structured_logger = get_structured_logger()
        return self._structured_logger

    # Tracing
    def get_trace_manager(self):
        if self._trace_manager is None:
            from app.utils.tracing import get_trace_manager
            self._trace_manager = get_trace_manager()
        return self._trace_manager

    # LLM Manager (for UI or agents that need it)
    def get_llm_manager(self):
        if self._llm_manager is None:
            from app.llm.llm_manager import get_llm_manager
            self._llm_manager = get_llm_manager()
        return self._llm_manager


_provider: Optional[ServiceProvider] = None


def get_provider() -> ServiceProvider:
    global _provider
    if _provider is None:
        _provider = ServiceProvider()
    return _provider


