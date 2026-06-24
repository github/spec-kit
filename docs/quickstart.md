# 快速开始

这份指南面向本仓库分发版的 Spec Kit。它保留核心 Spec-Driven Development 流程，同时默认带上架构 SSOT、仓库治理、BDD/UIF 行为契约、HTML 预览、实现期 handoff 和最终 code review receipt。

> [!NOTE]
> 自动化脚本同时提供 Bash (`.sh`) 和 PowerShell (`.ps1`) 版本。`specify` CLI 会按系统自动选择，也可以通过 `--script sh|ps` 显式指定。

## 推荐流程

> [!TIP]
> Spec Kit 会根据当前 Git 分支自动识别 active feature，例如 `001-photo-album`。切换规格时通常只需要切换分支。

生产功能建议使用默认增强链路：

```text
/speckit.constitution
/speckit.arch.scenario-generate
/speckit.arch.logical-generate
/speckit.arch.process-generate
/speckit.arch.development-generate
/speckit.arch.physical-generate
/speckit.repository-governance.refresh
/speckit.specify
/speckit.clarify
/speckit.checklist
/speckit.preview.mid-html
/speckit.plan
/speckit.tasks
/speckit.analyze
/speckit.implement
```

接手旧仓库时，把五个 `/speckit.arch.*-generate` 换成对应的 `/speckit.arch.*-reverse`，先从仓库事实反向生成架构 SSOT。

小实验可以安装 `lean` 预设后走轻量路径：

```bash
specify preset add lean
```

```text
/speckit.specify -> /speckit.plan -> /speckit.tasks -> /speckit.implement
```

## 1. 安装 Specify

推荐使用 [uv](https://docs.astral.sh/uv/) 持久安装：

```bash
uv tool install specify-cli --from git+https://github.com/bigsmartben/spec-kit.git
```

从仓库地址安装：

```bash
uv tool install specify-cli --from git+https://github.com/bigsmartben/spec-kit.git
```

也可以一次性运行：

```bash
uvx --from git+https://github.com/bigsmartben/spec-kit.git specify init my-project
```

显式选择脚本类型：

```bash
specify init my-project --script ps  # Force PowerShell
specify init my-project --script sh  # Force POSIX shell
```

## 2. 初始化项目

选择你正在使用的 AI 编码助手：

```bash
specify init my-project --integration codex
cd my-project
```

在已有仓库中初始化：

```bash
specify init . --integration codex --force
```

如果 agent 工具没有安装，但你只想先生成 Spec Kit 文件：

```bash
specify init my-project --integration copilot --ignore-agent-tools
```

Codex 和部分 agent 支持 skills 模式：

```bash
specify init my-project --integration codex --integration-options="--skills"
```

查看当前支持的集成：

```bash
specify integration list
```

## 3. 建立项目原则与治理

在编码助手中先建立项目原则：

```text
/speckit.constitution This project uses behavior-first requirements, keeps architecture decisions explicit, and requires validation evidence before tasks are marked complete.
```

刷新仓库治理规范：

```text
/speckit.repository-governance.refresh
```

治理命令会生成或更新当前 integration 对应的 agent 上下文文件中的受管段，并维护内部治理记忆：

```text
.specify/memory/repository-governance.md
```

它用于约束 SSOT 读取顺序、目录责任、agent 平台适配和仓库事实证据。

## 4. 生成 ARCH SSOT

新项目或架构正在重塑时：

```text
/speckit.arch.scenario-generate
/speckit.arch.logical-generate
/speckit.arch.process-generate
/speckit.arch.development-generate
/speckit.arch.physical-generate
```

接手已有仓库时：

```text
/speckit.arch.scenario-reverse
/speckit.arch.logical-reverse
/speckit.arch.process-reverse
/speckit.arch.development-reverse
/speckit.arch.physical-reverse
```

主要产物：

```text
.specify/memory/architecture.md
.specify/memory/architecture-scenario-view.md
.specify/memory/architecture-logical-view.md
.specify/memory/architecture-process-view.md
.specify/memory/architecture-development-view.md
.specify/memory/architecture-physical-view.md
.specify/memory/architecture-repo-facts.md   # reverse 额外使用
```

后续 `/speckit.plan` 会基于这些架构边界、约束、反模式和未解缺口进行规划。

## 5. 创建并澄清规格

创建功能规格时只描述用户目标、业务规则和验收语义，不要过早指定技术栈：

```text
/speckit.specify Build a photo album app. Users can create albums, group photos by date, reorder albums by drag and drop, and preview photos as tiles. The UI must support mobile browsing and desktop bulk organization.
```

澄清缺口：

```text
/speckit.clarify Focus on album permissions, empty states, reorder conflict behavior, responsive UI states, and validation boundaries.
```

运行 BDD/NFR readiness gate：

```text
/speckit.checklist
```

检查生成的 readiness 清单：

```text
specs/<feature>/checklists/behavior-testability.md
```

如果清单指出 Given/When/Then、可观察结果、边界状态或 NFR 声明缺失，先回到 `/speckit.clarify` 或 `/speckit.specify` 补齐。

## 6. 预览 UI/UX 规格

对 UI、流程或交互有不确定性时，先生成保真度合适的预览产物：

```text
/speckit.preview.mid-html mobile album browsing and reorder flow
```

打开输出文件评审：

```text
specs/<feature>/preview/wireflow-mid.html
```

这个文件只用于实现前评审 flow、信息架构、状态和交互假设，不会修改生产代码。也可以按需要使用 `/speckit.preview.low-md`、`/speckit.preview.low-html`、`/speckit.preview.high-md` 或 `/speckit.preview.high-html`。

## 7. 生成计划与行为契约

规划阶段再指定技术栈和工程约束：

```text
/speckit.plan Use Vite, TypeScript, SQLite, and a minimal dependency set. Store photo metadata locally and do not upload images.
```

默认 `workflow-preset` 会把已通过 readiness gate 的需求投影为 BDD、UIF 和 fixture intent，并在规划中正式化为契约。常见产物包括：

```text
specs/<feature>/behavior/bdd.draft.feature
specs/<feature>/behavior/uif.intent.json
specs/<feature>/behavior/data-fixtures.intent.json
specs/<feature>/contracts/bdd/
specs/<feature>/contracts/uif/
specs/<feature>/contracts/behavior/
specs/<feature>/quickstart.md
```

`quickstart.md` 应包含可执行或可复现的验证路径，后续 tasks 和 code review receipt 会引用它。

## 8. 拆任务、分析并实现

生成任务：

```text
/speckit.tasks
```

默认任务生成会从 BDD、UIF、行为契约、接口契约、`research.md` 和 `quickstart.md` 派生测试层级、fixture/mock/sandbox 策略和验证证据要求。

实现前做一致性检查：

```text
/speckit.analyze
```

开始实现：

```text
/speckit.implement
```

中大型功能会进入 Core/Vertical Planner/Worker 三层 handoff 编排，常见输出：

```text
specs/<feature>/handoffs/implement/<run-id>/handoff-manifest.json
specs/<feature>/handoffs/implement/<run-id>/<shard>.json
specs/<feature>/handoffs/implement/<run-id>/<shard>.context.md
specs/<feature>/handoffs/implement/<run-id>/results/<shard>.json
```

如果当前 agent runtime 不支持隔离 subagent，按输出的新 worker 指令在干净会话中执行单个 handoff：

```text
/speckit.implement Use handoff JSON specs/<feature>/handoffs/implement/<run-id>/<shard>.json
```

Final Code Review 会以 `task_type: code_review` receipt 记录已检查的设计、sequence、contract、quickstart 来源、数据副作用审查、授权范围内的一致性修复和真实 e2e 缺口。

## 9. 可选：运行带 review gate 的 workflow

如果你想体验可恢复的端到端 workflow：

```bash
specify workflow add speckit
specify workflow run speckit --input spec="Build a small photo album app with album reorder and tile preview"
specify workflow status
specify workflow resume <run_id>
```

内置 `speckit` workflow 会串联 specify、plan、tasks、implement，并在 spec review 和 plan review 处暂停等待人工确认。

## 常见操作

查看增强能力：

```bash
specify extension search
specify preset search
specify workflow search
```

重新安装默认增强能力：

```bash
specify extension add arch
specify extension add preview
specify extension add repository-governance
specify preset add workflow-preset
```

升级当前项目中的 integration 文件：

```bash
specify integration upgrade
```

卸载某个 integration：

```bash
specify integration uninstall <key>
```

## 下一步

- 阅读 [完整方法论](../spec-driven.md)。
- 查看 [扩展系统](../extensions/README.md)、[预设系统](../presets/README.md) 和 [workflow 系统](../workflows/README.md)。
- 本地开发 CLI 时参考 [local-development](./local-development.md)。
