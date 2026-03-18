from typing import List, Set, Dict
import re
from collections import Counter

class SkillsExtractor:
    """
    Extract 10-15 core skills from text - conservative and high-quality approach.
    Focuses on technical skills, tools, and explicit competencies.
    """
    
    def __init__(self):
        """
        Initialize with skill indicators and extensive stop patterns.
        """
        # Skill indicators (words that signal a skill follows)
        self.skill_indicators = {
            'experience with', 'proficient in', 'skilled in', 'knowledge of',
            'familiar with', 'expertise in', 'expert in', 'certified in',
            'specialization in', 'trained in', 'competent in', 'mastery of',
            'proficiency in'
        }
        
        # Expanded common non-skill words to aggressively filter
        self.stop_words = {
            # Generic terms
            'experience', 'years', 'work', 'working', 'looking', 'seeking',
            'position', 'role', 'job', 'company', 'team', 'environment',
            'opportunity', 'responsibilities', 'requirements', 'qualifications',
            'description', 'summary', 'objective', 'education', 'degree',
            
            # Education terms
            'university', 'college', 'school', 'graduated', 'bachelor',
            'master', 'phd', 'diploma', 'certificate', 'student',
            
            # Location/time
            'location', 'date', 'month', 'year', 'day', 'time',
            'tirana', 'albania', 'remote', 'hybrid', 'onsite',
            
            # Generic descriptors
            'full', 'part', 'salary', 'benefits', 'apply', 'application',
            'excellent', 'strong', 'good', 'basic', 'advanced', 'intermediate',
            'ability', 'skills', 'skill', 'understanding', 'background',
            
            # Common verbs/connectors
            'and', 'or', 'with', 'for', 'the', 'of', 'in', 'to', 'a', 'an',
            'is', 'are', 'be', 'have', 'has', 'will', 'can', 'may',
            'work', 'working', 'develop', 'create', 'manage', 'use', 'using',
            
            # Business terms
            'company', 'organization', 'industry', 'business', 'professional',
            'candidate', 'applicant', 'employee', 'employer', 'intern',
            
            # Common verbs and generic nouns (Noise filters)
            'analyze', 'collaborate', 'conduct', 'produce', 'email', 'title',
            'knowledge', 'proficiency', 'familiarity', 'coordinator',
            'design', 'implement', 'test', 'deploy', 'maintain', 'support',
            'lead', 'guide', 'mentor', 'train', 'evaluate', 'review',
            'improve', 'optimize', 'increase', 'decrease', 'ensure',
            'responsible', 'capable', 'proven', 'track', 'record',
            'communication', 'written', 'verbal', 'interpersonal',
            'problem', 'solving', 'analytical', 'critical', 'thinking',
            'detail', 'oriented', 'multitask', 'prioritize', 'manage',
            'management', 'project', 'projects', 'product', 'products',
            'service', 'services', 'customer', 'customers', 'client', 'clients',
            'user', 'users', 'portfolio', 'online', 'website', 'web', 'page',
            'pages', 'site', 'sites', 'app', 'apps', 'application', 'applications',
            'system', 'systems', 'platform', 'platforms', 'tool', 'tools',
            'software', 'hardware', 'network', 'networks', 'server', 'servers',
            'result', 'results', 'data', 'information', 'report', 'reports',
            'record', 'records', 'file', 'files', 'document', 'documents',
            'form', 'forms', 'policy', 'policies', 'procedure', 'procedures',
            'process', 'processes', 'method', 'methods', 'practice', 'practices',
            'standard', 'standards', 'rule', 'rules', 'google', 'facebook'
        }
        
        # High-value technical terms (expanded list)
        self.technical_terms = {
            # Programming languages
            'python', 'java', 'javascript', 'typescript', 'c++', 'csharp', 'c#',
            'ruby', 'php', 'swift', 'kotlin', 'go', 'rust', 'scala', 'r',
            
            # Data & databases
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'oracle',
            'nosql', 'database', 'bigquery',
            
            # Web frameworks
            'react', 'angular', 'vue', 'nodejs', 'node.js', 'django', 'flask',
            'spring', 'laravel', 'express',
            
            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins',
            'terraform', 'ansible',
            
            # Data tools
            'tableau', 'powerbi', 'power bi', 'excel', 'spss', 'sas',
            'looker', 'qlik',
            
            # Web tech
            'html', 'css', 'bootstrap', 'tailwind', 'sass', 'webpack',
            
            # ML/AI
            'tensorflow', 'pytorch', 'scikit-learn', 'keras', 'pandas',
            'numpy', 'scipy', 'matplotlib', 'seaborn',
            
            # Version control & tools
            'git', 'github', 'gitlab', 'bitbucket', 'jira', 'confluence',
            
            # Marketing/Design tools
            'photoshop', 'illustrator', 'indesign', 'figma', 'sketch',
            'canva', 'premiere', 'after effects',
            'google analytics', 'google ads', 'facebook ads', 'seo', 'sem',
            'mailchimp', 'hubspot', 'salesforce',
            
            # Medical/Healthcare
            'ehr', 'emr', 'hipaa', 'icd', 'cpt', 'epic', 'cerner',
            'telemedicine', 'radiology', 'diagnostics',
            
            # Methodologies
            'agile', 'scrum', 'kanban', 'devops', 'cicd', 'ci/cd',
            'machine learning', 'deep learning', 'data analysis',
            'data science', 'statistical analysis'
        }
    
    def is_valid_skill(self, term: str) -> bool:
        """
        Check if a term is a valid skill (not noise).
        
        Args:
            term: Potential skill term
            
        Returns:
            True if valid skill
        """
        term_lower = term.lower().strip()
        
        # Filter out stop words
        if term_lower in self.stop_words:
            return False
        
        # Filter out single letters
        if len(term_lower) <= 1:
            return False
        
        # Filter out pure numbers
        if term_lower.isdigit():
            return False
        
        # Filter out terms that are mostly punctuation
        if len(re.findall(r'[a-z]', term_lower)) < 2:
            return False
        
        # Keep if it's a known technical term
        if term_lower in self.technical_terms:
            return True
        
        # Keep if it contains a known technical term
        for tech in self.technical_terms:
            if tech in term_lower:
                return True
        
        # Keep if it's alphanumeric (like "Python3", "C++")
        if re.search(r'[a-z]+[0-9#+\.]+', term_lower):
            return True
        
        # If it's longer than 3 chars and passed the stop word filter, 
        # it might be a multi-word explicit skill (e.g. "financial modeling")
        if len(term_lower.split()) > 1:
            return True
            
        
        return False
    
    def extract_explicit_skills(self, text: str) -> Set[str]:
        """
        Extract skills that are explicitly mentioned with skill indicators.
        
        Args:
            text: Text to analyze
            
        Returns:
            Set of explicitly mentioned skills
        """
        skills = set()
        text_lower = text.lower()
        
        for indicator in self.skill_indicators:
            # Pattern: "experience with Python, SQL, and Tableau"
            pattern = f'{re.escape(indicator)}\\s+([^.;]+?)(?:\\.|;|\\n|$)'
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            
            for match in matches:
                phrase = match.group(1).strip()
                # Split by common delimiters
                terms = re.split(r',\s*|\s+and\s+|\s+or\s+|/|\|', phrase)
                
                for term in terms:
                    term = term.strip()
                    # Clean up articles and prepositions
                    term = re.sub(r'^(the|a|an|in|of|with|for)\s+', '', term)
                    term = re.sub(r'\s+(in|of|with|for)$', '', term)
                    
                    if self.is_valid_skill(term):
                        # Keep only first 3 words max
                        words = term.split()[:3]
                        skills.add(' '.join(words))
        
        return skills
    
    def extract_technical_keywords(self, text: str) -> Set[str]:
        """
        Extract known technical terms that appear in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Set of technical keywords
        """
        skills = set()
        text_lower = text.lower()
        
        # Check for each known technical term
        for tech_term in self.technical_terms:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(tech_term) + r'\b'
            if re.search(pattern, text_lower):
                skills.add(tech_term)
        
        return skills
    
    def extract_dynamic_tools(self, text: str) -> set:
        """
        Extract capitalized terms or abbreviations natively.
        Using a robust stop-word list, this catches non-hardcoded 
        skills like 'Celery' from bulleted lists.
        """
        skills = set()
        
        # Matches Capitalized words or ALLCAPS words safely
        pattern = r'\b[A-Z][A-Za-z0-9+#\.]{1,}\b'
        matches = re.findall(pattern, text)
        
        for term in matches:
            term_lower = term.lower()
            if term_lower not in self.stop_words:
                skills.add(term_lower)
                
        return set(skills)
    
    def extract_skills(self, text: str, max_skills: int = 15) -> Dict[str, List[str]]:
        """
        Main method: Extract top 10-15 core skills from text.
        
        Args:
            text: Text to analyze
            max_skills: Maximum number of skills to return (default: 15)
            
        Returns:
            Dict with extracted skills
        """
        # Strategy 1: Explicit skills (high confidence)
        explicit = self.extract_explicit_skills(text)
        
        # Strategy 2: Known technical terms
        technical = self.extract_technical_keywords(text)
        
        # Strategy 3: Dynamic context terms (embedded capitalized proper nouns)
        dynamic = self.extract_dynamic_tools(text)
        
        # Combine explicitly mentioned, known tech terms, and dynamic proper nouns
        all_skills = list(explicit) + [t for t in technical if t not in explicit]
        all_skills += [d for d in dynamic if d not in explicit and d not in technical]
        
        # Deduplicate and limit to max_skills
        unique_skills = []
        seen = set()
        for skill in all_skills:
            skill_lower = skill.lower()
            if skill_lower not in seen:
                unique_skills.append(skill)
                seen.add(skill_lower)
                if len(unique_skills) >= max_skills:
                    break
        
        return {
            'all_skills': unique_skills[:max_skills],
            'explicit_skills': list(explicit)[:10],
            'technical_terms': list(technical)[:10]
        }
    
    def compare_skills(self, cv_text: str, job_text: str) -> Dict:
        """
        Compare core skills between CV and job description.
        
        Args:
            cv_text: CV text
            job_text: Job description text
            
        Returns:
            Dict with comparison results
        """
        cv_skills_data = self.extract_skills(cv_text, max_skills=15)
        job_skills_data = self.extract_skills(job_text, max_skills=15)
        
        cv_skills = set([s.lower() for s in cv_skills_data['all_skills']])
        job_skills = set([s.lower() for s in job_skills_data['all_skills']])
        
        matched = cv_skills.intersection(job_skills)
        missing = job_skills - cv_skills
        extra = cv_skills - job_skills
        
        # Calculate match percentage
        if len(job_skills) > 0:
            match_percentage = (len(matched) / len(job_skills)) * 100
        else:
            match_percentage = 0.0
        
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