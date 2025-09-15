"""
Compatibility shim for tests expecting app.agents.sql_agent_v2
Re-exports get_sql_agent and SQLAgent from sql_agent.py
"""
from typing import Any, Dict, Optional

from .sql_agent import SQLAgent, get_sql_agent, generate_sql_with_agent  # noqa: F401
from app.agents.system_prompt import get_ner_enhanced_hybrid_schema_snippets  # noqa: F401
from app.db.connection import get_connection  # noqa: F401

_sql_agent_instance: Optional[SQLAgent] = None


def get_sql_agent_singleton(config: Optional[Dict[str, Any]] = None) -> SQLAgent:
    global _sql_agent_instance
    if _sql_agent_instance is None:
        _sql_agent_instance = SQLAgent(config)
    return _sql_agent_instance

