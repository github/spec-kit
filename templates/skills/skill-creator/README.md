# 技能创建器 (Skill Creator)

> 快速创建符合标准的AI技能定义和目录结构

## 📋 概述

技能创建器是一个用于创建新AI技能的元工具。它提供标准化的模板、自动化脚本和完整的指南，帮助你快速创建结构规范、文档完善的技能定义。

## ✨ 主要功能

- ✅ 自动创建标准技能目录结构
- ✅ 提供多种模板文件（SKILL.md、README.md、脚本模板等）
- ✅ 验证技能名称格式（kebab-case）
- ✅ 生成基础配置文件
- ✅ 包含完整的技能开发指南
- ✅ 支持快速命令行创建

## 🚀 快速开始

### 方法1：使用自动化脚本（推荐）

```powershell
# 切换到脚本目录
cd .claude/skills/skill-creator/scripts

# 创建新技能
python create_skill.py --name "log-analyzer" --description "日志分析工具"
```

### 方法2：手动创建

```powershell
# 1. 创建技能目录
$skillName = "your-skill-name"
$skillPath = ".claude/skills/$skillName"
New-Item -ItemType Directory -Path $skillPath
New-Item -ItemType Directory -Path "$skillPath\templates"
New-Item -ItemType Directory -Path "$skillPath\scripts"
New-Item -ItemType Directory -Path "$skillPath\config"

# 2. 复制模板文件
Copy-Item ".claude/skills/skill-creator/templates/*.template" -Destination $skillPath

# 3. 编辑SKILL.md完善内容
```

## 📖 技能目录标准结构

```
.claude/skills/{skill-name}/
├── SKILL.md              # 技能提示词文件（必需）
├── LICENSE.txt           # 许可证文件（必需）
├── README.md             # 技能说明文档（推荐）
├── templates/            # 模板文件目录（可选）
│   ├── template1.txt
│   └── template2.json
├── scripts/              # 脚本文件目录（可选）
│   ├── main_script.py
│   └── requirements.txt
└── config/               # 配置文件目录（可选）
    └── config.json
```

## 📁 本技能目录结构

```
skill-creator/
├── SKILL.md                          # 技能提示词（使用指南）
├── LICENSE.txt                       # MIT许可证
├── README.md                         # 本文件
├── templates/                        # 模板文件
│   ├── SKILL.md.template            # SKILL.md模板
│   ├── README.md.template           # README模板
│   ├── LICENSE.txt.template         # LICENSE模板
│   ├── script-template.py           # Python脚本模板
│   └── config-template.json         # 配置文件模板
├── scripts/                          # 自动化脚本
│   └── create_skill.py              # 技能创建脚本
└── config/                           # 配置文件
    └── skill-structure.json         # 技能结构定义
```

## 🎯 使用场景

### 场景1：为现有脚本创建技能

如果你有一个Python脚本想要封装成AI技能：

```powershell
# 1. 使用脚本创建技能框架
python create_skill.py --name "my-tool" --description "我的工具描述"

# 2. 复制脚本到技能目录
Copy-Item "原始脚本.py" -Destination ".claude/skills/my-tool/scripts/"

# 3. 编辑 SKILL.md，完善使用指南
```

### 场景2：创建全新的技能

```powershell
# 1. 创建技能框架
python create_skill.py --name "new-feature" --description "新功能描述"

# 2. 在 scripts/ 目录下编写新脚本
# 3. 在 templates/ 目录下创建模板文件
# 4. 在 config/ 目录下创建配置文件
# 5. 完善 SKILL.md 和 README.md
```

## ⚙️ 命令行参数

### create_skill.py

```
--name          技能名称（必需，kebab-case格式）
--description   技能描述（必需，简短说明）
```

### 示例

```powershell
# 创建数据库工具技能
python create_skill.py --name "db-manager" --description "数据库管理工具"

# 创建API测试技能
python create_skill.py --name "api-tester" --description "API接口自动化测试"

# 创建日志分析技能
python create_skill.py --name "log-analyzer" --description "日志文件分析和统计"
```

## 📐 技能命名规范

### ✅ 正确的命名

- `apollo-config-sync` - Apollo配置同步
- `database-query` - 数据库查询
- `log-analyzer` - 日志分析器
- `api-tester` - API测试器
- `code-reviewer` - 代码审查器

### ❌ 错误的命名

- `ApolloConfigSync` - PascalCase（应使用kebab-case）
- `apollo_config_sync` - snake_case（应使用kebab-case）
- `acs` - 缩写不清晰
- `tool1` - 无意义的名称
- `-my-skill` - 不能以连字符开头
- `my--skill` - 不能有连续连字符

## 📝 SKILL.md 编写指南

### 必需部分

1. **YAML Front Matter**（元数据）
```yaml
---
name: skill-name
description: 技能描述
license: MIT
---
```

2. **技能用途**
   - 说明何时使用此技能
   - 列举适用场景

3. **使用指南**
   - 基本使用方法
   - 命令示例
   - 参数说明

4. **工作流程**
   - AI执行此技能的步骤

5. **注意事项**
   - 重要提醒
   - 最佳实践

### 推荐部分

- 核心工具/脚本说明
- 故障排查指南
- 高级用法示例
- 配置说明

## 🔧 配置文件说明

### skill-structure.json

定义技能的标准结构和规范：

- `skill_structure`: 技能目录结构定义
- `naming_rules`: 命名规则和示例
- `skill_md_sections`: SKILL.md各章节要求
- `description_template`: 描述模板
- `path_conventions`: 路径规范
- `best_practices`: 最佳实践列表

## 💡 最佳实践

### 1. 技能粒度

- ✅ 每个技能专注于一个明确任务
- ✅ 避免创建"万能"技能
- ✅ 相关功能可分成多个技能

### 2. 文档质量

- ✅ 提供清晰的使用示例
- ✅ 包含常见场景的命令
- ✅ 说明所有参数选项
- ✅ 提供故障排查指南

### 3. 路径管理

- ✅ 使用绝对路径
- ✅ 适配Windows环境
- ✅ 在示例中正确转义

### 4. 脚本管理

- ✅ 脚本放在 scripts/ 目录
- ✅ 添加清晰注释
- ✅ 提供依赖说明
- ✅ 确保独立可运行

## 🔍 验证检查清单

创建技能后，请检查：

- [ ] 技能名称符合kebab-case格式
- [ ] SKILL.md包含完整的YAML front matter
- [ ] 所有路径使用绝对路径
- [ ] 包含LICENSE.txt文件
- [ ] README.md说明清晰
- [ ] 命令示例可执行
- [ ] 模板文件完整
- [ ] 配置文件有效

## 📚 参考现有技能

学习优秀示例：

- [apollo-config-sync](../apollo-config-sync/SKILL.md) - 配置管理类技能
- [database-query](../database-query/SKILL.md) - 查询工具类技能
- [algorithmic-art](../gitlab/SKILL.MD) - 创作生成类技能

## 🤝 贡献指南

欢迎改进技能创建器！

如果你有好的模板或建议：
1. 在 `templates/` 目录下添加新模板
2. 更新 `config/skill-structure.json`
3. 完善 `SKILL.md` 文档

## ❓ 常见问题

**Q: 如何更新现有技能？**

A: 直接编辑技能目录下的文件即可，无需重新创建。

**Q: 可以删除不需要的目录吗？**

A: 可以。templates/、scripts/、config/ 都是可选的，按需使用。

**Q: 如何让AI识别新技能？**

A: 只要技能目录在 `.claude/skills/` 下且有正确的 SKILL.md，AI会自动识别。

**Q: 技能名称可以修改吗？**

A: 可以重命名目录，但需同步更新 SKILL.md 中的 name 字段和所有路径引用。

## 📄 许可证

MIT License - 详见 [LICENSE.txt](LICENSE.txt)

## 📮 支持

如有问题或建议，请参考 [SKILL.md](SKILL.md) 中的详细指南。
