# Music Transposer App - Development Roadmap

## Project Overview

Transform the current desktop Python/Tkinter app into a cross-platform mobile and desktop application using Flutter + FastAPI.

**Current State:** Desktop-only Python app with Tkinter GUI
**Target State:** Native apps for iOS, iPad, Android, macOS, Windows

---

## Technology Stack

### Frontend
- **Flutter** (Dart language)
- Single codebase for 6 platforms
- Material Design UI components
- HTTP client for API calls

### Backend
- **FastAPI** (Python)
- Reuses existing `cli.py`, `transpose.py` logic
- RESTful API endpoints
- File upload/download handling
- Cloud-hosted (Railway, Render, or DigitalOcean)

### Processing Tools
- **Audiveris** - PDF to MusicXML conversion
- **MuseScore** - MusicXML to PDF rendering
- Both run on cloud server (not on mobile devices)

---

## Phase 1: FastAPI Backend (Week 1-2)

### Goals
- Convert Python functions to REST API
- Handle file uploads and downloads
- Implement session management
- Test locally before deployment

### Tasks

#### 1.1: Project Setup
- [ ] Create `api/` directory in project root
- [ ] Create virtual environment: `python -m venv api/venv`
- [ ] Install dependencies:
  ```bash
  pip install fastapi uvicorn python-multipart aiofiles
  ```
- [ ] Create `api/requirements.txt`
- [ ] Create `api/main.py`

#### 1.2: Core API Endpoints

**Endpoint 1: Upload PDF**
```python
POST /api/upload-pdf
- Accept: multipart/form-data (PDF file)
- Process: Run Audiveris conversion
- Return: { session_id, musicxml_data, metadata: { key, time_sig, part } }
```

**Endpoint 2: Transpose**
```python
POST /api/transpose
- Accept: { session_id, target_key (int: -7 to 7) }
- Process: Run transpose.py logic
- Return: { transposed_musicxml_data }
```

**Endpoint 3: Convert to PDF**
```python
POST /api/convert-to-pdf
- Accept: { session_id }
- Process: Run MuseScore conversion
- Return: PDF file download
```

**Endpoint 4: Health Check**
```python
GET /api/health
- Return: { status: "ok", version: "1.0" }
```

#### 1.3: File Management
- [ ] Implement session-based file storage
- [ ] Create temp directories for processing
- [ ] Add file cleanup after 1 hour
- [ ] Handle concurrent uploads

#### 1.4: Error Handling
- [ ] Audiveris failure responses
- [ ] Invalid file format errors
- [ ] Invalid key selection errors
- [ ] Server error logging

#### 1.5: Testing
- [ ] Test with curl/Postman
- [ ] Test file upload limits
- [ ] Test concurrent requests
- [ ] Verify cleanup works

#### 1.6: Documentation
- [ ] API documentation (FastAPI auto-generates)
- [ ] Example requests/responses
- [ ] Error code reference

**Deliverable:** Working FastAPI server running on `http://localhost:8000`

---

## Phase 2: Cloud Deployment (Week 2)

### Goals
- Deploy backend to production
- Install Audiveris/MuseScore on server
- Test from internet

### Tasks

#### 2.1: Choose Hosting Provider

**Option A: Railway** (Recommended - Easiest)
- Free tier available for testing
- Easy GitHub integration
- One-click deploy
- ~$5-10/month for production

**Option B: Render**
- Free tier with limitations
- Good Python support
- ~$7/month for production

**Option C: DigitalOcean**
- More control
- Requires server management
- ~$12/month

#### 2.2: Server Setup
- [ ] Create account on chosen platform
- [ ] Create new project/app
- [ ] Configure environment variables
- [ ] Set up file storage (temp directories)

#### 2.3: Install Dependencies
- [ ] Install Python dependencies from requirements.txt
- [ ] Install Audiveris on server
- [ ] Install MuseScore on server
- [ ] Verify both tools work via CLI

#### 2.4: Deploy Backend
- [ ] Push code to GitHub (if using Railway/Render)
- [ ] Configure build commands
- [ ] Set up custom domain (optional)
- [ ] Enable HTTPS

#### 2.5: Testing
- [ ] Test all endpoints from internet
- [ ] Verify file upload works
- [ ] Check processing times
- [ ] Monitor server logs

**Deliverable:** Backend API accessible at `https://your-app.railway.app` or similar

---

## Phase 3: Flutter App Setup (Week 3)

### Goals
- Install Flutter SDK
- Create new Flutter project
- Set up for multi-platform development
- Create basic UI structure

### Tasks

#### 3.1: Install Flutter

**macOS Installation:**
```bash
# Download Flutter SDK
git clone https://github.com/flutter/flutter.git -b stable
export PATH="$PATH:`pwd`/flutter/bin"

# Run flutter doctor
flutter doctor

# Install Xcode (already have ✓)
# Install Android Studio
# Install VS Code + Flutter extension
```

#### 3.2: Create Flutter Project
```bash
cd "/Users/harikoornala/Code/Random Projects with Chat/omr app apptmet 2"
flutter create flutter_app
cd flutter_app
```

#### 3.3: Enable All Platforms
```bash
flutter config --enable-macos-desktop
flutter config --enable-windows-desktop
flutter config --enable-linux-desktop
flutter config --enable-web
```

#### 3.4: Add Dependencies

Edit `pubspec.yaml`:
```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.1.0              # API calls
  file_picker: ^6.1.1       # File upload
  path_provider: ^2.1.1     # File paths
  dio: ^5.4.0               # Better HTTP with progress
  provider: ^6.1.1          # State management
```

#### 3.5: Project Structure
```
flutter_app/
├── lib/
│   ├── main.dart              # Entry point
│   ├── screens/
│   │   ├── home_screen.dart   # Main UI
│   │   └── result_screen.dart # Show results
│   ├── services/
│   │   └── api_service.dart   # API calls
│   ├── models/
│   │   └── music_data.dart    # Data models
│   └── widgets/
│       ├── file_upload.dart   # Upload widget
│       ├── key_selector.dart  # Dropdown
│       └── transpose_button.dart
└── pubspec.yaml
```

#### 3.6: Test Basic Setup
```bash
# Run on macOS
flutter run -d macos

# Run on iOS simulator
flutter run -d ios

# Run on web
flutter run -d chrome
```

**Deliverable:** Flutter app running "Hello World" on macOS, iOS simulator, and web browser

---

## Phase 4: Flutter UI Development (Week 3-4)

### Goals
- Recreate Tkinter UI in Flutter
- Implement file upload
- Add key selection dropdown
- Show music metadata
- Display results

### Tasks

#### 4.1: Design UI Layout

**Main Screen:**
```
┌─────────────────────────────────────┐
│   🎵 Music Transposer               │
├─────────────────────────────────────┤
│                                     │
│  Step 1: Upload Sheet Music PDF    │
│  ┌─────────────────────────────┐   │
│  │  📁 Choose PDF File         │   │
│  └─────────────────────────────┘   │
│  Status: [Processing...]            │
│                                     │
│  ───────────────────────────────    │
│                                     │
│  Step 2: Current Key Information   │
│  ┌─────────────────────────────┐   │
│  │  Current Key: Eb major       │   │
│  │  Time Signature: 4/4         │   │
│  │  Part: Piano                 │   │
│  └─────────────────────────────┘   │
│                                     │
│  ───────────────────────────────    │
│                                     │
│  Step 3: Select Target Key         │
│  Transpose to: [D major (2 sharps)▼]│
│                                     │
│  ┌──────────┐  ┌──────────────┐    │
│  │Transpose │  │Convert to PDF│    │
│  └──────────┘  └──────────────┘    │
│                                     │
│  Result: [Success message]          │
└─────────────────────────────────────┘
```

#### 4.2: Implement File Upload
- [ ] Add file picker button
- [ ] Validate PDF files only
- [ ] Show file name after selection
- [ ] Display upload progress bar

#### 4.3: API Integration
- [ ] Create API service class
- [ ] Implement upload-pdf call
- [ ] Parse response (key, time sig, part)
- [ ] Handle errors and timeouts

#### 4.4: Display Music Info
- [ ] Show current key signature
- [ ] Show time signature
- [ ] Show part name
- [ ] Format display nicely

#### 4.5: Key Selection Dropdown
- [ ] Create list of all major keys
- [ ] Format: "D major (2 sharps)"
- [ ] Enable after upload succeeds
- [ ] Map to fifths notation (-7 to 7)

#### 4.6: Transpose Button
- [ ] Disable until file uploaded
- [ ] Call transpose API
- [ ] Show loading indicator
- [ ] Enable "Convert to PDF" after success

#### 4.7: Convert to PDF Button
- [ ] Disable until transposition done
- [ ] Call convert-to-pdf API
- [ ] Download PDF file
- [ ] Ask user to open/share

#### 4.8: Responsive Design
- [ ] Adapt layout for phone screens
- [ ] Optimize for tablet/iPad
- [ ] Test on different screen sizes
- [ ] Add landscape mode support

**Deliverable:** Fully functional Flutter app with all features working

---

## Phase 5: Testing (Week 5)

### Goals
- Test on all target platforms
- Fix bugs
- Optimize performance
- Polish UI

### Tasks

#### 5.1: iOS Testing
- [ ] Test on iPhone simulator (various models)
- [ ] Test on iPad simulator
- [ ] Test file upload from iOS
- [ ] Test PDF download/sharing
- [ ] Test on physical iPhone (if available)

#### 5.2: Android Testing
- [ ] Install Android Studio
- [ ] Create Android emulator
- [ ] Test on Android phone emulator
- [ ] Test on Android tablet emulator
- [ ] Test file permissions
- [ ] Test on physical Android device (if available)

#### 5.3: Desktop Testing
- [ ] Test on macOS
- [ ] Test file dialogs
- [ ] Test on Windows (if available)
- [ ] Verify UI scaling

#### 5.4: Bug Fixes
- [ ] Fix any crashes
- [ ] Handle edge cases
- [ ] Improve error messages
- [ ] Fix UI issues

#### 5.5: Performance Optimization
- [ ] Optimize file upload speed
- [ ] Add caching for repeated requests
- [ ] Reduce app size
- [ ] Improve loading times

#### 5.6: UI Polish
- [ ] Add animations
- [ ] Improve colors/styling
- [ ] Add app icon
- [ ] Add splash screen

**Deliverable:** Stable app tested on all platforms

---

## Phase 6: App Store Preparation (Week 6)

### Goals
- Prepare for iOS App Store
- Prepare for Google Play Store
- Create app store assets
- Submit for review

### Tasks

#### 6.1: iOS App Store

**Requirements:**
- Apple Developer Account ($99/year)
- App Store Connect access
- App icon (1024x1024)
- Screenshots for all devices
- Privacy policy
- App description

**Steps:**
- [ ] Create Apple Developer account
- [ ] Generate app icon assets
- [ ] Take screenshots (iPhone, iPad)
- [ ] Write app description
- [ ] Create privacy policy
- [ ] Configure App Store Connect
- [ ] Build release version
- [ ] Upload to TestFlight
- [ ] Submit for review

#### 6.2: Google Play Store

**Requirements:**
- Google Play Developer Account ($25 one-time)
- App icon (512x512)
- Screenshots for phones/tablets
- Feature graphic
- Privacy policy
- App description

**Steps:**
- [ ] Create Google Play account
- [ ] Generate app icon
- [ ] Take screenshots (Android)
- [ ] Write app description
- [ ] Create feature graphic
- [ ] Build release APK/AAB
- [ ] Upload to Play Console
- [ ] Submit for review

#### 6.3: Optional: macOS/Windows Distribution
- [ ] Package macOS app (DMG)
- [ ] Code sign macOS app
- [ ] Create Windows installer
- [ ] Distribute via website

**Deliverable:** Apps live on App Store and Google Play!

---

## Timeline Summary

| Phase | Duration | Key Milestone |
|-------|----------|---------------|
| Phase 1: FastAPI Backend | 1-2 weeks | Working local API |
| Phase 2: Cloud Deployment | 3-5 days | Production API live |
| Phase 3: Flutter Setup | 2-3 days | "Hello World" on all platforms |
| Phase 4: Flutter UI | 1-2 weeks | Full-featured app |
| Phase 5: Testing | 1 week | Stable, bug-free app |
| Phase 6: App Stores | 3-5 days | Published apps |
| **Total** | **6-8 weeks** | **Shipped product** |

---

## Cost Breakdown

### Development (One-time)
- Time investment: 6-8 weeks
- Tools: Free (Flutter, VS Code, Python)

### Year 1 Costs
- Apple Developer Account: $99/year
- Google Play Developer: $25 one-time
- Cloud Hosting: $60-240/year ($5-20/month)
- **Total Year 1: $184-364**

### Ongoing Costs (Year 2+)
- Apple Developer Account: $99/year
- Cloud Hosting: $60-240/year
- **Total: $159-339/year**

---

## Success Criteria

- ✅ Upload PDF and see correct key signature
- ✅ Transpose to any major key
- ✅ Download transposed PDF
- ✅ Works on iPhone, iPad, Android
- ✅ Works on macOS, Windows
- ✅ Response time < 30 seconds for average PDF
- ✅ No crashes or data loss
- ✅ Published on App Store and Google Play

---

## Risks & Mitigation

### Risk 1: Cloud Hosting Too Expensive
**Mitigation:** Start with Railway free tier, upgrade as needed

### Risk 2: Audiveris/MuseScore Hard to Install on Server
**Mitigation:** Use Docker container with pre-installed tools

### Risk 3: App Store Rejection
**Mitigation:** Follow guidelines carefully, test thoroughly

### Risk 4: Slow Processing Times
**Mitigation:** Optimize backend, add caching, consider CDN

### Risk 5: Learning Curve for Flutter/Dart
**Mitigation:** Start with simple UI, iterate, use Claude Code for help

---

## Next Steps

**Immediate (Next Session):**
1. Create `api/` directory
2. Set up FastAPI project
3. Implement upload-pdf endpoint
4. Test locally

**This Week:**
- Complete Phase 1 (FastAPI Backend)
- Deploy to Railway/Render
- Test from internet

**Next Week:**
- Install Flutter
- Create Flutter project
- Build basic UI

---

## Resources

### Documentation
- FastAPI: https://fastapi.tiangolo.com/
- Flutter: https://docs.flutter.dev/
- Railway: https://docs.railway.app/
- Render: https://render.com/docs

### Tutorials
- Flutter File Upload: https://pub.dev/packages/file_picker
- FastAPI File Upload: https://fastapi.tiangolo.com/tutorial/request-files/
- Flutter HTTP: https://docs.flutter.dev/cookbook/networking/fetch-data

### Community
- Flutter Discord: https://discord.gg/flutter
- r/FlutterDev: https://reddit.com/r/FlutterDev
- FastAPI Discord: https://discord.gg/fastapi

---

## Notes for Future Claude Instances

When continuing this project:

1. **Read CLAUDE.md** for technical architecture
2. **Read this ROADMAP.md** for development plan
3. **Check current phase** - see what's completed
4. **Review code** in `api/` and `flutter_app/` directories
5. **Continue from last checkpoint**

The plan is flexible - adjust as needed based on:
- User feedback
- Technical challenges
- Time constraints
- Budget considerations

Good luck! 🚀
