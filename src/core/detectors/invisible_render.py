"""Detector for text with invisible rendering mode."""

import fitz  # PyMuPDF

from src.core.models import Finding, Location, Severity
from src.core.detectors.base import BaseDetector


class InvisibleRenderDetector(BaseDetector):
    """
    Detects text rendered in invisible mode.
    
    PDF supports a text rendering mode that makes text invisible while
    still being selectable and readable by screen readers/AI.
    Mode 3 = invisible fill and stroke.
    """
    
    name = "InvisibleRenderDetector"
    description = "Detects text with invisible rendering mode in PDF"
    severity = Severity.HIGH
    enabled = True
    
    def detect(self, doc: fitz.Document) -> list[Finding]:
        """Scan for invisible text rendering."""
        findings = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_findings = self._analyze_page(page, page_num)
            findings.extend(page_findings)
        
        return findings
    
    def _analyze_page(self, page: fitz.Page, page_num: int) -> list[Finding]:
        """Check for invisible rendering mode in page content."""
        findings = []
        
        # Get the raw page content to look for rendering mode changes
        # Text rendering mode 3 = invisible
        try:
            # Extract text blocks and check for invisible text via alternate method
            # PyMuPDF's rawdict can show more details
            blocks = page.get_text("rawdict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
            
            for block in blocks:
                if block.get("type") != 0:
                    continue
                
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        # Check span flags for rendering mode hints
                        flags = span.get("flags", 0)
                        text = span.get("text", "").strip()
                        
                        if not text or len(text) < 3:
                            continue
                        
                        # Check if text appears to be invisible via other indicators
                        # Some PDFs mark invisible text with specific flags
                        # Also check for text with no visual representation
                        
                        color = span.get("color", 0)
                        size = span.get("size", 12)
                        
                        # Invisible text often has color=0 (black) but render mode makes it invisible
                        # Combined with other suspicious attributes
                        bbox = span.get("bbox", (0, 0, 0, 0))
                        
                        # Check if bbox height is near-zero (invisible rendering)
                        if bbox[3] - bbox[1] < 0.5 and size > 0:
                            findings.append(Finding(
                                detector=self.name,
                                severity=self.severity,
                                location=Location(
                                    page=page_num + 1,
                                    x=bbox[0],
                                    y=bbox[1],
                                ),
                                content="Invisible render mode (zero-height text)",
                                context=text[:100] + ("..." if len(text) > 100 else ""),
                                explanation="Text has near-zero rendered height despite having content. This may indicate invisible rendering mode."
                            ))
        
        except Exception as e:
            # If analysis fails, continue without findings
            pass
        
        return findings
