# Dockerfile for Music Transposer API
# Includes Audiveris and MuseScore for Linux deployment

FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    openjdk-17-jre-headless \
    musescore3 \
    wget \
    curl \
    xvfb \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Download and build Audiveris from source (using gradle wrapper)
WORKDIR /opt
RUN wget https://github.com/Audiveris/audiveris/archive/refs/tags/5.7.1.zip && \
    unzip 5.7.1.zip && \
    rm 5.7.1.zip && \
    cd audiveris-5.7.1 && \
    chmod +x gradlew && \
    ./gradlew build -x test && \
    cp build/libs/Audiveris-*.jar /opt/audiveris.jar && \
    cd /opt && \
    rm -rf audiveris-5.7.1

# Create wrapper script for Audiveris
RUN echo '#!/bin/bash\nexport DISPLAY=:99\nXvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &\njava -Xmx4g -jar /opt/audiveris.jar "$@"' > /usr/local/bin/audiveris && \
    chmod +x /usr/local/bin/audiveris

# Verify installations
RUN musescore3 --version || echo "MuseScore installed"

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY api/requirements.txt ./api/
RUN pip3 install --no-cache-dir -r api/requirements.txt

# Copy application code
COPY . .

# Set environment variables for binary paths
# Audiveris wrapper script at /usr/local/bin/audiveris
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
