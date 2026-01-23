import os
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import sys
import time

# --- CONFIGURATION ---
FILENAME_PATTERN = re.compile(r"p\d+i(\d+)", re.IGNORECASE)

def get_base_path():
    """
    Determines the folder where the EXE is running.
    """
    if getattr(sys, 'frozen', False):
        # If running as an EXE
        return Path(sys.executable).parent
    else:
        # If running as a script
        return Path(__file__).parent

def get_sort_key(filename):
    match = FILENAME_PATTERN.search(filename)
    if match:
        return int(match.group(1))
    return 9999

def parse_xliff_content(xml_content):
    extracted_lines = []
    try:
        root = ET.fromstring(xml_content)
        namespaces = {'xliff': 'urn:oasis:names:tc:xliff:document:1.2'}
        trans_units = root.findall('.//xliff:trans-unit', namespaces)
        if not trans_units:
            trans_units = root.findall('.//trans-unit') + root.findall('.//unit')

        for unit in trans_units:
            source = unit.find('xliff:source', namespaces)
            if source is None:
                source = unit.find('source')
            if source is not None and source.text:
                text = " ".join(source.text.split())
                if text:
                    extracted_lines.append(text)
    except Exception:
        pass 
    return extracted_lines

def process_course_folder(course_path):
    course_name = course_path.name
    print(f"Checking folder: {course_name}...")
    
    all_course_data = []

    for root, dirs, files in os.walk(course_path):
        for file in files:
            file_path = Path(root) / file
            
            if file.lower().endswith(('.xlf', '.xliff')):
                sort_num = get_sort_key(file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text_lines = parse_xliff_content(f.read())
                        if text_lines:
                            all_course_data.append((sort_num, file, text_lines))
                except Exception as e:
                    print(f"  Error reading {file}: {e}")

            elif file.lower().endswith('.zip'):
                try:
                    with zipfile.ZipFile(file_path, 'r') as z:
                        for internal_filename in z.namelist():
                            if internal_filename.lower().endswith(('.xlf', '.xliff')):
                                sort_num = get_sort_key(internal_filename)
                                with z.open(internal_filename) as zf:
                                    text_lines = parse_xliff_content(zf.read())
                                    if text_lines:
                                        all_course_data.append((sort_num, internal_filename, text_lines))
                except Exception as e:
                    print(f"  Error reading zip {file}: {e}")

    all_course_data.sort(key=lambda x: (x[0], x[1]))

    if all_course_data:
        output_filename = get_base_path() / f"{course_name}_Summary.md"
        with open(output_filename, 'w', encoding='utf-8') as md:
            md.write(f"# Course Summary: {course_name}\n\n")
            for sort_key, filename, lines in all_course_data:
                md.write(f"## Topic: {filename} (Sequence: {sort_key})\n")
                for line in lines:
                    md.write(f"* {line}\n")
                md.write("\n---\n\n")
        print(f"  -> SUCCESS: Created {output_filename.name}")
    else:
        print(f"  -> No XLIFF data found.")

def main():
    root_dir = get_base_path()
    print(f"--- Course Content Extractor ---")
    print(f"Scanning folder: {root_dir}\n")
    
    count = 0
    for item in root_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            process_course_folder(item)
            count += 1
            
    print(f"\nScan complete. Processed {count} folders.")
    print("You can close this window now.")
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
