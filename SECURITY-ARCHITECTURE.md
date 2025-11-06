# Security Architecture - Crawler API

## 🏗️ Kiến trúc tổng quan

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Request                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Security Middleware Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   CORS       │  │ Rate Limit   │  │  Security    │      │
│  │  Middleware  │→ │  Middleware  │→ │  Headers     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Authentication Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   JWT        │  │  Password    │  │   User       │      │
│  │   Auth       │→ │  Hashing     │→ │   Storage    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Authorization Layer                             │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │   Role       │→ │  Permission  │                        │
│  │   Check      │  │  Validation  │                        │
│  └──────────────┘  └──────────────┘                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Validation Layer                                │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │   Input      │→ │   URL        │                        │
│  │   Sanitize   │  │  Validation  │                        │
│  └──────────────┘  └──────────────┘                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Business Logic Layer                            │
│            (Existing Endpoints)                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Audit Logging                                   │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │   Security   │→ │   Access     │                        │
│  │   Events     │  │   Logs       │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

## 🔐 Security Components

### 1. Authentication Flow

```
User Login
    │
    ├─→ Validate Credentials
    │       │
    │       ├─→ Success → Generate JWT Token
    │       │              │
    │       │              └─→ Return Token
    │       │
    │       └─→ Failure → Return 401
    │
    └─→ Store Token (Client-side)
            │
            └─→ Include in Request Headers
                    │
                    └─→ Verify Token (Every Request)
```

### 2. Authorization Flow

```
Request with Token
    │
    ├─→ Extract Token from Header
    │       │
    │       ├─→ Decode Token
    │       │       │
    │       │       ├─→ Extract User Info
    │       │       │       │
    │       │       │       └─→ Check Role
    │       │       │               │
    │       │       │               ├─→ Admin → Allow
    │       │       │               ├─→ User → Check Permission
    │       │       │               └─→ Public → Allow
    │       │       │
    │       │       └─→ Invalid Token → 401
    │       │
    │       └─→ No Token → 401 (if protected)
```

### 3. Rate Limiting Flow

```
Request
    │
    ├─→ Check Rate Limit (per IP/User)
    │       │
    │       ├─→ Within Limit → Allow → Increment Counter
    │       │
    │       └─→ Exceeded → Return 429
    │
    └─→ Continue to Next Middleware
```

## 📁 File Structure

```
app/
├── main.py                    # FastAPI app entry point
├── config.py                  # Configuration management
│
├── security/
│   ├── __init__.py
│   ├── auth.py                # JWT authentication
│   ├── dependencies.py        # FastAPI dependencies
│   └── password.py            # Password hashing
│
├── middleware/
│   ├── __init__.py
│   ├── rate_limit.py          # Rate limiting
│   ├── security.py            # Security headers
│   └── audit.py                # Audit logging
│
├── models/
│   ├── __init__.py
│   ├── user.py                # User models
│   └── token.py               # Token models
│
└── utils/
    ├── __init__.py
    ├── validation.py          # Input/URL validation
    └── logger.py              # Security logging
```

## 🔑 Key Components

### Authentication Module (`security/auth.py`)
- JWT token generation
- Token verification
- Token refresh logic
- User authentication

### Dependencies (`security/dependencies.py`)
- `get_current_user`: Extract và verify user từ token
- `get_current_admin`: Verify admin role
- `get_optional_user`: Optional authentication

### Rate Limiting (`middleware/rate_limit.py`)
- IP-based rate limiting
- User-based rate limiting
- Configurable limits per endpoint

### Validation (`utils/validation.py`)
- URL validation (whitelist domains, protocol check)
- Input sanitization
- XSS prevention
- SQL injection prevention

### Audit Logging (`middleware/audit.py`)
- Log authentication attempts
- Log API calls với context
- Log security events
- Log file rotation

## 🛡️ Security Layers

### Layer 1: Network Security
- HTTPS enforcement (production)
- CORS configuration
- Security headers

### Layer 2: Application Security
- Authentication (JWT)
- Authorization (Role-based)
- Input validation
- Rate limiting

### Layer 3: Data Security
- Password hashing (bcrypt)
- Token encryption
- Secure storage

### Layer 4: Monitoring & Logging
- Audit logging
- Security event tracking
- Error logging

## 🔄 Request Flow với Security

```
1. Client Request
   ↓
2. CORS Middleware (Check Origin)
   ↓
3. Rate Limiting Middleware (Check Rate Limit)
   ↓
4. Security Headers Middleware (Add Headers)
   ↓
5. Authentication Middleware (Verify Token if needed)
   ↓
6. Authorization Middleware (Check Permissions)
   ↓
7. Input Validation (Sanitize & Validate)
   ↓
8. Business Logic (Process Request)
   ↓
9. Audit Logging (Log Request)
   ↓
10. Response
```

## 📊 Security Metrics

### Metrics to Track:
- Authentication success/failure rate
- Rate limit hits
- Failed authorization attempts
- Invalid token attempts
- Malicious input attempts
- API response times

### Alerts:
- Multiple failed login attempts
- Rate limit exceeded frequently
- Unusual access patterns
- Security anomalies

## 🔒 Secrets Management

### Development:
- `.env` file (gitignored)
- Environment variables

### Production:
- Secrets manager (AWS Secrets Manager, Vault)
- Environment variables từ container orchestrator
- Không hardcode secrets trong code

## 🧪 Security Testing

### Test Categories:
1. **Authentication Tests**
   - Valid/invalid credentials
   - Token expiration
   - Token refresh

2. **Authorization Tests**
   - Role-based access
   - Permission checks

3. **Input Validation Tests**
   - Malicious URLs
   - SQL injection
   - XSS attempts

4. **Rate Limiting Tests**
   - Limit enforcement
   - Different limits per endpoint

5. **Security Headers Tests**
   - Header presence
   - Correct values
