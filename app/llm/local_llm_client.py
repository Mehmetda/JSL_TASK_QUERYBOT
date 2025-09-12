"""
Local LLM Client for Llama 7B model
"""
import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from typing import List, Dict, Any, Optional
import logging
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import get_model_name, should_use_gpu

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocalLLMClient:
    """Local LLM client using Llama 7B model"""
    
    def __init__(self, model_name: str = None):
        """
        Initialize the local LLM client
        
        Args:
            model_name: Hugging Face model name for Llama 7B
                       If None, uses the model from config
        """
        self.model_name = model_name or get_model_name()
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        
        # Use GPU if available and configured
        if should_use_gpu() and torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"
            
        logger.info(f"Using device: {self.device}")
        logger.info(f"Model: {self.model_name}")
        
    def load_model(self, model_name: Optional[str] = None):
        """Load the model and tokenizer"""
        if model_name:
            self.model_name = model_name
            
        try:
            logger.info(f"Loading model: {self.model_name}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            
            # Add padding token if it doesn't exist
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
                trust_remote_code=True
            )
            
            # Create pipeline
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            )
            
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            # Fallback to a smaller model
            self._load_fallback_model()
    
    def _load_fallback_model(self):
        """Load a fallback model if the main model fails"""
        try:
            logger.info("Loading fallback model...")
            self.model_name = "microsoft/DialoGPT-small"
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1
            )
            logger.info("Fallback model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading fallback model: {e}")
            raise e
    
    def generate_response(self, messages: List[Dict[str, str]], max_tokens: int = 300, temperature: float = 0.1) -> Dict[str, Any]:
        """
        Generate response using the local model
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Dictionary with response content and usage info
        """
        if not self.pipeline:
            self.load_model()
        
        try:
            # Format messages for the model
            prompt = self._format_messages(messages)
            
            # Generate response
            response = self.pipeline(
                prompt,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                return_full_text=False
            )
            
            # Extract response text
            response_text = response[0]['generated_text'].strip()
            
            # Calculate token usage (approximate)
            input_tokens = len(self.tokenizer.encode(prompt))
            output_tokens = len(self.tokenizer.encode(response_text))
            
            return {
                "content": response_text,
                "usage": {
                    "prompt_tokens": input_tokens,
                    "completion_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "content": f"Error generating response: {str(e)}",
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }
    
    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """Format messages for the model"""
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
    
    def chat_completions_create(self, model: str, messages: List[Dict[str, str]], max_tokens: int = 300, temperature: float = 0.1) -> Dict[str, Any]:
        """
        OpenAI-compatible interface for chat completions
        
        Args:
            model: Model name (ignored, uses loaded model)
            messages: List of message dictionaries
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            OpenAI-compatible response format
        """
        response = self.generate_response(messages, max_tokens, temperature)
        
        return {
            "choices": [{
                "message": {
                    "content": response["content"],
                    "role": "assistant"
                }
            }],
            "usage": response["usage"]
        }

# Global client instance
_client = None

def get_local_llm_client() -> LocalLLMClient:
    """Get or create the global LLM client instance"""
    global _client
    if _client is None:
        _client = LocalLLMClient()
    return _client

def initialize_llm(model_name: str = "microsoft/DialoGPT-medium"):
    """Initialize the LLM with a specific model"""
    global _client
    _client = LocalLLMClient(model_name)
    _client.load_model()
    return _client
