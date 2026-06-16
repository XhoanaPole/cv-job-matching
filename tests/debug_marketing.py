import sys
import os
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from preprocessing.document_parser import DocumentParser
from preprocessing.text_cleaning import TextCleaner
from embeddings.embedder import TextEmbedder
from vector_store.faiss_index import FAISSJobIndex
from matching.matcher_v2 import CVJobMatcherV2

parser       = DocumentParser()
text_cleaner = TextCleaner()
text_embedder= TextEmbedder()
faiss_index  = FAISSJobIndex(embedding_dim=text_embedder.embedding_dim)
matcher      = CVJobMatcherV2(text_cleaner, text_embedder, faiss_index)

# Load all 15 job descriptions
base_dir = Path("data/raw")
domains  = ["data_analysis", "Marketing", "Medicine"]

job_ids, job_texts = [], []
for domain in domains:
    for f in (base_dir / domain).iterdir():
        if f.is_file() and "job_description" in f.name:
            text = parser.parse_file(str(f))
            if text:
                job_ids.append(f"{domain}_{f.name}")
                job_texts.append(text)

cleaned_jobs   = text_cleaner.clean_batch(job_texts)
cleaned_texts  = [r['cleaned_text'] for r in cleaned_jobs]
embeddings     = text_embedder.embed_batch(cleaned_texts, show_progress=False)
faiss_index.add_jobs(job_embeddings=embeddings, job_ids=job_ids, job_texts=cleaned_texts)

# Apply the Chosen weights
matcher.set_weights(40, 20, 15, 15, 10)

# Load the Marketing CV
mkt_cv_path = base_dir / "Marketing" / "sample_cv_marketing.txt"
mkt_cv_text = parser.parse_file(str(mkt_cv_path))

result  = matcher.match_cv_to_jobs(cv_text=mkt_cv_text, cv_id="Marketing_CV", top_k=15)
matches = result.get('matches', [])

print("\n=== Top-3 Matches for Marketing CV (Chosen weights: 40/20/15/15/10) ===\n")
for i, m in enumerate(matches[:3], 1):
    bd = m['score_breakdown']
    print(f"Rank #{i}")
    print(f"  job_id        : {m['job_id']}")
    print(f"  Hybrid Score  : {bd['final_hybrid']} / 100")
    print(f"  Semantic pts  : {bd['semantic_points']} / 40   (raw FAISS: {bd['raw_faiss_pct']}%)")
    print(f"  Skills pts    : {bd['skills_points']} / 20   (overlap: {bd['raw_skills_pct']}%)")
    print(f"  Domain pts    : {bd['domain_points']} / 15")
    print(f"  Education pts : {bd['education_points']} / 15")
    print(f"  Seniority pts : {bd['seniority_points']} / 10")
    print(f"  CV domain     : {bd.get('cv_domain')}  ->  Job domain: {bd.get('job_domain')}")
    print(f"  Fit category  : {m['fit_category'].upper()}")
    print()
