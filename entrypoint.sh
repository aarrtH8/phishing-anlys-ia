#!/bin/bash
set -e

# Define screen size
export SCREEN_WIDTH=1920
export SCREEN_HEIGHT=1080
export SCREEN_DEPTH=24
export DISPLAY=:99

echo "🖥️  Starting Xvfb..."
Xvfb :99 -screen 0 ${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH} &

# Wait for Xvfb to be ready
echo "⏳ Waiting for X server..."
for i in {1..10}; do
    if xdpyinfo -display :99 >/dev/null 2>&1; then
        echo "✅ X server is ready!"
        break
    fi
    sleep 1
done

echo "🎨 Setting background..."
# Set solid grey background so user sees SOMETHING instead of black void
xsetroot -solid "#333333" -display :99 || echo "Warning: xsetroot skipped"

echo "🖼️  Starting Fluxbox..."
fluxbox -display :99 &

echo "🔌 Starting x11vnc..."
x11vnc -display :99 -forever -shared -bg -nopw -quiet -listen 0.0.0.0 -xkb

echo "🌐 Starting NoVNC..."
# Use websockify to bridge VNC (5900) to Web (6080) with NoVNC webroot
websockify --web=/usr/share/novnc/ --wrap-mode=ignore --heartbeat=30 6080 localhost:5900 &

echo "✅ Visual Environment Ready!"
echo "👉 Access via Browser: http://localhost:6080/vnc.html"
echo "👉 Access via VNC: localhost:5900"

# Execute the passed command or keep alive
if [ "$1" ]; then
    echo "🚀 Executing command: $@"
    exec "$@"
else
    echo "💤 Sleeping forever (container active)..."
    tail -f /dev/null
fi
