# 🚀 Hướng dẫn Push Code lên GitHub

## Bước 1: Tạo Repository trên GitHub

1. Đăng nhập vào GitHub: https://github.com
2. Click vào **"+"** ở góc trên bên phải → **"New repository"**
3. Điền thông tin:
   - **Repository name**: `MMOMarketplace-PythonWebCrawler`
   - **Description**: (tùy chọn) `Python Web Scraping API với Scrapy và FastAPI`
   - **Visibility**: 
     - ✅ **Public** (nếu muốn public)
     - ✅ **Private** (nếu muốn private)
   - **⚠️ KHÔNG TICK** các options:
     - ❌ Add a README file
     - ❌ Add .gitignore
     - ❌ Choose a license
4. Click **"Create repository"**

## Bước 2: Push Code lên GitHub

Sau khi tạo repository, chạy lệnh sau để push code:

```bash
git push -u origin main
```

**Lưu ý:** 
- Nếu dùng SSH key authentication, có thể cần đổi remote URL sang SSH:
  ```bash
  git remote set-url origin git@github.com:Ngyenvanphong111299/MMOMarketplace-PythonWebCrawler.git
  ```

## Bước 3: Kiểm tra

Sau khi push thành công, vào GitHub repository và kiểm tra:
- ✅ Code đã được push
- ✅ Files và folders đúng
- ✅ `.gitignore` hoạt động đúng (không có các file không cần thiết)

## Bước 4: Cấu hình GitHub Secrets (Sau khi push)

Sau khi code đã trên GitHub, cấu hình GitHub Secrets theo `GITHUB-SECRETS-GUIDE.md` để enable auto deploy.

## Troubleshooting

### Lỗi: "Repository not found"
- Đảm bảo repository đã được tạo trên GitHub
- Kiểm tra tên repository chính xác: `MMOMarketplace-PythonWebCrawler`
- Kiểm tra username: `Ngyenvanphong111299`

### Lỗi: "Authentication failed"
- Cần setup authentication:
  - **Option 1**: Personal Access Token (PAT)
    - Tạo PAT: GitHub → Settings → Developer settings → Personal access tokens
    - Sử dụng PAT thay cho password khi push
  - **Option 2**: SSH Key
    - Setup SSH key và dùng SSH URL thay vì HTTPS

### Lỗi: "Permission denied"
- Kiểm tra quyền truy cập repository
- Đảm bảo bạn là owner hoặc có quyền write

