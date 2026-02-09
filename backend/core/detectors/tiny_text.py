"""Detector for extremely small (microscopic) text."""

import fitz  # PyMuPDF

from backend.core.models import Finding, Location, Severity
from backend.core.detectors.base import BaseDetector


class TinyTextDetector(BaseDetector):
    """Detects text that is too small to be visible to humans."""
    
    name = "TinyTextDetector"
    description = "Detects microscopic text that humans cannot read but screen readers will"
    severity = Severity.HIGH
    enabled = True
    
    def __init__(self, min_font_size: float = 4.0, min_text_length: int = 5):
        """
        Args:
            min_font_size: Text smaller than this (in points) is flagged
            min_text_length: Minimum text length to report
        """
        self.min_font_size = min_font_size
        self.min_text_length = min_text_length
    
    def detect(self, doc: fitz.Document) -> list[Finding]:
        """Scan for microscopic text."""
        findings = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_findings = self._analyze_page(page, page_num)
            findings.extend(page_findings)
        
        return findings
    
    def _analyze_page(self, page: fitz.Page, page_num: int) -> list[Finding]:
        """Analyze a single page for tiny text."""
        findings = []
        
        blocks = page.get_text("dict")["blocks"]
        
        for block in blocks:
            if block.get("type") != 0:
                continue
            
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if len(text) < self.min_text_length:
                        continue
                    
                    font_size = span.get("size", 12)
                    
                    if font_size < self.min_font_size:
                        bbox = span.get("bbox", (0, 0, 0, 0))
                        
                        findings.append(Finding(
                            detector=self.name,
                            severity=self.severity,
                            location=Location(
                                page=page_num + 1,
                                x=bbox[0],
                                y=bbox[1],
                            ),
                            content=f"Microscopic text ({font_size:.1f}pt)",
                            context=text[:100] + ("..." if len(text) > 100 else ""),
                            explanation=f"Text at {font_size:.1f}pt is too small to read visually (minimum readable is ~6pt). This hidden text will still be read by screen readers."
                        ))
        
        return findings
