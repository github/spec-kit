# Trae AI Integration

## Overview

This document details the integration of Trae AI into the spec-kit project. Trae AI is an IDE-based AI assistant that does not have a CLI component, making it uniquely suited for integration with spec-kit's agent context management system.

## Changes Made

### 1. Core Configuration

**File**: `src/specify_cli/__init__.py`

- Added Trae AI to `AI_CHOICES` dictionary:
  ```python
  "trae": "Trae AI (IDE-based)"
  ```

- Added folder mapping to `agent_folder_map`:
  ```python
  "trae": ".trae/"
  ```

### 2. Bash Script Updates

**File**: `scripts/bash/update-agent-context.sh`

- Added TRAE_FILE definition:
  ```bash
  TRAE_FILE="$REPO_ROOT/.trae/rules/specify-rules.md"
  ```

- Added trae case statement:
  ```bash
  trae)
      update_agent_file "$TRAE_FILE" "Trae AI"
      ;;
  ```

- Added Trae AI check in update_all_existing_agents function:
  ```bash
  if [[ -f "$TRAE_FILE" ]]; then
      update_agent_file "$TRAE_FILE" "Trae AI"
      found_agent=true
  fi
  ```

### 3. PowerShell Script Updates

**File**: `scripts/powershell/update-agent-context.ps1`

- Added TRAE_FILE definition:
  ```powershell
  $TRAE_FILE = Join-Path $REPO_ROOT '.trae/rules/specify-rules.md'
  ```

- Added trae switch statement:
  ```powershell
  'trae'     { Update-AgentFile -TargetFile $TRAE_FILE -AgentName 'Trae AI' }
  ```

- Added Trae AI check in Update-AllExistingAgents function:
  ```powershell
  if (Test-Path $TRAE_FILE) { 
      if (-not (Update-AgentFile -TargetFile $TRAE_FILE -AgentName 'Trae AI')) { $ok = $false }
      $found = $true 
  }
  ```

## Usage

### For Trae AI Users

1. **Create the rules directory**:
   ```bash
   mkdir -p .trae/rules/
   ```

2. **Initialize the specify rules file**:
   ```bash
   touch .trae/rules/specify-rules.md
   ```

3. **Add your Trae AI specific rules**:
   Edit `.trae/rules/specify-rules.md` with your preferred rules and constraints.

### For spec-kit Operations

#### Update Trae AI Context

```bash
# Using the bash script
./scripts/bash/update-agent-context.sh trae

# Using the PowerShell script
./scripts/powershell/update-agent-context.ps1 -Type trae
```

#### Update All Agents (including Trae AI)

```bash
# Using the bash script
./scripts/bash/update-agent-context.sh

# Using the PowerShell script
./scripts/powershell/update-agent-context.ps1
```

#### Using specify CLI

```bash
# Check available agents
specify --list-agents

# Output should include:
# trae: Trae AI (IDE-based)
```

## Key Features

- **IDE-based Design**: Properly marked as "IDE-based" since Trae AI has no CLI component
- **Consistent Integration**: Follows the same pattern as other AI agents in spec-kit
- **Automatic Detection**: Included in automatic agent detection during bulk updates
- **Cross-platform Support**: Works with both Bash and PowerShell scripts

## File Structure

```
.trae/
└── rules/
    └── specify-rules.md    # Trae AI specific rules and constraints
```

## Verification

To verify the integration is working correctly:

1. Run `specify --list-agents` and confirm Trae AI is listed
2. Run the update scripts and verify no errors occur
3. Check that the `.trae/rules/specify-rules.md` file is properly managed

## Notes

- Trae AI does not require CLI-specific checks since it's IDE-based
- The integration focuses on rules file management rather than CLI interaction
- Error messages have been updated to include 'trae' as an expected agent type

## Version

**Integration Date**: 2025
**spec-kit Version**: Compatible with current release
**Trae AI Support**: Full integration completed

---

*This document will be maintained to reflect any future updates to Trae AI integration.*

# Trae AI 集成

## 概述

本文档详细介绍了将 Trae AI 集成到 spec-kit 项目中的过程。Trae AI 是一个基于 IDE 的 AI 助手，没有 CLI 组件，这使其特别适合与 spec-kit 的 agent 上下文管理系统集成。

## 所做的更改

### 1. 核心配置

**文件**: `src/specify_cli/__init__.py`

- 将 Trae AI 添加到 `AI_CHOICES` 字典:
  ```python
  "trae": "Trae AI (IDE-based)"
  ```

- 添加到文件夹映射 `agent_folder_map`:
  ```python
  "trae": ".trae/"
  ```

### 2. Bash 脚本更新

**文件**: `scripts/bash/update-agent-context.sh`

- 添加 TRAE_FILE 定义:
  ```bash
  TRAE_FILE="$REPO_ROOT/.trae/rules/specify-rules.md"
  ```

- 添加 trae case 语句:
  ```bash
  trae)
      update_agent_file "$TRAE_FILE" "Trae AI"
      ;;
  ```

- 在 update_all_existing_agents 函数中添加 Trae AI 检查:
  ```bash
  if [[ -f "$TRAE_FILE" ]]; then
      update_agent_file "$TRAE_FILE" "Trae AI"
      found_agent=true
  fi
  ```

### 3. PowerShell 脚本更新

**文件**: `scripts/powershell/update-agent-context.ps1`

- 添加 TRAE_FILE 定义:
  ```powershell
  $TRAE_FILE = Join-Path $REPO_ROOT '.trae/rules/specify-rules.md'
  ```

- 添加 trae switch 语句:
  ```powershell
  'trae'     { Update-AgentFile -TargetFile $TRAE_FILE -AgentName 'Trae AI' }
  ```

- 在 Update-AllExistingAgents 函数中添加 Trae AI 检查:
  ```powershell
  if (Test-Path $TRAE_FILE) { 
      if (-not (Update-AgentFile -TargetFile $TRAE_FILE -AgentName 'Trae AI')) { $ok = $false }
      $found = $true 
  }
  ```

## 使用方法

### 针对 Trae AI 用户

1. **创建规则目录**:
   ```bash
   mkdir -p .trae/rules/
   ```

2. **初始化 specify 规则文件**:
   ```bash
   touch .trae/rules/specify-rules.md
   ```

3. **添加您的 Trae AI 特定规则**:
   使用您偏好的规则和约束编辑 `.trae/rules/specify-rules.md`。

### 针对 spec-kit 操作

#### 更新 Trae AI 上下文

```bash
# 使用 bash 脚本
./scripts/bash/update-agent-context.sh trae

# 使用 PowerShell 脚本
./scripts/powershell/update-agent-context.ps1 -Type trae
```

#### 更新所有 Agent（包括 Trae AI）

```bash
# 使用 bash 脚本
./scripts/bash/update-agent-context.sh

# 使用 PowerShell 脚本
./scripts/powershell/update-agent-context.ps1
```

#### 使用 specify CLI

```bash
# 检查可用的 agent
specify --list-agents

# 输出应该包含:
# trae: Trae AI (IDE-based)
```

## 关键特性

- **基于 IDE 的设计**: 由于 Trae AI 没有 CLI 组件，正确标记为"IDE-based"
- **一致的集成**: 遵循与 spec-kit 中其他 AI agent 相同的模式
- **自动检测**: 在批量更新期间包含在自动 agent 检测中
- **跨平台支持**: 适用于 Bash 和 PowerShell 脚本

## 文件结构

```
.trae/
└── rules/
    └── specify-rules.md    # Trae AI 特定规则和约束
```

## 验证

要验证集成是否正常工作：

1. 运行 `specify --list-agents` 并确认 Trae AI 已列出
2. 运行更新脚本并验证没有错误发生
3. 检查 `.trae/rules/specify-rules.md` 文件是否正确管理

## 注意事项

- 由于 Trae AI 是基于 IDE 的，不需要 CLI 特定的检查
- 集成侧重于规则文件管理而不是 CLI 交互
- 错误消息已更新，包含 'trae' 作为预期的 agent 类型

## 版本

**集成日期**: 2025
**spec-kit 版本**: 与当前版本兼容
**Trae AI 支持**: 完整集成已完成

---

*本文档将保持更新以反映 Trae AI 集成的任何未来更新。*