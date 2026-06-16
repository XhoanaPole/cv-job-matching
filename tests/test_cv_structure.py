"""
Test how CV structure affects matching results
"""

import sys
sys.path.append('src')

from preprocessing.text_cleaning import TextCleaner
from embeddings.embedder import TextEmbedder
from vector_store.faiss_index import FAISSJobIndex
from matching.matcher import CVJobMatcher

# Load the saved FAISS index (with Medicine jobs)
cleaner = TextCleaner()
embedder = TextEmbedder(model_name='all-MiniLM-L6-v2')
faiss_index = FAISSJobIndex.load(
    'data/processed/faiss.index',
    'data/processed/metadata.pkl'
)
matcher = CVJobMatcher(cleaner, embedder, faiss_index)

# Test all 4 versions
cv_versions = {
    'Version A (Original)': 'data/raw/Medicine/sample_cv.txt',
    'Version B (Skills-First)': 'data/raw/Medicine/sample_cv_version_b.txt',
    'Version C (Narrative)': 'data/raw/Medicine/sample_cv_version_c.txt',
    'Version D (Minimal)': 'data/raw/Medicine/sample_cv_version_d.txt'
}

print("=" * 70)
print("CV STRUCTURE IMPACT TEST")
print("=" * 70)

results = {}

for version_name, cv_path in cv_versions.items():
    print(f"\n📄 Testing: {version_name}")
    print("-" * 70)
    
    # Read CV
    with open(cv_path, 'r', encoding='utf-8') as f:
        cv_text = f.read()
    
    # Match to jobs
    result = matcher.match_cv_to_jobs(cv_text, cv_id=version_name, top_k=5)
    
    # Store results
    results[version_name] = result
    
    # Display
    if 'error' in result:
        print(f"  ❌ Error: {result['error']}")
    else:
        print("  Top 5 Matches:")
        for i, match in enumerate(result['matches'], 1):
            score_percent = match['score'] * 100
            bar_length = int(score_percent / 5)
            bar = '█' * bar_length + '░' * (20 - bar_length)
            print(f"  {i}. {match['job_id']:40s} {bar} {score_percent:5.1f}%")

# Comparison Analysis
print("\n" + "=" * 70)
print("COMPARATIVE ANALYSIS")
print("=" * 70)

print("\n📊 Score Comparison for Top Match:")
print("-" * 70)
for version_name, result in results.items():
    if 'matches' in result and len(result['matches']) > 0:
        top_match = result['matches'][0]
        print(f"{version_name:30s} → {top_match['job_id']:40s} {top_match['score']*100:5.1f}%")

print("\n📊 Score Variation:")
print("-" * 70)
top_scores = [r['matches'][0]['score']*100 for r in results.values() if 'matches' in r]
if top_scores:
    print(f"  Minimum score: {min(top_scores):.1f}%")
    print(f"  Maximum score: {max(top_scores):.1f}%")
    print(f"  Range: {max(top_scores) - min(top_scores):.1f}%")
    print(f"  Average: {sum(top_scores)/len(top_scores):.1f}%")

print("\n📊 Ranking Stability:")
print("-" * 70)
# Check if top job is same across versions
top_jobs = [r['matches'][0]['job_id'] for r in results.values() if 'matches' in r]
if len(set(top_jobs)) == 1:
    print(f"  ✅ All versions ranked the same job #1: {top_jobs[0]}")
else:
    print(f"  ⚠️  Different jobs ranked #1 across versions:")
    for version_name, result in results.items():
        if 'matches' in result:
            print(f"    {version_name}: {result['matches'][0]['job_id']}")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)