# Git分支切换与代码同步技能

## 概述

这是一个用于Git分支切换和代码同步的自动化工具技能，帮助开发者快速切换分支并更新代码到最新状态。特别适合在查看Git提交记录后需要切换分支的场景。

## 主要特性

- ✅ 自动查找Git仓库（当前目录或父目录）
- ✅ 切换到指定分支并拉取最新代码
- ✅ 强制模式：丢弃本地修改，重置到远程状态
- ✅ 多仓库批量操作
- ✅ 自动处理冲突和特殊场景
- ✅ 详细的状态检查和错误提示
- ✅ 支持dry-run模式预览操作

## 快速开始

### 基本用法

```powershell
# 切换到master分支并更新
python scripts\git_branch_sync.py --branch master

# 强制模式（丢弃本地修改）
python scripts\git_branch_sync.py --branch develop --force

# 多仓库批量操作
python scripts\git_branch_sync.py --scan-repos --branch master --force
```

### 典型工作流

1. **使用git-commit-log查看提交记录**
   ```powershell
   python .claude/skills/git-commit-log/scripts/git_commit_log.py --scan-repos --author zhangsan
   ```

2. **切换到感兴趣的分支**
   ```powershell
   python scripts\git_branch_sync.py --repo C:\projects\my-api --branch feature/new-feature
   ```

## 参数说明

| 参数 | 说明 |
|------|------|
| `--branch` `-b` | 目标分支名称（必需） |
| `--force` `-f` | 强制模式：丢弃本地修改 |
| `--repo` `-r` | 仓库路径（可选） |
| `--scan-repos` | 扫描多个仓库 |
| `--dry-run` | 模拟运行，不实际执行 |
| `--verbose` `-v` | 详细输出 |

## 文件结构

```
git-branch-sync/
├── SKILL.md              # 技能提示词文件（AI使用）
├── LICENSE.txt           # MIT许可证
├── README.md             # 本文档
└── scripts/
    └── git_branch_sync.py  # 核心脚本
```

## 安全提示

⚠️ **重要警告**

- 强制模式（`--force`）会**永久删除**本地未提交的修改！
- 使用前请确保重要修改已提交或备份
- 建议先使用 `--dry-run` 预览操作

## 许可证

MIT License - 详见 [LICENSE.txt](LICENSE.txt)

## 更多信息

详细的使用指南和配置说明，请参阅 [SKILL.md](SKILL.md)
