# Use Python 3.11 slim as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies including OpenJDK 17 (for cfr.jar) and dependencies for Playwright/OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN groupadd -r phishhunter && useradd -r -g phishhunter -m -d /home/phishhunter phishhunter

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (chromium only to save space) and system deps
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy project code
COPY . .

# Create directory for downloads/artifacts and set permissions
RUN mkdir -p output/dump && \
    chown -R phishhunter:phishhunter /app

# Switch to non-root user
USER phishhunter

# Entry point
ENTRYPOINT ["python", "main.py"]
