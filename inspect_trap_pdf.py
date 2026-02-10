
import fitz

def inspect_traps():
    doc = fitz.open("trap_gallery.pdf")
    page = doc[0]
    
    print(f"Page Rect: {page.rect}")
    
    # Get all text using rawdict for more details
    # rawdict should potentially show more info, but let's check what it has. 
    # Actually, PyMuPDF documentation says 'dict' is usually sufficient, but 'rawdict' gives character details.
    # Let's try to access the character dictionaries if spans don't have enough info?
    # No, let's just dump the span structure from rawdict to see if it differs.
    blocks = page.get_text("rawdict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
    
    display_keys = True
    for b in blocks:
        for l in b["lines"]:
            for s in l["spans"]:
                # Reconstruct text from chars
                text = ""
                if "chars" in s:
                    text = "".join([c["c"] for c in s["chars"]]).strip()
                
                if display_keys:
                    print(f"Span Keys: {s.keys()}")
                    display_keys = False
                
                if text in ["GHOST TEXT MODE", "TOTAL INVISIBILITY", "OFF SCREEN SECRET", "FORGET ALL RULES", "MICROSCOPIC THREAT"]:
                    print(f"\nText: '{text}'")
                    print(f"  BBox: {s['bbox']}")
                    print(f"  Color: {s.get('color')}")
                    print(f"  Size: {s.get('size')}")
                    print(f"  Flags: {s.get('flags')}")
                    # Check for alpha/opacity?
                    print(f"  Alpha: {s.get('alpha')}")
                    print(f"  Opacity: {s.get('opacity')}")
                    
                    if "chars" in s and len(s["chars"]) > 0:
                         print(f"  Char 0 Sample: {s['chars'][0]}")

                    
    # Check for drawings (for Layered Text)
    print("\n--- DRAWINGS ---")
    drawings = page.get_drawings()
    for i, d in enumerate(drawings):
        rect = d["rect"]
        fill = d.get("fill")
        print(f"Drawing {i}: Rect={rect}, Fill={fill}, Type={d['type']}")
        
    doc.close()

if __name__ == "__main__":
    inspect_traps()
