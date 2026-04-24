from typing import Dict, Tuple
import re

# ---------------------------------------------------------------------------
# Domain keyword taxonomy
# ---------------------------------------------------------------------------
DOMAIN_KEYWORDS: Dict[str, list] = {
    "healthcare": [
        "patient", "clinical", "nursing", "nurse", "cardiology", "surgery",
        "hospital", "physician", "doctor", "ehr", "emr", "acls", "iv therapy",
        "triage", "diagnosis", "medication", "pharmacy", "anatomy", "pathology",
        "radiology", "oncology", "pediatrics", "geriatrics", "wound care",
        "patient care", "vital signs", "emergency care", "medical", "healthcare",
        "intensive care", "icu", "bls", "cpr", "ward", "clinic", "dental",
        "therapist", "physiotherapy", "rehabilitation", "public health",
    ],
    "technology": [
        "python", "javascript", "typescript", "java", "c++", "c#", "golang",
        "software", "algorithm", "database", "sql", "nosql", "cloud", "aws",
        "azure", "gcp", "api", "rest", "graphql", "backend", "frontend",
        "machine learning", "deep learning", "neural network", "ai", "llm",
        "git", "docker", "kubernetes", "devops", "ci/cd", "linux", "bash",
        "react", "vue", "angular", "node", "django", "flask", "fastapi",
        "data science", "data engineering", "big data", "spark", "hadoop",
        "computer vision", "natural language processing", "tensorflow", "pytorch",
        "cybersecurity", "blockchain", "embedded systems", "iot",
    ],
    "marketing": [
        "seo", "sem", "campaign", "brand", "branding", "advertising",
        "social media", "market research", "copywriting", "content marketing",
        "conversion", "google analytics", "google ads", "facebook ads",
        "email marketing", "lead generation", "crm", "hubspot", "salesforce",
        "digital marketing", "influencer", "pr", "public relations",
        "storytelling", "engagement", "roi", "ctr", "impressions", "reach",
        "market strategy", "product launch", "b2b", "b2c", "growth hacking",
    ],
    "finance": [
        "accounting", "auditing", "budget", "forecasting", "investment",
        "portfolio", "gaap", "ifrs", "bookkeeping", "tax", "compliance",
        "revenue", "profit", "loss", "balance sheet", "income statement",
        "financial analysis", "risk management", "banking", "insurance",
        "equity", "debt", "valuation", "cfa", "cpa", "controller",
        "accounts payable", "accounts receivable", "payroll", "treasury",
        "financial reporting", "cost analysis", "cash flow",
    ],
    "legal": [
        "litigation", "contract", "attorney", "lawyer", "regulation",
        "statute", "jurisdiction", "arbitration", "compliance", "counsel",
        "paralegal", "law", "legal", "court", "plaintiff", "defendant",
        "intellectual property", "trademark", "patent", "copyright",
        "corporate law", "criminal law", "civil law", "negotiation",
        "due diligence", "mergers", "acquisitions", "gdpr", "data protection",
    ],
    "education": [
        "teaching", "curriculum", "pedagogy", "students", "classroom",
        "assessment", "lesson plan", "professor", "lecturer", "tutor",
        "school", "university", "learning outcomes", "e-learning",
        "instructional design", "training", "workshop", "seminar",
        "academic", "research", "thesis", "publication", "grading",
        "special education", "early childhood", "stem education",
    ],
    "engineering": [
        "mechanical", "electrical", "civil", "structural", "cad", "autocad",
        "manufacturing", "quality control", "circuit", "pcb", "embedded",
        "solidworks", "matlab", "plc", "scada", "hydraulics", "pneumatics",
        "materials science", "thermodynamics", "fluid dynamics", "welding",
        "3d printing", "product design", "tolerance", "iso standards",
        "construction", "geotechnical", "environmental engineering",
    ],
    "business": [
        "strategy", "operations", "consulting", "stakeholder", "agile",
        "scrum", "kpi", "leadership", "management", "supply chain",
        "logistics", "procurement", "vendor", "erp", "sap", "business analysis",
        "process improvement", "change management", "organizational",
        "executive", "entrepreneurship", "startup", "growth strategy",
        "business development", "partnership", "negotiation",
    ],
}

# ---------------------------------------------------------------------------
# Domain compatibility matrix
# ---------------------------------------------------------------------------
DOMAIN_COMPATIBILITY: Dict[str, Dict[str, float]] = {
    "healthcare": {
        "healthcare": 1.0, "technology":  0.1, "marketing":   0.0,
        "finance":    0.1, "legal":       0.2, "education":   0.3,
        "engineering":0.1, "business":    0.1,
    },
    "technology": {
        "healthcare": 0.1, "technology":  1.0, "marketing":   0.3,
        "finance":    0.3, "legal":       0.1, "education":   0.2,
        "engineering":0.6, "business":    0.3,
    },
    "marketing": {
        "healthcare": 0.0, "technology":  0.3, "marketing":   1.0,
        "finance":    0.2, "legal":       0.1, "education":   0.1,
        "engineering":0.0, "business":    0.6,
    },
    "finance": {
        "healthcare": 0.1, "technology":  0.3, "marketing":   0.2,
        "finance":    1.0, "legal":       0.5, "education":   0.1,
        "engineering":0.1, "business":    0.5,
    },
    "legal": {
        "healthcare": 0.2, "technology":  0.1, "marketing":   0.1,
        "finance":    0.5, "legal":       1.0, "education":   0.2,
        "engineering":0.1, "business":    0.3,
    },
    "education": {
        "healthcare": 0.3, "technology":  0.2, "marketing":   0.1,
        "finance":    0.1, "legal":       0.2, "education":   1.0,
        "engineering":0.1, "business":    0.2,
    },
    "engineering": {
        "healthcare": 0.1, "technology":  0.6, "marketing":   0.0,
        "finance":    0.1, "legal":       0.1, "education":   0.1,
        "engineering":1.0, "business":    0.2,
    },
    "business": {
        "healthcare": 0.1, "technology":  0.3, "marketing":   0.6,
        "finance":    0.5, "legal":       0.3, "education":   0.2,
        "engineering":0.2, "business":    1.0,
    },
}

AMBIGUOUS_DOMAIN_SCORE = 0.5

class DomainClassifier:
    def classify(self, text: str) -> Tuple[str, float]:
        text_lower = text.lower()
        text_lower = re.sub(r'\s+', ' ', text_lower)
        scores: Dict[str, int] = {domain: 0 for domain in DOMAIN_KEYWORDS}
        for domain, keywords in DOMAIN_KEYWORDS.items():
            for kw in keywords:
                if ' ' in kw:
                    if kw in text_lower:
                        scores[domain] += 2
                else:
                    pattern = rf'\b{re.escape(kw)}\b'
                    hits = len(re.findall(pattern, text_lower))
                    scores[domain] += hits
        total_hits = sum(scores.values())
        if total_hits < 2:
            return ('unknown', 0.0)
        best_domain = max(scores, key=scores.__getitem__)
        confidence = scores[best_domain] / total_hits if total_hits > 0 else 0.0
        return (best_domain, round(confidence, 3))

    def get_compatibility(self, cv_domain: str, job_domain: str) -> float:
        if cv_domain == 'unknown' or job_domain == 'unknown':
            return AMBIGUOUS_DOMAIN_SCORE
        row = DOMAIN_COMPATIBILITY.get(cv_domain, {})
        return row.get(job_domain, AMBIGUOUS_DOMAIN_SCORE)

    def score_pair(self, cv_text: str, job_text: str) -> Dict:
        cv_domain, cv_conf = self.classify(cv_text)
        job_domain, job_conf = self.classify(job_text)
        compatibility = self.get_compatibility(cv_domain, job_domain)
        return {
            'cv_domain':        cv_domain,
            'cv_confidence':    cv_conf,
            'job_domain':       job_domain,
            'job_confidence':   job_conf,
            'compatibility':    compatibility,
        }
