import zipfile
import xml.etree.ElementTree as ET
import sys

sys.stdout.reconfigure(encoding='utf-8')

pptx_path = "ATLAS_presentation.pptx"
with zipfile.ZipFile(pptx_path, 'r') as zip_ref:
    xml_content = zip_ref.read("ppt/slides/slide12.xml")
    root = ET.fromstring(xml_content)
    
    for elem in root.iter('{http://schemas.openxmlformats.org/presentationml/2006/main}sp'):
        texts = [t.text for t in elem.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}t') if t.text]
        if any("NAV" in t or "Market" in t or "4.652" in t for t in texts):
            print("--- SHAPE ---")
            for p in elem.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}p'):
                p_text = "".join(t.text for t in p.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}t') if t.text)
                print(f"  P: {p_text}")
                for r in p.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}r'):
                    r_text = "".join(t.text for t in r.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}t') if t.text)
                    print(f"    R: {r_text}")
