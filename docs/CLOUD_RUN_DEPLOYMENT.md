# Cloud Run 自动部署配置指南

本文档说明如何配置 GitHub Actions 自动部署到 Google Cloud Run。

## 📋 前置要求

1. Google Cloud Platform (GCP) 账户
2. 已创建 GCP 项目
3. 已启用 Cloud Run API
4. GitHub 仓库访问权限

## 🔧 配置步骤

### 步骤 1: 创建服务账户

在 Google Cloud Console 中创建服务账户并授予必要权限：

```bash
# 1. 创建服务账户
gcloud iam service-accounts create github-actions-sa \
    --display-name="GitHub Actions Service Account" \
    --project=YOUR_PROJECT_ID

# 2. 授予 Cloud Run Admin 权限
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin"

# 3. 授予 Service Account User 权限
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"

# 4. 授予 Storage Admin 权限（用于构建镜像）
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

# 5. 授予 Cloud Build Service Account 权限
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudbuild.builds.editor"
```

### 步骤 2: 创建并下载服务账户密钥

```bash
# 创建密钥
gcloud iam service-accounts keys create github-actions-key.json \
    --iam-account=github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --project=YOUR_PROJECT_ID

gcloud iam service-accounts keys create github-actions-key.json \
    --iam-account=627774354694-compute@developer.gserviceaccount.com \
    --project=YOUR_PROJECT_ID
```

### 步骤 3: 配置 GitHub Secrets

在 GitHub 仓库中设置以下 Secrets：

1. 进入仓库 → **Settings** → **Secrets and variables** → **Actions**
2. 点击 **New repository secret**
3. 添加以下 secrets：

| Secret 名称 | 说明 | 示例值 |
|------------|------|--------|
| `GCP_PROJECT_ID` | GCP 项目 ID | `srr-project-demo` |
| `GCP_SA_KEY` | 服务账户密钥 JSON（完整内容） | `{"type":"service_account",...}` |

**获取 GCP_SA_KEY：**
- 打开步骤 2 创建的 `github-actions-key.json` 文件
- 复制整个 JSON 内容
- 粘贴到 GitHub Secret 中

### 步骤 4: 配置 Workflow 参数（可选）

编辑 `.github/workflows/cloud-run-deploy.yml`，根据需要修改：

```yaml
env:
  PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  SERVICE_NAME: srr-backend        # Cloud Run 服务名称
  REGION: asia-east1              # 部署区域
```

**可用的区域：**
- `asia-east1` (台湾)
- `asia-northeast1` (东京)
- `us-central1` (爱荷华)
- `europe-west1` (比利时)

### 步骤 5: 调整资源限制（可选）

在 workflow 文件中可以修改以下参数：

```yaml
--memory 2Gi          # 内存限制（1Gi, 2Gi, 4Gi, 8Gi）
--cpu 2               # CPU 数量（1, 2, 4, 8）
--timeout 300         # 请求超时时间（秒）
--max-instances 10    # 最大实例数
```

## 🚀 部署流程

### 自动部署

当您推送代码到 `main` 分支时，如果修改了以下路径的文件，会自动触发部署：

- `backend/**` - 后端代码变更
- `.github/workflows/cloud-run-deploy.yml` - Workflow 配置变更

### 手动触发

1. 进入 GitHub 仓库
2. 点击 **Actions** 标签
3. 选择 **Deploy Backend to Cloud Run** workflow
4. 点击 **Run workflow** 按钮

## 📝 Dockerfile 配置说明

Workflow 使用以下参数指定 Dockerfile 位置：

```bash
--source .                          # 构建上下文：项目根目录
--dockerfile backend/Dockerfile     # Dockerfile 路径
```

这确保了：
- 构建上下文是项目根目录（`.`）
- Dockerfile 位于 `backend/Dockerfile`
- Dockerfile 中的 `COPY` 命令路径正确

## 🔍 验证部署

### 查看部署状态

1. 在 GitHub Actions 中查看 workflow 运行日志
2. 在 Google Cloud Console → Cloud Run 中查看服务状态

### 测试部署的服务

部署完成后，workflow 会输出服务 URL。您也可以手动获取：

```bash
gcloud run services describe srr-backend \
    --region asia-east1 \
    --format 'value(status.url)'
```

### 查看日志

```bash
# 查看 Cloud Run 服务日志
gcloud run services logs read srr-backend \
    --region asia-east1 \
    --limit 50
```

## 🐛 故障排除

### 问题 1: 认证失败

**错误信息：** `Permission denied` 或 `Authentication failed`

**解决方案：**
- 检查 `GCP_SA_KEY` secret 是否正确设置
- 确认服务账户有正确的 IAM 角色
- 验证 `GCP_PROJECT_ID` 是否正确

### 问题 2: Dockerfile 未找到

**错误信息：** `dockerfile not found` 或 `Cannot locate Dockerfile`

**解决方案：**
- 确认 `backend/Dockerfile` 文件存在
- 检查 workflow 中的 `--dockerfile` 参数路径是否正确
- 确认构建上下文是项目根目录（`.`）

### 问题 3: 构建失败

**错误信息：** `Build failed` 或 `Docker build error`

**解决方案：**
- 检查 Dockerfile 语法是否正确
- 确认所有依赖文件路径正确（如 `config/requirements.txt`）
- 查看 GitHub Actions 日志获取详细错误信息

### 问题 4: 部署超时

**错误信息：** `Deployment timeout`

**解决方案：**
- 增加 `--timeout` 参数值
- 检查 Dockerfile 中的构建步骤是否过于耗时
- 考虑使用 Cloud Build 缓存

## 📚 相关资源

- [Cloud Run 文档](https://cloud.google.com/run/docs)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [gcloud CLI 参考](https://cloud.google.com/sdk/gcloud/reference/run/deploy)

## 🔐 安全建议

1. **使用 Workload Identity Federation（推荐）**
   - 比服务账户密钥更安全
   - 无需存储 JSON 密钥
   - 参考：[Workload Identity Federation 设置](https://github.com/google-github-actions/auth#setting-up-workload-identity-federation)

2. **限制服务账户权限**
   - 只授予必要的权限
   - 定期审查 IAM 角色

3. **保护 Secrets**
   - 不要将密钥提交到代码仓库
   - 定期轮换服务账户密钥

---

**最后更新：** 2025-12-06

