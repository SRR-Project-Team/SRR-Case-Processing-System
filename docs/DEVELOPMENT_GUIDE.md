# 🛠️ 开发指南

## 📋 概述

本文档提供SRR案件处理系统的开发、调试和维护指南。

## 🚀 快速开始

### 环境准备
```bash
# 安装Python依赖
pip install -r config/requirements.txt
pip install -r config/requirements_ocr.txt

# 安装Node.js依赖
cd frontend/srr-chatbot
npm install
```

### 启动开发环境
```bash
# 启动系统（实时日志模式）
python start.py start --logs
```

## 🔧 开发工具

### 启动脚本
- **实时日志**: `python start.py start --logs`
- **静默模式**: `python start.py start`
- **系统检查**: `python start.py check`
- **进程清理**: `python start.py cleanup`

### 数据库管理
```bash
# 查看统计信息
python database_manager.py stats

# 列出案件
python database_manager.py list 10

# 搜索案件
python database_manager.py search "关键词"

# 导出数据
python database_manager.py export backup.json
```

## 📊 日志和调试

### 日志级别
- **INFO**: 正常操作信息
- **WARNING**: 警告信息
- **ERROR**: 错误信息

### 调试技巧
1. **使用实时日志模式**进行开发调试
2. **查看浏览器控制台**了解前端错误
3. **检查数据库状态**验证数据完整性
4. **监控API请求**确保接口正常

## 🗄️ 数据库开发

### 模型定义
```python
# src/database/models.py
class SRRCase(Base):
    __tablename__ = "srr_cases"
    # A-Q字段定义
```

### 数据库操作
```python
# 获取数据库管理器
from src.database import get_db_manager
db = get_db_manager()

# 保存案件
case_id = db.save_case(case_data)

# 查询案件
case = db.get_case(case_id)
```

## 🔄 文件处理开发

### 添加新的文件类型
1. 在 `src/core/` 目录创建新的提取器
2. 在 `src/api/main.py` 添加处理逻辑
3. 更新 `src/core/output.py` 的数据模型

### OCR开发
```python
# 使用EasyOCR
import easyocr
reader = easyocr.Reader(['en', 'ch_sim', 'ch_tra'])
results = reader.readtext(image)
```

## 🎨 前端开发

### 组件开发
```typescript
// src/components/NewComponent.tsx
import React from 'react';

interface Props {
  // 属性定义
}

const NewComponent: React.FC<Props> = ({ ... }) => {
  // 组件逻辑
  return <div>...</div>;
};
```

### API集成
```typescript
// src/services/api.ts
export const processFile = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await axios.post('/api/process-srr-file', formData);
  return response.data;
};
```

## 🧪 测试

### 单元测试
```python
# tests/test_module.py
import unittest
from src.module import function

class TestModule(unittest.TestCase):
    def test_function(self):
        result = function()
        self.assertEqual(result, expected)
```

### 集成测试
```bash
# 测试API端点
curl -X POST http://localhost:8001/api/process-srr-file \
  -F "file=@test.txt"
```

## 📈 性能优化

### 后端优化
- 使用数据库索引
- 优化OCR参数
- 实现模型缓存

### 前端优化
- 组件懒加载
- 图片压缩
- 请求去重

## 🔍 问题排查

### 常见问题
1. **端口占用**: 使用 `python start.py cleanup`
2. **依赖缺失**: 运行 `python start.py check`
3. **数据库错误**: 检查数据库文件权限
4. **OCR失败**: 检查图片质量和格式

### 调试步骤
1. 检查系统状态
2. 查看日志输出
3. 验证数据完整性
4. 测试API接口

## 📚 相关文档

- [API文档](API_DOCUMENTATION.md)
- [数据库指南](DATABASE_GUIDE.md)
- [系统功能](SYSTEM_FEATURES.md)
- [部署指南](DEPLOYMENT_GUIDE.md)

---

**作者**: Project3 Team  
**版本**: 2.0  
**更新时间**: 2025-01-15
