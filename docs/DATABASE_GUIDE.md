# 🗄️ data库使用指南

## 📋 概述

SRR案件处理系统采用SQLite数据库存储案件数据，提供完整的数据管理功能。

## 🏗️ 架构设计

### data库结构
```
src/database/
├── __init__.py          # 模块初始化
├── models.py            # 数据模型定义
└── manager.py           # 数据库管理器
```

### 核心组件
- **SRRCase**: 案件数据模型
- **DatabaseManager**: 数据库管理器
- **get_db_manager()**: 全局数据库实例

## 🚀 快速开始

### 1. 基本使用
```python
from src.database import get_db_manager

# getdata库manager
db = get_db_manager()

# save案件
case_data = {
    'A_date_received': '2025-01-15',
    'B_source': 'E-mail',
    'E_caller_name': '张三',
    # ... 其他field
}
case_id = db.save_case(case_data)
```

### 2. query案件
```python
# get单个案件
case = db.get_case(case_id)

# get案件list
cases = db.get_cases(limit=10, offset=0)

# search案件
results = db.search_cases("关键词")
```

### 3. statisticsinformation
```python
# getstatisticsinformation
stats = db.get_stats()
print(f"总案件数: {stats['total_cases']}")
```

## 📊 data模型

### A-Qfieldmap
| 字段 | 描述 | 类型 |
|------|------|------|
| A_date_received | 接收日期 | String(50) |
| B_source | 来源 | String(50) |
| C_case_number | 案件号 | String(50) |
| D_type | 类型 | String(50) |
| E_caller_name | 来电人 | String(100) |
| F_contact_no | 联系电话 | String(50) |
| G_slope_no | 斜坡号 | String(50) |
| H_location | 位置 | String(200) |
| I_nature_of_request | 请求性质 | Text |
| J_subject_matter | 事项主题 | String(100) |
| K_10day_rule_due_date | 10天规则截止 | String(50) |
| L_icc_interim_due | ICC临时回复 | String(50) |
| M_icc_final_due | ICC最终回复 | String(50) |
| N_works_completion_due | 工程完成 | String(50) |
| O1_fax_to_contractor | 传真给承包商 | String(50) |
| O2_email_send_time | 邮件发送时间 | String(50) |
| P_fax_pages | 传真页数 | String(50) |
| Q_case_details | 案件详情 | Text |

### 系统field
| 字段 | 描述 | 类型 |
|------|------|------|
| id | 主键 | Integer |
| original_filename | 原始文件名 | String(255) |
| file_type | 文件类型 | String(20) |
| processing_time | 处理时间 | DateTime |
| created_at | 创建时间 | DateTime |
| updated_at | 更新时间 | DateTime |
| is_active | 是否有效 | Boolean |

## 🛠️ 管理utility

### 命令行utility
```bash
# 显示statisticsinformation
python database_manager.py stats

# 列出案件
python database_manager.py list 10

# search案件
python database_manager.py search "关键词"

# 查看案件详情
python database_manager.py details 1

# exportdata
python database_manager.py export backup.json

# 交互式管理
python database_manager.py
```

### APIinterface
```bash
# get案件list
GET /api/cases?limit=100&offset=0

# get单个案件
GET /api/cases/{case_id}

# search案件
GET /api/cases/search?q=关键词
```

## 📈 performanceoptimize

### 索引建议
```sql
-- 创建常用查询的索引
CREATE INDEX idx_caller_name ON srr_cases(E_caller_name);
CREATE INDEX idx_slope_no ON srr_cases(G_slope_no);
CREATE INDEX idx_file_type ON srr_cases(file_type);
CREATE INDEX idx_created_at ON srr_cases(created_at);
```

### queryoptimize
- 使用limit限制结果数量
- 避免SELECT *，只查询需要的字段
- 使用索引字段进行搜索

## 🔄 data迁移

### exportdata
```python
# export所有案件
cases = db.get_cases(limit=10000)
with open('backup.json', 'w') as f:
    json.dump(cases, f, ensure_ascii=False, indent=2)
```

### importdata
```python
# 从JSONfileimport
with open('backup.json', 'r') as f:
    cases = json.load(f)
    
for case in cases:
    db.save_case(case)
```

## 🛡️ 备份策略

### automatic备份
```bash
#!/bin/bash
# 每日备份脚本
DATE=$(date +%Y%m%d)
cp data/srr_cases.db backups/srr_cases_$DATE.db
```

### 恢复data
```bash
# 从备份恢复
cp backups/srr_cases_20250115.db data/srr_cases.db
```

## 🔧 故障排除

### 常见问题

1. **数据库锁定**
   ```bash
   # check是否有其他进程在使用data库
   lsof data/srr_cases.db
   ```

2. **权限问题**
   ```bash
   # 确保data库file可写
   chmod 664 data/srr_cases.db
   ```

3. **磁盘空间不足**
   ```bash
   # check磁盘空间
   df -h
   ```

### log查看
```python
# 启用SQLAlchemylog
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

## 📚 相关文档

- [数据库解决方案](DATABASE_SOLUTION.md) - 完整的技术方案
- [数据库整理记录](DATABASE_CLEANUP.md) - 模块整理过程
- [API文档](API_DOCUMENTATION.md) - API接口说明
- [部署指南](DEPLOYMENT_GUIDE.md) - 系统部署说明

## 🎯 最佳实践

1. **定期备份** - 每日自动备份数据库
2. **监控性能** - 定期检查查询性能
3. **数据清理** - 定期清理无效数据
4. **索引优化** - 根据查询模式优化索引
5. **版本控制** - 数据库结构变更要记录

---

**数据库模块现在结构清晰、功能完整、易于维护！** 🚀
