"""Unit tests for ZeroWidthCharDetector."""

import pytest
from unittest.mock import MagicMock, patch


class TestZeroWidthCharDetector:
    """Test the zero-width character detection logic."""
    
    def test_detects_zwsp(self):
        """Test detection of Zero Width Space."""
        from backend.core.detectors.zero_width import ZeroWidthCharDetector, ZERO_WIDTH_CHARS
        
        detector = ZeroWidthCharDetector()
        
        # Create mock document with ZWSP
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=1)
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Hello\u200bWorld"  # ZWSP between words
        mock_page.get_text.side_effect = lambda fmt=None: (
            "Hello\u200bWorld" if fmt is None else 
            {"blocks": [{"type": 0, "lines": [{"spans": [{"text": "Hello\u200bWorld", "bbox": (0, 0, 100, 20)}]}]}]}
        )
        mock_doc.__getitem__ = MagicMock(return_value=mock_page)
        
        findings = detector.detect(mock_doc)
        
        assert len(findings) == 1
        assert "Zero Width Space" in findings[0].content
        assert findings[0].severity.value == "high"
    
    def test_detects_multiple_chars(self):
        """Test detection of multiple zero-width characters."""
        from backend.core.detectors.zero_width import ZeroWidthCharDetector
        
        detector = ZeroWidthCharDetector()
        
        # Text with multiple invisible chars
        text_with_issues = "Test\u200bOne\u200cTwo\u00adThree"
        
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=1)
        mock_page = MagicMock()
        mock_page.get_text.side_effect = lambda fmt=None: (
            text_with_issues if fmt is None else 
            {"blocks": [{"type": 0, "lines": [{"spans": [{"text": text_with_issues, "bbox": (0, 0, 100, 20)}]}]}]}
        )
        mock_doc.__getitem__ = MagicMock(return_value=mock_page)
        
        findings = detector.detect(mock_doc)
        
        assert len(findings) == 3  # ZWSP, ZWNJ, Soft Hyphen
    
    def test_clean_text_no_findings(self):
        """Test that clean text produces no findings."""
        from backend.core.detectors.zero_width import ZeroWidthCharDetector
        
        detector = ZeroWidthCharDetector()
        
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=1)
        mock_page = MagicMock()
        mock_page.get_text.side_effect = lambda fmt=None: (
            "This is clean text with no issues." if fmt is None else 
            {"blocks": [{"type": 0, "lines": [{"spans": [{"text": "This is clean text with no issues.", "bbox": (0, 0, 100, 20)}]}]}]}
        )
        mock_doc.__getitem__ = MagicMock(return_value=mock_page)
        
        findings = detector.detect(mock_doc)
        
        assert len(findings) == 0
    
    def test_context_extraction(self):
        """Test that context is properly extracted around findings."""
        from backend.core.detectors.zero_width import ZeroWidthCharDetector
        
        detector = ZeroWidthCharDetector(context_chars=10)
        
        text = "Some prefix Hello\u200bWorld some suffix"
        
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=1)
        mock_page = MagicMock()
        mock_page.get_text.side_effect = lambda fmt=None: (
            text if fmt is None else 
            {"blocks": [{"type": 0, "lines": [{"spans": [{"text": text, "bbox": (0, 0, 100, 20)}]}]}]}
        )
        mock_doc.__getitem__ = MagicMock(return_value=mock_page)
        
        findings = detector.detect(mock_doc)
        
        assert len(findings) == 1
        # Context should include surrounding text
        assert "Hello" in findings[0].context
        assert "World" in findings[0].context


class TestZeroWidthCharList:
    """Test the character detection list."""
    
    def test_all_chars_are_invisible(self):
        """Verify all listed chars are actually zero-width/invisible."""
        from backend.core.detectors.zero_width import ZERO_WIDTH_CHARS
        
        # All these should be characters that don't render visibly
        for char, name in ZERO_WIDTH_CHARS.items():
            # Check it's a single character
            assert len(char) == 1, f"{name} should be a single character"
            # Check the unicode category suggests it's a format/control char
            import unicodedata
            category = unicodedata.category(char)
            assert category in ('Cf', 'Mn', 'Lo', 'Zs'), \
                f"{name} (U+{ord(char):04X}) has unexpected category {category}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
