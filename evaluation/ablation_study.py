"""
ablation_study.py
-----------------
Compares 5 weight configurations on the hybrid scoring formula across 6 domains.
Outputs Precision@3, category accuracy, score spread, and a full comparison CSV.

Configs:
  A_Equal          — equal weights baseline
  B_Semantic_Heavy — semantic-dominant baseline
  C_Old            — initial configuration (40/20/15/15/10)
  D_Proposed       — seniority-boosted candidate (38/17/15/15/15)
  E_Live           — final deployed configuration (35/20/15/15/15)

Run from the project root:
    python ablation_study.py
"""

import sys
import os
import csv

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from preprocessing.text_cleaning import TextCleaner
from preprocessing.document_parser import DocumentParser
from embeddings.embedder import TextEmbedder
from vector_store.faiss_index import FAISSJobIndex
from matching.matcher_v2 import CVJobMatcherV2

# ─────────────────────────────────────────────────────────────────────────────
# 1. DOMAIN FILE MANIFEST
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
            {'id': 'JD1_Entry',  'file': 'data/raw/Human Resources/job_description_1_hr.txt',  'level': 'Entry'},
            {'id': 'JD2_Mid',    'file': 'data/raw/Human Resources/job_description_2_hr.docx',  'level': 'Mid'},
            {'id': 'JD3_Senior', 'file': 'data/raw/Human Resources/job_description_3_hr.txt',  'level': 'Senior'},
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
# 2. HUMAN GROUND TRUTH
# ─────────────────────────────────────────────────────────────────────────────
GROUND_TRUTH = {
    'Data Analysis': {
        'Data_Analyst': {
            'JD1_Entry': 'Strong', 'JD2_Mid': 'Moderate', 'JD3_Senior': 'Weak',
        },
    },
    'Marketing': {
        'Andi_Shehu': {
            'JD1_Entry': 'Moderate', 'JD2_Mid': 'Strong', 'JD3_FMCG': 'Moderate',
        },
    },
    'Medicine': {
        'Maria_Kola': {
            'JD1_Mid': 'Moderate', 'JD2_Entry': 'Strong', 'JD3_Senior': 'Weak',
        },
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
# 3. WEIGHT CONFIGURATIONS  (values on 0-100 scale matching matcher_v2.py)
# ─────────────────────────────────────────────────────────────────────────────
CONFIGS = {
    'A_Equal':          {'semantic': 20, 'skills': 20, 'domain': 20, 'education': 20, 'seniority': 20},
    'B_Semantic_Heavy': {'semantic': 60, 'skills': 15, 'domain': 10, 'education': 10, 'seniority':  5},
    'C_Old':            {'semantic': 40, 'skills': 20, 'domain': 15, 'education': 15, 'seniority': 10},
    'D_Proposed':       {'semantic': 38, 'skills': 17, 'domain': 15, 'education': 15, 'seniority': 15},
    'E_Live':           {'semantic': 35, 'skills': 20, 'domain': 15, 'education': 15, 'seniority': 15},
}

LABEL_ORDER = {'Strong': 3, 'Moderate': 2, 'Weak': 1}


# ─────────────────────────────────────────────────────────────────────────────
# 4. HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def category_from_score(score: float) -> str:
    if score >= 70:
        return 'Strong'
    elif score >= 40:
        return 'Moderate'
    return 'Weak'


def ranking_correct(scores: dict, gt: dict) -> bool:
    """
    Returns True if the system's score ordering is consistent with human labels.
    Strong > Moderate > Weak must be preserved; ties within same tier are fine.
    """
    jd_ids = list(gt.keys())
    for i in range(len(jd_ids)):
        for j in range(i + 1, len(jd_ids)):
            a, b = jd_ids[i], jd_ids[j]
            if a not in scores or b not in scores:
                continue
            gt_a, gt_b   = LABEL_ORDER[gt[a]], LABEL_ORDER[gt[b]]
            sc_a, sc_b   = scores[a], scores[b]
            if gt_a > gt_b and sc_a <= sc_b:
                return False
            if gt_b > gt_a and sc_b <= sc_a:
                return False
    return True


# ─────────────────────────────────────────────────────────────────────────────
# 5. MAIN ABLATION LOOP
# ─────────────────────────────────────────────────────────────────────────────
def run_ablation():
    print("=" * 70)
    print("ABLATION STUDY — 4 Weight Configurations × 6 Domains")
    print("=" * 70)

    # Shared components — load model ONCE
    print("\nLoading embedding model (this takes ~10 seconds)...")
    cleaner    = TextCleaner(remove_emails=True, remove_phone=True, remove_urls=True, min_length=50)
    embedder   = TextEmbedder(model_name='all-MiniLM-L6-v2')
    doc_parser = DocumentParser()
    print(f"Model ready. Embedding dim: {embedder.embedding_dim}\n")

    # Pre-load and embed all domain texts (shared across all 4 configs)
    print("Loading and embedding domain texts...")
    domain_data_loaded = {}

    for domain_name, domain_cfg in DOMAINS.items():
        print(f"  [{domain_name}]")

        jd_raw_texts, jd_ids = [], []
        for jd in domain_cfg['jds']:
            text = doc_parser.parse_file(jd['file'])
            if text:
                jd_raw_texts.append(text)
                jd_ids.append(jd['id'])
            else:
                print(f"    WARNING: could not load {jd['file']}")

        if not jd_raw_texts:
            print(f"    SKIPPING — no JD texts loaded for {domain_name}")
            continue

        cleaned = cleaner.clean_batch(jd_raw_texts)
        cleaned_texts = [r['cleaned_text'] for r in cleaned]
        valid_ids     = [jd_ids[r['original_index']] for r in cleaned]
        embeddings    = embedder.embed_batch(cleaned_texts, show_progress=False)

        cv_texts = {}
        for cv in domain_cfg['cvs']:
            text = doc_parser.parse_file(cv['file'])
            if text:
                cv_texts[cv['name']] = text
            else:
                print(f"    WARNING: could not load {cv['file']}")

        domain_data_loaded[domain_name] = {
            'jd_ids':    valid_ids,
            'jd_texts':  cleaned_texts,
            'jd_embeds': embeddings,
            'cv_texts':  cv_texts,
        }

    # ── Run each config ──────────────────────────────────────────────────────
    all_scores = {}   # config → domain → cv_name → jd_id → float

    for config_name, weights in CONFIGS.items():
        print(f"\n{'-'*70}")
        print(f"Config {config_name}  | weights: {weights}")
        print('-' * 70)
        all_scores[config_name] = {}

        for domain_name, data in domain_data_loaded.items():
            all_scores[config_name][domain_name] = {}

            # Fresh temp FAISS index for this domain
            temp_index = FAISSJobIndex(embedding_dim=embedder.embedding_dim)
            temp_index.add_jobs(
                job_embeddings=data['jd_embeds'],
                job_ids=data['jd_ids'],
                job_texts=data['jd_texts'],
            )

            # One matcher per domain; swap weights per config
            matcher = CVJobMatcherV2(cleaner, embedder, temp_index)
            matcher.set_weights(**weights)

            for cv_name, cv_text in data['cv_texts'].items():
                result = matcher.match_cv_to_jobs(
                    cv_text=cv_text,
                    cv_id=cv_name,
                    top_k=len(data['jd_ids']),
                )

                cv_scores = {}
                for match in result.get('matches', []):
                    jid   = match['job_id']
                    score = match['score_breakdown']['final_hybrid']
                    cv_scores[jid] = score

                all_scores[config_name][domain_name][cv_name] = cv_scores

                # Per-pair console output
                gt_cv = GROUND_TRUTH.get(domain_name, {}).get(cv_name, {})
                print(f"  {domain_name} / {cv_name}")
                for jid, sc in sorted(cv_scores.items()):
                    gt_lbl  = gt_cv.get(jid, '?')
                    sys_cat = category_from_score(sc)
                    ok      = 'OK' if sys_cat == gt_lbl else 'XX'
                    print(f"    {jid:<20} {sc:>5.1f}%  sys={sys_cat:<10} gt={gt_lbl} {ok}")

    # ─────────────────────────────────────────────────────────────────────────
    # 6. COMPUTE METRICS
    # ─────────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("METRICS")
    print("=" * 70)

    metrics = {}
    for config_name in CONFIGS:
        p3_scores   = []
        cat_hits    = 0
        cat_total   = 0
        spreads     = []
        all_flat    = []

        for domain_name in domain_data_loaded:
            gt_domain = GROUND_TRUTH.get(domain_name, {})
            for cv_name, cv_scores in all_scores[config_name][domain_name].items():
                gt_cv = gt_domain.get(cv_name, {})
                if not gt_cv:
                    continue

                # Precision@3
                p3_scores.append(1 if ranking_correct(cv_scores, gt_cv) else 0)

                # Category accuracy
                for jid, gt_lbl in gt_cv.items():
                    if jid in cv_scores:
                        if category_from_score(cv_scores[jid]) == gt_lbl:
                            cat_hits += 1
                        cat_total += 1

                # Spread (max - min scores for this CV)
                vals = list(cv_scores.values())
                if vals:
                    spreads.append(max(vals) - min(vals))
                    all_flat.extend(vals)

        metrics[config_name] = {
            'precision_at_3':    sum(p3_scores) / len(p3_scores) if p3_scores else 0,
            'category_accuracy': cat_hits / cat_total if cat_total else 0,
            'avg_spread':        sum(spreads) / len(spreads) if spreads else 0,
            'min_score':         min(all_flat) if all_flat else 0,
            'max_score':         max(all_flat) if all_flat else 0,
            'cat_hits':          cat_hits,
            'cat_total':         cat_total,
            'p3_detail':         p3_scores,
        }

    # ── Comparison table ─────────────────────────────────────────────────────
    print(f"\n{'Config':<22} {'Precision@3':>12} {'Cat Accuracy':>14} {'Avg Spread':>12} {'Combined':>10}")
    print("-" * 75)
    for cfg, m in metrics.items():
        combined = (m['precision_at_3'] + m['category_accuracy']) / 2
        print(
            f"{cfg:<22} {m['precision_at_3']:>11.1%} "
            f"{m['category_accuracy']:>13.1%} "
            f"{m['avg_spread']:>11.1f}% "
            f"{combined:>9.1%}"
        )

    # ── Score distributions ───────────────────────────────────────────────────
    print(f"\n{'Config':<22} {'Min':>7} {'Max':>7} {'Range':>8}")
    print("-" * 50)
    for cfg, m in metrics.items():
        print(f"{cfg:<22} {m['min_score']:>6.1f}% {m['max_score']:>6.1f}% {m['max_score']-m['min_score']:>7.1f}%")

    # ── Winner ───────────────────────────────────────────────────────────────
    winner_name, winner_m = max(
        metrics.items(),
        key=lambda x: (x[1]['precision_at_3'] + x[1]['category_accuracy']) / 2
    )
    combined_score = (winner_m['precision_at_3'] + winner_m['category_accuracy']) / 2
    print(f"\nWINNER: {winner_name}  (combined {combined_score:.1%})")

    # ── Recommendation ────────────────────────────────────────────────────────
    print("\nRECOMMENDATION")
    print("-" * 50)
    m_c   = metrics['C_Old']
    m_d   = metrics['D_Proposed']
    m_e   = metrics['E_Live']

    delta_cd_p3  = m_d['precision_at_3']    - m_c['precision_at_3']
    delta_cd_cat = m_d['category_accuracy'] - m_c['category_accuracy']
    delta_de_p3  = m_e['precision_at_3']    - m_d['precision_at_3']
    delta_de_cat = m_e['category_accuracy'] - m_d['category_accuracy']

    print(f"  C_Old -> D_Proposed  Precision@3 delta : {delta_cd_p3:+.1%}")
    print(f"  C_Old -> D_Proposed  Cat accuracy delta: {delta_cd_cat:+.1%}")
    print(f"  D_Proposed -> E_Live Precision@3 delta : {delta_de_p3:+.1%}")
    print(f"  D_Proposed -> E_Live Cat accuracy delta: {delta_de_cat:+.1%}")

    if winner_name == 'E_Live':
        print("  E_Live (deployed) is the best configuration. No change needed.")
    elif winner_name == 'D_Proposed':
        print("  Config D wins overall, but E_Live (deployed) is close — check deltas.")
    else:
        print(f"  {winner_name} performs best overall.")

    # ─────────────────────────────────────────────────────────────────────────
    # 7. SAVE CSV  (C_Old vs D_Proposed vs E_Live)
    # ─────────────────────────────────────────────────────────────────────────
    csv_path = 'ablation_results_final.csv'
    rows = []
    for domain_name, domain_cfg in DOMAINS.items():
        if domain_name not in domain_data_loaded:
            continue
        gt_domain = GROUND_TRUTH.get(domain_name, {})
        for cv in domain_cfg['cvs']:
            cv_name = cv['name']
            gt_cv   = gt_domain.get(cv_name, {})
            for jd in domain_cfg['jds']:
                jid  = jd['id']
                sc_c = all_scores['C_Old'][domain_name].get(cv_name, {}).get(jid)
                sc_d = all_scores['D_Proposed'][domain_name].get(cv_name, {}).get(jid)
                sc_e = all_scores['E_Live'][domain_name].get(cv_name, {}).get(jid)
                if sc_c is None or sc_d is None or sc_e is None:
                    continue
                rows.append({
                    'domain':             domain_name,
                    'cv_name':            cv_name,
                    'jd_level':           jd['level'],
                    'config_c_score':     round(sc_c, 2),
                    'config_d_score':     round(sc_d, 2),
                    'config_live_score':  round(sc_e, 2),
                    'human_rating':       gt_cv.get(jid, 'unknown'),
                    'config_c_category':  category_from_score(sc_c),
                    'config_d_category':  category_from_score(sc_d),
                    'config_live_category': category_from_score(sc_e),
                })

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'domain', 'cv_name', 'jd_level',
            'config_c_score', 'config_d_score', 'config_live_score',
            'human_rating',
            'config_c_category', 'config_d_category', 'config_live_category',
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nCSV saved -> {csv_path}  ({len(rows)} rows)")

    # ─────────────────────────────────────────────────────────────────────────
    # 8. E_Live is already deployed in matcher_v2.py — no auto-update needed.
    # ─────────────────────────────────────────────────────────────────────────

    return winner_name, metrics


def _update_matcher_weights(new_weights: dict):
    """Patch the default weights in src/matching/matcher_v2.py."""
    path = os.path.join('src', 'matching', 'matcher_v2.py')
    with open(path, 'r', encoding='utf-8') as f:
        src = f.read()

    old_block = (
        "        self.weights = {\n"
        "            'semantic': 40,\n"
        "            'skills': 20,\n"
        "            'domain': 15,\n"
        "            'education': 15,\n"
        "            'seniority': 10\n"
        "        }"
    )
    new_block = (
        "        self.weights = {\n"
        f"            'semantic': {new_weights['semantic']},\n"
        f"            'skills': {new_weights['skills']},\n"
        f"            'domain': {new_weights['domain']},\n"
        f"            'education': {new_weights['education']},\n"
        f"            'seniority': {new_weights['seniority']}\n"
        "        }"
    )

    if old_block not in src:
        print("\nWARNING: Could not find weight block in matcher_v2.py — manual update required.")
        print(f"  Set weights to: {new_weights}")
        return

    updated = src.replace(old_block, new_block, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(updated)

    # Also update the docstring table at the top of the file
    print(f"\nmatcher_v2.py updated with Config D weights: {new_weights}")


if __name__ == '__main__':
    winner, metrics = run_ablation()
    print("\nDone.")
