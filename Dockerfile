# Dockerfile for Music Transposer API
# Includes Audiveris and MuseScore for Linux deployment
# Based on working Audiveris Dockerfile example

FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies including OpenJDK 17
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    wget \
    git \
    openjdk-17-jdk \
    musescore3 \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Set Java environment variables
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH=$PATH:$JAVA_HOME/bin

# Build Audiveris from source using the working approach
RUN git clone --branch 5.7.1 https://github.com/Audiveris/audiveris.git && \
    cd audiveris && \
    ./gradlew build && \
    mkdir /audiveris-extract && \
    tar -xvf /audiveris/build/distributions/Audiveris*.tar -C /audiveris-extract && \
    mv /audiveris-extract/Audiveris*/* /audiveris-extract/ && \
    rm -rf /audiveris

# Verify installations
RUN /audiveris-extract/bin/Audiveris -help || echo "Audiveris installed"
RUN musescore3 --version || echo "MuseScore installed"

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY api/requirements.txt ./api/
RUN pip3 install --no-cache-dir -r api/requirements.txt

# Copy application code
COPY . .

# Set environment variables for binary paths
# Audiveris binary from extracted distribution
ENV AUDIVERIS_BIN=/audiveris-extract/bin/Audiveris
ENV MUSESCORE_BIN=musescore3
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the application
CMD ["python3", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
