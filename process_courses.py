import os
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

# --- CONFIGURATION ---
# The regex pattern to find the topic number. 
# It looks for 'p' followed by digits, then 'i', then captures the digits after 'i'.
FILENAME_PATTERN = re.compile(r"p\d+i(\d+)", re.IGNORECASE)

def get_sort_key(filename):
    """
    Extracts the topic number from the filename to use as a sort key.
    Returns the integer found after 'i', or 9999 if not found (puts it at the end).
    """
    match = FILENAME_PATTERN.search(filename)
    if match:
        return int(match.group(1))
    return 9999

def parse_xliff_content(xml_content):
    """
    Parses raw XML string content and returns a list of source text strings.
    """
    extracted_lines = []
    try:
        root = ET.fromstring(xml_content)
        
        # Handle namespaces (common in XLIFF 1.2)
        namespaces = {'xliff': 'urn:oasis:names:tc:xliff:document:1.2'}
        
        # Try finding with namespace first
        trans_units = root.findall('.//xliff:trans-unit', namespaces)
        
        # Fallback if no namespace or different version
        if not trans_units:
            trans_units = root.findall('.//trans-unit') + root.findall('.//unit')

        for unit in trans_units:
            # Find source tag
            source = unit.find('xliff:source', namespaces)
            if source is None:
                source = unit.find('source')
            
            if source is not None and source.text:
                text = " ".join(source.text.split()) # Clean whitespace
                if text:
                    extracted_lines.append(text)
                    
    except ET.ParseError:
        print("  -> Warning: distinct XML parse error.")
    except Exception as e:
        print(f"  -> Warning: {e}")
        
    return extracted_lines

def process_course_folder(course_path):
    """
    Scans a single course folder for .xlf, .xliff, and .zip files.
    Aggregates text, sorts by topic, and writes a Markdown file.
    """
    course_name = course_path.name
    print(f"Processing Course: {course_name}...")
    
    # Store tuples of (sort_key, filename, content_list)
    all_course_data = []

    # 1. Walk through the folder
    for root, dirs, files in os.walk(course_path):
        for file in files:
            file_path = Path(root) / file
            
            # Case A: Standard XLIFF file
            if file.lower().endswith(('.xlf', '.xliff')):
                sort_num = get_sort_key(file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        text_lines = parse_xliff_content(content)
                        if text_lines:
                            all_course_data.append((sort_num, file, text_lines))
                except Exception as e:
                    print(f"  Error reading {file}: {e}")

            # Case B: Zipped file (may contain XLIFFs)
            elif file.lower().endswith('.zip'):
                try:
                    with zipfile.ZipFile(file_path, 'r') as z:
                        for internal_filename in z.namelist():
                            if internal_filename.lower().endswith(('.xlf', '.xliff')):
                                # Use the internal filename for sorting logic
                                sort_num = get_sort_key(internal_filename)
                                
                                # Read XML from zip memory
                                with z.open(internal_filename) as zf:
                                    content = zf.read() # returns bytes
                                    text_lines = parse_xliff_content(content)
                                    if text_lines:
                                        all_course_data.append((sort_num, internal_filename, text_lines))
                except Exception as e:
                    print(f"  Error reading zip {file}: {e}")

    # 2. Sort the data based on the extracted 'i' number
    # Sorts by number first, then by filename alphabetically as a tie-breaker
    all_course_data.sort(key=lambda x: (x[0], x[1]))

    # 3. Write the consolidated Markdown file
    if all_course_data:
        output_filename = f"{course_name}_Summary.md"
        with open(output_filename, 'w', encoding='utf-8') as md:
            md.write(f"# Course Summary: {course_name}\n\n")
            
            for sort_key, filename, lines in all_course_data:
                # Add a header for the topic so the Chatbot knows where it came from
                md.write(f"## Topic: {filename} (Sequence: {sort_key})\n")
                for line in lines:
                    md.write(f"* {line}\n")
                md.write("\n---\n\n")
        
        print(f"  -> Created {output_filename} with {len(all_course_data)} topics.")
    else:
        print(f"  -> No XLIFF data found for {course_name}.")

def main():
    # Get current working directory
    root_dir = Path.cwd()
    
    # Iterate over immediate subdirectories (Assume each is a Course)
    for item in root_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'): # Skip hidden folders
            process_course_folder(item)

if __name__ == "__main__":
    main()
