---
name: apollo-config-sync
description: Apollo配置中心配置拉取工具。当用户需要从Apollo配置中心拉取配置、同步配置、查看配置变化时使用。支持多环境(dev/test/uat/pro)和多模块配置管理。
license: MIT
---

# Apollo配置同步技能

## 技能用途

帮助用户从Apollo配置中心拉取和管理配置文件。适用于以下场景：
- 用户需要拉取Apollo配置
- 用户需要同步某个环境的配置到本地
- 用户需要查看配置的变化
- 用户需要对比不同环境的配置
- 用户需要批量拉取多个模块的配置

## 核心工具脚本

项目中的Apollo配置工具位于：`.claude/skills/apollo-config-sync/scripts/apollo_config_sync.py`

## 使用指南

### 1. 基本使用模式

当用户提出与Apollo配置相关的需求时，你应该：

1. **理解用户需求**
   - 确认要拉取的模块（如：op-api, op-order, op-user等）
   - 确认目标环境（dev/test/uat/pro）
   - 确认要拉取的namespace（如：bootstrap.yml, application.yml等）

2. **执行配置拉取**
   ```powershell
   # 使用快速启动脚本
   cd .specify/skills/apollo-config-sync/scripts
   .\apollo_sync.cmd
   
   # 或者直接使用Python脚本(默认只输出到控制台,不保存文件)
   python apollo_config_sync.py --module op-api --env pro --namespace bootstrap.yml
   
   # 如果需要保存到文件
   python apollo_config_sync.py --module op-api --env pro --namespace bootstrap.yml --save
   ```

3. **查看拉取结果**
   - 默认情况下,配置只输出到控制台,不产生文件
   - 如果使用 `--save` 参数,配置文件保存在：`.claude/skills/apollo-config-sync/scripts/apollo_configs/{env}/{module}/`
   - 日志文件位于：`.claude/skills/apollo-config-sync/scripts/apollo_sync.log`

### 2. 常用命令示例

```powershell
# 拉取op-api模块生产环境配置(仅输出到控制台)
python apollo_config_sync.py --module op-api --env pro

# 拉取并保存配置到文件
python apollo_config_sync.py --module op-api --env pro --save

# 保存配置并生成带时间戳的副本
python apollo_config_sync.py --module op-api --save --save-timestamped

# 拉取op-order模块测试环境配置
python apollo_config_sync.py --module op-order --env test

# 拉取所有可用的namespace
python apollo_config_sync.py --module op-api --all

# 静默模式(不输出到控制台,仅保存文件)
python apollo_config_sync.py --module op-api --no-print --save

# 指定自定义Apollo地址
python apollo_config_sync.py --module op-api --apollo-url http://custom.apollo.com:8080
```

### 3. Python代码集成

如果用户需要在代码中使用Apollo配置，参考 `.claude/skills/apollo-config-sync/scripts/apollo_usage_examples.py`：

```python
from apollo_config_sync import ApolloConfig
import yaml

# 创建Apollo配置实例
apollo = ApolloConfig(
    app_id='op-api',
    cluster='default',
    env='pro'
)

# 拉取配置
result = apollo.fetch_config_without_cache('bootstrap.yml')

if result:
    config = result.get('configurations', {})
    # 解析YAML配置
    yaml_content = config.get('content', '')
    parsed_config = yaml.safe_load(yaml_content)
    
    # 使用配置
    db_url = parsed_config['spring']['datasource']['url']
```

## 前置准备

### 1. 配置Apollo环境地址

在使用此技能前，需要先配置Apollo配置中心的环境地址：

**步骤：**
1. 复制配置模板：`cp config/apollo_env.json.template config/apollo_env.json`
2. 编辑 `config/apollo_env.json` 填写实际的Apollo环境地址：
   ```json
   {
     "environments": {
       "dev": "http://apollo-dev.example.com:8080",
       "test": "http://apollo-test.example.com:8080",
       "uat": "http://apollo-uat.example.com:8080",
       "pro": "http://apollo-pro.example.com:8080"
     },
     "default_cluster": "default",
     "timeout": 10,
     "common_namespaces": [
       "bootstrap.yml",
       "application.yml"
     ],
     "common_modules": [
       "your-module-api",
       "your-module-order"
     ]
   }
   ```
3. 确保配置文件权限正确（仅当前用户可读）

⚠️ **安全提示**：
- 配置文件 `config/apollo_env.json` 包含内部环境地址，已自动被 .gitignore 忽略
- 不要将此文件提交到版本控制系统
- 建议使用内网地址，避免暴露到外网
- 如果Apollo开启了访问控制，请确保有相应的访问权限

### 2. 安装依赖

```bash
pip install requests pyyaml
```

## 使用指南

### 1. 环境配置

配置文件支持自定义环境名称和地址，例如：
```
dev  -> 开发环境（从配置文件读取）
test -> 测试环境（从配置文件读取）
uat  -> UAT环境（从配置文件读取）
pro  -> 生产环境（从配置文件读取）
```

### 2. 支持的模块列表

在配置文件的 `common_modules` 中定义你的模块列表，例如：
- your-module-api（API模块）
- your-module-order（订单模块）
- your-module-user（用户模块）
- oversea-op-api（海外运营API）
- oversea-op-order（海外订单）

## 故障排查

### 常见问题

1. **连接失败**
   - 检查网络连接
   - 验证Apollo地址是否正确
   - 确认环境参数是否正确

2. **认证失败**
   - 确认app_id（模块名）是否正确
   - 检查是否需要secret密钥
   - 验证访问权限

3. **配置为空**
   - 确认namespace名称是否正确
   - 检查该环境下是否已发布配置
   - 查看apollo_sync.log日志文件

### 日志查看

```powershell
# 查看最新日志
Get-Content .claude/skills/apollo-config-sync/scripts/apollo_sync.log -Tail 50

# 实时监控日志
Get-Content .claude/skills/apollo-config-sync/scripts/apollo_sync.log -Wait
```

## 参考文档

- 使用示例：`.claude/skills/apollo-config-sync/scripts/apollo_usage_examples.py`

## 工作流程

当用户请求Apollo配置相关操作时：

1. **确认需求**：明确模块、环境、namespace
2. **切换目录**：`cd .claude/skills/apollo-config-sync/scripts`
3. **执行命令**：根据需求选择合适的命令参数
4. **验证结果**：检查配置文件是否正确生成
5. **提供反馈**：告知用户配置保存位置和关键信息

## 注意事项

- 这是Windows环境，使用PowerShell命令
- 不要使用Linux命令（如 && 等）
- **默认情况下配置只输出到控制台，不保存文件**（避免产生大量临时文件）
- 如果需要保存配置，使用 `--save` 参数
- 如果需要保留历史版本，使用 `--save-timestamped` 参数
- 配置文件包含敏感信息（如数据库密码），注意保护
- 拉取生产环境配置时要特别谨慎
- 建议使用批处理脚本 `apollo_sync.cmd` 进行快速操作
