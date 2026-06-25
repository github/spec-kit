<div align="center">
    <img src="./media/logo_large.webp" alt="Spec Kit Logo" width="180" height="180"/>
    <h1>Spec Kit Local Extensions</h1>
    <h3><em>面向本地增强工作流的 Spec Kit 分发版。</em></h3>
</div>

<p align="center">
    <strong>这个仓库的重点不是复述基础用法，而是打包一组本地扩展和预设，让规格、架构、证据、预览、治理和多 agent 实现流程连成一条可审查的链路。</strong>
</p>

---

## 本地定位

这个 checkout 是一个带本地增强能力的 Spec Kit 仓库。它保留核心 `specify` 工作流，同时默认安装一组本地扩展和一个默认预设。

本 README 只介绍仓库中实际存在的本地内容：

- `extensions/` 下的本地扩展。
- `presets/` 下的本地预设。
- `specify init` 默认会安装的增强能力。
- 需要手动安装的可选能力。
- 扩展和预设运行后会写入的主要产物。

如果你只是想知道这个仓库相比基础流程多了什么，可以先看这三件事：

- 默认扩展：`arch`、`discovery`、`intake`、`preview`、`repository-governance`。
- 默认预设：`workflow-preset`。
- 自动上下文扩展：`agent-context`。

## 快速开始

在本仓库开发或试用时，优先从仓库地址安装 CLI：

```bash
uv tool install specify-cli --from git+https://github.com/bigsmartben/spec-kit.git
```

初始化一个项目：

```bash
specify init my-project --integration codex
cd my-project
```

在已有目录里初始化：

```bash
specify init . --integration codex --force
```

如果当前机器没有对应 agent CLI，但你只想生成文件：

```bash
specify init my-project --integration codex --ignore-agent-tools
```

初始化完成后，本地默认能力会被复制到项目的 `.specify/` 目录，并注册到所选 agent 的命令或 skill 目录中。

## 默认安装内容

`specify init` 当前默认安装这些本地扩展和预设：

| 类型 | ID | 来源目录 | 作用 |
| --- | --- | --- | --- |
| 自动扩展 | `agent-context` | `extensions/agent-context` | 维护 AGENTS、CLAUDE、Copilot 等 agent context 文件里的 Spec Kit 受管段。 |
| 默认扩展 | `arch` | `extensions/arch` | 生成或反向生成项目级 4+1 架构视图，形成架构 SSOT。 |
| 默认扩展 | `discovery` | `extensions/discovery` | 在正式计划前做可行性、技术选型、旧代码评估、接口理解、PoC 和场景化技术决策。 |
| 默认扩展 | `intake` | `extensions/intake` | 把 PRD、设计稿、Figma、测试用例等来源归一化为 SDD 可消费的证据包。 |
| 默认扩展 | `preview` | `extensions/preview` | 从规格和计划生成低、中、高保真 Markdown 或自包含 HTML 预览。 |
| 默认扩展 | `repository-governance` | `extensions/repository-governance` | 生成仓库治理 SSOT，帮助 agent 明确目录责任、读取顺序和事实证据。 |
| 默认预设 | `workflow-preset` | `presets/workflow-preset` | 强化 BDD、NFR、UIF、设计产物、任务验证策略和 implement handoff 编排。 |

默认扩展列表在 `src/specify_cli/commands/init.py` 的 `DEFAULT_BUNDLED_EXTENSIONS` 中维护。默认预设列表在同文件的 `DEFAULT_BUNDLED_PRESETS` 中维护。

## 默认扩展

### `arch`

`arch` 给项目补一层架构记忆。它不是 feature 计划，也不是实现设计；它负责把项目级边界、运行时职责、部署假设、约束和架构缺口写成稳定 SSOT。

常用命令：

```text
/speckit.arch.scenario-generate
/speckit.arch.logical-generate
/speckit.arch.process-generate
/speckit.arch.development-generate
/speckit.arch.physical-generate
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
.specify/memory/architecture-repo-facts.md
```

使用建议：

- 新项目先跑 `*-generate`，把目标架构讲清楚。
- 旧仓库先跑 `*-reverse`，从真实文件、入口、配置、测试和部署线索反推架构事实。
- 五个视图都足够具体后，再让 `architecture.md` 成为后续规划的架构摘要。

### `discovery`

`discovery` 放在 `/speckit.plan` 之前，用来处理“不确定能不能做、怎么做更稳、旧代码到底长什么样”这类问题。

常用命令：

```text
/speckit.discovery.feasibility
/speckit.discovery.techselect
/speckit.discovery.decision
/speckit.discovery.codebase
/speckit.discovery.codebase-api-imp
/speckit.discovery.poc
```

适合场景：

- 需要做 go/no-go 可行性判断。
- 需要比较多个技术方案。
- 需要在 API、性能、迁移、UX、兼容性之间做场景化决策。
- 接手旧代码，需要先评估风险、复用资产和集成边界。
- 需要解释一个已实现 API、SDK 方法、CLI 命令、消息 topic 或内部能力的真实执行路径。
- 静态判断不够，需要一个有边界的 PoC。

典型产物会写在当前 feature 的 discovery 相关文件中，例如 feasibility、tech-selection、legacy codebase risk、PoC plan/result 或 API implementation overview。

### `intake`

`intake` 负责把外部输入变成可追踪证据，而不是直接替你生成需求。它的重点是保留来源、标记不确定性、做结构化归一化，让后续 `/speckit.specify`、`/speckit.plan` 能带着证据继续工作。

常用命令：

```text
/speckit.intake.prd
/speckit.intake.visual-design
/speckit.intake.test-cases
```

支持来源：

- PRD、产品说明、Markdown、PDF、导出的文档。
- 图片、线框图、设计 PDF、Figma 文件、Figma 页面或节点。
- 既有测试、Gherkin、手工测试用例、QA 导出、测试管理表格。

主要产物：

```text
specs/<feature>/intake/prd/
specs/<feature>/intake/visual-design/
specs/<feature>/intake/test-cases/
```

这些目录中会包含 source manifest、source files、归一化 YAML、evidence packet 和 schema 校验所需材料。

### `preview`

`preview` 在实现前生成评审产物。它不改应用源码，不替代实现；它用当前 feature 的规格、计划和契约生成可以讨论的 wireflow 或 HTML 预览。

常用命令：

```text
/speckit.preview.low-md
/speckit.preview.low-html
/speckit.preview.mid-md
/speckit.preview.mid-html
/speckit.preview.high-md
/speckit.preview.high-html
```

主要产物：

```text
specs/<feature>/preview/wireflow-low.md
specs/<feature>/preview/wireflow-low.html
specs/<feature>/preview/wireflow-mid.md
specs/<feature>/preview/wireflow-mid.html
specs/<feature>/preview/wireflow-high.md
specs/<feature>/preview/wireflow-high.html
```

使用建议：

- 需求还早期：用 `low-md` 或 `low-html` 看主路径和分支。
- 产品、设计和工程需要一起评审：用 `mid-md` 或 `mid-html`。
- 交互、状态、权限、响应式和错误反馈要确认：用 `high-md` 或 `high-html`。

### `repository-governance`

`repository-governance` 生成 agent 可读的仓库治理说明。它把目录职责、SSOT 读取顺序、工具链证据、agent 平台适配和仓库事实投影到当前 agent 的上下文文件中。

常用命令：

```text
/speckit.repository-governance.generate
```

它也注册了 hook，可在 constitution、plan、tasks 之后提示生成或更新治理内容。

主要产物：

```text
.specify/memory/repository-governance.md
```

以及当前集成对应的 agent context 文件中的受管治理段。

使用建议：

- 多 agent 协作时使用。
- 新人或新 agent 接手仓库时使用。
- 仓库目录结构、构建工具、SSOT 或平台适配规则变化后使用。

### `agent-context`

`agent-context` 是上下文维护扩展。它读取集成元数据，并更新当前 agent 的说明文件，例如 `AGENTS.md`、`CLAUDE.md` 或 `.github/copilot-instructions.md`。

常用命令：

```text
/speckit.agent-context.update
```

它主要维护受管 Spec Kit 段，不应覆盖用户在标记之外手写的内容。

## 默认预设

### `workflow-preset`

`workflow-preset` 是这个本地分发版的核心增强预设。它包装或替换核心命令，让规格驱动流程更适合复杂功能和多 agent 实现。

它会增强这些命令：

```text
/speckit.specify
/speckit.clarify
/speckit.checklist
/speckit.constitution
/speckit.analyze
/speckit.plan
/speckit.tasks
/speckit.implement
```

主要增强：

- `/speckit.checklist` 增加 BDD、NFR、视觉保真 readiness gate。
- `/speckit.constitution` 增加 Change Scope Granularity 治理。
- `/speckit.plan` 增加 Phase 0 行为投影、BDD/UIF/data fixture intent 和可选设计产物。
- `/speckit.tasks` 从行为契约、接口契约、`research.md`、`quickstart.md` 派生验证策略。
- `/speckit.implement` 使用 Core Agent、Vertical Planner、Worker 的 handoff 编排。
- 最终实现阶段包含 code review receipt，记录 checked sources、数据副作用审查、授权修复和延期验证 todo。

典型产物：

```text
specs/<feature>/contracts/bdd/
specs/<feature>/contracts/uif/
specs/<feature>/contracts/behavior/
specs/<feature>/handoffs/implement/<run-id>/
```

实现 handoff 相关 schema 由 `presets/workflow-preset/schemas/` 提供。

## 可选本地扩展

### `bug`

`bug` 提供三段式 bug 工作流：评估、修复、验证。

命令：

```text
/speckit.bug.assess
/speckit.bug.fix
/speckit.bug.test
```

主要产物：

```text
.specify/bugs/<slug>/assessment.md
.specify/bugs/<slug>/fix.md
.specify/bugs/<slug>/test.md
```

安装：

```bash
specify extension add bug
```

### `git`

`git` 是内置可选扩展，不在当前默认扩展列表中。它负责 Git 初始化、feature branch、branch validation、remote 检测和可配置自动提交。

命令：

```text
/speckit.git.initialize
/speckit.git.feature
/speckit.git.validate
/speckit.git.remote
/speckit.git.commit
```

配置文件：

```text
.specify/extensions/git/git-config.yml
```

安装：

```bash
specify extension add git
```

## 可选本地预设

### `lean`

`lean` 把核心流程压缩成更轻量的命令，适合小功能、实验、低仪式感任务。

它覆盖这些命令：

```text
/speckit.constitution
/speckit.specify
/speckit.plan
/speckit.tasks
/speckit.implement
```

安装：

```bash
specify preset add lean
```

### `arch-governance`

`arch-governance` 位于：

```text
extensions/arch/presets/arch-governance/
```

它包装 `/speckit.plan`，让规划阶段显式读取 `arch` 扩展产出的架构 SSOT。适合已经用 `arch` 维护架构记忆，并希望每次 feature plan 都检查架构边界的项目。

从本地目录安装：

```bash
specify preset add --dev .specify/extensions/arch/presets/arch-governance
```

如果是在这个仓库源码中测试，可使用源码路径：

```bash
specify preset add --dev extensions/arch/presets/arch-governance
```

## 开发和测试用本地包

这些目录主要服务扩展/预设作者或测试，不建议作为普通项目主流程：

| 类型 | ID | 来源目录 | 用途 |
| --- | --- | --- | --- |
| 扩展模板 | `template` | `extensions/template` | 新扩展作者复制和改造的起始模板。 |
| 扩展测试 | `selftest` | `extensions/selftest` | 验证扩展发现、安装和注册生命周期。 |
| 预设模板 | `scaffold` | `presets/scaffold` | 新预设作者复制和改造的起始模板。 |
| 预设测试 | `self-test` | `presets/self-test` | 覆盖核心模板和命令，用于测试 preset 解析与组合。 |

## 推荐使用路径

### 新项目

```text
/speckit.constitution
/speckit.arch.scenario-generate
/speckit.arch.logical-generate
/speckit.arch.process-generate
/speckit.arch.development-generate
/speckit.arch.physical-generate
/speckit.specify
/speckit.clarify
/speckit.discovery.feasibility
/speckit.plan
/speckit.preview.mid-html
/speckit.tasks
/speckit.analyze
/speckit.implement
```

### 旧仓库接入

```text
/speckit.constitution
/speckit.discovery.codebase
/speckit.arch.scenario-reverse
/speckit.arch.logical-reverse
/speckit.arch.process-reverse
/speckit.arch.development-reverse
/speckit.arch.physical-reverse
/speckit.repository-governance.generate
/speckit.specify
/speckit.plan
/speckit.tasks
/speckit.implement
```

### 已有 PRD、设计或测试用例

```text
/speckit.intake.prd
/speckit.intake.visual-design
/speckit.intake.test-cases
/speckit.specify
/speckit.clarify
/speckit.plan
```

### 前端和交互功能

```text
/speckit.intake.visual-design
/speckit.specify
/speckit.preview.low-md
/speckit.plan
/speckit.preview.mid-html
/speckit.tasks
/speckit.implement
```

### 大型或跨模块实现

保留默认 `workflow-preset`，让 `/speckit.implement` 生成 handoff manifest、context digest、worker handoff 和 receipt。

重点查看：

```text
specs/<feature>/handoffs/implement/<run-id>/
```

### 小功能或实验

```bash
specify preset add lean
```

然后使用轻量核心链路：

```text
/speckit.specify
/speckit.plan
/speckit.tasks
/speckit.implement
```

### Bug 修复

```bash
specify extension add bug
```

然后：

```text
/speckit.bug.assess
/speckit.bug.fix
/speckit.bug.test
```

## 产物地图

| 目录或文件 | 来源 | 含义 |
| --- | --- | --- |
| `.specify/memory/architecture*.md` | `arch` | 4+1 架构视图和综合架构 SSOT。 |
| `.specify/memory/architecture-repo-facts.md` | `arch` reverse 命令 | 从既有仓库提取的架构事实。 |
| `.specify/memory/repository-governance.md` | `repository-governance` | 内部仓库治理 SSOT。 |
| `specs/<feature>/intake/` | `intake` | PRD、视觉设计、测试用例的结构化证据包。 |
| `specs/<feature>/preview/` | `preview` | Markdown wireflow 和自包含 HTML 预览。 |
| `specs/<feature>/contracts/bdd/` | `workflow-preset` | BDD 行为契约。 |
| `specs/<feature>/contracts/uif/` | `workflow-preset` | UI flow / interface fidelity 契约。 |
| `specs/<feature>/contracts/behavior/` | `workflow-preset` | 行为场景、fixture、assertion 等正式契约。 |
| `specs/<feature>/handoffs/implement/<run-id>/` | `workflow-preset` | implement 阶段多 agent handoff、context digest、receipt。 |
| `.specify/bugs/<slug>/` | `bug` | 单个 bug 的 assess/fix/test 报告。 |
| `.specify/extensions/git/git-config.yml` | `git` | Git 分支和自动提交配置。 |

## 本地安装和管理

查看已安装扩展：

```bash
specify extension list
```

安装本地内置扩展：

```bash
specify extension add bug
specify extension add git
```

从本地源码目录安装扩展：

```bash
specify extension add --dev extensions/preview
specify extension add --dev extensions/intake
```

查看已安装预设：

```bash
specify preset list
```

安装本地内置预设：

```bash
specify preset add lean
```

从本地源码目录安装预设：

```bash
specify preset add --dev presets/workflow-preset
```

禁用或启用扩展：

```bash
specify extension disable preview
specify extension enable preview
```

移除预设：

```bash
specify preset remove lean
```

## 开发验证

本仓库是 Python 项目。常用验证命令：

```bash
uv run pytest
```

只验证集成相关测试：

```bash
uv run pytest tests/integrations -v
```

验证本地扩展或预设时，优先在临时项目中使用 `--dev` 安装源码目录：

```bash
specify extension add --dev extensions/preview
specify extension add --dev extensions/intake
specify preset add --dev presets/workflow-preset
```

## 维护提示

- README 中的默认扩展和默认预设必须与 `src/specify_cli/commands/init.py` 保持一致。
- 扩展命令清单应以各自 `extension.yml` 为准。
- 预设覆盖关系应以各自 `preset.yml` 为准。
- `git` 是本地内置可选扩展，不应写成默认安装。
- `template`、`selftest`、`scaffold`、`self-test` 是开发/测试用途，不应包装成普通用户主路径。

## 许可证

本项目使用 MIT License。详见 [LICENSE](./LICENSE)。
