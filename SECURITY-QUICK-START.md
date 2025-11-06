# Security Implementation - Quick Start Guide

## 🚀 Bắt đầu nhanh

Tài liệu này cung cấp hướng dẫn nhanh để bắt đầu implement security cho Crawler API.

## 📋 Prerequisites

- Python 3.11+
- FastAPI đã được cài đặt
- Hiểu cơ bản về JWT và authentication

## ⚡ Quick Steps

### Step 1: Cài đặt Dependencies

Thêm vào `requirements.txt`:

```txt
# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# Rate Limiting
slowapi==0.1.9

# Environment Variables
python-dotenv==1.0.0
```

Chạy:
```bash
pip install -r requirements.txt
```

### Step 2: Tạo .env file

Tạo file `.env` trong root directory:

```env
# JWT Settings
SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# Admin Default (change in production!)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

### Step 3: Tạo cấu trúc thư mục

```bash
mkdir -p app/security app/middleware app/models app/utils
touch app/__init__.py
touch app/security/__init__.py
touch app/middleware/__init__.py
touch app/models/__init__.py
touch app/utils/__init__.py
```

### Step 4: Implement Core Security Files

#### 4.1. `app/config.py` - Configuration

```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    
    # CORS
    allowed_origins: List[str] = []
    
    class Config:
        env_file = ".env"

settings = Settings()
```

#### 4.2. `app/security/password.py` - Password Hashing

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

#### 4.3. `app/security/auth.py` - JWT Authentication

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from app.config import settings

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None
```

#### 4.4. `app/security/dependencies.py` - FastAPI Dependencies

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.security.auth import verify_token

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ"
        )
    return payload
```

### Step 5: Apply Security to Endpoints

```python
from fastapi import Depends
from app.security.dependencies import get_current_user

@app.post("/api/crawl-detail")
async def crawl_detail(
    request: CrawlDetailRequest,
    current_user: dict = Depends(get_current_user)  # Thêm authentication
):
    # Existing logic...
    pass
```

## 🎯 Priority Order

### Must Have (High Priority):
1. ✅ Authentication (JWT)
2. ✅ Input Validation
3. ✅ Rate Limiting
4. ✅ Security Headers

### Should Have (Medium Priority):
5. ✅ CORS Configuration
6. ✅ Audit Logging
7. ✅ Authorization (Role-based)

### Nice to Have (Low Priority):
8. ✅ API Keys
9. ✅ Request Size Limits

## 📝 Next Steps

Sau khi hoàn thành Quick Start, xem:
- `SECURITY-IMPLEMENTATION-PLAN.md` - Chi tiết đầy đủ
- `SECURITY-ARCHITECTURE.md` - Kiến trúc tổng quan

## 🔍 Testing Quick Start

### Test Authentication:
```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Use token
curl -X GET http://localhost:8000/api/listings?type=openai.com \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## ⚠️ Important Notes

1. **Đổi SECRET_KEY** trong production
2. **Đổi ADMIN_PASSWORD** trong production
3. **Không commit .env file**
4. **Sử dụng HTTPS** trong production
5. **Monitor logs** để phát hiện attacks
