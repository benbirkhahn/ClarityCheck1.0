"""
PDF Sanitizer - Removes identified AI traps from documents.

Takes a PDF and removes/neutralizes hidden content identified by the detection engine.
"""

import fitz  # PyMuPDF
from typing import Optional

from src.core.models import Report, Finding
from src.core.analyzer import TrapAnalysis, TrapType


def sanitize_pdf(
    pdf_bytes: bytes, 
    report: Report, 
    analysis: Optional[TrapAnalysis] = None
) -> bytes:
    """
    Remove AI traps from a PDF document.
    
    Strategies:
    1. Remove text spans that match hidden content (white text, tiny text, etc.)
    2. Remove suspicious annotations
    3. Clean metadata
    4. Redact off-screen content
    
    Args:
        pdf_bytes: Original PDF content
        report: Detection report with findings
        analysis: Optional trap analysis for smarter removal
        
    Returns:
        Sanitized PDF as bytes
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    try:
        # Group findings by page for efficient processing
        findings_by_page = {}
        for finding in report.findings:
            page_num = finding.location.page - 1  # Convert to 0-indexed
            if page_num not in findings_by_page:
                findings_by_page[page_num] = []
            findings_by_page[page_num].append(finding)
        
        # Process each page with findings
        for page_num, findings in findings_by_page.items():
            if page_num < len(doc):
                page = doc[page_num]
                _sanitize_page(page, findings)
        
        # Clean document-level metadata if flagged
        if any(f.detector == "MetadataDetector" for f in report.findings):
            _clean_metadata(doc)
        
        # Save to bytes
        output = doc.tobytes(garbage=4, deflate=True)
        return output
        
    finally:
        doc.close()


def _sanitize_page(page: fitz.Page, findings: list[Finding]):
    """Remove identified traps from a single page."""
    
    for finding in findings:
        detector = finding.detector
        
        # Strategy depends on detector type
        if detector in ["MatchingColorDetector", "TinyTextDetector", "LowContrastDetector"]:
            _redact_hidden_text(page, finding)
        
        elif detector == "HiddenAnnotationDetector":
            _remove_annotations(page, finding)
        
        elif detector == "OffScreenTextDetector":
            _redact_hidden_text(page, finding)
        
        elif detector in ["SuspiciousSpacingDetector", "InvisibleRenderDetector"]:
            _redact_hidden_text(page, finding)
        
        elif detector == "LayeredTextDetector":
            _redact_hidden_text(page, finding)
        
        # ZeroWidthCharDetector - these are in the text stream, harder to remove
        # For now, we'll leave these as they're less impactful


def _redact_hidden_text(page: fitz.Page, finding: Finding):
    """Redact (completely remove) hidden text from page."""
    
    x = finding.location.x or 0
    y = finding.location.y or 0
    
    if x <= 0 and y <= 0:
        return
    
    # Get text blocks with detailed info
    blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
    
    redact_rects = []
    
    for block in blocks:
        if block.get("type") != 0:
            continue
        
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                bbox = span.get("bbox", (0, 0, 0, 0))
                span_x, span_y = bbox[0], bbox[1]
                
                # Check if this span is near the finding location
                if abs(span_x - x) < 10 and abs(span_y - y) < 10:
                    # Found the hidden text span - get its full rect
                    rect = fitz.Rect(bbox)
                    redact_rects.append(rect)
                    
                # Also check by text content
                text = span.get("text", "")
                color = span.get("color", 0)
                size = span.get("size", 12)
                
                # Hidden if: white color (16777215 = 0xFFFFFF) or tiny size
                is_white = color == 16777215 or color == 0xFFFFFF
                is_tiny = size < 4
                
                if (is_white or is_tiny) and text.strip():
                    rect = fitz.Rect(bbox)
                    redact_rects.append(rect)
    
    # Apply all redactions at once
    for rect in redact_rects:
        try:
            page.add_redact_annot(rect)
        except Exception:
            pass
    
    try:
        page.apply_redactions()
    except Exception:
        pass


def _remove_annotations(page: fitz.Page, finding: Finding):
    """Remove suspicious annotations from page."""
    x = finding.location.x or 0
    y = finding.location.y or 0
    
    # Find and delete annotations near the reported location
    for annot in page.annots():
        if annot is None:
            continue
        
        rect = annot.rect
        # Check if annotation is near the reported location
        if (abs(rect.x0 - x) < 50 and abs(rect.y0 - y) < 50):
            try:
                page.delete_annot(annot)
            except Exception:
                pass


def _clean_metadata(doc: fitz.Document):
    """Remove or sanitize document metadata."""
    try:
        # Clear sensitive metadata fields
        doc.set_metadata({
            "title": "",
            "author": "",
            "subject": "",
            "keywords": "",
            "creator": "ClarityCheck Sanitized",
            "producer": "ClarityCheck",
        })
    except Exception:
        pass


def get_sanitization_preview(
    pdf_bytes: bytes,
    report: Report,
    analysis: Optional[TrapAnalysis] = None
) -> dict:
    """
    Get a preview of what would be removed without actually modifying.
    
    Returns a summary of planned removals.
    """
    removals = []
    
    for finding in report.findings:
        action = "unknown"
        
        if finding.detector in ["MatchingColorDetector", "TinyTextDetector", 
                                 "LowContrastDetector", "OffScreenTextDetector",
                                 "SuspiciousSpacingDetector", "InvisibleRenderDetector",
                                 "LayeredTextDetector"]:
            action = "REMOVE - Hidden text will be redacted"
        
        elif finding.detector == "HiddenAnnotationDetector":
            action = "REMOVE - Annotation will be deleted"
        
        elif finding.detector == "MetadataDetector":
            action = "CLEAN - Metadata will be sanitized"
        
        elif finding.detector == "ZeroWidthCharDetector":
            action = "SKIP - Zero-width chars are embedded in text stream"
        
        removals.append({
            "page": finding.location.page,
            "content": finding.context[:50] + "..." if len(finding.context) > 50 else finding.context,
            "detector": finding.detector,
            "action": action,
        })
    
    return {
        "total_findings": len(report.findings),
        "will_remove": sum(1 for r in removals if r["action"].startswith("REMOVE")),
        "will_clean": sum(1 for r in removals if r["action"].startswith("CLEAN")),
        "will_skip": sum(1 for r in removals if r["action"].startswith("SKIP")),
        "details": removals,
    }
