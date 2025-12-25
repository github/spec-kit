# Apollo配置同步工具 (Apollo Config Sync)

> 从Apollo配置中心拉取和管理配置文件的自动化工具

## 📋 概述

Apollo配置同步工具帮助开发者快速从Apollo配置中心拉取配置文件到本地。支持多环境(dev/test/uat/pro)和多模块配置管理，适用于配置查看、对比、备份等场景。

本技能封装了Apollo配置中心的API调用，提供简洁的命令行接口和Python集成方式。

## ✨ 主要功能

- ✅ 支持多环境配置拉取（dev/test/uat/pro）
- ✅ 支持多模块批量操作（op-api, op-order, oversea-op-api等）
- ✅ 自动保存配置到本地目录
- ✅ 生成详细的操作日志
- ✅ 支持所有namespace类型（bootstrap.yml, application.yml等）
- ✅ 提供Python API供代码集成
- ✅ 支持静默模式和自定义Apollo地址

## 🚀 快速开始

### 1. 配置环境地址

首次使用需要配置Apollo环境地址：

```bash
# 复制配置模板
cp config/apollo_env.json.template config/apollo_env.json

# 编辑配置文件，填入你的Apollo环境地址
vim config/apollo_env.json
```

配置文件格式：
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

⚠️ **安全提示**：
- 配置文件 `config/apollo_env.json` 包含内部环境地址，已被 .gitignore 忽略
- 不要将此文件提交到公开仓库
- 建议使用内网地址，避免暴露到外网

### 2. 前置要求

- Python 3.x
- requests库

### 3. 安装依赖

```powershell
cd scripts
pip install requests
```

### 4. 基本使用

```powershell
# 使用快速启动脚本（最简单）
cd scripts
.\apollo_sync.cmd

# 或直接使用Python脚本
python apollo_config_sync.py --module your-module-api --env pro --namespace bootstrap.yml
```

## 📖 使用指南

### 场景1：拉取单个模块配置

拉取op-api模块生产环境的bootstrap配置：

```powershell
cd .specify/skills/apollo-config-sync/scripts
python apollo_config_sync.py --module op-api --env pro --namespace bootstrap.yml
```

配置文件将保存到：
```
apollo_configs/pro/op-api/bootstrap.yml
```

### 场景2：拉取所有namespace

拉取op-order模块测试环境的所有配置：

```powershell
python apollo_config_sync.py --module op-order --env test --all
```

### 场景3：对比不同环境配置

先拉取不同环境的配置，然后对比：

```powershell
# 拉取测试环境
python apollo_config_sync.py --module op-api --env test --namespace application.yml

# 拉取生产环境
python apollo_config_sync.py --module op-api --env pro --namespace application.yml

# 使用diff工具对比
code --diff apollo_configs\test\op-api\application.yml apollo_configs\pro\op-api\application.yml
```

### 场景4：批量拉取多个模块

使用PowerShell循环批量拉取：

```powershell
$modules = @("op-api", "op-order", "op-user", "op-product")
foreach ($module in $modules) {
    python apollo_config_sync.py --module $module --env pro --namespace bootstrap.yml
}
```

### 场景5：Python代码集成

在Python代码中使用Apollo配置：

```python
from apollo_config_sync import ApolloConfig
import yaml

# 创建Apollo客户端
apollo = ApolloConfig(
    app_id='op-api',
    cluster='default',
    env='pro'
)

# 拉取配置
result = apollo.fetch_config_without_cache('bootstrap.yml')

if result:
    config = result.get('configurations', {})
    yaml_content = config.get('content', '')
    parsed_config = yaml.safe_load(yaml_content)
    
    # 使用配置
    print(parsed_config['spring']['datasource']['url'])
```

## 📁 目录结构

```
apollo-config-sync/
├── SKILL.md              # AI技能提示词文件
├── LICENSE.txt           # MIT许可证
├── README.md             # 本文件（使用说明）
├── scripts/              # 脚本文件
│   ├── apollo_config_sync.py      # 主程序
│   ├── apollo_sync.cmd            # 快速启动脚本
│   ├── apollo_usage_examples.py   # 使用示例
│   ├── requirements.txt           # Python依赖
│   ├── apollo_configs/            # 配置保存目录
│   │   ├── dev/                   # 开发环境配置
│   │   ├── test/                  # 测试环境配置
│   │   ├── uat/                   # UAT环境配置
│   │   └── pro/                   # 生产环境配置
│   └── apollo_sync.log            # 操作日志
└── config/               # 配置文件
    └── apollo_env.json   # 环境地址配置
```

## ⚙️ 配置说明

### 环境地址配置

配置文件位于 `config/apollo_env.json`：

```json
{
  "environments": {
    "dev": "http://dev.example.com.cn:8080",
    "test": "http://uat.example.com.cn:8080",
    "uat": "http://uat.example.com.cn:8080",
    "pro": "http://pro.example.com.cn:8080"
  },
  "default_cluster": "default",
  "timeout": 10
}
```

### 配置项说明

- `environments`: Apollo各环境的地址映射
- `default_cluster`: 默认集群名称
- `timeout`: HTTP请求超时时间（秒）

### 命令行参数

```
--module         模块名称/app_id（必需）
--env            环境名称（必需：dev/test/uat/pro）
--namespace      命名空间名称（默认：bootstrap.yml）
--all            拉取所有namespace
--no-print       静默模式，不输出到控制台
--apollo-url     自定义Apollo地址
```

## 🎯 支持的模块列表

### ECP核心模块

- `op-api` - 运营平台API
- `op-order` - 订单模块
- `op-user` - 用户模块
- `op-product` - 产品模块
- `op-process` - 流程模块
- `op-biz` - 业务模块
- `op-auth` - 认证模块
- `op-job` - 定时任务模块

### 海外业务模块

- `oversea-op-api` - 海外运营API
- `oversea-op-order` - 海外订单模块
- `oversea-op-product` - 海外产品模块
- `oversea-op-user` - 海外用户模块
- `oversea-op-process` - 海外流程模块

## 🔧 故障排查

### 常见问题

**Q: 连接Apollo失败？**

A: 检查以下几点：
- 网络连接是否正常
- Apollo地址是否正确（检查 `config/apollo_env.json`）
- 环境参数是否正确（dev/test/uat/pro）
- 防火墙是否阻止了连接

**Q: 提示认证失败？**

A: 确认：
- app_id（模块名）是否正确
- 是否有权限访问该配置
- 如果配置需要secret，需要在代码中添加

**Q: 拉取的配置为空？**

A: 可能的原因：
- namespace名称不正确
- 该环境下未发布配置
- 配置已被删除
- 查看日志文件 `apollo_sync.log` 获取详细信息

**Q: 如何查看日志？**

A: 使用PowerShell命令：
```powershell
# 查看最新50行
Get-Content .claude/skills/apollo-config-sync/scripts/apollo_sync.log -Tail 50

# 实时监控日志
Get-Content .claude/skills/apollo-config-sync/scripts/apollo_sync.log -Wait
```

**Q: 配置文件包含敏感信息怎么办？**

A: 注意事项：
- 配置文件包含数据库密码等敏感信息
- 不要提交到Git仓库（已在 .gitignore 中）
- 妥善保管本地配置文件
- 生产环境配置尤其要注意保护

## 📚 相关文档

- 详细技能指南：[SKILL.md](SKILL.md)
- Apollo官方文档：[Apollo配置中心](https://www.apolloconfig.com/)
- Python requests库：[requests文档](https://docs.python-requests.org/)

## 🔍 工作原理

1. **环境映射**：根据env参数选择对应的Apollo地址
2. **API调用**：调用Apollo的 `/configs/{appId}/{cluster}/{namespace}` 接口
3. **配置解析**：解析返回的JSON获取配置内容
4. **文件保存**：按照 `{env}/{module}/{namespace}` 结构保存
5. **日志记录**：记录操作详情到 apollo_sync.log

## 💡 最佳实践

1. **定期备份**：定期拉取生产配置进行备份
2. **环境对比**：发布前对比测试和生产环境配置差异
3. **安全第一**：妥善保管包含敏感信息的配置文件
4. **日志审查**：定期检查日志，发现异常操作
5. **脚本集成**：在部署脚本中集成配置拉取，确保最新配置

## 🤝 贡献

欢迎改进本工具！可以：
- 添加新的环境支持
- 优化错误处理
- 增加配置验证功能
- 改进日志格式

## 📄 许可证

MIT License - 详见 [LICENSE.txt](LICENSE.txt)

## 📮 支持

如需帮助，请参考：
- [SKILL.md](SKILL.md) - AI使用指南
- Apollo配置中心官方文档
