# Music Transposer API - Dockerfile
# Audiveris + Verovio for sheet music processing

FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    openjdk-17-jre-headless git curl unzip ca-certificates \
    tesseract-ocr tesseract-ocr-eng verovio \
    python3 python3-pip \
    fonts-dejavu-core fonts-noto-core \
 && rm -rf /var/lib/apt/lists/*

# --- Audiveris build ---
WORKDIR /opt
# pin or keep development; depth=1 avoids huge checkout
ARG AUDIVERIS_REF=development
RUN git clone --depth 1 --branch "$AUDIVERIS_REF" https://github.com/Audiveris/audiveris.git

WORKDIR /opt/audiveris
# distTar is what creates build/distributions/Audiveris-*.tar
RUN chmod +x gradlew \
 && ./gradlew --no-daemon --console=plain distTar

# extract the distribution (note: lowercase 'audiveris' script)
RUN mkdir -p /audiveris-extract \
 && tar -xf build/distributions/Audiveris*.tar -C /audiveris-extract --strip-components=1

RUN /audiveris-extract/bin/audiveris -help

# Clean up build artifacts
RUN rm -rf /opt/audiveris

# --- FastAPI application setup ---
WORKDIR /app

# Copy and install Python dependencies
COPY api/requirements.txt ./api/
RUN pip3 install --no-cache-dir -r api/requirements.txt

# Copy application code
COPY . .

# Set environment variables for binary paths
ENV AUDIVERIS_BIN=/audiveris-extract/bin/audiveris
ENV VEROVIO_BIN=verovio
ENV MUSESCORE_BIN=musescore3
ENV PYTHONUNBUFFERED=1
ENV QT_QPA_PLATFORM=offscreen

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/health || exit 1

# Run the application
CMD ["python3", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
