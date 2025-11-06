# Security Implementation - API Key Authentication

## 🔐 Tổng quan

API này sử dụng **API Key Authentication** để bảo vệ các endpoints. API key được hash bằng SHA-256 để bảo mật.

## 🔑 API Key

API Key mặc định: `XzEcSl7aaW7wfeyxW74IGpGDBcM4noaO`

**Lưu ý**: Trong production, hãy đổi API key này và lưu trong file `.env`.

## 📋 Cách sử dụng

### 1. Cấu hình Environment Variables

Tạo file `.env` trong root directory (copy từ `.env.example`):

```env
API_KEY=XzEcSl7aaW7wfeyxW74IGpGDBcM4noaO
API_KEY_HEADER=X-API-Key
```

### 2. Gửi API Key trong Request

Thêm header `X-API-Key` vào request:

```bash
curl -X POST http://localhost:8000/api/crawl-detail \
  -H "Content-Type: application/json" \
  -H "X-API-Key: XzEcSl7aaW7wfeyxW74IGpGDBcM4noaO" \
  -d '{
    "type": "openai.com",
    "url": "https://openai.com/blog/..."
  }'
```

### 3. Endpoints yêu cầu API Key

Các endpoints sau **yêu cầu** API key:

- `POST /api/crawl-detail` - Crawl detail page
- `GET /api/test-scheduler` - Test scheduler
- `GET /api/scheduler-status` - Lấy trạng thái scheduler

### 4. Endpoints công khai (không cần API key)

- `GET /` - Root endpoint
- `GET /api/listings?type={source}` - Lấy danh sách listings

## 🛡️ Các tính năng bảo mật

### 1. API Key Authentication
- API key được hash bằng SHA-256
- So sánh sử dụng constant-time comparison (tránh timing attacks)
- Header name có thể cấu hình

### 2. Rate Limiting
- Public endpoints: 60 requests/minute
- Protected endpoints: 30 requests/minute
- Rate limit headers trong response

### 3. Security Headers
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Content-Security-Policy
- Referrer-Policy

### 4. Input Validation
- URL validation với domain whitelist
- Input sanitization
- Length limits

### 5. CORS
- Cấu hình allowed origins
- Cấu hình allowed methods và headers

## 📝 Error Responses

### 401 Unauthorized
```json
{
  "detail": "API key không được cung cấp. Vui lòng thêm header X-API-Key"
}
```

hoặc

```json
{
  "detail": "API key không hợp lệ"
}
```

### 429 Too Many Requests
```json
{
  "success": false,
  "detail": "Quá nhiều requests. Vui lòng thử lại sau.",
  "retry_after": 60
}
```

## 🔧 Cấu hình nâng cao

Xem file `.env.example` để xem tất cả các cấu hình có thể:

- `RATE_LIMIT_PER_MINUTE` - Rate limit cho public endpoints
- `RATE_LIMIT_PER_HOUR` - Rate limit cho protected endpoints
- `ALLOWED_ORIGINS` - CORS allowed origins
- `ALLOWED_DOMAINS` - Domain whitelist cho URL validation
- `SECURITY_HEADERS_ENABLED` - Bật/tắt security headers
- `RATE_LIMIT_ENABLED` - Bật/tắt rate limiting

## 🧪 Testing

### Test với Python requests:

```python
import requests

headers = {
    "X-API-Key": "XzEcSl7aaW7wfeyxW74IGpGDBcM4noaO",
    "Content-Type": "application/json"
}

# Test protected endpoint
response = requests.post(
    "http://localhost:8000/api/crawl-detail",
    headers=headers,
    json={
        "type": "openai.com",
        "url": "https://openai.com/blog/..."
    }
)

print(response.json())
```

### Test với curl:

```bash
# Test protected endpoint
curl -X POST http://localhost:8000/api/crawl-detail \
  -H "X-API-Key: XzEcSl7aaW7wfeyxW74IGpGDBcM4noaO" \
  -H "Content-Type: application/json" \
  -d '{"type": "openai.com", "url": "https://openai.com/blog/..."}'

# Test public endpoint (không cần API key)
curl http://localhost:8000/api/listings?type=openai.com
```

## ⚠️ Lưu ý bảo mật

1. **Không commit API key** vào git
2. **Đổi API key** trong production
3. **Sử dụng HTTPS** trong production
4. **Monitor logs** để phát hiện attacks
5. **Rotate API keys** định kỳ

## 📚 Cấu trúc code

```
app/
├── security/
│   ├── api_key.py          # API key hashing và verification
│   └── dependencies.py     # FastAPI dependencies
├── middleware/
│   ├── rate_limit.py       # Rate limiting
│   └── security_headers.py # Security headers
├── utils/
│   └── validation.py      # URL và input validation
└── config.py               # Configuration management
```
