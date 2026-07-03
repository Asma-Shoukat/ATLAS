import zipfile
import xml.etree.ElementTree as ET
import sys

sys.stdout.reconfigure(encoding='utf-8')

pptx_path = "ATLAS_presentation.pptx"
with zipfile.ZipFile(pptx_path, 'r') as zip_ref:
    xml_content = zip_ref.read("ppt/slides/slide11.xml")
    root = ET.fromstring(xml_content)
    
    # We want to trace elements around the text "3.363" and the bullets "▪"
    # Let's find all text elements and print their ancestor tags to see their structure
    for elem in root.iter('{http://schemas.openxmlformats.org/presentationml/2006/main}sp'):
        # Check if this shape contains the text we are interested in
        texts = [t.text for t in elem.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}t') if t.text]
        if any("3.363" in t or "Explain" in t or "2.621" in t for t in texts):
            print("--- SHAPE ---")
            # Let's print the paragraphs in this shape
            for p in elem.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}p'):
                p_text = "".join(t.text for t in p.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}t') if t.text)
                print(f"  P: {p_text}")
                # Print individual runs if needed
                for r in p.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}r'):
                    r_text = "".join(t.text for t in r.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}t') if t.text)
                    print(f"    R: {r_text}")
