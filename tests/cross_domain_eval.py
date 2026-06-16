import sys
import os
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from preprocessing.document_parser import DocumentParser
from preprocessing.text_cleaning import TextCleaner
from embeddings.embedder import TextEmbedder
from vector_store.faiss_index import FAISSJobIndex
from matching.matcher_v2 import CVJobMatcherV2

# ── Setup ─────────────────────────────────────────────────────────────────────
parser        = DocumentParser()
text_cleaner  = TextCleaner()
text_embedder = TextEmbedder()
faiss_index   = FAISSJobIndex(embedding_dim=text_embedder.embedding_dim)
matcher       = CVJobMatcherV2(text_cleaner, text_embedder, faiss_index)

# Apply the Chosen (Phase 3) weights
matcher.set_weights(40, 20, 15, 15, 10)

domains  = ["data_analysis", "Marketing", "Medicine"]
base_dir = Path("data/raw")

# Domain display names for readability
domain_labels = {
    "data_analysis": "Data Analysis",
    "Marketing":     "Marketing",
    "Medicine":      "Medicine",
}

# ── Index all 15 job descriptions from all 3 domains ─────────────────────────
print("=== Indexing all 15 job descriptions ===")
job_ids, job_texts, job_domain_map = [], [], {}

for domain in domains:
    for f in sorted((base_dir / domain).iterdir()):
        if f.is_file() and "job_description" in f.name:
            text = parser.parse_file(str(f))
            if text:
                jid = f"{domain}_{f.stem}"
                job_ids.append(jid)
                job_texts.append(text)
                job_domain_map[jid] = domain

cleaned_jobs  = text_cleaner.clean_batch(job_texts)
cleaned_texts = [r['cleaned_text'] for r in cleaned_jobs]
embeddings    = text_embedder.embed_batch(cleaned_texts, show_progress=False)
faiss_index.add_jobs(job_embeddings=embeddings, job_ids=job_ids, job_texts=cleaned_texts)
print(f"Indexed {len(job_ids)} jobs.\n")

# ── All 6 CVs across all domains ─────────────────────────────────────────────
cv_queries = []
for domain in domains:
    for f in sorted((base_dir / domain).iterdir()):
        if f.is_file() and "sample_cv" in f.name:
            text = parser.parse_file(str(f))
            if text:
                cv_queries.append({
                    "label": f"{domain_labels[domain]} — {f.stem}",
                    "domain": domain,
                    "text": text
                })
print(f"Loaded {len(cv_queries)} CVs total.\n")

# ── Query each CV against all 15 jobs ────────────────────────────────────────
SEPARATOR = "=" * 70

for cv in cv_queries:
    print(SEPARATOR)
    print(f"  CV: {cv['label']} Candidate")
    print(f"  Querying against all 15 jobs (3 domains) — Top 5 results")
    print(SEPARATOR)

    result  = matcher.match_cv_to_jobs(cv_text=cv["text"], cv_id=cv["label"], top_k=15)
    matches = result.get("matches", [])

    print(f"  {'Rank':<6} {'Job ID':<45} {'Score':>7}  {'Domain':<16}  {'Correct?'}")
    print(f"  {'-'*4}  {'-'*43}  {'-'*7}  {'-'*14}  {'-'*8}")

    for rank, m in enumerate(matches[:5], 1):
        jid         = m['job_id']
        score       = m['score_breakdown']['final_hybrid']
        matched_dom = "unknown"
        for d in domains:
            if jid.startswith(d):
                matched_dom = d
                break
        is_correct  = "YES" if matched_dom == cv["domain"] else "NO "
        label       = domain_labels.get(matched_dom, matched_dom)
        short_jid   = jid.replace("data_analysis_", "DA_").replace("Marketing_", "MKT_").replace("Medicine_", "MED_")
        print(f"  #{rank:<5} {short_jid:<45} {score:>6.1f}%  {label:<16}  {is_correct}")

    # Summary
    top5_domains    = []
    for m in matches[:5]:
        jid = m['job_id']
        for d in domains:
            if jid.startswith(d):
                top5_domains.append(d)
                break
    correct_in_top5 = sum(1 for d in top5_domains if d == cv["domain"])
    top1_correct    = top5_domains[0] == cv["domain"] if top5_domains else False
    mrr = 0.0
    for rank, d in enumerate(top5_domains, 1):
        if d == cv["domain"]:
            mrr = 1.0 / rank
            break

    print(f"\n  Precision@1 : {'PASS' if top1_correct else 'FAIL'}")
    print(f"  Precision@5 : {correct_in_top5}/5  ({correct_in_top5/5*100:.0f}%)")
    print(f"  MRR         : {mrr:.3f}")
    print()

print(SEPARATOR)
print("  Configuration: Phase 3 Hybrid Scorer — weights 40/20/15/15/10")
print("  Dataset: 3 CVs x 15 jobs (5 DA + 5 MKT + 5 MED) = 45 CV-job pairs")
print(SEPARATOR)
