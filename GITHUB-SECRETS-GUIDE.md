# Hướng dẫn cấu hình GitHub Secrets cho Auto Deploy

## 📋 Danh sách Secrets cần cấu hình

### 🔴 Bắt buộc (Required)

#### 1. SSH Connection Secrets

| Secret Name | Mô tả | Ví dụ | Cách lấy |
|------------|-------|-------|----------|
| `SSH_HOST` | Địa chỉ IP hoặc domain của server | `192.168.1.100` hoặc `deploy.example.com` | IP/Domain của server production |
| `SSH_USERNAME` | Username để SSH vào server | `root` hoặc `deploy` | Username SSH của server |
| `SSH_PRIVATE_KEY` | SSH private key (full key content) | `-----BEGIN OPENSSH PRIVATE KEY-----...` | Generate SSH key pair và copy private key |
| `SSH_PORT` | Port SSH (optional, default: 22) | `22` hoặc `2222` | Port SSH của server (nếu khác 22) |

#### 2. Application Secrets

| Secret Name | Mô tả | Ví dụ | Default |
|------------|-------|-------|---------|
| `API_KEY` | API key cho ứng dụng | `XzEcSl7aaW7wfeyxW74IGpGDBcM4noaO` | **Bắt buộc** |
| `DEPLOY_PORT` | Port để expose API (optional) | `8000` | `8000` |
| `DATA_VOLUME_PATH` | Đường dẫn mount data trên server | `/app/data` hoặc `/home/user/web-scraping/data` | `/app/data` |

#### 3. Configuration Secrets (Optional)

| Secret Name | Mô tả | Ví dụ | Default |
|------------|-------|-------|---------|
| `ALLOWED_ORIGINS` | CORS allowed origins | `https://yourdomain.com,https://www.yourdomain.com` | `http://localhost:3000` |
| `ALLOWED_DOMAINS` | Domain whitelist cho URL validation | `openai.com,techcrunch.com,anthropic.com,adobe.com` | `openai.com,techcrunch.com,...` |
| `RATE_LIMIT_PER_MINUTE` | Rate limit per minute | `60` | `60` |
| `DEPLOY_URL` | URL của deployed API (cho notification) | `https://api.yourdomain.com` | `http://your-server:8000` |

## 🔧 Cách cấu hình

### Bước 1: Vào GitHub Repository Settings

1. Mở repository trên GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**

### Bước 2: Thêm từng Secret

Thêm từng secret theo danh sách ở trên với tên chính xác.

### Bước 3: Generate SSH Key (nếu chưa có)

```bash
# Trên máy local hoặc server
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_actions_deploy

# Copy public key lên server (authorized_keys)
ssh-copy-id -i ~/.ssh/github_actions_deploy.pub user@server

# Copy private key để thêm vào GitHub Secrets
cat ~/.ssh/github_actions_deploy
```

**Lưu ý**: Copy toàn bộ nội dung private key (bao gồm `-----BEGIN` và `-----END`)

## 📝 Chi tiết từng Secret

### SSH_HOST

Địa chỉ server để deploy:
- IP: `192.168.1.100`
- Domain: `deploy.example.com`
- Localhost (nếu deploy trên GitHub runner): `localhost`

### SSH_USERNAME

Username để SSH:
- `root` (nếu có quyền root)
- `deploy` (recommended - tạo user riêng cho deploy)
- `ubuntu`, `ec2-user` (tùy OS)

### SSH_PRIVATE_KEY

SSH private key đầy đủ:
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAFwAAAAdzc2gtcn
...
(many lines)
...
-----END OPENSSH PRIVATE KEY-----
```

**Quan trọng**: Copy toàn bộ key, bao gồm BEGIN và END lines.

### SSH_PORT

Port SSH (nếu không dùng port 22):
- Default: `22`
- Custom: `2222`, `22022`, etc.

### API_KEY

API key cho ứng dụng (phải khớp với API key trong code):
```
XzEcSl7aaW7wfeyxW74IGpGDBcM4noaO
```

**Lưu ý**: Đổi API key này trong production!

### DEPLOY_PORT

Port để expose API trên server:
- Default: `8000`
- Custom: `8080`, `3000`, etc.

### DATA_VOLUME_PATH

Đường dẫn trên server để mount data:
```
/app/data
/home/user/web-scraping/data
/var/www/web-scraping/data
```

### ALLOWED_ORIGINS

CORS allowed origins (comma-separated):
```
https://yourdomain.com,https://www.yourdomain.com,https://api.yourdomain.com
```

### ALLOWED_DOMAINS

Domain whitelist cho URL validation:
```
openai.com,techcrunch.com,anthropic.com,adobe.com
```

### DEPLOY_URL

URL của deployed API (dùng cho notifications):
```
https://api.yourdomain.com
http://192.168.1.100:8000
```

## 🔐 Security Best Practices

### 1. SSH Key

- ✅ Tạo SSH key riêng cho GitHub Actions
- ✅ Không dùng SSH key cá nhân
- ✅ Chỉ cấp quyền cần thiết cho user
- ✅ Rotate keys định kỳ

### 2. API Key

- ✅ Đổi API key trong production
- ✅ Sử dụng API key mạnh (32+ ký tự)
- ✅ Không commit API key vào code

### 3. Server Setup

- ✅ Tạo user riêng cho deploy (không dùng root)
- ✅ Cấp quyền Docker cho user
- ✅ Setup firewall rules
- ✅ Enable SSH key authentication only

## 📋 Checklist cấu hình

- [ ] SSH_HOST đã được set
- [ ] SSH_USERNAME đã được set
- [ ] SSH_PRIVATE_KEY đã được set (full key)
- [ ] SSH_PORT đã được set (nếu cần)
- [ ] API_KEY đã được set
- [ ] DEPLOY_PORT đã được set (nếu khác 8000)
- [ ] DATA_VOLUME_PATH đã được set
- [ ] ALLOWED_ORIGINS đã được set (nếu cần)
- [ ] ALLOWED_DOMAINS đã được set (nếu cần)
- [ ] DEPLOY_URL đã được set (cho notification)

## 🧪 Test SSH Connection

Test SSH connection trước khi deploy:

```bash
# Test từ máy local
ssh -i ~/.ssh/github_actions_deploy user@server

# Test Docker access
ssh -i ~/.ssh/github_actions_deploy user@server "docker ps"
```

## 📚 Ví dụ cấu hình đầy đủ

### Server: Ubuntu/Debian

```bash
# 1. Tạo user deploy
sudo adduser deploy
sudo usermod -aG docker deploy

# 2. Setup SSH key
sudo mkdir -p /home/deploy/.ssh
sudo chmod 700 /home/deploy/.ssh
# Copy public key vào authorized_keys
sudo nano /home/deploy/.ssh/authorized_keys
sudo chmod 600 /home/deploy/.ssh/authorized_keys
sudo chown -R deploy:deploy /home/deploy/.ssh

# 3. Tạo thư mục data
sudo mkdir -p /app/data
sudo chown -R deploy:deploy /app/data
```

### GitHub Secrets

```
SSH_HOST: 192.168.1.100
SSH_USERNAME: deploy
SSH_PRIVATE_KEY: (full private key)
SSH_PORT: 22
API_KEY: your-production-api-key-here
DEPLOY_PORT: 8000
DATA_VOLUME_PATH: /app/data
ALLOWED_ORIGINS: https://yourdomain.com
DEPLOY_URL: https://api.yourdomain.com
```

## 🚀 Sau khi cấu hình

1. Push code lên branch `main` hoặc `master`
2. GitHub Actions sẽ tự động:
   - Build Docker image
   - Push lên registry
   - Deploy lên server
   - Health check

3. Xem logs tại tab **Actions** trên GitHub

## ⚠️ Troubleshooting

### Lỗi SSH connection failed
- Kiểm tra SSH_HOST và SSH_PORT
- Kiểm tra firewall rules
- Kiểm tra SSH_PRIVATE_KEY có đúng format

### Lỗi Permission denied
- Kiểm tra SSH_USERNAME có đúng
- Kiểm tra user có quyền Docker
- Kiểm tra user có quyền truy cập thư mục data

### Lỗi Docker pull failed
- Kiểm tra GITHUB_TOKEN có quyền read packages
- Kiểm tra image có tồn tại trong registry
- Kiểm tra network connection

