"""
PDF Sanitizer - Removes identified AI traps from documents.

Takes a PDF and removes/neutralizes hidden content identified by the detection engine.
"""

import fitz  # PyMuPDF
from typing import Optional

import logging

# Configure logger
schema_logger = logging.getLogger("sanitizer")
schema_logger.setLevel(logging.INFO)

from backend.core.models import Report, Finding
from backend.core.analyzer import TrapAnalysis, TrapType


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
        
        elif detector == "InvisibleRenderDetector":
            _redact_hidden_text(page, finding)

        elif detector == "VisualMismatchDetector":
            _redact_hidden_text(page, finding)
            
        # SuspiciousSpacingDetector - User feedback indicates this is often valid text.
        # We will Report it, but NOT Redact it.
        # elif detector == "SuspiciousSpacingDetector":
        #    _redact_hidden_text(page, finding)
        
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
    
    schema_logger.info(f"Redacting hidden text on page. Findings: {len(redact_rects)} candidates so far. Location: {x},{y}")

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
                    text = span.get("text", "") # Ensure text is captured
                    redact_rects.append((rect, text))
                    schema_logger.info(f"Found match by coordinate: {text} at {rect}")
                    
                # Also check by text content
                text = span.get("text", "")
                color = span.get("color", 0)
                size = span.get("size", 12)
                
                # Hidden if: 
                # 1. White color: 0xFFFFFF (16777215) OR very close to white (> 0xFEFEFE)
                # 2. Variable Type handling for color (int vs float)
                is_white = False
                if isinstance(color, int):
                    is_white = color > 16711422 # 0xFEFEFE
                elif isinstance(color, (float, tuple, list)):
                    # Handle float colors (0.0-1.0) - if all components > 0.99
                    if isinstance(color, float):
                        is_white = color > 0.99
                    else:
                        is_white = all(c > 0.99 for c in color)
                
                is_tiny = size < 4
                
                if (is_white or is_tiny) and text.strip():
                    rect = fitz.Rect(bbox)
                    redact_rects.append((rect, text))
                    schema_logger.info(f"Found match by heuristic (white/tiny): '{text}' Color: {color} Size: {size}")

    # FALLBACK: If we haven't found a match by coordinates or heuristic,
    # search for the EXACT text content in the finding.
    # This handles coordinate drift between detection engine and PyMuPDF.
    if finding.content and len(finding.content.strip()) > 3:
        # Search for the text on the page
        text_instances = page.search_for(finding.content)
        if text_instances:
            schema_logger.info(f"Fallback Search: Found {len(text_instances)} instances of '{finding.content}'")
            
            # Filter by location AND dimension to avoid redacting legitimate text
            expected_x = finding.location.x or 0
            expected_y = finding.location.y or 0
            expected_width = finding.width or 0
            expected_height = finding.height or 0
            
            for rect in text_instances:
                # Check if this instance matches the expected location
                loc_match = abs(rect.x0 - expected_x) < 10 and abs(rect.y0 - expected_y) < 10
                
                # Check if this instance matches the expected dimensions
                # Allow some tolerance for PDF rendering variations
                width_match = expected_width > 0 and abs(rect.width - expected_width) < 5
                height_match = expected_height > 0 and abs(rect.height - expected_height) < 2
                size_match = width_match and height_match
                
                # Only redact if EITHER location matches OR dimensions match
                # This handles cases where coordinates drift but size is consistent
                if loc_match or size_match:
                    redact_rects.append((rect, finding.content))
                    schema_logger.info(f"Fallback Match: Using instance at {rect} (loc_match={loc_match}, size_match={size_match})")
                    break  # Only take the first match to avoid over-redaction
                else:
                    schema_logger.debug(f"Skipping instance at {rect} - no match (expected: {expected_x},{expected_y} w={expected_width} h={expected_height})")
            
            if not any(loc_match or size_match for rect in text_instances):
                schema_logger.warning(f"Fallback Search: Found text but no instances matched location/size criteria")
        else:
             schema_logger.warning(f"Fallback Search: Could NOT find '{finding.content}' on page!")


    
    # Apply redactions
    for item in redact_rects:
        # Handle both tuple (rect, text) and legacy (rect)
        if isinstance(item, tuple):
            rect, span_text = item
        else:
            rect = item
            span_text = ""

        try:
            # Check for overlap with visible text before drawing black box
            # SAFETY OVERRIDE: If it's definitely a trap (White/Tiny/Layered), NUKE IT regardless of overlap.
            # The "Do No Harm" logic is mainly for "Suspicious Spacing" or "Ambiguous" detections.
            is_high_confidence_trap = (
                finding.detector in ["MatchingColorDetector", "TinyTextDetector", "LayeredTextDetector", "InvisibleRenderDetector", "VisualMismatchDetector"]
                # We can't access is_white/is_tiny here easily as they were local to the loop above.
                # But finding.detector is a good proxy.
            )

            if not is_high_confidence_trap and span_text and _has_visible_overlap(page, rect, span_text):
                # overlap detected: attempting to redact this would destroy the visible text above/below it.
                # "Do No Harm" policy: Skip redaction, preserve the document.
                schema_logger.warning(f"Skipping redaction due to visible overlap: {span_text} ({finding.detector})")
                continue
            else:
                # Standard Redaction: Surgical Removal (Transparent)
                # User requested "remove instead of adding boxes"
                annot = page.add_redact_annot(rect)
                annot.set_colors(stroke=None, fill=None) # Invisible/Transparent
                annot.info["content"] = "Redacted AI Trap"
                annot.update()
        except Exception:
            pass
    
    try:
        # Apply redactions (burn them in)
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
    except Exception:
        pass


def _has_visible_overlap(page: fitz.Page, target_rect: fitz.Rect, target_text: str) -> bool:
    """Check if the target rect overlaps with other visible text."""
    blocks = page.get_text("dict")["blocks"]
    
    # Expand rect MORE to catch near-misses (Safety Buffer increased to 6px)
    # This prevents "Collateral Damage" where apply_redactions() nukes nearby text
    # Proximity tests show blast radius is > 2px, so 6px is safely conservative.
    check_rect = fitz.Rect(target_rect)
    check_rect.x0 -= 6
    check_rect.y0 -= 6
    check_rect.x1 += 6
    check_rect.y1 += 6

    for block in blocks:
        if block.get("type") != 0:
            continue
            
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                # Skip the target text itself
                # (Simple heuristic: if text matches and rect is identical)
                span_rect = fitz.Rect(span.get("bbox"))
                if span_rect.intersects(target_rect) and span.get("text") == target_text:
                     continue
                
                # Check intersection
                if span_rect.intersects(check_rect):
                    # We found intersecting text. Is it "ours" (hidden) or "theirs" (visible)?
                    # If it's another hidden trap, we don't care. 
                    # If it's normal text (size > 6), we care.
                    span_size = span.get("size", 0)
                    if span_size > 6:
                        return True
    return False


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
                                 "LayeredTextDetector", "VisualMismatchDetector"]:
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
