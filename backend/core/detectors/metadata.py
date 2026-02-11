"""Detector for potentially problematic document metadata."""

import fitz  # PyMuPDF

from backend.core.models import Finding, Location, Severity
from backend.core.detectors.base import BaseDetector


class MetadataDetector(BaseDetector):
    """Detects document metadata that screen readers might expose."""
    
    name = "MetadataDetector"
    description = "Flags document metadata that may be read by assistive technology"
    severity = Severity.LOW
    enabled = False  # Disabled: rarely useful for homework traps
    
    # Metadata fields to check
    METADATA_FIELDS = [
        ("title", "Document title"),
        ("author", "Author name"),
        ("subject", "Subject"),
        ("keywords", "Keywords"),
        ("creator", "Creator application"),
        ("producer", "PDF producer"),
    ]
    
    def detect(self, doc: fitz.Document) -> list[Finding]:
        """Check document metadata for potential issues."""
        findings = []
        
        metadata = doc.metadata
        if not metadata:
            return findings
        
        for field, description in self.METADATA_FIELDS:
            value = metadata.get(field, "")
            if not value or not value.strip():
                continue
            
            value = value.strip()
            
            # Flag potentially problematic metadata
            issues = self._analyze_metadata_value(field, value)
            
            if issues:
                findings.append(Finding(
                    detector=self.name,
                    severity=Severity.MEDIUM if issues else Severity.LOW,
                    location=Location(page=0),  # Metadata is document-level
                    content=f"Metadata: {description}",
                    context=value[:100] + ("..." if len(value) > 100 else ""),
                    explanation=f"Document {description.lower()} contains: '{value[:50]}...'. " + 
                               (f"Issues: {', '.join(issues)}. " if issues else "") +
                               "Some screen readers announce document metadata, which may expose unintended information."
                ))
        
        return findings
    
    def _analyze_metadata_value(self, field: str, value: str) -> list[str]:
        """Analyze a metadata value for potential issues."""
        issues = []
        
        # Check for suspiciously long values (might contain hidden content)
        if len(value) > 200:
            issues.append("unusually long value")
        
        # Check for hidden characters
        if any(ord(c) < 32 and c not in '\n\r\t' for c in value):
            issues.append("contains control characters")
        
        # Check for potential PII in author field
        if field == "author":
            # Simple heuristic: if it looks like a full email
            if "@" in value and "." in value:
                issues.append("may contain email address")
        
        # Check for file paths (common in creator/producer)
        if field in ("creator", "producer"):
            if "/" in value or "\\" in value:
                if any(sensitive in value.lower() for sensitive in ["users", "home", "documents"]):
                    issues.append("may expose file path")
        
        return issues
