# Git提交记录拉取技能

拉取并分析Git仓库提交记录的AI技能。

## 功能特性

- ✅ 多仓库支持：自动扫描指定目录下的所有Git仓库
- ✅ 时间筛选：支持按日期范围筛选提交记录
- ✅ 作者筛选：支持按提交者筛选
- ✅ 代码差异：可选显示每次提交的代码变更
- ✅ JSON输出：结构化的JSON格式输出，便于分析
- ✅ 控制台输出：默认只输出到控制台，不创建临时文件

## 快速开始

### 1. 基本用法

```bash
cd scripts

# 拉取当前仓库最近7天的提交记录
python git_commit_log.py

# 拉取指定目录下所有仓库的提交记录
python git_commit_log.py --repo-dir /path/to/repos

# 指定时间范围
python git_commit_log.py --since "2024-01-01" --until "2024-01-31"

# 指定作者
python git_commit_log.py --author "张三"

# 包含代码差异
python git_commit_log.py --show-diff

# 限制提交数量
python git_commit_log.py --max-count 50
```

### 2. 高级用法

```bash
# 扫描多个仓库并显示差异
python git_commit_log.py --repo-dir /path/to/repos --show-diff --max-count 100

# 分析特定作者在特定时间段的提交
python git_commit_log.py --author "张三" --since "2024-01-01" --until "2024-01-31"

# 组合使用多个参数
python git_commit_log.py \
  --repo-dir /path/to/repos \
  --author "张三" \
  --since "2024-01-01" \
  --show-diff \
  --max-count 50
```

## 输出格式

脚本输出JSON格式的提交记录：

```json
{
  "repository": "/path/to/repo",
  "branch": "main",
  "total_commits": 10,
  "commits": [
    {
      "hash": "abc123def456",
      "author": "张三",
      "email": "zhangsan@example.com",
      "date": "2024-01-15T10:30:00+08:00",
      "message": "feat: 添加新功能",
      "files_changed": 3,
      "insertions": 150,
      "deletions": 20,
      "diff": "... (如果启用 --show-diff)"
    }
  ]
}
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--repo-dir` | Git仓库目录路径，如果未指定则使用当前目录 | 当前目录 |
| `--since` | 起始日期 (格式: YYYY-MM-DD) | 7天前 |
| `--until` | 结束日期 (格式: YYYY-MM-DD) | 今天 |
| `--author` | 提交作者名称（支持模糊匹配） | 所有作者 |
| `--show-diff` | 显示每次提交的代码差异 | 不显示 |
| `--max-count` | 最大提交数量 | 100 |

## 使用场景

1. **代码审查准备**：在代码审查前快速了解最近的变更
2. **工作量统计**：统计团队成员的提交情况
3. **变更追踪**：追踪特定时间段的代码变更
4. **问题排查**：通过提交记录定位问题引入的时间点
5. **多仓库管理**：批量查看多个仓库的提交情况

## 注意事项

⚠️ **重要提示**：

- 脚本默认只输出到控制台，不创建临时文件
- 使用 `--show-diff` 时输出会很大，建议配合 `--max-count` 限制数量
- 确保对目标仓库有读取权限
- 多仓库扫描时会自动跳过非Git目录

## 技术细节

- **Git命令**：使用标准Git命令行工具
- **编码**：UTF-8
- **输出格式**：JSON
- **错误处理**：自动跳过无效仓库，继续处理其他仓库

## 许可证

MIT License
