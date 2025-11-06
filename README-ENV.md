# Hướng dẫn sử dụng .env.example

## 📋 `.env.example` là gì?

`.env.example` là một **template file** (file mẫu) dùng để:

1. **Documentation** - Ghi lại các biến môi trường cần thiết cho project
2. **Template** - Làm mẫu để tạo file `.env` thực tế
3. **Safe to commit** - Có thể commit vào git (không chứa secrets)
4. **Onboarding** - Giúp developer mới biết cần cấu hình gì

## 🔑 Sự khác biệt giữa `.env` và `.env.example`

| File | Mục đích | Có commit vào git? | Chứa secrets? |
|------|----------|---------------------|---------------|
| `.env` | File thực tế chứa giá trị | ❌ KHÔNG | ✅ CÓ (API keys, passwords) |
| `.env.example` | Template/documentation | ✅ CÓ | ❌ KHÔNG (chỉ có tên biến) |

## 📝 Cách sử dụng

### Bước 1: Copy file example
```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

### Bước 2: Chỉnh sửa file `.env`
Mở file `.env` và thay đổi các giá trị theo môi trường của bạn:

```env
# Thay đổi API key thành giá trị thực của bạn
API_KEY=your-actual-api-key-here

# Thay đổi CORS origins theo frontend của bạn
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### Bước 3: Không commit `.env`
Đảm bảo `.env` nằm trong `.gitignore`:

```gitignore
.env
.env.local
.env.*.local
```

## 🎯 Ví dụ cụ thể

### File `.env.example` (template - có thể commit):
```env
# API Key Configuration
API_KEY=your-api-key-here
API_KEY_HEADER=X-API-Key

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
```

### File `.env` (thực tế - KHÔNG commit):
```env
# API Key Configuration
API_KEY=XzEcSl7aaW7wfeyxW74IGpGDBcM4noaO
API_KEY_HEADER=X-API-Key

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
```

## 🔐 Tại sao cần `.env.example`?

### 1. **Bảo mật**
- `.env` chứa secrets → KHÔNG commit
- `.env.example` không có secrets → CÓ thể commit
- Team members biết cần config gì mà không cần secrets

### 2. **Documentation**
- Tự động document các biến môi trường
- Giải thích mục đích của từng biến
- Default values và format

### 3. **Onboarding**
- Developer mới clone project
- Copy `.env.example` → `.env`
- Điền giá trị thực tế
- Không cần hỏi "cần config gì?"

### 4. **Consistency**
- Đảm bảo mọi người dùng cùng structure
- Tránh thiếu biến môi trường
- Dễ maintain và update

## 📚 Best Practices

### ✅ Nên làm:
- Giữ `.env.example` update với code
- Comment rõ ràng cho mỗi biến
- Có giá trị mặc định hợp lý
- Nhóm các biến liên quan

### ❌ Không nên:
- Đặt giá trị thực (secrets) trong `.env.example`
- Commit file `.env` vào git
- Xóa `.env.example` khỏi git
- Thiếu comment giải thích

## 🔄 Workflow

```
1. Developer clone project
   ↓
2. Thấy file .env.example
   ↓
3. Copy .env.example → .env
   ↓
4. Điền giá trị thực tế vào .env
   ↓
5. Chạy ứng dụng (đọc từ .env)
```

## 💡 Lưu ý

1. **Không commit `.env`** - Luôn để trong `.gitignore`
2. **Update `.env.example`** - Khi thêm biến mới, nhớ update example
3. **Documentation** - Comment rõ ràng mục đích của từng biến
4. **Default values** - Code có default values, nhưng `.env.example` giúp rõ ràng hơn

## 📖 Xem thêm

- File `app/config.py` - Nơi đọc các biến môi trường
- File `.env.example` - Template file
- File `README-SECURITY.md` - Hướng dẫn bảo mật
