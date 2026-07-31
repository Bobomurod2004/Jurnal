FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get -o Acquire::Retries=5 -o Acquire::http::Timeout=120 update \
    && apt-get install -y --no-install-recommends \
    libpq-dev \
    postgresql-client \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 120 --retries 5 -r requirements.txt

# Copy project files
COPY . .

# Create upload directories
RUN mkdir -p /var/www/journal/static/uploads/avatars \
    /var/www/journal/static/uploads/articles \
    /var/www/journal/static/uploads/documents \
    /var/www/journal/static/uploads/issues \
    /var/www/journal/private_uploads/articles \
    /var/www/journal/private_uploads/documents \
    /var/www/journal/private_uploads/payments

# Default command (will be overridden in docker-compose)
CMD ["python", "mainweb/run.py"]
