# GitHub Actions Workflows

Thư mục này chứa các workflow files cho GitHub Actions CI/CD.

## 📋 Workflows

### 1. `ci-cd.yml` - Main CI/CD Pipeline
- **Trigger**: Push/PR vào main/master/develop
- **Jobs**: Build, test, push image, deploy

### 2. `docker-build.yml` - Docker Build và Test
- **Trigger**: Push, tags, PR, manual
- **Jobs**: Build Docker image, test container

### 3. `lint.yml` - Code Quality
- **Trigger**: Push/PR vào main/master/develop
- **Jobs**: Lint code với flake8, black, isort

### 4. `release.yml` - Release Workflow
- **Trigger**: Tạo GitHub Release hoặc manual
- **Jobs**: Build và push release image với version tag

## 🚀 Sử dụng

Workflows sẽ tự động chạy khi:
- Push code lên GitHub
- Tạo Pull Request
- Tạo Release
- Manual trigger (workflow_dispatch)

Xem chi tiết tại: `README-CICD.md`

