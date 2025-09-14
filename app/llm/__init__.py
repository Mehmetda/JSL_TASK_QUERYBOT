"""
LLM module for OpenAI and Ollama integration
"""
from .llm_manager import LLMManager, get_llm_manager
from .ollama_client import OllamaClient, get_ollama_client, test_ollama_connection

__all__ = ['LLMManager', 'get_llm_manager', 'OllamaClient', 'get_ollama_client', 'test_ollama_connection']
