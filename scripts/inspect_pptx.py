import zipfile
import xml.etree.ElementTree as ET
import sys

def inspect_pptx(pptx_path):
    sys.stdout.reconfigure(encoding='utf-8')
    
    with zipfile.ZipFile(pptx_path, 'r') as zip_ref:
        slide_files = sorted([f for f in zip_ref.namelist() if f.startswith('ppt/slides/slide') and f.endswith('.xml')])
        
        print(f"Total slides found: {len(slide_files)}")
        for slide_file in slide_files:
            print(f"\n--- {slide_file} ---")
            xml_content = zip_ref.read(slide_file)
            root = ET.fromstring(xml_content)
            
            texts = []
            for elem in root.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}t'):
                if elem.text:
                    texts.append(elem.text.strip())
            
            # Print slide text content
            print(" | ".join([t for t in texts if t]))

if __name__ == "__main__":
    inspect_pptx("ATLAS_presentation.pptx")
