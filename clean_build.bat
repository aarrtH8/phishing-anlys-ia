@echo off
echo 🧹 Cleaning Docker builder cache...
docker builder prune -f

echo 🏗️ Building Docker image (no cache)...
docker-compose build --no-cache

echo 🚀 Starting container...
docker-compose up -d

echo ✅ Done! Access at http://localhost:6080/vnc.html
