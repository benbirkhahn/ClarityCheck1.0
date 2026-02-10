FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (if any required by PyMuPDF or other libs)
# build-essential is often needed for compiling python extensions
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY backend/ ./backend/

# Create uploads directory
RUN mkdir -p uploads

# Set PYTHONPATH to include /app so imports work correctly
ENV PYTHONPATH=/app

# Copy and prepare start script
COPY backend/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Default command
CMD ["/app/start.sh"]
