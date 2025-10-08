FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py database.py cli.py setup_uri.py ./

# Create directories for tokens database
RUN mkdir -p /app/tokens

# Create non-root user
RUN useradd -m -u 1000 obsidian && \
    chown -R obsidian:obsidian /app

# Switch to non-root user
USER obsidian

# Expose port
EXPOSE 5985

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5985/health || exit 1

# Run uvicorn with multiple workers
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5985", "--workers", "2"]
