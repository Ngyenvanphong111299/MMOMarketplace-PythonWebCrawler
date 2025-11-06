# Hướng dẫn sử dụng Docker

## 🚀 Quick Start

### Sử dụng Docker Compose (Khuyến nghị)
```bash
docker-compose up -d
```

### Sử dụng Docker thông thường
```bash
docker build -t python-web-scraping:latest .
docker run -d --name python-web-scraping -p 8000:8000 \
  -v $(pwd)/mycrawler/data:/app/mycrawler/data \
  python-web-scraping:latest
```

## Yêu cầu
- Docker >= 20.10
- Docker Compose >= 2.0 (hoặc cài đặt riêng)

## Build và chạy với Docker Compose

### 1. Build image
```bash
docker-compose build
```

### 2. Chạy container
```bash
docker-compose up -d
```

### 3. Xem logs
```bash
docker-compose logs -f
```

### 4. Dừng container
```bash
docker-compose down
```

## Build và chạy với Docker thông thường

### 1. Build image
```bash
docker build -t python-web-scraping:latest .
```

### 2. Chạy container
```bash
docker run -d \
  --name python-web-scraping \
  -p 8000:8000 \
  -v $(pwd)/mycrawler/data:/app/mycrawler/data \
  python-web-scraping:latest
```

### 3. Xem logs
```bash
docker logs -f python-web-scraping
```

### 4. Dừng container
```bash
docker stop python-web-scraping
docker rm python-web-scraping
```

## Kiểm tra API

Sau khi container chạy, truy cập:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health check: http://localhost:8000/

## Lưu ý

1. **Data persistence**: Thư mục `mycrawler/data` được mount vào container để dữ liệu được lưu lại giữa các lần chạy.

2. **Port**: Mặc định sử dụng port 8000. Nếu port này đã được sử dụng, có thể thay đổi trong `docker-compose.yml` hoặc khi chạy lệnh `docker run`.

3. **Resource limits**: Nếu cần giới hạn tài nguyên, có thể thêm vào `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
```

4. **Playwright browsers**: Playwright browsers đã được cài đặt trong image. Nếu cần thêm browsers khác, có thể sửa Dockerfile.

5. **Development mode**: Nếu muốn mount code để development với hot reload, uncomment dòng volume trong `docker-compose.yml`:
```yaml
volumes:
  - ./mycrawler/data:/app/mycrawler/data
  - .:/app  # Uncomment dòng này
```
