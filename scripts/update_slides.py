import zipfile
import xml.etree.ElementTree as ET
import os

def update_slides():
    in_pptx = "ATLAS_presentation.pptx"
    out_pptx = "ATLAS_presentation_fixed.pptx"
    
    ET.register_namespace('a', 'http://schemas.openxmlformats.org/drawingml/2006/main')
    ET.register_namespace('p', 'http://schemas.openxmlformats.org/presentationml/2006/main')
    ET.register_namespace('r', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships')
    
    # Specific replacements targeting the CURRENT state of slide 11 (after partial replacement)
    replacements = {
        "ppt/slides/slide11.xml": [
            ("APPROVED | Confidence: -0.226 (Threshold: -1.5", "APPROVED | Confidence: 2.621 (Threshold: -2.0)"),
            ("A safe room is a room (preferably below ground in which people can take shelter from a tornado.", 
             'Answer: "...continuous security and compliance at the core of IBM Cloud\'s platform... find compliant-by-default infrastructure..." [ibmcld_12538-7-2121]'),
            # Clean up the rest of the file if needed
            ("[c8db6e06ff46669e-50302-52227]", "")
        ]
    }
    
    with zipfile.ZipFile(in_pptx, 'r') as zip_in:
        with zipfile.ZipFile(out_pptx, 'w') as zip_out:
            for item in zip_in.infolist():
                filename = item.filename
                
                if filename in replacements:
                    print(f"Modifying {filename}...")
                    xml_content = zip_in.read(filename)
                    root = ET.fromstring(xml_content)
                    
                    reps_done = 0
                    for elem in root.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}t'):
                        if elem.text:
                            original_text = elem.text
                            for search_text, rep_text in replacements[filename]:
                                if search_text in original_text:
                                    elem.text = original_text.replace(search_text, rep_text)
                                    if elem.text != original_text:
                                        reps_done += 1
                                        print(f"  Replaced: '{search_text[:40]}' -> '{rep_text[:40]}'")
                                        original_text = elem.text
                    
                    modified_xml = ET.tostring(root, encoding='utf-8')
                    zip_out.writestr(filename, modified_xml)
                    print(f"  Saved modified XML for {filename} (Total reps: {reps_done})")
                else:
                    zip_out.writestr(item, zip_in.read(item.filename))
                    
    os.replace(out_pptx, in_pptx)
    print("PPTX slides final update completed.")

if __name__ == "__main__":
    update_slides()
