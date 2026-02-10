import fitz  # PyMuPDF
# import numpy as np # Avoid heavy dependency
from backend.core.models import Finding, Location, Severity
from backend.core.detectors.base import BaseDetector

class VisualMismatchDetector(BaseDetector):
    """
    Detects text that renders as invisible or near-invisible.
    
    Strategy:
    1. Identify text span bbox.
    2. Render that specific region of the page to a pixmap.
    3. Analyze pixels to check if there is any 'ink' (contrast).
    4. If text characters exist but pixels are blank/uniform, it's a trap.
    
    Catches:
    - Render Mode 3 (Invisible)
    - Opacity 0 (Transparent)
    - White text on White background
    - Text covered by images/shapes (Z-order masking)
    """
    
    name = "VisualMismatchDetector"
    description = "Detects text that is present in code but visually invisible"
    severity = Severity.HIGH
    enabled = True
    
    def detect(self, doc: fitz.Document) -> list[Finding]:
        findings = []
        for i in range(len(doc)):
            page = doc[i]
            findings.extend(self._analyze_page(page, i))
        return findings

    def _analyze_page(self, page: fitz.Page, page_num: int) -> list[Finding]:
        findings = []
        
        # Get text blocks
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
        
        # Render the WHOLE page once to avoid 1000s of tiny renders (performance)
        # Use a decent median resolution (e.g. 72 dpi is 1.0 zoom, maybe 2.0 for precision)
        # However, for checking specific text, we might want to clip.
        # But 'page.get_pixmap(clip=...)' re-renders. 
        # Actually, let's try per-span clipping first. If slow, optimize.
        
        for block in blocks:
            if block["type"] != 0:
                continue
                
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text or len(text) < 2: 
                        continue
                        
                    bbox = fitz.Rect(span["bbox"])
                    
                    # Skip if off-screen (handled by OffScreenDetector)
                    if bbox.x1 < 0 or bbox.x0 > page.rect.width or bbox.y1 < 0 or bbox.y0 > page.rect.height:
                        continue
                        
                    # Skip tiny text (handled by TinyTextDetector)
                    if span["size"] < 3:
                        continue

                    # Render just this area
                    # Zoom=2 for better anti-aliasing detection
                    try:
                        pix = page.get_pixmap(clip=bbox, matrix=fitz.Matrix(2, 2))
                        
                        # Convert to numpy for fast analysis if possible, or just check bytes
                        # Pixmap samples are bytes.
                        # Check if it's all one color (or very low variance)
                        if pix.width < 1 or pix.height < 1:
                            continue
                            
                        # Simple check: Is there any significant deviation from the background?
                        # We assume background is likely white or the corner pixel color.
                        # Let's verify "imperceptibility".
                        
                        # Heuristic: Calculate standard deviation of pixel data.
                        # If std_dev is nearly 0, it's a solid color (invisible).
                        
                        # Access samples. format is typically RGB or RGBA
                        if pix.n < 3: # Gray or Alpha
                             continue 
                             
                        samples = pix.samples
                        # This is a byte sequence. 
                        # If we cast to list, it's slow. 
                        # let's just use fitz methods if available, or just simple check.
                        
                        # Check if all pixels are effectively identical to top-left pixel?
                        # No, background might be complex. 
                        
                        # Best approach for "Hidden Text":
                        # The text SHOULD add contrast.
                        # If the span region has ZERO or NEAR ZERO valid pixels compared to a blank region?
                        
                        # Let's count "non-white" pixels?
                        # No, background might be dark.
                        
                        # Let's try: Calculate pixel standard deviation.
                        # Valid text should produce high variance (text color vs background).
                        # Invisible text should have variance ~0 (uniform color).
                        
                        import math
                        
                        # Convert to list of bytes is ok for small clips
                        # optimization: skip expensive analysis for obvious cases
                        
                        # We can use pix.color_count() ? No.
                        
                        # Let's use Python's built-in checks on the bytes
                        # If content is "uniform", it's suspicious.
                        
                        # Check if the region is uniform color
                        if self._is_uniform_color(samples):
                             findings.append(Finding(
                                detector=self.name,
                                severity=self.severity,
                                location=Location(
                                    page=page_num+1, 
                                    x=bbox.x0, 
                                    y=bbox.y0,
                                    width=bbox.width,
                                    height=bbox.height
                                ),
                                content="Visually Invisible Text",
                                context=text[:50],
                                explanation="Text is present in code but renders as a uniform color block (invisible) to the user."
                            ))
                            
                    except Exception as e:
                        # print(f"Visual check error: {e}")
                        pass
                        
        return findings

    def _is_uniform_color(self, samples: bytes) -> bool:
        """Check if byte stream represents a uniform color (low variance)."""
        if not samples or len(samples) < 10:
            return True
        
        # Optimization: Check a subset of pixels to avoid O(N) on large regions
        # Check standard deviation or just unique count?
        # unique count is robust against solid colors.
        
        # If we just take every Nth byte to sample?
        # samples is bytes. 
        # set(samples) is fast.
        
        unique_bytes = set(samples)
        
        # A solid color region (e.g. all white) will have very few unique byte values (255, maybe 254/253 due to noise)
        # Anti-aliased text will have many unique values (edges fade).
        
        # Threshold: 
        # - Solid block: < 5 unique values
        # - Text: > 10 unique values usually
        
        if len(unique_bytes) < 5: 
             return True
             
        return False

