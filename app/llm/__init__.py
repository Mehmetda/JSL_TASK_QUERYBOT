"""
LLM module for OpenAI and Ollama integration
"""
from .llm_manager import LLMManager, get_llm_manager
from .ollama_client import OllamaClient, get_ollama_client, test_ollama_connection

# Backward-compat exports used by some tests
def get_local_llm_client():  # pragma: no cover
    return get_ollama_client()

def initialize_llm():  # pragma: no cover
    return get_llm_manager()

__all__ = [
    'LLMManager', 'get_llm_manager',
    'OllamaClient', 'get_ollama_client', 'test_ollama_connection',
    'get_local_llm_client', 'initialize_llm'
]
