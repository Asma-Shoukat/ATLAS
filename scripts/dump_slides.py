import zipfile
import xml.etree.ElementTree as ET

def dump_all_slides(pptx_path, out_txt_path):
    with zipfile.ZipFile(pptx_path, 'r') as zip_ref:
        # Get slide xml files and sort them numerically based on slide number
        slide_files = [f for f in zip_ref.namelist() if f.startswith('ppt/slides/slide') and f.endswith('.xml')]
        
        def extract_slide_num(filename):
            # Extract number from 'ppt/slides/slideX.xml'
            num_part = filename.replace('ppt/slides/slide', '').replace('.xml', '')
            try:
                return int(num_part)
            except ValueError:
                return 9999
                
        slide_files.sort(key=extract_slide_num)
        
        with open(out_txt_path, 'w', encoding='utf-8') as f:
            f.write(f"Total slides found: {len(slide_files)}\n")
            for slide_file in slide_files:
                f.write(f"\n=========================================\n")
                f.write(f"  {slide_file}\n")
                f.write(f"=========================================\n")
                xml_content = zip_ref.read(slide_file)
                root = ET.fromstring(xml_content)
                
                texts = []
                for elem in root.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}t'):
                    if elem.text:
                        texts.append(elem.text.strip())
                
                joined_text = " | ".join([t for t in texts if t])
                f.write(joined_text + "\n")
                print(f"Dumped {slide_file}")

if __name__ == "__main__":
    dump_all_slides("ATLAS_presentation.pptx", "scripts/slide_inspect.txt")
