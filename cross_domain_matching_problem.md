# Cross-Domain Matching Problem — Analysis & Proposed Solutions

**Project:** AI-Powered CV-to-Job Matching Platform  
**Author:** Xhoana Pole  
**Date:** April 2026

---

## 1. The Problem We Faced

During the testing phase of our matching platform, we identified a critical anomaly:

> A CV written entirely in the **Medical domain** (nursing, cardiology, emergency care) was being assigned a **50% match score** against a job description in the **Marketing domain** (SEO, market research, campaign management).

To a human evaluator, these two documents are clearly unrelated and should produce a score close to 0%. However, our system was outputting a "Moderate Fit" classification — which is fundamentally incorrect and would severely mislead a real user.

---

## 2. Why Does This Happen?

Our matching pipeline uses a **Sentence Transformer model** (`all-MiniLM-L6-v2`) combined with a **FAISS vector index** to compute cosine similarity between a CV embedding and a job description embedding.

The root cause of the anomaly lies in how these models work:

- Sentence Transformers map text into a **high-dimensional vector space** based on semantic meaning and linguistic patterns.
- They are trained on **general-purpose English text**, not domain-specific professional documents.
- As a result, any two documents written in **formal professional English** will inevitably share a baseline of geometric similarity in the vector space — because they share the same language structure, grammar patterns, and generic professional vocabulary (e.g., *"managed," "responsible for," "coordinated," "team"*).
- This means that even completely unrelated professional documents almost never score below **0.35–0.50** in raw cosine similarity.

In short: the model is not "understanding" that Medicine and Marketing are unrelated fields. It is only detecting that both texts are written in formal professional English.

---

## 3. What We Already Tried — Score Normalization

**Approach 1: Baseline Penalty + Exponential Scaling**

Our first attempt was to apply a mathematical post-processing function to the raw FAISS scores:

```python
def _normalize_score(self, raw_score: float) -> float:
    baseline = 0.30
    if raw_score <= baseline:
        return 0.0
    scaled = (raw_score - baseline) / (1.0 - baseline)
    return float(max(0.0, min(1.0, scaled ** 1.5)))
```

**How it works:**
- Any raw score below 0.30 is immediately forced to 0%.
- Remaining scores are linearly rescaled and then exponentially compressed using a 1.5 power curve.

**Result:**
- Raw score of 0.50 → normalized to ~8% (Weak Fit) ✅
- Raw score of 0.90 → normalized to ~72% (Strong Fit) ✅

**Limitation:** While this approach significantly reduced false positives, it still relies purely on linguistic patterns. A marketing job written in very formal clinical-sounding language could still artificially inflate the score.

---

## 4. Proposed Approaches Going Forward

### Approach 2 (Recommended): Hybrid Scoring — Semantic + Lexical

**Core Idea:** Combine two independent signals into a single final score.

| Signal | Weight | Description |
|---|---|---|
| FAISS Semantic Similarity | 70% | Measures overall linguistic and contextual overlap via vector embeddings |
| Skills Match Percentage | 30% | Measures direct keyword overlap between extracted CV skills and job-required skills |

**Formula:**
```
Final Score = (Normalized FAISS Score × 0.70) + (Skills Match % × 0.30)
```

**Why This Works:**

The Skills Match component is **domain-sensitive by definition**. If a CV contains `[Cardiology, ACLS, Patient Care, IV Therapy]` and the job requires `[SEO, Google Analytics, Campaign Management, Brand Strategy]`, the skills overlap is mathematically **0%**. This zero directly penalizes the final composite score, regardless of how linguistically similar the two documents appear to a general-purpose AI.

**Concrete Example:**

| Comparison | FAISS Score | Skills Match | Final Hybrid Score | Classification |
|---|---|---|---|---|
| Medicine CV ↔ Marketing Job | 55% | 2% | **(55×0.7)+(2×0.3) = 39.1%** | ❌ Weak Fit |
| Medicine CV ↔ Medicine Job | 85% | 65% | **(85×0.7)+(65×0.3) = 79%** | ✅ Strong Fit |

**Why We Recommend This:**
- Both components are already computed in the pipeline — no new models are required.
- It is mathematically transparent and easy to explain.
- It directly addresses the root cause by anchoring the score to domain-relevant skills.

---

### Approach 3 (Future Work): Domain-Specific Model Fine-Tuning

**Core Idea:** Fine-tune the `all-MiniLM-L6-v2` model on a labeled dataset of CV-job pairs, where each pair is annotated with a human-assigned relevance score.

**Why This Would Work:**
- A fine-tuned model would learn to assign low similarity scores to pairs from completely different domains, because it would have seen labeled examples proving these are poor matches.

**Why We Have Not Implemented This:**
- Requires a large labeled training dataset of CV-job pairs, which is not publicly available or trivial to construct.
- Requires GPU training infrastructure and significant time investment.
- For a diploma thesis scope, this is considered **Future Work**.

---

## 5. Summary & Recommendation

| Approach | Status | Effectiveness | Complexity |
|---|---|---|---|
| Raw FAISS Score (initial) | ❌ Removed | Poor — 50% for unrelated domains | None |
| Normalization + Exponential Penalty | ✅ Implemented | Moderate — reduces but doesn't eliminate false positives | Low |
| **Hybrid Semantic + Skills Score** | **⬜ Proposed** | **High — directly targets domain mismatch** | **Low** |
| Model Fine-Tuning | ⬜ Future Work | Very High — but requires labeled data + GPU | Very High |

We propose to implement **Approach 2 (Hybrid Scoring)** as the next immediate step. It is the most technically sound improvement achievable within the current project scope and provides a meaningful, explainable research contribution for the thesis defense.

---

## 6. Second Problem: Misleading Skills Extraction

Beyond the scoring anomaly, we also identified that the **skills shown on match cards** (Matched Skills / Missing Skills) were sometimes **inaccurate or misleading** — showing skills that didn't actually belong to the CV or job domain.

### Root Cause

The current `SkillsExtractor` class operates using a **purely lexical, unsupervised approach**. It extracts skills by:
1. Matching multi-word technical phrases from a predefined pattern list
2. Extracting terms following explicit skill-signal phrases (e.g., "experience with...", "proficient in...")
3. Capturing `CamelCase` and `ALLCAPS` tokens by frequency
4. Capturing short lowercase technical-looking terms (e.g., `sql`, `git`, `rest`)

This approach works well for **technical CVs** (software, data science) where skills appear as proper nouns and acronyms with clear capitalization patterns.

However, it **degrades significantly** for **medical, legal, or business CVs** because:
- Medical skills are not always capitalized consistently (e.g., *patient care, clinical assessment, wound management*)
- The fuzzy substring matching (`if j_skill in c_skill or c_skill in j_skill`) is overly generous — a CV containing the word `"care"` can falsely match a job skill like `"healthcare management"` or `"childcare"`
- Generic capitalized tokens like `"Patient"`, `"Hospital"`, `"Care"` get picked up as "skills" when they are actually just nouns

### Concrete Example

A medical CV containing *"patient care, ACLS, IV therapy"* matched against a marketing job containing *"brand care, customer care strategy"* could produce:
- **Falsely Matched Skills:** `care` (substring match of `"patient care"` and `"customer care"`)
- **Falsely Missing Skills:** Generic marketing terms like `"campaigns"`, `"analytics"` flagged as gaps even though they are irrelevant to the CV domain

### Proposed Solution

**Tighter Substring Matching:** Change the fuzzy overlap from a simple substring check to a **whole-word boundary match** or a minimum character length threshold to avoid single-word false positives:

```python
# Current (too loose):
if j_skill in c_skill or c_skill in j_skill:

# Proposed (stricter):
if j_skill == c_skill or (len(j_skill) > 5 and j_skill in c_skill) or (len(c_skill) > 5 and c_skill in j_skill):
```

**Domain-Aware Phrase Library:** Expand the `phrase_patterns` in `SkillsExtractor` to include medical, legal, and business multi-word phrases, so domain-specific skills are captured as full phrases rather than individual noisy tokens.

**Future Work — NER-Based Extraction:** A Named Entity Recognition (NER) model trained specifically on job/CV documents (e.g., using SpaCy with a skills NER model) would dramatically improve extraction accuracy across all domains, at the cost of additional infrastructure complexity.

---

## 7. Combined Impact

These two problems are directly connected:
- **Inflated cross-domain scores** make the match feel misleading even before the user reads the skills.
- **Inaccurate skills** then further undermine trust in the system when the user sees irrelevant matched/missing skills on the result card.

Addressing both problems together (Hybrid Scoring + Stricter Skills Matching) will produce a significantly more trustworthy and academically defensible system.
