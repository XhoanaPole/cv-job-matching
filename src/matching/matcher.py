from typing import List, Dict
import numpy as np
from .skills_extractor import SkillsExtractor

class CVJobMatcher:
    """
    High-level matcher that combines preprocessing, embedding, FAISS search, and gap analysis.
    """
    
    def __init__(self, text_cleaner, embedder, faiss_index, include_gap_analysis=True):
        """
        Initialize matcher with all components.
        
        Args:
            text_cleaner: TextCleaner instance
            embedder: TextEmbedder instance
            faiss_index: FAISSJobIndex instance
            include_gap_analysis: Whether to include skills gap analysis (default: True)
        """
        self.cleaner = text_cleaner
        self.embedder = embedder
        self.index = faiss_index
        self.include_gap_analysis = include_gap_analysis
        
        # Initialize skills extractor if gap analysis enabled
        if self.include_gap_analysis:
            self.skills_extractor = SkillsExtractor()
        
    def match_cv_to_jobs(self, cv_text: str, cv_id: str = None, top_k: int = 10) -> dict:
        """
        Match a single CV to jobs with automatic gap analysis.
        
        Args:
            cv_text: Raw CV text
            cv_id: Optional CV identifier
            top_k: Number of top job matches to return
            
        Returns:
            Dict with CV info, matched jobs, and gap analysis
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
        
        # Build matches with gap analysis
        matches = []
        for job_id, score in zip(job_ids, scores):
            match_info = {
                'job_id': job_id,
                'similarity_score': float(score)
            }
            
            # Add gap analysis if enabled and job text available
            if self.include_gap_analysis and self.index.job_texts:
                try:
                    # Find job index
                    job_idx = self.index.job_ids.index(job_id)
                    job_text = self.index.job_texts[job_idx]
                    
                    # Compare skills
                    gap_analysis = self.skills_extractor.compare_skills(cleaned_cv, job_text)
                    
                    match_info['gap_analysis'] = {
                        'matched_skills': gap_analysis['matched_skills'],
                        'missing_skills': gap_analysis['missing_skills'],
                        'match_percentage': gap_analysis['match_percentage'],
                        'matched_count': gap_analysis['matched_count'],
                        'missing_count': gap_analysis['missing_count']
                    }
                    
                except (ValueError, IndexError) as e:
                    match_info['gap_analysis'] = {
                        'error': f'Could not perform gap analysis: {str(e)}'
                    }
            
            matches.append(match_info)
        
        result = {
            'cv_id': cv_id or 'unknown',
            'matches': matches,
            'cleaned_text': cleaned_cv
        }
        
        # Add overall CV skills if gap analysis enabled
        if self.include_gap_analysis:
            cv_skills = self.skills_extractor.extract_skills(cleaned_cv)
            result['cv_skills_summary'] = {
                'total_skills': len(cv_skills['all_skills']),
                'top_technical_terms': cv_skills['technical_terms'][:10],
                'top_keywords': [s for s in cv_skills['all_skills'] if s not in cv_skills['technical_terms']][:10]
            }
        
        return result
    
    def match_multiple_cvs(self, cv_texts: List[str], cv_ids: List[str] = None, top_k: int = 10) -> List[dict]:
        """
        Match multiple CVs to jobs efficiently with gap analysis.
        
        Args:
            cv_texts: List of raw CV texts
            cv_ids: Optional list of CV identifiers
            top_k: Number of top job matches per CV
            
        Returns:
            List of match results with gap analysis
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
        
        # Format results with gap analysis
        all_results = []
        result_idx = 0
        
        for i, cv_id in enumerate(cv_ids):
            if i in original_indices:
                # Valid CV
                job_ids = search_results[result_idx]['job_ids']
                scores = search_results[result_idx]['scores']
                cleaned_cv = cleaned_texts[result_idx]
                
                matches = []
                for job_id, score in zip(job_ids, scores):
                    match_info = {
                        'job_id': job_id,
                        'similarity_score': float(score)
                    }
                    
                    # Add gap analysis
                    if self.include_gap_analysis and self.index.job_texts:
                        try:
                            job_idx = self.index.job_ids.index(job_id)
                            job_text = self.index.job_texts[job_idx]
                            gap_analysis = self.skills_extractor.compare_skills(cleaned_cv, job_text)
                            
                            match_info['gap_analysis'] = {
                                'matched_skills': gap_analysis['matched_skills'],
                                'missing_skills': gap_analysis['missing_skills'],
                                'match_percentage': gap_analysis['match_percentage'],
                                'matched_count': gap_analysis['matched_count'],
                                'missing_count': gap_analysis['missing_count']
                            }
                        except (ValueError, IndexError):
                            match_info['gap_analysis'] = {'error': 'Gap analysis unavailable'}
                    
                    matches.append(match_info)
                
                result = {
                    'cv_id': cv_id,
                    'matches': matches,
                    'cleaned_text': cleaned_cv
                }
                
                # Add CV skills summary
                if self.include_gap_analysis:
                    cv_skills = self.skills_extractor.extract_skills(cleaned_cv)
                    result['cv_skills_summary'] = {
                        'total_skills': len(cv_skills['all_skills']),
                        'top_technical_terms': cv_skills['technical_terms'][:10],
                        'top_keywords': [s for s in cv_skills['all_skills'] if s not in cv_skills['technical_terms']][:10]
                    }
                
                all_results.append(result)
                result_idx += 1
            else:
                # Invalid CV
                all_results.append({
                    'cv_id': cv_id,
                    'error': 'CV text too short or invalid after cleaning',
                    'matches': []
                })
        
        return all_results
    
    def get_detailed_gap_analysis(self, cv_text: str, job_id: str) -> dict:
        """
        Get detailed gap analysis for a specific CV-job pair.
        
        Args:
            cv_text: CV text (raw or cleaned)
            job_id: Job identifier
            
        Returns:
            Detailed gap analysis with all skills
        """
        # Clean CV
        cleaned_cv = self.cleaner.clean(cv_text)
        
        if not cleaned_cv:
            return {'error': 'Invalid CV text'}
        
        # Find job
        try:
            job_idx = self.index.job_ids.index(job_id)
            job_text = self.index.job_texts[job_idx]
        except (ValueError, IndexError):
            return {'error': f'Job {job_id} not found or job text unavailable'}
        
        # Perform detailed comparison
        if not self.include_gap_analysis:
            self.skills_extractor = SkillsExtractor()
        
        gap_analysis = self.skills_extractor.compare_skills(cleaned_cv, job_text)
        
        return {
            'job_id': job_id,
            'cv_skills': gap_analysis['cv_skills'],
            'job_skills': gap_analysis['job_skills'],
            'matched_skills': gap_analysis['matched_skills'],
            'missing_skills': gap_analysis['missing_skills'],
            'extra_skills': gap_analysis.get('extra_skills', []),
            'match_percentage': gap_analysis['match_percentage'],
            'summary': {
                'total_cv_skills': len(gap_analysis['cv_skills']),
                'total_job_skills': len(gap_analysis['job_skills']),
                'matched': gap_analysis['matched_count'],
                'missing': gap_analysis['missing_count']
            }
        }
    
    def get_match_details(self, cv_id: str, job_id: str, match_results: dict) -> dict:
        """
        Get detailed information about a specific CV-job match from previous results.
        
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
                    'similarity_score': match['similarity_score'],
                    'gap_analysis': match.get('gap_analysis', {}),
                    'cv_text': match_results.get('cleaned_text'),
                    'job_text': job_text
                }
        
        return {
            'error': f'No match found between {cv_id} and {job_id}'
        }