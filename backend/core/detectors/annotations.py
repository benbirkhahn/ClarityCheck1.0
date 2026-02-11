"""Detector for hidden annotations and comments."""

import fitz  # PyMuPDF

from backend.core.models import Finding, Location, Severity
from backend.core.detectors.base import BaseDetector


class HiddenAnnotationDetector(BaseDetector):
    """Detects annotations that may contain hidden text."""
    
    name = "HiddenAnnotationDetector"
    description = "Detects PDF annotations that may be read by assistive technology"
    severity = Severity.MEDIUM
    enabled = False  # Disabled: rarely useful for homework traps
    
    # Annotation types that often contain hidden/problematic content
    SUSPICIOUS_TYPES = {
        fitz.PDF_ANNOT_TEXT: "Text annotation (sticky note)",
        fitz.PDF_ANNOT_FREE_TEXT: "Free text annotation",
        fitz.PDF_ANNOT_POPUP: "Popup annotation",
        fitz.PDF_ANNOT_REDACT: "Redaction annotation (may expose redacted content)",
        fitz.PDF_ANNOT_WIDGET: "Form widget",
    }
    
    def detect(self, doc: fitz.Document) -> list[Finding]:
        """Scan for hidden annotations."""
        findings = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_findings = self._analyze_page(page, page_num)
            findings.extend(page_findings)
        
        return findings
    
    def _analyze_page(self, page: fitz.Page, page_num: int) -> list[Finding]:
        """Analyze annotations on a single page."""
        findings = []
        
        for annot in page.annots():
            if annot is None:
                continue
            
            annot_type = annot.type[0]  # Numeric type
            annot_type_name = annot.type[1]  # String name
            
            # Get annotation content
            content = annot.info.get("content", "")
            title = annot.info.get("title", "")
            subject = annot.info.get("subject", "")
            
            # Check if annotation has text content
            text_content = " | ".join(filter(None, [title, subject, content]))
            
            if not text_content.strip():
                continue
            
            # Check if it's a suspicious type or has concerning properties
            rect = annot.rect
            is_tiny = rect.width < 5 or rect.height < 5
            is_invisible = annot.opacity == 0 if hasattr(annot, 'opacity') else False
            
            severity = self.severity
            issues = []
            
            if annot_type in self.SUSPICIOUS_TYPES:
                issues.append(self.SUSPICIOUS_TYPES[annot_type])
            
            if is_tiny:
                issues.append("microscopic size")
                severity = Severity.HIGH
            
            if is_invisible:
                issues.append("invisible (opacity=0)")
                severity = Severity.HIGH
            
            # Flag if annotation has content
            if text_content:
                findings.append(Finding(
                    detector=self.name,
                    severity=severity,
                    location=Location(
                        page=page_num + 1,
                        x=rect.x0,
                        y=rect.y0,
                    ),
                    content=f"Annotation: {annot_type_name}" + (f" ({', '.join(issues)})" if issues else ""),
                    context=text_content[:100] + ("..." if len(text_content) > 100 else ""),
                    explanation="PDF annotations may be read by screen readers. Review this content to ensure it's appropriate and accessible."
                ))
        
        return findings
