<div align="center">
    <img src="./media/logo_large.webp" alt="Spec Kit Logo" width="200" height="200"/>
    <h1>🌱 Spec Kit</h1>
    <h3><em>更快速地构建高质量软件。</em></h3>
</div>

<p align="center">
    <strong>一个开源工具集，让你专注于产品场景和可预测的结果，而不是从头开始凭感觉编写每一段代码。</strong>
</p>

<p align="center">
    <a href="https://github.com/github/spec-kit/actions/workflows/release.yml"><img src="https://github.com/github/spec-kit/actions/workflows/release.yml/badge.svg" alt="版本发布"/></a>
    <a href="https://github.com/github/spec-kit/stargazers"><img src="https://img.shields.io/github/stars/github/spec-kit?style=social" alt="GitHub stars"/></a>
    <a href="https://github.com/github/spec-kit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/github/spec-kit" alt="许可证"/></a>
    <a href="https://github.github.io/spec-kit/"><img src="https://img.shields.io/badge/文档-GitHub_Pages-blue" alt="文档"/></a>
</p>

---

## 目录

- [🤔 什么是规格驱动开发？](#-什么是规格驱动开发)
- [⚡ 开始使用](#-开始使用)
- [📽️ 视频概览](#️-视频概览)
- [🤖 支持的 AI 智能体](#-支持的 ai-智能体)
- [🔧 Specify CLI 参考](#-specify-cli-参考)
- [📚 核心理念](#-核心理念)
- [🌟 开发阶段](#-开发阶段)
- [🎯 实验目标](#-实验目标)
- [🔧 前提条件](#-前提条件)
- [📖 了解更多](#-了解更多)
- [📋 详细流程](#-详细流程)
- [🔍 故障排除](#-故障排除)
- [👥 维护者](#-维护者)
- [💬 支持](#-支持)
- [🙏 致谢](#-致谢)
- [📄 许可证](#-许可证)

## 🤔 什么是规格驱动开发？

规格驱动开发 (Spec-Driven Development, SDD) **颠覆了**传统的软件开发模式。几十年来，代码一直处于核心地位——而规格（Specifications）只是我们在开始“真正的”编码工作之前构建并随后丢弃的脚手架。规格驱动开发改变了这一点：**规格变得可执行**，直接生成可运行的实现，而不仅仅是起到指导作用。

## ⚡ 开始使用

### 1. 使用 Specify CLI

无需永久安装，你可以使用 `uvx` 直接从 GitHub 运行该工具：

```bash
# 创建新项目
uvx --from git+https://github.com/lizhouyang/spec-kit-trae.git specify init <PROJECT_NAME>

# 或在当前目录中初始化
uvx --from git+https://github.com/lizhouyang/spec-kit-trae.git specify init . --ai claude
# 或者
uvx --from git+https://github.com/lizhouyang/spec-kit-trae.git specify init --here --ai claude

# 检查环境及工具
uvx --from git+https://github.com/lizhouyang/spec-kit-trae.git specify check
```

### 2. 确立项目原则

在项目目录中启动你的 AI 助手。你可以直接在助手内使用 `/speckit.*` 系列斜杠命令。

使用 **`/speckit.constitution`** 命令来创建项目的治理原则和开发指南，这些原则将指导后续的所有开发工作。

```bash
/speckit.constitution 创建专注于代码质量、测试标准、用户体验一致性和性能要求的原则
```

### 3. 创建规格 (Spec)

使用 **`/speckit.specify`** 命令来描述你想要构建的内容。请关注**“做什么”**和**“为什么”**，而不是具体的技术栈。

```bash
/speckit.specify 构建一个可以帮助我整理相册的应用程序。相册按日期分组，并可以在主页上通过拖放重新组织。相册不会嵌套。在每个相册中，照片以瓷砖界面进行预览。
```

### 4. 创建技术实现方案

使用 **`/speckit.plan`** 命令来提供你的技术栈和架构选择。

```bash
/speckit.plan 该应用使用 Vite 和最少数量的库。尽可能使用原生 HTML、CSS 和 JavaScript。图像不上传到任何地方，元数据存储在本地 SQLite 数据库中。
```

### 5. 任务分解

使用 **`/speckit.tasks`** 根据你的实现方案创建可执行的任务列表。

```bash
/speckit.tasks
```

### 6. 执行实现

使用 **`/speckit.implement`** 执行所有任务并根据方案构建功能。

```bash
/speckit.implement
```

如需详细的分步说明，请参阅我们的[综合指南](./spec-driven.md)。

## 📽️ 视频概览

想看看 Spec Kit 的实际运作吗？观看我们的[视频概览](https://www.youtube.com/watch?v=a9eR1xsfvHg&pp=0gcJCckJAYcqIYzv)！

[![Spec Kit 视频封面](/media/spec-kit-video-header.jpg)](https://www.youtube.com/watch?v=a9eR1xsfvHg&pp=0gcJCckJAYcqIYzv)

## 🤖 支持的 AI 智能体

| 智能体 | 支持 | 备注 |
| ------------------------------------------------------------------------------------ | ------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| [Qoder CLI](https://qoder.com/cli)                                                   | ✅      |                                                                                                                                           |
| [Amazon Q Developer CLI](https://aws.amazon.com/developer/learning/q-developer-cli/) | ⚠️      | Amazon Q Developer CLI [不支持](https://github.com/aws/amazon-q-developer-cli/issues/3064)斜杠命令的自定义参数。 |
| [Amp](https://ampcode.com/)                                                          | ✅      |                                                                                                                                           |
| [Auggie CLI](https://docs.augmentcode.com/cli/overview)                              | ✅      |                                                                                                                                           |
| [Claude Code](https://www.anthropic.com/claude-code)                                 | ✅      |                                                                                                                                           |
| [CodeBuddy CLI](https://www.codebuddy.ai/cli)                                        | ✅      |                                                                                                                                           |
| [Codex CLI](https://github.com/openai/codex)                                         | ✅      |                                                                                                                                           |
| [Cursor](https://cursor.sh/)                                                         | ✅      |                                                                                                                                           |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli)                            | ✅      |                                                                                                                                           |
| [GitHub Copilot](https://code.visualstudio.com/)                                     | ✅      |                                                                                                                                           |
| [IBM Bob](https://www.ibm.com/products/bob)                                          | ✅      | 基于 IDE 的智能体，支持斜杠命令 |
| [Jules](https://jules.google.com/)                                                   | ✅      |                                                                                                                                           |
| [Kilo Code](https://github.com/Kilo-Org/kilocode)                                    | ✅      |                                                                                                                                           |
| [opencode](https://opencode.ai/)                                                     | ✅      |                                                                                                                                           |
| [Qwen Code](https://github.com/QwenLM/qwen-code)                                     | ✅      |                                                                                                                                           |
| [Roo Code](https://roocode.com/)                                                     | ✅      |                                                                                                                                           |
| [SHAI (OVHcloud)](https://github.com/ovh/shai)                                       | ✅      |                                                                                                                                           |
| [Windsurf](https://windsurf.com/)                                                    | ✅      |                                                                                                                                           |

## 🔧 Specify CLI 参考

注：以下所有 `specify` 命令都可以通过 `uvx --from git+https://github.com/github/spec-kit.git` 前缀运行。

### 命令

| 命令 | 描述 |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `init`  | 从最新模板初始化一个新的 Specify 项目 |
| `check` | 检查已安装的工具（`git`, `claude`, `gemini`, `code`/`code-insiders`, `cursor-agent`, `windsurf`, `qwen`, `opencode`, `codex`, `shai`, `qoder`） |

### `specify init` 参数与选项

| 参数/选项 | 类型 | 描述 |
| ---------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `<project-name>`       | 参数 | 新项目目录的名称（如果使用 `--here` 则可选，或使用 `.` 代表当前目录） |
| `--ai`                 | 选项 | 要使用的 AI 助手：`claude`, `gemini`, `copilot`, `cursor-agent`, `qwen`, `opencode`, `codex`, `windsurf`, `kilocode`, `auggie`, `roo`, `codebuddy`, `amp`, `shai`, `q`, `bob` 或 `qoder` |
| `--script`             | 选项 | 要使用的脚本变体：`sh` (bash/zsh) 或 `ps` (PowerShell) |
| `--ignore-agent-tools` | 标志 | 跳过对 AI 智能体工具（如 Claude Code）的检查 |
| `--no-git`             | 标志 | 跳过 git 仓库初始化 |
| `--here`               | 标志 | 在当前目录初始化项目，而不是创建新目录 |
| `--force`              | 标志 | 在当前目录初始化时强制合并/覆盖（跳过确认） |
| `--skip-tls`           | 标志 | 跳过 SSL/TLS 验证（不推荐） |
| `--debug`              | 标志 | 启用详细的调试输出以进行故障排除 |
| `--github-token`       | 选项 | 用于 API 请求的 GitHub 令牌（或设置 GH_TOKEN/GITHUB_TOKEN 环境变量） |

### 示例

```bash
# 基本项目初始化
uvx --from git+https://github.com/github/spec-kit.git specify init my-project

# 使用特定的 AI 助手进行初始化
uvx --from git+https://github.com/github/spec-kit.git specify init my-project --ai claude

# 初始化并支持 Cursor
uvx --from git+https://github.com/github/spec-kit.git specify init my-project --ai cursor-agent

# 初始化并支持 Qoder
uvx --from git+https://github.com/github/spec-kit.git specify init my-project --ai qoder

# 检查系统要求
uvx --from git+https://github.com/github/spec-kit.git specify check
```

### 可用斜杠命令

运行 `specify init` 后，你的 AI 编码智能体将可以访问这些斜杠命令进行结构化开发：

#### 核心命令

规格驱动开发流程的基本命令：

| 命令 | 描述 |
| ----------------------- | ------------------------------------------------------------------------ |
| `/speckit.constitution` | 创建或更新项目的治理原则和开发指南 |
| `/speckit.specify`      | 定义你想要构建的内容（需求和用户故事） |
| `/speckit.plan`         | 使用你选择的技术栈创建技术实现方案 |
| `/speckit.tasks`        | 生成可执行的任务列表 |
| `/speckit.implement`    | 执行所有任务，根据方案构建功能 |

#### 可选命令

用于增强质量和验证的附加命令：

| 命令 | 描述 |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `/speckit.clarify`   | 澄清描述不足的区域（建议在 `/speckit.plan` 之前运行；原名为 `/quizme`） |
| `/speckit.analyze`   | 跨成果的一致性与覆盖范围分析（在 `/speckit.tasks` 之后，`/speckit.implement` 之前运行） |
| `/speckit.checklist` | 生成自定义质量检查清单，验证需求的完整性、清晰度和一致性（类似于“英语语言的单元测试”） |

### 环境变量

| 变量 | 描述 |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `SPECIFY_FEATURE` | 对于非 Git 仓库，覆盖功能检测。设置为功能目录名称（例如 `001-photo-albums`），以便在不使用 Git 分支的情况下开发特定功能。<br/>\*\*必须在运行 `/speckit.plan` 或后续命令前，在智能体的上下文中设置。 |

## 📚 核心理念

规格驱动开发是一个结构化过程，强调：

- **意图驱动开发**：规格在“如何做”之前定义“做什么”。
- **丰富的规格创建**：使用护栏和组织原则。
- **多步精细化**：而不是通过提示词一次性生成代码。
- **高度依赖**：利用先进 AI 模型的规格理解能力。

## 🌟 开发阶段

| 阶段 | 重点 | 关键活动 |
| ---------------------------------------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **0 到 1 开发** (绿地项目) | 从零开始生成 | <ul><li>从高层需求开始</li><li>生成规格</li><li>规划实现步骤</li><li>构建生产就绪的应用</li></ul> |
| **创意探索** | 并行实现 | <ul><li>探索多种解决方案</li><li>支持多种技术栈和架构</li><li>实验 UX 模式</li></ul> |
| **迭代增强** (棕地项目) | 现代化改造 | <ul><li>迭代添加功能</li><li>现代化遗留系统</li><li>适配流程</li></ul> |

## 🎯 实验目标

我们的研究和实验重点在于：

### 技术独立性

- 使用各种技术栈创建应用程序。
- 验证规格驱动开发是一个不绑定于特定技术、编程语言或框架的过程。

### 企业级约束

- 演示关键任务应用程序的开发。
- 纳入组织约束（云提供商、技术栈、工程实践）。
- 支持企业设计系统和合规性要求。

### 以用户为中心

- 为不同的用户群体和偏好构建应用。
- 支持各种开发方法（从凭感觉编码到 AI 原生开发）。

### 创意与迭代过程

- 验证并行实现探索的概念。
- 提供稳健的迭代功能开发流程。
- 扩展流程以处理升级和现代化任务。

## 🔧 前提条件

- **Linux/macOS/Windows**
- 已安装[受支持](#-支持的 ai-智能体)的 AI 编码智能体。
- [uv](https://docs.astral.sh/uv/) 用于包管理
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

## 📖 了解更多

- **[规格驱动开发方法论详解](./spec-driven.md)** - 深入了解完整流程
- **[详细演示](#-详细流程)** - 逐步实现指南

---

## 📋 详细流程

<details>
<summary>点击展开详细的分步操作指南</summary>

你可以使用 Specify CLI 来引导你的项目，这会将所需的成果物带入你的环境。运行：

```bash
uvx --from git+https://github.com/github/spec-kit.git specify init <project_name>
```

或在当前目录初始化：

```bash
uvx --from git+https://github.com/github/spec-kit.git specify init .
# 或使用 --here 标志
uvx --from git+https://github.com/github/spec-kit.git specify init --here
# 当目录非空时跳过确认
uvx --from git+https://github.com/github/spec-kit.git specify init . --force
```

![Specify CLI 在终端中引导新项目](./media/specify_cli.gif)

系统会提示你选择正在使用的 AI 智能体。你也可以直接在终端中指定：

```bash
uvx --from git+https://github.com/github/spec-kit.git specify init <project_name> --ai claude
```

CLI 会检查你是否安装了 Claude Code, Gemini CLI, Cursor CLI, Qwen CLI, opencode, Codex CLI, Qoder CLI 或 Amazon Q Developer CLI。如果你没有安装，或者更愿意在不检查工具的情况下获取模板，请在命令中使用 `--ignore-agent-tools`。

### **步骤 1:** 确立项目原则

进入项目文件夹并运行你的 AI 智能体（例如 `claude`）。

![引导 Claude Code 环境](./media/bootstrap-claude-code.gif)

如果你看到 `/speckit.constitution`, `/speckit.specify`, `/speckit.plan`, `/speckit.tasks` 和 `/speckit.implement` 命令可用，说明配置正确。

第一步应该是使用 `/speckit.constitution` 命令建立项目的治理原则。这有助于确保后续所有开发阶段的决策一致性：

```text
/speckit.constitution 创建专注于代码质量、测试标准、用户体验一致性和性能要求的原则。包括这些原则如何指导技术决策和实现选择的治理规则。
```

此步骤会创建或更新 `.specify/memory/constitution.md` 文件。

### **步骤 2:** 创建项目规格 (Spec)

确立原则后，即可创建功能规格。使用 `/speckit.specify` 命令，然后提供具体的项目需求。

> [!IMPORTANT]
> 尽可能明确你想要构建**什么**以及**为什么**。**在此阶段不要关注技术栈**。

### **步骤 3:** 功能规格澄清（规划前必做）

在创建技术方案**之前**，你应该运行结构化澄清流程以减少下游返工。

1. 使用 `/speckit.clarify`（结构化）——按顺序、基于覆盖范围的提问，并将答案记录在澄清部分。
2. 如果仍感模糊，可选择进行即兴的自由形式细化。

### **步骤 4:** 生成方案 (Plan)

现在你可以指定技术栈和其他技术需求了。使用 `/speckit.plan`：

```text
我们将使用 .NET Aspire 生成，使用 Postgres 作为数据库。前端应使用 Blazor server，具有拖放式任务板和实时更新。
```

此步骤的输出将包含一系列实现细节文档。

### **步骤 5:** 让 AI 验证方案

方案到位后，应让 AI 运行一遍，确保没有遗漏。

### **步骤 6:** 使用 /speckit.tasks 生成任务分解

方案验证后，使用 `/speckit.tasks` 命令自动将方案分解为具体的、可操作的任务。

### **步骤 7:** 实现 (Implementation)

准备就绪后，使用 `/speckit.implement` 命令执行你的实现方案。

> [!IMPORTANT]
> AI 智能体会执行本地 CLI 命令（如 `dotnet`, `npm` 等）——请确保你的机器上安装了所需的工具。

一旦实现完成，测试应用程序并解决可能无法在 CLI 日志中看到的任何运行时错误（例如浏览器控制台错误）。

</details>

---

## 🔍 故障排除

### Linux 上的 Git 凭据管理器

如果你在 Linux 上遇到 Git 身份验证问题，可以安装 Git Credential Manager。

## 👥 维护者

- Den Delimarsky ([@localden](https://github.com/localden))
- John Lam ([@jflam](https://github.com/jflam))

## 💬 支持

如需支持，请打开 [GitHub issue](https://github.com/github/spec-kit/issues/new)。

## 🙏 致谢

本项目深受 [John Lam](https://github.com/jflam) 研究工作的启发并基于此构建。

## 📄 许可证

本项目根据 MIT 开源许可证条款进行许可。请参阅 [LICENSE](./LICENSE) 文件了解完整条款。
