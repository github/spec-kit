# Kimi CLI + Spec Kit 配置指南

## 安装 Kimi CLI

```bash
pip install kimi-cli
# 或
uv tool install kimi-cli
```

## 配置

1. 复制此配置文件到 `~/.kimi/config.toml`：

```bash
cp .kimi/config.toml ~/.kimi/config.toml
```

2. 设置 API Key（选择一种方式）：

**方式 1：环境变量（推荐）**
```bash
export MOONSHOT_API_KEY="your-moonshot-api-key"
```

**方式 2：配置文件**
编辑 `~/.kimi/config.toml`，在 `[providers.moonshot]` 部分添加：
```toml
api_key = "your-api-key"
```

## 使用 Spec Kit

在项目目录中运行：

```bash
# 初始化 Spec Kit 项目
specify init my-project --ai kimi

# 或在现有项目初始化
specify init . --ai kimi
```

## Spec Kit Slash Commands

初始化后，你可以在 Kimi CLI 中使用以下命令：

- `/speckit.constitution` - 建立项目原则
- `/speckit.specify` - 定义需求规格
- `/speckit.plan` - 制定技术计划
- `/speckit.tasks` - 生成任务列表
- `/speckit.implement` - 执行实现

## 获取 Moonshot API Key

1. 访问 https://platform.moonshot.ai/
2. 注册/登录账号
3. 创建 API Key

## 文档

- Kimi CLI: https://github.com/MoonshotAI/kimi-cli
- Spec Kit: https://github.com/github/spec-kit
