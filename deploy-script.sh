#!/bin/bash
# Script deploy helper - có thể chạy thủ công trên server
# Sử dụng script này để test deploy trước khi setup auto-deploy

set -e

# Configuration
REGISTRY="ghcr.io"
IMAGE_NAME="python-web-scraping"
REPO_NAME="OWNER/REPO"  # Thay bằng repo của bạn
GHCR_TOKEN="${GHCR_TOKEN}"  # GitHub PAT token
GHCR_USERNAME="${GHCR_USERNAME}"  # GitHub username
API_KEY="${API_KEY:-XzEcSl7aaW7wfeyxW74IGpGDBcM4noaO}"
DEPLOY_PORT="${DEPLOY_PORT:-8000}"
DATA_VOLUME_PATH="${DATA_VOLUME_PATH:-/app/data}"

echo "🚀 Bắt đầu deploy..."

# Login vào GitHub Container Registry
echo "${GHCR_TOKEN}" | docker login ${REGISTRY} -u ${GHCR_USERNAME} --password-stdin

# Pull image mới nhất
echo "📥 Pulling image..."
docker pull ${REGISTRY}/${REPO_NAME}/${IMAGE_NAME}:latest

# Dừng và xóa container cũ
echo "🛑 Stopping old container..."
docker stop python-web-scraping || true
docker rm python-web-scraping || true

# Chạy container mới
echo "▶️ Starting new container..."
docker run -d \
  --name python-web-scraping \
  --restart unless-stopped \
  -p ${DEPLOY_PORT}:8000 \
  -v ${DATA_VOLUME_PATH}:/app/mycrawler/data \
  -e API_KEY="${API_KEY}" \
  -e RATE_LIMIT_PER_MINUTE="${RATE_LIMIT_PER_MINUTE:-60}" \
  -e ALLOWED_ORIGINS="${ALLOWED_ORIGINS:-http://localhost:3000}" \
  -e ALLOWED_DOMAINS="${ALLOWED_DOMAINS:-openai.com,techcrunch.com,anthropic.com,adobe.com}" \
  ${REGISTRY}/${REPO_NAME}/${IMAGE_NAME}:latest

# Cleanup old images
echo "🧹 Cleaning up old images..."
docker image prune -f

# Kiểm tra container đang chạy
echo "⏳ Waiting for container to start..."
sleep 10

if docker ps | grep -q python-web-scraping; then
  echo "✅ Container đang chạy!"
  
  # Health check
  echo "🏥 Running health check..."
  sleep 5
  if curl -f http://localhost:${DEPLOY_PORT}/ > /dev/null 2>&1; then
    echo "✅ Health check passed!"
    echo "🚀 Deploy thành công!"
    exit 0
  else
    echo "❌ Health check failed!"
    exit 1
  fi
else
  echo "❌ Container không chạy!"
  docker logs python-web-scraping
  exit 1
fi

