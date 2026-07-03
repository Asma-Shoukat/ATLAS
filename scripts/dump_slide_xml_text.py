import zipfile
import xml.etree.ElementTree as ET
import sys

sys.stdout.reconfigure(encoding='utf-8')

pptx_path = "ATLAS_presentation.pptx"
with zipfile.ZipFile(pptx_path, 'r') as zip_ref:
    xml_content = zip_ref.read("ppt/slides/slide11.xml")
    root = ET.fromstring(xml_content)
    
    for idx, elem in enumerate(root.iter()):
        if elem.tag.endswith('t') and elem.text:
            # Print parent tag and text
            print(f"{idx}: <{elem.tag.split('}')[-1]}> {elem.text}")
