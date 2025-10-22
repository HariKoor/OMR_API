# Music Transposer API

FastAPI backend for the Music Transposer application. Provides REST endpoints for converting PDF sheet music to MusicXML, transposing to different keys, and generating PDF output.

## Features

- 🎵 **PDF to MusicXML Conversion** using Audiveris
- 🎼 **Music Transposition** to any major key (-7 flats to +7 sharps)
- 📄 **PDF Generation** from transposed MusicXML using MuseScore
- 🔄 **Session Management** for multi-step workflows
- 📚 **Auto-generated API Documentation** via FastAPI
- 🌐 **CORS Enabled** for cross-origin requests (Flutter web/mobile apps)

---

## Prerequisites

### System Requirements
- Python 3.11+
- Audiveris 5.7.1+ installed at `/Applications/Audiveris.app/Contents/MacOS/Audiveris`
- MuseScore 4 installed at `/Applications/MuseScore 4.app/Contents/MacOS/mscore`

### Python Dependencies
See `requirements.txt`:
- FastAPI
- Uvicorn
- python-multipart (for file uploads)
- aiofiles (for async file operations)

---

## Installation

### 1. Install Dependencies

```bash
cd api
pip install -r requirements.txt
```

### 2. Verify Audiveris and MuseScore

```bash
# Check Audiveris
/Applications/Audiveris.app/Contents/MacOS/Audiveris --help

# Check MuseScore
/Applications/MuseScore\ 4.app/Contents/MacOS/mscore --help
```

If not installed:
- **Audiveris**: Download from https://github.com/Audiveris/audiveris/releases
- **MuseScore**: Download from https://musescore.org/

---

## Running the Server

### Development Mode (Auto-reload on code changes)

```bash
# From project root
python -m uvicorn api.main:app --reload --port 8000

# Or from api directory
cd api
uvicorn main:app --reload --port 8000
```

### Production Mode

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Server will start at: **http://localhost:8000**

---

## API Endpoints

### Base URL
```
http://localhost:8000
```

### 1. Health Check
```http
GET /api/health
```

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

---

### 2. Upload PDF
```http
POST /api/upload-pdf
Content-Type: multipart/form-data
```

**Parameters:**
- `file` (file): PDF file to upload

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "metadata": {
    "key_signature": -3,
    "key_display": "Eb major (3 flats)",
    "time_signature": [4, 4],
    "part_name": "Piano"
  }
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/upload-pdf" \
  -F "file=@sheet1.pdf"
```

---

### 3. Transpose Music
```http
POST /api/transpose
Content-Type: application/x-www-form-urlencoded
```

**Parameters:**
- `session_id` (string): Session ID from upload response
- `target_key` (integer): Target key signature (-7 to +7 in fifths notation)

**Key Signature Values:**
- `-7` = Cb major (7 flats)
- `-3` = Eb major (3 flats)
- `0` = C major (no sharps/flats)
- `2` = D major (2 sharps)
- `7` = C# major (7 sharps)

**Response:**
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "transposed_key": 2,
  "transposed_key_display": "D major (2 sharps)",
  "message": "Successfully transposed to D major (2 sharps)"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/transpose" \
  -d "session_id=550e8400-e29b-41d4-a716-446655440000" \
  -d "target_key=2"
```

---

### 4. Convert to PDF
```http
POST /api/convert-to-pdf
Content-Type: application/x-www-form-urlencoded
```

**Parameters:**
- `session_id` (string): Session ID from upload response

**Response:**
- PDF file download

**Example:**
```bash
curl -X POST "http://localhost:8000/api/convert-to-pdf" \
  -d "session_id=550e8400-e29b-41d4-a716-446655440000" \
  -o transposed.pdf
```

---

### 5. Get Available Keys
```http
GET /api/keys
```

**Response:**
```json
{
  "keys": [
    {
      "fifths": -7,
      "display": "Cb major (7 flats)",
      "name": "Cb"
    },
    {
      "fifths": 0,
      "display": "C major",
      "name": "C"
    },
    {
      "fifths": 2,
      "display": "D major (2 sharps)",
      "name": "D"
    }
    // ... all keys from -7 to +7
  ]
}
```

---

## Interactive API Documentation

FastAPI provides automatic interactive documentation:

### Swagger UI (Recommended)
**http://localhost:8000/docs**

- Interactive interface
- Try endpoints directly in browser
- See request/response schemas
- Test file uploads

### ReDoc (Alternative)
**http://localhost:8000/redoc**

- Clean, readable documentation
- Better for sharing with team

---

## Usage Workflow

### Complete Example

```bash
# 1. Upload PDF
RESPONSE=$(curl -X POST "http://localhost:8000/api/upload-pdf" \
  -F "file=@sheet1.pdf")

# Extract session_id from response (using jq)
SESSION_ID=$(echo $RESPONSE | jq -r '.session_id')
echo "Session ID: $SESSION_ID"

# 2. Transpose to D major (2 sharps)
curl -X POST "http://localhost:8000/api/transpose" \
  -d "session_id=$SESSION_ID" \
  -d "target_key=2"

# 3. Download transposed PDF
curl -X POST "http://localhost:8000/api/convert-to-pdf" \
  -d "session_id=$SESSION_ID" \
  -o transposed_output.pdf

echo "Done! Check transposed_output.pdf"
```

---

## Architecture

### File Flow
```
1. User uploads PDF
   ↓
2. Audiveris converts PDF → MusicXML (.mxl)
   ↓
3. Unzip .mxl → Extract .xml
   ↓
4. Parse MusicXML → Extract metadata
   ↓
5. Store in session (temp directory)
   ↓
6. User requests transposition
   ↓
7. Run transpose.py logic
   ↓
8. Save transposed MusicXML
   ↓
9. User requests PDF
   ↓
10. MuseScore renders MusicXML → PDF
   ↓
11. Return PDF to user
```

### Session Storage
- Sessions stored in `/tmp/music_transposer_sessions/`
- Each session has unique UUID
- Auto-cleanup after 1 hour (on server startup)
- In production: Use Redis or database for session storage

---

## Error Handling

### Common Errors

**400 Bad Request**
```json
{
  "detail": "File must be a PDF"
}
```

**404 Not Found**
```json
{
  "detail": "Session not found"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Audiveris failed to generate MusicXML file"
}
```

---

## Configuration

### Environment Variables

Create `.env` file (optional):

```bash
# Server
HOST=0.0.0.0
PORT=8000

# Paths (override defaults)
AUDIVERIS_BIN=/Applications/Audiveris.app/Contents/MacOS/Audiveris
MUSESCORE_BIN=/Applications/MuseScore 4.app/Contents/MacOS/mscore

# Session cleanup
SESSION_MAX_AGE=3600  # 1 hour in seconds
```

### CORS Configuration

By default, CORS allows all origins (`*`). For production, specify allowed domains:

```python
# In api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-flutter-app.com",
        "https://your-domain.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Deployment

### Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    musescore \
    wget \
    unzip

# Install Audiveris
RUN wget https://github.com/Audiveris/audiveris/releases/download/5.3/audiveris.zip \
    && unzip audiveris.zip -d /opt/audiveris

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t music-transposer-api .
docker run -p 8000:8000 music-transposer-api
```

### Railway / Render

1. Push code to GitHub
2. Connect to Railway/Render
3. Set environment variables
4. Deploy!

See [ROADMAP.md](../ROADMAP.md) for detailed deployment instructions.

---

## Testing

### Manual Testing with curl

See examples above in "Usage Workflow"

### Automated Testing (Future)

```bash
# Install pytest
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

---

## Development

### Project Structure

```
api/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
└── README.md           # This file

../
├── cli.py              # Audiveris & MuseScore integration
├── transpose.py        # Transposition logic
└── CLAUDE.md          # Project documentation
```

### Adding New Endpoints

1. Define route in `main.py`:
```python
@app.post("/api/new-endpoint")
async def new_endpoint(param: str):
    return {"result": "success"}
```

2. Restart server (auto-reloads in dev mode)

3. Check docs at http://localhost:8000/docs

---

## Troubleshooting

### Server won't start

**Check port availability:**
```bash
lsof -i :8000
```

**Use different port:**
```bash
uvicorn api.main:app --port 8001
```

### Audiveris not found

**Verify installation:**
```bash
ls -la /Applications/Audiveris.app/Contents/MacOS/Audiveris
```

**Update path in code:**
Edit `cli.py` and change `AUDIVERIS_BIN` constant

### MuseScore not found

**Verify installation:**
```bash
ls -la "/Applications/MuseScore 4.app/Contents/MacOS/mscore"
```

**Update path in code:**
Edit `cli.py` and change `MUSESCORE_BIN` constant

### File upload fails

**Check file size limits:**
FastAPI defaults to 100MB. Increase if needed:

```python
app = FastAPI(
    ...
    max_request_size=200 * 1024 * 1024  # 200 MB
)
```

### Session not found

Sessions expire after 1 hour. Check session directory:
```bash
ls -la /tmp/music_transposer_sessions/
```

---

## Performance

### Typical Processing Times

- **PDF Upload + Audiveris**: 10-30 seconds (depends on PDF complexity)
- **Transposition**: 1-3 seconds
- **PDF Generation**: 3-10 seconds

### Optimization Tips

1. **Use caching** for repeated transpositions
2. **Queue processing** for high traffic
3. **CDN** for static file serving
4. **Load balancing** with multiple workers

---

## Security Considerations

### Production Checklist

- [ ] Enable HTTPS (use reverse proxy like nginx)
- [ ] Restrict CORS to specific domains
- [ ] Add authentication (API keys, JWT)
- [ ] Implement rate limiting
- [ ] Validate file uploads (type, size, content)
- [ ] Sanitize file names
- [ ] Use environment variables for secrets
- [ ] Regular session cleanup
- [ ] Monitor disk usage
- [ ] Set up logging and monitoring

---

## License

See main project LICENSE file.

---

## Support

For issues or questions:
1. Check [ROADMAP.md](../ROADMAP.md) for development plan
2. Check [CLAUDE.md](../CLAUDE.md) for architecture details
3. Review FastAPI docs: https://fastapi.tiangolo.com/

---

## Changelog

### v1.0.0 (2025-10-22)
- Initial release
- Upload PDF endpoint
- Transpose endpoint
- Convert to PDF endpoint
- Session management
- Auto-generated API docs
- CORS support

---

**Happy Transposing! 🎵**
