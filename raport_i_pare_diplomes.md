# First Thesis Report

**University Metropolitan Tirana**  
**Faculty of Informatics and Engineering**  
**Programme: Computer Science / Software Engineering**

---

**Student:** Xhoana Pole  
**E-mail:** xhoana.pole23@umt.edu.al  
**Date:** March 2026  
**Submission Deadline:** 03 April 2026

---

## 1. Thesis Title

**"AI-Powered CV-Job Matching System Using Semantic Embeddings and Approximate Nearest-Neighbour Search"**

---

## 2. Thesis Description

### Context and Motivation

The recruitment and hiring process is one of the most time-intensive workflows in modern organizations. Hiring managers routinely review hundreds of CVs for a single job opening, relying on keyword-based filtering tools that fundamentally fail to understand the semantic meaning behind a candidate's experience or skills. These tools reject a CV simply because an applicant wrote *"programmer"* when the job posting required *"software developer"* — semantically equivalent terms treated as completely unrelated.

From the candidate's perspective, the problem is equally challenging: job seekers lack objective, data-driven feedback on how well their profile aligns with a specific role and where they should focus their development efforts.

### Problem Being Solved

This project designs and implements an **intelligent web platform** that automatically and semantically compares a candidate's CV against one or more job descriptions, producing:

- A **similarity score** expressed as a percentage (0–100%)
- A structured list of **Aligned Skills** — competencies present in both the CV and the job posting
- An identification of **Skill Gaps / Growth Opportunities** — requirements in the job posting not yet reflected in the CV

The system achieves this not through keyword comparison, but by converting text documents into **high-dimensional numerical vectors** (semantic embeddings), where sentences and phrases with similar meaning are geometrically close to each other in vector space. This represents a fundamental shift from classical statistical NLP to modern deep learning-based language understanding.

---

## 3. Objectives

The primary objectives of this work are:

1. **Build a multi-format document processing pipeline** — clean, normalize, and extract text from CVs and job descriptions provided as PDF, DOCX, TXT files, or live web URLs via scraping.

2. **Implement semantic embeddings** — encode documents using the pre-trained *all-MiniLM-L6-v2* SentenceTransformer model, transforming each document into a 384-dimensional dense vector where semantic proximity is geometrically preserved.

3. **Integrate FAISS** (*Facebook AI Similarity Search*) — build a persistent vector index enabling ultra-fast nearest-neighbour similarity search between CV embeddings and indexed job description embeddings.

4. **Develop a RESTful backend API** (FastAPI) — expose all matching functionality via REST endpoints supporting file uploads, live URL scraping, and JSON-based interactions.

5. **Build a premium SaaS-grade frontend** — a modern single-page web dashboard with animated similarity visualizations, multi-view navigation, a dynamic skills analysis panel, and a CSS theming engine.

6. **Conduct a comparative evaluation** — benchmark TF-IDF (classical NLP baseline) against semantic embeddings on the same document set, documenting the qualitative and quantitative differences in matching accuracy.

---

## 4. Brief Literature Review

### 4.1 Classical NLP — TF-IDF

**TF-IDF (Term Frequency — Inverse Document Frequency)**, formalized by Salton & Buckley (1988), is the foundational technique for text document ranking and retrieval. It quantifies the importance of each word in a document relative to a corpus of documents. While computationally lightweight and interpretable, TF-IDF has a fundamental semantic blindspot: it operates purely on word frequency statistics. Two synonymous terms — *"engineer"* and *"developer"* — score zero overlap with each other regardless of their actual conceptual relationship.

### 4.2 Transformer Models and Sentence Embeddings

The introduction of **BERT** (Devlin et al., 2018) represented a paradigm shift in NLP. BERT learns contextual, bidirectional representations of language by pre-training on massive text corpora using masked language modeling and next-sentence prediction objectives. **SentenceTransformers** (Reimers & Gurevych, 2019) extends the BERT architecture specifically for the task of encoding full sentences and paragraphs into fixed-size dense vector representations. The *all-MiniLM-L6-v2* model used in this project is a distilled, efficiency-optimized member of this family — producing 384-dimensional embeddings with significantly reduced inference latency while retaining strong semantic representation quality.

### 4.3 Approximate Nearest-Neighbour Search with FAISS

**FAISS** (*Facebook AI Similarity Search*), developed by Meta AI Research (Johnson et al., 2019), is an industry-standard library for efficient similarity search and clustering of dense vectors. FAISS supports multiple index types suited to different scale requirements: *IndexFlatL2* provides exact brute-force L2 distance search optimal for smaller document collections (as used in this project), while *IndexIVFFlat* and *IndexHNSW* support approximate search over billions of vectors. FAISS stores vectors in a persistent binary index on disk, enabling fast retrieval across sessions without re-embedding.

### 4.4 AI-Assisted Recruitment Systems

Prior work in intelligent recruitment includes **LinkedIn's personalized job recommendation system** (Kenthapadi et al., 2017), which leverages collaborative filtering and deep learning to match candidates to roles at scale. More recent research has explored knowledge graph-based approaches to skill relationship modeling (Joho et al., 2020) and transformer-based CV parsing with named entity recognition for structured skill extraction. Specialized datasets and shared tasks such as **SkillSpan** and models like **JobBERT** (Zhang et al., 2022) demonstrate a growing research community focused on domain-specific NLP for the labour market.

---

## 5. Methodology / Approach

### 5.1 Two-Phase Evolutionary Development

**Phase 1 — TF-IDF Baseline:**
The system was first prototyped using TF-IDF vectorization with cosine similarity as a methodological baseline. This phase served to establish a performance reference point and empirically surface the limitations of classical approaches: poor semantic coverage, sensitivity to exact keyword overlap, and inability to generalize across synonymous technical terminology.

**Phase 2 — Semantic Embeddings + FAISS (Final Architecture):**
The architecture was completely redesigned around dense semantic vector representations and approximate nearest-neighbour search, directly addressing every limitation identified in Phase 1. This redesign constitutes the primary academic and technical contribution of the project.

### 5.2 System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Browser)                       │
│          HTML5 / CSS3 / Vanilla JavaScript                      │
│   • Drag-and-drop file upload (PDF, DOCX, TXT)                  │
│   • Live URL input for job posting scraping                     │
│   • Animated SVG similarity score rings (0–100%)                │
│   • Aligned Skills & Growth Opportunities panels                │
│   • Dynamic CSS Theme Engine (5 colour palettes)                │
└───────────────────────┬─────────────────────────────────────────┘
                        │ HTTP REST (multipart / JSON)
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                  BACKEND — FastAPI (Python)                     │
│                                                                 │
│  ┌──────────────┐    ┌──────────────────┐   ┌───────────────┐  │
│  │  Document    │    │  Text Cleaning   │   │  Skills       │  │
│  │  Parser      │───▶│  Pipeline        │──▶│  Extractor    │  │
│  │  PDF/DOCX/   │    │  NLTK stopwords  │   │  (regex NLP + │  │
│  │  TXT / URL   │    │  + normalization │   │  blacklist)   │  │
│  └──────────────┘    └────────┬─────────┘   └───────────────┘  │
│                               │                                 │
│                               ▼                                 │
│                  ┌────────────────────────┐                     │
│                  │  SentenceTransformers  │                     │
│                  │   all-MiniLM-L6-v2     │                     │
│                  │   [384-dim vectors]    │                     │
│                  └───────────┬────────────┘                     │
│                              │                                  │
│             ┌────────────────┴────────────────┐                 │
│             ▼                                 ▼                 │
│  ┌─────────────────────┐          ┌────────────────────────┐    │
│  │   FAISS Index       │          │  Score Normalisation   │    │
│  │   (IndexFlatL2)     │─────────▶│  L2 distance → 0–100% │    │
│  │   [persistent disk] │          │  similarity score      │    │
│  └─────────────────────┘          └────────────────────────┘    │
└──────────────────────────────────────────────────────────────── ┘
                        │ JSON Response
                        ▼
        { score, aligned_skills, growth_opportunities }
```

### 5.3 Technology Stack

| Layer | Technologies |
|---|---|
| **Language** | Python 3.10+, JavaScript (ES2022) |
| **API Framework** | FastAPI, Uvicorn, Pydantic |
| **AI / NLP** | SentenceTransformers (`all-MiniLM-L6-v2`), FAISS-CPU, NLTK |
| **Document Parsing** | pdfplumber, PyPDF2, python-docx |
| **Web Scraping** | requests, BeautifulSoup4 |
| **Frontend** | Vanilla HTML5, CSS3, JavaScript (no framework) |
| **Data Storage** | File-system persistent FAISS binary index |
| **Version Control** | Git, GitHub |

---

## 6. Expected Results

By the end of this project, the following deliverables are expected:

1. **A fully functional matching system** — a complete, tested web application accessible from the browser, capable of semantically comparing CVs with job descriptions in real time and returning structured match results.

2. **A comparative evaluation report** — a documented benchmark comparing TF-IDF and semantic embedding approaches on the same document pairs, with concrete examples demonstrating the qualitative superiority of the semantic approach.

3. **Qualitative case studies** — 3–5 end-to-end examples showing how the system processes student CVs, identifies aligned competencies, and highlights skill development priorities.

4. **A complete thesis document** — structured academic report covering introduction, literature review, methodology, implementation, evaluation, and conclusions.

5. **A documented source code repository** — a clean GitHub repository with code comments, installation instructions, and usage examples.

---

## 7. Work Plan

| Phase | Period | Key Activities | Status |
|---|---|---|---|
| **Phase 0 — Planning & Research** | January 2026 | Literature review, objective definition, repository setup | ✅ Complete |
| **Phase 1 — TF-IDF Baseline** | January – February 2026 | Classical prototype implementation, limitation analysis | ✅ Complete |
| **Phase 2 — Semantic Architecture** | February 2026 | SentenceTransformers + FAISS integration, multi-format parsing | ✅ Complete |
| **Phase 3 — Backend API** | February – March 2026 | FastAPI endpoints, skills extraction, URL scraping, testing | ✅ Complete |
| **Phase 4 — Frontend Dashboard** | March 2026 | Premium SaaS UI, visualizations, dynamic themes, multi-view navigation | ✅ Complete |
| **Phase 5 — Evaluation & Testing** | April 2026 | Case studies, TF-IDF vs. embeddings benchmark, result documentation | 🔄 In Progress |
| **Phase 6 — Final Thesis Report** | April – May 2026 | Academic writing, revision, final submission | ⏳ Planned |

---

## References

- Reimers, N., & Gurevych, I. (2019). *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks.* Proceedings of EMNLP 2019.
- Johnson, J., Douze, M., & Jégou, H. (2019). *Billion-scale similarity search with GPUs.* IEEE Transactions on Big Data, 7(3), 535–547.
- Devlin, J., Chang, M. W., Lee, K., & Toutanova, K. (2018). *BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding.* Proceedings of NAACL 2019.
- Kenthapadi, K., Le, B., & Venkataraman, G. (2017). *Personalized Job Recommendation System at LinkedIn.* KDD Workshop on Data Science for Human Resources.
- Salton, G., & Buckley, C. (1988). *Term-weighting approaches in automatic text retrieval.* Information Processing & Management, 24(5), 513–523.
