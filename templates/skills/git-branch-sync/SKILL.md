---
name: git-branch-sync
description: Git分支切换与代码同步工具。当用户需要切换Git分支、同步最新代码、强制更新本地仓库时使用。支持自动处理冲突、丢弃本地修改、多仓库批量操作。
license: MIT
---

# Git分支切换与代码同步技能

## 技能用途

在使用 git-commit-log 技能查看提交记录后，帮助用户切换到指定分支并将代码更新到最新状态。适用于以下场景：

- 查看某个分支的提交记录后需要切换到该分支
- 需要将本地代码更新到远程最新状态
- 本地有冲突或未提交的修改，需要强制丢弃
- 多个仓库需要批量切换分支并更新
- 清理本地修改，重置到干净状态

## 核心工具

脚本位置：`scripts\git_branch_sync.py`

## 使用指南

### 基本使用方法

```powershell
# 切换到指定分支并更新代码（自动查找当前目录的Git仓库）
python scripts\git_branch_sync.py --branch master

# 强制模式：丢弃本地修改并更新
python scripts\git_branch_sync.py --branch develop --force

# 指定仓库路径
python scripts\\git_branch_sync.py --repo C:\\projects\\myrepo --branch feature/new-feature

# 多仓库批量操作
python scripts\git_branch_sync.py --scan-repos --branch master --force
```

### 参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--branch` | `-b` | 目标分支名称（必需） | - |
| `--force` | `-f` | 强制模式：丢弃本地修改 | False |
| `--repo` | `-r` | 仓库路径（可选） | 当前目录 |
| `--scan-repos` | - | 扫描多个仓库 | False |
| `--base-dir` | - | 扫描的基础目录 | C:\\projects |
| `--scan-depth` | - | 扫描深度 | 2 |
| `--prune` | `-p` | 清理远程已删除的分支 | True |
| `--verbose` | `-v` | 详细输出 | False |
| `--dry-run` | - | 模拟运行，不实际执行 | False |

### 使用场景示例

#### 场景1：查看提交记录后切换分支

```powershell
# 1. 先查看提交记录
python .claude/skills/git-commit-log/scripts/git_commit_log.py --scan-repos --author zhangsan --since "2025-12-24"

# 2. 发现感兴趣的分支后，切换过去
python scripts\git_branch_sync.py --scan-repos --branch feature/new-feature
```

#### 场景2：强制更新到最新（丢弃本地修改）

```powershell
# 当本地有未提交的修改或冲突时，强制丢弃并更新
python scripts\git_branch_sync.py --branch master --force
```

#### 场景3：多仓库批量切换到主分支

```powershell
# 将所有仓库切换到master分支并更新
python scripts\git_branch_sync.py --scan-repos --branch master --force
```

#### 场景4：预览操作而不实际执行

```powershell
# 使用dry-run模式查看将要执行的操作
python scripts\git_branch_sync.py --scan-repos --branch develop --force --dry-run
```

## 工作流程

当执行此技能时，工具会按以下步骤处理：

### 1. 仓库发现阶段

- 如果指定了 `--repo`，直接使用该路径
- 如果指定了 `--scan-repos`，扫描基础目录下的所有Git仓库
- 否则，自动查找当前目录或父目录中的Git仓库

### 2. 状态检查阶段

对每个仓库执行：
- 检查是否为有效的Git仓库
- 检查当前分支和状态
- 检查是否有未提交的修改
- 检查目标分支是否存在

### 3. 代码更新阶段（正常模式）

如果未指定 `--force`：
```bash
git fetch origin --prune          # 获取远程更新，清理已删除的分支
git checkout <branch>              # 切换到目标分支
git pull origin <branch>           # 拉取最新代码
```

**注意**：如果本地有未提交的修改或冲突，此模式会失败并提示用户。

### 4. 代码更新阶段（强制模式）

如果指定了 `--force`：
```bash
git fetch origin --prune          # 获取远程更新
git clean -fd                     # 删除未跟踪的文件和目录
git reset --hard HEAD             # 丢弃所有本地修改
git checkout <branch>              # 切换到目标分支
git reset --hard origin/<branch>   # 强制重置到远程分支状态
```

**警告**：此模式会永久删除所有本地未提交的修改！

### 5. 结果报告阶段

- 显示每个仓库的操作结果
- 统计成功/失败的数量
- 对于失败的仓库，显示错误原因

## 冲突和特殊场景处理

### 场景1：本地有未提交的修改

**问题**：执行 `git checkout` 或 `git pull` 时提示有未提交的修改。

**解决方案**：
```powershell
# 使用强制模式丢弃本地修改
python scripts\git_branch_sync.py --branch master --force
```

### 场景2：本地分支和远程分支冲突

**问题**：本地分支的提交历史与远程不同，无法fast-forward。

**解决方案**：
```powershell
# 强制模式会重置到远程状态
python scripts\git_branch_sync.py --branch develop --force
```

### 场景3：目标分支不存在

**问题**：要切换的分支在远程不存在。

**解决方案**：
- 工具会自动尝试从 `origin/<branch>` 创建本地分支
- 如果远程也不存在，会跳过该仓库并报告错误

### 场景4：分离头指针状态（detached HEAD）

**问题**：当前处于detached HEAD状态。

**解决方案**：
- 工具会自动处理，直接切换到目标分支
- 在强制模式下，会丢弃当前的detached状态

### 场景5：Git仓库损坏

**问题**：Git仓库的 `.git` 目录损坏或不完整。

**解决方案**：
- 工具会跳过该仓库并报告错误
- 建议手动修复或重新克隆仓库

## 安全机制

### 1. 确认提示

在强制模式下，如果检测到本地有未提交的修改，会显示警告：

```
⚠️  警告: 仓库 'project-name' 有未提交的修改！
强制模式将会丢弃以下修改：
  M file1.py
  M file2.js
  ?? new_file.txt

确认要继续吗？ (y/N)
```

### 2. 备份机制（可选）

可以在强制操作前创建备份：

```powershell
# 手动创建备份分支
git branch backup-$(Get-Date -Format "yyyyMMdd-HHmmss")

# 然后执行强制同步
python scripts\git_branch_sync.py --branch master --force
```

### 3. Dry-run 模式

使用 `--dry-run` 预览操作：

```powershell
python scripts\git_branch_sync.py --scan-repos --branch master --force --dry-run
```

输出示例：
```
[DRY RUN] 仓库: op-api
  当前分支: develop
  目标分支: master
  将执行操作:
    1. git fetch origin --prune
    2. git clean -fd
    3. git reset --hard HEAD
    4. git checkout master
    5. git reset --hard origin/master
```

## 故障排查

### 问题1：找不到Git仓库

**症状**：提示 "No git repository found"

**解决方案**：
```powershell
# 使用 --repo 明确指定仓库路径
python scripts\\git_branch_sync.py --repo C:\\projects --branch master

# 或者使用 --scan-repos 扫描多个仓库
python scripts\\git_branch_sync.py --scan-repos --base-dir C:\\projects --branch master
```

### 问题2：权限不足

**症状**：提示 "Permission denied"

**解决方案**：
- 检查文件是否被其他程序占用（如IDE、编辑器）
- 以管理员身份运行PowerShell
- 检查文件系统权限

### 问题3：网络问题导致fetch失败

**症状**：`git fetch` 超时或失败

**解决方案**：
```powershell
# 先手动测试网络连接
git ls-remote origin

# 配置代理（如需要）
git config --global http.proxy http://proxy.example.com:8080

# 或者跳过fetch，只处理本地分支
python scripts\git_branch_sync.py --branch master --no-fetch
```

### 问题4：多个仓库部分失败

**症状**：扫描多个仓库时，部分成功部分失败

**解决方案**：
- 查看详细输出 `--verbose`
- 对失败的仓库单独处理
- 使用 `--continue-on-error` 参数继续处理其他仓库

## 注意事项

### ⚠️ 重要警告

1. **数据丢失风险**：强制模式（`--force`）会永久删除本地未提交的修改，无法恢复！
2. **分支切换影响**：切换分支会改变工作目录的文件内容，可能影响正在运行的程序。
3. **多仓库操作**：批量操作多个仓库时要特别小心，建议先使用 `--dry-run` 预览。

### ✅ 最佳实践

1. **使用前检查状态**：
   ```powershell
   git status
   git branch -vv
   ```

2. **重要修改先备份**：
   ```powershell
   # 创建临时分支保存修改
   git branch backup-temp
   git add -A
   git commit -m "临时备份"
   ```

3. **分步骤执行**：
   - 先用 `--dry-run` 预览
   - 再用 `--verbose` 查看详细信息
   - 最后执行实际操作

4. **配合git-commit-log使用**：
   ```powershell
   # 1. 查看提交记录，确定要切换的分支
   python .claude/skills/git-commit-log/scripts/git_commit_log.py --scan-repos --author zhangsan

   # 2. 切换到目标分支
   python scripts\git_branch_sync.py --repo <repo-path> --branch <branch-name>
   ```

## 输出格式

### 成功输出示例

```
🔍 扫描Git仓库...
  找到 5 个仓库

📦 处理仓库: op-api (1/5)
  当前分支: develop → 目标分支: master
  ✓ 获取远程更新
  ✓ 切换到分支 master
  ✓ 更新到最新代码
  ✅ 完成

📦 处理仓库: op-order (2/5)
  当前分支: master → 目标分支: master
  ℹ️  已在目标分支
  ✓ 更新到最新代码
  ✅ 完成

...

📊 操作统计:
  ✅ 成功: 4 个仓库
  ❌ 失败: 1 个仓库
  ⏭️  跳过: 0 个仓库
  ⏱️  总耗时: 12.3 秒
```

### 失败输出示例

```
📦 处理仓库: op-biz (3/5)
  当前分支: feature/test → 目标分支: master
  ✓ 获取远程更新
  ❌ 错误: 本地有未提交的修改
  
  未提交的文件:
    M src/main/java/Service.java
    ?? temp.txt
  
  💡 建议:
    - 提交或储藏修改: git stash
    - 使用强制模式: --force (将丢弃修改)
```

## 与其他技能的配合

### 配合 git-commit-log 技能

典型工作流：

1. **查看最近提交**：
   ```powershell
   python .claude/skills/git-commit-log/scripts/git_commit_log.py --scan-repos --author zhangsan --since "2025-12-24"
   ```

2. **分析输出**，找到感兴趣的分支和仓库

3. **切换到目标分支**：
   ```powershell
   python scripts\git_branch_sync.py --repo C:\projects\my-api --branch feature/new-feature
   ```

4. **查看该分支的详细diff**：
   ```powershell
   python .claude/skills/git-commit-log/scripts/git_commit_log.py --repo C:\projects\my-api --branch feature/new-feature --diff
   ```

## 脚本输出说明

脚本会输出JSON格式的结果供AI处理：

```json
{
  "success": true,
  "total": 5,
  "succeeded": 4,
  "failed": 1,
  "skipped": 0,
  "results": [
    {
      "repo": "C:\\projects\\my-api",
      "repo_name": "my-api",
      "success": true,
      "from_branch": "develop",
      "to_branch": "master",
      "message": "Successfully switched and updated",
      "forced": false
    },
    {
      "repo": "C:\\projects\\my-order",
      "repo_name": "my-order",
      "success": false,
      "error": "Local changes would be overwritten",
      "suggestion": "Use --force to discard local changes"
    }
  ]
}
```

## 技能限制

- 仅支持Git版本控制系统
- 需要网络连接以获取远程更新
- 强制模式会永久删除本地修改
- 不处理Git子模块（submodules）
- 不处理Git大文件存储（LFS）
