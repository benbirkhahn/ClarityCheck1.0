"""Detector for text potentially hidden under images or overlapping elements."""

import fitz  # PyMuPDF

from backend.core.models import Finding, Location, Severity
from backend.core.detectors.base import BaseDetector


class LayeredTextDetector(BaseDetector):
    """
    Detects text that may be hidden under images or other elements.
    
    Looks for text blocks that share coordinates with image blocks,
    suggesting text might be layered underneath.
    """
    
    name = "LayeredTextDetector"
    description = "Detects text potentially hidden under images or other elements"
    severity = Severity.HIGH
    enabled = True
    
    def __init__(
        self,
        overlap_threshold: float = 0.5,
        cover_overlap_threshold: float = 0.75,
        max_cover_text_spans: int = 2,
    ):
        """
        Args:
            overlap_threshold: Minimum overlap ratio to flag (0-1)
        """
        self.overlap_threshold = overlap_threshold
        self.cover_overlap_threshold = cover_overlap_threshold
        self.max_cover_text_spans = max_cover_text_spans
    
    def detect(self, doc: fitz.Document) -> list[Finding]:
        """Scan for text hidden under images."""
        findings = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_findings = self._analyze_page(page, page_num)
            findings.extend(page_findings)
        
        return findings
    
    def _analyze_page(self, page: fitz.Page, page_num: int) -> list[Finding]:
        """Analyze text and image layering on a page."""
        findings = []
        
        blocks = page.get_text("dict")["blocks"]
        
        # Separate text and image blocks
        text_blocks = []
        image_rects = []
        
        for block in blocks:
            bbox = block.get("bbox", (0, 0, 0, 0))
            rect = fitz.Rect(bbox)
            
            if block.get("type") == 0:  # Text
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if text and len(text) >= 5:
                            span_bbox = span.get("bbox", (0, 0, 0, 0))
                            text_blocks.append({
                                "rect": fitz.Rect(span_bbox),
                                "text": text
                            })
            
            elif block.get("type") == 1:  # Image
                image_rects.append(rect)
        
        # Also get images via get_images for more complete coverage
        try:
            for img in page.get_images():
                # Get image bbox
                img_rects = page.get_image_rects(img[0])
                for r in img_rects:
                    if r:
                        image_rects.append(r)
        except:
            pass
        
        cover_shapes = self._candidate_cover_shapes(page, text_blocks)

        # Check for text overlapping with images
        for tb in text_blocks:
            text_rect = tb["rect"]
            text = tb["text"]
            
            # Check overlap with images
            for img_rect in image_rects:
                overlap = self._calculate_overlap(text_rect, img_rect)
                
                if overlap > self.overlap_threshold:
                    findings.append(Finding(
                        detector=self.name,
                        severity=self.severity,
                            location=Location(
                                page=page_num + 1,
                                x=text_rect.x0,
                                y=text_rect.y0,
                                width=text_rect.width,
                                height=text_rect.height
                            ),
                        content=f"Text under image ({overlap*100:.0f}% overlap)",
                        context=text[:100] + ("..." if len(text) > 100 else ""),
                        explanation="Text appears to be positioned under an image. This text is invisible to users but readable by AI/screen readers."
                    ))
                    break  # Don't report same text multiple times
            
            # Check overlap with targeted cover shapes, not general layout panels.
            for draw_rect in cover_shapes:
                overlap = self._calculate_overlap(text_rect, draw_rect)

                if overlap > self.cover_overlap_threshold and self._is_visually_hidden(page, text_rect):
                    findings.append(Finding(
                        detector=self.name,
                        severity=self.severity,
                        location=Location(
                            page=page_num + 1,
                            x=text_rect.x0,
                            y=text_rect.y0,
                            width=text_rect.width,
                            height=text_rect.height,
                        ),
                        content=f"Text covered by shape ({overlap*100:.0f}% overlap)",
                        context=text[:100] + ("..." if len(text) > 100 else ""),
                        explanation="Text appears to be covered by a targeted filled shape. This is a common technique to hide instructions."
                    ))
                    break

        
        return findings

    def _candidate_cover_shapes(self, page: fitz.Page, text_blocks: list[dict]) -> list[fitz.Rect]:
        """Keep only filled shapes that look like targeted covers, not layout panels."""
        cover_shapes = []

        for draw in page.get_drawings():
            if "f" not in draw.get("type", ""):
                continue

            draw_rect = draw["rect"]
            if draw_rect.width < 5 or draw_rect.height < 5:
                continue

            fill = draw.get("fill")
            if not self._is_near_page_background(fill):
                continue

            overlapped_spans = 0
            for tb in text_blocks:
                if self._calculate_overlap(tb["rect"], draw_rect) > self.cover_overlap_threshold:
                    overlapped_spans += 1
                    if overlapped_spans > self.max_cover_text_spans:
                        break

            if 0 < overlapped_spans <= self.max_cover_text_spans:
                cover_shapes.append(draw_rect)

        return cover_shapes

    def _is_near_page_background(self, fill: tuple | None, threshold: float = 0.08) -> bool:
        """Assume white page background and keep only near-background cover shapes."""
        if not fill or len(fill) != 3:
            return False
        return all(channel >= 1 - threshold for channel in fill)

    def _is_visually_hidden(
        self,
        page: fitz.Page,
        text_rect: fitz.Rect,
        darkness_threshold: float = 220.0,
        max_dark_ratio: float = 0.02,
    ) -> bool:
        """Render the covered region and confirm there are almost no visible dark glyph pixels."""
        try:
            pix = page.get_pixmap(clip=text_rect, matrix=fitz.Matrix(2, 2), alpha=False)
        except Exception:
            return True

        if pix.width == 0 or pix.height == 0:
            return True

        dark_pixels = 0
        total_pixels = 0
        for i in range(0, len(pix.samples), pix.n):
            r, g, b = pix.samples[i:i + 3]
            luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
            if luminance < darkness_threshold:
                dark_pixels += 1
            total_pixels += 1

        if total_pixels == 0:
            return True

        return (dark_pixels / total_pixels) <= max_dark_ratio
    
    def _calculate_overlap(self, rect1: fitz.Rect, rect2: fitz.Rect) -> float:
        """Calculate overlap ratio of rect1 with rect2."""
        intersection = rect1 & rect2  # Intersection
        
        if intersection.is_empty:
            return 0.0
        
        rect1_area = rect1.width * rect1.height
        if rect1_area == 0:
            return 0.0
        
        intersection_area = intersection.width * intersection.height
        return intersection_area / rect1_area
