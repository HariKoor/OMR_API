#!/usr/bin/env python3
"""
FastAPI Backend for Music Transposition App

Provides REST API endpoints for:
- PDF upload and conversion to MusicXML
- Music transposition
- PDF generation from transposed MusicXML
"""

import sys
import os
from pathlib import Path
import uuid
import shutil
from typing import Optional
import tempfile

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path to import cli and transpose modules
sys.path.append(str(Path(__file__).parent.parent))

from cli import run_audiveris, unzip_mxl, parse_musicxml, convert_musicxml_to_pdf
from transpose import transpose_musicxml, KEY_SIGNATURES

app = FastAPI(
    title="Music Transposer API",
    description="API for transposing sheet music from PDF files",
    version="1.0.0"
)

# Enable CORS for Flutter web app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Flutter app domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session storage directory
SESSIONS_DIR = Path(tempfile.gettempdir()) / "music_transposer_sessions"
SESSIONS_DIR.mkdir(exist_ok=True)

# Session data storage (in production, use Redis or database)
sessions = {}


def get_session_dir(session_id: str) -> Path:
    """Get or create session directory."""
    session_dir = SESSIONS_DIR / session_id
    session_dir.mkdir(exist_ok=True)
    return session_dir


@app.get("/")
async def root():
    """API root - health check."""
    return {
        "status": "ok",
        "message": "Music Transposer API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "POST /api/upload-pdf",
            "transpose": "POST /api/transpose",
            "convert": "POST /api/convert-to-pdf",
            "health": "GET /api/health"
        }
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}


@app.post("/api/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file and convert it to MusicXML using Audiveris.

    Returns:
        session_id: Unique session identifier
        metadata: Key signature, time signature, part name
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    # Create session
    session_id = str(uuid.uuid4())
    session_dir = get_session_dir(session_id)

    try:
        # Save uploaded PDF
        pdf_path = session_dir / "input.pdf"
        with open(pdf_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Run Audiveris conversion
        run_audiveris(str(pdf_path))

        # Find generated MXL file
        mxl_path = pdf_path.with_suffix('.mxl')
        if not mxl_path.exists():
            raise HTTPException(
                status_code=500,
                detail="Audiveris failed to generate MusicXML file"
            )

        # Unzip MXL
        unzipped_dir = unzip_mxl(str(mxl_path))

        # Find XML file inside
        xml_files = list(Path(unzipped_dir).rglob("*.xml"))
        if not xml_files:
            raise HTTPException(
                status_code=500,
                detail="No MusicXML file found in archive"
            )

        xml_path = xml_files[0]

        # Parse MusicXML
        music_data = parse_musicxml(str(xml_path))

        # Store session data
        sessions[session_id] = {
            "pdf_path": str(pdf_path),
            "mxl_path": str(mxl_path),
            "xml_path": str(xml_path),
            "original_key": music_data.key_signature,
            "time_signature": music_data.time_signature,
            "part_name": music_data.part_name
        }

        # Format key signature for response
        if music_data.key_signature is not None:
            key_info = KEY_SIGNATURES[music_data.key_signature]
            key_name = key_info[0]
            accidental = key_info[1]
            count = key_info[2]

            if accidental == 'sharp':
                key_display = f"{key_name} major ({count} sharps)"
            elif accidental == 'flat':
                key_display = f"{key_name} major ({count} flats)"
            else:
                key_display = f"{key_name} major"
        else:
            key_display = "Unknown"

        return {
            "session_id": session_id,
            "metadata": {
                "key_signature": music_data.key_signature,
                "key_display": key_display,
                "time_signature": music_data.time_signature,
                "part_name": music_data.part_name
            }
        }

    except Exception as e:
        # Clean up on error
        if session_id in sessions:
            del sessions[session_id]
        shutil.rmtree(session_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/transpose")
async def transpose(session_id: str = Form(...), target_key: int = Form(...)):
    """
    Transpose music to a different key.

    Args:
        session_id: Session identifier from upload
        target_key: Target key signature (-7 to +7 in fifths notation)

    Returns:
        transposed_path: Path to transposed MusicXML file
    """
    # Validate session
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    # Validate target key
    if target_key not in KEY_SIGNATURES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid target key. Must be between -7 and +7, got {target_key}"
        )

    session_data = sessions[session_id]

    try:
        # Parse original XML
        from cli import MusicXMLFile
        music_data = MusicXMLFile(
            file_path=session_data["xml_path"],
            key_signature=session_data["original_key"],
            time_signature=session_data["time_signature"],
            part_name=session_data["part_name"]
        )

        # Transpose
        transposed_path = transpose_musicxml(music_data, target_key)

        # Store transposed path in session
        sessions[session_id]["transposed_path"] = transposed_path

        # Format target key for response
        key_info = KEY_SIGNATURES[target_key]
        key_name = key_info[0]
        accidental = key_info[1]
        count = key_info[2]

        if accidental == 'sharp':
            key_display = f"{key_name} major ({count} sharps)"
        elif accidental == 'flat':
            key_display = f"{key_name} major ({count} flats)"
        else:
            key_display = f"{key_name} major"

        return {
            "success": True,
            "session_id": session_id,
            "transposed_key": target_key,
            "transposed_key_display": key_display,
            "message": f"Successfully transposed to {key_display}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/convert-to-pdf")
async def convert_to_pdf(session_id: str = Form(...)):
    """
    Convert transposed MusicXML to PDF using MuseScore.

    Args:
        session_id: Session identifier

    Returns:
        PDF file download
    """
    # Validate session
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session_data = sessions[session_id]

    # Check if file has been transposed
    if "transposed_path" not in session_data:
        raise HTTPException(
            status_code=400,
            detail="No transposed file available. Please transpose first."
        )

    try:
        transposed_xml = session_data["transposed_path"]

        # Convert to PDF
        pdf_path = convert_musicxml_to_pdf(transposed_xml)

        # Return PDF file
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"transposed_{Path(pdf_path).name}"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/keys")
async def get_available_keys():
    """Get list of all available keys for transposition."""
    keys = []
    for fifths in range(-7, 8):
        key_info = KEY_SIGNATURES[fifths]
        key_name = key_info[0]
        accidental = key_info[1]
        count = key_info[2]

        if accidental == 'sharp':
            display = f"{key_name} major ({count} sharps)"
        elif accidental == 'flat':
            display = f"{key_name} major ({count} flats)"
        else:
            display = f"{key_name} major"

        keys.append({
            "fifths": fifths,
            "display": display,
            "name": key_name
        })

    return {"keys": keys}


# Cleanup old sessions (run periodically in production)
@app.on_event("startup")
async def cleanup_old_sessions():
    """Clean up sessions older than 1 hour."""
    import time
    current_time = time.time()
    for session_dir in SESSIONS_DIR.iterdir():
        if session_dir.is_dir():
            # Check if older than 1 hour
            dir_age = current_time - session_dir.stat().st_mtime
            if dir_age > 3600:  # 1 hour in seconds
                shutil.rmtree(session_dir, ignore_errors=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
