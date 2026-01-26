---
description: 根据可用的设计工件将现有任务转换为可操作的、依赖排序的GitHub问题。
tools: ['github/github-mcp-server/issue_write']
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## 用户输入

```text
$ARGUMENTS
```

在继续之前，您**必须**考虑用户输入（如果不为空）。

## 流程概要

1. 从仓库根目录运行 `{SCRIPT}` 并解析 FEATURE_DIR 和 AVAILABLE_DOCS 列表。所有路径必须是绝对路径。对于参数中的单引号，如"I'm Groot"，使用转义语法：例如 'I'\''m Groot'（或如果可能使用双引号："I'm Groot"）。
1. 从执行的脚本中，提取**任务**的路径。
1. 通过运行以下命令获取Git远程:

```bash
git config --get remote.origin.url
```

> [!CAUTION]
> 仅当远程是GITHUB URL时才继续下一步

1. 对于列表中的每个任务，使用GitHub MCP服务器在代表Git远程的仓库中创建一个新问题。

> [!CAUTION]
> 在任何情况下都不要在与远程URL不匹配的仓库中创建问题
