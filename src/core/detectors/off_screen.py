"""Detector for text positioned outside visible page bounds."""

import fitz  # PyMuPDF

from src.core.models import Finding, Location, Severity
from src.core.detectors.base import BaseDetector


class OffScreenTextDetector(BaseDetector):
    """Detects text positioned outside the visible page area."""
    
    name = "OffScreenTextDetector"
    description = "Detects text hidden by positioning outside page bounds"
    severity = Severity.HIGH
    enabled = True
    
    def __init__(self, margin_threshold: float = 50.0):
        """
        Args:
            margin_threshold: How far outside bounds to flag (in points)
        """
        self.margin_threshold = margin_threshold
    
    def detect(self, doc: fitz.Document) -> list[Finding]:
        """Scan for text outside page boundaries."""
        findings = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_rect = page.rect  # Page boundaries
            page_findings = self._analyze_page(page, page_num, page_rect)
            findings.extend(page_findings)
        
        return findings
    
    def _analyze_page(self, page: fitz.Page, page_num: int, page_rect: fitz.Rect) -> list[Finding]:
        """Analyze a single page for off-screen text."""
        findings = []
        
        blocks = page.get_text("dict")["blocks"]
        
        for block in blocks:
            if block.get("type") != 0:
                continue
            
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if not text:
                        continue
                    
                    bbox = span.get("bbox", (0, 0, 0, 0))
                    x0, y0, x1, y1 = bbox
                    
                    # Check if text is outside page bounds
                    issues = []
                    
                    if x1 < -self.margin_threshold:
                        issues.append("far left of page")
                    elif x0 > page_rect.width + self.margin_threshold:
                        issues.append("far right of page")
                    
                    if y1 < -self.margin_threshold:
                        issues.append("above page")
                    elif y0 > page_rect.height + self.margin_threshold:
                        issues.append("below page")
                    
                    # Also check for extremely negative positions (common trick)
                    if x0 < -1000 or y0 < -1000:
                        issues.append("positioned at extreme negative coordinates")
                    
                    if issues:
                        findings.append(Finding(
                            detector=self.name,
                            severity=self.severity,
                            location=Location(
                                page=page_num + 1,
                                x=x0,
                                y=y0,
                            ),
                            content=f"Off-screen text ({', '.join(issues)})",
                            context=text[:100] + ("..." if len(text) > 100 else ""),
                            explanation=f"Text at position ({x0:.0f}, {y0:.0f}) is outside visible page area ({page_rect.width:.0f}x{page_rect.height:.0f}). Screen readers may still read this hidden content."
                        ))
        
        return findings
