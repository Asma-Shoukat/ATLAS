import zipfile
import xml.etree.ElementTree as ET

pptx_path = "ATLAS_presentation.pptx"
with zipfile.ZipFile(pptx_path, 'r') as zip_ref:
    slide_files = [f for f in zip_ref.namelist() if f.startswith('ppt/slides/slide') and f.endswith('.xml')]
    for sf in slide_files:
        xml_content = zip_ref.read(sf)
        root = ET.fromstring(xml_content)
        texts = [elem.text for elem in root.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}t') if elem.text]
        for t in texts:
            if "1,091" in t:
                print(f"Found in {sf}: '{t}'")
