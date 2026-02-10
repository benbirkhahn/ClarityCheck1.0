"""Detection engine that orchestrates all detectors."""

from pathlib import Path
import fitz  # PyMuPDF

from backend.core.models import Report, Finding
from backend.core.detectors.base import BaseDetector
from backend.core.detectors.zero_width import ZeroWidthCharDetector
from backend.core.detectors.matching_color import MatchingColorDetector
from backend.core.detectors.off_screen import OffScreenTextDetector
from backend.core.detectors.tiny_text import TinyTextDetector
from backend.core.detectors.annotations import HiddenAnnotationDetector
from backend.core.detectors.metadata import MetadataDetector
from backend.core.detectors.invisible_render import InvisibleRenderDetector
from backend.core.detectors.low_contrast import LowContrastDetector
from backend.core.detectors.suspicious_spacing import SuspiciousSpacingDetector
from backend.core.detectors.layered_text import LayeredTextDetector
from backend.core.detectors.visual_mismatch import VisualMismatchDetector


class DetectionEngine:
    """Main engine for running accessibility detectors on documents."""
    
    def __init__(self):
        self.detectors: list[BaseDetector] = []
        self._register_default_detectors()
    
    def _register_default_detectors(self):
        """Register all built-in detectors."""
        self.register(ZeroWidthCharDetector())
        self.register(MatchingColorDetector())
        self.register(OffScreenTextDetector())
        self.register(TinyTextDetector())
        self.register(HiddenAnnotationDetector())
        self.register(MetadataDetector())
        self.register(InvisibleRenderDetector())
        self.register(LowContrastDetector())
        self.register(SuspiciousSpacingDetector())
        self.register(LayeredTextDetector())
        self.register(VisualMismatchDetector())
    
    def register(self, detector: BaseDetector):
        """Register a detector with the engine."""
        self.detectors.append(detector)
    
    def analyze(self, pdf_path: str | Path) -> Report:
        """Analyze a PDF file and return a report."""
        pdf_path = Path(pdf_path)
        doc = fitz.open(pdf_path)
        
        try:
            findings = self._run_detectors(doc)
            summary = {}
            for f in findings:
                summary[f.detector] = summary.get(f.detector, 0) + 1
            
            return Report(
                job_id="",
                filename=pdf_path.name,
                total_pages=len(doc),
                findings=findings,
                summary=summary,
            )
        finally:
            doc.close()
    
    def analyze_bytes(self, pdf_bytes: bytes, filename: str) -> Report:
        """Analyze PDF from bytes (for uploads)."""
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        try:
            findings = self._run_detectors(doc)
            summary = {}
            for f in findings:
                summary[f.detector] = summary.get(f.detector, 0) + 1
            
            return Report(
                job_id="",
                filename=filename,
                total_pages=len(doc),
                findings=findings,
                summary=summary,
            )
        finally:
            doc.close()
    
    def _run_detectors(self, doc: fitz.Document) -> list[Finding]:
        """Run all enabled detectors on the document."""
        findings = []
        for detector in self.detectors:
            if detector.enabled:
                try:
                    findings.extend(detector.detect(doc))
                except Exception as e:
                    print(f"Error in {detector.name}: {e}")
        
        findings.sort(key=lambda f: (f.location.page, f.location.y or 0))
        return findings


engine = DetectionEngine()
