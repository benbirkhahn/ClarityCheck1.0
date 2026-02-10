
import fitz

def test_extraction():
    doc = fitz.open("trap_gallery.pdf")
    page = doc[0]
    
    print("--- DICT Extraction ---")
    blocks_dict = page.get_text("dict")["blocks"]
    found_dict = False
    for b in blocks_dict:
        for l in b.get("lines", []):
            for s in l.get("spans", []):
                if "OFF SCREEN" in s["text"]:
                    print(f"FOUND in DICT: {s['text']} at {s['bbox']}")
                    found_dict = True
    if not found_dict:
        print("NOT FOUND in DICT")

    print("\n--- RAWDICT Extraction ---")
    blocks_raw = page.get_text("rawdict")["blocks"]
    found_raw = False
    for b in blocks_raw:
        for l in b.get("lines", []):
            for s in l.get("spans", []):
                # rawdict spans don't have 'text' key directly, need to check chars or if it's there
                # Wait, my inspect script accessed s['text'] in rawdict earlier and failed?
                # Step 2417 failed with KeyError: 'text'.
                # So rawdict spans DO NOT have 'text'.
                
                # I must reconstruct it.
                text = ""
                if "chars" in s:
                    text = "".join([c["c"] for c in s["chars"]])
                else:
                    text = s.get("text", "") # Fallback just in case
                
                if len(text) > 0:
                     print(f"DEBUG: Found '{text}' at {s['bbox']}")

                if "OFF SCREEN" in text:
                    print(f"FOUND in RAWDICT: {text} at {s['bbox']}")
                    found_raw = True
    if not found_raw:
        print("NOT FOUND in RAWDICT")

if __name__ == "__main__":
    test_extraction()
