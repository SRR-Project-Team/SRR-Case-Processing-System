# Contributing to SRR Case Processing System

我们欢迎社区贡献！请遵循以下指南。

## 🚀 快速开始

1. Fork 这个仓库
2. 创建您的功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

## 📋 开发指南

### 环境设置
```bash
# 克隆仓库
git clone https://github.com/[USERNAME]/SRR-Case-Processing-System.git
cd SRR-Case-Processing-System

# 安装依赖
pip install -r requirements.txt
cd frontend/srr-chatbot && npm install

# 启动系统
python start.py
```

### 代码规范
- 使用 Python PEP 8 编码规范
- React 组件使用 TypeScript
- 为新功能添加测试
- 保持文档更新

### 测试
```bash
# 运行系统检查
python start.py check

# 清理测试文件
python start.py cleanup
```

## 🐛 报告问题

请使用 GitHub Issues 报告问题，包含：
- 详细的问题描述
- 复现步骤
- 预期行为
- 系统环境信息

## 💡 功能建议

我们欢迎新功能建议！请先创建一个 Issue 讨论：
- 功能描述
- 使用场景
- 实现思路

## 📝 文档贡献

文档改进同样重要：
- 修正错误
- 添加示例
- 改进说明

感谢您的贡献！🙏
