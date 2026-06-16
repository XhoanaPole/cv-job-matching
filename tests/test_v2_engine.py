import sys
import os

# Add src to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from preprocessing.text_cleaning import TextCleaner
from embeddings.embedder import TextEmbedder
from vector_store.faiss_index import FAISSJobIndex
from matching.matcher_v2 import CVJobMatcherV2

print("=== Loading Engine ===")
text_cleaner = TextCleaner()
text_embedder = TextEmbedder()
faiss_index = FAISSJobIndex(embedding_dim=text_embedder.embedding_dim)

matcher_v2 = CVJobMatcherV2(text_cleaner, text_embedder, faiss_index)

print("\n=== Adding Jobs to Vector Store ===")
job_marketing = """
Looking for a Senior SEO Marketing Manager to lead our performance marketing team. 
Must have 5+ years of experience with Google Analytics, Google Ads, and overall strategy.
You will run campaign execution, branding, and conversion rate optimization (CRO)
to maximize ROI. Master's degree preferred but not required.
"""

job_healthcare = """
Hiring a Clinical Nurse for our Pediatric Cardiology unit. 
Must have valid nursing license, CPR, ACLS, and vital signs assessment experience.
Patient care and wound management are required daily responsibilities. 
Bachelor's degree required.
"""

# Embed and add jobs to the isolated FAISS structure
cleaned_jobs = text_cleaner.clean_batch([job_marketing, job_healthcare])
cleaned_texts = [r['cleaned_text'] for r in cleaned_jobs]
job_embeddings = text_embedder.embed_batch(cleaned_texts, show_progress=False)

faiss_index.add_jobs(
    job_embeddings=job_embeddings, 
    job_ids=["job_marketing_1", "job_healthcare_1"], 
    job_texts=cleaned_texts
)

print("\n=== Testing Candidate CV ===")
nurse_cv = """
I am a clinical nurse with a Bachelor's degree and 3 years of experience in an intensive care setting.
Specialized in patient care, administering medication, wound management, and vital signs monitoring.
Certifications: ACLS, BLS.
Looking to advance my clinical assessment skills in a fast-paced hospital ward.
Junior level to mid-level.
"""

# Test the matcher
results = matcher_v2.match_cv_to_jobs(
    cv_text=nurse_cv,
    cv_id="Nurse_Jane_Doe_CV",
    top_k=2
)

print(f"\n--- Results for: {results['cv_id']} ---")
for match in results['matches']:
    print(f"\nComparing to Job:     {match['job_id']}")
    print(f"Overall Fit Category: {match['fit_category'].upper()}")
    
    bd = match['score_breakdown']
    print(f"Final Hybrid Score:   {bd['final_hybrid']}%")
    print(f"  - Semantic points : {bd['semantic_points']} / 40  (Raw FAISS: {bd['raw_faiss_pct']}%)")
    print(f"  - Skills points   : {bd['skills_points']} / 20  (Overlap: {bd['raw_skills_pct']}%)")
    print(f"  - Domain points   : {bd['domain_points']} / 15")
    print(f"  - Education points: {bd['education_points']} / 15")
    print(f"  - Seniority points: {bd['seniority_points']} / 10")
    
    print("\n  [Profile View]")
    print(f"  CV Domain vs Job Domain : {bd.get('cv_domain')} vs {bd.get('job_domain')}  (Compat: {bd.get('domain_compatibility')})")
    print(f"  CV Edu vs Job Edu       : {bd.get('cv_education')} vs {bd.get('job_education')}")
    print(f"  CV Level vs Job Level   : {bd.get('cv_seniority')} vs {bd.get('job_seniority')}")
