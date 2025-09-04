# MusicBrainz MCP Server Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8081

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project configuration files first for better caching
COPY pyproject.toml .
COPY README.md .

# Copy application code BEFORE installing dependencies
COPY src/ src/
COPY tests/ tests/
COPY docs/ docs/

# Install Python dependencies (now that source code is available)
RUN pip install --no-cache-dir -e .

# Create non-root user
RUN useradd --create-home --shell /bin/bash musicbrainz
RUN chown -R musicbrainz:musicbrainz /app
USER musicbrainz

# Expose port (smithery.ai uses 8081)
EXPOSE 8081

# Health check using httpx with proper error handling
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import httpx; import sys; \
try: \
    response = httpx.get('http://localhost:8081/health', timeout=5); \
    sys.exit(0 if 200 <= response.status_code < 400 else 1) \
except Exception: \
    sys.exit(1)" || exit 1

# Default command
CMD ["python", "-m", "musicbrainz_mcp.server"]
