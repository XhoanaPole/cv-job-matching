# AI-Powered CV-Job Matching System
### Diploma Thesis — Comprehensive Project Summary
**Author:** Xhoana Pole

---

## 1. Project Goal & Motivation

The recruitment and hiring process is one of the most time-intensive workflows in modern organizations. Human recruiters routinely sift through hundreds of CVs for a single job opening, relying on keyword-based tools that fail to understand the semantic meaning behind a candidate's experience. Similarly, job seekers struggle to objectively evaluate how well their profile aligns with a target role.

The goal of this project is to build an **AI-Powered CV-Job Matching System** — a fully functional intelligent web platform that **automatically and semantically matches a candidate's CV against one or more job descriptions**, producing a structured similarity score, a skill overlap analysis, and actionable gap insights. The system is built to demonstrate the real-world application of **Natural Language Processing (NLP) and vector-space AI** within a production-grade software architecture.

---

## 2. Evolutionary Development Journey

### Phase 1 — TF-IDF Baseline (Classical NLP)
The project was initially prototyped using **TF-IDF (Term Frequency–Inverse Document Frequency)**, a classical statistical NLP technique. In this phase, CV and job description texts were tokenized and converted into sparse numerical vectors, where each dimension represented the relative importance of a word across the document corpus. Cosine similarity was then computed between the CV vector and each job description vector to produce a basic relevance score.

**Limitations discovered in Phase 1:**
- TF-IDF is purely frequency-based and has no understanding of semantic meaning.
- Synonyms and related concepts (e.g., *"developed"* vs *"engineered"*, *"ML"* vs *"machine learning"*) score as zero-overlap.
- Scores were brittle and highly sensitive to exact keyword overlap between documents.
- The approach failed to capture the contextual meaning of multi-word technical phrases.

### Phase 2 — Semantic Embeddings & FAISS (Production Architecture)
In response to the limitations of Phase 1, the system was completely redesigned around **dense semantic vector embeddings** using the **SentenceTransformers library** with the pre-trained `all-MiniLM-L6-v2` model. This model encodes entire sentences and paragraphs into a 384-dimensional dense vector space where semantically similar content is geometrically close.

To enable fast and scalable similarity search across multiple job descriptions, the project integrates **FAISS (Facebook AI Similarity Search)** — a production-grade vector indexing library developed by Meta AI Research. FAISS stores the encoded job description vectors in a persistent index on disk (`data/processed/faiss.index`) and performs extremely fast nearest-neighbour L2 distance searches to rank job matches against any given CV at runtime.

This shift from sparse keyword vectors to rich semantic embeddings is the core academic and technical contribution of the project.

---

## 3. System Architecture

The application is built as a **decoupled full-stack system** with a FastAPI Python backend and a Vanilla JavaScript frontend.

### Backend — Python FastAPI
| Component | Module | Responsibility |
|---|---|---|
| **API Layer** | `src/api/main.py` | FastAPI REST endpoints, CORS, multipart file processing |
| **Document Parser** | `src/preprocessing/document_parser.py` | Text extraction from `.txt`, `.pdf`, `.docx`; live URL web scraping via BeautifulSoup4 |
| **Text Cleaner** | `src/preprocessing/text_cleaning.py` | Lowercasing, stopword removal, punctuation normalization |
| **Embedder** | `src/embeddings/embedder.py` | `all-MiniLM-L6-v2` SentenceTransformer — encodes text to 384-dim vectors |
| **FAISS Index** | `src/vector_store/faiss_index.py` | Persistent vector store; L2 nearest-neighbour search |
| **Matcher** | `src/matching/matcher.py` | Orchestrates embedding + FAISS query; returns ranked similarity scores |
| **Skills Extractor** | `src/matching/skills_extractor.py` | Dynamic NLP extraction of technical terms, frameworks, and methodologies |

### Frontend — Vanilla HTML / CSS / JavaScript
A premium single-page SaaS dashboard with:
- Multi-view routing (Dashboard, Analytics, My Resumes, Settings)
- Drag-and-drop file upload for `.pdf`, `.docx`, `.txt` CVs and job descriptions
- Live URL input for direct web scraping of online job postings
- SVG animated circular progress rings visualizing FAISS similarity scores
- Dynamic CSS Theme Engine (5 colour palettes, persisted in `localStorage`)
- 3D card tilt physics and mouse-tracking radial cursor glow via hardware-accelerated JavaScript

---

## 4. Core Technical Features

### 4.1 Multi-Format Document Parsing
The `DocumentParser` class extracts clean plaintext from:
- `.txt` — direct read
- `.pdf` — via `pdfplumber` and `PyPDF2` with page concatenation
- `.docx` — via `python-docx` paragraph traversal
- **Live URLs** — via `requests` + `BeautifulSoup4` HTML tag filtering (removes scripts, navbars, footers; preserves article body text)

### 4.2 Semantic Similarity Scoring
The `all-MiniLM-L6-v2` model encodes both the CV and each job description into 384-dimensional floating-point vectors. The FAISS index stores job description vectors and, at query time, returns a ranked list of **L2 distances** to the CV vector. These distances are converted to a normalized **0–100% similarity score** displayed as an animated SVG progress ring in the frontend.

### 4.3 Dynamic Skills Extraction (Blacklist-Driven Pipeline)
The `SkillsExtractor` was evolved through two approaches:

**Original (whitelist-based):** A hardcoded dictionary of ~80 known technologies. Reliable for listed terms but completely blind to anything outside the dictionary (e.g., `LangChain`, `Pinecone`, `Streamlit`).

**Current (blacklist-driven, frequency-weighted):** A four-stage pipeline:
1. **Multi-word technical phrase detection** — regex patterns for terms like `"machine learning"`, `"natural language processing"`, `"CI/CD"`, `"REST API"`
2. **Indicator-context extraction** — parses phrases following signal words like `"experience with"`, `"proficient in"`, `"worked with"`
3. **Frequency-ranked capitalized token extraction** — any properly capitalized or acronym-style token not in the noise blacklist is captured and ranked by frequency of occurrence
4. **Lowercase code-style term detection** — catches short technical tokens like `sql`, `git`, `bash`

Skills are matched with **fuzzy substring overlap** so `"react"` matches `"react.js"`, `"scikit"` matches `"scikit-learn"`, etc.

### 4.4 Web Scraping Integration
The system accepts live job posting URLs directly in the UI. The backend uses `requests` to fetch the target page and `BeautifulSoup4` to strip navigation, header, footer, and script elements, extracting only the meaningful article text. This extracted content is then passed directly into the same FAISS embedding pipeline as any uploaded file.

---

## 5. Technology Stack

| Layer | Technologies |
|---|---|
| **Language** | Python 3.10+, JavaScript (ES2022) |
| **API Framework** | FastAPI, Uvicorn, Pydantic |
| **AI / NLP** | SentenceTransformers (`all-MiniLM-L6-v2`), FAISS-CPU, NLTK |
| **Document Parsing** | pdfplumber, PyPDF2, python-docx |
| **Web Scraping** | requests, BeautifulSoup4 |
| **Frontend** | Vanilla HTML5, CSS3, JavaScript (no framework) |
| **Data Storage** | File-system persistent FAISS index (`.index` binary) |
| **Version Control** | Git, GitHub |

---

## 6. Future Work

The following extensions are documented for future development cycles:

1. **Multi-Agent Architecture** — Decomposing the pipeline into an Orchestrator Agent, Extraction Agent, Embedding Agent, and Career Coaching Agent using frameworks like CrewAI or LangGraph.
2. **LLM Integration** — Using GPT-4 or an open-source LLM to generate personalised cover letters and interview preparation materials from gap analysis results.
3. **Database Persistence** — Migrating the in-memory FAISS index to a persistent backend (PostgreSQL + pgvector or Pinecone) with user account management and OAuth2 authentication.
4. **OCR Support** — Integrating Tesseract OCR to process scanned PDF documents.
5. **Playwright Scraping** — Adding Playwright as a fallback web scraper for JavaScript-rendered job posting pages (LinkedIn, Indeed).

---
---

## ACADEMIC ABSTRACT

**Title:** Semantic CV-Job Matching Using Dense Vector Embeddings and Approximate Nearest-Neighbour Search

**Abstract:**

This thesis presents the design, implementation, and evaluation of an AI-powered Curriculum Vitae (CV) to job description matching system that leverages dense semantic vector representations and large-scale approximate nearest-neighbour search to compute meaningful similarity scores between candidate profiles and job postings. The central motivation of this work is to address the fundamental shortcomings of classical keyword-based recruitment matching systems, which fail to capture the semantic relationships between synonymous terms, contextually related technologies, and domain-specific competencies.

The system was developed in two distinct evolutionary phases. In the first phase, a baseline was established using **TF-IDF (Term Frequency–Inverse Document Frequency)** vectorization coupled with cosine similarity, which, while interpretable, demonstrated severe limitations in semantic coverage due to its statistical, frequency-only representational model. In the second and primary phase, the architecture was redesigned around **SentenceTransformers** — specifically the `all-MiniLM-L6-v2` pre-trained transformer model — which encodes entire text passages into 384-dimensional dense embedding spaces where semantic proximity is geometrically preserved. To enable fast similarity retrieval across multiple indexed job descriptions, the system integrates **FAISS (Facebook AI Similarity Search)**, an industry-grade approximate nearest-neighbour indexing library, storing document embeddings in a persistent binary index and supporting real-time L2-distance ranking at query time.

The platform is deployed as a full-stack application: a RESTful **FastAPI** backend handles multi-format document ingestion (PDF, DOCX, TXT) and live web scraping of online job postings via BeautifulSoup4, while a premium Vanilla JavaScript frontend delivers an interactive SaaS-grade dashboard interface complete with animated similarity visualizations, multi-view navigation, and a dynamic CSS theming engine. A supplementary **dynamic skills extraction pipeline** — designed as a frequency-weighted, blacklist-driven NLP module — provides structured Aligned Skills and Growth Opportunity panels alongside the primary semantic score, supporting candidates in understanding the qualitative dimensions of each match.

Experimental evaluation demonstrates that semantic embedding-based matching produces substantially higher-quality relevance rankings than TF-IDF baselines for domain-specific technical documents. The system is positioned as a proof-of-concept for AI-assisted recruitment tooling and provides a foundation for future extensions including multi-agent orchestration, large language model integration for personalized career coaching, and database-persistent user profile management.

**Keywords:** Natural Language Processing, Semantic Similarity, Sentence Embeddings, FAISS, Approximate Nearest-Neighbour Search, TF-IDF, Recruitment AI, CV Matching, SentenceTransformers, FastAPI
