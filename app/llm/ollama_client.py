"""
Ollama Client for local LLM integration

This module provides a client for interacting with Ollama models locally.
It supports various models including TinyLlama, Gemma3, and other Ollama-compatible models.
"""
import requests
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Client for interacting with Ollama models
    
    This client provides a simple interface to communicate with Ollama's API
    and generate responses using local models.
    """
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "tinyllama"):
        """
        Initialize Ollama client
        
        Args:
            base_url: Ollama server URL (default: http://localhost:11434)
            model: Model name to use (default: tinyllama)
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.session = requests.Session()
        self.session.timeout = 30  # 30 second timeout
        
    def is_available(self) -> bool:
        """
        Check if Ollama server is available
        
        Returns:
            True if Ollama server is running, False otherwise
        """
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Ollama server not available: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available models
        
        Returns:
            List of available model names
        """
        try:
            response = self.session.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            return []
    
    def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int = 300, 
        temperature: float = 0.1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate response using Ollama model
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with response content and usage info
        """
        try:
            # Convert messages to prompt format
            prompt = self._format_messages(messages)
            
            # Prepare request payload
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                    "top_p": kwargs.get("top_p", 0.9),
                    "top_k": kwargs.get("top_k", 40),
                    "repeat_penalty": kwargs.get("repeat_penalty", 1.1),
                }
            }
            
            # Make request to Ollama
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
            
            data = response.json()
            
            # Extract response
            content = data.get("response", "").strip()
            
            # Calculate approximate token usage
            prompt_tokens = len(prompt.split())  # Rough estimation
            completion_tokens = len(content.split())  # Rough estimation
            
            return {
                "content": content,
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens
                },
                "model_used": f"ollama:{self.model}",
                "ollama_response": data
            }
            
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise e
    
    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """
        Format messages for Ollama model
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Formatted prompt string
        """
        formatted_prompt = ""
        
        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")
            
            if role == "system":
                formatted_prompt += f"System: {content}\n\n"
            elif role == "user":
                formatted_prompt += f"User: {content}\n\n"
            elif role == "assistant":
                formatted_prompt += f"Assistant: {content}\n\n"
        
        formatted_prompt += "Assistant:"
        return formatted_prompt
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Ollama server
        
        Returns:
            Dictionary with connection status and available models
        """
        try:
            is_available = self.is_available()
            models = self.get_available_models() if is_available else []
            
            return {
                "available": is_available,
                "base_url": self.base_url,
                "current_model": self.model,
                "available_models": models,
                "model_in_use": self.model in models if models else False
            }
        except Exception as e:
            return {
                "available": False,
                "error": str(e),
                "base_url": self.base_url,
                "current_model": self.model
            }


# Global Ollama client instance
_ollama_client = None

def get_ollama_client(model: str = "tinyllama") -> OllamaClient:
    """
    Get or create the global Ollama client instance
    
    Args:
        model: Model name to use
        
    Returns:
        OllamaClient instance
    """
    global _ollama_client
    if _ollama_client is None or _ollama_client.model != model:
        _ollama_client = OllamaClient(model=model)
    return _ollama_client

def test_ollama_connection(model: str = "tinyllama") -> Dict[str, Any]:
    """
    Test Ollama connection with specific model
    
    Args:
        model: Model name to test
        
    Returns:
        Connection test results
    """
    client = get_ollama_client(model)
    return client.test_connection()
