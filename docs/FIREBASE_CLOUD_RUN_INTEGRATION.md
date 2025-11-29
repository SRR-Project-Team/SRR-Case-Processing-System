# Firebase前端与Cloud Run后端集成指南

本指南说明如何将已部署在Firebase的前端和已部署在Cloud Run的后端连接起来，使它们能够正常协作。

## 📋 前置条件

- ✅ 前端已部署在Firebase Hosting
- ✅ 后端已部署在Google Cloud Run
- ✅ 已获取Firebase前端URL（例如：`https://your-project.web.app`）
- ✅ 已获取Cloud Run后端URL（例如：`https://your-service-xxx-xx.a.run.app`）

## 🔧 配置步骤

### 步骤1: 配置后端CORS设置

后端需要允许Firebase前端域名访问。在Cloud Run服务中设置环境变量：

1. **登录Google Cloud Console**
   - 访问 [Google Cloud Console](https://console.cloud.google.com)
   - 选择您的项目

2. **进入Cloud Run服务**
   - 导航到 **Cloud Run** > 选择您的后端服务

3. **设置环境变量**
   - 点击 **编辑和部署新版本**
   - 在 **变量和密钥** 标签页中，添加以下环境变量：
   
   ```
   变量名: CORS_ALLOWED_ORIGINS
   变量值: https://srr-demo.web.app/,https://srr-demo.firebaseapp.com/,http://localhost:3000
   ```
   
   **注意**：
   - 将 `your-firebase-app` 替换为您的实际Firebase项目名称
   - 包含多个URL时，用逗号分隔（不要有空格）
   - 建议同时包含 `.web.app` 和 `.firebaseapp.com` 两个域名
   - 保留 `http://localhost:3000` 用于本地开发

4. **部署新版本**
   - 点击 **部署** 保存更改
   - 等待部署完成（通常需要1-2分钟）

### 步骤2: 配置前端API端点

前端需要在构建时设置正确的Cloud Run API URL。

#### 方法1: 使用部署脚本（推荐）

使用提供的部署脚本，它会自动设置环境变量并构建：

```bash
cd frontend/srr-chatbot
./deploy.sh https://your-cloud-run-service-url.run.app
```

#### 方法2: 手动设置环境变量

在构建前设置环境变量：

```bash
# 设置Cloud Run API URL
export REACT_APP_API_URL=https://your-cloud-run-service-url.run.app

# 进入前端目录
cd frontend/srr-chatbot

# 构建生产版本
npm run build

# 返回项目根目录并部署到Firebase
cd ../..
firebase deploy --only hosting
```

#### 方法3: 创建.env.production文件（可选）

在 `frontend/srr-chatbot/` 目录下创建 `.env.production` 文件：

```bash
# .env.production
REACT_APP_API_URL=https://your-cloud-run-service-url.run.app
```

然后正常构建和部署：

```bash
cd frontend/srr-chatbot
npm run build
cd ../..
firebase deploy --only hosting
```

**注意**：`.env.production` 文件包含敏感信息，不应提交到Git仓库。确保 `.gitignore` 已包含此文件。

### 步骤3: 验证连接

部署完成后，验证前后端连接是否正常：

1. **检查后端CORS配置**
   ```bash
   # 测试后端健康检查端点
   curl https://your-cloud-run-service-url.run.app/health
   
   # 应该返回: {"status":"healthy","message":"SRR案件processAPI运行正常，支持TXT和PDF文件"}
   ```

2. **检查前端能否访问后端**
   - 打开Firebase部署的前端URL
   - 打开浏览器开发者工具（F12）
   - 切换到 **Network** 标签页
   - 尝试上传文件或执行操作
   - 检查API请求是否成功（状态码200）
   - 如果出现CORS错误，检查后端CORS配置

3. **测试API端点**
   ```bash
   # 从浏览器控制台测试（在Firebase前端页面）
   fetch('https://your-cloud-run-service-url.run.app/health')
     .then(r => r.json())
     .then(console.log)
   ```

## 🔍 故障排除

### 问题1: CORS错误

**症状**：浏览器控制台显示 `Access-Control-Allow-Origin` 错误

**解决方案**：
1. 确认后端环境变量 `CORS_ALLOWED_ORIGINS` 已正确设置
2. 确认Firebase URL已包含在允许的源列表中（包括协议 `https://`）
3. 确认后端服务已重新部署
4. 检查后端日志确认CORS配置已生效：
   ```bash
   gcloud run services logs read your-service-name --region=your-region
   ```
   查找输出中的 `🌐 CORS允许的源:` 日志

### 问题2: API请求404错误

**症状**：前端无法找到API端点

**解决方案**：
1. 确认 `REACT_APP_API_URL` 环境变量设置正确
2. 确认Cloud Run服务URL正确（包含 `https://` 协议）
3. 确认前端已重新构建和部署
4. 检查浏览器Network标签页，查看实际请求的URL

### 问题3: API请求超时

**症状**：请求长时间无响应

**解决方案**：
1. 检查Cloud Run服务是否正常运行
2. 检查Cloud Run服务的超时设置（建议设置为至少120秒）
3. 检查网络连接
4. 查看Cloud Run日志排查后端问题

### 问题4: 环境变量未生效

**症状**：前端仍使用旧的API URL

**解决方案**：
1. 确认环境变量在构建前设置（React环境变量在构建时编译进代码）
2. 清除浏览器缓存
3. 确认已重新构建前端（`npm run build`）
4. 确认已重新部署到Firebase

## 📝 环境变量参考

### 后端环境变量（Cloud Run）

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `CORS_ALLOWED_ORIGINS` | 允许的前端域名（逗号分隔） | `https://your-app.web.app,https://your-app.firebaseapp.com,http://localhost:3000` |
| `PORT` | 服务端口（Cloud Run自动设置） | `8080` |

### 前端环境变量（构建时）

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `REACT_APP_API_URL` | Cloud Run后端API URL | `https://your-service-xxx-xx.a.run.app` |

## 🔄 更新部署流程

当需要更新部署时，按以下顺序操作：

1. **更新后端**（如果需要）
   - 修改代码
   - 重新部署到Cloud Run
   - 更新CORS配置（如果需要添加新的前端域名）

2. **更新前端**（如果需要）
   - 修改代码
   - 设置 `REACT_APP_API_URL` 环境变量
   - 运行 `npm run build`
   - 运行 `firebase deploy --only hosting`

## 📚 相关文档

- [Firebase Hosting文档](https://firebase.google.com/docs/hosting)
- [Cloud Run文档](https://cloud.google.com/run/docs)
- [FastAPI CORS文档](https://fastapi.tiangolo.com/tutorial/cors/)
- [React环境变量文档](https://create-react-app.dev/docs/adding-custom-environment-variables/)

## ✅ 检查清单

部署前确认：

- [ ] 已获取Firebase前端URL
- [ ] 已获取Cloud Run后端URL
- [ ] 后端CORS环境变量已设置
- [ ] 后端服务已重新部署
- [ ] 前端API URL环境变量已设置
- [ ] 前端已重新构建
- [ ] 前端已重新部署到Firebase
- [ ] 已测试前端能否访问后端API
- [ ] 已检查浏览器控制台无错误
- [ ] 已测试文件上传功能

---

**最后更新**: 2025-01-21  
**版本**: 1.0

