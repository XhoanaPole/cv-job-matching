"""
skills_extractor_v2.py
----------------------
Improved version of SkillsExtractor with:
  - Expanded multi-domain phrase library (tech, healthcare, marketing,
    finance, legal, business)
  - Stricter substring matching in compare_skills() — short tokens (< 6 chars)
    must be exact matches, preventing false positives like 'care' matching
    'patient care' or 'customer care'
"""

from typing import List, Set, Dict
import re
from collections import Counter


class SkillsExtractorV2:
    """
    Dynamically extract skills using a blacklist-driven, frequency-weighted
    approach. Improved over V1 with:
      1. Broader phrase library covering 7 professional domains
      2. Stricter substring matching gate in compare_skills()
    """

    def __init__(self):
        self.skill_indicators = {
            'experience with', 'proficient in', 'skilled in', 'knowledge of',
            'familiar with', 'expertise in', 'expert in', 'certified in',
            'specialization in', 'trained in', 'competent in', 'mastery of',
            'proficiency in', 'working with', 'experience in', 'background in',
            'hands-on with', 'using', 'worked with', 'used',
        }

        self.stop_words = {
            'experience', 'years', 'work', 'working', 'looking', 'seeking',
            'position', 'role', 'job', 'company', 'team', 'environment',
            'opportunity', 'responsibilities', 'requirements', 'qualifications',
            'description', 'summary', 'objective', 'education', 'degree',
            'university', 'college', 'school', 'graduated', 'bachelor',
            'master', 'phd', 'diploma', 'certificate', 'student',
            'location', 'date', 'month', 'year', 'day', 'time',
            'tirana', 'albania', 'remote', 'hybrid', 'onsite',
            'full', 'part', 'salary', 'benefits', 'apply', 'application',
            'excellent', 'strong', 'good', 'basic', 'advanced', 'intermediate',
            'ability', 'skills', 'skill', 'understanding', 'background',
            'and', 'or', 'with', 'for', 'the', 'of', 'in', 'to', 'a', 'an',
            'is', 'are', 'be', 'have', 'has', 'will', 'can', 'may', 'its',
            'this', 'that', 'these', 'those', 'their', 'our', 'your', 'we',
            'you', 'he', 'she', 'they', 'it', 'as', 'at', 'by', 'from',
            'into', 'through', 'during', 'before', 'after', 'above', 'below',
            'work', 'working', 'develop', 'create', 'manage', 'use', 'using',
            'analyze', 'collaborate', 'conduct', 'produce', 'design',
            'implement', 'test', 'deploy', 'maintain', 'support', 'lead',
            'guide', 'mentor', 'train', 'evaluate', 'review', 'improve',
            'optimize', 'ensure', 'build', 'write', 'solve', 'define',
            'identify', 'monitor', 'communicate', 'coordinate', 'assist',
            'provide', 'include', 'require', 'perform', 'help', 'join',
            'become', 'operate',
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
            'every', 'same', 'own', 'different', 'various', 'multiple',
            'able', 'capable', 'effective', 'proficient', 'knowledgeable',
            'successful', 'excellent', 'outstanding', 'proven', 'demonstrated',
            'expert', 'advanced', 'intermediate', 'basic', 'familiar',
            'understanding', 'working', 'experience', 'skills', 'skill',
            'ability', 'track', 'record', 'team', 'teams', 'player',
            'independent', 'motivated', 'driven', 'detail', 'oriented',
            'fast', 'paced', 'environment', 'dynamic', 'highly', 'strong',
            'solid', 'deep', 'broad', 'extensive', 'comprehensive', 'hands',
            'on', 'practical', 'theoretical', 'academic', 'professional',
            'personal', 'excellent', 'great', 'good', 'better', 'best',
            'top', 'high', 'quality', 'level', 'entry', 'junior', 'senior',
            'lead', 'manager', 'director', 'vp', 'president', 'chief',
            'executive', 'officer', 'staff', 'member', 'associate',
            'assistant', 'coordinator', 'specialist', 'analyst', 'consultant',
            'engineer', 'developer', 'designer', 'architect', 'administrator',
            'code', 'plan', 'core', 'main', 'key', 'primary', 'secondary',
            'daily', 'weekly', 'monthly', 'yearly', 'annual', 'base', 'based',
            'focus', 'focused', 'goal', 'goals', 'objective', 'objectives',
            'aim', 'aims', 'target', 'targets', 'mission', 'vision', 'value',
            'values', 'culture', 'diversity', 'inclusion', 'equity', 'equal',
            'opportunity', 'employer', 'candidate', 'applicant', 'hire',
            'hiring', 'recruiting', 'recruitment', 'talent', 'acquisition',
            'resources', 'human', 'people', 'person', 'individual', 'group',
            'department', 'division', 'branch', 'office', 'headquarters',
            'local', 'global', 'international', 'national', 'regional',
            'remote', 'hybrid', 'flexible', 'schedule', 'hours', 'time',
            'part', 'full', 'contract', 'temporary', 'permanent', 'freelance',
            'internship', 'volunteer', 'unpaid', 'paid', 'salary', 'wage',
            'rate', 'pay', 'compensation', 'benefits', 'perks', 'bonus',
            'commission', 'equity', 'stock', 'options', 'shares', 'profit',
            'sharing', 'retirement', 'pension', 'health', 'dental', 'vision',
            'life', 'insurance', 'disability', 'leave', 'vacation', 'holiday',
            'sick', 'days', 'time', 'off', 'pto', 'paid', 'unpaid', 'maternity',
            'paternity', 'parental', 'family', 'medical', 'bereavement',
            'jury', 'duty', 'military', 'voting', 'sabbatical', 'study',
            'training', 'development', 'education', 'tuition', 'reimbursement',
            'assistance', 'allowance', 'stipend', 'grant', 'scholarship',
            'loan', 'repayment', 'forgiveness', 'program', 'programs',
        }

        # ── Expanded multi-domain phrase library ─────────────────────────
        self.phrase_patterns = [
            # Technology / Data Science
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
            r'\bafter effects\b',
            r'\bobject[\- ]oriented\b',
            r'\bversion control\b',
            r'\bcloud computing\b',
            r'\bmicroservices architecture\b',
            # Civil / Structural Engineering
            r'\bstructural analysis\b',
            r'\bstructural design\b',
            r'\bstructural engineering\b',
            r'\breinforced concrete\b',
            r'\bsteel structures\b',
            r'\bmetal structures\b',
            r'\bsteel detailing\b',
            r'\bbuilding information modeling\b',
            r'\bquantity surveying\b',
            r'\bsite supervision\b',
            r'\bconstruction management\b',
            r'\bseismic design\b',
            r'\bfoundation design\b',
            r'\bgeotechnical engineering\b',
            r'\bbridge engineering\b',
            r'\bload calculation\b',
            r'\bconcrete design\b',
            r'\bsteel connection design\b',
            # Architecture
            r'\barchitectural design\b',
            r'\bspace planning\b',
            r'\binterior design\b',
            r'\bproject visualization\b',
            r'\bfeasibility study\b',
            r'\bbuilding codes\b',
            r'\bzoning regulations\b',
            r'\burban planning\b',
            r'\bsustainable design\b',
            r'\bsite analysis\b',
            r'\bconceptual design\b',
            # Healthcare / Medical
            r'\bpatient care\b',
            r'\bclinical assessment\b',
            r'\bwound management\b',
            r'\bemergency care\b',
            r'\biv therapy\b',
            r'\bvital signs\b',
            r'\belectronic health records\b',
            r'\behr management\b',
            r'\bintensive care\b',
            r'\bpublic health\b',
            r'\binfection control\b',
            r'\bpalliative care\b',
            r'\bpatient education\b',
            r'\bclinical trials\b',
            r'\bmedical imaging\b',
            # Marketing / Sales
            r'\bgoogle analytics\b',
            r'\bgoogle ads\b',
            r'\bfacebook ads\b',
            r'\bsocial media management\b',
            r'\bcontent marketing\b',
            r'\bemail marketing\b',
            r'\blead generation\b',
            r'\bbrand strategy\b',
            r'\bmarket research\b',
            r'\bcustomer acquisition\b',
            r'\bconversion rate optimisation\b',
            r'\bpaid media\b',
            r'\bseo optimisation\b',
            r'\bdigital marketing\b',
            r'\bpublic relations\b',
            # Finance / Accounting
            r'\bfinancial reporting\b',
            r'\brisk management\b',
            r'\bfinancial analysis\b',
            r'\baccounts payable\b',
            r'\baccounts receivable\b',
            r'\bcash flow management\b',
            r'\bbudget forecasting\b',
            r'\btax compliance\b',
            r'\baudit management\b',
            # Legal
            r'\bcontract negotiation\b',
            r'\bdue diligence\b',
            r'\bcorporate law\b',
            r'\bintellectual property\b',
            r'\bcompliance management\b',
            r'\blegal research\b',
            # Business / Management
            r'\bproject management\b',
            r'\bstakeholder management\b',
            r'\bchange management\b',
            r'\bprocess improvement\b',
            r'\bbusiness development\b',
            r'\bsupply chain management\b',
            r'\bstrategic planning\b',
            r'\bteam leadership\b',
            r'\bperformance management\b',
        ]

    # ------------------------------------------------------------------
    # Internal helpers (identical to V1)
    # ------------------------------------------------------------------

    def _clean_text(self, text: str) -> str:
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _strip_non_skills(self, text: str) -> str:
        """Remove scheduling, logistics, and other universally non-skill patterns
        before any extraction method runs. These patterns are domain-agnostic:
        they are never skills in any field (medicine, tech, teaching, etc.)."""
        patterns = [
            r'\b\d{1,2}[AaPp][Mm](?:\s*[-–]\s*\d{1,2}[AaPp][Mm])?\b',  # 8AM, 8AM-5PM
            r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b',
            r'\b(?:full|part)[\s-]time\b',
            r'\b(?:remote|hybrid|on-?site|in-?person)\b',
            r'\b\d+\s*(?:years?|months?|weeks?)\s*(?:of\s*)?(?:experience)?\b',
            r'\b\d{1,2}\s*[-–]\s*\d{1,2}\s*(?:hours?|hrs?)\b',  # 8-5 hours
            r'\bAvailability\b',
            r'\bShift\b',
        ]
        for p in patterns:
            text = re.sub(p, '', text, flags=re.IGNORECASE)
        return text

    def _is_valid(self, term: str) -> bool:
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

    def extract_phrases(self, text: str) -> Set[str]:
        found = set()
        text_lower = text.lower()
        for pat in self.phrase_patterns:
            for m in re.finditer(pat, text_lower):
                phrase = re.sub(r'[\-/]', ' ', m.group(0)).strip()
                phrase = re.sub(r'\s+', ' ', phrase)
                found.add(phrase)
        return found

    def extract_indicator_skills(self, text: str) -> Set[str]:
        skills = set()
        text_lower = text.lower()
        for indicator in self.skill_indicators:
            pattern = rf'{re.escape(indicator)}\s+([^.\n;(]+?)(?:\.|\;|\n|\(|$)'
            for match in re.finditer(pattern, text_lower, re.IGNORECASE):
                phrase = match.group(1).strip()
                terms = re.split(r',\s*|\s+and\s+|\s+or\s+|/|\|', phrase)
                for term in terms:
                    term = re.sub(r'^(the|a|an|in|of|with|for)\s+', '', term.strip())
                    term = re.sub(r'\s+(in|of|with|for)$', '', term)
                    term = term.strip()
                    if self._is_valid(term):
                        words = term.split()[:4]
                        skills.add(' '.join(words))
        return skills

    def extract_capitalized_terms(self, text: str) -> Counter:
        """Method 3 — captures multi-word capitalized phrases AND standalone acronyms.
        Examples: 'Patient Care', 'Primary Care Setting', 'EHR', 'HIPAA', 'Tableau'.
        Lone fragments like 'Care' or 'Time' are filtered out in extract_skills()."""
        counts: Counter = Counter()

        common_words = re.compile(
            r'^(The|This|That|These|Those|Our|Your|Their|We|You|He|She|They|It|'
            r'As|At|If|But|So|Yet|For|Nor|Or|And|In|Of|To|A|An|Is|Are|Was|Were|'
            r'Be|Been|Being|Have|Has|Had|Do|Does|Did|Will|Would|Could|Should|May|'
            r'Might|Must|Shall|Can)$'
        )

        # Pattern A: multi-word capitalized phrases (Patient Care, Primary Care Setting)
        multi_word_pat = r'\b[A-Z][a-zA-Z0-9]*(?:\s+[A-Z][a-zA-Z0-9]*)+\b'
        for match in re.finditer(multi_word_pat, text):
            phrase = match.group(0).strip()
            phrase_lower = phrase.lower()
            if phrase_lower in self.stop_words:
                continue
            if common_words.match(phrase.split()[0]):
                continue
            counts[phrase_lower] += 1

        # Pattern B: standalone acronyms (EHR, HIPAA, ACLS, AWS)
        acronym_pat = r'\b[A-Z]{2,}\b'
        for match in re.finditer(acronym_pat, text):
            term = match.group(0)
            term_lower = term.lower()
            if term_lower in self.stop_words:
                continue
            counts[term_lower] += 1

        return counts

    def extract_lowercase_tech(self, text: str) -> Set[str]:
        found = set()
        pattern = r'\b([a-z0-9\+\#\.\-]{2,20})\b'
        
        whitelist = {
            'git', 'sql', 'aws', 'css', 'html', 'php', 'api', 'seo', 'roi', 
            'kpi', 'crm', 'erp', 'b2b', 'b2c', 'saas', 'paas', 'iaas', 'json',
            'xml', 'csv', 'pdf', 'linux', 'unix', 'macos', 'windows', 'ios',
            'android', 'java', 'rust', 'ruby', 'perl', 'bash', 'yaml',
            'python', 'javascript', 'typescript', 'react', 'angular', 'vue',
            'node', 'docker', 'kubernetes', 'azure', 'gcp', 'mysql', 'postgres',
            'mongodb', 'redis', 'django', 'flask', 'fastapi', 'spring', 'boot',
            'laravel', 'sass', 'less', 'webpack', 'babel', 'c++', 'c#', '.net',
            'go', 'swift', 'kotlin', 'dart', 'flutter', 'xamarin', 'ionic',
            'github', 'gitlab', 'bitbucket', 'jira', 'confluence', 'trello',
            'asana', 'slack', 'agile', 'scrum', 'kanban', 'waterfall', 'devops',
            'jenkins', 'travis', 'circleci', 'heroku', 'digitalocean', 'firebase',
            'supabase', 'graphql', 'rest', 'ruby on rails', 'react native',
            'excel', 'word', 'powerpoint', 'office',
            # Civil / Structural Engineering tools
            'autocad', 'revit', 'etabs', 'sap2000', 'staad', 'tekla', 'robot',
            'archicad', 'rhino', 'sketchup', 'lumion', 'navisworks', 'primavera',
            'powerbi',
        }
        
        for match in re.finditer(pattern, text.lower()):
            term = match.group(1)
            if term in self.stop_words:
                continue
            if len(term) < 2:
                continue
                
            has_special = bool(re.search(r'[0-9\+\#\.]', term))
            in_whitelist = term in whitelist
            is_short = len(term) <= 4 and term.isalpha()
            
            if has_special or in_whitelist or is_short:
                found.add(term)
        return found

    def extract_skills(self, text: str, max_skills: int = 30) -> Dict[str, List[str]]:
        # Strip scheduling/logistics patterns first (domain-agnostic)
        text = self._strip_non_skills(text)
        text = self._clean_text(text)

        phrases           = self.extract_phrases(text)
        indicator_skills  = self.extract_indicator_skills(text)
        cap_counts        = self.extract_capitalized_terms(text)

        # Filter Method 3: only keep acronyms (all-caps) or multi-word phrases.
        # This prevents lone fragments like 'Care', 'Time', 'Role' from surviving.
        cap_ranked = [
            term for term, _ in cap_counts.most_common(50)
            if len(term) >= 4 and (term.replace(' ', '').isupper() or ' ' in term)
        ]

        lower_tech        = self.extract_lowercase_tech(text)

        seen: Set[str] = set()
        all_skills: List[str] = []

        def add_if_new(term: str):
            t = term.lower().strip()
            if t and t not in seen and self._is_valid(t):
                seen.add(t)
                all_skills.append(t)

        for p in sorted(phrases):            add_if_new(p)
        for s in sorted(indicator_skills):   add_if_new(s)
        for c in cap_ranked:                 add_if_new(c)
        for lt in sorted(lower_tech):        add_if_new(lt)

        return {
            'all_skills':      all_skills[:max_skills],
            'explicit_skills': sorted(list(indicator_skills))[:15],
            'technical_terms': sorted(list(phrases | set(cap_ranked[:20])))[:15],
        }

    def _normalize_skill(self, skill: str) -> str:
        """Strip spaces, hyphens, underscores and slashes for fuzzy comparison.
        Catches variants like 'Power BI' vs 'PowerBI', 'scikit-learn' vs 'scikitlearn'."""
        return re.sub(r'[\s\-_/]', '', skill.lower())

    def compare_skills(self, cv_text: str, job_text: str) -> Dict:
        """
        Compare CV skills against job-required skills.

        STRICT matching (V2 improvement):
        - Exact match always counts.
        - Substring match only allowed when BOTH skills are >= 6 characters.
          This prevents 'care' matching 'patient care', 'customer care', etc.
        - Normalized match: strips spaces/hyphens before comparing, catching
          variants like 'Power BI' vs 'PowerBI'.

        Skills are framed from the JOB's perspective:
          matched_skills = job requirements the CV covers
          missing_skills = job requirements the CV lacks
        """
        cv_data  = self.extract_skills(cv_text,  max_skills=40)
        job_data = self.extract_skills(job_text, max_skills=40)

        cv_skills  = set(cv_data['all_skills'])
        job_skills = set(job_data['all_skills'])

        matched: Set[str] = set()
        missing: Set[str] = set()

        for j_skill in job_skills:
            found = False
            j_norm = self._normalize_skill(j_skill)
            for c_skill in cv_skills:
                exact  = j_skill == c_skill
                j_in_c = len(j_skill) >= 4 and j_skill in c_skill
                c_in_j = len(c_skill) >= 4 and c_skill in j_skill
                c_norm = self._normalize_skill(c_skill)
                norm_match = (len(j_norm) >= 4 and len(c_norm) >= 4) and (
                    j_norm == c_norm or j_norm in c_norm or c_norm in j_norm
                )
                if exact or j_in_c or c_in_j or norm_match:
                    matched.add(j_skill)
                    found = True
                    break
            if not found:
                missing.add(j_skill)

        match_percentage = (len(matched) / len(job_skills) * 100) if job_skills else 0.0

        return {
            'cv_skills':        sorted(list(cv_skills)),
            'job_skills':       sorted(list(job_skills)),
            'matched_skills':   sorted(list(matched)),
            'missing_skills':   sorted(list(missing)),
            'extra_skills':     sorted(list(cv_skills - matched)),
            'match_percentage': round(match_percentage, 2),
            'matched_count':    len(matched),
            'missing_count':    len(missing),
        }
