import zipfile
import xml.etree.ElementTree as ET
import sys

def test_slides():
    sys.stdout.reconfigure(encoding='utf-8')
    slides_to_test = ["slide5", "slide9", "slide11", "slide12", "slide13"]
    with zipfile.ZipFile("ATLAS_presentation.pptx", 'r') as zip_ref:
        for slide in slides_to_test:
            print(f"\n=========================================\n  {slide}\n=========================================")
            xml_content = zip_ref.read(f"ppt/slides/{slide}.xml")
            root = ET.fromstring(xml_content)
            for idx, elem in enumerate(root.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}t')):
                print(f"{idx}: '{elem.text}'")

if __name__ == "__main__":
    test_slides()
