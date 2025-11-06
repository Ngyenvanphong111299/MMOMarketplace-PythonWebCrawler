# Kế hoạch triển khai Security cho Crawler API

## 📋 Tổng quan

Tài liệu này mô tả kế hoạch chi tiết để implement các biện pháp bảo mật cho Crawler API, bao gồm authentication, authorization, rate limiting, và các biện pháp bảo mật khác.

## 🔍 Phân tích hiện trạng

### Các vấn đề bảo mật hiện tại:
1. ❌ Không có authentication/authorization
2. ❌ Không có rate limiting
3. ❌ Không có CORS configuration
4. ❌ Input validation chưa đầy đủ
5. ❌ Không có security headers
6. ❌ Không có audit logging
7. ❌ URL validation yếu (chỉ check `startsWith('http')`)
8. ❌ Không có request size limits
9. ❌ Không có API key management
10. ❌ Không có HTTPS enforcement

### Endpoints phân loại theo mức độ bảo mật:

| Endpoint | Method | Mức độ | Yêu cầu bảo mật |
|----------|--------|--------|-----------------|
| `/` | GET | Public | Rate limiting cơ bản |
| `/api/listings` | GET | Public | Rate limiting |
| `/api/crawl-detail` | POST | Protected | Authentication + Rate limiting |
| `/api/test-scheduler` | GET | Admin | Authentication + Admin role |
| `/api/scheduler-status` | GET | Admin | Authentication + Admin role |

## 🎯 Mục tiêu bảo mật

1. **Authentication**: Xác thực người dùng với JWT tokens hoặc API keys
2. **Authorization**: Phân quyền theo role (user, admin)
3. **Rate Limiting**: Giới hạn số lượng requests
4. **Input Validation**: Validate và sanitize tất cả inputs
5. **Security Headers**: Thêm security headers (CORS, CSP, etc.)
6. **Audit Logging**: Log tất cả security events
7. **URL Validation**: Validate URLs chặt chẽ hơn
8. **Request Size Limits**: Giới hạn kích thước request
9. **Environment Variables**: Quản lý secrets qua environment variables

## 📝 Kế hoạch triển khai

### Phase 1: Setup cơ bản và Dependencies (Ưu tiên cao)

#### 1.1. Thêm dependencies vào `requirements.txt`
- `python-jose[cryptography]` - JWT token handling
- `passlib[bcrypt]` - Password hashing
- `python-multipart` - Form data handling (đã có trong fastapi)
- `slowapi` - Rate limiting
- `email-validator` - Email validation (nếu cần)

#### 1.2. Tạo cấu trúc thư mục
```
python-webScraping/
├── app/
│   ├── __init__.py
│   ├── main.py              # app.py được refactor
│   ├── config.py            # Configuration management
│   ├── security/
│   │   ├── __init__.py
│   │   ├── auth.py          # Authentication logic
│   │   ├── dependencies.py  # FastAPI dependencies
│   │   └── password.py      # Password hashing
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── rate_limit.py    # Rate limiting middleware
│   │   ├── security.py      # Security headers middleware
│   │   └── audit.py         # Audit logging middleware
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py          # User models
│   │   └── token.py         # Token models
│   └── utils/
│       ├── __init__.py
│       ├── validation.py    # URL và input validation
│       └── logger.py        # Security logging
```

#### 1.3. Tạo file `.env.example`
- `SECRET_KEY` - Secret key cho JWT
- `ALGORITHM` - Algorithm cho JWT (HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time
- `API_KEY_PREFIX` - Prefix cho API keys
- `RATE_LIMIT_PER_MINUTE` - Rate limit cho public endpoints
- `RATE_LIMIT_PER_HOUR` - Rate limit cho protected endpoints
- `ALLOWED_ORIGINS` - CORS allowed origins
- `ADMIN_USERNAME` - Default admin username
- `ADMIN_PASSWORD` - Default admin password (hash)

### Phase 2: Configuration Management (Ưu tiên cao)

#### 2.1. Tạo `app/config.py`
- Load environment variables từ `.env`
- Cấu hình JWT settings
- Cấu hình rate limiting
- Cấu hình CORS
- Validation và default values

### Phase 3: Authentication & Authorization (Ưu tiên cao)

#### 3.1. Tạo `app/security/auth.py`
- JWT token generation
- JWT token verification
- Token decode/encode functions
- User authentication logic

#### 3.2. Tạo `app/security/dependencies.py`
- `get_current_user` - Dependency để lấy user từ token
- `get_current_admin` - Dependency để verify admin role
- `get_optional_user` - Dependency cho optional authentication

#### 3.3. Tạo `app/security/password.py`
- Password hashing (bcrypt)
- Password verification

#### 3.4. Tạo `app/models/user.py`
- `User` model (Pydantic)
- `UserInDB` model
- `Token` model
- `TokenData` model

#### 3.5. Tạo endpoints authentication
- `POST /api/auth/login` - Login và nhận token
- `POST /api/auth/register` - Register (optional, có thể disable)
- `POST /api/auth/refresh` - Refresh token
- `GET /api/auth/me` - Lấy thông tin user hiện tại

#### 3.6. Tạo user storage
- Option 1: JSON file (simple, cho development)
- Option 2: SQLite database (recommended)
- Option 3: External database (PostgreSQL, MySQL)

### Phase 4: Rate Limiting (Ưu tiên trung bình)

#### 4.1. Tạo `app/middleware/rate_limit.py`
- Rate limiting middleware với slowapi
- Different limits cho different endpoints
- IP-based rate limiting
- User-based rate limiting (nếu có authentication)

#### 4.2. Cấu hình rate limits
- Public endpoints: 60 requests/minute
- Protected endpoints: 30 requests/minute
- Admin endpoints: 100 requests/hour

### Phase 5: Input Validation & Sanitization (Ưu tiên cao)

#### 5.1. Tạo `app/utils/validation.py`
- URL validation function (check domain, protocol, etc.)
- Input sanitization
- SQL injection prevention (nếu dùng database)
- XSS prevention

#### 5.2. Cập nhật endpoints
- Validate URL trong `/api/crawl-detail` chặt chẽ hơn
- Whitelist domains được phép crawl (optional)
- Validate type parameter

### Phase 6: Security Headers & CORS (Ưu tiên trung bình)

#### 6.1. Tạo `app/middleware/security.py`
- Security headers middleware:
  - X-Content-Type-Options: nosniff
  - X-Frame-Options: DENY
  - X-XSS-Protection: 1; mode=block
  - Strict-Transport-Security (HSTS)
  - Content-Security-Policy
  - Referrer-Policy

#### 6.2. Cấu hình CORS
- Allow specific origins
- Allow specific methods
- Allow specific headers
- Credentials handling

### Phase 7: Audit Logging (Ưu tiên trung bình)

#### 7.1. Tạo `app/middleware/audit.py`
- Log tất cả authentication attempts
- Log tất cả API calls (user, IP, endpoint, timestamp)
- Log security events (failed auth, rate limit exceeded, etc.)
- Log file rotation

#### 7.2. Tạo `app/utils/logger.py`
- Security logger configuration
- Log format với security context
- Log levels cho security events

### Phase 8: Request Size Limits (Ưu tiên thấp)

#### 8.1. Cấu hình FastAPI
- Max request size
- Max upload size
- Body size limits

### Phase 9: API Key Support (Optional - Ưu tiên thấp)

#### 9.1. Tạo API key system
- Generate API keys cho users
- API key authentication
- API key rotation
- API key expiration

### Phase 10: Update Existing Endpoints (Ưu tiên cao)

#### 10.1. Cập nhật endpoints với security
- `GET /api/listings` - Thêm rate limiting
- `POST /api/crawl-detail` - Thêm authentication + improved validation
- `GET /api/test-scheduler` - Thêm admin authentication
- `GET /api/scheduler-status` - Thêm admin authentication

#### 10.2. Refactor `app.py` → `app/main.py`
- Tách code thành modules
- Import security dependencies
- Apply middleware

## 🔧 Chi tiết Implementation

### Dependencies cần thêm:

```txt
# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# Rate Limiting
slowapi==0.1.9

# Environment Variables
python-dotenv==1.0.0

# Database (nếu dùng SQLite)
aiosqlite==0.19.0
sqlalchemy==2.0.23

# Email validation (optional)
email-validator==2.1.0
```

### Security Configuration:

```python
# JWT Settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Rate Limiting
RATE_LIMIT_PER_MINUTE = 60
RATE_LIMIT_PER_HOUR = 1000

# CORS
ALLOWED_ORIGINS = ["http://localhost:3000", "http://localhost:8080"]
```

### User Roles:

1. **Public**: Không cần authentication
   - GET `/api/listings`

2. **User**: Cần authentication
   - POST `/api/crawl-detail`

3. **Admin**: Cần authentication + admin role
   - GET `/api/test-scheduler`
   - GET `/api/scheduler-status`

## 📊 Thứ tự triển khai (Recommended)

1. ✅ Phase 1: Setup cơ bản và Dependencies
2. ✅ Phase 2: Configuration Management
3. ✅ Phase 3: Authentication & Authorization
4. ✅ Phase 5: Input Validation & Sanitization (có thể làm song song với Phase 3)
5. ✅ Phase 10: Update Existing Endpoints
6. ✅ Phase 4: Rate Limiting
7. ✅ Phase 6: Security Headers & CORS
8. ✅ Phase 7: Audit Logging
9. ✅ Phase 8: Request Size Limits
10. ✅ Phase 9: API Key Support (Optional)

## 🧪 Testing Plan

### Security Testing:
1. Test authentication với invalid tokens
2. Test rate limiting
3. Test input validation (malicious URLs, SQL injection, XSS)
4. Test authorization (user không thể access admin endpoints)
5. Test CORS configuration
6. Test security headers

### Test Cases:
- ✅ Login với invalid credentials
- ✅ Access protected endpoints không có token
- ✅ Access admin endpoints với user token
- ✅ Rate limit exceeded scenarios
- ✅ Malicious URL inputs
- ✅ SQL injection attempts
- ✅ XSS attempts

## 📚 Documentation Updates

Cần cập nhật:
1. README.md - Thêm hướng dẫn authentication
2. API documentation - Thêm security requirements
3. Environment variables documentation
4. Deployment guide - Security considerations

## 🔐 Production Considerations

1. **Secrets Management**: Sử dụng secrets manager (AWS Secrets Manager, HashiCorp Vault)
2. **HTTPS**: Enforce HTTPS trong production
3. **Database**: Sử dụng production database (PostgreSQL)
4. **Monitoring**: Setup security monitoring và alerting
5. **Backup**: Backup user data và logs
6. **Updates**: Keep dependencies updated
7. **Penetration Testing**: Periodic security audits

## ⚠️ Lưu ý quan trọng

1. **Không commit secrets**: Sử dụng `.env` và `.gitignore`
2. **Change default credentials**: Đổi mật khẩu admin mặc định
3. **Strong secret key**: Sử dụng secret key mạnh cho JWT
4. **Regular updates**: Update dependencies thường xuyên
5. **Log monitoring**: Monitor security logs để phát hiện attacks
6. **Rate limiting**: Cấu hình rate limits phù hợp với use case

## 📅 Timeline ước tính

- Phase 1-2: 1-2 giờ
- Phase 3: 3-4 giờ
- Phase 5: 1-2 giờ
- Phase 10: 1-2 giờ
- Phase 4, 6, 7: 2-3 giờ mỗi phase
- Phase 8-9: 1-2 giờ mỗi phase (optional)

**Tổng ước tính**: 12-20 giờ cho full implementation

## ✅ Checklist

- [ ] Phase 1: Setup cơ bản
- [ ] Phase 2: Configuration
- [ ] Phase 3: Authentication
- [ ] Phase 4: Rate Limiting
- [ ] Phase 5: Input Validation
- [ ] Phase 6: Security Headers
- [ ] Phase 7: Audit Logging
- [ ] Phase 8: Request Limits
- [ ] Phase 9: API Keys (Optional)
- [ ] Phase 10: Update Endpoints
- [ ] Testing
- [ ] Documentation
