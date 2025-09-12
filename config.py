"""
Configuration file for the application
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LLM Configuration
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "microsoft/DialoGPT-medium")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
USE_GPU = os.getenv("USE_GPU", "true").lower() == "true"

# Database Configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", "app/db/demo.sqlite")

# Model paths for different Llama models
LLAMA_MODELS = {
    "llama-2-7b": "meta-llama/Llama-2-7b-chat-hf",
    "llama-2-7b-base": "meta-llama/Llama-2-7b-hf",
    "dialo-gpt-medium": "microsoft/DialoGPT-medium",
    "dialo-gpt-small": "microsoft/DialoGPT-small",
}

def get_model_name():
    """Get the configured model name"""
    return LLM_MODEL_NAME

def get_embedding_model():
    """Get the configured embedding model name"""
    return EMBEDDING_MODEL

def should_use_gpu():
    """Check if GPU should be used"""
    return USE_GPU
