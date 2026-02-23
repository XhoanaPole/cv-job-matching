# Smart CV Job Matching System

Bachelor Thesis Project: Semantic job matching for junior/entry-level students using embeddings and FAISS.

## Overview

This system matches student CVs with job descriptions using:
- **Text preprocessing** to normalize CVs and job descriptions
- **Sentence-Transformers** to generate semantic embeddings
- **FAISS vector database** for efficient similarity search
- **FastAPI** to expose matching functionality via REST API

## Project Structure

```
cv-job-matching/
├── data/
│   ├── raw/                    # Raw CVs and job descriptions
│   │   ├── cvs/
│   │   └── job_descriptions/
│   └── processed/              # Cleaned texts and embeddings
│
├── src/
│   ├── preprocessing/
│   │   └── text_cleaning.py    # Text normalization
│   ├── embeddings/
│   │   └── embedder.py         # Embedding generation
│   ├── vector_store/
│   │   └── faiss_index.py      # FAISS vector database
│   ├── matching/
│   │   └── matcher.py          # Matching logic
│   └── api/
│       └── main.py             # FastAPI application
│
├── notebooks/
│   ├── explore_texts.ipynb     # Data exploration
│   └── similarity_tests.ipynb  # Similarity experiments
│
├── requirements.txt
└── README.md
```

## Installation

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Download NLTK Data (optional)

```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
```

## Quick Start

### Option 1: Python Script

```python
from src.preprocessing.text_cleaning import TextCleaner
from src.embeddings.embedder import TextEmbedder
from src.vector_store.faiss_index import FAISSJobIndex
from src.matching.matcher import CVJobMatcher

# Initialize components
cleaner = TextCleaner()
embedder = TextEmbedder(model_name='all-MiniLM-L6-v2')
faiss_index = FAISSJobIndex(embedding_dim=embedder.embedding_dim)

# Add jobs to index
job_texts = ["Job description 1...", "Job description 2..."]
job_ids = ["job_1", "job_2"]

cleaned_jobs = cleaner.clean_batch(job_texts)
job_embeddings = embedder.embed_batch([r['cleaned_text'] for r in cleaned_jobs])
faiss_index.add_jobs(job_embeddings, job_ids)

# Match CV
matcher = CVJobMatcher(cleaner, embedder, faiss_index)
cv_text = "Student CV text..."
results = matcher.match_cv_to_jobs(cv_text, cv_id="cv_1", top_k=5)

print(results)
```

### Option 2: FastAPI Server

```bash
# Start the API server
cd src/api
python main.py

# Or use uvicorn
uvicorn main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for interactive API documentation.

## API Endpoints

### 1. Add Job Descriptions

```bash
curl -X POST "http://localhost:8000/jobs/add" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "job_001",
    "description": "Junior Software Developer position..."
  }'
```

### 2. Match CV to Jobs

```bash
curl -X POST "http://localhost:8000/match" \
  -H "Content-Type: application/json" \
  -d '{
    "cv_text": "Computer Science student with Python skills...",
    "cv_id": "cv_001",
    "top_k": 5
  }'
```

Response:
```json
{
  "cv_id": "cv_001",
  "matches": [
    {"job_id": "job_001", "score": 0.82},
    {"job_id": "job_003", "score": 0.78}
  ]
}
```

### 3. Upload CV File

```bash
curl -X POST "http://localhost:8000/match/upload" \
  -F "file=@path/to/cv.txt" \
  -F "top_k=10"
```

## Usage Examples

### Example 1: Build Complete System

```python
import os
from pathlib import Path
from src.preprocessing.text_cleaning import TextCleaner, load_text_file
from src.embeddings.embedder import TextEmbedder, EmbeddingPipeline
from src.vector_store.faiss_index import FAISSJobIndex
from src.matching.matcher import CVJobMatcher

# Initialize
cleaner = TextCleaner(remove_emails=True, remove_phone=True)
embedder = TextEmbedder(model_name='all-MiniLM-L6-v2')

# Load job descriptions
job_dir = Path('data/raw/job_descriptions')
jobs = []
job_ids = []
for file in job_dir.glob('*.txt'):
    jobs.append(load_text_file(file))
    job_ids.append(file.stem)

# Process jobs
pipeline = EmbeddingPipeline(cleaner, embedder)
job_data = pipeline.process_texts(jobs, job_ids)

# Create FAISS index
faiss_index = FAISSJobIndex(embedding_dim=embedder.embedding_dim)
faiss_index.add_jobs(
    job_data['embeddings'],
    job_data['text_ids'],
    job_data['cleaned_texts']
)

# Save index
faiss_index.save('data/processed/faiss.index', 'data/processed/metadata.pkl')

# Create matcher
matcher = CVJobMatcher(cleaner, embedder, faiss_index)

# Match CVs
cv_dir = Path('data/raw/cvs')
for cv_file in cv_dir.glob('*.txt'):
    cv_text = load_text_file(cv_file)
    results = matcher.match_cv_to_jobs(cv_text, cv_id=cv_file.stem, top_k=5)
    print(f"\n{cv_file.name}:")
    for match in results['matches']:
        print(f"  - {match['job_id']}: {match['score']:.3f}")
```

### Example 2: Jupyter Notebook Analysis

See `notebooks/explore_texts.ipynb` for interactive exploration.

## Design Choices & Justification

### 1. Sentence-Transformers Model
- **Choice**: `all-MiniLM-L6-v2`
- **Why**: Lightweight (384 dimensions), fast, good semantic understanding
- **Alternative**: `all-mpnet-base-v2` (768 dimensions, more accurate but slower)

### 2. FAISS Index Type
- **Choice**: `IndexFlatL2` (brute-force L2 distance)
- **Why**: Small dataset, guaranteed best results, simple
- **Alternative**: Use `IndexIVFFlat` for large datasets (>100k jobs)

### 3. Text Preprocessing
- **Removes**: emails, phone numbers, URLs
- **Normalizes**: lowercase, whitespace
- **Why**: Focus on skills and experience, not formatting

### 4. Similarity Metric
- **Choice**: L2 distance converted to similarity score
- **Formula**: `1 / (1 + distance)`
- **Why**: Intuitive scores in [0, 1] range

## Evaluation Strategy

### 1. Manual Inspection
Create test cases for:
- Junior developer CV → software jobs
- CV with no experience → entry-level jobs
- Student with specific skills → matching roles

### 2. Compare Configurations
Test different parameters:
- With/without text cleaning
- Different embedding models
- Top-K values (5, 10, 20)

### 3. Case Studies
Document 3-5 examples showing:
- CV text
- Top 3 matched jobs
- Why matches make sense (or don't)

## Development Workflow

1. **Prepare Data**: Add CV and job text files to `data/raw/`
2. **Explore**: Use notebooks to test preprocessing and embeddings
3. **Build Index**: Run script to create FAISS index
4. **Test Matching**: Use API or Python to test matches
5. **Evaluate**: Document results and design choices
6. **Iterate**: Adjust parameters based on results

## Thesis Deliverables Checklist

- [ ] Text preprocessing pipeline
- [ ] Embedding generation system
- [ ] FAISS vector database
- [ ] Matching algorithm
- [ ] FastAPI REST API
- [ ] Evaluation results
- [ ] Documentation of design choices
- [ ] Code repository with examples

## Troubleshooting

### Issue: Low similarity scores
- Check if text cleaning is too aggressive
- Try different embedding models
- Ensure CV and job texts have sufficient content

### Issue: Out of memory
- Process CVs in smaller batches
- Use `faiss-cpu` instead of `faiss-gpu`
- Reduce embedding dimension

### Issue: Slow matching
- Use batch processing for multiple CVs
- Consider approximate FAISS index for large datasets

## Next Steps

1. Collect sample CVs and job descriptions
2. Run initial experiments in notebooks
3. Build and test the full pipeline
4. Evaluate results and document findings
5. Write thesis chapters explaining approach

## License

This is a bachelor thesis project for educational purposes.

## Contact

Xhoana Pole  
University Metropolitan Tirana 
xhoana.pole23@umt.edu.al