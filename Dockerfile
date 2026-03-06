# Use official Playwright image (includes Python, Browsers, System Deps)
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DISPLAY=:99 \
    DEBIAN_FRONTEND=noninteractive

# Install System Dependencies
# - Java (for CFR/Java analysis)
# - X11/VNC (for visual mode)
# - Network tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jre-headless \
    xvfb \
    x11vnc \
    fluxbox \
    novnc \
    websockify \
    net-tools \
    python3-numpy \
    python3-opencv \
    build-essential \
    dos2unix \
    x11-utils \
    x11-xserver-utils \
    feh \
    xterm \
    zenity \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create index.html redirect to vnc.html for NoVNC webroot
RUN echo '<html><head><meta http-equiv="refresh" content="0; url=vnc.html"></head><body>Redirecting...</body></html>' \
    > /usr/share/novnc/index.html

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Setup Entrypoint
COPY entrypoint.sh /start.sh
RUN dos2unix /start.sh && chmod +x /start.sh

# Create output directory
RUN mkdir -p output/dump && \
    chmod -R 777 output

# Expose ports
EXPOSE 6080 5900

# Entry point
ENTRYPOINT ["/start.sh"]
