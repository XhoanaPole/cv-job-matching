"""
matcher_v2.py
-------------
Enhanced CV-to-Job matcher with a 5-signal hybrid scoring formula:

  Signal              Weight  Max Points
  ──────────────────  ──────  ──────────
  Semantic (FAISS)     40 %     40 pts
  Lexical  (Skills)    20 %     20 pts
  Domain Category      15 %     15 pts
  Education Level      15 %     15 pts
  Seniority Level      10 %     10 pts
  ──────────────────  ──────  ──────────
  Total               100 %    100 pts

Fit thresholds (applied to the final 0-100 score):
  Strong Fit  ≥ 70
  Moderate    40 – 69
  Weak Fit    < 40
"""

from typing import List, Dict
import numpy as np
from .skills_extractor_v2 import SkillsExtractorV2
from .domain_classifier import DomainClassifier
from .profile_classifier import ProfileClassifier


class CVJobMatcherV2:
    """
    Drop-in replacement for CVJobMatcher with full 5-signal hybrid scoring.
    Retains identical public API so the FastAPI routes need only a one-line swap.
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self, text_cleaner, embedder, faiss_index, include_gap_analysis=True):
        self.cleaner              = text_cleaner
        self.embedder             = embedder
        self.index                = faiss_index
        self.include_gap_analysis = include_gap_analysis

        if self.include_gap_analysis:
            self.skills_extractor = SkillsExtractorV2()

        self.domain_classifier  = DomainClassifier()
        self.profile_classifier = ProfileClassifier()

    # ------------------------------------------------------------------
    # Internal scoring helpers
    # ------------------------------------------------------------------

    def _normalize_faiss(self, raw_score: float) -> float:
        """
        Squash raw FAISS cosine score into [0, 1] with a baseline penalty.
        Any score ≤ 0.30 is treated as no signal.
        """
        baseline = 0.30
        if raw_score <= baseline:
            return 0.0
        scaled = (raw_score - baseline) / (1.0 - baseline)
        return float(max(0.0, min(1.0, scaled ** 1.5)))

    def _compute_hybrid_score(
        self,
        faiss_score:          float,
        skills_pct:           float,
        domain_compatibility: float,
        education_score:      float,
        seniority_score:      float,
    ) -> Dict:
        """
        Combine all 5 signals into a transparent points breakdown.

        All input scores are normalised to [0, 1].
        Output `final_hybrid` is on a 0-100 scale for human readability.
        """
        semantic_raw  = self._normalize_faiss(faiss_score)
        lexical_raw   = skills_pct / 100.0
        domain_raw    = domain_compatibility
        education_raw = education_score
        seniority_raw = seniority_score

        semantic_pts  = round(semantic_raw  * 40, 2)   # max 40
        skills_pts    = round(lexical_raw   * 20, 2)   # max 20
        domain_pts    = round(domain_raw    * 15, 2)   # max 15
        edu_pts       = round(education_raw * 15, 2)   # max 15
        sen_pts       = round(seniority_raw * 10, 2)   # max 10

        final = round(semantic_pts + skills_pts + domain_pts + edu_pts + sen_pts, 2)

        return {
            # --- aggregated ---
            'final_hybrid':       final,
            # --- per-signal points ---
            'semantic_points':    semantic_pts,
            'skills_points':      skills_pts,
            'domain_points':      domain_pts,
            'education_points':   edu_pts,
            'seniority_points':   sen_pts,
            # --- raw inputs (for transparency / LLM prompt) ---
            'raw_faiss_pct':      round(faiss_score * 100, 2),
            'raw_skills_pct':     round(skills_pct, 2),
        }

    def _fit_category(self, score_100: float) -> str:
        if score_100 >= 70:
            return 'strong fit'
        elif score_100 >= 40:
            return 'moderate fit'
        return 'weak fit'

    def _enrich_match(
        self,
        job_id:     str,
        raw_score:  float,
        cleaned_cv: str,
    ) -> Dict:
        """
        Run all 5 signals for one CV-job pair and return a fully populated
        match dict that the API and LLM layer can consume directly.
        """
        match_info  = {'job_id': job_id}
        skills_pct  = 0.0
        domain_info = {}
        profile_info = {}

        if self.include_gap_analysis and self.index.job_texts:
            try:
                job_idx  = self.index.job_ids.index(job_id)
                job_text = self.index.job_texts[job_idx]

                # ── Signal 2: Skills (lexical) ──────────────────────────
                gap = self.skills_extractor.compare_skills(cleaned_cv, job_text)
                skills_pct = gap.get('match_percentage', 0.0)
                match_info['gap_analysis'] = {
                    'matched_skills':   gap['matched_skills'],
                    'missing_skills':   gap['missing_skills'],
                    'match_percentage': gap['match_percentage'],
                    'matched_count':    gap['matched_count'],
                    'missing_count':    gap['missing_count'],
                }

                # ── Signal 3: Domain (categorical) ──────────────────────
                domain_info = self.domain_classifier.score_pair(cleaned_cv, job_text)

                # ── Signals 4 & 5: Education + Seniority ────────────────
                profile_info = self.profile_classifier.score_pair(cleaned_cv, job_text)

            except (ValueError, IndexError) as exc:
                match_info['gap_analysis'] = {
                    'error': f'Analysis unavailable: {exc}'
                }

        # ── Signal 1: Semantic (FAISS) + combine all ────────────────────
        breakdown = self._compute_hybrid_score(
            faiss_score          = float(raw_score),
            skills_pct           = skills_pct,
            domain_compatibility = domain_info.get('compatibility', 0.5),
            education_score      = profile_info.get('education_score', 0.5),
            seniority_score      = profile_info.get('seniority_score', 0.5),
        )

        # Attach domain & profile labels to breakdown for the LLM
        breakdown['cv_domain']            = domain_info.get('cv_domain',  'unknown')
        breakdown['job_domain']           = domain_info.get('job_domain', 'unknown')
        breakdown['domain_compatibility'] = f"{round(domain_info.get('compatibility', 0.5) * 100)}%"
        breakdown['cv_education']         = profile_info.get('cv_education',  'unknown')
        breakdown['job_education']        = profile_info.get('job_education', 'not specified')
        breakdown['cv_seniority']         = profile_info.get('cv_seniority',  'mid')
        breakdown['job_seniority']        = profile_info.get('job_seniority', 'mid')

        match_info['similarity_score'] = breakdown['final_hybrid'] / 100.0
        match_info['score_breakdown']  = breakdown
        match_info['fit_category']     = self._fit_category(breakdown['final_hybrid'])

        return match_info

    # ------------------------------------------------------------------
    # Public API — identical signatures to CVJobMatcher
    # ------------------------------------------------------------------

    def match_cv_to_jobs(self, cv_text: str, cv_id: str = None, top_k: int = 10) -> dict:
        """Match a single CV to the top-K most similar jobs."""
        cleaned_cv = self.cleaner.clean(cv_text)
        if not cleaned_cv:
            return {
                'cv_id':   cv_id or 'unknown',
                'error':   'CV text too short or invalid after cleaning',
                'matches': [],
            }

        cv_embedding = self.embedder.embed_single(cleaned_cv)
        job_ids, scores = self.index.search(cv_embedding, top_k)

        matches = [
            self._enrich_match(job_id, score, cleaned_cv)
            for job_id, score in zip(job_ids, scores)
        ]

        result = {
            'cv_id':        cv_id or 'unknown',
            'matches':      matches,
            'cleaned_text': cleaned_cv,
        }

        if self.include_gap_analysis:
            cv_skills = self.skills_extractor.extract_skills(cleaned_cv)
            result['cv_skills_summary'] = {
                'total_skills':       len(cv_skills['all_skills']),
                'top_technical_terms': cv_skills['technical_terms'][:10],
                'top_keywords':       [
                    s for s in cv_skills['all_skills']
                    if s not in cv_skills['technical_terms']
                ][:10],
            }

        return result

    def match_multiple_cvs(
        self,
        cv_texts: List[str],
        cv_ids:   List[str] = None,
        top_k:    int       = 10,
    ) -> List[dict]:
        """Match a batch of CVs to jobs."""
        if cv_ids is None:
            cv_ids = [f'cv_{i}' for i in range(len(cv_texts))]

        cleaned_results  = self.cleaner.clean_batch(cv_texts)
        if not cleaned_results:
            return [
                {'cv_id': cid, 'error': 'All CVs invalid', 'matches': []}
                for cid in cv_ids
            ]

        cleaned_texts    = [r['cleaned_text'] for r in cleaned_results]
        original_indices = [r['original_index'] for r in cleaned_results]
        cv_embeddings    = self.embedder.embed_batch(cleaned_texts)
        search_results   = self.index.search_batch(cv_embeddings, top_k)

        all_results  = []
        result_idx   = 0

        for i, cv_id in enumerate(cv_ids):
            if i in original_indices:
                job_ids    = search_results[result_idx]['job_ids']
                scores     = search_results[result_idx]['scores']
                cleaned_cv = cleaned_texts[result_idx]

                matches = [
                    self._enrich_match(job_id, score, cleaned_cv)
                    for job_id, score in zip(job_ids, scores)
                ]

                res = {
                    'cv_id':        cv_id,
                    'matches':      matches,
                    'cleaned_text': cleaned_cv,
                }
                if self.include_gap_analysis:
                    cv_skills = self.skills_extractor.extract_skills(cleaned_cv)
                    res['cv_skills_summary'] = {
                        'total_skills':        len(cv_skills['all_skills']),
                        'top_technical_terms': cv_skills['technical_terms'][:10],
                        'top_keywords':        [
                            s for s in cv_skills['all_skills']
                            if s not in cv_skills['technical_terms']
                        ][:10],
                    }
                all_results.append(res)
                result_idx += 1
            else:
                all_results.append({
                    'cv_id':   cv_id,
                    'error':   'CV too short or invalid',
                    'matches': [],
                })

        return all_results
