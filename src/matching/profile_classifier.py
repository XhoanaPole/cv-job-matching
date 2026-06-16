"""
profile_classifier.py
---------------------
Lexical classifier for two candidate-profile signals:
  1. Education level  (high_school → diploma → bachelor → master → phd)
  2. Seniority level  (intern → junior → mid → senior → executive)

No ML models required — pure keyword matching with an ordinal scoring scheme.
"""

from typing import Dict, List, Tuple
from datetime import date
import re

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
        'team lead', 'tech lead',
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


# ---------------------------------------------------------------------------
# Experience-year patterns (used for JD classification when no keyword found)
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Date-range parsing for CV experience (used to detect seniority from dates)
# ---------------------------------------------------------------------------
MONTH_NAMES = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
}

_MONTH_PAT = (
    r'(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may'
    r'|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?'
    r'|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)'
)
_YEAR_PAT = r'(?:19|20)\d{2}'
_SEP_PAT  = r'\s*[-–—]\s*'
_PRES_PAT = r'(?:present|current|now|ongoing|to\s+date)'

# "Jan 2023 – Dec 2023"  /  "Jan 2023 – Present"
_RE_MONTH_RANGE = re.compile(
    rf'({_MONTH_PAT})\s+({_YEAR_PAT}){_SEP_PAT}'
    rf'(?:({_MONTH_PAT})\s+({_YEAR_PAT})|({_PRES_PAT}))',
    re.IGNORECASE,
)
# "2021 – 2023"  /  "2021 – Present"  (fallback when month names absent)
_RE_YEAR_RANGE = re.compile(
    rf'\b({_YEAR_PAT}){_SEP_PAT}(?:({_YEAR_PAT})|({_PRES_PAT}))\b',
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
EXPERIENCE_YEAR_PATTERNS: List[Tuple[str, str]] = [
    # Entry / no experience required → junior
    (r'\b0\s*[-–]\s*1\s+years?\b',               'junior'),
    (r'\b0\s+1\s+years?\b',                       'junior'),  # dash stripped by TextCleaner
    (r'\brecent\s+graduates?\b',                  'junior'),
    (r'\bno\s+(?:prior\s+)?experience\s+required\b', 'junior'),
    # 2+ years or 2-N year ranges → mid
    (r'\b2\s*\+\s*years?\b',                      'mid'),
    (r'\btwo\s*\+?\s*years?\b',                   'mid'),
    (r'\b2\s*[-–]\s*[3-9]\s+years?\b',            'mid'),   # "2-4 years" (raw)
    (r'\b2\s+[3-9]\s+years?\b',                   'mid'),   # "2 4 years" (dash stripped)
    # 3+ years, explicit minimums, or 3-N year ranges → senior
    (r'\b(?:minimum\s+)?3\s*\+?\s*years?\b',      'senior'),
    (r'\b[4-9]\s*\+?\s*years?\b',                'senior'),
    (r'\b3\s*[-–]\s*\d+\s+years?\b',             'senior'),  # "3-6 years" (raw)
    (r'\b3\s+\d+\s+years?\b',                    'senior'),  # "3 6 years" (dash stripped)
    (r'\b[4-9]\s*[-–]\s*\d+\s+years?\b',         'senior'),  # "4-8 years" (raw)
    (r'\b[4-9]\s+\d+\s+years?\b',                'senior'),  # "4 8 years" (dash stripped)
]


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

    def _months_of_experience(self, text: str) -> int:
        """Sum months from all date ranges found in the text (CV work experience)."""
        today = date.today()
        durations = []

        for m in _RE_MONTH_RANGE.finditer(text):
            start_month = MONTH_NAMES.get(m.group(1)[:3].lower(), 1)
            start_year  = int(m.group(2))
            if m.group(5):  # "present / current / now"
                end_month, end_year = today.month, today.year
            else:
                end_month = MONTH_NAMES.get(m.group(3)[:3].lower(), 1)
                end_year  = int(m.group(4))
            months = (end_year - start_year) * 12 + (end_month - start_month)
            if 0 < months < 600:
                durations.append(months)

        if not durations:
            for m in _RE_YEAR_RANGE.finditer(text):
                start_year = int(m.group(1))
                end_year   = today.year if m.group(3) else int(m.group(2))
                months     = (end_year - start_year) * 12
                if 0 < months < 600:
                    durations.append(months)

        return sum(durations)

    def _months_to_seniority(self, total_months: int) -> Tuple[str, int]:
        if total_months < 12:
            return 'intern', 0
        elif total_months < 36:
            return 'junior', 1
        elif total_months < 72:
            return 'mid', 2
        elif total_months < 120:
            return 'senior', 3
        else:
            return 'executive', 4

    @staticmethod
    def _kw_hit(kw: str, text_lower: str) -> bool:
        """Word-boundary keyword match — prevents 'coo' firing on 'coordinate',
        'intern' on 'international', etc."""
        return bool(re.search(r'\b' + re.escape(kw.strip()) + r'\b', text_lower))

    def detect_seniority(self, text: str, is_jd: bool = False) -> Tuple[str, int]:
        """
        Returns (level_name, ordinal_index) for the seniority level with
        the MOST keyword hits in the text.

        For JDs (is_jd=True): year-requirement patterns run first because they
        encode the actual experience requirement and are more reliable than
        keywords that may appear in organizational context ("reporting to the
        Director").  Falls back to keyword matching if no pattern fires.

        For CVs (is_jd=False): explicit intern/internship keywords take
        priority because they are unambiguous entry-level signals.  Falls back
        to keyword matching otherwise.
        """
        text_lower = text.lower()

        if is_jd:
            for pattern, level in EXPERIENCE_YEAR_PATTERNS:
                if re.search(pattern, text_lower):
                    return level, SENIORITY_LEVELS.index(level)
        else:
            intern_kws = SENIORITY_KEYWORDS['intern']
            if any(self._kw_hit(kw, text_lower) for kw in intern_kws):
                return 'intern', 0

        hit_counts = {}
        for level, keywords in SENIORITY_KEYWORDS.items():
            hits = sum(1 for kw in keywords if self._kw_hit(kw, text_lower))
            if hits > 0:
                hit_counts[level] = hits

        if not hit_counts:
            return 'mid', 2  # default fallback

        best_level = max(hit_counts, key=hit_counts.__getitem__)
        best_idx   = SENIORITY_LEVELS.index(best_level)
        return best_level, best_idx

    def score_seniority_match(self, cv_text: str, job_text: str) -> Dict:
        """
        Directional seniority alignment score (0.0–1.0).
        diff = job_idx - cv_idx  (positive = JD more senior than CV)
          - diff ≤ 0  (exact match or overqualified) → 1.00
          - diff = 1  (JD one level above CV)        → 0.60
          - diff = 2  (JD two levels above CV)       → 0.20
          - diff ≥ 3                                 → 0.00
        """
        cv_level,  cv_idx  = self.detect_seniority(cv_text,  is_jd=False)
        job_level, job_idx = self.detect_seniority(job_text, is_jd=True)

        diff = job_idx - cv_idx          # directed: + means underqualified
        if diff <= 0:
            score = 1.00
        elif diff == 1:
            score = 0.60
        elif diff == 2:
            score = 0.20
        else:
            score = 0.00

        job_text_lower = job_text.lower()
        job_from_pattern = any(
            re.search(p, job_text_lower) for p, _ in EXPERIENCE_YEAR_PATTERNS
        )

        return {
            'cv_seniority':              cv_level,
            'cv_seniority_idx':          cv_idx,
            'job_seniority':             job_level,
            'job_seniority_idx':         job_idx,
            'job_seniority_from_pattern': job_from_pattern,
            'seniority_score':           round(score, 3),
            'seniority_diff':            diff,
        }

    # ------------------------------------------------------------------
    # Combined pair scorer
    # ------------------------------------------------------------------

    def score_pair(self, cv_text: str, job_text: str) -> Dict:
        """Run both classifiers and return a merged result dict."""
        edu = self.score_education_match(cv_text, job_text)
        sen = self.score_seniority_match(cv_text, job_text)
        return {**edu, **sen}
