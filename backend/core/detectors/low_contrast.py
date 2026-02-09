"""Detector for very low contrast text (not quite matching, but nearly invisible)."""

import fitz  # PyMuPDF

from backend.core.models import Finding, Location, Severity
from backend.core.detectors.base import BaseDetector


def luminance(rgb: tuple) -> float:
    """Calculate relative luminance of an RGB color (0-1 scale)."""
    r, g, b = rgb
    # sRGB to linear
    def linearize(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    
    r, g, b = linearize(r), linearize(g), linearize(b)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(l1: float, l2: float) -> float:
    """Calculate WCAG contrast ratio between two luminance values."""
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


class LowContrastDetector(BaseDetector):
    """
    Detects text with very low contrast against background.
    
    WCAG requires minimum 4.5:1 for normal text, 3:1 for large text.
    We flag anything below 2:1 as potentially hidden.
    """
    
    name = "LowContrastDetector"
    description = "Detects text with contrast too low to be easily readable"
    severity = Severity.MEDIUM
    enabled = True
    
    def __init__(self, min_contrast: float = 2.0, min_text_length: int = 5):
        """
        Args:
            min_contrast: Minimum contrast ratio to consider visible
            min_text_length: Minimum text length to report
        """
        self.min_contrast = min_contrast
        self.min_text_length = min_text_length
    
    def detect(self, doc: fitz.Document) -> list[Finding]:
        """Scan for low contrast text."""
        findings = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_findings = self._analyze_page(page, page_num)
            findings.extend(page_findings)
        
        return findings
    
    def _analyze_page(self, page: fitz.Page, page_num: int) -> list[Finding]:
        """Analyze text contrast on a page."""
        findings = []
        
        # Assume white background for MVP
        bg_luminance = luminance((1.0, 1.0, 1.0))
        
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
        
        for block in blocks:
            if block.get("type") != 0:
                continue
            
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if len(text) < self.min_text_length:
                        continue
                    
                    color_int = span.get("color", 0)
                    text_color = self._int_to_rgb(color_int)
                    text_luminance = luminance(text_color)
                    
                    ratio = contrast_ratio(text_luminance, bg_luminance)
                    
                    # Skip pure white (caught by MatchingColorDetector)
                    # and normal readable text
                    if ratio < self.min_contrast and ratio > 1.05:
                        bbox = span.get("bbox", (0, 0, 0, 0))
                        
                        findings.append(Finding(
                            detector=self.name,
                            severity=Severity.HIGH if ratio < 1.5 else Severity.MEDIUM,
                            location=Location(
                                page=page_num + 1,
                                x=bbox[0],
                                y=bbox[1],
                            ),
                            content=f"Low contrast text (ratio: {ratio:.2f}:1)",
                            context=text[:100] + ("..." if len(text) > 100 else ""),
                            explanation=f"Text color {self._rgb_to_hex(text_color)} has contrast ratio {ratio:.2f}:1 against white. WCAG minimum is 4.5:1. This text is difficult or impossible to read visually."
                        ))
        
        return findings
    
    def _int_to_rgb(self, color_int: int) -> tuple:
        """Convert PyMuPDF color int to RGB tuple (0-1 scale)."""
        r = ((color_int >> 16) & 0xFF) / 255.0
        g = ((color_int >> 8) & 0xFF) / 255.0
        b = (color_int & 0xFF) / 255.0
        return (r, g, b)
    
    def _rgb_to_hex(self, rgb: tuple) -> str:
        """Convert RGB tuple to hex string."""
        r, g, b = [int(c * 255) for c in rgb]
        return f"#{r:02X}{g:02X}{b:02X}"
