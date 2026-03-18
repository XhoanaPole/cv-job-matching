"""
Test script for gap analysis functionality.
Run this to verify the new features work correctly.
"""

from pathlib import Path
from src.preprocessing.text_cleaning import TextCleaner
from src.embeddings.embedder import TextEmbedder
from src.vector_store.faiss_index import FAISSJobIndex
from src.matching.matcher import CVJobMatcher

def load_text(filepath):
    """Load text from file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def test_single_domain(domain_name, cleaner=None, embedder=None):
    """Test gap analysis with a specific domain"""
    
    print("="*80)
    print(f"TESTING GAP ANALYSIS - {domain_name.upper()}")
    print("="*80)
    
    # Initialize components
    print("\n1. Initializing components...")
    if cleaner is None:
        cleaner = TextCleaner()
    if embedder is None:
        embedder = TextEmbedder(model_name='all-MiniLM-L6-v2')
        
    faiss_index = FAISSJobIndex(embedding_dim=embedder.embedding_dim)
    
    # Set data directory
    data_dir = Path(f'data/raw/{domain_name}')
    
    if not data_dir.exists():
        print(f"   ❌ ERROR: Directory {data_dir} does not exist!")
        return False
    
    print(f"   ✓ Found directory: {data_dir}")
    
    # Load CV - look for sample_cv.txt (without any suffix)
    print("\n2. Loading CV...")
    cv_file = data_dir / 'sample_cv.txt'
    
    if not cv_file.exists():
        print(f"   ❌ ERROR: {cv_file} not found!")
        print(f"   Available files: {[f.name for f in data_dir.glob('*.txt')]}")
        return False
    
    cv_text = load_text(cv_file)
    print(f"   ✓ Loaded CV: {cv_file.name} ({len(cv_text)} characters)")
    
    # Load jobs
    print("\n3. Loading job descriptions...")
    job_files = sorted(data_dir.glob('job_description_*.txt'))
    
    if not job_files:
        print(f"   ❌ ERROR: No job_description_*.txt files found!")
        return False
    
    job_texts = [load_text(f) for f in job_files]
    job_ids = [f.stem for f in job_files]
    print(f"   ✓ Loaded {len(job_files)} job descriptions:")
    for jf in job_files:
        print(f"      - {jf.name}")
    
    # Clean and embed jobs
    print("\n4. Processing job descriptions...")
    cleaned_jobs = cleaner.clean_batch(job_texts)
    job_embeddings = embedder.embed_batch([r['cleaned_text'] for r in cleaned_jobs])
    print(f"   ✓ Cleaned and embedded {len(cleaned_jobs)} jobs")
    
    # Add to FAISS index WITH job texts
    print("\n5. Building FAISS index...")
    faiss_index.add_jobs(
        job_embeddings=job_embeddings,  # Fixed: use correct parameter name
        job_ids=job_ids,
        job_texts=job_texts  # IMPORTANT: Store original texts for gap analysis
    )
    
    # Create matcher with gap analysis
    print("\n6. Creating matcher with gap analysis enabled...")
    matcher = CVJobMatcher(
        text_cleaner=cleaner,
        embedder=embedder,
        faiss_index=faiss_index,
        include_gap_analysis=True  # Enable gap analysis
    )
    
    # Match CV to jobs
    print("\n7. Matching CV to jobs...")
    results = matcher.match_cv_to_jobs(
        cv_text=cv_text,
        cv_id=f'{domain_name}_cv',
        top_k=3  # Top 3 matches
    )
    
    # Display results
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    
    print(f"\nCV ID: {results['cv_id']}")
    
    if 'cv_skills_summary' in results:
        print(f"\n📊 CV SKILLS SUMMARY:")
        summary = results['cv_skills_summary']
        print(f"   Total skills detected: {summary['total_skills']}")
        print(f"   Top technical terms: {', '.join(summary['top_technical_terms'][:7])}")
        print(f"   Top keywords: {', '.join(summary['top_keywords'][:7])}")
    
    print(f"\n🎯 TOP {len(results['matches'])} JOB MATCHES:\n")
    
    for i, match in enumerate(results['matches'], 1):
        print(f"\n{'='*80}")
        print(f"RANK #{i}: {match['job_id']}")
        print(f"{'='*80}")
        print(f"Similarity Score: {match['similarity_score']:.4f}")
        
        if 'gap_analysis' in match:
            gap = match['gap_analysis']
            
            if 'error' in gap:
                print(f"   ⚠️  {gap['error']}")
            else:
                print(f"\n📈 SKILLS MATCH PERCENTAGE: {gap['match_percentage']}%")
                print(f"   ✅ Matched Skills: {gap['matched_count']}")
                print(f"   ❌ Missing Skills: {gap['missing_count']}")
                
                print(f"\n✅ MATCHED SKILLS ({gap['matched_count']}):")
                if gap['matched_skills']:
                    for skill in gap['matched_skills'][:12]:  # Show top 12
                        print(f"   • {skill}")
                    if len(gap['matched_skills']) > 12:
                        print(f"   ... and {len(gap['matched_skills']) - 12} more")
                else:
                    print("   (none)")
                
                print(f"\n❌ MISSING SKILLS ({gap['missing_count']}):")
                if gap['missing_skills']:
                    for skill in gap['missing_skills'][:12]:  # Show top 12
                        print(f"   • {skill}")
                    if len(gap['missing_skills']) > 12:
                        print(f"   ... and {len(gap['missing_skills']) - 12} more")
                else:
                    print("   (none)")
    
    # Test detailed gap analysis for top match
    print("\n" + "="*80)
    print("DETAILED GAP ANALYSIS FOR TOP MATCH")
    print("="*80)
    
    top_job_id = results['matches'][0]['job_id']
    detailed = matcher.get_detailed_gap_analysis(cv_text, top_job_id)
    
    if 'error' not in detailed:
        print(f"\nJob: {detailed['job_id']}")
        print(f"Match Percentage: {detailed['match_percentage']}%")
        print(f"\nSummary:")
        print(f"   CV Skills: {detailed['summary']['total_cv_skills']}")
        print(f"   Job Requirements: {detailed['summary']['total_job_skills']}")
        print(f"   Matched: {detailed['summary']['matched']}")
        print(f"   Missing: {detailed['summary']['missing']}")
    
    print("\n" + "="*80)
    print(f"✅ {domain_name.upper()} TEST COMPLETED SUCCESSFULLY!")
    print("="*80)
    
    return True

def test_all_domains():
    """Test all three domains"""
    domains = ['Medicine', 'data_analysis', 'marketing']
    
    print("\n" + "🚀"*40)
    print("TESTING ALL DOMAINS")
    print("🚀"*40 + "\n")
    
    print("\nInitializing shared AI models (this takes a moment)...")
    shared_cleaner = TextCleaner()
    shared_embedder = TextEmbedder(model_name='all-MiniLM-L6-v2')
    
    results = {}
    
    for domain in domains:
        success = test_single_domain(domain, cleaner=shared_cleaner, embedder=shared_embedder)
        results[domain] = success
        print("\n\n")
    
    # Summary
    print("="*80)
    print("FINAL SUMMARY")
    print("="*80)
    for domain, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{domain:20} : {status}")
    print("="*80)

def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1:
        # Test specific domain
        domain = sys.argv[1]
        test_single_domain(domain)
    else:
        # Test all domains
        test_all_domains()

if __name__ == "__main__":
    main()