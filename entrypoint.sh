#!/bin/bash
# No set -e: we handle errors manually to avoid premature exit

export SCREEN_WIDTH=1920
export SCREEN_HEIGHT=1080
export SCREEN_DEPTH=24
export DISPLAY=:99

echo "Starting Xvfb on :99..."
Xvfb :99 -screen 0 ${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH} -ac +extension GLX +render -noreset &
XVFB_PID=$!

# Wait for X server (up to 15s)
echo "Waiting for X server..."
for i in $(seq 1 15); do
    if xdpyinfo -display :99 >/dev/null 2>&1; then
        echo "X server ready (attempt $i)."
        break
    fi
    sleep 1
done

# Set grey background
xsetroot -solid "#2b2b2b" -display :99 2>/dev/null || true

# Start window manager
fluxbox -display :99 &
sleep 1

echo "Starting x11vnc on port 5900..."
x11vnc -display :99 -forever -shared -nopw -quiet -listen 0.0.0.0 -xkb &
X11VNC_PID=$!

# Wait for VNC port 5900 to be open (up to 15s)
echo "Waiting for VNC port 5900..."
for i in $(seq 1 15); do
    if netstat -tnl 2>/dev/null | grep -q ':5900' || ss -tnl 2>/dev/null | grep -q ':5900'; then
        echo "VNC ready on port 5900 (attempt $i)."
        break
    fi
    sleep 1
done
# Extra buffer for x11vnc to stabilize
sleep 1

echo "Starting NoVNC/websockify on port 6080..."
websockify --web=/usr/share/novnc/ --wrap-mode=ignore --heartbeat=30 6080 localhost:5900 &
NOVNC_PID=$!

sleep 1
echo "================================================"
echo " Visual Environment Ready!"
echo " Browser: http://localhost:6080/"
echo " VNC:     localhost:5900"
echo "================================================"

# Execute the passed command or keep container alive
if [ -n "$1" ]; then
    echo "Executing: $@"
    exec "$@"
else
    echo "Container idle - awaiting docker exec commands."
    tail -f /dev/null
fi
