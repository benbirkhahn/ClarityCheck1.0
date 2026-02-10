import sys
import os
sys.path.append(os.getcwd())

import fitz
from backend.core.models import Report, Finding, Location
from backend.core.sanitizer import sanitize_pdf

def create_dummy_pdf():
    doc = fitz.open()
    page = doc.new_page()
    
    # Visible text
    page.insert_text((50, 50), "Visible Content", fontsize=12, color=(0, 0, 0))
    
    # "Hidden" Trap (Off-white, not strictly 0xFFFFFF)
    # 0.99 float color roughly equals 252/255
    page.insert_text((50, 100), "Evasive Trap", fontsize=12, color=(0.99, 0.99, 0.99))
    
    return doc.tobytes()

def test_sanitization():
    print("Creating dummy PDF...")
    pdf_bytes = create_dummy_pdf()
    
    # Simulate Findings
    findings = [
        Finding(
            id="1", detector="MatchingColorDetector", severity="high",
            # Massive offset (50px) to simulate bad coordinates
            location=Location(page=1, x=100, y=150, char_index=0),
            content="Evasive Trap", context="Evasive Trap", explanation="Off-white text"
        )
    ]
    
    report = Report(job_id="test", filename="test.pdf", total_pages=1, findings=findings)
    
    print("Running sanitization...")
    sanitized_bytes = sanitize_pdf(pdf_bytes, report)
    
    # Verify
    doc = fitz.open(stream=sanitized_bytes, filetype="pdf")
    page = doc[0]
    text = page.get_text()
    
    print("\n--- Result Text ---")
    print(text)
    print("-------------------")
    
    if "Evasive Trap" not in text:
        print("SUCCESS: Traps removed.")
    else:
        print("FAILURE: Traps still present.")

if __name__ == "__main__":
    test_sanitization()
