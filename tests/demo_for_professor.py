"""
Complete CV-Job Matching System Demo
For Bachelor Thesis Presentation

Author: [Your Name]
Date: January 2026

This script demonstrates the complete workflow:
1. Load structured data from category folders
2. Clean and preprocess text
3. Generate embeddings
4. Build FAISS index
5. Match CVs to jobs
6. Display results with analysis
"""

import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.append('src')

from preprocessing.text_cleaning import TextCleaner
from embeddings.embedder import TextEmbedder, EmbeddingPipeline
from vector_store.faiss_index import FAISSJobIndex
from matching.matcher import CVJobMatcher
from preprocessing.document_parser import DocumentParser


# ============================================================
# CONFIGURATION
# ============================================================

BASE_PATH = Path('data/raw')
INDEX_FILE = 'data/processed/faiss.index'
METADATA_FILE = 'data/processed/metadata.pkl'
RESULTS_FILE = 'data/processed/matching_results.txt'

# Categories you're testing
CATEGORIES = ['Medicine', 'Marketing', 'Data Analysis']


# ============================================================
# DATA LOADING
# ============================================================

def load_category_data(category_path: Path):
    """Load all CVs and jobs from a category folder."""
    category_name = category_path.name
    
    cvs = []
    cv_ids = []
    jobs = []
    job_ids = []
    
    # Initialize parser
    parser = DocumentParser()
    
    print(f"  Loading from: {category_path.name}")
    
    # Load ALL file types (.txt, .docx, .pdf)
    for file in sorted(category_path.iterdir()):
        # Skip directories
        if file.is_dir():
            continue
        
        # Check if supported format
        if file.suffix.lower() not in ['.txt', '.docx', '.pdf']:
            continue
        
        # Parse the file
        content = parser.parse_file(file)
        
        if not content:
            print(f"      Failed to parse: {file.name}")
            continue
        
        # Determine if it's a CV or job
        if 'cv' in file.stem.lower():
            cvs.append(content)
            cv_ids.append(f"{category_name}_{file.stem}")
            print(f"     CV: {file.name} ({len(content)} chars)")
        else:
            jobs.append(content)
            job_ids.append(f"{category_name}_{file.stem}")
            print(f"     Job: {file.name} ({len(content)} chars)")
    
    return {
        'category': category_name,
        'cvs': cvs,
        'cv_ids': cv_ids,
        'jobs': jobs,
        'job_ids': job_ids
    }



def load_all_data():
    """Load all CVs and jobs from all categories."""
    all_cvs = []
    all_cv_ids = []
    all_jobs = []
    all_job_ids = []
    category_info = {}
    
    print("\n" + "=" * 70)
    print("STEP 1: LOADING DATA")
    print("=" * 70)
    
    for category_name in CATEGORIES:
        category_path = BASE_PATH / category_name
        
        if not category_path.exists():
            print(f"\n  Warning: Category folder not found: {category_name}")
            continue
        
        print(f"\n Category: {category_name}")
        data = load_category_data(category_path)
        
        all_cvs.extend(data['cvs'])
        all_cv_ids.extend(data['cv_ids'])
        all_jobs.extend(data['jobs'])
        all_job_ids.extend(data['job_ids'])
        
        category_info[category_name] = {
            'cvs': len(data['cvs']),
            'jobs': len(data['jobs'])
        }
        
        print(f"  → {len(data['cvs'])} CV(s), {len(data['jobs'])} job(s)")
    
    print("\n" + "-" * 70)
    print(f"TOTAL LOADED: {len(all_cvs)} CVs, {len(all_jobs)} jobs")
    print("-" * 70)
    
    return {
        'cvs': all_cvs,
        'cv_ids': all_cv_ids,
        'jobs': all_jobs,
        'job_ids': all_job_ids,
        'category_info': category_info
    }


# ============================================================
# TEXT PREPROCESSING
# ============================================================

def preprocess_data(data, cleaner):
    """Clean all CVs and jobs."""
    print("\n" + "=" * 70)
    print("STEP 2: TEXT PREPROCESSING")
    print("=" * 70)
    
    print("\n Cleaning job descriptions...")
    cleaned_jobs = cleaner.clean_batch(data['jobs'])
    print(f"   Successfully cleaned: {len(cleaned_jobs)}/{len(data['jobs'])} jobs")
    
    if len(cleaned_jobs) < len(data['jobs']):
        skipped = len(data['jobs']) - len(cleaned_jobs)
        print(f"    Skipped {skipped} jobs (too short after cleaning)")
    
    print("\n Cleaning CVs...")
    cleaned_cvs = cleaner.clean_batch(data['cvs'])
    print(f"   Successfully cleaned: {len(cleaned_cvs)}/{len(data['cvs'])} CVs")
    
    return cleaned_jobs, cleaned_cvs


# ============================================================
# EMBEDDING GENERATION
# ============================================================

def generate_embeddings(cleaned_jobs, cleaned_cvs, data, embedder):
    """Generate embeddings for jobs and CVs."""
    print("\n" + "=" * 70)
    print("STEP 3: GENERATING EMBEDDINGS")
    print("=" * 70)
    
    # Extract data
    job_texts = [r['cleaned_text'] for r in cleaned_jobs]
    job_indices = [r['original_index'] for r in cleaned_jobs]
    job_ids = [data['job_ids'][i] for i in job_indices]
    
    cv_texts = [r['cleaned_text'] for r in cleaned_cvs]
    cv_indices = [r['original_index'] for r in cleaned_cvs]
    cv_ids = [data['cv_ids'][i] for i in cv_indices]
    
    print(f"\n Generating job embeddings...")
    print(f"  Model: {embedder.model.get_sentence_embedding_dimension()}-dimensional vectors")
    job_embeddings = embedder.embed_batch(job_texts, show_progress=True)
    print(f"   Created {job_embeddings.shape[0]} job embeddings")
    
    print(f"\n Generating CV embeddings...")
    cv_embeddings = embedder.embed_batch(cv_texts, show_progress=True)
    print(f"   Created {cv_embeddings.shape[0]} CV embeddings")
    
    return {
        'job_embeddings': job_embeddings,
        'job_ids': job_ids,
        'job_texts': job_texts,
        'cv_embeddings': cv_embeddings,
        'cv_ids': cv_ids,
        'cv_texts': cv_texts
    }


# ============================================================
# FAISS INDEX
# ============================================================

def build_faiss_index(embedding_data, embedder):
    """Build FAISS vector index for jobs."""
    print("\n" + "=" * 70)
    print("STEP 4: BUILDING FAISS VECTOR INDEX")
    print("=" * 70)
    
    print(f"\n Creating FAISS index...")
    print(f"  Index type: IndexFlatL2 (L2 distance)")
    print(f"  Embedding dimension: {embedder.embedding_dim}")
    
    faiss_index = FAISSJobIndex(embedding_dim=embedder.embedding_dim)
    
    faiss_index.add_jobs(
        job_embeddings=embedding_data['job_embeddings'],
        job_ids=embedding_data['job_ids'],
        job_texts=embedding_data['job_texts']
    )
    
    # Save index
    os.makedirs('data/processed', exist_ok=True)
    faiss_index.save(INDEX_FILE, METADATA_FILE)
    print(f"   Index saved to: {INDEX_FILE}")
    
    return faiss_index


# ============================================================
# CV-JOB MATCHING
# ============================================================

def match_cvs_to_jobs(embedding_data, matcher):
    """Match all CVs to jobs and return results."""
    print("\n" + "=" * 70)
    print("STEP 5: MATCHING CVs TO JOBS")
    print("=" * 70)
    
    all_results = []
    
    for i, (cv_id, cv_embedding) in enumerate(zip(embedding_data['cv_ids'], embedding_data['cv_embeddings'])):
        print(f"\n Matching CV {i+1}/{len(embedding_data['cv_ids'])}: {cv_id}")
        
        # Get top 5 matches
        job_ids, scores = matcher.index.search(cv_embedding, top_k=5)
        
        matches = []
        for job_id, score in zip(job_ids, scores):
            matches.append({
                'job_id': job_id,
                'score': score
            })
            
            # Visual representation
            score_percent = score * 100
            bar_length = int(score_percent / 5)
            bar = '█' * bar_length + '░' * (20 - bar_length)
            print(f"  {job_id:40s} {bar} {score_percent:5.1f}%")
        
        all_results.append({
            'cv_id': cv_id,
            'matches': matches
        })
    
    return all_results


# ============================================================
# RESULTS ANALYSIS
# ============================================================

def analyze_results(results):
    """Analyze matching results for thesis insights."""
    print("\n" + "=" * 70)
    print("STEP 6: RESULTS ANALYSIS")
    print("=" * 70)
    
    print("\n Cross-Category Matching Analysis:")
    print("-" * 70)
    
    for result in results:
        cv_id = result['cv_id']
        cv_category = cv_id.split('_')[0]  # Extract category (Medicine, Marketing, etc.)
        
        print(f"\n {cv_id}")
        
        # Check if top matches are from same category
        top_match = result['matches'][0]
        top_category = top_match['job_id'].split('_')[0]
        
        if cv_category == top_category:
            print(f"  Best match is from SAME category ({cv_category})")
        else:
            print(f"    Best match is from DIFFERENT category")
        
        # Count matches per category
        category_counts = {}
        for match in result['matches']:
            job_category = match['job_id'].split('_')[0]
            category_counts[job_category] = category_counts.get(job_category, 0) + 1
        
        print(f"  Top 5 matches by category:")
        for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
            print(f"    {cat}: {count}/5 matches")


def save_results(results, data):
    """Save detailed results to file for thesis documentation."""
    print("\n" + "=" * 70)
    print("SAVING RESULTS")
    print("=" * 70)
    
    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("CV-JOB MATCHING RESULTS\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 70 + "\n\n")
        
        f.write("DATASET SUMMARY\n")
        f.write("-" * 70 + "\n")
        for category, info in data['category_info'].items():
            f.write(f"{category}: {info['cvs']} CVs, {info['jobs']} jobs\n")
        f.write(f"\nTotal: {len(data['cvs'])} CVs, {len(data['jobs'])} jobs\n")
        f.write("\n")
        
        f.write("=" * 70 + "\n")
        f.write("MATCHING RESULTS\n")
        f.write("=" * 70 + "\n\n")
        
        for result in results:
            f.write(f"CV: {result['cv_id']}\n")
            f.write("-" * 70 + "\n")
            f.write("Top 5 Job Matches:\n")
            for i, match in enumerate(result['matches'], 1):
                score_percent = match['score'] * 100
                f.write(f"  {i}. {match['job_id']:<40s} Score: {score_percent:5.1f}%\n")
            f.write("\n")
    
    print(f"✓ Results saved to: {RESULTS_FILE}")


# ============================================================
# MAIN DEMO FUNCTION
# ============================================================

def main():
    """Run complete demo workflow."""
    print("\n" + "=" * 70)
    print("SMART CV-JOB MATCHING SYSTEM")
    print("Bachelor Thesis Demonstration")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load data
    data = load_all_data()
    
    if len(data['jobs']) == 0:
        print("\n ERROR: No job descriptions found!")
        print("   Please check your data/raw/ folder structure")
        return
    
    if len(data['cvs']) == 0:
        print("\n ERROR: No CVs found!")
        print("   Please check your data/raw/ folder structure")
        return
    
    # Initialize components
    print("\n  Initializing system components...")
    cleaner = TextCleaner(
        remove_emails=True,
        remove_phone=True,
        remove_urls=True,
        min_length=50
    )
    print("  ✓ Text cleaner initialized")
    
    embedder = TextEmbedder(model_name='all-MiniLM-L6-v2')
    print("  ✓ Embedding model loaded")
    
    # Preprocess
    cleaned_jobs, cleaned_cvs = preprocess_data(data, cleaner)
    
    if len(cleaned_jobs) == 0:
        print("\n ERROR: No valid jobs after cleaning!")
        print("   Job descriptions might be too short")
        return
    
    # Generate embeddings
    embedding_data = generate_embeddings(cleaned_jobs, cleaned_cvs, data, embedder)
    
    # Build FAISS index
    faiss_index = build_faiss_index(embedding_data, embedder)
    
    # Create matcher
    matcher = CVJobMatcher(cleaner, embedder, faiss_index)
    
    # Match CVs
    results = match_cvs_to_jobs(embedding_data, matcher)
    
    # Analyze results
    analyze_results(results)
    
    # Save results
    save_results(results, data)
    
    # Final summary
    print("\n" + "=" * 70)
    print("DEMO COMPLETE!")
    print("=" * 70)
    print(f" Processed: {len(data['cvs'])} CVs, {len(data['jobs'])} jobs")
    print(f" Created: {faiss_index.index.ntotal} job embeddings")
    print(f" Generated: {len(results)} matching results")
    print(f" Results saved to: {RESULTS_FILE}")
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)


if __name__ == "__main__":
    main()