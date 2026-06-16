"""
Quick verification script to check if everything is set up correctly
before running the demo for your professor.

Run this first to catch any issues!
"""

import sys
from pathlib import Path

print("=" * 70)
print("SETUP VERIFICATION SCRIPT")
print("=" * 70)

errors = []
warnings = []
success = []

# Check 1: Folder structure
print("\n1️⃣  Checking folder structure...")
base_path = Path('data/raw')

if not base_path.exists():
    errors.append("❌ 'data/raw' folder not found!")
else:
    success.append("✅ 'data/raw' folder exists")
    
    categories = ['Medicine', 'Marketing', 'Data Analysis']
    for category in categories:
        cat_path = base_path / category
        if not cat_path.exists():
            warnings.append(f"⚠️  Category folder missing: {category}")
        else:
            # Count files
            txt_files = list(cat_path.glob('*.txt'))
            cv_files = [f for f in txt_files if 'cv' in f.stem.lower()]
            job_files = [f for f in txt_files if 'cv' not in f.stem.lower()]
            
            print(f"   📁 {category}:")
            print(f"      CVs: {len(cv_files)}")
            print(f"      Jobs: {len(job_files)}")
            
            if len(cv_files) == 0:
                warnings.append(f"⚠️  No CVs found in {category}")
            if len(job_files) == 0:
                warnings.append(f"⚠️  No jobs found in {category}")
            
            if len(cv_files) > 0 and len(job_files) > 0:
                success.append(f"✅ {category} has data")

# Check 2: Source code files
print("\n2️⃣  Checking source code files...")
required_files = [
    'src/preprocessing/text_cleaning.py',
    'src/embeddings/embedder.py',
    'src/vector_store/faiss_index.py',
    'src/matching/matcher.py'
]

for file_path in required_files:
    if Path(file_path).exists():
        success.append(f"✅ {file_path}")
    else:
        errors.append(f"❌ Missing: {file_path}")

# Check 3: Demo script
print("\n3️⃣  Checking demo script...")
if Path('demo_for_professor.py').exists():
    success.append("✅ demo_for_professor.py exists")
else:
    errors.append("❌ demo_for_professor.py not found!")

# Check 4: Dependencies
print("\n4️⃣  Checking Python dependencies...")
try:
    import numpy
    success.append("✅ numpy installed")
except ImportError:
    errors.append("❌ numpy not installed")

try:
    import faiss
    success.append("✅ faiss installed")
except ImportError:
    errors.append("❌ faiss not installed")

try:
    from sentence_transformers import SentenceTransformer
    success.append("✅ sentence-transformers installed")
except ImportError:
    errors.append("❌ sentence-transformers not installed")

# Check 5: Sample data content
print("\n5️⃣  Checking sample data content...")
sample_files = []
for category in ['Medicine', 'Marketing', 'Data Analysis']:
    cat_path = base_path / category
    if cat_path.exists():
        for txt_file in cat_path.glob('*.txt'):
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                if len(content) < 100:
                    warnings.append(f"⚠️  {txt_file.name} seems too short ({len(content)} chars)")
                elif len(content) > 50:
                    success.append(f"✅ {txt_file.name} has content ({len(content)} chars)")
            except Exception as e:
                errors.append(f"❌ Cannot read {txt_file.name}: {e}")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

print(f"\n✅ Success: {len(success)} checks passed")
print(f"⚠️  Warnings: {len(warnings)}")
print(f"❌ Errors: {len(errors)}")

if warnings:
    print("\n⚠️  WARNINGS:")
    for w in warnings:
        print(f"  {w}")

if errors:
    print("\n❌ ERRORS (must fix before demo):")
    for e in errors:
        print(f"  {e}")
    print("\n🔧 To fix:")
    print("  1. Make sure 'data/raw' folder exists")
    print("  2. Create category folders: Medicine, Marketing, Data Analysis")
    print("  3. Add .txt files to each folder")
    print("  4. Run: pip install -r requirements.txt")
else:
    print("\n" + "=" * 70)
    print("🎉 ALL CHECKS PASSED!")
    print("=" * 70)
    print("\n✅ You're ready to run the demo!")
    print("\nNext step:")
    print("  python demo_for_professor.py")
    print("=" * 70)