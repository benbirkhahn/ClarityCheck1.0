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
        margin = self.margin_threshold

        # texttrace preserves off-page text that normal block extraction can miss.
        for span in page.get_texttrace():
            chars = "".join(chr(c[0]) for c in span.get("chars", [])).strip()
            if not chars:
                continue

            bbox = span.get("bbox")
            if not bbox:
                continue

            x0, y0, x1, y1 = bbox
            is_off_screen = (
                x1 < -margin or
                x0 > page_rect.width + margin or
                y1 < -margin or
                y0 > page_rect.height + margin
            )

            if is_off_screen:
                findings.append(Finding(
                    detector=self.name,
                    severity=self.severity,
                    location=Location(
                        page=page_num + 1,
                        x=x0,
                        y=y0,
                        width=x1 - x0,
                        height=y1 - y0,
                    ),
                    content="Off-screen text",
                    context=chars[:100] + ("..." if len(chars) > 100 else ""),
                    explanation=f"Text at position ({x0:.0f}, {y0:.0f}) is outside visible page area."
                ))
        
        return findings
