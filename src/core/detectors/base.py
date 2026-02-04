"""Base detector interface for ClarityCheck."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import fitz  # PyMuPDF

if TYPE_CHECKING:
    from src.core.models import Finding, Severity


class BaseDetector(ABC):
    """Abstract base class for all accessibility detectors."""
    
    name: str = "BaseDetector"
    description: str = "Base detector description"
    severity: "Severity" = None
    enabled: bool = True
    
    @abstractmethod
    def detect(self, doc: fitz.Document) -> list["Finding"]:
        """Analyze a document and return a list of findings."""
        pass
    
    def remediate(self, doc: fitz.Document, finding: "Finding") -> fitz.Document:
        """Remove or fix a specific finding. Override in subclasses."""
        return doc
