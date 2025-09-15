"""
Configuration file for the application
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LLM Configuration
# Primary LLM (OpenAI)
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Fallback LLM (Ollama)
# Default set to TinyLlama for lightweight local runs
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "tinyllama")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Default Language
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")

# Embedding Model
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Database Configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", "app/db/demo.sqlite")

# Available Models Configuration
AVAILABLE_MODELS = {
    # OpenAI Models
    "openai": {
        "gpt-3.5-turbo": "GPT-3.5 Turbo (Fast, Cost-effective)",
        "gpt-4": "GPT-4 (High quality, More expensive)",
        "gpt-4-turbo": "GPT-4 Turbo (Latest, Best performance)"
    },
    # Ollama Models
    "ollama": {
        "tinyllama": "TinyLlama (Fast, Lightweight)",
        "gemma3:4b": "Gemma3 4B (Balanced performance)",
        "gemma3:12b": "Gemma3 12B (High quality)",
        "llama3:8b": "Llama3 8B (Good balance)",
        "llama3:70b": "Llama3 70B (Best quality)"
    }
}

def get_openai_model():
    """Get the configured OpenAI model name"""
    return OPENAI_MODEL

def get_ollama_model():
    """Get the configured Ollama model name"""
    return OLLAMA_MODEL

def get_embedding_model():
    """Get the configured embedding model name"""
    return EMBEDDING_MODEL

def get_ollama_base_url():
    """Get the Ollama base URL"""
    return OLLAMA_BASE_URL

def is_openai_configured():
    """Check if OpenAI is properly configured"""
    return OPENAI_API_KEY is not None and OPENAI_API_KEY.strip() != ""

def get_available_models():
    """Get available models configuration"""
    return AVAILABLE_MODELS
