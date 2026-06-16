"""
run_all_evaluations.py
----------------------
Auto-scans every domain folder in data/raw/, runs each CV against every JD
using the full 5-signal CVJobMatcherV2, and saves results/full_evaluation.csv.

File classification rules:
  - Contains 'job' or 'administrative_assistant' in filename → JD
  - Contains 'cv', 'sample', 'europass', or 'resume'        → CV
  - Any .docx / .pdf with no 'job' keyword                  → CV (person-name files)
  - .txt without any keyword match                           → skip
  - Known junk names (fghj, fgyhu, desktop)                 → skip
"""

import os
import sys
import csv

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from preprocessing.text_cleaning import TextCleaner
from preprocessing.document_parser import DocumentParser
from embeddings.embedder import TextEmbedder
from vector_store.faiss_index import FAISSJobIndex
from matching.matcher_v2 import CVJobMatcherV2

# ── File-type detection ─────────────────────────────────────────────────────

VALID_EXTS  = {'.txt', '.docx', '.pdf'}
JD_KEYWORDS = {'job', 'administrative_assistant'}
CV_KEYWORDS = {'cv', 'sample', 'europass', 'resume'}
JUNK_STEMS  = {'fghj', 'fgyhu', 'desktop'}


def classify_file(fname: str) -> str:
    ext   = os.path.splitext(fname)[1].lower()
    stem  = os.path.splitext(fname)[0].lower()
    lower = fname.lower()

    if ext not in VALID_EXTS:
        return 'skip'
    if any(j in stem for j in JUNK_STEMS):
        return 'skip'
    if any(k in lower for k in JD_KEYWORDS):
        return 'jd'
    if any(k in lower for k in CV_KEYWORDS):
        return 'cv'
    # Person-name PDFs / DOCXs with no 'job' keyword → treat as CV
    if ext in {'.docx', '.pdf'}:
        return 'cv'
    return 'skip'


def fit_category(score: float) -> str:
    if score >= 70:
        return 'Strong'
    if score >= 40:
        return 'Moderate'
    return 'Weak'


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    base_dir   = os.path.dirname(os.path.abspath(__file__))
    raw_dir    = os.path.join(base_dir, 'data', 'raw')
    output_dir = os.path.join(base_dir, 'results')
    os.makedirs(output_dir, exist_ok=True)
    out_path   = os.path.join(output_dir, 'full_evaluation.csv')

    cleaner  = TextCleaner(remove_emails=True, remove_phone=True,
                           remove_urls=True, min_length=50)
    parser   = DocumentParser()
    embedder = TextEmbedder(model_name='all-MiniLM-L6-v2')

    fieldnames = ['domain', 'cv_filename', 'jd_filename', 'jd_level', 'score', 'category']
    rows = []

    domain_dirs = sorted(
        d for d in os.listdir(raw_dir)
        if os.path.isdir(os.path.join(raw_dir, d))
    )

    for domain in domain_dirs:
        domain_dir = os.path.join(raw_dir, domain)
        all_files  = os.listdir(domain_dir)

        cv_files = sorted(f for f in all_files if classify_file(f) == 'cv')
        jd_files = sorted(f for f in all_files if classify_file(f) == 'jd')

        if not cv_files:
            print(f"\n[{domain}] SKIP — no CV files detected")
            continue
        if not jd_files:
            print(f"\n[{domain}] SKIP — no JD files detected")
            continue

        print(f"\n[{domain}]")
        print(f"  CVs ({len(cv_files)}): {cv_files}")
        print(f"  JDs ({len(jd_files)}): {jd_files}")

        # ── Parse & index JDs ──────────────────────────────────────────────
        jd_texts, jd_ids, jd_fnames = [], [], []
        for jd_file in jd_files:
            text = parser.parse_file(os.path.join(domain_dir, jd_file))
            if text:
                jd_texts.append(text)
                jd_ids.append(os.path.splitext(jd_file)[0])
                jd_fnames.append(jd_file)
            else:
                print(f"  PARSE FAIL (JD): {jd_file}")

        if not jd_texts:
            print(f"  No parseable JDs — skipping domain.")
            continue

        cleaned_jds = cleaner.clean_batch(jd_texts)
        if not cleaned_jds:
            print(f"  All JD texts too short after cleaning — skipping domain.")
            continue

        clean_jd_texts  = [r['cleaned_text']               for r in cleaned_jds]
        valid_jd_ids    = [jd_ids[r['original_index']]     for r in cleaned_jds]
        valid_jd_fnames = [jd_fnames[r['original_index']]  for r in cleaned_jds]

        embeddings = embedder.embed_batch(clean_jd_texts, show_progress=False)
        index      = FAISSJobIndex(embedding_dim=embedder.embedding_dim)
        index.add_jobs(job_embeddings=embeddings,
                       job_ids=valid_jd_ids, job_texts=clean_jd_texts)
        matcher = CVJobMatcherV2(cleaner, embedder, index)

        # ── Match each CV against all JDs ──────────────────────────────────
        for cv_file in cv_files:
            cv_text = parser.parse_file(os.path.join(domain_dir, cv_file))
            if not cv_text:
                print(f"  PARSE FAIL (CV): {cv_file}")
                continue

            result    = matcher.match_cv_to_jobs(cv_text=cv_text, cv_id=cv_file,
                                                 top_k=len(valid_jd_ids))
            score_map = {
                m['job_id']: round(m['score_breakdown']['final_hybrid'], 1)
                for m in result.get('matches', [])
            }

            for jd_id, jd_fname in zip(valid_jd_ids, valid_jd_fnames):
                score = score_map.get(jd_id, 0.0)
                cat   = fit_category(score)
                rows.append({
                    'domain':      domain,
                    'cv_filename': cv_file,
                    'jd_filename': jd_fname,
                    'jd_level':    jd_id,
                    'score':       score,
                    'category':    cat,
                })
                print(f"    {cv_file[:38]:38s}  ×  {jd_fname[:38]:38s}  {score:5.1f}  {cat}")

    # ── Save CSV ───────────────────────────────────────────────────────────
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n{'='*72}")
    print(f"Total pairs evaluated: {len(rows)}")
    print(f"Saved -> {out_path}")

    # ── Domain summary ────────────────────────────────────────────────────
    print(f"\n{'DOMAIN':<42} {'N':>3}  {'Strong':>6}  {'Moderate':>8}  {'Weak':>4}")
    print('-' * 72)
    for d in sorted(set(r['domain'] for r in rows)):
        sub       = [r for r in rows if r['domain'] == d]
        ns, nm, nw = (sum(1 for r in sub if r['category'] == c)
                      for c in ('Strong', 'Moderate', 'Weak'))
        print(f"  {d:<40} {len(sub):>3}  {ns:>6}  {nm:>8}  {nw:>4}")

    total_s = sum(1 for r in rows if r['category'] == 'Strong')
    total_m = sum(1 for r in rows if r['category'] == 'Moderate')
    total_w = sum(1 for r in rows if r['category'] == 'Weak')
    print('-' * 72)
    print(f"  {'TOTAL':<40} {len(rows):>3}  {total_s:>6}  {total_m:>8}  {total_w:>4}")


if __name__ == '__main__':
    main()
