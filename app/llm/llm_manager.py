"""
LLM Manager for handling OpenAI and Ollama LLM switching

This manager provides automatic fallback from OpenAI to Ollama when needed.
OpenAI is used as the primary LLM, with Ollama as fallback for offline scenarios.
"""
import os
import logging
from typing import Dict, Any, List
from app.llm.ollama_client import get_ollama_client, test_ollama_connection
from app.utils import check_internet_connection, check_openai_availability
from config import get_openai_model, get_ollama_model, is_openai_configured

logger = logging.getLogger(__name__)

class LLMManager:
    """Manages LLM selection and automatic fallback between OpenAI and Ollama"""
    
    def __init__(self):
        self.current_mode = "auto"  # "openai", "ollama", "auto"
        self.ollama_client = None
        self.openai_client = None
        self.openai_model = get_openai_model()
        self.ollama_model = get_ollama_model()
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize both OpenAI and Ollama clients"""
        # Initialize OpenAI client
        try:
            if is_openai_configured():
                from openai import OpenAI
                api_key = os.getenv("OPENAI_API_KEY")
                self.openai_client = OpenAI(api_key=api_key)
                logger.info(f"OpenAI client initialized with model: {self.openai_model}")
            else:
                logger.warning("OpenAI API key not configured")
                self.openai_client = None
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.openai_client = None
        
        # Initialize Ollama client
        try:
            self.ollama_client = get_ollama_client(self.ollama_model)
            # Test connection
            connection_test = self.ollama_client.test_connection()
            if connection_test["available"]:
                logger.info(f"Ollama client initialized with model: {self.ollama_model}")
            else:
                logger.warning(f"Ollama server not available: {connection_test.get('error', 'Unknown error')}")
                self.ollama_client = None
        except Exception as e:
            logger.error(f"Failed to initialize Ollama client: {e}")
            self.ollama_client = None
        
    
    def set_mode(self, mode: str):
        """Set LLM mode: 'openai', 'ollama', or 'auto'"""
        if mode not in ["openai", "ollama", "auto"]:
            raise ValueError(f"Invalid mode: {mode}. Must be 'openai', 'ollama', or 'auto'")
        self.current_mode = mode
        logger.info(f"LLM mode set to: {mode}")
    
    def get_available_modes(self) -> List[str]:
        """Get list of available LLM modes"""
        modes = []
        if self.openai_client:
            modes.append("openai")
        if self.ollama_client:
            modes.append("ollama")
        if len(modes) > 1:
            modes.append("auto")
        return modes
    
    def get_current_mode(self) -> str:
        """Get current LLM mode"""
        return self.current_mode
    
    def get_effective_mode(self) -> str:
        """Get the effective mode that will be used for generation"""
        if self.current_mode == "auto":
            # Check internet and OpenAI availability first
            if check_internet_connection() and check_openai_availability() and self.openai_client:
                return "openai"
            # Fallback to Ollama
            elif self.ollama_client:
                return "ollama"
            else:
                # No clients available
                raise RuntimeError("No LLM clients available")
        else:
            return self.current_mode
    
    def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Generate response using the appropriate LLM with automatic fallback"""
        mode = None
        try:
            mode = self.get_effective_mode()
            if mode == "openai" and self.openai_client:
                return self._generate_with_openai(messages, **kwargs)
            if mode == "ollama" and self.ollama_client:
                return self._generate_with_ollama(messages, **kwargs)
            # If we get here, try whichever client exists
            if self.openai_client:
                logger.info("Falling back to OpenAI")
                return self._generate_with_openai(messages, **kwargs)
            if self.ollama_client:
                logger.info("Falling back to Ollama")
                return self._generate_with_ollama(messages, **kwargs)
            raise RuntimeError("No LLM client available")
        except Exception as e:
            logger.error(f"Primary LLM failed: {e}")
            # Try opposite client if available
            if mode == "openai" and self.ollama_client:
                logger.info("OpenAI failed, falling back to Ollama")
                return self._generate_with_ollama(messages, **kwargs)
            if mode == "ollama" and self.openai_client:
                logger.info("Ollama failed, falling back to OpenAI")
                return self._generate_with_openai(messages, **kwargs)
            # Last chance: try any available
            if self.ollama_client:
                try:
                    return self._generate_with_ollama(messages, **kwargs)
                except Exception:
                    pass
            if self.openai_client:
                try:
                    return self._generate_with_openai(messages, **kwargs)
                except Exception:
                    pass
            # Nothing worked
            raise RuntimeError("No LLM clients available")
    
    def _generate_with_openai(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Generate response using OpenAI"""
        try:
            response = self.openai_client.chat.completions.create(
                model=kwargs.get("model", self.openai_model),
                messages=messages,
                max_tokens=kwargs.get("max_tokens", 300),
                temperature=kwargs.get("temperature", 0.1)
            )
            
            return {
                "content": response.choices[0].message.content.strip(),
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                },
                "model_used": f"openai:{self.openai_model}"
            }
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise e
    
    def _generate_with_ollama(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Generate response using Ollama"""
        try:
            response = self.ollama_client.generate_response(
                messages=messages,
                max_tokens=kwargs.get("max_tokens", 300),
                temperature=kwargs.get("temperature", 0.1)
            )
            
            return {
                "content": response["content"],
                "usage": response["usage"],
                "model_used": f"ollama:{self.ollama_model}"
            }
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise e
    
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of all LLM clients"""
        ollama_status = {}
        if self.ollama_client:
            ollama_status = self.ollama_client.test_connection()
        
        return {
            "current_mode": self.current_mode,
            "effective_mode": self.get_effective_mode(),
            "openai_available": self.openai_client is not None,
            "openai_model": self.openai_model,
            "ollama_available": self.ollama_client is not None,
            "ollama_model": self.ollama_model,
            "ollama_status": ollama_status,
            "internet_available": check_internet_connection(),
            "openai_accessible": check_openai_availability() if self.openai_client else False,
            "available_modes": self.get_available_modes()
        }

# Global manager instance
_llm_manager = None

def get_llm_manager() -> LLMManager:
    """Get the global LLM manager instance"""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager
