from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List, Optional
import sys
import os
import tempfile
import shutil
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from preprocessing.text_cleaning import TextCleaner
from preprocessing.document_parser import DocumentParser
from embeddings.embedder import TextEmbedder
from vector_store.faiss_index import FAISSJobIndex
from matching.matcher_v2 import CVJobMatcherV2     # v2 — 5-signal hybrid (active)
from matching.llm_summary_v2 import enrich_matches_with_llm
from agentic_debate.orchestrator import DebateOrchestrator

# Global instances (initialized on startup)
matcher = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the matching system on startup, clean up on shutdown."""
    global matcher

    INDEX_FILE = 'data/processed/faiss.index'
    METADATA_FILE = 'data/processed/metadata.pkl'

    cleaner = TextCleaner(
        remove_emails=True,
        remove_phone=True,
        remove_urls=True,
        min_length=50
    )

    embedder = TextEmbedder(model_name='all-MiniLM-L6-v2')

    faiss_index = FAISSJobIndex.load_or_create(
        INDEX_FILE,
        METADATA_FILE,
        embedding_dim=embedder.embedding_dim
    )

    matcher = CVJobMatcherV2(cleaner, embedder, faiss_index)

    print("- Matching system initialized")
    print(f"- Jobs in index: {matcher.index.index.ntotal}")

    yield  # server runs here

    matcher = None

app = FastAPI(
    title="Smart CV Job Matching API",
    description="Match junior/entry-level students with relevant job opportunities",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for the frontend application
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class JobDescription(BaseModel):
    job_id: str
    description: str

class CompareJob(BaseModel):
    job_id: str
    description: str

class CompareRequest(BaseModel):
    cv_text: str
    jobs: List[CompareJob]

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
    
    # Enrich with LLM Summaries
    if 'matches' in result:
        result['matches'] = enrich_matches_with_llm(result['matches'])
    
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
    
    # Enrich with LLM Summaries
    if 'matches' in result:
        result['matches'] = enrich_matches_with_llm(result['matches'])
    
    return result

@app.post("/compare/upload", response_model=MatchResponse)
async def compare_dynamic_upload(
    cv_file: UploadFile = File(...),
    job_files: List[UploadFile] = File(default=[])
):
    """
    Compare a single CV against a list of job descriptions via multi-part file upload.
    Supports .txt, .pdf, and .docx files.
    """
    if not matcher:
        raise HTTPException(status_code=500, detail="Core models not initialized")

    if not job_files:
        raise HTTPException(status_code=400, detail="No job description files provided")
        
    doc_parser = DocumentParser()
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Save and parse CV
        cv_path = os.path.join(temp_dir, os.path.basename(cv_file.filename))
        with open(cv_path, "wb") as f:
            f.write(await cv_file.read())

        cv_text = doc_parser.parse_file(cv_path)
        if not cv_text:
            raise HTTPException(status_code=400, detail="Failed to parse CV document. Ensure it is a valid format.")

        # Save and parse Jobs
        parsed_jobs = []
        parsed_job_ids = []
        for j_file in job_files:
            if not j_file.filename:
                continue
            j_path = os.path.join(temp_dir, os.path.basename(j_file.filename))
            with open(j_path, "wb") as f:
                f.write(await j_file.read())
            
            j_text = doc_parser.parse_file(j_path)
            if j_text:
                parsed_jobs.append(j_text)
                parsed_job_ids.append(j_file.filename.split('.')[0])
                
        if not parsed_jobs:
            raise HTTPException(status_code=400, detail="Failed to parse any of the provided job description files.")
            
        # 1. Clean jobs
        cleaned_results = matcher.cleaner.clean_batch(parsed_jobs)
        if not cleaned_results:
            raise HTTPException(status_code=400, detail="Job descriptions are too short or invalid after text extraction.")
        
        cleaned_texts = [r['cleaned_text'] for r in cleaned_results]
        valid_job_ids = [parsed_job_ids[r['original_index']] for r in cleaned_results]
        
        # 2. Embed jobs dynamically
        job_embeddings = matcher.embedder.embed_batch(cleaned_texts, show_progress=False)
        
        # 3. Create isolated FAISS index
        temp_index = FAISSJobIndex(embedding_dim=matcher.embedder.embedding_dim)
        temp_index.add_jobs(job_embeddings=job_embeddings, job_ids=valid_job_ids, job_texts=cleaned_texts)

        # 4. Create isolated Matcher — V2 with full 5-signal scoring
        temp_matcher = CVJobMatcherV2(matcher.cleaner, matcher.embedder, temp_index)
        
        # 5. Evaluate CV
        result = temp_matcher.match_cv_to_jobs(
            cv_text=cv_text,
            cv_id=cv_file.filename,
            top_k=len(valid_job_ids)
        )
        
        # Inject texts for client-side debate triggering
        if 'matches' in result:
            for match in result['matches']:
                match['cv_text'] = cv_text
                try:
                    idx = valid_job_ids.index(match['job_id'])
                    match['job_text'] = cleaned_texts[idx]
                except ValueError:
                    match['job_text'] = ""
        
        # 6. Enrich with LLM Summaries (Parallel)
        if 'matches' in result:
            result['matches'] = enrich_matches_with_llm(result['matches'])
        
        return result
        
    finally:
        # Clean up temporary files
        shutil.rmtree(temp_dir, ignore_errors=True)

@app.post("/compare/text", response_model=MatchResponse)
async def compare_text(request: CompareRequest):
    """
    Compare a CV (pasted as plain text) against job descriptions (also pasted as text).
    Mirrors /compare/upload but accepts JSON instead of multipart form data.
    """
    if not matcher:
        raise HTTPException(status_code=500, detail="Core models not initialized")
    if not request.jobs:
        raise HTTPException(status_code=400, detail="No job descriptions provided")
    if not request.cv_text.strip():
        raise HTTPException(status_code=400, detail="CV text cannot be empty")

    cv_text  = request.cv_text
    job_texts = [j.description for j in request.jobs]
    job_ids   = [j.job_id      for j in request.jobs]

    cleaned_results = matcher.cleaner.clean_batch(job_texts)
    if not cleaned_results:
        raise HTTPException(status_code=400, detail="Job descriptions are too short or invalid after cleaning")

    cleaned_texts  = [r['cleaned_text']               for r in cleaned_results]
    valid_job_ids  = [job_ids[r['original_index']]    for r in cleaned_results]

    job_embeddings = matcher.embedder.embed_batch(cleaned_texts, show_progress=False)
    temp_index = FAISSJobIndex(embedding_dim=matcher.embedder.embedding_dim)
    temp_index.add_jobs(job_embeddings=job_embeddings, job_ids=valid_job_ids, job_texts=cleaned_texts)

    temp_matcher = CVJobMatcherV2(matcher.cleaner, matcher.embedder, temp_index)
    result = temp_matcher.match_cv_to_jobs(cv_text=cv_text, cv_id="pasted_cv", top_k=len(valid_job_ids))

    if 'matches' in result:
        for match in result['matches']:
            match['cv_text'] = cv_text
            try:
                idx = valid_job_ids.index(match['job_id'])
                match['job_text'] = cleaned_texts[idx]
            except ValueError:
                match['job_text'] = ""
        result['matches'] = enrich_matches_with_llm(result['matches'])

    return result


class DebateRequest(BaseModel):
    cv_text: str
    job_text: str
    faiss_score: float

@app.post("/compare/debate")
async def compare_debate(request: DebateRequest):
    orchestrator = DebateOrchestrator()
    result = await orchestrator.run_debate(
        cv_text=request.cv_text, 
        job_text=request.job_text, 
        faiss_score=request.faiss_score
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