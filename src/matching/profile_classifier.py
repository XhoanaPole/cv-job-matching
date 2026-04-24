"""
profile_classifier.py
---------------------
Lexical classifier for two candidate-profile signals:
  1. Education level  (high_school → diploma → bachelor → master → phd)
  2. Seniority level  (intern → junior → mid → senior → executive)

No ML models required — pure keyword matching with an ordinal scoring scheme.
"""

from typing import Dict, Tuple

# ---------------------------------------------------------------------------
# Education
# ---------------------------------------------------------------------------
EDUCATION_LEVELS = ['high_school', 'diploma', 'bachelor', 'master', 'phd']

EDUCATION_KEYWORDS: Dict[str, list] = {
    'phd': [
        'phd', 'ph.d', 'ph.d.', 'doctorate', 'doctoral',
        'doctor of philosophy', 'dphil', 'd.phil',
    ],
    'master': [
        'master', "master's", 'msc', 'm.sc', 'mba', 'm.b.a', 'meng',
        'm.eng', 'ma ', 'm.a ', 'm.a.', 'postgraduate', 'post-graduate',
        'graduate degree', 'magistër', 'magistër shkencash',
    ],
    'bachelor': [
        'bachelor', "bachelor's", 'bsc', 'b.sc', 'ba ', 'b.a ', 'b.a.',
        'beng', 'b.eng', 'undergraduate', 'licencë', 'licenciate',
        'b.s.', 'b.s ', 'hons', 'honours degree',
    ],
    'diploma': [
        'diploma', 'associate degree', 'hnc', 'hnd',
        'foundation degree', 'vocational', 'technical certificate',
        'advanced certificate', 'professional certificate',
    ],
    'high_school': [
        'high school', 'secondary school', 'gcse', 'a-level', 'a level',
        'baccalaureate', 'matura', 'abitur', 'gymnasium',
        'liceul', 'gjimnaz',
    ],
}

# ---------------------------------------------------------------------------
# Seniority
# ---------------------------------------------------------------------------
SENIORITY_LEVELS = ['intern', 'junior', 'mid', 'senior', 'executive']

SENIORITY_KEYWORDS: Dict[str, list] = {
    'executive': [
        'ceo', 'cto', 'cfo', 'coo', 'chief ', 'vp ', 'vice president',
        'director', 'head of department', 'head of ', 'executive',
        'president', 'partner', 'founder', 'co-founder',
    ],
    'senior': [
        'senior ', 'sr. ', 'sr ', 'lead ', 'principal ',
        'staff engineer', 'staff developer', 'supervisor', 'manager',
        'team lead', 'tech lead', 'specialist',
    ],
    'junior': [
        'junior', 'jr.', 'jr ', 'entry level', 'entry-level',
        'graduate ', 'trainee', 'fresher', 'beginner',
        'starting position', 'new graduate',
    ],
    'intern': [
        'intern', 'internship', 'apprentice', 'apprenticeship',
        'placement student', 'work experience', 'praktik',
    ],
}


class ProfileClassifier:
    """
    Detects education level and seniority from raw text for both the CV and
    the job description, then converts the alignment into a 0.0–1.0 score.
    """

    # ------------------------------------------------------------------
    # Education helpers
    # ------------------------------------------------------------------

    def detect_education(self, text: str) -> Tuple[str, int]:
        """
        Returns (level_name, ordinal_index) for the HIGHEST education level
        detected in the text.

        Returns ('unknown', -1) when nothing is found.
        """
        text_lower = text.lower()
        best_level = 'unknown'
        best_idx   = -1

        for level, keywords in EDUCATION_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    idx = EDUCATION_LEVELS.index(level)
                    if idx > best_idx:
                        best_level = level
                        best_idx   = idx

        return best_level, best_idx

    def score_education_match(self, cv_text: str, job_text: str) -> Dict:
        """
        Score education alignment on a 0.0–1.0 scale:
          - Exact match          → 1.00
          - Overqualified        → 0.90  (not a real problem — slight bonus)
          - 1 level below        → 0.50
          - 2 levels below       → 0.20
          - 3+ levels below      → 0.00
          - Job doesn't specify  → 0.75  (neutral-positive, can't penalise)
          - CV doesn't specify   → 0.50  (mild penalty — ambiguity)
        """
        cv_level,  cv_idx  = self.detect_education(cv_text)
        job_level, job_idx = self.detect_education(job_text)

        if job_idx == -1:
            score = 0.75
        elif cv_idx == -1:
            score = 0.50
        else:
            diff = cv_idx - job_idx        # +ve = overqualified, -ve = underqualified
            if diff >= 0:
                score = 1.0 if diff == 0 else 0.90
            elif diff == -1:
                score = 0.50
            elif diff == -2:
                score = 0.20
            else:
                score = 0.00

        return {
            'cv_education':  cv_level,
            'job_education': job_level if job_idx != -1 else 'not specified',
            'education_score': round(score, 3),
        }

    # ------------------------------------------------------------------
    # Seniority helpers
    # ------------------------------------------------------------------

    def detect_seniority(self, text: str) -> Tuple[str, int]:
        """
        Returns (level_name, ordinal_index) for the seniority level with
        the MOST keyword hits in the text.

        Defaults to ('mid', 2) when ambiguous — the safe middle ground.
        """
        text_lower = text.lower()
        hit_counts = {}

        for level, keywords in SENIORITY_KEYWORDS.items():
            hits = sum(1 for kw in keywords if kw in text_lower)
            if hits > 0:
                hit_counts[level] = hits

        if not hit_counts:
            return 'mid', 2  # default fallback

        best_level = max(hit_counts, key=hit_counts.__getitem__)
        best_idx   = SENIORITY_LEVELS.index(best_level)
        return best_level, best_idx

    def score_seniority_match(self, cv_text: str, job_text: str) -> Dict:
        """
        Score seniority alignment on a 0.0–1.0 scale:
          - 0 levels apart → 1.00
          - 1 level apart  → 0.60
          - 2 levels apart → 0.25
          - 3+ levels apart→ 0.00
        """
        cv_level,  cv_idx  = self.detect_seniority(cv_text)
        job_level, job_idx = self.detect_seniority(job_text)

        diff = abs(cv_idx - job_idx)
        if diff == 0:
            score = 1.00
        elif diff == 1:
            score = 0.60
        elif diff == 2:
            score = 0.25
        else:
            score = 0.00

        return {
            'cv_seniority':  cv_level,
            'job_seniority': job_level,
            'seniority_score': round(score, 3),
        }

    # ------------------------------------------------------------------
    # Combined pair scorer
    # ------------------------------------------------------------------

    def score_pair(self, cv_text: str, job_text: str) -> Dict:
        """Run both classifiers and return a merged result dict."""
        edu = self.score_education_match(cv_text, job_text)
        sen = self.score_seniority_match(cv_text, job_text)
        return {**edu, **sen}
