# ✅ Checklist GitHub Secrets cho Auto Deploy

## 🔴 Bắt buộc (Required)

### SSH Connection
- [ ] **SSH_HOST** - Địa chỉ IP/domain của server (ví dụ: `192.168.1.100` hoặc `deploy.example.com`)
- [ ] **SSH_USERNAME** - Username để SSH (ví dụ: `root`, `deploy`, `ubuntu`)
- [ ] **SSH_PRIVATE_KEY** - SSH private key (toàn bộ nội dung, bao gồm BEGIN và END lines)
- [ ] **SSH_PORT** - Port SSH (optional, default: `22`)

### Application Configuration
- [ ] **API_KEY** - API key cho ứng dụng (ví dụ: `XzEcSl7aaW7wfeyxW74IGpGDBcM4noaO`)
- [ ] **DEPLOY_PORT** - Port để expose API (optional, default: `8000`)
- [ ] **DATA_VOLUME_PATH** - Đường dẫn mount data trên server (ví dụ: `/app/data`)

### GitHub Container Registry
- [ ] **GHCR_TOKEN** - GitHub Personal Access Token với quyền `read:packages` (hoặc dùng GITHUB_TOKEN tự động)
- [ ] **GHCR_USERNAME** - GitHub username (optional, default: dùng github.actor)

## 🟡 Tùy chọn (Optional)

### Configuration
- [ ] **ALLOWED_ORIGINS** - CORS allowed origins (comma-separated)
- [ ] **ALLOWED_DOMAINS** - Domain whitelist cho URL validation
- [ ] **RATE_LIMIT_PER_MINUTE** - Rate limit per minute (default: `60`)
- [ ] **DEPLOY_URL** - URL của deployed API (cho notification)

## 📝 Hướng dẫn từng bước

### Bước 1: Tạo SSH Key Pair

```bash
# Trên máy local
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_actions_deploy

# Copy public key lên server
ssh-copy-id -i ~/.ssh/github_actions_deploy.pub user@server

# Xem private key để copy vào GitHub Secrets
cat ~/.ssh/github_actions_deploy
```

### Bước 2: Tạo GitHub Personal Access Token (PAT)

1. Vào GitHub → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Click **Generate new token (classic)**
3. Chọn scopes:
   - ✅ `read:packages` (để pull images từ GitHub Container Registry)
   - ✅ `write:packages` (nếu cần push images)
4. Copy token và lưu vào secret `GHCR_TOKEN`

### Bước 3: Thêm Secrets vào GitHub

1. Vào repository → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Thêm từng secret theo checklist ở trên

## 🔐 Chi tiết từng Secret

### SSH_HOST
```
192.168.1.100
```
hoặc
```
deploy.example.com
```

### SSH_USERNAME
```
deploy
```
hoặc
```
root
```

### SSH_PRIVATE_KEY
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAFwAAAAdzc2gtcn
...
(nhiều dòng)
...
-----END OPENSSH PRIVATE KEY-----
```
**Lưu ý**: Copy toàn bộ key, bao gồm BEGIN và END lines!

### SSH_PORT
```
22
```
hoặc
```
2222
```

### API_KEY
```
XzEcSl7aaW7wfeyxW74IGpGDBcM4noaO
```
**⚠️ Đổi API key này trong production!**

### DEPLOY_PORT
```
8000
```

### DATA_VOLUME_PATH
```
/app/data
```
hoặc
```
/home/deploy/web-scraping/data
```

### GHCR_TOKEN
GitHub Personal Access Token với quyền `read:packages`

### GHCR_USERNAME
GitHub username (nếu không dùng PAT, có thể để trống để dùng github.actor)

### ALLOWED_ORIGINS
```
https://yourdomain.com,https://www.yourdomain.com
```

### ALLOWED_DOMAINS
```
openai.com,techcrunch.com,anthropic.com,adobe.com
```

### DEPLOY_URL
```
https://api.yourdomain.com
```
hoặc
```
http://192.168.1.100:8000
```

## 🧪 Test sau khi cấu hình

1. Push code lên branch `main` hoặc `master`
2. Vào tab **Actions** trên GitHub
3. Xem workflow chạy và kiểm tra logs
4. Nếu có lỗi, kiểm tra lại secrets

## ⚠️ Lưu ý quan trọng

1. **SSH_PRIVATE_KEY**: Phải copy toàn bộ key, không được thiếu dòng
2. **API_KEY**: Đổi API key trong production, không dùng key mặc định
3. **GHCR_TOKEN**: Cần quyền `read:packages` để pull images
4. **SSH_USERNAME**: Nên tạo user riêng cho deploy, không dùng root
5. **DATA_VOLUME_PATH**: Phải tồn tại trên server và user có quyền write

