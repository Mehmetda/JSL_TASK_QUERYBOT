"""
FAISS vector store implementation
"""
import faiss
import numpy as np
import pickle
import os
from typing import List, Dict, Any, Optional, Tuple
import logging
from .embeddings import EmbeddingService

logger = logging.getLogger(__name__)


class FAISSVectorStore:
    """FAISS-based vector store for similarity search"""
    
    def __init__(self, 
                 embedding_service: EmbeddingService,
                 index_path: Optional[str] = None,
                 dimension: Optional[int] = None):
        """
        Initialize FAISS vector store
        
        Args:
            embedding_service: Embedding service instance
            index_path: Path to save/load index
            dimension: Embedding dimension (auto-detected if None)
        """
        self.embedding_service = embedding_service
        self.index_path = index_path
        self.dimension = dimension or embedding_service.get_embedding_dimension()
        self.index = None
        self.metadata = []  # Store metadata for each vector
        self.id_to_metadata = {}  # Map from FAISS ID to metadata
        self.next_id = 0
        
        # Initialize index
        self._initialize_index()
        
        # Load existing index if path exists
        if self.index_path and os.path.exists(self.index_path):
            self.load_index()
    
    def _initialize_index(self):
        """Initialize FAISS index"""
        try:
            # Use IndexFlatIP for cosine similarity (inner product)
            self.index = faiss.IndexFlatIP(self.dimension)
            logger.info(f"Initialized FAISS index with dimension {self.dimension}")
        except Exception as e:
            logger.error(f"Failed to initialize FAISS index: {e}")
            raise e
    
    def add_documents(self, 
                     texts: List[str], 
                     metadata: List[Dict[str, Any]] = None) -> List[int]:
        """
        Add documents to the vector store
        
        Args:
            texts: List of texts to add
            metadata: List of metadata dictionaries
            
        Returns:
            List of document IDs
        """
        try:
            if metadata is None:
                metadata = [{} for _ in texts]
            
            if len(texts) != len(metadata):
                raise ValueError("Number of texts must match number of metadata entries")
            
            # Generate embeddings
            embeddings = self.embedding_service.encode(texts)
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            
            # Add to index
            start_id = self.next_id
            self.index.add(embeddings)
            
            # Store metadata
            doc_ids = []
            for i, (text, meta) in enumerate(zip(texts, metadata)):
                doc_id = start_id + i
                doc_metadata = {
                    'id': doc_id,
                    'text': text,
                    **meta
                }
                self.metadata.append(doc_metadata)
                self.id_to_metadata[doc_id] = doc_metadata
                doc_ids.append(doc_id)
            
            self.next_id += len(texts)
            
            logger.info(f"Added {len(texts)} documents to vector store")
            return doc_ids
            
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise e
    
    def search(self, 
               query: str, 
               k: int = 5, 
               filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        
        Args:
            query: Query text
            k: Number of results to return
            filter_metadata: Optional metadata filter
            
        Returns:
            List of search results with metadata
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.encode([query])
            faiss.normalize_L2(query_embedding)
            
            # Search
            scores, indices = self.index.search(query_embedding, k)
            
            # Prepare results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:  # No more results
                    break
                
                if idx in self.id_to_metadata:
                    result = {
                        'score': float(score),
                        'metadata': self.id_to_metadata[idx]
                    }
                    
                    # Apply metadata filter if provided
                    if filter_metadata:
                        if self._matches_filter(result['metadata'], filter_metadata):
                            results.append(result)
                    else:
                        results.append(result)
            
            logger.info(f"Found {len(results)} results for query")
            return results
            
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []
    
    def _matches_filter(self, metadata: Dict[str, Any], filter_dict: Dict[str, Any]) -> bool:
        """Check if metadata matches filter criteria"""
        for key, value in filter_dict.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True
    
    def get_document(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        return self.id_to_metadata.get(doc_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        return {
            'total_documents': len(self.metadata),
            'index_size': self.index.ntotal,
            'dimension': self.dimension,
            'index_path': self.index_path
        }
    
    def save_index(self, path: Optional[str] = None):
        """Save index to disk"""
        try:
            save_path = path or self.index_path
            if not save_path:
                raise ValueError("No path specified for saving index")
            
            # Save FAISS index
            faiss.write_index(self.index, save_path + '.faiss')
            
            # Save metadata
            with open(save_path + '.pkl', 'wb') as f:
                pickle.dump({
                    'metadata': self.metadata,
                    'id_to_metadata': self.id_to_metadata,
                    'next_id': self.next_id
                }, f)
            
            logger.info(f"Index saved to {save_path}")
            
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            raise e
    
    def load_index(self, path: Optional[str] = None):
        """Load index from disk"""
        try:
            load_path = path or self.index_path
            if not load_path:
                raise ValueError("No path specified for loading index")
            
            # Load FAISS index
            self.index = faiss.read_index(load_path + '.faiss')
            
            # Load metadata
            with open(load_path + '.pkl', 'rb') as f:
                data = pickle.load(f)
                self.metadata = data['metadata']
                self.id_to_metadata = data['id_to_metadata']
                self.next_id = data['next_id']
            
            logger.info(f"Index loaded from {load_path}")
            
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            raise e
    
    def clear(self):
        """Clear all documents from the store"""
        self._initialize_index()
        self.metadata = []
        self.id_to_metadata = {}
        self.next_id = 0
        logger.info("Vector store cleared")
