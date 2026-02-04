"""Detector for text with color matching the background (e.g., white on white)."""

import fitz  # PyMuPDF

from src.core.models import Finding, Location, Severity
from src.core.detectors.base import BaseDetector


def color_distance(c1: tuple, c2: tuple) -> float:
    """Calculate Euclidean distance between two RGB colors (0-1 scale)."""
    if len(c1) != 3 or len(c2) != 3:
        return 1.0  # Assume different if color format unexpected
    return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5


def is_near_white(color: tuple, threshold: float = 0.1) -> bool:
    """Check if a color is near white."""
    if len(color) != 3:
        return False
    return all(c > (1 - threshold) for c in color)


def is_near_black(color: tuple, threshold: float = 0.1) -> bool:
    """Check if a color is near black."""
    if len(color) != 3:
        return False
    return all(c < threshold for c in color)


class MatchingColorDetector(BaseDetector):
    """Detects text where the color closely matches the background."""
    
    name = "MatchingColorDetector"
    description = "Detects hidden text where text color matches background color"
    severity = Severity.HIGH
    enabled = True
    
    def __init__(self, color_threshold: float = 0.05, min_text_length: int = 3):
        """
        Args:
            color_threshold: Max color distance to consider "matching" (0-1 scale)
            min_text_length: Minimum text length to report (avoid single chars)
        """
        self.color_threshold = color_threshold
        self.min_text_length = min_text_length
    
    def detect(self, doc: fitz.Document) -> list[Finding]:
        """Scan for text with colors matching likely backgrounds."""
        findings = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_findings = self._analyze_page(page, page_num)
            findings.extend(page_findings)
        
        return findings
    
    def _analyze_page(self, page: fitz.Page, page_num: int) -> list[Finding]:
        """Analyze a single page for hidden text."""
        findings = []
        
        # Get text with styling information
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
        
        # Estimate page background (usually white, but check)
        # For MVP, assume white background - could enhance later
        page_bg = (1.0, 1.0, 1.0)  # White
        
        for block in blocks:
            if block.get("type") != 0:  # Skip non-text blocks
                continue
            
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if len(text) < self.min_text_length:
                        continue
                    
                    # Get text color (PyMuPDF returns as int, convert to RGB tuple)
                    color_int = span.get("color", 0)
                    text_color = self._int_to_rgb(color_int)
                    
                    # Check if text color matches background
                    distance = color_distance(text_color, page_bg)
                    
                    if distance < self.color_threshold:
                        bbox = span.get("bbox", (0, 0, 0, 0))
                        
                        # Determine the specific issue
                        if is_near_white(text_color):
                            issue_type = "white text on white background"
                        elif is_near_black(text_color) and is_near_black(page_bg):
                            issue_type = "black text on black background"
                        else:
                            issue_type = f"text color matches background"
                        
                        findings.append(Finding(
                            detector=self.name,
                            severity=self.severity,
                            location=Location(
                                page=page_num + 1,
                                x=bbox[0],
                                y=bbox[1],
                            ),
                            content=f"Hidden text ({issue_type})",
                            context=text[:100] + ("..." if len(text) > 100 else ""),
                            explanation=f"Text with color {self._rgb_to_hex(text_color)} is nearly invisible against the background. Screen readers will read this aloud even though sighted users cannot see it."
                        ))
        
        return findings
    
    def _int_to_rgb(self, color_int: int) -> tuple:
        """Convert PyMuPDF color int to RGB tuple (0-1 scale)."""
        # PyMuPDF stores color as integer: 0xRRGGBB
        r = ((color_int >> 16) & 0xFF) / 255.0
        g = ((color_int >> 8) & 0xFF) / 255.0
        b = (color_int & 0xFF) / 255.0
        return (r, g, b)
    
    def _rgb_to_hex(self, rgb: tuple) -> str:
        """Convert RGB tuple (0-1 scale) to hex string."""
        r, g, b = [int(c * 255) for c in rgb]
        return f"#{r:02X}{g:02X}{b:02X}"
