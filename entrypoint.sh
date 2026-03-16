#!/bin/bash
# PhishHunter entrypoint — starts Xvfb, Fluxbox, x11vnc, NoVNC then runs the command.
# Do NOT use 'set -e' here: we want best-effort startup, not abort on first warning.

export SCREEN_WIDTH=${SCREEN_WIDTH:-1920}
export SCREEN_HEIGHT=${SCREEN_HEIGHT:-1080}
export SCREEN_DEPTH=${SCREEN_DEPTH:-24}
export DISPLAY=:99

# ── 1. Xvfb ─────────────────────────────────────────────────────────────────
echo "🖥️  Starting Xvfb (${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH})..."
Xvfb :99 -screen 0 "${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH}" \
         -ac -nolisten tcp -dpi 96 &
XVFB_PID=$!

# Wait up to 15 s for X server
echo "⏳ Waiting for X server..."
X_READY=0
for i in $(seq 1 15); do
    if xdpyinfo -display :99 >/dev/null 2>&1; then
        echo "✅ X server ready (${i}s)"
        X_READY=1
        break
    fi
    sleep 1
done

if [ "$X_READY" -eq 0 ]; then
    echo "⚠️  X server did not respond in 15s — analysis will continue in headless mode"
fi

# ── 2. Fluxbox window manager ────────────────────────────────────────────────
if [ "$X_READY" -eq 1 ]; then
    echo "🎨 Setting background (dark blue)..."
    xsetroot -solid "#1a1a2e" -display :99 2>/dev/null || true

    echo "🖼️  Starting Fluxbox..."
    fluxbox -display :99 >/dev/null 2>&1 &
    sleep 1   # let fluxbox settle before attaching x11vnc
fi

# ── 3. x11vnc ────────────────────────────────────────────────────────────────
if [ "$X_READY" -eq 1 ]; then
    echo "🔌 Starting x11vnc on :5900..."
    x11vnc -display :99 \
           -forever \
           -shared \
           -nopw \
           -quiet \
           -listen 0.0.0.0 \
           -xkb \
           -noxrecord \
           -noxfixes \
           -noxdamage \
           -rfbport 5900 \
           >/tmp/x11vnc.log 2>&1 &

    # Wait up to 8 s for x11vnc to bind port 5900
    VNC_READY=0
    for i in $(seq 1 8); do
        if ss -lnt 2>/dev/null | grep -q ':5900' || \
           netstat -lnt 2>/dev/null | grep -q ':5900'; then
            echo "✅ x11vnc ready on :5900 (${i}s)"
            VNC_READY=1
            break
        fi
        sleep 1
    done
    [ "$VNC_READY" -eq 0 ] && echo "⚠️  x11vnc may still be starting on :5900"
fi

# ── 4. NoVNC / websockify ────────────────────────────────────────────────────
if [ "$X_READY" -eq 1 ]; then
    echo "🌐 Starting NoVNC (websockify :6080 → :5900)..."
    websockify \
        --web=/usr/share/novnc/ \
        --wrap-mode=ignore \
        --heartbeat=30 \
        6080 localhost:5900 \
        >/tmp/websockify.log 2>&1 &

    sleep 1
    echo "✅ Visual environment ready!"
    echo "   Browser : http://localhost:6080/vnc_lite.html"
    echo "   VNC raw  : localhost:5900"
fi

# ── 5. Execute command or keep alive ─────────────────────────────────────────
if [ -n "$1" ]; then
    echo "🚀 Executing: $*"
    exec "$@"
else
    echo "💤 No command given — container sleeping (connect via NoVNC to debug)"
    tail -f /dev/null
fi
