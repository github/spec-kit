# 数据库查询技能

安全地查询MySQL数据库的AI技能，仅支持只读SELECT查询。

## 功能特性

- ✅ 只读查询：仅支持SELECT语句，确保数据安全
- ✅ JSON输出：自动格式化查询结果为JSON格式
- ✅ 中文支持：正确处理中文字符
- ✅ 类型处理：自动处理Decimal和日期时间类型
- ✅ 配置化：数据库连接信息从配置文件读取

## 快速开始

### 1. 配置数据库连接

```bash
# 复制配置模板
cp config/db_config.json.template config/db_config.json

# 编辑配置文件，填入你的数据库连接信息
vim config/db_config.json
```

配置文件格式：
```json
{
  "host": "your-database-host.example.com",
  "port": "3306",
  "user": "your_database_username",
  "password": "your_database_password",
  "database": "your_database_name"
}
```

### 2. 安装依赖

```bash
pip install mysql-connector-python
```

### 3. 使用示例

```bash
cd scripts

# 查询示例
python db_query.py "SELECT * FROM users LIMIT 10"

# 带条件的查询
python db_query.py "SELECT id, name, email FROM users WHERE status = 'active'"

# 聚合查询
python db_query.py "SELECT COUNT(*) as total FROM orders WHERE created_at > '2024-01-01'"
```

## 安全说明

⚠️ **重要安全提示**：

1. **只读查询**：脚本仅允许执行SELECT查询，自动拒绝UPDATE、DELETE、INSERT等修改操作
2. **配置安全**：数据库密码存储在本地配置文件中，不要将 `config/db_config.json` 提交到版本控制系统
3. **权限最小化**：建议为此工具创建只读数据库用户，限制访问权限
4. **生产环境**：在生产环境中使用时，考虑使用环境变量或密钥管理服务

## 输出格式

查询结果以JSON格式输出，示例：

```json
[
    {
        "id": 1,
        "name": "张三",
        "email": "zhangsan@example.com",
        "created_at": "2024-01-15T10:30:00"
    },
    {
        "id": 2,
        "name": "李四",
        "email": "lisi@example.com",
        "created_at": "2024-01-16T14:20:00"
    }
]
```

## 错误处理

脚本会处理以下常见错误：

- 数据库连接失败
- 认证失败（用户名或密码错误）
- 数据库不存在
- SQL语法错误
- 非SELECT查询尝试

所有错误信息会输出到stderr，便于日志分析。

## 技术细节

- **数据库驱动**：mysql-connector-python
- **连接模式**：dictionary模式（结果以字典形式返回）
- **编码**：UTF-8
- **类型转换**：自动转换Decimal和日期时间类型为JSON可序列化格式

## 许可证

MIT License
