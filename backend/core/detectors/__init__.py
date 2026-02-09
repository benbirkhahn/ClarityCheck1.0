"""Detection modules for ClarityCheck."""

from backend.core.detectors.base import BaseDetector
from backend.core.detectors.zero_width import ZeroWidthCharDetector
from backend.core.detectors.matching_color import MatchingColorDetector
from backend.core.detectors.off_screen import OffScreenTextDetector
from backend.core.detectors.tiny_text import TinyTextDetector
from backend.core.detectors.annotations import HiddenAnnotationDetector
from backend.core.detectors.metadata import MetadataDetector

__all__ = [
    "BaseDetector",
    "ZeroWidthCharDetector",
    "MatchingColorDetector",
    "OffScreenTextDetector",
    "TinyTextDetector",
    "HiddenAnnotationDetector",
    "MetadataDetector",
]
