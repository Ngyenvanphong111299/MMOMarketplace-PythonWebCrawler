# GitHub Actions CI/CD Pipeline

## 📋 Tổng quan

Dự án này sử dụng GitHub Actions để tự động:
- Build Docker image
- Test code và Docker image
- Push image lên GitHub Container Registry
- Deploy (optional)

## 🔄 Workflows

### 1. CI/CD Pipeline (`ci-cd.yml`)

**Trigger:**
- Push vào `main`, `master`, `develop`
- Pull requests vào `main`, `master`, `develop`

**Jobs:**
1. **build-and-test**: Build và test Docker image
2. **build-and-push**: Build và push image lên GitHub Container Registry (chỉ khi push vào main/master)
3. **deploy**: Deploy notification (có thể cấu hình auto-deploy)

### 2. Docker Build (`docker-build.yml`)

**Trigger:**
- Push vào `main`, `master`
- Push tags `v*`
- Pull requests
- Manual trigger (workflow_dispatch)

**Chức năng:**
- Build Docker image
- Test image với các API endpoints
- Verify API key authentication

### 3. Lint và Code Quality (`lint.yml`)

**Trigger:**
- Push vào `main`, `master`, `develop`
- Pull requests

**Chức năng:**
- Check code formatting với Black
- Check import sorting với isort
- Lint code với flake8

### 4. Release (`release.yml`)

**Trigger:**
- Tạo GitHub Release
- Manual trigger với version input

**Chức năng:**
- Build và push image với version tag
- Tag image với version và latest

## 🚀 Cách sử dụng

### 1. Push code lên GitHub

```bash
git add .
git commit -m "Update code"
git push origin main
```

GitHub Actions sẽ tự động chạy workflows.

### 2. Tạo Release

```bash
# Tạo tag
git tag v1.0.0
git push origin v1.0.0

# Hoặc tạo release trên GitHub UI
```

### 3. Pull Docker image từ GitHub Container Registry

```bash
# Login
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Pull image
docker pull ghcr.io/OWNER/REPO/python-web-scraping:latest
```

## 🔐 Cấu hình Secrets

### GitHub Secrets (nếu cần deploy tự động)

1. Vào **Settings** → **Secrets and variables** → **Actions**
2. Thêm các secrets:
   - `SSH_HOST`: Server host để deploy
   - `SSH_USERNAME`: SSH username
   - `SSH_KEY`: SSH private key

### GitHub Container Registry

GitHub Container Registry sử dụng `GITHUB_TOKEN` tự động, không cần cấu hình thêm.

## 📊 Workflow Status

Xem trạng thái workflows tại:
- **Actions** tab trên GitHub repository
- Badge có thể thêm vào README:

```markdown
![CI/CD](https://github.com/OWNER/REPO/workflows/CI/CD%20Pipeline/badge.svg)
```

## 🧪 Test trong CI/CD

Workflow sẽ tự động test:
- ✅ Docker image build thành công
- ✅ Container chạy được
- ✅ Root endpoint hoạt động
- ✅ API key authentication hoạt động
- ✅ Protected endpoints yêu cầu API key

## 📝 Cấu trúc Workflows

```
.github/
└── workflows/
    ├── ci-cd.yml          # Main CI/CD pipeline
    ├── docker-build.yml   # Docker build và test
    ├── lint.yml           # Code quality checks
    └── release.yml        # Release workflow
```

## 🔧 Tùy chỉnh

### Thay đổi Registry

Sửa trong workflow files:
```yaml
env:
  REGISTRY: docker.io  # Thay vì ghcr.io
  REGISTRY_USERNAME: ${{ secrets.DOCKER_USERNAME }}
  REGISTRY_PASSWORD: ${{ secrets.DOCKER_PASSWORD }}
```

### Thêm Test Cases

Thêm vào `docker-build.yml`:
```yaml
- name: Run custom tests
  run: |
    docker run --rm ${{ env.IMAGE_NAME }}:${{ github.sha }} \
      python -m pytest tests/
```

### Deploy tự động

Uncomment và cấu hình phần deploy trong `ci-cd.yml`:
```yaml
- name: Deploy to server
  uses: appleboy/ssh-action@master
  with:
    host: ${{ secrets.SSH_HOST }}
    # ...
```

## 📚 Tài liệu tham khảo

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Buildx Action](https://github.com/docker/build-push-action)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)

