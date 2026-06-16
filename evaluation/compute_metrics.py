import csv
from collections import defaultdict

comparison_data = [
    ("Data Analysis", "CV1", "JD1 Entry", "Strong", 72, "Strong", "Strong", "Strong", "Strong"),
    ("Data Analysis", "CV1", "JD2 Mid", "Moderate", 42, "Moderate", "Moderate", "Moderate", "Moderate"),
    ("Data Analysis", "CV1", "JD3 Senior", "Weak", 27, "Weak", "Weak", "Weak", "Weak"),
    ("Marketing", "CV1 Andi", "JD1 Entry", "Moderate", 61, "Moderate", "Strong", "Strong", "Moderate"),
    ("Marketing", "CV1 Andi", "JD2 Mid", "Strong", 55, "Moderate", "Strong", "Moderate", "Strong"),
    ("Marketing", "CV1 Andi", "JD3 FMCG", "Moderate", 53, "Moderate", "Weak", "Strong", "Weak"),
    ("Medicine", "CV1 Maria", "JD1 Mid", "Moderate", 51, "Moderate", "Weak", "Weak", "Weak"),
    ("Medicine", "CV1 Maria", "JD2 Entry", "Strong", 52, "Moderate", "Strong", "Strong", "Strong"),
    ("Medicine", "CV1 Maria", "JD3 Senior", "Weak", 41, "Moderate", "Weak", "Weak", "Weak"),
    ("Software Eng", "CV1 Ardit", "JD1 Senior", "Weak", 42, "Moderate", "Weak", "Weak", "Moderate"),
    ("Software Eng", "CV1 Ardit", "JD2 Mid", "Moderate", 60, "Moderate", "Strong", "Moderate", "Moderate"),
    ("Software Eng", "CV1 Ardit", "JD3 Go Senior", "Weak", 27, "Weak", "Weak", "Weak", "Weak"),
    ("Software Eng", "CV2 Klea", "JD1 Senior", "Weak", 44, "Moderate", "Weak", "Weak", "Moderate"),
    ("Software Eng", "CV2 Klea", "JD2 Mid", "Moderate", 55, "Moderate", "Strong", "Moderate", "Moderate"),
    ("Software Eng", "CV2 Klea", "JD3 Go Senior", "Weak", 27, "Weak", "Weak", "Weak", "Weak"),
    ("HR", "CV1 Erisa", "JD1 Entry", "Strong", 60, "Moderate", "Strong", "Strong", "Strong"),
    ("HR", "CV1 Erisa", "JD2 Mid", "Weak", 60, "Moderate", "Moderate", "Weak", "Weak"),
    ("HR", "CV1 Erisa", "JD3 Senior", "Weak", 31, "Weak", "Weak", "Weak", "Weak"),
    ("HR", "CV2 Klajdi", "JD1 Entry", "Strong", 59, "Moderate", "Strong", "Strong", "Strong"),
    ("HR", "CV2 Klajdi", "JD2 Mid", "Weak", 58, "Moderate", "Moderate", "Weak", "Weak"),
    ("HR", "CV2 Klajdi", "JD3 Senior", "Weak", 36, "Weak", "Weak", "Weak", "Weak"),
    ("Finance", "CV1 Besa", "JD1 Entry", "Strong", 67, "Moderate", "Strong", "Strong", "Strong"),
    ("Finance", "CV1 Besa", "JD2 Senior", "Weak", 31, "Weak", "Weak", "Weak", "Weak"),
    ("Finance", "CV1 Besa", "JD3 Specialist", "Moderate", 30, "Weak", "Moderate", "Weak", "Weak"),
    ("Finance", "CV2 Endri", "JD1 Entry", "Strong", 64, "Moderate", "Strong", "Strong", "Strong"),
    ("Finance", "CV2 Endri", "JD2 Senior", "Weak", 32, "Weak", "Weak", "Weak", "Weak"),
    ("Finance", "CV2 Endri", "JD3 Specialist", "Weak", 34, "Weak", "Moderate", "Weak", "Weak"),
    ("Law", "CV1 Elona", "JD1 Mid", "Moderate", 55, "Moderate", "Moderate", "Weak", "Moderate"),
    ("Law", "CV1 Elona", "JD2 Entry", "Strong", 73, "Strong", "Strong", "Strong", "Strong"),
    ("Law", "CV1 Elona", "JD3 Senior", "Weak", 45, "Moderate", "Weak", "Weak", "Weak"),
    ("Law", "CV2 Ardit", "JD1 Mid", "Moderate", 61, "Moderate", "Moderate", "Weak", "Moderate"),
    ("Law", "CV2 Ardit", "JD2 Entry", "Strong", 59, "Moderate", "Strong", "Strong", "Strong"),
    ("Law", "CV2 Ardit", "JD3 Senior", "Weak", 51, "Moderate", "Weak", "Weak", "Weak"),
    ("Architecture", "CV1 Kejsi", "JD1 Entry", "Strong", 41, "Weak", "Strong", "Moderate", "Moderate"),
    ("Architecture", "CV1 Kejsi", "JD2 Mid", "Moderate", 33, "Weak", "Moderate", "Weak", "Moderate"),
    ("Architecture", "CV1 Kejsi", "JD3 Hoja", "Moderate", 41, "Weak", "Strong", "Weak", "Moderate"),
    ("Architecture", "CV2 Andi", "JD1 Entry", "Strong", 65, "Moderate", "Strong", "Strong", "Strong"),
    ("Architecture", "CV2 Andi", "JD2 Mid", "Moderate", 51, "Moderate", "Strong", "Weak", "Moderate"),
    ("Architecture", "CV2 Andi", "JD3 Hoja", "Moderate", 51, "Moderate", "Strong", "Moderate", "Moderate"),
    ("Civil Eng", "CV1 Klajdi", "JD1 Entry", "Strong", 41, "Weak", "Strong", "Strong", "Strong"),
    ("Civil Eng", "CV1 Klajdi", "JD2 Mid", "Moderate", 46, "Moderate", "Moderate", "Weak", "Moderate"),
    ("Civil Eng", "CV1 Klajdi", "JD3 Senior", "Weak", 45, "Moderate", "Weak", "Weak", "Weak"),
    ("Civil Eng", "CV2 Miranda", "JD1 Entry", "Strong", 44, "Moderate", "Strong", "Moderate", "Strong"),
    ("Civil Eng", "CV2 Miranda", "JD2 Mid", "Strong", 69, "Moderate", "Strong", "Strong", "Strong"),
    ("Civil Eng", "CV2 Miranda", "JD3 Senior", "Weak", 56, "Moderate", "Moderate", "Weak", "Weak"),
]

def sys_category(score):
    if score >= 70: return "Strong"
    elif score >= 40: return "Moderate"
    else: return "Weak"

def to_num(label):
    l = label.strip().upper()
    if "STRONG" in l: return 3
    if "MODERATE" in l: return 2
    if "WEAK" in l: return 1
    return 0

def normalize(label):
    l = label.strip().upper()
    if "STRONG" in l: return "Strong"
    if "MODERATE" in l: return "Moderate"
    if "WEAK" in l: return "Weak"
    return "?"

def spearman(x, y):
    n = len(x)
    def rank(lst):
        sorted_idx = sorted(range(n), key=lambda i: lst[i])
        r = [0] * n
        for rank_val, idx in enumerate(sorted_idx, 1):
            r[idx] = rank_val
        return r
    rx = rank(x)
    ry = rank(y)
    d2 = sum((rx[i] - ry[i])**2 for i in range(n))
    return 1 - (6 * d2) / (n * (n**2 - 1))

# Build per-row evaluator predictions
rows = []
for d in comparison_data:
    domain, cv, jd, human, score, sys_cat_raw, chatgpt, gemini, claude_eval = d
    sys_pred = sys_category(score)
    rows.append({
        "domain": domain,
        "cv": cv,
        "jd": jd,
        "human": normalize(human),
        "system": normalize(sys_pred),
        "chatgpt": normalize(chatgpt),
        "gemini": normalize(gemini),
        "claude": normalize(claude_eval),
        "score": score,
    })

evaluators = ["system", "chatgpt", "gemini", "claude"]
n_total = len(rows)
human_nums = [to_num(r["human"]) for r in rows]

# ── 1. Overall accuracy ────────────────────────────────────────────────────────
overall = {}
for ev in evaluators:
    correct = sum(r[ev] == r["human"] for r in rows)
    overall[ev] = {"correct": correct, "total": n_total, "pct": correct / n_total * 100}

# ── 2. Per-domain accuracy ─────────────────────────────────────────────────────
domains = sorted(set(r["domain"] for r in rows))
domain_acc = {d: {} for d in domains}
for domain in domains:
    subset = [r for r in rows if r["domain"] == domain]
    n = len(subset)
    for ev in evaluators:
        correct = sum(r[ev] == r["human"] for r in subset)
        domain_acc[domain][ev] = {"correct": correct, "total": n, "pct": correct / n * 100}

# ── 3. Spearman correlation ────────────────────────────────────────────────────
spearman_overall = {}
for ev in evaluators:
    ev_nums = [to_num(r[ev]) for r in rows]
    spearman_overall[ev] = spearman(human_nums, ev_nums)

spearman_domain = {d: {} for d in domains}
for domain in domains:
    subset = [r for r in rows if r["domain"] == domain]
    h = [to_num(r["human"]) for r in subset]
    for ev in evaluators:
        e = [to_num(r[ev]) for r in subset]
        if len(set(h)) == 1 or len(set(e)) == 1:
            spearman_domain[domain][ev] = float('nan')
        else:
            spearman_domain[domain][ev] = spearman(h, e)

# ── 4-6. Agreement by tier ─────────────────────────────────────────────────────
tier_acc = {}
for tier in ["Strong", "Moderate", "Weak"]:
    subset = [r for r in rows if r["human"] == tier]
    n = len(subset)
    tier_acc[tier] = {}
    for ev in evaluators:
        correct = sum(r[ev] == r["human"] for r in subset)
        tier_acc[tier][ev] = {"correct": correct, "total": n, "pct": correct / n * 100 if n > 0 else 0}

# ── Print summary ──────────────────────────────────────────────────────────────
print("=== OVERALL ACCURACY ===")
for ev in evaluators:
    o = overall[ev]
    print(f"  {ev:10s}: {o['correct']}/{o['total']} = {o['pct']:.1f}%")

print("\n=== PER-DOMAIN ACCURACY ===")
header = f"{'Domain':20s}" + "".join(f"  {ev:10s}" for ev in evaluators)
print(header)
for domain in domains:
    row_str = f"{domain:20s}"
    for ev in evaluators:
        da = domain_acc[domain][ev]
        row_str += f"  {da['correct']}/{da['total']}={da['pct']:4.0f}%"
    print(row_str)

print("\n=== SPEARMAN CORRELATION (overall) ===")
for ev in evaluators:
    print(f"  {ev:10s}: {spearman_overall[ev]:.4f}")

print("\n=== AGREEMENT BY TIER ===")
for tier in ["Strong", "Moderate", "Weak"]:
    ta = tier_acc[tier]
    parts = [f"{ev}: {ta[ev]['correct']}/{ta[ev]['total']}={ta[ev]['pct']:.0f}%" for ev in evaluators]
    print(f"  {tier:10s}: " + "  |  ".join(parts))

# ── Save to CSV ────────────────────────────────────────────────────────────────
output_rows = []

# Section 1: overall accuracy
output_rows.append(["Section", "Domain/Tier", "Metric", "System", "ChatGPT", "Gemini", "Claude"])
output_rows.append(["Overall Accuracy", "ALL", "correct/total",
    f"{overall['system']['correct']}/{overall['system']['total']}",
    f"{overall['chatgpt']['correct']}/{overall['chatgpt']['total']}",
    f"{overall['gemini']['correct']}/{overall['gemini']['total']}",
    f"{overall['claude']['correct']}/{overall['claude']['total']}"])
output_rows.append(["Overall Accuracy", "ALL", "pct",
    f"{overall['system']['pct']:.1f}",
    f"{overall['chatgpt']['pct']:.1f}",
    f"{overall['gemini']['pct']:.1f}",
    f"{overall['claude']['pct']:.1f}"])

# Section 2: per-domain accuracy
for domain in domains:
    da = domain_acc[domain]
    output_rows.append(["Domain Accuracy", domain, "correct/total",
        f"{da['system']['correct']}/{da['system']['total']}",
        f"{da['chatgpt']['correct']}/{da['chatgpt']['total']}",
        f"{da['gemini']['correct']}/{da['gemini']['total']}",
        f"{da['claude']['correct']}/{da['claude']['total']}"])
    output_rows.append(["Domain Accuracy", domain, "pct",
        f"{da['system']['pct']:.1f}",
        f"{da['chatgpt']['pct']:.1f}",
        f"{da['gemini']['pct']:.1f}",
        f"{da['claude']['pct']:.1f}"])

# Section 3: Spearman overall
output_rows.append(["Spearman rho", "ALL", "correlation",
    f"{spearman_overall['system']:.4f}",
    f"{spearman_overall['chatgpt']:.4f}",
    f"{spearman_overall['gemini']:.4f}",
    f"{spearman_overall['claude']:.4f}"])

# Section 3b: Spearman per domain
for domain in domains:
    sd = spearman_domain[domain]
    output_rows.append(["Spearman rho", domain, "correlation",
        f"{sd['system']:.4f}" if sd['system'] == sd['system'] else "N/A",
        f"{sd['chatgpt']:.4f}" if sd['chatgpt'] == sd['chatgpt'] else "N/A",
        f"{sd['gemini']:.4f}" if sd['gemini'] == sd['gemini'] else "N/A",
        f"{sd['claude']:.4f}" if sd['claude'] == sd['claude'] else "N/A"])

# Section 4-6: tier agreement
for tier in ["Strong", "Moderate", "Weak"]:
    ta = tier_acc[tier]
    output_rows.append([f"{tier} Agreement", tier, "correct/total",
        f"{ta['system']['correct']}/{ta['system']['total']}",
        f"{ta['chatgpt']['correct']}/{ta['chatgpt']['total']}",
        f"{ta['gemini']['correct']}/{ta['gemini']['total']}",
        f"{ta['claude']['correct']}/{ta['claude']['total']}"])
    output_rows.append([f"{tier} Agreement", tier, "pct",
        f"{ta['system']['pct']:.1f}",
        f"{ta['chatgpt']['pct']:.1f}",
        f"{ta['gemini']['pct']:.1f}",
        f"{ta['claude']['pct']:.1f}"])

with open("final_metrics.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(output_rows)

print("\nSaved -> final_metrics.csv")
