from typing import List, Set, Dict
import re
from collections import Counter

class SkillsExtractor:
    """
    Dynamically extract skills using a blacklist-driven, frequency-weighted approach.
    No hardcoded skill whitelists - captures any technology, framework, or methodology
    that appears in the text and survives the noise filter.
    """
    
    def __init__(self):
        # Skill context indicators — when these appear, extract what follows
        self.skill_indicators = {
            'experience with', 'proficient in', 'skilled in', 'knowledge of',
            'familiar with', 'expertise in', 'expert in', 'certified in',
            'specialization in', 'trained in', 'competent in', 'mastery of',
            'proficiency in', 'working with', 'experience in', 'background in',
            'hands-on with', 'using', 'worked with', 'used'
        }

        # Comprehensive noise blacklist - any word here gets discarded
        self.stop_words = {
            # Generic / vague
            'experience', 'years', 'work', 'working', 'looking', 'seeking',
            'position', 'role', 'job', 'company', 'team', 'environment',
            'opportunity', 'responsibilities', 'requirements', 'qualifications',
            'description', 'summary', 'objective', 'education', 'degree',

            # Education
            'university', 'college', 'school', 'graduated', 'bachelor',
            'master', 'phd', 'diploma', 'certificate', 'student',

            # Location/time
            'location', 'date', 'month', 'year', 'day', 'time',
            'tirana', 'albania', 'remote', 'hybrid', 'onsite',

            # Generic descriptors
            'full', 'part', 'salary', 'benefits', 'apply', 'application',
            'excellent', 'strong', 'good', 'basic', 'advanced', 'intermediate',
            'ability', 'skills', 'skill', 'understanding', 'background',

            # Articles / connectors
            'and', 'or', 'with', 'for', 'the', 'of', 'in', 'to', 'a', 'an',
            'is', 'are', 'be', 'have', 'has', 'will', 'can', 'may', 'its',
            'this', 'that', 'these', 'those', 'their', 'our', 'your', 'we',
            'you', 'he', 'she', 'they', 'it', 'as', 'at', 'by', 'from',
            'into', 'through', 'during', 'before', 'after', 'above', 'below',

            # Generic verbs
            'work', 'working', 'develop', 'create', 'manage', 'use', 'using',
            'analyze', 'collaborate', 'conduct', 'produce', 'design', 'implement',
            'test', 'deploy', 'maintain', 'support', 'lead', 'guide', 'mentor',
            'train', 'evaluate', 'review', 'improve', 'optimize', 'ensure',
            'build', 'write', 'solve', 'define', 'identify', 'monitor',
            'communicate', 'coordinate', 'assist', 'provide', 'include',
            'require', 'perform', 'help', 'join', 'become', 'operate',

            # Business / HR noise
            'company', 'organization', 'industry', 'business', 'professional',
            'candidate', 'applicant', 'employee', 'employer', 'intern',
            'responsible', 'capable', 'proven', 'track', 'record',
            'communication', 'written', 'verbal', 'interpersonal',
            'problem', 'solving', 'analytical', 'critical', 'thinking',
            'detail', 'oriented', 'multitask', 'prioritize',
            'management', 'project', 'projects', 'product', 'products',
            'service', 'services', 'customer', 'customers', 'client', 'clients',
            'user', 'users', 'portfolio', 'online', 'website', 'web', 'page',
            'pages', 'site', 'sites', 'app', 'apps',
            'system', 'systems', 'platform', 'platforms', 'tool', 'tools',
            'software', 'hardware', 'network', 'networks', 'server', 'servers',
            'result', 'results', 'data', 'information', 'report', 'reports',
            'record', 'records', 'file', 'files', 'document', 'documents',
            'form', 'forms', 'policy', 'policies', 'procedure', 'procedures',
            'process', 'processes', 'method', 'methods', 'practice', 'practices',
            'standard', 'standards', 'rule', 'rules',
            'knowledge', 'proficiency', 'familiarity', 'coordinator',
            'google', 'facebook', 'microsoft', 'amazon', 'apple',
            'email', 'title', 'new', 'high', 'large', 'best', 'fast',
            'real', 'time', 'key', 'core', 'main', 'cross', 'end', 'based',
            'driven', 'related', 'level', 'type', 'example', 'following',
            'such', 'including', 'well', 'plus', 'also', 'both', 'other',
            'more', 'most', 'than', 'not', 'no', 'all', 'any', 'each',
            'every', 'same', 'own', 'different', 'various', 'multiple'
        }

        # Multiword technical phrase patterns (to detect before tokenization)
        self.phrase_patterns = [
            r'\bnatural language processing\b',
            r'\blarge language model\b',
            r'\bmachine learning\b',
            r'\bdeep learning\b',
            r'\bcomputer vision\b',
            r'\bdata science\b',
            r'\bdata analysis\b',
            r'\bdata engineering\b',
            r'\bstatistical analysis\b',
            r'\bci[/\-]cd\b',
            r'\bdevops\b',
            r'\brestful api\b',
            r'\brest api\b',
            r'\bgraph ql\b',
            r'\bpower bi\b',
            r'\bscikit[\-\s]learn\b',
            r'\bnode\.js\b',
            r'\bvue\.js\b',
            r'\breact\.js\b',
            r'\bnext\.js\b',
            r'\bexpress\.js\b',
            r'\bscikit learn\b',
            r'\bafter effects\b',
            r'\bgoogle analytics\b',
            r'\bgoogle ads\b',
            r'\bfacebook ads\b',
            r'\bobject oriented\b',
            r'\bobject-oriented\b',
        ]

    def _clean_text(self, text: str) -> str:
        """Normalize whitespace and remove non-ASCII artifacts."""
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def extract_phrases(self, text: str) -> Set[str]:
        """Extract known multi-word technical phrases."""
        found = set()
        text_lower = text.lower()
        for pat in self.phrase_patterns:
            for m in re.finditer(pat, text_lower):
                phrase = re.sub(r'[\-/]', ' ', m.group(0)).strip()
                phrase = re.sub(r'\s+', ' ', phrase)
                found.add(phrase)
        return found

    def extract_indicator_skills(self, text: str) -> Set[str]:
        """Extract skills following explicit skill-signal phrases."""
        skills = set()
        text_lower = text.lower()

        for indicator in self.skill_indicators:
            pattern = rf'{re.escape(indicator)}\s+([^.\n;(]+?)(?:\.|;|\n|\(|$)'
            for match in re.finditer(pattern, text_lower, re.IGNORECASE):
                phrase = match.group(1).strip()
                terms = re.split(r',\s*|\s+and\s+|\s+or\s+|/|\|', phrase)
                for term in terms:
                    term = re.sub(r'^(the|a|an|in|of|with|for)\s+', '', term.strip())
                    term = re.sub(r'\s+(in|of|with|for)$', '', term)
                    term = term.strip()
                    if self._is_valid(term):
                        words = term.split()[:4]  # up to 4-word terms
                        skills.add(' '.join(words))
        return skills

    def extract_capitalized_terms(self, text: str) -> Counter:
        """
        Frequency-weighted extraction of Capitalized/ALLCAPS tokens.
        Returns a Counter so we can rank by frequency across the document.
        """
        counts: Counter = Counter()
        # Match capitalized tokens (CamelCase, ALLCAPS, mixed like 'GPT-4', 'Node.js')
        pattern = r'\b[A-Z][A-Za-z0-9+#\.\-]{1,30}\b'
        for match in re.finditer(pattern, text):
            term = match.group(0)
            term_lower = term.lower()

            # Skip if it's purely a stop word or common English word
            if term_lower in self.stop_words:
                continue
            # Skip if it looks like a sentence-starting common word (short, all-alpha)
            if len(term) <= 2:
                continue
            # Skip pure numbers
            if term.isdigit():
                continue
            # Skip words ending in common suffix patterns that are noise
            if re.match(r'^(The|This|That|These|Those|Our|Your|Their|We|You|He|She|They|It|As|At|If|But|So|Yet|For|Nor|Or|And)$', term):
                continue

            counts[term_lower] += 1

        return counts

    def extract_lowercase_tech(self, text: str) -> Set[str]:
        """
        Catch lowercase technical terms that are genuinely technical but never capitalized,
        e.g.: 'docker', 'git', 'sql', 'rest', 'grep', 'bash'.
        These are detected as short alphanumeric tokens adjacent to code-like context.
        """
        found = set()
        # Match lowercase tokens 2–20 chars that look like tech (allow digits, +, #, .)
        pattern = r'\b([a-z][a-z0-9+#\.\-]{1,19})\b'
        for match in re.finditer(pattern, text.lower()):
            term = match.group(1)
            if term in self.stop_words:
                continue
            if len(term) < 2:
                continue
            # Only keep if it looks code-ish: contains digit/symbol, or is short acronym
            if re.search(r'[0-9\+\#\.]', term) or (len(term) <= 5 and term.isalpha()):
                found.add(term)
        return found

    def _is_valid(self, term: str) -> bool:
        """Basic noise gate for a term."""
        t = term.lower().strip()
        if not t or len(t) < 2:
            return False
        if t in self.stop_words:
            return False
        if t.isdigit():
            return False
        if len(re.findall(r'[a-z]', t)) < 2:
            return False
        return True

    def extract_skills(self, text: str, max_skills: int = 30) -> Dict[str, List[str]]:
        """
        Main extraction pipeline. Returns up to max_skills, ranked by signal strength.

        Priority order:
         1. Multi-word technical phrases (highest confidence)
         2. Indicator-context skills (explicit context)
         3. Capitalized token frequency (ranked by frequency)
         4. Lowercase code-style terms
        """
        text = self._clean_text(text)

        # 1. Multi-word phrases
        phrases = self.extract_phrases(text)

        # 2. Indicator-context skills
        indicator_skills = self.extract_indicator_skills(text)

        # 3. Frequency-ranked capitalized tokens
        cap_counts = self.extract_capitalized_terms(text)
        # Sort by frequency descending
        cap_ranked = [term for term, _ in cap_counts.most_common(50)]

        # 4. Lowercase code-style terms
        lower_tech = self.extract_lowercase_tech(text)

        # Merge in priority order, deduplicating
        seen: Set[str] = set()
        all_skills: List[str] = []

        def add_if_new(term: str):
            t = term.lower().strip()
            if t and t not in seen and self._is_valid(t):
                seen.add(t)
                all_skills.append(t)

        for p in sorted(phrases):
            add_if_new(p)
        for s in sorted(indicator_skills):
            add_if_new(s)
        for c in cap_ranked:
            add_if_new(c)
        for lt in sorted(lower_tech):
            add_if_new(lt)

        return {
            'all_skills': all_skills[:max_skills],
            'explicit_skills': sorted(list(indicator_skills))[:15],
            'technical_terms': sorted(list(phrases | set(cap_ranked[:20])))[:15]
        }

    def compare_skills(self, cv_text: str, job_text: str) -> Dict:
        """
        Compare skills between CV and job description.
        Uses a generous overlap: a CV skill 'matches' a job skill if one
        is a substring of the other (handles 'react' vs 'react.js' etc.)
        """
        cv_data = self.extract_skills(cv_text, max_skills=40)
        job_data = self.extract_skills(job_text, max_skills=40)

        cv_skills = set(cv_data['all_skills'])
        job_skills = set(job_data['all_skills'])

        # Fuzzy overlap: a CV skill matches if it contains or is contained by a job skill
        matched = set()
        missing = set()

        for j_skill in job_skills:
            found = False
            for c_skill in cv_skills:
                if j_skill in c_skill or c_skill in j_skill:
                    matched.add(j_skill)
                    found = True
                    break
            if not found:
                missing.add(j_skill)

        extra = cv_skills - matched

        match_percentage = (len(matched) / len(job_skills) * 100) if job_skills else 0.0

        return {
            'cv_skills': sorted(list(cv_skills)),
            'job_skills': sorted(list(job_skills)),
            'matched_skills': sorted(list(matched)),
            'missing_skills': sorted(list(missing)),
            'extra_skills': sorted(list(extra)),
            'match_percentage': round(match_percentage, 2),
            'matched_count': len(matched),
            'missing_count': len(missing)
        }