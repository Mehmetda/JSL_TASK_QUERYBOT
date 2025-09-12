"""
Embedding service for vector operations
"""
import numpy as np
from typing import List, Union
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing embeddings"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize embedding service
        
        Args:
            model_name: Name of the sentence transformer model
        """
        self.model_name = model_name
        self.model = None
        self.embedding_dim = None
        
    def _load_model(self):
        """Load the embedding model"""
        if self.model is None:
            try:
                logger.info(f"Loading embedding model: {self.model_name}")
                self.model = SentenceTransformer(self.model_name)
                # Get embedding dimension
                test_embedding = self.model.encode(["test"])
                self.embedding_dim = test_embedding.shape[1]
                logger.info(f"Embedding model loaded, dimension: {self.embedding_dim}")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise e
    
    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Encode texts to embeddings
        
        Args:
            texts: Single text or list of texts
            
        Returns:
            Numpy array of embeddings
        """
        if self.model is None:
            self._load_model()
        
        try:
            if isinstance(texts, str):
                texts = [texts]
            
            embeddings = self.model.encode(texts)
            return embeddings
            
        except Exception as e:
            logger.error(f"Error encoding texts: {e}")
            raise e
    
    def encode_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Encode texts in batches for better performance
        
        Args:
            texts: List of texts to encode
            batch_size: Batch size for processing
            
        Returns:
            Numpy array of embeddings
        """
        if self.model is None:
            self._load_model()
        
        try:
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch_embeddings = self.model.encode(batch)
                all_embeddings.append(batch_embeddings)
            
            return np.vstack(all_embeddings)
            
        except Exception as e:
            logger.error(f"Error encoding batch: {e}")
            raise e
    
    def get_embedding_dimension(self) -> int:
        """Get the embedding dimension"""
        if self.embedding_dim is None:
            self._load_model()
        return self.embedding_dim
    
    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Cosine similarity score
        """
        try:
            # Normalize embeddings
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Calculate cosine similarity
            similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
