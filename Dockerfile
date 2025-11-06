# # Dockerfile for Music Transposer API
# # Includes Audiveris and MuseScore for Linux deployment
# # Based on working Audiveris Dockerfile example with Ubuntu 22.04

# FROM ubuntu:22.04

# # Prevent interactive prompts during package installation
# ENV DEBIAN_FRONTEND=noninteractive

# # Install system dependencies including OpenJDK 17
# RUN apt-get update && apt-get install -y \
#     python3 \
#     python3-pip \
#     curl \
#     wget \
#     git \
#     openjdk-17-jdk \
#     musescore3 \
#     tesseract-ocr \
#     tesseract-ocr-eng \
#     && rm -rf /var/lib/apt/lists/*

# # Set Java environment variables
# ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
# ENV PATH=$PATH:$JAVA_HOME/bin

# # Clone and build Audiveris from source (using development branch like working example)
# WORKDIR /opt
# RUN git clone --branch development https://github.com/Audiveris/audiveris.git && \
#     cd audiveris && \
#     ./gradlew build && \
#     mkdir /audiveris-extract && \
#     tar -xf /opt/audiveris/build/distributions/Audiveris*.tar -C /audiveris-extract --strip-components=1 && \
#     rm -rf /opt/audiveris

# # Set working directory
# WORKDIR /app

# # Copy requirements and install Python dependencies
# COPY api/requirements.txt ./api/
# RUN pip3 install --no-cache-dir -r api/requirements.txt

# # Copy application code
# COPY . .

# # Set environment variables for binary paths
# ENV AUDIVERIS_BIN=/audiveris-extract/bin/Audiveris
# ENV MUSESCORE_BIN=musescore3
# ENV PYTHONUNBUFFERED=1

# # Expose port
# EXPOSE 8000

# # Health check
# HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
#     CMD curl -f http://localhost:8000/api/health || exit 1

# # Run the application
# CMD ["python3", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]


# Music Transposer API (Audiveris + Verovio; optional MuseScore)
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Base deps
RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    curl wget git ca-certificates \
    openjdk-17-jre-headless \
    tesseract-ocr tesseract-ocr-eng \
    verovio \
    unzip \
    fonts-dejavu-core fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*

# Java env
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="$PATH:$JAVA_HOME/bin"

# ---- Build Audiveris from source (development branch or pin a tag) ----
WORKDIR /opt
RUN git clone --depth 1 --branch development https://github.com/Audiveris/audiveris.git

WORKDIR /opt/audiveris
# gradlew fetches Gradle itself; jre-headless is enough to run it
RUN chmod +x gradlew && ./gradlew distTar --no-daemon --console=plain

# Extract distro; note: binary is LOWERCASE 'audiveris'
RUN mkdir -p /audiveris-extract && \
    tar -xf /opt/audiveris/build/distributions/Audiveris*.tar -C /audiveris-extract --strip-components=1 && \
    rm -rf /opt/audiveris

# Verify (do NOT swallow errors)
RUN /audiveris-extract/bin/audiveris -help

# ---- OPTIONAL: MuseScore (fallback) via AppImage ----
# AppImages for MuseScore 3 need libfuse2
# Uncomment to enable MuseScore fallback:
# RUN apt-get update && apt-get install -y libfuse2 && rm -rf /var/lib/apt/lists/*
# RUN mkdir -p /opt/mscore && \
#     wget -O /opt/mscore/MuseScore-3.AppImage \
#       https://github.com/musescore/MuseScore/releases/download/v3.7.0/MuseScore-3.7.0-x86_64.AppImage && \
#     chmod +x /opt/mscore/MuseScore-3.AppImage
# # Wrapper so we can call 'mscore' headlessly
# RUN printf '%s\n' '#!/bin/sh' \
#   'export QT_QPA_PLATFORM=offscreen' \
#   'exec /opt/mscore/MuseScore-3.AppImage "$@"' \
#   > /usr/local/bin/mscore && chmod +x /usr/local/bin/mscore
# # Quick check (will print version and exit 0)
# RUN /usr/local/bin/mscore -v || true

# Binaries for the app
ENV AUDIVERIS_BIN=/audiveris-extract/bin/audiveris
ENV VEROVIO_BIN=verovio
# If you enabled MuseScore wrapper above, you may also set:
# ENV MUSESCORE_BIN=/usr/local/bin/mscore

# FastAPI app
WORKDIR /app
COPY api/requirements.txt ./api/
RUN pip3 install --no-cache-dir -r api/requirements.txt

COPY . .

# Useful defaults for headless rendering
ENV QT_QPA_PLATFORM=offscreen
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -fsS http://localhost:8000/api/health || exit 1

CMD ["python3", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]