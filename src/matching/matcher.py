from typing import List, Dict
import numpy as np

class CVJobMatcher:
    """
    High-level matcher that combines preprocessing, embedding, and FAISS search.
    """
    
    def __init__(self, text_cleaner, embedder, faiss_index):
        """
        Initialize matcher with all components.
        
        Args:
            text_cleaner: TextCleaner instance
            embedder: TextEmbedder instance
            faiss_index: FAISSJobIndex instance
        """
        self.cleaner = text_cleaner
        self.embedder = embedder
        self.index = faiss_index
        
    def match_cv_to_jobs(self, cv_text: str, cv_id: str = None, top_k: int = 10) -> dict:
        """
        Match a single CV to jobs.
        
        Args:
            cv_text: Raw CV text
            cv_id: Optional CV identifier
            top_k: Number of top job matches to return
            
        Returns:
            Dict with CV info and matched jobs
        """
        # Clean CV text
        cleaned_cv = self.cleaner.clean(cv_text)
        if not cleaned_cv:
            return {
                'cv_id': cv_id or 'unknown',
                'error': 'CV text too short or invalid after cleaning',
                'matches': []
            }
        
        # Generate embedding
        cv_embedding = self.embedder.embed_single(cleaned_cv)
        
        # Search for matches
        job_ids, scores = self.index.search(cv_embedding, top_k)
        
        # Format results
        matches = [
            {
                'job_id': job_id,
                'score': float(score)
            }
            for job_id, score in zip(job_ids, scores)
        ]
        
        return {
            'cv_id': cv_id or 'unknown',
            'matches': matches,
            'cleaned_text': cleaned_cv
        }
    
    def match_multiple_cvs(self, cv_texts: List[str], cv_ids: List[str] = None, top_k: int = 10) -> List[dict]:
        """
        Match multiple CVs to jobs efficiently.
        
        Args:
            cv_texts: List of raw CV texts
            cv_ids: Optional list of CV identifiers
            top_k: Number of top job matches per CV
            
        Returns:
            List of match results
        """
        if cv_ids is None:
            cv_ids = [f"cv_{i}" for i in range(len(cv_texts))]
        
        # Clean all CVs
        cleaned_results = self.cleaner.clean_batch(cv_texts)
        
        if len(cleaned_results) == 0:
            return [{
                'cv_id': cv_id,
                'error': 'No valid CVs after cleaning',
                'matches': []
            } for cv_id in cv_ids]
        
        # Extract data
        cleaned_texts = [r['cleaned_text'] for r in cleaned_results]
        original_indices = [r['original_index'] for r in cleaned_results]
        
        # Generate embeddings
        cv_embeddings = self.embedder.embed_batch(cleaned_texts)
        
        # Batch search
        search_results = self.index.search_batch(cv_embeddings, top_k)
        
        # Format results
        all_results = []
        result_idx = 0
        
        for i, cv_id in enumerate(cv_ids):
            if i in original_indices:
                # Valid CV
                job_ids = search_results[result_idx]['job_ids']
                scores = search_results[result_idx]['scores']
                
                matches = [
                    {
                        'job_id': job_id,
                        'score': float(score)
                    }
                    for job_id, score in zip(job_ids, scores)
                ]
                
                all_results.append({
                    'cv_id': cv_id,
                    'matches': matches,
                    'cleaned_text': cleaned_texts[result_idx]
                })
                result_idx += 1
            else:
                # Invalid CV
                all_results.append({
                    'cv_id': cv_id,
                    'error': 'CV text too short or invalid after cleaning',
                    'matches': []
                })
        
        return all_results
    
    def get_match_details(self, cv_id: str, job_id: str, match_results: dict) -> dict:
        """
        Get detailed information about a specific CV-job match.
        
        Args:
            cv_id: CV identifier
            job_id: Job identifier
            match_results: Results from match_cv_to_jobs
            
        Returns:
            Dict with match details
        """
        for match in match_results.get('matches', []):
            if match['job_id'] == job_id:
                # Find job text if available
                job_idx = self.index.job_ids.index(job_id)
                job_text = self.index.job_texts[job_idx] if self.index.job_texts else None
                
                return {
                    'cv_id': cv_id,
                    'job_id': job_id,
                    'score': match['score'],
                    'cv_text': match_results.get('cleaned_text'),
                    'job_text': job_text
                }
        
        return {
            'error': f'No match found between {cv_id} and {job_id}'
        }