"""
run_ablation_semantic.py
------------------------
Ablation: Version A (lexical-only skills matching) vs
          Version B (lexical + semantic fallback at threshold 0.80).

Runs both versions over the same 27 CV-JD pairs that have human ground-truth
labels (the same pairs used in ablation_study.py), then prints a comparison
table and saves two detail CSVs.

Usage:
    python run_ablation_semantic.py
"""

import sys
import os
import csv
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from preprocessing.text_cleaning  import TextCleaner
from preprocessing.document_parser import DocumentParser
from embeddings.embedder           import TextEmbedder
from vector_store.faiss_index      import FAISSJobIndex
from matching.matcher_v2           import CVJobMatcherV2

# ─────────────────────────────────────────────────────────────────────────────
# 1. DOMAIN FILE MANIFEST  (identical to ablation_study.py)
# ─────────────────────────────────────────────────────────────────────────────
DOMAINS = {
    'Data Analysis': {
        'cvs': [
            {'name': 'Data_Analyst', 'file': 'data/raw/data_analysis/sample_cv_d_analytics.txt'},
        ],
        'jds': [
            {'id': 'JD1_Entry',  'file': 'data/raw/data_analysis/job_description_1_d_analytics.txt', 'level': 'Entry'},
            {'id': 'JD2_Mid',    'file': 'data/raw/data_analysis/job_description_2_d_analytics.txt', 'level': 'Mid'},
            {'id': 'JD3_Senior', 'file': 'data/raw/data_analysis/job_description_3_d_analytics.txt', 'level': 'Senior'},
        ],
    },
    'Marketing': {
        'cvs': [
            {'name': 'Andi_Shehu', 'file': 'data/raw/Marketing/sample_cv_marketing.txt'},
        ],
        'jds': [
            {'id': 'JD1_Entry', 'file': 'data/raw/Marketing/job_description_1_marketing.txt', 'level': 'Entry'},
            {'id': 'JD2_Mid',   'file': 'data/raw/Marketing/job_description_2_marketing.txt', 'level': 'Mid'},
            {'id': 'JD3_FMCG',  'file': 'data/raw/Marketing/job_description_3_marketing.txt', 'level': 'FMCG'},
        ],
    },
    'Medicine': {
        'cvs': [
            {'name': 'Maria_Kola', 'file': 'data/raw/Medicine/sample_cv_version_b_med.txt'},
        ],
        'jds': [
            {'id': 'JD1_Mid',    'file': 'data/raw/Medicine/job_description_1med.txt',   'level': 'Mid'},
            {'id': 'JD2_Entry',  'file': 'data/raw/Medicine/job_description_2_med.docx', 'level': 'Entry'},
            {'id': 'JD3_Senior', 'file': 'data/raw/Medicine/job_description_3.docx',     'level': 'Senior'},
        ],
    },
    'Human Resources': {
        'cvs': [
            {'name': 'Erisa',  'file': 'data/raw/Human Resources/sample_cv_1.txt'},
            {'name': 'Klajdi', 'file': 'data/raw/Human Resources/sample_cv_2.txt'},
        ],
        'jds': [
            {'id': 'JD1_Entry',  'file': 'data/raw/Human Resources/job_description_1_hr.txt',   'level': 'Entry'},
            {'id': 'JD2_Mid',    'file': 'data/raw/Human Resources/job_description_2_hr.docx',  'level': 'Mid'},
            {'id': 'JD3_Senior', 'file': 'data/raw/Human Resources/job_description_3_hr.txt',   'level': 'Senior'},
        ],
    },
    'Finance': {
        'cvs': [
            {'name': 'Besa',  'file': 'data/raw/Finance/sample_cv_1.txt'},
            {'name': 'Endri', 'file': 'data/raw/Finance/sample_cv_2.docx'},
        ],
        'jds': [
            {'id': 'JD1_Entry',  'file': 'data/raw/Finance/job_description_1_finance.txt',  'level': 'Entry'},
            {'id': 'JD2_Senior', 'file': 'data/raw/Finance/job_description_2_finance.txt',  'level': 'Senior'},
            {'id': 'JD3_Mid',    'file': 'data/raw/Finance/job_description_3_finance.docx', 'level': 'Mid'},
        ],
    },
    'Software Engineering': {
        'cvs': [
            {'name': 'Ardit', 'file': 'data/raw/software_engineering/sample_cv_1.txt'},
            {'name': 'Klea',  'file': 'data/raw/software_engineering/sample_cv_2.docx'},
        ],
        'jds': [
            {'id': 'JD1_Senior',   'file': 'data/raw/software_engineering/job_description_1_sftw.txt',  'level': 'Senior'},
            {'id': 'JD2_Mid',      'file': 'data/raw/software_engineering/job_desciprion_2_sftw.docx',  'level': 'Mid'},
            {'id': 'JD3_GoSenior', 'file': 'data/raw/software_engineering/job_description_3_sftw.txt',  'level': 'GoSenior'},
        ],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# 2. GROUND TRUTH  (identical to ablation_study.py)
# ─────────────────────────────────────────────────────────────────────────────
GROUND_TRUTH = {
    'Data Analysis': {
        'Data_Analyst': {'JD1_Entry': 'Strong', 'JD2_Mid': 'Moderate', 'JD3_Senior': 'Weak'},
    },
    'Marketing': {
        'Andi_Shehu': {'JD1_Entry': 'Moderate', 'JD2_Mid': 'Strong', 'JD3_FMCG': 'Moderate'},
    },
    'Medicine': {
        'Maria_Kola': {'JD1_Mid': 'Moderate', 'JD2_Entry': 'Strong', 'JD3_Senior': 'Weak'},
    },
    'Human Resources': {
        'Erisa':  {'JD1_Entry': 'Strong', 'JD2_Mid': 'Weak', 'JD3_Senior': 'Weak'},
        'Klajdi': {'JD1_Entry': 'Strong', 'JD2_Mid': 'Weak', 'JD3_Senior': 'Weak'},
    },
    'Finance': {
        'Besa':  {'JD1_Entry': 'Strong', 'JD2_Senior': 'Weak', 'JD3_Mid': 'Moderate'},
        'Endri': {'JD1_Entry': 'Strong', 'JD2_Senior': 'Weak', 'JD3_Mid': 'Weak'},
    },
    'Software Engineering': {
        'Ardit': {'JD1_Senior': 'Weak', 'JD2_Mid': 'Moderate', 'JD3_GoSenior': 'Weak'},
        'Klea':  {'JD1_Senior': 'Weak', 'JD2_Mid': 'Moderate', 'JD3_GoSenior': 'Weak'},
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# 3. HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def category_from_score(score: float) -> str:
    if score >= 70:
        return 'Strong'
    elif score >= 40:
        return 'Moderate'
    return 'Weak'


def run_version(version_label: str, semantic_skills: bool,
                cleaner, embedder, doc_parser,
                domain_data: dict) -> list:
    """
    Score all pairs for one version configuration.
    Returns a list of result dicts, one per CV-JD pair.
    """
    rows = []
    for domain_name, data in domain_data.items():
        temp_index = FAISSJobIndex(embedding_dim=embedder.embedding_dim)
        temp_index.add_jobs(
            job_embeddings=data['jd_embeds'],
            job_ids=data['jd_ids'],
            job_texts=data['jd_texts'],
        )

        matcher = CVJobMatcherV2(
            cleaner, embedder, temp_index,
            semantic_skills=semantic_skills,
        )

        gt_domain = GROUND_TRUTH.get(domain_name, {})

        for cv_name, cv_text in data['cv_texts'].items():
            result = matcher.match_cv_to_jobs(
                cv_text=cv_text,
                cv_id=cv_name,
                top_k=len(data['jd_ids']),
            )
            gt_cv = gt_domain.get(cv_name, {})

            for match in result.get('matches', []):
                jid   = match['job_id']
                bd    = match['score_breakdown']
                score = bd['final_hybrid']
                cat   = category_from_score(score)
                gt    = gt_cv.get(jid, '?')
                correct = (cat == gt)

                rows.append({
                    'version':      version_label,
                    'domain':       domain_name,
                    'cv_name':      cv_name,
                    'jd_id':        jid,
                    'score':        round(score, 2),
                    'system_cat':   cat,
                    'human_label':  gt,
                    'correct':      'YES' if correct else 'NO',
                    'skills_pct':   round(bd.get('raw_skills_pct', 0), 2),
                    'skills_pts':   round(bd.get('skills_points', 0), 2),
                })

    return rows


# ─────────────────────────────────────────────────────────────────────────────
# 4. MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    t0 = time.time()
    print("=" * 70)
    print("ABLATION: Version A (lexical) vs Version B (lexical + semantic)")
    print("=" * 70)

    print("\nLoading shared components...")
    cleaner    = TextCleaner(remove_emails=True, remove_phone=True,
                             remove_urls=True, min_length=50)
    embedder   = TextEmbedder(model_name='all-MiniLM-L6-v2')
    doc_parser = DocumentParser()
    print(f"Embedding model ready — dim: {embedder.embedding_dim}\n")

    # Pre-load and embed all domain texts ONCE (shared between both versions)
    print("Pre-loading domain files...")
    domain_data: dict = {}
    for domain_name, domain_cfg in DOMAINS.items():
        jd_raw, jd_ids = [], []
        for jd in domain_cfg['jds']:
            text = doc_parser.parse_file(jd['file'])
            if text:
                jd_raw.append(text)
                jd_ids.append(jd['id'])
            else:
                print(f"  WARNING: could not load {jd['file']}")

        if not jd_raw:
            continue

        cleaned   = cleaner.clean_batch(jd_raw)
        c_texts   = [r['cleaned_text'] for r in cleaned]
        valid_ids = [jd_ids[r['original_index']] for r in cleaned]
        embeds    = embedder.embed_batch(c_texts, show_progress=False)

        cv_texts = {}
        for cv in domain_cfg['cvs']:
            text = doc_parser.parse_file(cv['file'])
            if text:
                cv_texts[cv['name']] = text

        domain_data[domain_name] = {
            'jd_ids':    valid_ids,
            'jd_texts':  c_texts,
            'jd_embeds': embeds,
            'cv_texts':  cv_texts,
        }
        print(f"  Loaded: {domain_name} ({len(valid_ids)} JDs, {len(cv_texts)} CVs)")

    total_pairs = sum(
        len(d['cv_texts']) * len(d['jd_ids'])
        for d in domain_data.values()
    )
    print(f"\nTotal pairs to score per version: {total_pairs}")

    # ── Run Version A ─────────────────────────────────────────────────────────
    print("\n" + "-" * 70)
    print("Running Version A — lexical matching only (no semantic fallback)...")
    t_a = time.time()
    rows_a = run_version('A_Lexical', False, cleaner, embedder, doc_parser, domain_data)
    print(f"Version A done in {time.time() - t_a:.1f}s")

    # ── Run Version B ─────────────────────────────────────────────────────────
    print("\n" + "-" * 70)
    print("Running Version B — lexical + semantic fallback (threshold 0.80)...")
    t_b = time.time()
    rows_b = run_version('B_Semantic', True, cleaner, embedder, doc_parser, domain_data)
    print(f"Version B done in {time.time() - t_b:.1f}s")

    # ── Accuracy metrics ──────────────────────────────────────────────────────
    def accuracy(rows):
        labelled = [r for r in rows if r['human_label'] != '?']
        if not labelled:
            return 0.0, 0, 0
        correct = sum(1 for r in labelled if r['correct'] == 'YES')
        return correct / len(labelled) * 100, correct, len(labelled)

    def tier_accuracy(rows, tier):
        subset = [r for r in rows if r['human_label'] == tier]
        if not subset:
            return 0.0, 0, 0
        correct = sum(1 for r in subset if r['correct'] == 'YES')
        return correct / len(subset) * 100, correct, len(subset)

    def domain_accuracy(rows, domain):
        subset = [r for r in rows if r['domain'] == domain and r['human_label'] != '?']
        if not subset:
            return 0.0, 0, 0
        correct = sum(1 for r in subset if r['correct'] == 'YES')
        return correct / len(subset) * 100, correct, len(subset)

    acc_a, ok_a, n_a = accuracy(rows_a)
    acc_b, ok_b, n_b = accuracy(rows_b)

    # ── Pair-level diff: pairs where B changed the outcome ───────────────────
    # Build lookup: (domain, cv, jd) → correct_flag
    lookup_a = {(r['domain'], r['cv_name'], r['jd_id']): r['correct'] for r in rows_a}
    lookup_b = {(r['domain'], r['cv_name'], r['jd_id']): r['correct'] for r in rows_b}

    newly_correct = 0   # A wrong, B right
    newly_wrong   = 0   # A right, B wrong
    unchanged     = 0
    changed_pairs = []

    for key in lookup_a:
        ca, cb = lookup_a[key], lookup_b.get(key, 'NO')
        if ca == cb:
            unchanged += 1
        elif ca == 'NO' and cb == 'YES':
            newly_correct += 1
            row_b = next(r for r in rows_b if (r['domain'], r['cv_name'], r['jd_id']) == key)
            row_a = next(r for r in rows_a if (r['domain'], r['cv_name'], r['jd_id']) == key)
            changed_pairs.append({
                'direction': 'FIXED',
                'domain': key[0], 'cv': key[1], 'jd': key[2],
                'score_a': row_a['score'], 'cat_a': row_a['system_cat'],
                'score_b': row_b['score'], 'cat_b': row_b['system_cat'],
                'human': row_a['human_label'],
                'skills_pct_a': row_a['skills_pct'], 'skills_pct_b': row_b['skills_pct'],
            })
        else:
            newly_wrong += 1
            row_b = next(r for r in rows_b if (r['domain'], r['cv_name'], r['jd_id']) == key)
            row_a = next(r for r in rows_a if (r['domain'], r['cv_name'], r['jd_id']) == key)
            changed_pairs.append({
                'direction': 'BROKEN',
                'domain': key[0], 'cv': key[1], 'jd': key[2],
                'score_a': row_a['score'], 'cat_a': row_a['system_cat'],
                'score_b': row_b['score'], 'cat_b': row_b['system_cat'],
                'human': row_a['human_label'],
                'skills_pct_a': row_a['skills_pct'], 'skills_pct_b': row_b['skills_pct'],
            })

    # ── Print results ─────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    print(f"\n{'Metric':<35} {'Version A':>12} {'Version B':>12} {'Delta':>10}")
    print("-" * 72)
    print(f"{'Overall accuracy':<35} {acc_a:>11.1f}% {acc_b:>11.1f}% {acc_b-acc_a:>+9.1f}pp")
    print(f"{'Correct pairs':<35} {ok_a:>12} {ok_b:>12} {ok_b-ok_a:>+10}")
    print(f"{'Total labelled pairs':<35} {n_a:>12} {n_b:>12}")

    print(f"\n{'Tier breakdown':<35} {'Version A':>12} {'Version B':>12} {'Delta':>10}")
    print("-" * 72)
    for tier in ('Strong', 'Moderate', 'Weak'):
        pa, ca, na = tier_accuracy(rows_a, tier)
        pb, cb, nb = tier_accuracy(rows_b, tier)
        print(f"  {tier:<33} {pa:>11.1f}% {pb:>11.1f}% {pb-pa:>+9.1f}pp  ({na} pairs)")

    print(f"\n{'Domain breakdown':<35} {'Version A':>12} {'Version B':>12} {'Delta':>10}")
    print("-" * 72)
    for domain in sorted(domain_data.keys()):
        pa, ca, na = domain_accuracy(rows_a, domain)
        pb, cb, nb = domain_accuracy(rows_b, domain)
        print(f"  {domain:<33} {pa:>11.1f}% {pb:>11.1f}% {pb-pa:>+9.1f}pp  ({na} pairs)")

    print(f"\n{'Pair-level changes':<35}")
    print("-" * 72)
    print(f"  Pairs fixed by semantic fallback (A wrong, B right): {newly_correct}")
    print(f"  Pairs broken by semantic fallback (A right, B wrong): {newly_wrong}")
    print(f"  Unchanged pairs:                                        {unchanged}")

    if changed_pairs:
        print(f"\nChanged pairs detail:")
        print(f"  {'Dir':<7} {'Domain':<22} {'CV':<14} {'JD':<14} "
              f"{'Human':<10} {'Cat A':<10} {'Cat B':<10} "
              f"{'Skl% A':>7} {'Skl% B':>7}")
        print("  " + "-" * 100)
        for p in sorted(changed_pairs, key=lambda x: x['direction']):
            print(
                f"  {p['direction']:<7} {p['domain']:<22} {p['cv']:<14} {p['jd']:<14} "
                f"{p['human']:<10} {p['cat_a']:<10} {p['cat_b']:<10} "
                f"{p['skills_pct_a']:>7.1f} {p['skills_pct_b']:>7.1f}"
            )

    # ── Save CSVs ─────────────────────────────────────────────────────────────
    fieldnames = ['version', 'domain', 'cv_name', 'jd_id', 'score',
                  'system_cat', 'human_label', 'correct', 'skills_pct', 'skills_pts']

    csv_a = 'ablation_semantic_A.csv'
    csv_b = 'ablation_semantic_B.csv'

    with open(csv_a, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows_a)

    with open(csv_b, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows_b)

    print(f"\nDetail CSVs saved:")
    print(f"  {csv_a}  ({len(rows_a)} rows)")
    print(f"  {csv_b}  ({len(rows_b)} rows)")

    # ── Thesis comparison table ───────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("THESIS COMPARISON TABLE (copy into Chapter 6)")
    print("=" * 70)
    print(f"""
| Configuration       | Accuracy | Strong | Moderate | Weak  | Delta    |
|---------------------|----------|--------|----------|-------|----------|
| Original (Book2)    | 50.3%    | 27%    | 84%      | 45%   | baseline |
| Version A (lexical) | {acc_a:.1f}%   | —      | —        | —     | —        |
| Version B (sem. fb) | {acc_b:.1f}%   | —      | —        | —     | {acc_b-acc_a:+.1f}pp    |

Note: Version A is a replication of the original run on the 27-pair subset.
Version B adds semantic skill matching as a fourth fallback tier (threshold = 0.80).
Full 153-pair numbers require running run_all_pairs.py in both modes — see below.
""")

    print(f"Total wall time: {time.time()-t0:.0f}s")


if __name__ == '__main__':
    main()
