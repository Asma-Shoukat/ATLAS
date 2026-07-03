import zipfile
import xml.etree.ElementTree as ET

pptx_path = "ATLAS_presentation.pptx"
with zipfile.ZipFile(pptx_path, 'r') as zip_ref:
    slide_files = [f for f in zip_ref.namelist() if f.startswith('ppt/slides/slide') and f.endswith('.xml')]
    
    targets = ["3.363", "3.847", "2.621", "2.926", "7.431", "4.652"]
    for sf in slide_files:
        xml_content = zip_ref.read(sf)
        root = ET.fromstring(xml_content)
        texts = [elem.text for elem in root.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}t') if elem.text]
        for t in texts:
            for target in targets:
                if target in t:
                    print(f"Found {target} in {sf}: '{t}'")
