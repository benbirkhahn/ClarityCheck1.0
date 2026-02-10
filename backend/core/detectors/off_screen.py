"""Detector for text positioned outside visible page bounds."""

import fitz  # PyMuPDF

from backend.core.models import Finding, Location, Severity
from backend.core.detectors.base import BaseDetector


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
        
        # Standard dict is sufficient as rawdict/xml also fail for extreme off-screen text
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
                    if not bbox: continue
                    
                    x0, y0, x1, y1 = bbox
                    if not bbox: continue
                    
                    x0, y0, x1, y1 = bbox
                    
                    # Simple robust check: Is it effectively off the page?
                    # Using a generous margin (e.g. 50pts) to avoid false positives on bleed text
                    margin = self.margin_threshold
                    
                    is_off_screen = (
                        x1 < -margin or                 # Far Left
                        x0 > page_rect.width + margin or # Far Right
                        y1 < -margin or                 # Far Above
                        y0 > page_rect.height + margin  # Far Below
                    )
                    
                    if is_off_screen:
                        findings.append(Finding(
                            detector=self.name,
                            severity=self.severity,
                            location=Location(
                                page=page_num + 1,
                                x=x0,
                                y=y0,
                            ),
                            content="Off-screen text",
                            context=text[:100] + ("..." if len(text) > 100 else ""),
                            explanation=f"Text at position ({x0:.0f}, {y0:.0f}) is outside visible page area. Logic: x1({x1}) < -{margin}"
                        ))
        
        return findings
