"""
Quick test with your mixed format files
"""

import sys
from pathlib import Path
sys.path.append('src')

from preprocessing.document_parser import DocumentParser

# Initialize parser
parser = DocumentParser()

print("=" * 70)
print("TESTING YOUR MEDICINE FILES")
print("=" * 70)

# Test directory
medicine_dir = Path('data/raw/Medicine')

print(f"\n📁 Scanning: {medicine_dir}")
print("-" * 70)

# Try to parse each file
results = {}

for file in sorted(medicine_dir.iterdir()):
    if file.is_file():
        print(f"\n📄 File: {file.name}")
        print(f"   Format: {file.suffix}")
        
        # Try to parse
        text = parser.parse_file(file)
        
        if text:
            results[file.name] = text
            print(f"   ✅ Success! Extracted {len(text)} characters")
            print(f"   First 100 chars: {text[:100]}...")
        else:
            print(f"   ❌ Failed to parse")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Total files found: {len(list(medicine_dir.iterdir()))}")
print(f"Successfully parsed: {len(results)}")
print(f"\nParsed files:")
for filename in results.keys():
    print(f"  ✓ {filename}")