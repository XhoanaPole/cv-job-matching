# Smart CV–Job Matching System

**Bachelor Thesis Project** — University Metropolitan Tirana  
Semantic CV–job matching for junior/entry-level candidates using embeddings, FAISS, and a multi-agent LLM debate protocol.

---

## Overview

This system evaluates the fit between a candidate's CV and a job description through a three-stage pipeline:

1. **Semantic Embedding Matching** — Sentence-Transformers + FAISS vector search to compute similarity scores
2. **LLM Summary & Skills Extraction** — OpenAI-powered skill gap analysis and profile classification
3. **Agentic Debate Protocol** — A multi-agent system (Advocate, Skeptic, Judge) that reasons over each CV–job pair to produce a final hiring recommendation

The system was evaluated on 153 CV–job pairs across 20+ professional domains, benchmarked against Claude, Gemini, and GPT-4o as reference judges.

---

## Results Summary

| System | Accuracy (153 pairs) |
|---|---|
| This system | 77/153 — **50.3%** |
| Claude (reference) | **81%** |
| Gemini (reference) | 71.2% |
| GPT-4o (reference) | 62.7% |

Dataset tiers: 52 Strong matches · 45 Medium matches · 56 Weak matches

---

## Project Structure

```
cv-job-matching/
│
├── src/
│   ├── api/
│   │   └── main.py                  # FastAPI application
│   ├── agentic_debate/
│   │   ├── advocate.py              # Argues for the candidate
│   │   ├── skeptic.py               # Challenges the match
│   │   ├── judge.py                 # Final verdict agent
│   │   ├── orchestrator.py          # Manages the debate flow
│   │   └── roadmap.py               # Career roadmap generation
│   ├── embeddings/
│   │   └── embedder.py              # Sentence-Transformer embeddings
│   ├── matching/
│   │   ├── matcher_v2.py            # Core matching logic (v2)
│   │   ├── llm_summary_v2.py        # OpenAI-powered CV/job summaries
│   │   ├── skills_extractor_v2.py   # Skill gap extraction
│   │   ├── profile_classifier.py    # Seniority & domain classification
│   │   └── domain_classifier.py     # Domain detection
│   ├── preprocessing/
│   │   ├── document_parser.py       # PDF, DOCX, TXT parser
│   │   └── text_cleaning.py         # Text normalization
│   └── vector_store/
│       └── faiss_index.py           # FAISS vector database
│
├── frontend/
│   ├── index_v9.html                # Main UI
│   ├── app_v9.js                    # Frontend logic
│   └── styles_v9.css                # Styles
│
├── data/
│   └── raw/                         # 27 domain folders (CVs + job descriptions)
│       ├── Architecture/
│       ├── Artificial Intelligence and Machine Learning/
│       ├── Business Administration/
│       ├── Civil Engineering/
│       ├── Cybersecurity/
│       ├── Dentistry/
│       ├── Economics/
│       ├── Education and Teaching/
│       ├── Electrical Engineering/
│       ├── Film and Video Production/
│       ├── Finance/
│       ├── Graphic Design/
│       ├── Hospitality and Tourism/
│       ├── Human Resources/
│       ├── Journalism and Media/
│       ├── Law/
│       ├── Logistics and Supply Chain/
│       ├── Marketing/
│       ├── Mechanical Engineering/
│       ├── Medicine/
│       ├── Nursing/
│       ├── Pharmacy/
│       ├── Project Management/
│       ├── Psychology/
│       ├── Social Work/
│       ├── Data Analysis/
│       └── Software Engineering/
│
├── evaluation/
│   ├── ablation_study.py            # Ablation methodology
│   ├── run_all_evaluations.py       # Full evaluation pipeline
│   ├── run_all_pairs.py             # Pair-level evaluation runner
│   ├── run_ablation_semantic.py     # Semantic ablation runner
│   ├── compute_metrics.py           # Metrics computation
│   ├── ablation_results_final.csv   # Final ablation results
│   ├── ablation_semantic_A.csv      # Semantic ablation set A
│   └── ablation_semantic_B.csv      # Semantic ablation set B
│
├── tests/                           # Test suite
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/XhoanaPole/cv-job-matching.git
cd cv-job-matching
```

### 2. Create and activate virtual environment

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the project root:

```
OPENAI_API_KEY=your_openai_api_key_here
```

---

## Running the System

### Option 1: FastAPI Server

```bash
uvicorn src.api.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for the interactive API documentation.

### Option 2: Docker

```bash
docker-compose up --build
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/match` | Match a CV (text) against the job index |
| `POST` | `/match/upload` | Upload a CV file for matching |
| `POST` | `/compare/upload` | Upload CV + job files for a dynamic comparison |
| `POST` | `/compare/text` | Compare pasted CV and job texts (JSON) |
| `POST` | `/compare/debate` | Run the agentic debate on a CV–job pair |
| `POST` | `/jobs/add` | Add a single job to the index |
| `POST` | `/jobs/add_batch` | Add multiple jobs to the index |
| `GET` | `/stats` | Index statistics |
| `GET` | `/` | Health check |

### Example: Match CV to Jobs

```bash
curl -X POST "http://localhost:8000/match" \
  -H "Content-Type: application/json" \
  -d '{
    "cv_text": "Computer Science graduate with Python and ML experience...",
    "top_k": 5
  }'
```

---

## Evaluation

Run the full evaluation pipeline:

```bash
cd evaluation
python run_all_evaluations.py
```

Run the ablation study:

```bash
python ablation_study.py
```

---

## Dataset

20+ professional domains, each containing sample CVs and job descriptions:

Architecture · Artificial Intelligence and Machine Learning · Business Administration · Civil Engineering · Cybersecurity · Dentistry · Economics · Education and Teaching · Electrical Engineering · Film and Video Production · Finance · Graphic Design · Hospitality and Tourism · Human Resources · Journalism and Media · Law · Logistics and Supply Chain · Marketing · Mechanical Engineering · Medicine · Nursing · Pharmacy · Project Management · Psychology · Social Work · Data Analysis · Software Engineering

---

## License

This is a bachelor thesis project for educational purposes.

## Contact

**Xhoana Pole**  
University Metropolitan Tirana  
xhoana.pole23@umt.edu.al
