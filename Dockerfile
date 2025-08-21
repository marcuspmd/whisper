# Multi-stage build for Whisper Transcriber
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    portaudio19-dev \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy source code
COPY src/ src/
COPY main.py .
COPY setup.py .

# Production stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash whisper

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/whisper/.local

# Copy application code
COPY --chown=whisper:whisper src/ src/
COPY --chown=whisper:whisper main.py .
COPY --chown=whisper:whisper requirements.txt .
COPY --chown=whisper:whisper README.md .
COPY --chown=whisper:whisper LICENSE .

# Switch to non-root user
USER whisper

# Make sure user's local bin is in PATH
ENV PATH=/home/whisper/.local/bin:$PATH

# Expose web interface port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Default command (web interface)
CMD ["python", "main.py", "--web", "--web-host", "0.0.0.0", "--web-port", "3000"]

# Labels
LABEL maintainer="Marcus Paulo M Dias <marcusmazzon@gmail.com>" \
      description="Real-time audio transcription with Whisper AI" \
      version="1.0.0" \
      org.opencontainers.image.title="Whisper Transcriber" \
      org.opencontainers.image.description="Real-time audio transcription with Whisper AI and translation" \
      org.opencontainers.image.url="https://github.com/marcuspmd/whisper" \
      org.opencontainers.image.source="https://github.com/marcuspmd/whisper" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.created="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
      org.opencontainers.image.revision="$(git rev-parse HEAD)" \
      org.opencontainers.image.licenses="MIT"
