#!/usr/bin/env python3
"""
MusicXML Transposition Tool

Transposes a MusicXML file to a different key signature by modifying
all pitch elements and updating the key signature throughout the score.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class MusicXMLFile:
    file_path: str
    key_signature: Optional[int]
    time_signature: Optional[Tuple[int, int]]
    part_name: Optional[str]


# Chromatic scale mapping
NOTES = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
CHROMATIC = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Key signature to pitch mapping (fifths notation: -7 to +7)
KEY_SIGNATURES = {
    -7: ('C', 'flat', 7),   # Cb major
    -6: ('G', 'flat', 6),   # Gb major
    -5: ('D', 'flat', 5),   # Db major
    -4: ('A', 'flat', 4),   # Ab major
    -3: ('E', 'flat', 3),   # Eb major
    -2: ('B', 'flat', 2),   # Bb major
    -1: ('F', None, 1),     # F major
    0: ('C', None, 0),      # C major
    1: ('G', None, 1),      # G major
    2: ('D', None, 2),      # D major
    3: ('A', None, 3),      # A major
    4: ('E', None, 4),      # E major
    5: ('B', None, 5),      # B major
    6: ('F', 'sharp', 6),   # F# major
    7: ('C', 'sharp', 7),   # C# major
}


def note_to_chromatic(step: str, alter: int = 0) -> int:
    """Convert a note step and alteration to chromatic index (0-11)."""
    base_notes = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
    return (base_notes[step] + alter) % 12


def chromatic_to_note(chromatic_index: int, prefer_sharps: bool = True) -> Tuple[str, int]:
    """
    Convert chromatic index back to note step and alteration.

    Args:
        chromatic_index: 0-11 representing C through B
        prefer_sharps: If True, use sharps for black keys; otherwise use flats

    Returns:
        Tuple of (step, alter) where alter is -1 (flat), 0 (natural), or 1 (sharp)
    """
    # Natural notes mapping
    naturals = {0: 'C', 2: 'D', 4: 'E', 5: 'F', 7: 'G', 9: 'A', 11: 'B'}

    chromatic_index = chromatic_index % 12

    if chromatic_index in naturals:
        return (naturals[chromatic_index], 0)

    # Black keys - choose sharp or flat
    if prefer_sharps:
        # Use the note below and sharp it
        sharp_map = {1: ('C', 1), 3: ('D', 1), 6: ('F', 1), 8: ('G', 1), 10: ('A', 1)}
        return sharp_map[chromatic_index]
    else:
        # Use the note above and flat it
        flat_map = {1: ('D', -1), 3: ('E', -1), 6: ('G', -1), 8: ('A', -1), 10: ('B', -1)}
        return flat_map[chromatic_index]


def calculate_semitone_shift(from_key: int, to_key: int) -> int:
    """Calculate the semitone shift between two key signatures."""
    from_tonic = note_to_chromatic(KEY_SIGNATURES[from_key][0],
                                   1 if KEY_SIGNATURES[from_key][1] == 'sharp' else
                                   -1 if KEY_SIGNATURES[from_key][1] == 'flat' else 0)
    to_tonic = note_to_chromatic(KEY_SIGNATURES[to_key][0],
                                 1 if KEY_SIGNATURES[to_key][1] == 'sharp' else
                                 -1 if KEY_SIGNATURES[to_key][1] == 'flat' else 0)
    return (to_tonic - from_tonic) % 12


def transpose_musicxml(music_file: MusicXMLFile, target_key: int, output_path: Optional[str] = None) -> str:
    """
    Transpose a MusicXML file to a different key signature.

    Args:
        music_file: MusicXMLFile dataclass with source file info
        target_key: Target key signature in fifths notation (-7 to +7)
        output_path: Optional output file path. If None, creates {original}_transposed.xml

    Returns:
        Path to the transposed output file
    """
    if music_file.key_signature is None:
        raise ValueError("Source file must have a key signature to transpose")

    if target_key not in KEY_SIGNATURES:
        raise ValueError(f"Target key must be between -7 and +7, got {target_key}")

    # Calculate transposition interval
    semitone_shift = calculate_semitone_shift(music_file.key_signature, target_key)
    prefer_sharps = target_key >= 0  # Positive keys use sharps, negative use flats

    print(f"🎵 Transposing from {KEY_SIGNATURES[music_file.key_signature][0]} " +
          f"to {KEY_SIGNATURES[target_key][0]} ({semitone_shift} semitones)")

    # Parse the XML file
    tree = ET.parse(music_file.file_path)
    root = tree.getroot()

    # Detect namespace
    ns = {"": root.tag.split("}")[0].strip("{")} if "}" in root.tag else {}
    ns_prefix = "{" + ns[""] + "}" if ns else ""

    # Update all key signatures
    for key_elem in root.findall(f".//{ns_prefix}key", ns):
        fifths = key_elem.find(f"{ns_prefix}fifths", ns)
        if fifths is not None:
            fifths.text = str(target_key)

    # Transpose all pitches
    notes_transposed = 0
    for pitch_elem in root.findall(f".//{ns_prefix}pitch", ns):
        step = pitch_elem.find(f"{ns_prefix}step", ns)
        alter = pitch_elem.find(f"{ns_prefix}alter", ns)
        octave = pitch_elem.find(f"{ns_prefix}octave", ns)

        if step is not None and octave is not None:
            # Get current pitch info
            current_step = step.text
            current_alter = int(alter.text) if alter is not None and alter.text else 0
            current_octave = int(octave.text)

            # Convert to chromatic and transpose
            chromatic_value = note_to_chromatic(current_step, current_alter)
            new_chromatic = (chromatic_value + semitone_shift) % 12

            # Check if we crossed octave boundary
            octave_shift = (chromatic_value + semitone_shift) // 12
            new_octave = current_octave + octave_shift

            # Convert back to note notation
            new_step, new_alter = chromatic_to_note(new_chromatic, prefer_sharps)

            # Update XML
            step.text = new_step
            octave.text = str(new_octave)

            if new_alter == 0:
                # Remove alter element if natural
                if alter is not None:
                    pitch_elem.remove(alter)
            else:
                # Add or update alter element
                if alter is None:
                    alter = ET.SubElement(pitch_elem, f"{ns_prefix}alter")
                    # Insert after step
                    pitch_elem.remove(alter)
                    pitch_elem.insert(1, alter)
                alter.text = str(new_alter)

            notes_transposed += 1

    # Determine output path
    if output_path is None:
        original_path = Path(music_file.file_path)
        output_path = str(original_path.with_name(
            original_path.stem + f"_transposed_to_{KEY_SIGNATURES[target_key][0]}.xml"
        ))

    # Write transposed file
    tree.write(output_path, encoding="UTF-8", xml_declaration=True)

    print(f"✅ Transposed {notes_transposed} notes")
    print(f"✅ Output written to: {output_path}")

    return output_path


def main():
    """Example usage of the transposition tool."""
    # Example: transpose the parsed file
    from cli import parse_musicxml

    # Parse the original file
    xml_file = parse_musicxml("/Users/harikoornala/Code/Random Projects with Chat/omr app apptmet 2/sheet1_unzipped/sheet1.xml")

    print(f"Original key: {xml_file.key_signature} ({KEY_SIGNATURES.get(xml_file.key_signature, 'Unknown')})")
    print(f"Time signature: {xml_file.time_signature}")
    print(f"Part: {xml_file.part_name}")
    print()

    # Transpose to D major (2 sharps, fifths = 2)
    target_key = 2
    transposed_file = transpose_musicxml(xml_file, target_key)

    # Verify the transposition
    print("\nVerifying transposition...")
    transposed_xml = parse_musicxml(transposed_file)
    print(f"New key: {transposed_xml.key_signature} ({KEY_SIGNATURES.get(transposed_xml.key_signature, 'Unknown')})")


if __name__ == "__main__":
    main()
