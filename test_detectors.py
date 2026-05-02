
from pathlib import Path

from backend.core.engine import DetectionEngine


TEST_PDF = Path(__file__).with_name("test_document.pdf")

def test_detectors():
    print(f"Running Detection Engine on {TEST_PDF.name}...")
    engine = DetectionEngine()
    
    with TEST_PDF.open("rb") as f:
        pdf_bytes = f.read()
        
    report = engine.analyze_bytes(pdf_bytes, TEST_PDF.name)
    
    print(f"\nTotal Findings: {len(report.findings)}")
    for f in report.findings:
        print(f"[{f.detector}] {f.content} (Page {f.location.page})")

if __name__ == "__main__":
    test_detectors()
