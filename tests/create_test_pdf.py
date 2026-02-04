"""Create a test PDF containing zero-width characters."""

import fitz  # PyMuPDF


def create_test_pdf(output_path: str = "test_document.pdf"):
    """Create a PDF with various zero-width characters for testing."""
    
    doc = fitz.open()
    page = doc.new_page()
    
    # Sample text with embedded zero-width characters
    test_content = [
        ("Normal paragraph without issues:", 72, 72),
        ("This is a clean paragraph with no accessibility issues.", 72, 92),
        ("", 72, 120),
        ("Paragraph with Zero Width Space (ZWSP):", 72, 140),
        ("Hello\u200bWorld - The ZWSP is between Hello and World.", 72, 160),
        ("", 72, 188),
        ("Paragraph with Zero Width Non-Joiner (ZWNJ):", 72, 208),
        ("Test\u200cText - The ZWNJ is between Test and Text.", 72, 228),
        ("", 72, 256),
        ("Paragraph with Soft Hyphen:", 72, 276),
        ("Accessibility\u00adCompliance - Soft hyphen embedded.", 72, 296),
        ("", 72, 324),
        ("Paragraph with multiple issues:", 72, 344),
        ("This\u200bhas\u200cmultiple\u00adinvisible\u200dcharacters\ufeffhidden.", 72, 364),
        ("", 72, 392),
        ("Page 1 complete.", 72, 420),
    ]
    
    for text, x, y in test_content:
        if text:
            page.insert_text((x, y), text, fontsize=11)
    
    # Add a second page
    page2 = doc.new_page()
    page2_content = [
        ("Page 2 - More test content:", 72, 72),
        ("", 72, 100),
        ("Byte Order Mark (BOM) test:", 72, 120),
        ("Document\ufeffStart - BOM character present.", 72, 140),
        ("", 72, 168),
        ("Clean paragraph for comparison:", 72, 188),
        ("This paragraph has absolutely no hidden characters.", 72, 208),
    ]
    
    for text, x, y in page2_content:
        if text:
            page2.insert_text((x, y), text, fontsize=11)
    
    doc.save(output_path)
    doc.close()
    
    print(f"Created test PDF: {output_path}")
    print("Embedded characters:")
    print("  - Zero Width Space (U+200B)")
    print("  - Zero Width Non-Joiner (U+200C)")
    print("  - Zero Width Joiner (U+200D)")
    print("  - Soft Hyphen (U+00AD)")
    print("  - Byte Order Mark (U+FEFF)")


if __name__ == "__main__":
    create_test_pdf()
