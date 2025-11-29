#!/bin/bash
# Firebase部署脚本 - 设置环境变量并构建
# 使用方法: ./deploy.sh <your-cloud-run-url>

if [ -z "$1" ]; then
    echo "❌ 错误: 请提供Cloud Run后端URL"
    echo "使用方法: ./deploy.sh <your-cloud-run-url>"
    echo "示例: ./deploy.sh https://your-service-xxx-xx.a.run.app"
    exit 1
fi

CLOUD_RUN_URL=$1

echo "🚀 开始部署到Firebase..."
echo "📡 Cloud Run API URL: $CLOUD_RUN_URL"

# 设置环境变量并构建
export REACT_APP_API_URL=$CLOUD_RUN_URL
cd "$(dirname "$0")"
npm run build

if [ $? -eq 0 ]; then
    echo "✅ 构建成功"
    echo "📤 部署到Firebase..."
    cd ../..
    firebase deploy --only hosting
else
    echo "❌ 构建失败"
    exit 1
fi

