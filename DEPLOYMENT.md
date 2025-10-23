# Deployment Guide

How to deploy the Music Transposer API to the cloud with Audiveris and MuseScore.

---

## The Challenge

Audiveris and MuseScore are currently installed on your Mac at:
- `/Applications/Audiveris.app/`
- `/Applications/MuseScore 4.app/`

Cloud servers run **Linux**, not macOS, so we need Linux versions of these tools.

---

## Solution: Docker Container

We've created a Docker container that includes:
- ✅ Ubuntu 22.04 Linux base
- ✅ Python 3
- ✅ Audiveris 5.7.1 (installed via official .deb package)
- ✅ MuseScore 3 (Linux version)
- ✅ Your FastAPI application

The code now **auto-detects the OS** and uses the correct binary paths.

**Note:** Audiveris is installed using the official Ubuntu 22.04 .deb package from the GitHub releases, which properly handles all dependencies and binary paths.

---

## Deployment Options

### **Option 1: Railway** (Easiest)

Railway supports Docker and auto-deploys from GitHub.

#### Step 1: Push to GitHub

```bash
cd "/Users/harikoornala/Code/Random Projects with Chat/omr app apptmet 2"

# Initialize git (if not already)
git init
git add .
git commit -m "Initial commit: Music Transposer API"

# Create repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/music-transposer.git
git push -u origin main
```

#### Step 2: Deploy to Railway

1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your repository
6. Railway detects Dockerfile and builds automatically!
7. Wait 5-10 minutes for build
8. Get your URL: `https://your-app.up.railway.app`

**Environment Variables** (already set in Dockerfile):
- `AUDIVERIS_BIN=/usr/bin/audiveris`
- `MUSESCORE_BIN=musescore3`

**Cost:** ~$5-10/month (free tier available)

**Build Time:** First deployment takes 10-15 minutes. Subsequent updates take 3-5 minutes.

---

### **Option 2: Render**

Render also supports Docker.

#### Step 1: Push to GitHub (same as above)

#### Step 2: Deploy to Render

1. Go to https://render.com
2. Sign up
3. Click "New +" → "Web Service"
4. Connect GitHub repository
5. Select:
   - **Environment**: Docker
   - **Region**: Pick closest to you
   - **Instance Type**: Starter ($7/month) or Free (with limitations)
6. Click "Create Web Service"
7. Wait for build (10-15 minutes first time)
8. Get your URL: `https://your-app.onrender.com`

**Cost:** Free tier (sleeps after inactivity) or $7/month

---

### **Option 3: DigitalOcean App Platform**

#### Step 1: Push to GitHub (same as above)

#### Step 2: Deploy to DigitalOcean

1. Go to https://cloud.digitalocean.com/apps
2. Click "Create App"
3. Connect GitHub
4. Select repository
5. DigitalOcean detects Dockerfile
6. Choose plan: Basic ($5/month)
7. Deploy!

**Cost:** $5/month minimum

---

### **Option 4: Build Docker Locally (Testing)**

Test the Docker container on your Mac before deploying:

```bash
# Build the image
docker build -t music-transposer-api .

# Run locally
docker run -p 8000:8000 music-transposer-api

# Test
curl http://localhost:8000/api/health
```

This ensures everything works before cloud deployment.

---

## How It Works in Production

### On Your Mac (Development)
```
cli.py detects: macOS
Uses: /Applications/Audiveris.app/
Uses: /Applications/MuseScore 4.app/
```

### On Cloud Server (Production)
```
cli.py detects: Linux
Uses: /usr/bin/audiveris (installed via .deb package)
Uses: musescore3 (apt-get package)
```

**Same code, different binaries!**

### Audiveris Installation Method
The Dockerfile uses the official Audiveris .deb package for Ubuntu 22.04:
```dockerfile
RUN wget https://github.com/Audiveris/audiveris/releases/download/5.7.1/Audiveris-5.7.1-ubuntu22.04-x86_64.deb && \
    apt-get install -y ./Audiveris-5.7.1-ubuntu22.04-x86_64.deb
```

This is more reliable than manual JAR extraction because:
- Handles all dependencies automatically
- Installs to standard system paths
- Works consistently across deployments

---

## Verify Deployment

After deployment, test all endpoints:

```bash
# Replace with your actual URL
export API_URL="https://your-app.up.railway.app"

# 1. Health check
curl $API_URL/api/health

# 2. Get available keys
curl $API_URL/api/keys

# 3. Upload a PDF (will take 15-30 seconds)
curl -X POST "$API_URL/api/upload-pdf" \
  -F "file=@sheet1.pdf"

# 4. Transpose (use session_id from step 3)
curl -X POST "$API_URL/api/transpose" \
  -d "session_id=YOUR_SESSION_ID" \
  -d "target_key=2"

# 5. Download PDF
curl -X POST "$API_URL/api/convert-to-pdf" \
  -d "session_id=YOUR_SESSION_ID" \
  -o transposed.pdf
```

---

## Troubleshooting

### "Audiveris not found"

Check logs to see if Audiveris .deb package was installed:
```bash
# Railway/Render logs will show
docker logs <container-id>
```

The Dockerfile includes a verification step:
```dockerfile
RUN audiveris -help || echo "Audiveris installed"
```

If installation fails, common causes:
- Download URL changed (check https://github.com/Audiveris/audiveris/releases)
- Network issues during build
- Incompatible Ubuntu version

### "MuseScore not found"

Check if MuseScore installed:
```bash
# In Dockerfile, add verification
RUN musescore3 --version
```

### "Out of memory"

Audiveris needs RAM. Upgrade server plan:
- Railway: Increase memory limit
- Render: Use Starter plan ($7/month)
- DigitalOcean: Use at least Basic ($12/month)

### Processing too slow

PDF conversion can take time. Optimize:
1. Increase server resources
2. Add timeout handling in Flutter app
3. Consider async processing with webhooks

---

## Environment Variables

These are already set in the Dockerfile and don't need to be configured in Railway/Render:

```bash
# Binary paths (set in Dockerfile)
AUDIVERIS_BIN=/usr/bin/audiveris
MUSESCORE_BIN=musescore3
PYTHONUNBUFFERED=1
```

**Optional overrides** (only if you need to customize):
```bash
# Override binary paths (not recommended unless necessary)
AUDIVERIS_BIN=/custom/path/to/audiveris

# Uvicorn workers (for high traffic)
WEB_CONCURRENCY=4
```

---

## Updating the Deployment

When you make code changes:

```bash
# Commit and push
git add .
git commit -m "Update API"
git push

# Railway/Render auto-deploys from GitHub!
# Usually takes 3-5 minutes
```

---

## Cost Summary

### Development (Free)
- Local testing: $0
- Docker testing: $0

### Production

**Railway:**
- Free tier: $5 credit/month
- After free: ~$5-10/month
- Best for: Easy deployment

**Render:**
- Free tier: Available (sleeps when idle)
- Paid: $7/month
- Best for: Budget-conscious

**DigitalOcean:**
- Basic: $5/month (512 MB RAM)
- Standard: $12/month (1 GB RAM - recommended)
- Best for: Predictable pricing

**Recommendation:** Start with Railway free tier, upgrade when needed.

---

## Next Steps After Deployment

1. ✅ API is live in the cloud
2. Update Flutter app to use production URL
3. Test from mobile devices
4. Monitor logs and performance
5. Set up domain name (optional)
6. Enable HTTPS (automatic on Railway/Render)

---

## Alternative: Local Server (Not Recommended)

If cloud deployment is too complex, you could run the server on your Mac and expose it:

```bash
# Install ngrok
brew install ngrok

# Start your API
python -m uvicorn api.main:app --port 8000

# Expose to internet (in another terminal)
ngrok http 8000

# Use the ngrok URL in your Flutter app
# https://abc123.ngrok.io
```

**Cons:**
- Your Mac must always be on
- Unstable URL (changes on restart)
- Security concerns
- Not suitable for production

**Only use for development/testing!**

---

## Support

If deployment fails:
1. Check Railway/Render logs
2. Test Docker locally first
3. Verify Dockerfile builds successfully
4. Check environment variables are set

---

**You're ready to deploy!** 🚀

Choose Railway for easiest deployment, or Render if you want a free tier to start.
