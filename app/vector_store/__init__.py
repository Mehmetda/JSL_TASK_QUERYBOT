"""
Vector store module for FAISS integration
"""
from .faiss_store import FAISSVectorStore
from .embeddings import EmbeddingService

__all__ = ['FAISSVectorStore', 'EmbeddingService']
