import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Union

class TextEmbedder:
    """
    Generate embeddings for CVs and job descriptions using Sentence-Transformers.
    Uses the same model for both to ensure vector space compatibility.
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the embedder.
        
        Args:
            model_name: Name of the sentence-transformer model
                       'all-MiniLM-L6-v2' is lightweight and effective
                       'all-mpnet-base-v2' is more accurate but slower
        """
        print(f"Loading model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        print(f"Model loaded. Embedding dimension: {self.embedding_dim}")
        
    def embed_single(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Cleaned text string
            
        Returns:
            1D numpy array of shape (embedding_dim,)
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding
    
    def embed_batch(self, texts: List[str], batch_size: int = 32, show_progress: bool = True) -> np.ndarray:
        """
        Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of cleaned text strings
            batch_size: Number of texts to process at once
            show_progress: Show progress bar
            
        Returns:
            2D numpy array of shape (num_texts, embedding_dim)
        """
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )
        return embeddings
    
    def save_embeddings(self, embeddings: np.ndarray, filepath: str):
        """Save embeddings to disk."""
        np.save(filepath, embeddings)
        print(f"Embeddings saved to {filepath}")
    
    def load_embeddings(self, filepath: str) -> np.ndarray:
        """Load embeddings from disk."""
        embeddings = np.load(filepath)
        print(f"Embeddings loaded from {filepath}. Shape: {embeddings.shape}")
        return embeddings


class EmbeddingPipeline:
    """
    Complete pipeline for processing texts and generating embeddings.
    """
    
    def __init__(self, text_cleaner, embedder: TextEmbedder):
        self.cleaner = text_cleaner
        self.embedder = embedder
        
    def process_texts(self, raw_texts: List[str], text_ids: List[str] = None) -> dict:
        """
        Clean texts and generate embeddings.
        
        Args:
            raw_texts: List of raw text strings
            text_ids: Optional list of IDs for each text
            
        Returns:
            Dict with 'embeddings', 'text_ids', 'cleaned_texts'
        """
        # Clean texts
        cleaned_results = self.cleaner.clean_batch(raw_texts)
        
        if len(cleaned_results) == 0:
            raise ValueError("No valid texts after cleaning")
        
        # Extract cleaned texts and track original indices
        cleaned_texts = [r['cleaned_text'] for r in cleaned_results]
        original_indices = [r['original_index'] for r in cleaned_results]
        
        # Generate embeddings
        embeddings = self.embedder.embed_batch(cleaned_texts)
        
        # Map text IDs
        if text_ids:
            valid_ids = [text_ids[i] for i in original_indices]
        else:
            valid_ids = [f"text_{i}" for i in original_indices]
        
        return {
            'embeddings': embeddings,
            'text_ids': valid_ids,
            'cleaned_texts': cleaned_texts,
            'original_indices': original_indices
        }