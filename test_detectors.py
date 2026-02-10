
from backend.core.engine import DetectionEngine
import fitz

def test_detectors():
    print("Running Detection Engine on trap_gallery.pdf...")
    engine = DetectionEngine()
    
    # Read file
    with open("trap_gallery.pdf", "rb") as f:
        pdf_bytes = f.read()
        
    report = engine.analyze_bytes(pdf_bytes, "trap_gallery.pdf")
    
    print(f"\nTotal Findings: {len(report.findings)}")
    for f in report.findings:
        print(f"[{f.detector}] {f.content} (Page {f.location.page})")

if __name__ == "__main__":
    test_detectors()
