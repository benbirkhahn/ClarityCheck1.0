"""Detector for text with invisible rendering mode."""

import fitz  # PyMuPDF

from backend.core.models import Finding, Location, Severity
from backend.core.detectors.base import BaseDetector


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
        
        try:
            for span in page.get_texttrace():
                text = "".join(chr(c[0]) for c in span.get("chars", [])).strip()
                if not text or len(text) < 3:
                    continue

                bbox = span.get("bbox", (0, 0, 0, 0))
                render_type = span.get("type")
                opacity = span.get("opacity", 1.0)

                if render_type == 3 or opacity == 0 or bbox[3] - bbox[1] < 0.5:
                    findings.append(Finding(
                        detector=self.name,
                        severity=self.severity,
                        location=Location(
                            page=page_num + 1,
                            x=bbox[0],
                            y=bbox[1],
                            width=bbox[2] - bbox[0],
                            height=bbox[3] - bbox[1],
                        ),
                        content="Invisible render mode",
                        context=text[:100] + ("..." if len(text) > 100 else ""),
                        explanation="Text exists in the PDF text layer but is rendered invisibly or with zero opacity."
                    ))

        except Exception:
            pass
        
        return findings
