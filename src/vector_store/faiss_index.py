import faiss
import numpy as np
import pickle
import os
from typing import List, Tuple

class FAISSJobIndex:
    """
    FAISS vector database for job descriptions.
    Uses cosine similarity via IndexFlatIP.
    CVs are used as queries against this index.
    """
    
    def __init__(self, embedding_dim: int):
        """
        Initialize FAISS index.
        
        Args:
            embedding_dim: Dimension of embeddings (e.g., 384)
        """
        self.embedding_dim = embedding_dim
        # Inner Product index (cosine similarity if embeddings are normalized)
        self.index = faiss.IndexFlatIP(embedding_dim)
        self.job_ids = []
        self.job_texts = []
        
    def add_jobs(self, job_embeddings: np.ndarray, job_ids: List[str], job_texts: List[str] = None):
        """
        Add job descriptions to the index.
        """
        if job_embeddings.shape[1] != self.embedding_dim:
            raise ValueError(
                f"Expected embeddings of dimension {self.embedding_dim}, got {job_embeddings.shape[1]}"
            )
        
        # Ensure float32 for FAISS
        job_embeddings = job_embeddings.astype('float32')
        
        # Add to index
        self.index.add(job_embeddings)
        
        # Store metadata
        self.job_ids.extend(job_ids)
        if job_texts:
            self.job_texts.extend(job_texts)
        
        print(f"Added {len(job_ids)} jobs to index. Total jobs: {self.index.ntotal}")
    
    def search(self, cv_embedding: np.ndarray, top_k: int = 10) -> Tuple[List[str], List[float]]:
        """
        Search for top-K most similar jobs for a single CV.
        Returns true cosine similarity scores.
        """
        query = cv_embedding.reshape(1, -1).astype('float32')
        
        # Inner product search (cosine similarity)
        scores, indices = self.index.search(query, top_k)
        
        matched_job_ids = [self.job_ids[idx] for idx in indices[0]]
        
        # Higher score = more similar
        return matched_job_ids, scores[0].tolist()
    
    def search_batch(self, cv_embeddings: np.ndarray, top_k: int = 10) -> List[dict]:
        """
        Search for multiple CVs at once.
        Returns true cosine similarity scores.
        """
        queries = cv_embeddings.astype('float32')
        scores, indices = self.index.search(queries, top_k)
        
        results = []
        for i in range(len(cv_embeddings)):
            matched_job_ids = [self.job_ids[idx] for idx in indices[i]]
            results.append({
                'job_ids': matched_job_ids,
                'scores': scores[i].tolist()
            })
        
        return results
    
    def save(self, index_path: str, metadata_path: str):
        """Save FAISS index and metadata to disk."""
        faiss.write_index(self.index, index_path)
        with open(metadata_path, 'wb') as f:
            pickle.dump({
                'job_ids': self.job_ids,
                'job_texts': self.job_texts,
                'embedding_dim': self.embedding_dim
            }, f)
        print(f"Index saved to {index_path}")
        print(f"Metadata saved to {metadata_path}")
    
    @classmethod
    def load(cls, index_path: str, metadata_path: str):
        """Load FAISS index and metadata from disk."""
        with open(metadata_path, 'rb') as f:
            metadata = pickle.load(f)
        
        instance = cls(metadata['embedding_dim'])
        instance.index = faiss.read_index(index_path)
        instance.job_ids = metadata['job_ids']
        instance.job_texts = metadata['job_texts']
        
        print(f"Index loaded from {index_path}")
        print(f"Total jobs in index: {instance.index.ntotal}")
        return instance
    
    @classmethod
    def load_or_create(cls, index_path: str, metadata_path: str, embedding_dim: int = 384):
        """
        Load existing index if files exist, otherwise create new empty index.
        """
        if os.path.exists(index_path) and os.path.exists(metadata_path):
            print("Found existing index, loading...")
            return cls.load(index_path, metadata_path)
        else:
            print("No existing index found, creating new one...")
            return cls(embedding_dim)