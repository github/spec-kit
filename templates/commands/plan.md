---
description: 执行实施规划工作流, 使用计划模板生成设计制品.
handoffs:
  - label: 创建任务
    agent: speckit.tasks
    prompt: 将计划分解为任务
    send: true
  - label: 创建检查清单
    agent: speckit.checklist
    prompt: 为需求创建质量检查清单
    send: true
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

您**必须**在继续之前考虑用户输入(如果不为空).

## Outline

1. **设置**: 从存储库根目录运行 `{SCRIPT}` 并解析 JSON 以获取 FEATURE_SPEC, IMPL_PLAN, SPECS_DIR, BRANCH. 对于像 "I'm Groot" 这样的参数中的单引号, 使用转义语法: 例如 'I'\''m Groot' (或如果可能,使用双引号: "I'm Groot").

2. **加载上下文**: 读取 FEATURE_SPEC 和 `/memory/constitution.md`. 加载 IMPL_PLAN 模板(已复制).

3. **执行计划工作流**: 按照 IMPL_PLAN 模板中的结构执行以下操作:
   - 填充技术上下文(将未知项标记为 "NEEDS CLARIFICATION")
   - 从 constitution 填充检查部分
   - 评估门控(如果违规未justify, 则报错)
   - Phase 0: 生成 research.md (解决所有 NEEDS CLARIFICATION)
   - Phase 1: 生成 data-model.md, contracts/, quickstart.md
   - Phase 1: 更新代理上下文, 运行代理脚本
   - Re-evaluate Constitution: 检查是否所有 NEEDS CLARIFICATION 已解决
   - Phase 2: 生成 tasks.md, checklist.md
   - Check post-design: 验证设计是否符合规范要求

4. **Stop and report**: Command ends after Phase 2 planning. Report branch, IMPL_PLAN path, and generated artifacts.

## 阶段

### Phase 0: 大纲 & 研究

1. **从技术上下文提取未知项**以上:
   - 对于每个 NEEDS CLARIFICATION → 研究任务
   - 对于每个依赖项 → 最佳实践任务
   - 对于每个集成 → 模式任务

2. **生成并调度研究代理**:

   ```text
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **整合发现**在 `research.md` 中使用格式:
   - 决策: [选择了什么]
   - 理由: [为什么选择]
   - 考虑的替代方案: [评估了什么]

**输出**: 所有 NEEDS CLARIFICATION 已解决的 research.md

### Phase 1: Design & Contracts

**先决条件:** `research.md` 已完成

1. **从功能规范提取实体** → `data-model.md`:
   - 实体名称, 字段, 关系
   - 从需求中提取验证规则
   - 如果适用, 则提取状态转换

2. **根据功能需求生成 API 合同**:
   - 对于每个用户操作 → 端点
   - 使用标准 REST/GraphQL 模式
   - 将 OpenAPI/GraphQL 模式输出到 `/contracts/`

3. **代理上下文更新**:
   - 运行 `{AGENT_SCRIPT}`
   - 这些脚本检测当前正在使用的 AI 代理
   - 更新相应的代理特定上下文文件
   - 仅添加当前计划中的新技术
   - 保留标记之间的手动添加

**Output输出**: data-model.md, /contracts/*, quickstart.md, agent-specific file

## 关键规则

- 使用绝对路径
- 门控失败或未解决的澄清项时, 报错 (ERROR)
