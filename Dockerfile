FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create upload directories
RUN mkdir -p /var/www/journal/static/uploads/avatars \
    /var/www/journal/static/uploads/articles \
    /var/www/journal/static/uploads/documents \
    /var/www/journal/static/uploads/issues

# Default command (will be overridden in docker-compose)
CMD ["python", "mainweb/run.py"]
