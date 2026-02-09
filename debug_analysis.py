import sys
import os
from pathlib import Path

# Fix path
sys.path.append(os.getcwd())

from backend.core.engine import engine
from backend.core.analyzer import analyzer

def debug_file(path_str):
    path = Path(path_str)
    if not path.exists():
        print(f"File not found: {path}")
        return

    print(f"Analyzing {path}...")
    
    # 1. Run Detection
    report = engine.analyze(path)
    print(f"Raw Findings: {len(report.findings)}")
    
    # 2. Run Analysis (Classification)
    analysis = analyzer.analyze(report)
    
    # 3. Print Canary details
    canaries = [f for f in analysis.findings if f.trap_type.value == "canary"]
    
    print(f"\nFound {len(canaries)} Canary/Marked outcomes:")
    for c in canaries:
        print(f"--- CANARY DETECTED ---")
        print(f"Context: {c.original.context!r}")
        print(f"Reason: {c.classification_reason}")
        print(f"Decoded Text: {c.decoded_text}")
        print("-" * 30)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        debug_file(sys.argv[1])
    else:
        print("Usage: python debug_analysis.py <path_to_pdf>")
