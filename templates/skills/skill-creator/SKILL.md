---
name: skill-creator
description: 技能创建器。当用户需要创建新的AI技能、生成技能模板、初始化技能目录结构时使用。自动化创建符合标准的技能框架，包含必要的文件和目录。
license: MIT
---

# 技能创建器

## 技能用途

帮助用户快速创建新的AI技能定义。适用于以下场景：
- 用户需要创建新的技能
- 用户需要为现有脚本或工具创建技能封装
- 用户需要标准化的技能目录结构
- 用户需要技能模板和示例

## 技能目录标准结构

每个技能应包含以下标准结构：

```
.claude/skills/{skill-name}/
├── SKILL.md              # 技能提示词文件（必需）
├── LICENSE.txt           # 许可证文件（必需）
├── README.md             # 技能说明文档（推荐）
├── templates/            # 模板文件目录（可选）
├── scripts/              # 脚本文件目录（可选）
└── config/               # 配置文件目录（可选）
```

## SKILL.md 文件规范

SKILL.md 是技能的核心文件，必须包含以下部分：

### 1. YAML Front Matter（元数据）

```yaml
---
name: skill-name                    # 技能名称（kebab-case格式）
description: 技能描述。用途说明...    # 简短描述，说明何时触发此技能
license: MIT                        # 许可证类型
---
```

### 2. 技能内容结构

```markdown
# 技能标题

## 技能用途
明确说明此技能的使用场景和触发条件

## 核心工具/脚本
说明技能依赖的工具、脚本或资源的位置

## 使用指南
详细的使用说明，包括：
- 基本使用方法
- 常用命令示例
- 参数说明
- 配置选项

## 工作流程
描述AI在执行此技能时应遵循的步骤

## 故障排查
常见问题和解决方案

## 注意事项
重要提醒和最佳实践
```

## 创建新技能的工作流程

当用户请求创建新技能时，按以下步骤执行：

### 步骤 1: 理解需求

询问或确认以下信息：
- **技能名称**：使用 kebab-case 格式（如：apollo-config-sync）
- **技能用途**：这个技能解决什么问题？
- **触发场景**：用户在什么情况下需要这个技能？
- **依赖资源**：是否有现有脚本、工具或配置？
- **特殊要求**：是否需要模板、配置文件等？

### 步骤 2: 创建目录结构

```powershell
# 创建技能主目录
$skillName = "your-skill-name"
$skillPath = ".claude/skills/$skillName"
New-Item -ItemType Directory -Path $skillPath
New-Item -ItemType Directory -Path "$skillPath\templates"
New-Item -ItemType Directory -Path "$skillPath\scripts"
New-Item -ItemType Directory -Path "$skillPath\config"
```

### 步骤 3: 创建核心文件

**创建 SKILL.md**：
- 使用 `templates/SKILL.md.template` 作为基础
- 填充技能特定的内容
- 确保 YAML front matter 正确
- 包含完整的使用指南

**创建 LICENSE.txt**：
- 使用 `templates/LICENSE.txt.template`
- 根据需要调整版权信息

**创建 README.md**：
- 使用 `templates/README.md.template`
- 提供技能的概述和快速入门

### 步骤 4: 迁移或创建资源

如果技能基于现有脚本：
```powershell
# 复制脚本到技能目录
Copy-Item "source/script.py" -Destination "$skillPath\scripts\"
Copy-Item "source/config.json" -Destination "$skillPath\config\"
```

如果需要创建新脚本：
- 在 `scripts/` 目录下创建所需脚本
- 在 `config/` 目录下创建配置文件
- 在 `templates/` 目录下创建模板文件

### 步骤 5: 更新路径引用

确保 SKILL.md 中所有路径引用都使用相对路径：
- 脚本路径：`scripts\{script-name}`
- 配置路径：`config\{config-name}`
- 模板路径：`templates\{template-name}`

使用相对路径的好处：
- 技能目录可以自由移动或重命名
- 路径更简洁易读
- 跨项目复用更方便

### 步骤 6: 验证技能

1. 检查目录结构是否完整
2. 验证 SKILL.md 的 YAML front matter 格式
3. 确认所有文件路径正确
4. 测试脚本是否可执行

## 使用自动化脚本

可以使用自动化脚本快速创建技能框架：

```powershell
cd .specify/skills/skill-creator/scripts
python create_skill.py --name "new-skill-name" --description "技能描述"
```

脚本会自动：
- 创建标准目录结构
- 生成基础的 SKILL.md 文件
- 复制 LICENSE.txt
- 创建 README.md 框架

## 技能命名规范

### 命名格式

使用 **kebab-case** 格式：
- 全小写字母
- 单词间用连字符 `-` 分隔
- 简洁明了，描述性强

### 命名示例

✅ 好的命名：
- `apollo-config-sync` - Apollo配置同步
- `database-query` - 数据库查询
- `code-review` - 代码审查
- `git-workflow` - Git工作流
- `api-test` - API测试

❌ 不好的命名：
- `ApolloConfigSync` - 不要使用 PascalCase
- `apollo_config_sync` - 不要使用 snake_case
- `acs` - 避免缩写，不够清晰
- `tool1` - 避免无意义的名称

## 技能描述规范

在 YAML front matter 中的 `description` 字段应该：

1. **简洁明了**（1-2句话）
2. **说明用途**（解决什么问题）
3. **指明触发条件**（何时使用此技能）
4. **列举关键功能**（支持什么操作）

### 描述模板

```
{技能用途}。当用户需要{场景1}、{场景2}、{场景3}时使用。支持{功能1}、{功能2}和{功能3}。
```

### 描述示例

```yaml
description: Apollo配置中心配置拉取工具。当用户需要从Apollo配置中心拉取配置、同步配置、查看配置变化时使用。支持多环境(dev/test/uat/pro)和多模块配置管理。
```

## 模板文件说明

技能创建器提供以下模板：

### 1. SKILL.md.template
标准的技能提示词模板，包含：
- YAML front matter 结构
- 技能内容各个章节的框架
- 常用章节的示例内容

### 2. README.md.template
技能说明文档模板，包含：
- 技能概述
- 快速开始
- 详细功能说明
- 常见问题

### 3. LICENSE.txt.template
MIT 许可证模板

### 4. script-template.py
Python 脚本模板，包含：
- 标准的文件头注释
- 参数解析框架
- 日志配置
- 错误处理

### 5. config-template.json
配置文件模板

## 配置文件说明

### skill-structure.json

定义技能的标准目录结构：

```json
{
  "required": [
    "SKILL.md",
    "LICENSE.txt"
  ],
  "recommended": [
    "README.md"
  ],
  "optional": [
    "templates/",
    "scripts/",
    "config/"
  ]
}
```

## 最佳实践

### 1. 技能粒度

- ✅ 每个技能专注于一个明确的任务领域
- ✅ 避免创建过于庞大的"万能"技能
- ✅ 相关但独立的功能可以分成多个技能

### 2. 文档质量

- ✅ 提供清晰的使用示例
- ✅ 包含常见场景的命令示例
- ✅ 说明所有参数和配置选项
- ✅ 提供故障排查指南

### 3. 路径管理

- ✅ 始终使用绝对路径
- ✅ 适配 Windows 环境（使用反斜杠 `\`）
- ✅ 在代码示例中使用双反斜杠 `\\`（转义）

### 4. 脚本管理

- ✅ 将脚本放在 `scripts/` 目录下
- ✅ 为脚本添加清晰的注释和文档字符串
- ✅ 提供 requirements.txt 或依赖说明
- ✅ 确保脚本可独立运行

### 5. 模板管理

- ✅ 将可复用的模板放在 `templates/` 目录
- ✅ 模板文件使用 `.template` 后缀
- ✅ 在模板中使用占位符（如 `{PLACEHOLDER}`）
- ✅ 提供模板的使用说明

## 技能维护

### 更新技能

当需要更新现有技能时：
1. 更新 SKILL.md 中的内容
2. 如有脚本更新，同步更新 `scripts/` 目录
3. 更新 README.md 中的版本说明
4. 测试更新后的功能

### 技能列表管理

定期审查 `.claude/skills/` 目录：
- 确保所有技能都有完整的文档
- 删除过时或不再使用的技能
- 合并功能重复的技能

## 示例：创建一个新技能

假设我们要创建一个"日志分析"技能：

```powershell
# 1. 创建目录结构
cd .claude/skills/skill-creator/scripts
python create_skill.py --name "log-analyzer" --description "日志分析工具"

# 2. 切换到新技能目录
cd .claude/skills/log-analyzer

# 3. 编辑 SKILL.md，添加具体内容
# （使用文本编辑器编辑）

# 4. 添加脚本
# 将日志分析脚本复制到 scripts/ 目录

# 5. 添加配置
# 创建配置文件到 config/ 目录

# 6. 验证
Get-ChildItem -Recurse
```

## Windows 环境注意事项

- 使用 PowerShell 命令，不使用 Linux 命令
- 路径分隔符使用反斜杠 `\`
- 命令连接使用分号 `;`，不使用 `&&`
- 创建目录使用 `New-Item -ItemType Directory`
- 复制文件使用 `Copy-Item`

## 工作流程总结

当用户说"帮我创建一个新技能"时：

1. **询问需求**：技能名称、用途、依赖等
2. **创建目录**：使用标准结构创建技能目录
3. **生成文件**：基于模板创建 SKILL.md、LICENSE.txt、README.md
4. **迁移资源**：如有现有脚本，复制到 scripts/ 目录
5. **编写文档**：完善 SKILL.md 的各个章节
6. **验证测试**：确保路径正确、脚本可运行
7. **交付说明**：告知用户如何使用新创建的技能

## 快速命令参考

```powershell
# 列出所有技能
Get-ChildItem .claude/skills -Directory

# 创建新技能（使用脚本）
cd .claude/skills/skill-creator/scripts
python create_skill.py --name "skill-name" --description "描述"

# 手动创建技能目录
$skill = "skill-name"
$path = ".claude/skills/$skill"
New-Item -ItemType Directory -Path $path
New-Item -ItemType Directory -Path "$path\templates"
New-Item -ItemType Directory -Path "$path\scripts"
New-Item -ItemType Directory -Path "$path\config"

# 查看技能结构
Get-ChildItem .claude/skills/skill-name -Recurse
```

## 参考现有技能

可以参考以下已有技能作为示例：
- `apollo-config-sync` - 配置同步类技能
- `database-query` - 查询工具类技能
- `algorithmic-art` - 生成创作类技能

查看这些技能的 SKILL.md 文件可以了解不同类型技能的最佳实践。
