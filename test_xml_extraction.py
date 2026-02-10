
import fitz

def test_xml():
    doc = fitz.open("trap_gallery.pdf")
    page = doc[0]
    
    xml = page.get_text("xml")
    if "OFF SCREEN" in xml:
        print("FOUND in XML!")
        # Print context
        idx = xml.find("OFF SCREEN")
        print(xml[max(0, idx-100):min(len(xml), idx+100)])
    else:
        print("NOT FOUND in XML")

if __name__ == "__main__":
    test_xml()
