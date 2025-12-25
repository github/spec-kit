---
name: database-query
description: 数据库查询工具。当用户需要查询MySQL数据库、执行SELECT语句、查看数据库数据时使用。支持安全的只读查询，自动格式化输出JSON结果。
license: MIT
---

# 数据库查询技能

## 技能用途

帮助用户安全地执行MySQL数据库查询操作。适用于以下场景：
- 用户需要查询数据库中的数据
- 用户需要验证某条数据是否存在
- 用户需要查看表结构或数据样本
- 用户需要统计分析数据
- 用户需要导出查询结果

## 核心工具脚本

项目中的数据库查询工具位于：`.claude/skills/database-query/scripts/db_query.py`

## 安全特性

**重要**：此工具仅支持 SELECT 查询，禁止任何修改数据的操作（INSERT/UPDATE/DELETE/DROP等），确保数据安全。

## 前置准备

### 1. 配置数据库连接

在使用此技能前，需要先配置数据库连接信息：

**步骤：**
1. 复制配置模板：`cp config/db_config.json.template config/db_config.json`
2. 编辑 `config/db_config.json` 填写数据库连接信息：
   ```json
   {
     "host": "your-database-host.example.com",
     "port": "3306",
     "user": "your_database_username",
     "password": "your_database_password",
     "database": "your_database_name"
   }
   ```
3. 确保配置文件权限正确（仅当前用户可读）

⚠️ **安全提示**：
- 配置文件 `config/db_config.json` 包含敏感信息，已自动被 .gitignore 忽略
- 不要将此文件提交到版本控制系统
- 建议为此工具创建只读数据库用户
- 在生产环境中考虑使用环境变量或密钥管理服务

### 2. 安装依赖

```bash
pip install mysql-connector-python
```

## 使用指南

### 1. 基本使用

```powershell
# 切换到scripts目录
cd .claude\skills\database-query\scripts

# 执行简单查询
python db_query.py "SELECT * FROM table_name LIMIT 10"

# 查询特定字段
python db_query.py "SELECT id, name, create_time FROM users WHERE status = 1"

# 统计查询
python db_query.py "SELECT COUNT(*) as total FROM orders WHERE create_time > '2024-01-01'"
```

### 2. 常用查询场景

#### 查看表数据
```powershell
# 查看表的前10条记录
python db_query.py "SELECT * FROM op_order LIMIT 10"

# 查看特定订单
python db_query.py "SELECT * FROM op_order WHERE order_no = '202401010001'"
```

#### 数据统计
```powershell
# 统计订单总数
python db_query.py "SELECT COUNT(*) as total FROM op_order"

# 按状态统计
python db_query.py "SELECT status, COUNT(*) as count FROM op_order GROUP BY status"

# 查看今日新增订单
python db_query.py "SELECT COUNT(*) FROM op_order WHERE DATE(create_time) = CURDATE()"
```

#### 关联查询
```powershell
# 查询订单及其明细
python db_query.py "SELECT o.order_no, o.total_amount, d.product_name FROM op_order o LEFT JOIN op_order_detail d ON o.id = d.order_id WHERE o.id = 123"
```

#### 查看表结构
```powershell
# 查看表的列信息
python db_query.py "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = 'op' AND TABLE_NAME = 'op_order'"

# 查看表的索引
python db_query.py "SELECT * FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = 'op' AND TABLE_NAME = 'op_order'"
```

### 3. 输出格式

查询结果会以格式化的JSON输出：
```json
[
    {
        "id": 1,
        "order_no": "202401010001",
        "total_amount": 1000.50,
        "status": 1,
        "create_time": "2024-01-01T10:30:00"
    },
    {
        "id": 2,
        "order_no": "202401010002",
        "total_amount": 2500.00,
        "status": 2,
        "create_time": "2024-01-01T11:15:00"
    }
]
```

### 4. 高级用法

#### 处理大数据量
```powershell
# 使用LIMIT分页
python db_query.py "SELECT * FROM op_order ORDER BY id LIMIT 100 OFFSET 0"

# 使用条件过滤减少结果集
python db_query.py "SELECT * FROM op_order WHERE create_time > '2024-01-01' AND status = 1"
```

#### 复杂查询
```powershell
# 子查询
python db_query.py "SELECT * FROM op_order WHERE user_id IN (SELECT id FROM op_user WHERE vip_level > 3)"

# 聚合函数
python db_query.py "SELECT DATE(create_time) as date, SUM(total_amount) as daily_total FROM op_order GROUP BY DATE(create_time)"
```

## 工作流程

当用户需要查询数据库时：

1. **理解查询需求**
   - 确认要查询的表名
   - 确认查询条件
   - 确认需要返回的字段

2. **构建SQL语句**
   - 编写SELECT查询语句
   - 添加必要的WHERE条件
   - 考虑使用LIMIT限制结果集大小

3. **执行查询**
   ```powershell
   cd .claude/skills/database-query/scripts
   python db_query.py "YOUR_SQL_QUERY"
   ```

4. **分析结果**
   - 查看返回的JSON数据
   - 解释结果含义
   - 根据需要进行进一步查询

## 故障排查

### 常见错误

1. **连接失败**
   ```
   错误: 用户名或密码不正确
   ```
   - 检查db_query.py中的数据库配置
   - 确认网络连接正常

2. **查询被拒绝**
   ```
   错误: 出于安全考虑，只允许执行 SELECT 查询
   ```
   - 确认SQL语句以SELECT开头
   - 不要尝试执行修改操作

3. **语法错误**
   ```
   执行查询时发生错误: ...
   ```
   - 检查SQL语法是否正确
   - 确认表名、字段名是否存在
   - 注意SQL关键字大小写

### 调试技巧

```powershell
# 先验证表是否存在
python db_query.py "SHOW TABLES LIKE 'op_order'"

# 查看表结构
python db_query.py "DESC op_order"

# 测试连接
python db_query.py "SELECT 1"
```

## 安全注意事项

⚠️ **重要提醒**：

1. **只读访问**：该工具仅允许SELECT查询，确保数据安全
2. **密码保护**：数据库密码硬编码在脚本中，注意保护脚本文件
3. **生产数据**：当前连接的是生产数据库，查询时要谨慎
4. **结果集大小**：大表查询时务必使用LIMIT限制结果数量
5. **敏感信息**：查询结果可能包含敏感信息，注意保护

## 最佳实践

1. **总是使用LIMIT**
   ```sql
   SELECT * FROM large_table LIMIT 100
   ```

2. **使用索引字段作为条件**
   ```sql
   SELECT * FROM op_order WHERE id = 123  -- id是主键
   ```

3. **避免SELECT ***
   ```sql
   SELECT id, order_no, status FROM op_order  -- 只查询需要的字段
   ```

4. **先测试小范围**
   ```sql
   -- 先查一条看结构
   SELECT * FROM op_order LIMIT 1
   ```

## 常见表清单

ECP项目中的主要表：
- `op_order` - 订单表
- `op_order_detail` - 订单明细表
- `op_user` - 用户表
- `op_product` - 产品表
- `op_approval` - 审批表
- `op_channel` - 渠道表
- `global_table` - Seata全局事务表
- `branch_table` - Seata分支事务表
- `lock_table` - Seata锁表

## Python集成示例

如果需要在其他Python脚本中使用：

```python
import subprocess
import json

def query_database(sql):
    """执行数据库查询"""
    result = subprocess.run(
        ['python', '.claude/skills/database-query/scripts/db_query.py', sql],
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    
    if result.returncode == 0:
        # 解析JSON输出
        lines = result.stdout.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('['):
                json_str = '\n'.join(lines[i:])
                return json.loads(json_str)
    return None

# 使用示例
data = query_database("SELECT * FROM op_order LIMIT 5")
if data:
    for row in data:
        print(f"订单号: {row['order_no']}")
```

## 注意事项

- Windows环境，使用PowerShell
- 查询结果中文能正常显示
- Decimal和日期类型会自动转换为JSON可序列化格式
- 大结果集建议导出到文件或使用分页查询
