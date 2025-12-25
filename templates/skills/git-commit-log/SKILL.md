---
name: git-commit-log
description: Git提交记录拉取工具。查看Git提交历史、分析提交记录、查看代码差异。支持自动查找仓库、多仓库扫描、代码diff展示。默认只输出到控制台，不创建临时文件。
license: MIT
---

# Git提交记录拉取技能

## 技能用途

查看和分析Git提交记录，包括提交历史、文件变更和代码差异（diff）。工具会自动查找Git仓库，无需手动指定路径。

## 核心工具

脚本位置：`.claude/skills/git-commit-log/scripts/git_commit_log.py`

## 使用方法

### 基本用法

```powershell
# 自动查找当前或父目录的Git仓库
python git_commit_log.py --author zhangsan --since "2025-12-24 00:00:00"

# 扫描多个仓库
python git_commit_log.py --scan-repos --author zhangsan --since 2025-12-24

# 指定仓库路径
python git_commit_log.py --repo C:\\projects\\myrepo --author zhangsan
```

### 常用参数

| 参数 | 说明 |
|------|------|
| `--author` `-a` | 作者（用户名或邮箱，推荐只用用户名） |
| `--since` `-s` | 开始日期（推荐只用since，不要用until） |
| `--scan-repos` | 扫描多个仓库 |
| `--base-dir` | 扫描的基础目录 |
| `--scan-depth` | 扫描深度（默认2级） |
| `--format` `-f` | 输出格式（detailed/simple/oneline/json） |
| `--max-count` `-n` | 限制数量 |
| `--diff` | **显示代码差异（git diff）** |
| `--max-diff-lines` | 最大差异行数（默认500行） |
| `--stat-only` | 只显示统计 |
| `--save` | 保存到文件 |
| `--output` `-o` | 输出文件路径 |

### 最佳实践

**查找某人今天的提交：**
```powershell
python git_commit_log.py --scan-repos --author zhangsan --since "2025-12-24 00:00:00"
```

**查看提交并显示代码差异：**
```powershell
python git_commit_log.py --scan-repos --author zhangsan --since "2025-12-24" --diff
```

**快速浏览多个仓库：**
```powershell
python git_commit_log.py --scan-repos --author zhangsan --format simple --no-stats
```

**生成详细报告（包含代码差异）：**
```powershell
python git_commit_log.py --scan-repos --author zhangsan --since 2025-12-01 --diff --save --output report.txt
```

**查看特定提交的diff（限制行数）：**
```powershell
python git_commit_log.py --author zhangsan --since 2025-12-24 --diff --max-diff-lines 200
```

## 重要提示

- ✅ 作者搜索：用 `zhangsan` 而不是 `zhangsan@example.com`
- ✅ 日期查询：只用 `--since`，不要同时用 `--until`
- ✅ 多仓库：用 `--scan-repos` 自动扫描所有仓库
- ✅ 默认不保存文件，需要时用 `--save --output`
- ✅ 代码diff：添加 `--diff` 参数查看详细代码变更
- ⚠️ diff输出较大：建议配合 `--max-diff-lines` 限制行数
- ⚠️ diff影响性能：扫描多仓库时，加diff会变慢

## 故障排查

**未找到Git仓库：**
- 使用 `--scan-repos` 扫描多个仓库
- 使用 `--base-dir` 指定扫描目录

**未找到提交：**
- 检查作者名是否正确（只用用户名部分）
- 检查日期范围是否合理
- 使用 `--all-branches` 查看所有分支
