"""
run_all_pairs.py
Runs the hybrid scoring system for every CV × JD combination across all domains.
Outputs results to run_all_results.csv and prints a live summary table.
"""

import sys, os, csv, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from preprocessing.text_cleaning  import TextCleaner
from preprocessing.document_parser import DocumentParser
from embeddings.embedder           import TextEmbedder
from vector_store.faiss_index      import FAISSJobIndex
from matching.matcher_v2           import CVJobMatcherV2

BASE = os.path.dirname(os.path.abspath(__file__))
RAW  = os.path.join(BASE, 'data', 'raw')

# ---------------------------------------------------------------------------
# File-type helpers
# ---------------------------------------------------------------------------
CV_KEYWORDS  = ['cv', 'resume', 'candidate', 'krasniqi', 'marku', 'bendo',
                 'hoxha', 'basha', 'gjoka', 'cela', 'leka', 'pole', 'nushi',
                 'dervishi', 'hasa', 'koci', 'rama', 'kasmi', 'shehu', 'bala',
                 'zekthi', 'rivaldo', 'ardit', 'elira', 'albi', 'arta', 'drin',
                 'erion', 'blerina', 'arben', 'ilir', 'anxhela', 'rina',
                 'sample_cv', 'sample_cv_1', 'sample_cv_2', 'cv_1', 'cv_2',
                 'cv_arben', 'social_work_cv', 'psychology_cv', 'dentistry_cv',
                 'gentian', 'mirela', 'klevis', 'besnik']

JD_KEYWORDS  = ['job_description', 'job_descriprtion', 'job_desciprion',
                 'administrative_assistant']


def classify_file(filename: str):
    name = filename.lower().replace(' ', '_')
    stem = os.path.splitext(name)[0]
    for kw in JD_KEYWORDS:
        if kw in stem:
            return 'jd'
    for kw in CV_KEYWORDS:
        if kw in stem:
            return 'cv'
    return 'unknown'


SUPPORTED_EXT = {'.txt', '.docx', '.pdf'}


def list_domain_files(domain_path: str):
    cvs, jds = [], []
    try:
        for fname in sorted(os.listdir(domain_path)):
            ext = os.path.splitext(fname)[1].lower()
            if ext not in SUPPORTED_EXT:
                continue
            kind = classify_file(fname)
            full = os.path.join(domain_path, fname)
            if kind == 'cv':
                cvs.append((fname, full))
            elif kind == 'jd':
                jds.append((fname, full))
    except Exception:
        pass
    return cvs, jds


def fit_symbol(category: str) -> str:
    return {'strong fit': 'STRONG', 'moderate fit': 'MOD',
            'weak fit': 'WEAK'}.get(category, category.upper())


def main():
    print("Initialising models (this takes ~30s on first run)...")
    cleaner  = TextCleaner(remove_emails=True, remove_phone=True,
                            remove_urls=True, min_length=50)
    embedder = TextEmbedder(model_name='all-MiniLM-L6-v2')
    parser   = DocumentParser()

    domains = sorted([
        d for d in os.listdir(RAW)
        if os.path.isdir(os.path.join(RAW, d)) and d != 'desktop.ini'
    ])

    out_path = os.path.join(BASE, 'run_all_results.csv')
    fieldnames = [
        'domain', 'cv_file', 'jd_file',
        'score', 'category',
        'cv_seniority', 'jd_seniority', 'seniority_diff',
        'cap_applied',
        'semantic_pts', 'skills_pts', 'domain_pts', 'edu_pts', 'sen_pts',
        'raw_faiss_pct', 'raw_skills_pct',
    ]

    hdr = f"{'Domain':<28} {'CV':<35} {'JD':<40} {'Score':>6}  {'Cat':<8}"
    print('\n' + hdr)
    print('-' * len(hdr))

    total = ok = skip = 0

    with open(out_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for domain_name in domains:
            domain_path = os.path.join(RAW, domain_name)
            cvs, jds = list_domain_files(domain_path)

            if not cvs:
                print(f"  [SKIP] {domain_name} — no CV files detected")
                continue
            if not jds:
                print(f"  [SKIP] {domain_name} — no JD files detected")
                continue

            for (cv_fname, cv_full) in cvs:
                cv_text = parser.parse_file(cv_full)
                if not cv_text or len(cv_text.strip()) < 50:
                    print(f"  [SKIP] {cv_full} — empty/unparseable")
                    skip += 1
                    continue

                for (jd_fname, jd_full) in jds:
                    jd_text = parser.parse_file(jd_full)
                    if not jd_text or len(jd_text.strip()) < 50:
                        print(f"  [SKIP] {jd_full} — empty/unparseable")
                        skip += 1
                        continue

                    cleaned_jd   = cleaner.clean(jd_text)
                    jd_embedding = embedder.embed_single(cleaned_jd).reshape(1, -1)
                    idx = FAISSJobIndex(embedding_dim=embedder.embedding_dim)
                    idx.add_jobs(
                        job_embeddings=jd_embedding,
                        job_ids=['jd'],
                        job_texts=[cleaned_jd],
                    )

                    matcher = CVJobMatcherV2(cleaner, embedder, idx)
                    result  = matcher.match_cv_to_jobs(cv_text=cv_text, cv_id='cv', top_k=1)

                    if not result.get('matches'):
                        skip += 1
                        continue

                    match = result['matches'][0]
                    bd    = match.get('score_breakdown', {})
                    score = bd.get('final_hybrid', 0)
                    cat   = fit_symbol(match.get('fit_category', '?'))

                    print(
                        f"{domain_name:<28} {cv_fname:<35} {jd_fname:<40} "
                        f"{score:>5.1f}%  {cat:<8}"
                    )

                    writer.writerow({
                        'domain':        domain_name,
                        'cv_file':       cv_fname,
                        'jd_file':       jd_fname,
                        'score':         round(score, 2),
                        'category':      cat,
                        'cv_seniority':  bd.get('cv_seniority', ''),
                        'jd_seniority':  bd.get('job_seniority', ''),
                        'seniority_diff': '',
                        'cap_applied':   'YES' if bd.get('seniority_cap_applied') else '',
                        'semantic_pts':  bd.get('semantic_points', ''),
                        'skills_pts':    bd.get('skills_points', ''),
                        'domain_pts':    bd.get('domain_points', ''),
                        'edu_pts':       bd.get('education_points', ''),
                        'sen_pts':       bd.get('seniority_points', ''),
                        'raw_faiss_pct': bd.get('raw_faiss_pct', ''),
                        'raw_skills_pct': bd.get('raw_skills_pct', ''),
                    })
                    csvfile.flush()
                    total += 1
                    ok    += 1

    print(f'\nDone. {ok} pairs scored, {skip} skipped.')
    print(f'Results saved to: {out_path}')


if __name__ == '__main__':
    t0 = time.time()
    main()
    print(f'Total time: {time.time()-t0:.0f}s')
