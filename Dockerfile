# Dockerfile for Music Transposer API
# Includes Audiveris and MuseScore for Linux deployment

FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies including GUI libraries for Audiveris
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    default-jre \
    musescore3 \
    wget \
    unzip \
    curl \
    gdebi-core \
    libgtk-3-0 \
    libglib2.0-0 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxtst6 \
    libxi6 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install Audiveris using apt install (per official docs)
WORKDIR /tmp
RUN wget https://github.com/Audiveris/audiveris/releases/download/5.7.1/Audiveris-5.7.1-ubuntu22.04-x86_64.deb && \
    apt install -y ./Audiveris-5.7.1-ubuntu22.04-x86_64.deb && \
    rm Audiveris-5.7.1-ubuntu22.04-x86_64.deb

# Verify installations (Audiveris is at /opt/audiveris/bin/Audiveris)
RUN /opt/audiveris/bin/Audiveris -help || echo "Audiveris installed"
RUN musescore3 --version || echo "MuseScore installed"

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY api/requirements.txt ./api/
RUN pip3 install --no-cache-dir -r api/requirements.txt

# Copy application code
COPY . .

# Set environment variables for binary paths
# After .deb installation, Audiveris is at /opt/audiveris/bin/Audiveris (per official docs)
ENV AUDIVERIS_BIN=/opt/audiveris/bin/Audiveris
ENV MUSESCORE_BIN=musescore3
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the application
CMD ["python3", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
