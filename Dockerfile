# Use official slim Python base image
FROM python:3.10-slim

# Prevent Python from writing .pyc files and enable real-time stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies (for Pillow, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application files
COPY . .

# Expose Flask/Gunicorn port
EXPOSE 5000

# Start the app using Gunicorn (production WSGI server)
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]