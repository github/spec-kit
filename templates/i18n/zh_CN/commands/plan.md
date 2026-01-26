---
description: 使用计划模板执行实施计划工作流程以生成设计工件。
handoffs: 
  - label: 创建任务
    agent: speckit.tasks
    prompt: 将计划分解为任务
    send: true
  - label: 创建检查清单
    agent: speckit.checklist
    prompt: 为以下领域创建检查清单...
scripts:
  sh: scripts/bash/setup-plan.sh --json
  ps: scripts/powershell/setup-plan.ps1 -Json
agent_scripts:
  sh: scripts/bash/update-agent-context.sh __AGENT__
  ps: scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__
---

## 用户输入

```text
$ARGUMENTS
```

在继续之前，您**必须**考虑用户输入（如果不为空）。

## 流程概要

1. **设置**: 从仓库根目录运行 `{SCRIPT}` 并解析JSON中的 FEATURE_SPEC、IMPL_PLAN、SPECS_DIR、BRANCH。对于参数中的单引号，如"I'm Groot"，使用转义语法：例如 'I'\''m Groot'（或如果可能使用双引号："I'm Groot"）。

2. **加载上下文**: 读取 FEATURE_SPEC 和 `/memory/constitution.md`。加载 IMPL_PLAN 模板（已复制）。

3. **执行计划工作流**: 遵循 IMPL_PLAN 模板中的结构来:
   - 填写技术上下文（将未知标记为"需要澄清"）
   - 从宪法填写宪法检查部分
   - 评估门控（如果违规不合理则报错）
   - 阶段0: 生成 research.md（解决所有需要澄清的问题）
   - 阶段1: 生成 data-model.md、contracts/、quickstart.md
   - 阶段1: 通过运行代理脚本更新代理上下文
   - 设计后重新评估宪法检查

4. **停止并报告**: 命令在阶段2规划后结束。报告分支、IMPL_PLAN路径和生成的工件。

## 阶段

### 阶段0: 大纲和研究

1. **从上面的技术上下文中提取未知项**:
   - 对于每个需要澄清 → 研究任务
   - 对于每个依赖关系 → 最佳实践任务
   - 对于每个集成 → 模式任务

2. **生成并分派研究代理**:

   ```text
   对于技术上下文中的每个未知项:
     任务: "为{特性上下文}研究{未知项}"
   对于每个技术选择:
     任务: "查找{领域}中{技术}的最佳实践"
   ```

3. **在 `research.md` 中整合发现**，使用格式:
   - 决策: [选择了什么]
   - 理由: [为什么选择]
   - 考虑的替代方案: [还评估了什么]

**输出**: 解决所有需要澄清问题的 research.md

### 阶段1: 设计和契约

**先决条件:** `research.md` 完成

1. **从特性规格中提取实体** → `data-model.md`:
   - 实体名称、字段、关系
   - 来自要求的验证规则
   - 适用时的状态转换

2. **从功能性要求生成API契约**:
   - 对于每个用户操作 → 端点
   - 使用标准REST/GraphQL模式
   - 将OpenAPI/GraphQL模式输出到 `/contracts/`

3. **代理上下文更新**:
   - 运行 `{AGENT_SCRIPT}`
   - 这些脚本检测正在使用的AI代理
   - 更新相应的代理特定上下文文件
   - 仅添加当前计划中的新技术
   - 保留标记之间的手动添加

**输出**: data-model.md、/contracts/*、quickstart.md、代理特定文件

## 关键规则

- 使用绝对路径
- 门控失败或未解决澄清时报错
