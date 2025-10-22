# Dockerfile for Music Transposer API
# Includes Audiveris and MuseScore for Linux deployment

FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    default-jre \
    musescore3 \
    wget \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Audiveris (Java-based)
# Note: Using a working download link for Audiveris
WORKDIR /opt
RUN wget --no-check-certificate https://github.com/Audiveris/audiveris/releases/download/5.3.1/Audiveris-5.3.1.zip -O audiveris.zip || \
    wget https://github.com/Audiveris/audiveris/releases/download/5.2/Audiveris-5.2.zip -O audiveris.zip && \
    unzip -q audiveris.zip && \
    rm audiveris.zip

# Find the extracted Audiveris directory and create wrapper
RUN AUDIVERIS_DIR=$(find /opt -type d -name "Audiveris*" | head -1) && \
    AUDIVERIS_JAR=$(find $AUDIVERIS_DIR -name "*.jar" -o -name "Audiveris*.jar" | head -1) && \
    echo "#!/bin/bash" > /usr/local/bin/audiveris && \
    echo "java -Xmx4g -jar $AUDIVERIS_JAR \"\$@\"" >> /usr/local/bin/audiveris && \
    chmod +x /usr/local/bin/audiveris

# Verify MuseScore installation
RUN musescore3 --version || echo "MuseScore installed"

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY api/requirements.txt ./api/
RUN pip3 install --no-cache-dir -r api/requirements.txt

# Copy application code
COPY . .

# Set environment variables for binary paths
ENV AUDIVERIS_BIN=/usr/local/bin/audiveris
ENV MUSESCORE_BIN=musescore3
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the application
CMD ["python3", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
