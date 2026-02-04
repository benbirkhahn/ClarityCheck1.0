"""Detection modules for ClarityCheck."""

from src.core.detectors.base import BaseDetector
from src.core.detectors.zero_width import ZeroWidthCharDetector
from src.core.detectors.matching_color import MatchingColorDetector
from src.core.detectors.off_screen import OffScreenTextDetector
from src.core.detectors.tiny_text import TinyTextDetector
from src.core.detectors.annotations import HiddenAnnotationDetector
from src.core.detectors.metadata import MetadataDetector

__all__ = [
    "BaseDetector",
    "ZeroWidthCharDetector",
    "MatchingColorDetector",
    "OffScreenTextDetector",
    "TinyTextDetector",
    "HiddenAnnotationDetector",
    "MetadataDetector",
]
