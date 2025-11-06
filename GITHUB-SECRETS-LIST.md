# 📋 Danh sách GitHub Secrets cần cấu hình

## 🔴 Bắt buộc (Required)

### 1. SSH Connection (Để kết nối và deploy lên server)

| Secret Name | Giá trị ví dụ | Mô tả |
|------------|---------------|-------|
| `SSH_HOST` | `192.168.1.100` hoặc `deploy.example.com` | Địa chỉ IP hoặc domain của server |
| `SSH_USERNAME` | `deploy` hoặc `root` | Username để SSH vào server |
| `SSH_PRIVATE_KEY` | Xem bên dưới | SSH private key (toàn bộ nội dung) |
| `SSH_PORT` | `22` | Port SSH (nếu không dùng 22) |

**SSH_PRIVATE_KEY format:**
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAFwAAAAdzc2gtcn
...(nhiều dòng)...
-----END OPENSSH PRIVATE KEY-----
```

### 2. Application Configuration

| Secret Name | Giá trị ví dụ | Mô tả |
|------------|---------------|-------|
| `API_KEY` | `XzEcSl7aaW7wfeyxW74IGpGDBcM4noaO` | **⚠️ Đổi API key này trong production!** |
| `DATA_VOLUME_PATH` | `/app/data` | Đường dẫn trên server để mount data |
| `GHCR_TOKEN` | GitHub PAT token | GitHub Personal Access Token với quyền `read:packages` |

## 🟡 Tùy chọn (Optional - có default values)

| Secret Name | Giá trị ví dụ | Default | Mô tả |
|------------|---------------|---------|-------|
| `DEPLOY_PORT` | `8000` | `8000` | Port để expose API |
| `GHCR_USERNAME` | `your-username` | `github.actor` | GitHub username (nếu dùng PAT) |
| `ALLOWED_ORIGINS` | `https://yourdomain.com` | `http://localhost:3000` | CORS allowed origins |
| `ALLOWED_DOMAINS` | `openai.com,techcrunch.com` | `openai.com,techcrunch.com,...` | Domain whitelist |
| `RATE_LIMIT_PER_MINUTE` | `60` | `60` | Rate limit per minute |
| `DEPLOY_URL` | `https://api.yourdomain.com` | `http://your-server:8000` | URL của deployed API (cho notification) |

## 📝 Cách lấy từng Secret

### SSH_PRIVATE_KEY

**Tạo SSH key pair:**
```bash
# Trên máy local
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_actions_deploy

# Copy public key lên server
ssh-copy-id -i ~/.ssh/github_actions_deploy.pub user@server

# Xem private key để copy vào GitHub Secrets
cat ~/.ssh/github_actions_deploy
```

**Lưu ý:** Copy toàn bộ output, bao gồm `-----BEGIN` và `-----END` lines!

### GHCR_TOKEN (GitHub Personal Access Token)

1. Vào GitHub → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Click **Generate new token (classic)**
3. Chọn scopes:
   - ✅ `read:packages` (để pull images)
4. Copy token và lưu vào secret `GHCR_TOKEN`

**Hoặc:** Có thể dùng `GITHUB_TOKEN` tự động (không cần cấu hình)

### API_KEY

API key cho ứng dụng. **Quan trọng:** Đổi API key này trong production!

Hiện tại: `XzEcSl7aaW7wfeyxW74IGpGDBcM4noaO`

### DATA_VOLUME_PATH

Đường dẫn trên server để lưu data:
- `/app/data`
- `/home/deploy/web-scraping/data`
- `/var/www/web-scraping/data`

**Lưu ý:** Thư mục phải tồn tại và user có quyền write!

## ✅ Checklist cấu hình

### Bước 1: Setup SSH
- [ ] Tạo SSH key pair
- [ ] Copy public key lên server
- [ ] Test SSH connection
- [ ] Thêm `SSH_HOST` vào GitHub Secrets
- [ ] Thêm `SSH_USERNAME` vào GitHub Secrets
- [ ] Thêm `SSH_PRIVATE_KEY` vào GitHub Secrets (full key)
- [ ] Thêm `SSH_PORT` (nếu cần)

### Bước 2: Setup GitHub Container Registry
- [ ] Tạo GitHub PAT với quyền `read:packages`
- [ ] Thêm `GHCR_TOKEN` vào GitHub Secrets
- [ ] Thêm `GHCR_USERNAME` (nếu cần)

### Bước 3: Setup Application
- [ ] Thêm `API_KEY` vào GitHub Secrets (**đổi API key trong production!**)
- [ ] Thêm `DATA_VOLUME_PATH` vào GitHub Secrets
- [ ] Thêm `DEPLOY_PORT` (nếu khác 8000)
- [ ] Thêm `ALLOWED_ORIGINS` (nếu cần)
- [ ] Thêm `ALLOWED_DOMAINS` (nếu cần)
- [ ] Thêm `DEPLOY_URL` (cho notification)

### Bước 4: Setup Server
- [ ] Server có Docker installed
- [ ] User có quyền chạy Docker
- [ ] Thư mục data tồn tại và có quyền write
- [ ] Port không bị block bởi firewall

## 🧪 Test Connection

```bash
# Test SSH
ssh -i ~/.ssh/github_actions_deploy user@server

# Test Docker access
ssh -i ~/.ssh/github_actions_deploy user@server "docker ps"

# Test GitHub Container Registry login
echo "GHCR_TOKEN" | docker login ghcr.io -u USERNAME --password-stdin
```

## 📚 Tài liệu tham khảo

- Xem `GITHUB-SECRETS-GUIDE.md` để biết chi tiết hơn
- Xem `deploy-script.sh` để test deploy thủ công

