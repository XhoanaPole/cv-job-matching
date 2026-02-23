from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from preprocessing.text_cleaning import TextCleaner
from embeddings.embedder import TextEmbedder
from vector_store.faiss_index import FAISSJobIndex
from matching.matcher import CVJobMatcher

app = FastAPI(
    title="Smart CV Job Matching API",
    description="Match junior/entry-level students with relevant job opportunities",
    version="1.0.0"
)

# Global instances (initialized on startup)
matcher = None

class JobDescription(BaseModel):
    job_id: str
    description: str

class CVUpload(BaseModel):
    cv_id: str
    text: str

class MatchRequest(BaseModel):
    cv_text: str
    cv_id: Optional[str] = None
    top_k: int = 10

class MatchResponse(BaseModel):
    cv_id: str
    matches: List[dict]
    error: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the matching system on startup."""
    global matcher
    
    # Paths for persistent storage
    INDEX_FILE = 'data/processed/faiss.index'
    METADATA_FILE = 'data/processed/metadata.pkl'
    
    # Initialize components
    cleaner = TextCleaner(
        remove_emails=True,
        remove_phone=True,
        remove_urls=True,
        min_length=50
    )
    
    embedder = TextEmbedder(model_name='all-MiniLM-L6-v2')
    
    # Try to load existing index, or create new one
    faiss_index = FAISSJobIndex.load_or_create(
        INDEX_FILE,
        METADATA_FILE,
        embedding_dim=embedder.embedding_dim
    )
    
    # Create matcher
    matcher = CVJobMatcher(cleaner, embedder, faiss_index)
    
    print("✓ Matching system initialized")
    print(f"✓ Jobs in index: {matcher.index.index.ntotal}")

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "Smart CV Job Matching API",
        "status": "active",
        "jobs_in_index": matcher.index.index.ntotal if matcher else 0
    }

@app.post("/jobs/add", response_model=dict)
async def add_job(job: JobDescription):
    """
    Add a single job description to the index.
    
    Args:
        job: JobDescription with job_id and description text
    """
    if not matcher:
        raise HTTPException(status_code=500, detail="Matcher not initialized")
    
    # Clean job text
    cleaned = matcher.cleaner.clean(job.description)
    if not cleaned:
        raise HTTPException(status_code=400, detail="Job description too short or invalid")
    
    # Generate embedding
    embedding = matcher.embedder.embed_single(cleaned)
    
    # Add to index
    matcher.index.add_jobs(
        job_embeddings=embedding.reshape(1, -1),
        job_ids=[job.job_id],
        job_texts=[cleaned]
    )
    
    return {
        "message": "Job added successfully",
        "job_id": job.job_id,
        "total_jobs": matcher.index.index.ntotal
    }

@app.post("/jobs/add_batch", response_model=dict)
async def add_jobs_batch(jobs: List[JobDescription]):
    """
    Add multiple job descriptions at once.
    
    Args:
        jobs: List of JobDescription objects
    """
    if not matcher:
        raise HTTPException(status_code=500, detail="Matcher not initialized")
    
    if len(jobs) == 0:
        raise HTTPException(status_code=400, detail="No jobs provided")
    
    # Extract texts and IDs
    job_texts = [job.description for job in jobs]
    job_ids = [job.job_id for job in jobs]
    
    # Clean and embed
    cleaned_results = matcher.cleaner.clean_batch(job_texts)
    
    if len(cleaned_results) == 0:
        raise HTTPException(status_code=400, detail="No valid jobs after cleaning")
    
    cleaned_texts = [r['cleaned_text'] for r in cleaned_results]
    original_indices = [r['original_index'] for r in cleaned_results]
    valid_job_ids = [job_ids[i] for i in original_indices]
    
    # Generate embeddings
    embeddings = matcher.embedder.embed_batch(cleaned_texts)
    
    # Add to index
    matcher.index.add_jobs(
        job_embeddings=embeddings,
        job_ids=valid_job_ids,
        job_texts=cleaned_texts
    )
    
    return {
        "message": "Jobs added successfully",
        "jobs_added": len(valid_job_ids),
        "jobs_skipped": len(jobs) - len(valid_job_ids),
        "total_jobs": matcher.index.index.ntotal
    }

@app.post("/match", response_model=MatchResponse)
async def match_cv(request: MatchRequest):
    """
    Match a CV to the top-K most similar jobs.
    
    Args:
        request: MatchRequest with cv_text and optional cv_id, top_k
    """
    if not matcher:
        raise HTTPException(status_code=500, detail="Matcher not initialized")
    
    if matcher.index.index.ntotal == 0:
        raise HTTPException(status_code=400, detail="No jobs in index. Add jobs first.")
    
    result = matcher.match_cv_to_jobs(
        cv_text=request.cv_text,
        cv_id=request.cv_id,
        top_k=request.top_k
    )
    
    return result

@app.post("/match/upload", response_model=MatchResponse)
async def match_cv_file(file: UploadFile = File(...), top_k: int = 10):
    """
    Upload a CV file and get job matches.
    
    Args:
        file: CV file (txt format)
        top_k: Number of top matches to return
    """
    if not matcher:
        raise HTTPException(status_code=500, detail="Matcher not initialized")
    
    if matcher.index.index.ntotal == 0:
        raise HTTPException(status_code=400, detail="No jobs in index. Add jobs first.")
    
    # Read file content
    content = await file.read()
    cv_text = content.decode('utf-8')
    
    result = matcher.match_cv_to_jobs(
        cv_text=cv_text,
        cv_id=file.filename,
        top_k=top_k
    )
    
    return result

@app.get("/stats")
async def get_stats():
    """Get system statistics."""
    if not matcher:
        raise HTTPException(status_code=500, detail="Matcher not initialized")
    
    return {
        "total_jobs": matcher.index.index.ntotal,
        "embedding_dimension": matcher.index.embedding_dim,
        "model": "all-MiniLM-L6-v2"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)