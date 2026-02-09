"""Detector for zero-width and invisible characters."""

import fitz  # PyMuPDF

from backend.core.models import Finding, Location, Severity
from backend.core.detectors.base import BaseDetector


ZERO_WIDTH_CHARS = {
    '\u200b': 'Zero Width Space (ZWSP)',
    '\u200c': 'Zero Width Non-Joiner (ZWNJ)',
    '\u200d': 'Zero Width Joiner (ZWJ)',
    '\u200e': 'Left-to-Right Mark (LRM)',
    '\u200f': 'Right-to-Left Mark (RLM)',
    '\u2060': 'Word Joiner (WJ)',
    '\ufeff': 'Byte Order Mark (BOM)',
    '\u00ad': 'Soft Hyphen',
    '\u034f': 'Combining Grapheme Joiner',
    '\u3164': 'Hangul Filler',
}


class ZeroWidthCharDetector(BaseDetector):
    """Detects zero-width and invisible characters in PDF text."""
    
    name = "ZeroWidthCharDetector"
    description = "Detects invisible characters that screen readers may vocalize"
    severity = Severity.HIGH
    enabled = True
    
    def __init__(self, context_chars: int = 20):
        self.context_chars = context_chars
    
    def detect(self, doc: fitz.Document) -> list[Finding]:
        """Scan all pages for zero-width characters."""
        findings = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            blocks = page.get_text("dict")["blocks"]
            
            for i, char in enumerate(text):
                if char in ZERO_WIDTH_CHARS:
                    char_name = ZERO_WIDTH_CHARS[char]
                    
                    # Extract context
                    start = max(0, i - self.context_chars)
                    end = min(len(text), i + self.context_chars + 1)
                    context = text[start:end].replace(char, f'[{char_name}]')
                    context = context.replace('\n', ' ').strip()
                    
                    location = self._find_char_location(blocks, i, page_num)
                    
                    findings.append(Finding(
                        detector=self.name,
                        severity=self.severity,
                        location=location,
                        content=f"[{char_name}] (U+{ord(char):04X})",
                        context=context,
                        explanation=f"{char_name} is invisible but may be announced by screen readers."
                    ))
        
        return findings
    
    def _find_char_location(self, blocks: list, char_index: int, page_num: int) -> Location:
        """Approximate x,y coordinates of a character."""
        cumulative = 0
        
        for block in blocks:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    span_text = span.get("text", "")
                    if cumulative <= char_index < cumulative + len(span_text):
                        bbox = span.get("bbox", (0, 0, 0, 0))
                        return Location(page=page_num + 1, x=bbox[0], y=bbox[1], char_index=char_index)
                    cumulative += len(span_text)
        
        return Location(page=page_num + 1, char_index=char_index)
