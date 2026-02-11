"""Detector for text with suspicious character/word spacing."""

import re
import fitz  # PyMuPDF

from backend.core.models import Finding, Location, Severity
from backend.core.detectors.base import BaseDetector


class SuspiciousSpacingDetector(BaseDetector):
    """
    Detects text with unusual spacing patterns.
    
    Common AI trap technique: "T h i s  i s  h i d d e n" - spaces between
    every character to evade simple text matching.
    """
    
    name = "SuspiciousSpacingDetector"
    description = "Detects text with unusual spacing that may indicate obfuscation"
    severity = Severity.MEDIUM
    enabled = False  # Disabled: too aggressive, needs tuning with training data
    
    def __init__(self, min_text_length: int = 10):
        self.min_text_length = min_text_length
        # Pattern: single char, space(s), single char, space(s)... repeated
        self.spaced_pattern = re.compile(r'(\S\s+){5,}')
        # Pattern: multiple spaces between words
        self.multispace_pattern = re.compile(r'\S\s{3,}\S')
    
    def detect(self, doc: fitz.Document) -> list[Finding]:
        """Scan for suspiciously spaced text."""
        findings = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_findings = self._analyze_page(page, page_num)
            findings.extend(page_findings)
        
        return findings
    
    def _analyze_page(self, page: fitz.Page, page_num: int) -> list[Finding]:
        """Analyze text spacing on a page."""
        findings = []
        
        blocks = page.get_text("dict")["blocks"]
        
        for block in blocks:
            if block.get("type") != 0:
                continue
            
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "")
                    if len(text) < self.min_text_length:
                        continue
                    
                    bbox = span.get("bbox", (0, 0, 0, 0))
                    
                    # Check for character-by-character spacing
                    if self.spaced_pattern.search(text):
                        # Verify it's actually spaced-out text, not normal text
                        # by checking the ratio of spaces to non-spaces
                        non_space = len(text.replace(" ", ""))
                        spaces = len(text) - non_space
                        
                        if non_space > 0 and spaces / non_space > 0.7:
                            # Reconstruct what the text probably says
                            reconstructed = text.replace(" ", "")
                            
                            findings.append(Finding(
                                detector=self.name,
                                severity=Severity.HIGH,
                                location=Location(
                                    page=page_num + 1,
                                    x=bbox[0],
                                    y=bbox[1],
                                ),
                                content="Obfuscated text (character spacing)",
                                context=f"Original: {text[:60]}... | Decoded: {reconstructed[:40]}...",
                                explanation="Text has spaces between every character, a common technique to evade text detection while remaining readable by AI/screen readers."
                            ))
                    
                    # Check for excessive inter-word spacing
                    elif self.multispace_pattern.search(text):
                        findings.append(Finding(
                            detector=self.name,
                            severity=Severity.MEDIUM,
                                location=Location(
                                    page=page_num + 1,
                                    x=bbox[0],
                                    y=bbox[1],
                                    width=bbox[2]-bbox[0],
                                    height=bbox[3]-bbox[1]
                                ),
                            content="Unusual word spacing",
                            context=text[:100] + ("..." if len(text) > 100 else ""),
                            explanation="Text contains excessive spacing between words, which may indicate obfuscation attempts."
                        ))
        
        return findings
