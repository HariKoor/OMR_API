#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path
import shutil
import tempfile

from dataclasses import dataclass
from typing import Tuple, Dict, Optional
import xml.etree.ElementTree as ET



import platform

# Auto-detect operating system and set appropriate binary paths
SYSTEM = platform.system()

if SYSTEM == "Darwin":  # macOS
    AUDIVERIS_BIN = os.environ.get(
        "AUDIVERIS_BIN",
        "/Applications/Audiveris.app/Contents/MacOS/Audiveris"
    )
    MUSESCORE_BIN = os.environ.get(
        "MUSESCORE_BIN",
        "/Applications/MuseScore 4.app/Contents/MacOS/mscore"
    )
elif SYSTEM == "Linux":  # Linux (for cloud deployment)
    AUDIVERIS_BIN = os.environ.get(
        "AUDIVERIS_BIN",
        "/audiveris-extract/bin/Audiveris"  # Built from source
    )
    MUSESCORE_BIN = os.environ.get(
        "MUSESCORE_BIN",
        "musescore3"  # Installed via apt-get
    )
elif SYSTEM == "Windows":
    AUDIVERIS_BIN = os.environ.get(
        "AUDIVERIS_BIN",
        "C:\\Program Files\\Audiveris\\Audiveris.exe"
    )
    MUSESCORE_BIN = os.environ.get(
        "MUSESCORE_BIN",
        "C:\\Program Files\\MuseScore 4\\bin\\MuseScore4.exe"
    )
else:
    raise RuntimeError(f"Unsupported operating system: {SYSTEM}")

def run_audiveris(input_file):
    """Run Audiveris CLI to convert a scanned score into MusicXML (MXL)."""
    input_path = Path(input_file).expanduser().resolve()

    if not input_path.exists():
        print(f"❌ File not found: {input_path}")
        sys.exit(1)

    # Create a temporary working directory for output
    temp_dir = Path(tempfile.mkdtemp(prefix="audiveris_convert_"))
    print(f"🔧 Working in: {temp_dir}")

    # Run Audiveris CLI in batch mode
    cmd = [
        AUDIVERIS_BIN,
        "-batch",
        "-export",
        "-output", str(temp_dir),
        str(input_path)
    ]

    print(f"🚀 Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        print("❌ Audiveris failed.")
        print(result.stderr or result.stdout)
        sys.exit(result.returncode)

    # Find resulting MXL or MusicXML
    outputs = list(temp_dir.rglob("*.mxl")) + list(temp_dir.rglob("*.musicxml")) + list(temp_dir.rglob("*.xml"))
    if not outputs:
        print("❌ No MusicXML/MXL file was generated.")
        sys.exit(2)

    # Copy first found output to same directory as input
    output_file = outputs[0]
    target_file = input_path.with_suffix(output_file.suffix)
    shutil.copy2(output_file, target_file)
    print(f"✅ Exported: {target_file}")

    # Clean up temp folder
    shutil.rmtree(temp_dir)


def convert_musicxml_to_pdf(musicxml_file, output_pdf=None):
    """
    Convert a MusicXML file to PDF using MuseScore.

    Args:
        musicxml_file: Path to the MusicXML file (.xml or .musicxml)
        output_pdf: Optional output PDF path. If None, uses same name as input with .pdf extension

    Returns:
        Path to the generated PDF file
    """
    input_path = Path(musicxml_file).expanduser().resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"MusicXML file not found: {input_path}")

    # Determine output path
    if output_pdf is None:
        output_path = input_path.with_suffix('.pdf')
    else:
        output_path = Path(output_pdf).expanduser().resolve()

    # Check if MuseScore is installed
    musescore_path = Path(MUSESCORE_BIN)
    if not musescore_path.exists():
        raise FileNotFoundError(
            f"MuseScore not found at {MUSESCORE_BIN}. "
            "Please install MuseScore 4 or update the MUSESCORE_BIN path."
        )

    # Run MuseScore conversion
    cmd = [
        MUSESCORE_BIN,
        "-o", str(output_path),
        str(input_path)
    ]

    print(f"🎼 Converting {input_path.name} to PDF...")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"MuseScore conversion failed: {result.stderr or result.stdout}")

    if not output_path.exists():
        raise RuntimeError("PDF file was not generated")

    print(f"✅ PDF created: {output_path}")
    return str(output_path)


import zipfile
from pathlib import Path

def unzip_mxl(mxl_path):
    """
    Unzips a .mxl (compressed MusicXML) file and returns the path
    to the extracted folder. Raises an error if the file is invalid.
    """
    mxl = Path(mxl_path).expanduser().resolve()
    if not mxl.exists():
        raise FileNotFoundError(f"File not found: {mxl}")

    if mxl.suffix.lower() != ".mxl":
        raise ValueError("Input file must have .mxl extension")

    out_dir = mxl.with_name(mxl.stem + "_unzipped")

    try:
        with zipfile.ZipFile(mxl, 'r') as zf:
            zf.extractall(out_dir)
    except zipfile.BadZipFile:
        raise RuntimeError("The .mxl file is not a valid ZIP archive")

    print(f"✅ Extracted to: {out_dir}")
    return out_dir


from dataclasses import dataclass


@dataclass
class MusicXMLFile:
    file_path: str
    key_signature: Optional[int]
    time_signature: Optional[Tuple[int, int]]
    part_name: Optional[str]


    
def parse_musicxml(file_path: str) -> MusicXMLFile:
    """Extract key metadata and structural information from a MusicXML file."""
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    # Namespace handling (MusicXML files may include one)
    ns = {"": root.tag.split("}")[0].strip("{")} if "}" in root.tag else {}

    def find_text(tag, parent=root):
        elem = parent.find(tag, ns)
        return elem.text.strip() if elem is not None and elem.text else None
 
    # Key and time signature (first measure)
    key_elem = root.find(".//key/fifths", ns)
    key_signature = int(key_elem.text) if key_elem is not None else None
    
    beats = root.find(".//time/beats", ns)
    beat_type = root.find(".//time/beat-type", ns)
    time_signature = (int(beats.text), int(beat_type.text)) if beats is not None and beat_type is not None else None
    
    # Part name
    part_name = find_text(".//part-name")
    
 
    

    
    return MusicXMLFile(
        file_path=file_path,
        key_signature=key_signature,
        time_signature=time_signature,
        part_name=part_name,
    )
    
from typing import Tuple, Dict, List, Optional
import xml.etree.ElementTree as ET


#run_audiveris("/Users/harikoornala/Code/Random Projects with Chat/omr app apptmet 2/sheet1.pdf")
#unzip_mxl("/Users/harikoornala/Code/Random Projects with Chat/omr app apptmet 2/sheet1.mxl")
xml_data = parse_musicxml("/Users/harikoornala/Code/Random Projects with Chat/omr app apptmet 2/sheet1_unzipped/sheet1.xml")
print(xml_data)
