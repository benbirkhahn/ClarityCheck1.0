"""Detector for text potentially hidden under images or overlapping elements."""

import fitz  # PyMuPDF

from backend.core.models import Finding, Location, Severity
from backend.core.detectors.base import BaseDetector


class LayeredTextDetector(BaseDetector):
    """
    Detects text that may be hidden under images or other elements.
    
    Looks for text blocks that share coordinates with image blocks,
    suggesting text might be layered underneath.
    """
    
    name = "LayeredTextDetector"
    description = "Detects text potentially hidden under images or other elements"
    severity = Severity.HIGH
    enabled = False  # Disabled: complex edge cases, needs tuning
    
    def __init__(self, overlap_threshold: float = 0.5):
        """
        Args:
            overlap_threshold: Minimum overlap ratio to flag (0-1)
        """
        self.overlap_threshold = overlap_threshold
    
    def detect(self, doc: fitz.Document) -> list[Finding]:
        """Scan for text hidden under images."""
        findings = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_findings = self._analyze_page(page, page_num)
            findings.extend(page_findings)
        
        return findings
    
    def _analyze_page(self, page: fitz.Page, page_num: int) -> list[Finding]:
        """Analyze text and image layering on a page."""
        findings = []
        
        blocks = page.get_text("dict")["blocks"]
        
        # Separate text and image blocks
        text_blocks = []
        image_rects = []
        
        for block in blocks:
            bbox = block.get("bbox", (0, 0, 0, 0))
            rect = fitz.Rect(bbox)
            
            if block.get("type") == 0:  # Text
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if text and len(text) >= 5:
                            span_bbox = span.get("bbox", (0, 0, 0, 0))
                            text_blocks.append({
                                "rect": fitz.Rect(span_bbox),
                                "text": text
                            })
            
            elif block.get("type") == 1:  # Image
                image_rects.append(rect)
        
        # Also get images via get_images for more complete coverage
        try:
            for img in page.get_images():
                # Get image bbox
                img_rects = page.get_image_rects(img[0])
                for r in img_rects:
                    if r:
                        image_rects.append(r)
        except:
            pass
        
        # Check for text overlapping with images
        for tb in text_blocks:
            text_rect = tb["rect"]
            text = tb["text"]
            
            # Check overlap with images
            for img_rect in image_rects:
                overlap = self._calculate_overlap(text_rect, img_rect)
                
                if overlap > self.overlap_threshold:
                    findings.append(Finding(
                        detector=self.name,
                        severity=self.severity,
                            location=Location(
                                page=page_num + 1,
                                x=text_rect.x0,
                                y=text_rect.y0,
                                width=text_rect.width,
                                height=text_rect.height
                            ),
                        content=f"Text under image ({overlap*100:.0f}% overlap)",
                        context=text[:100] + ("..." if len(text) > 100 else ""),
                        explanation="Text appears to be positioned under an image. This text is invisible to users but readable by AI/screen readers."
                    ))
                    break  # Don't report same text multiple times
            
            # Check overlap with filled drawings (e.g. white boxes hiding text)
            # Only consider FILLED drawings
            drawings = page.get_drawings()
            for draw in drawings:
                # Type 'f' or 'fs' means filled
                if 'f' in draw.get("type", ""):
                    draw_rect = draw["rect"]
                    
                    # Skip if drawing is tiny (likely noise or bullet point)
                    if draw_rect.width < 5 or draw_rect.height < 5:
                        continue
                        
                    overlap = self._calculate_overlap(text_rect, draw_rect)
                    
                    if overlap > 0.9: # High overlap required for "covered by box"
                         findings.append(Finding(
                            detector=self.name,
                            severity=self.severity,
                            location=Location(
                                page=page_num + 1,
                                x=text_rect.x0,
                                y=text_rect.y0,
                            ),
                            content=f"Text covered by shape ({overlap*100:.0f}% overlap)",
                            context=text[:100] + ("..." if len(text) > 100 else ""),
                            explanation="Text appears to be covered by a filled shape (e.g., a white box). This is a common technique to hide instructions."
                        ))
                         break

        
        return findings
    
    def _calculate_overlap(self, rect1: fitz.Rect, rect2: fitz.Rect) -> float:
        """Calculate overlap ratio of rect1 with rect2."""
        intersection = rect1 & rect2  # Intersection
        
        if intersection.is_empty:
            return 0.0
        
        rect1_area = rect1.width * rect1.height
        if rect1_area == 0:
            return 0.0
        
        intersection_area = intersection.width * intersection.height
        return intersection_area / rect1_area
