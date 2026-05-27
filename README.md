<div align="center">
    <img src="./media/logo_large.webp" alt="Spec Kit Logo" width="180" height="180"/>
    <h1>Spec Kit</h1>
    <h3><em>用规格驱动 AI 编码，而不是靠一次性提示词碰运气。</em></h3>
</div>

<p align="center">
    <strong>Spec Kit 帮你把想法拆成原则、规格、计划、任务和实现，让 AI 编码助手按可追踪的工程流程工作。</strong>
</p>

<p align="center">
    <a href="https://github.com/bigsmartben/spec-kit/releases"><img src="https://img.shields.io/github/v/release/bigsmartben/spec-kit" alt="Latest Release"/></a>
    <a href="https://github.com/bigsmartben/spec-kit/stargazers"><img src="https://img.shields.io/github/stars/bigsmartben/spec-kit?style=social" alt="GitHub stars"/></a>
    <a href="https://github.com/bigsmartben/spec-kit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/bigsmartben/spec-kit" alt="License"/></a>
</p>

---

## 这是什么

Spec Kit 是一套面向使用者的 Spec-Driven Development 工具链。你先把项目目标写成清楚的规格，再让 AI 编码助手根据规格生成技术计划、任务列表并执行实现。

它适合这些场景：

- 从零开始做一个新功能或新项目。
- 给已有仓库补一套规格、架构记忆和实现流程。
- 让 AI agent 在改代码前先澄清需求、留下计划和可审查的任务。
- 团队希望统一不同 AI 编码助手的工作方式。

核心思路很直接：先讲清楚“要做什么”和“为什么”，再决定“怎么做”，最后按任务执行。

## 快速开始

### 1. 安装

推荐使用 [uv](https://docs.astral.sh/uv/)。最近已发布的固定内部版本安装命令如下：

```bash
uv tool install specify-cli --from git+https://github.com/bigsmartben/spec-kit.git@bigsmartben-v0.8.13-community.3
```

如果你要跟随当前分支安装，包括本仓库源码中已集成的 `workflow-preset` v1.2.0，可以使用：

```bash
uv tool install specify-cli --from git+https://github.com/bigsmartben/spec-kit.git
```

本地开发这个仓库时，可以从当前目录安装：

```bash
uv tool install --force ./
```

### 2. 初始化项目

选择你正在使用的 AI 编码助手。下面以 Claude Code 为例：

```bash
specify init my-project --integration claude
cd my-project
```

在已有目录里初始化：

```bash
specify init . --integration codex --force
```

如果你的 agent 工具没有安装，但你只想先生成文件：

```bash
specify init my-project --integration copilot --ignore-agent-tools
```

Codex 和部分 agent 支持 skills 模式：

```bash
specify init my-project --integration codex --integration-options="--skills"
```

查看当前安装支持哪些集成：

```bash
specify integration list
```

### 3. 开始一次规格驱动流程

进入项目目录，打开你的 AI 编码助手，然后按顺序使用 Spec Kit 命令。

```text
/speckit.constitution
```

先建立项目原则，例如代码质量、测试要求、用户体验、性能边界和架构约束。

```text
/speckit.specify Build a photo album app. Users can create albums, group photos by date, reorder albums by drag and drop, and preview photos as tiles.
```

创建功能规格。这里重点写“用户需要什么”和“为什么需要”，不要过早指定技术栈。

```text
/speckit.clarify
```

让 agent 追问缺失或含糊的需求，并把答案写回规格。

```text
/speckit.plan Use Vite, TypeScript, SQLite, and a minimal dependency set. Store metadata locally and do not upload images.
```

生成技术计划。这里再说明框架、数据库、部署方式、约束和工程偏好。

```text
/speckit.tasks
```

把规格和计划拆成可执行任务。

```text
/speckit.analyze
```

在实现前检查规格、计划和任务之间是否有冲突或遗漏。

```text
/speckit.implement
```

让 agent 按任务实现，并在任务文件中记录进度。

## 常用命令

| 命令 | 作用 |
| --- | --- |
| `/speckit.constitution` | 创建或更新项目原则，后续规格、计划和实现都会引用它。 |
| `/speckit.specify` | 写功能规格，关注需求、用户故事和验收标准。 |
| `/speckit.clarify` | 追问需求缺口，降低计划和实现阶段返工。 |
| `/speckit.plan` | 根据规格和你的技术约束生成实现计划。 |
| `/speckit.tasks` | 生成按依赖排序的任务清单。 |
| `/speckit.checklist` | 生成质量检查清单，用来审查规格完整性。 |
| `/speckit.analyze` | 检查规格、计划、任务之间的一致性和覆盖度。 |
| `/speckit.taskstoissues` | 把任务转换成 GitHub issues。 |
| `/speckit.implement` | 按任务执行实现。 |

某些集成使用 skills 而不是 slash commands。命令名通常会对应为 `speckit-<name>` skill，例如 `speckit-specify`、`speckit-plan`。

## 本仓库内置扩展

这个仓库不是只有 Spec Kit 核心流程，还带了可直接安装或默认安装的扩展。扩展用于增加新命令、新 hook 或额外工作流。

| 扩展 | 默认状态 | 你会用它做什么 |
| --- | --- | --- |
| `arch` | `specify init` 默认安装 | 生成或反向生成项目级 4+1 架构视图，形成 `.specify/memory/architecture*.md` 架构记忆。 |
| `preview` | `specify init` 默认安装 | 根据当前 feature 的规格和计划生成 `specs/<feature>/preview/index.html`，用于实现前验证 UI 和交互假设。 |
| `repository-governance` | 按需安装 | 生成 Repository Governance Framework 治理说明，包含垂直 SSOT 注册、读取顺序、缺失 SSOT 处理和仓库事实证据。 |
| `git` | 初始化时默认安装，传 `--no-git` 可跳过 | 初始化 Git、创建 feature branch、校验分支、检测 remote，并可配置自动提交。 |
| `template` | 开发模板 | 给扩展作者复制使用，不是普通项目必装扩展。 |
| `selftest` | 测试工具 | 用于验证扩展目录和 catalog 生命周期，主要服务仓库维护。 |

手动安装或重新安装扩展示例：

```bash
specify extension add arch
specify extension add preview
specify extension add repository-governance
specify extension add git
```

查看扩展：

```bash
specify extension search
specify extension info arch
```

扩展命令示例：

```text
/speckit.arch.generate
/speckit.arch.reverse
/speckit.preview.html
/speckit.repository-governance.refresh
```

### 什么时候用这些扩展

- 新项目或架构正在变化：先跑 `/speckit.arch.generate`，让后续计划有稳定架构上下文。
- 接手旧仓库：跑 `/speckit.arch.reverse`，先从仓库事实反推架构记忆。
- 做前端或交互功能：在 `/speckit.specify` 或 `/speckit.plan` 后跑 `/speckit.preview.html`，先看原型再实现。
- 团队使用多个 agent：用 `repository-governance` 维护仓库级治理框架和 agent 执行边界，减少上下文漂移。
- 希望 feature 分支和提交更规范：保留 `git` 扩展，按需要配置 `.specify/extensions/git/git-config.yml`。

## 本仓库内置预设

预设用于改变核心命令和模板的行为。它不一定新增能力，而是改变 Spec Kit 怎样产出规格、计划、任务和实现指令。

| 预设 | 默认状态 | 你会用它做什么 |
| --- | --- | --- |
| `workflow-preset` | `specify init` 默认安装 | 增加 BDD readiness gate、Phase 0 行为投影、设计产物和任务期验证策略派生，并把 `/speckit.implement` 改成 Core/Vertical Planner/Worker 三层 handoff 编排流程。 |
| `lean` | 手动安装 | 用更短的核心命令模板产出规格、计划、任务和实现，适合小功能、实验和低仪式感项目。 |
| `scaffold` | 开发模板 | 给预设作者复制使用，不是普通项目必装预设。 |
| `self-test` | 测试工具 | 用于验证预设覆盖和模板解析，主要服务仓库维护。 |

手动安装预设：

```bash
specify preset add lean
specify preset add workflow-preset
```

查看预设：

```bash
specify preset search
specify preset info workflow-preset
```

### 默认工作流预设带来的变化

`workflow-preset` v1.2.0 会保留 Spec Kit 的核心路径，但让复杂实现更容易拆分：

- `/speckit.checklist` 会在规划前检查 BDD readiness，缺口回到 clarify/specify。
- `/speckit.plan` 通过 Phase 0 把已通过质量门禁的需求投影为 BDD、UIF intent 和 fixture intent 草稿。
- `/speckit.plan` 可以补充对象设计和服务时序等设计产物。
- `/speckit.tasks` 不再要求独立测试策略文件，而是从行为契约、接口契约、`research.md` 和 `quickstart.md` 派生测试层级、fixture/mock/sandbox 策略和验证证据要求。
- `/speckit.implement` 会生成 handoff manifest、Vertical Planner 输出、worker handoff、context digest 和 receipt，让多 agent 或多阶段实现更可审查。

如果你的项目很小，可以安装 `lean`，用更轻量的规格到实现流程。

## 支持的 AI 编码助手

当前仓库通过 integration registry 支持多种 CLI 和 IDE agent。常用 key 包括：

```text
agy, amp, auggie, bob, claude, codebuddy, codex, copilot,
cursor-agent, devin, forge, gemini, generic, goose, iflow,
junie, kilocode, kimi, kiro-cli, lingma, opencode, pi,
qodercli, qwen, roo, shai, tabnine, trae, vibe, windsurf
```

初始化时用 `--integration <key>` 指定。CLI 型集成会检查对应工具是否存在；IDE 型集成会写入该工具需要的命令、规则或上下文文件。

如果你的工具不在列表里，可以使用 generic 集成并指定命令目录：

```bash
specify init my-project --integration generic --integration-options="--commands-dir .my-agent/commands"
```

## 初始化后会生成什么

一个典型项目会包含：

```text
.specify/
  memory/
    constitution.md
    architecture.md
  templates/
  scripts/
  extensions/
  presets/
  workflows/
specs/
  001-your-feature/
    spec.md
    plan.md
    tasks.md
```

agent 集成还会创建对应工具的命令目录和上下文文件，例如：

```text
.claude/skills/
CLAUDE.md

.github/agents/
.github/prompts/
.github/copilot-instructions.md

.agents/skills/
AGENTS.md
```

实际路径取决于你选择的 `--integration`。

## 推荐使用顺序

### 新项目

```text
/speckit.constitution
/speckit.arch.generate
/speckit.specify
/speckit.clarify
/speckit.preview.html
/speckit.plan
/speckit.tasks
/speckit.analyze
/speckit.implement
```

### 旧仓库接入

```text
/speckit.constitution
/speckit.arch.reverse
/speckit.repository-governance.refresh
/speckit.specify
/speckit.clarify
/speckit.plan
/speckit.tasks
/speckit.analyze
/speckit.implement
```

### 小功能或实验

```bash
specify preset add lean
```

然后使用核心链路：

```text
/speckit.specify
/speckit.plan
/speckit.tasks
/speckit.implement
```

## 常见操作

升级 CLI：

```bash
uv tool upgrade specify-cli
```

卸载某个集成：

```bash
specify integration uninstall <key>
```

升级当前项目里的集成文件：

```bash
specify integration upgrade
```

禁用或启用扩展：

```bash
specify extension disable git
specify extension enable git
```

移除预设：

```bash
specify preset remove lean
```

## 使用建议

- 写 `/speckit.specify` 时只写需求和业务规则，技术栈留给 `/speckit.plan`。
- 在 `/speckit.plan` 前运行 `/speckit.clarify`，可以减少实现阶段反复改规格。
- 对 UI 或流程不确定的功能，先用 `/speckit.preview.html` 看一个可打开的 HTML 原型。
- 对中大型功能，保留默认 `workflow-preset`，让任务和实现阶段通过验证证据、handoff 和 receipt 留下可审查记录。
- 对非常小的实验，使用 `lean`，减少模板负担。
- 如果 agent 生成了你没要求的复杂设计，让它回到 `spec.md`、`plan.md` 和 `.specify/memory/constitution.md` 逐条解释依据。

## 更多文档

- [完整方法论](./spec-driven.md)
- [安装指南](./docs/installation.md)
- [快速开始](./docs/quickstart.md)
- [扩展系统](./extensions/README.md)
- [预设系统](./presets/README.md)
- [集成 catalog](./integrations/README.md)
- [本地开发](./docs/local-development.md)

## 开发和验证

本仓库本身是 Python 项目。常用验证命令：

```bash
uv run pytest
```

只验证集成相关测试：

```bash
uv run pytest tests/integrations -v
```

验证某个扩展或预设时，优先在临时项目中安装本地目录：

```bash
specify extension add --dev ./extensions/preview
specify preset add --dev ./presets/workflow-preset
```

## 许可证

本项目使用 MIT License。详见 [LICENSE](./LICENSE)。

## 致谢

本仓库维护了面向当前使用场景的 Spec Kit 分发、扩展和预设。
