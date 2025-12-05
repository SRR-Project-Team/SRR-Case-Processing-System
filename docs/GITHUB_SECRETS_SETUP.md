# GitHub Secrets 配置完成指南

## ✅ 已完成的配置

### 1. 服务账户创建
- **服务账户名称**: `github-actions-sa`
- **服务账户邮箱**: `github-actions-sa@festive-canto-479603-q1.iam.gserviceaccount.com`
- **项目 ID**: `festive-canto-479603-q1`

### 2. 权限配置
已授予以下权限：
- ✅ `roles/run.admin` - Cloud Run 管理权限
- ✅ `roles/iam.serviceAccountUser` - 服务账户用户权限
- ✅ `roles/storage.admin` - 存储管理权限（用于构建镜像）
- ✅ `roles/cloudbuild.builds.editor` - Cloud Build 编辑权限

### 3. 密钥文件
- **密钥文件**: `github-actions-key.json`
- **位置**: 项目根目录
- **状态**: ✅ 已创建并添加到 `.gitignore`

## 📋 下一步：配置 GitHub Secrets

### 步骤 1: 获取密钥内容

```bash
# 查看密钥文件内容（用于复制到 GitHub）
cat github-actions-key.json
```

或者直接打开文件：`github-actions-key.json`

### 步骤 2: 在 GitHub 仓库中设置 Secrets

1. **打开 GitHub 仓库**
   - 进入您的 GitHub 仓库页面

2. **进入 Secrets 设置**
   - 点击仓库顶部的 **Settings**
   - 在左侧菜单找到 **Secrets and variables**
   - 点击 **Actions**

3. **添加 Secret 1: GCP_PROJECT_ID**
   - 点击 **New repository secret**
   - **Name**: `GCP_PROJECT_ID`
   - **Secret**: `festive-canto-479603-q1`
   - 点击 **Add secret**

4. **添加 Secret 2: GCP_SA_KEY**
   - 点击 **New repository secret**
   - **Name**: `GCP_SA_KEY`
   - **Secret**: 粘贴 `github-actions-key.json` 文件的**完整内容**
     - 包括所有 JSON 内容，从 `{` 开始到 `}` 结束
     - 确保格式正确（没有多余的空格或换行）
   - 点击 **Add secret**

### 步骤 3: 验证 Secrets 设置

在 GitHub 仓库中：
- Settings → Secrets and variables → Actions
- 确认两个 secrets 都存在：
  - ✅ `GCP_PROJECT_ID`
  - ✅ `GCP_SA_KEY`

## 🚀 测试部署

配置完成后，可以通过以下方式测试：

### 方式 1: 推送代码触发自动部署

```bash
# 修改 backend 目录下的任何文件
git add backend/
git commit -m "Test Cloud Run deployment"
git push origin main
```

### 方式 2: 手动触发部署

1. 进入 GitHub 仓库
2. 点击 **Actions** 标签
3. 选择 **Deploy Backend to Cloud Run** workflow
4. 点击 **Run workflow** 按钮
5. 选择分支（通常是 `main`）
6. 点击 **Run workflow**

## 📊 查看部署状态

### 在 GitHub Actions 中查看

1. 进入 GitHub 仓库 → **Actions**
2. 点击最新的 workflow 运行
3. 查看部署日志

### 在 Google Cloud Console 中查看

1. 访问 [Google Cloud Console](https://console.cloud.google.com)
2. 选择项目：`festive-canto-479603-q1`
3. 导航到 **Cloud Run**
4. 查看服务状态

### 使用命令行查看

```bash
# 查看 Cloud Run 服务列表
gcloud run services list --project=festive-canto-479603-q1

# 查看服务详细信息
gcloud run services describe srr-backend \
    --region=asia-east2 \
    --project=festive-canto-479603-q1

# 查看服务 URL
gcloud run services describe srr-backend \
    --region=asia-east2 \
    --project=festive-canto-479603-q1 \
    --format='value(status.url)'
```

## 🔍 验证部署配置

### 检查 Workflow 配置

确认 `.github/workflows/cloud-run-deploy.yml` 中的配置：

```yaml
env:
  PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}  # 应该读取到: festive-canto-479603-q1
  SERVICE_NAME: srr-backend                   # Cloud Run 服务名称
  REGION: asia-east2                         # 部署区域
```

### 检查服务名称

如果您的 Cloud Run 服务名称不是 `srr-backend`，需要修改 workflow 文件：

```bash
# 查看现有的 Cloud Run 服务
gcloud run services list --project=festive-canto-479603-q1
```

如果服务名称是 `my-app`，需要修改 workflow 中的 `SERVICE_NAME`。

## 🐛 故障排除

### 问题 1: 认证失败

**错误信息**: `Permission denied` 或 `Authentication failed`

**解决方案**:
- 检查 `GCP_SA_KEY` secret 是否正确设置
- 确认 JSON 格式完整（包括所有引号和括号）
- 验证服务账户权限是否正确授予

### 问题 2: 服务不存在

**错误信息**: `Service srr-backend not found`

**解决方案**:
- 检查服务名称是否正确
- 首次部署会自动创建服务
- 或手动创建服务后再部署

### 问题 3: Dockerfile 未找到

**错误信息**: `dockerfile not found`

**解决方案**:
- 确认 `backend/Dockerfile` 文件存在
- 检查 workflow 中的 `--dockerfile backend/Dockerfile` 路径

## 🔐 安全提醒

1. ✅ **密钥文件已添加到 .gitignore**
   - 文件 `github-actions-key.json` 不会被提交到 Git

2. ⚠️ **不要将密钥内容提交到代码仓库**
   - 密钥内容只应存储在 GitHub Secrets 中

3. 🔄 **定期轮换密钥**
   - 建议每 90 天更换一次服务账户密钥

4. 🗑️ **删除本地密钥文件（可选）**
   ```bash
   # 配置完成后，可以删除本地密钥文件（密钥已保存在 GitHub Secrets 中）
   rm github-actions-key.json
   ```

## 📝 配置总结

| 配置项 | 值 |
|--------|-----|
| 项目 ID | `festive-canto-479603-q1` |
| 服务账户 | `github-actions-sa@festive-canto-479603-q1.iam.gserviceaccount.com` |
| 服务名称 | `srr-backend` |
| 部署区域 | `asia-east2` |
| GitHub Secret 1 | `GCP_PROJECT_ID` |
| GitHub Secret 2 | `GCP_SA_KEY` |

## ✅ 完成检查清单

- [x] 服务账户已创建
- [x] 权限已授予
- [x] 密钥文件已创建
- [x] `.gitignore` 已更新
- [ ] GitHub Secrets 已配置（需要手动完成）
- [ ] 首次部署测试成功

---

**最后更新**: 2025-12-06

