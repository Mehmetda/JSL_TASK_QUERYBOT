"""
LLM Manager for handling OpenAI and Local LLM switching
"""
import os
import logging
from typing import Dict, Any, List
from app.llm import get_local_llm_client
from app.utils import check_internet_connection, check_openai_availability

logger = logging.getLogger(__name__)

class LLMManager:
    """Manages LLM selection and automatic fallback"""
    
    def __init__(self):
        self.current_mode = "auto"  # "openai", "local", "auto"
        self.local_client = None
        self.openai_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize both clients"""
        try:
            # Initialize local client
            self.local_client = get_local_llm_client()
            logger.info("Local LLM client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize local LLM: {e}")
            self.local_client = None
        
        try:
            # Initialize OpenAI client
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
                logger.info("OpenAI client initialized")
            else:
                logger.warning("No OpenAI API key found")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.openai_client = None
        
    
    def set_mode(self, mode: str):
        """Set LLM mode: 'openai', 'local', or 'auto'"""
        self.current_mode = mode
        logger.info(f"LLM mode set to: {mode}")
    
    def get_available_modes(self) -> List[str]:
        """Get list of available LLM modes"""
        modes = []
        if self.openai_client:
            modes.append("openai")
        if self.local_client:
            modes.append("local")
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
            if check_internet_connection() and check_openai_availability():
                return "openai"
            # Fallback to local
            else:
                return "local"
        else:
            return self.current_mode
    
    def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Generate response using the appropriate LLM"""
        effective_mode = self.get_effective_mode()
        
        if effective_mode == "openai" and self.openai_client:
            return self._generate_with_openai(messages, **kwargs)
        elif effective_mode == "local" and self.local_client:
            return self._generate_with_local(messages, **kwargs)
        else:
            # Fallback to available client
            if self.openai_client:
                return self._generate_with_openai(messages, **kwargs)
            elif self.local_client:
                return self._generate_with_local(messages, **kwargs)
            else:
                raise RuntimeError("No LLM client available")
    
    def _generate_with_openai(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Generate response using OpenAI"""
        try:
            response = self.openai_client.chat.completions.create(
                model=kwargs.get("model", "gpt-3.5-turbo"),
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
                "model_used": "openai"
            }
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise e
    
    def _generate_with_local(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Generate response using local LLM"""
        try:
            response = self.local_client.generate_response(
                messages=messages,
                max_tokens=kwargs.get("max_tokens", 300),
                temperature=kwargs.get("temperature", 0.1)
            )
            
            return {
                "content": response["content"],
                "usage": response["usage"],
                "model_used": "local"
            }
        except Exception as e:
            logger.error(f"Local LLM generation failed: {e}")
            raise e
    
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of all LLM clients"""
        return {
            "current_mode": self.current_mode,
            "effective_mode": self.get_effective_mode(),
            "openai_available": self.openai_client is not None,
            "local_available": self.local_client is not None,
            "internet_available": check_internet_connection(),
            "openai_accessible": check_openai_availability() if self.openai_client else False
        }

# Global manager instance
_llm_manager = None

def get_llm_manager() -> LLMManager:
    """Get the global LLM manager instance"""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager
