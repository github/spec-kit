<div align="center">
    <img src="./media/logo_small.webp"/>
    <h1>🌱 Spec Kit</h1>
    <h3><em>更快构建高质量软件。</em></h3>
</div>

<p align="center">
    <strong>通过规范驱动开发的帮助，让组织能够专注于产品场景，而不是编写无差异化的代码。</strong>
</p>

[![Release](https://github.com/github/spec-kit/actions/workflows/release.yml/badge.svg)](https://github.com/github/spec-kit/actions/workflows/release.yml)

---

## 目录

- [🤔 什么是规范驱动开发？](#-什么是规范驱动开发)
- [⚡ 快速开始](#-快速开始)
- [📽️ 视频概览](#️-视频概览)
- [🤖 支持的 AI 智能体](#-支持的-ai-智能体)
- [🔧 Specify CLI 参考](#-specify-cli-参考)
- [📚 核心理念](#-核心理念)
- [🌟 开发阶段](#-开发阶段)
- [🎯 实验目标](#-实验目标)
- [🔧 前置条件](#-前置条件)
- [📖 了解更多](#-了解更多)
- [📋 详细流程](#-详细流程)
- [🔍 故障排除](#-故障排除)
- [👥 维护者](#-维护者)
- [💬 支持](#-支持)
- [🙏 致谢](#-致谢)
- [📄 许可证](#-许可证)

## 🤔 什么是规范驱动开发？

规范驱动开发**颠覆了**传统软件开发模式。几十年来，代码一直是核心——规范只是我们搭建的脚手架，一旦编码的"真正工作"开始，就会被丢弃。规范驱动开发改变了这一点：**规范变成了可执行的**，直接生成可工作的实现，而不仅仅是指导实现。

## ⚡ 快速开始

### 1. 安装 Specify

选择你喜欢的安装方法：

#### 选项 1：持久安装（推荐）

一次安装，随处使用：

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
```

然后直接使用工具：

```bash
specify init <PROJECT_NAME>
specify check
```

#### 选项 2：一次性使用

直接运行而无需安装：

```bash
uvx --from git+https://github.com/github/spec-kit.git specify init <PROJECT_NAME>
```

**持久安装的好处：**

- 工具保持安装并在 PATH 中可用
- 无需创建 shell 别名
- 更好的工具管理，支持 `uv tool list`、`uv tool upgrade`、`uv tool uninstall`
- 更清洁的 shell 配置

### 2. 建立项目原则

使用 **`/constitution`** 命令创建项目的治理原则和开发指南，这将指导所有后续开发。

```bash
/constitution 创建专注于代码质量、测试标准、用户体验一致性和性能要求的原则
```

### 3. 创建规范

使用 **`/specify`** 命令描述你想要构建的内容。专注于**什么**和**为什么**，而不是技术栈。

```bash
/specify 构建一个应用程序，可以帮我在单独的相册中整理我的照片。相册按日期分组，可以在主页面上通过拖放重新组织。相册永远不会在其他嵌套相册中。在每个相册内，照片以瓦片式界面预览。
```

### 4. 创建技术实现计划

使用 **`/plan`** 命令提供你的技术栈和架构选择。

```bash
/plan 应用程序使用 Vite，并尽量减少库的数量。尽可能使用原生 HTML、CSS 和 JavaScript。图像不会上传到任何地方，元数据存储在本地 SQLite 数据库中。
```

### 5. 分解为任务

使用 **`/tasks`** 从你的实现计划创建可操作的任务列表。

```bash
/tasks
```

### 6. 执行实现

使用 **`/implement`** 执行所有任务并根据计划构建你的功能。

```bash
/implement
```

有关详细的逐步说明，请参阅我们的[综合指南](./spec-driven.md)。

## 📽️ 视频概览

想看看 Spec Kit 的实际操作吗？观看我们的[视频概览](https://www.youtube.com/watch?v=a9eR1xsfvHg&pp=0gcJCckJAYcqIYzv)！

[![Spec Kit 视频标题](/media/spec-kit-video-header.jpg)](https://www.youtube.com/watch?v=a9eR1xsfvHg&pp=0gcJCckJAYcqIYzv)

## 🤖 支持的 AI 智能体

| 智能体                                                      | 支持 | 注释                                              |
|-----------------------------------------------------------|---------|---------------------------------------------------|
| [Claude Code](https://www.anthropic.com/claude-code)      | ✅ |                                                   |
| [GitHub Copilot](https://code.visualstudio.com/)          | ✅ |                                                   |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli) | ✅ |                                                   |
| [Cursor](https://cursor.sh/)                              | ✅ |                                                   |
| [Qwen Code](https://github.com/QwenLM/qwen-code)          | ✅ |                                                   |
| [opencode](https://opencode.ai/)                          | ✅ |                                                   |
| [Windsurf](https://windsurf.com/)                         | ✅ |                                                   |
| [Kilo Code](https://github.com/Kilo-Org/kilocode)         | ✅ |                                                   |
| [Auggie CLI](https://docs.augmentcode.com/cli/overview)   | ✅ |                                                   |
| [Roo Code](https://roocode.com/)                          | ✅ |                                                   |
| [Codex CLI](https://github.com/openai/codex)              | ⚠️ | Codex [不支持](https://github.com/openai/codex/issues/2890)斜杠命令的自定义参数。  |

## 🔧 Specify CLI 参考

`specify` 命令支持以下选项：

### 命令

| 命令     | 描述                                                    |
|-------------|----------------------------------------------------------------|
| `init`      | 从最新模板初始化新的 Specify 项目      |
| `check`     | 检查已安装的工具 (`git`、`claude`、`gemini`、`code`/`code-insiders`、`cursor-agent`、`windsurf`、`qwen`、`opencode`、`codex`) |

### `specify init` 参数和选项

| 参数/选项        | 类型     | 描述                                                                  |
|------------------------|----------|------------------------------------------------------------------------------|
| `<project-name>`       | 参数 | 新项目目录的名称（如果使用 `--here` 则可选，或者对当前目录使用 `.`） |
| `--ai`                 | 选项   | 要使用的 AI 助手：`claude`、`gemini`、`copilot`、`cursor`、`qwen`、`opencode`、`codex`、`windsurf`、`kilocode`、`auggie` 或 `roo` |
| `--script`             | 选项   | 要使用的脚本变体：`sh`（bash/zsh）或 `ps`（PowerShell）                 |
| `--ignore-agent-tools` | 标志     | 跳过 AI 智能体工具检查，如 Claude Code                             |
| `--no-git`             | 标志     | 跳过 git 仓库初始化                                          |
| `--here`               | 标志     | 在当前目录中初始化项目而不是创建新目录   |
| `--force`              | 标志     | 在当前目录中初始化时强制合并/覆盖（跳过确认） |
| `--skip-tls`           | 标志     | 跳过 SSL/TLS 验证（不推荐）                                 |
| `--debug`              | 标志     | 启用详细调试输出以进行故障排除                            |
| `--github-token`       | 选项   | 用于 API 请求的 GitHub 令牌（或设置 GH_TOKEN/GITHUB_TOKEN 环境变量）  |

### 示例

```bash
# 基本项目初始化
specify init my-project

# 使用特定 AI 助手初始化
specify init my-project --ai claude

# 使用 Cursor 支持初始化
specify init my-project --ai cursor

# 使用 Windsurf 支持初始化
specify init my-project --ai windsurf

# 使用 PowerShell 脚本初始化（Windows/跨平台）
specify init my-project --ai copilot --script ps

# 在当前目录中初始化
specify init . --ai copilot
# 或使用 --here 标志
specify init --here --ai copilot

# 在当前（非空）目录中强制合并而不确认
specify init . --force --ai copilot
# 或
specify init --here --force --ai copilot

# 跳过 git 初始化
specify init my-project --ai gemini --no-git

# 启用调试输出进行故障排除
specify init my-project --ai claude --debug

# 使用 GitHub 令牌进行 API 请求（对企业环境有帮助）
specify init my-project --ai claude --github-token ghp_your_token_here

# 检查系统要求
specify check
```

### 可用的斜杠命令

运行 `specify init` 后，你的 AI 编码智能体将可以访问这些结构化开发的斜杠命令：

| 命令         | 描述                                                           |
|-----------------|-----------------------------------------------------------------------|
| `/constitution` | 创建或更新项目治理原则和开发指南 |
| `/specify`      | 定义你想要构建的内容（需求和用户故事）        |
| `/clarify`      | 澄清规范不足的区域（必须在 `/plan` 之前运行，除非明确跳过；之前称为 `/quizme`） |
| `/plan`         | 使用你选择的技术栈创建技术实现计划     |
| `/tasks`        | 生成实现的可操作任务列表                     |
| `/analyze`      | 跨制品一致性和覆盖率分析（在 /tasks 之后、/implement 之前运行） |
| `/implement`    | 执行所有任务以根据计划构建功能         |

### 环境变量

| 变量         | 描述                                                                                    |
|------------------|------------------------------------------------------------------------------------------------|
| `SPECIFY_FEATURE` | 为非 Git 仓库覆盖功能检测。设置为功能目录名称（例如 `001-photo-albums`）以在不使用 Git 分支时处理特定功能。<br/>**必须在使用 `/plan` 或后续命令之前在你正在使用的智能体上下文中设置。 |

## 📚 核心理念

规范驱动开发是一个强调以下方面的结构化过程：

- **意图驱动开发**，规范在"如何"之前定义"什么"
- **丰富的规范创建**，使用护栏和组织原则
- **多步骤细化**而不是从提示一次性代码生成
- **严重依赖**高级 AI 模型的规范解释能力

## 🌟 开发阶段

| 阶段 | 重点 | 关键活动 |
|-------|-------|----------------|
| **0-to-1 开发**（"绿地"） | 从头开始生成 | <ul><li>从高级需求开始</li><li>生成规范</li><li>规划实现步骤</li><li>构建生产就绪的应用程序</li></ul> |
| **创意探索** | 并行实现 | <ul><li>探索多样化解决方案</li><li>支持多种技术栈和架构</li><li>实验 UX 模式</li></ul> |
| **迭代增强**（"棕地"） | 棕地现代化 | <ul><li>迭代添加功能</li><li>现代化遗留系统</li><li>调整过程</li></ul> |

## 🎯 实验目标

我们的研究和实验重点关注：

### 技术独立性

- 使用多样化技术栈创建应用程序
- 验证规范驱动开发是一个不依赖于特定技术、编程语言或框架的过程的假设

### 企业约束

- 演示关键任务应用程序开发
- 结合组织约束（云提供商、技术栈、工程实践）
- 支持企业设计系统和合规要求

### 以用户为中心的开发

- 为不同的用户群体和偏好构建应用程序
- 支持各种开发方法（从氛围编码到 AI 原生开发）

### 创意和迭代过程

- 验证并行实现探索的概念
- 提供强大的迭代功能开发工作流程
- 扩展过程以处理升级和现代化任务

## 🔧 前置条件

- **Linux/macOS**（或 Windows 上的 WSL2）
- AI 编码智能体：[Claude Code](https://www.anthropic.com/claude-code)、[GitHub Copilot](https://code.visualstudio.com/)、[Gemini CLI](https://github.com/google-gemini/gemini-cli)、[Cursor](https://cursor.sh/)、[Qwen CLI](https://github.com/QwenLM/qwen-code)、[opencode](https://opencode.ai/)、[Codex CLI](https://github.com/openai/codex) 或 [Windsurf](https://windsurf.com/)
- [uv](https://docs.astral.sh/uv/) 用于包管理
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

如果你在某个智能体上遇到问题，请打开一个 issue，这样我们可以完善集成。

## 📖 了解更多

- **[完整的规范驱动开发方法论](./spec-driven.md)** - 深入了解完整过程
- **[详细演练](#-详细流程)** - 逐步实现指南

---

## 📋 详细流程

<details>
<summary>点击展开详细的逐步演练</summary>

你可以使用 Specify CLI 来引导你的项目，这将在你的环境中引入所需的制品。运行：

```bash
specify init <project_name>
```

或在当前目录中初始化：

```bash
specify init .
# 或使用 --here 标志
specify init --here
# 当目录已有文件时跳过确认
specify init . --force
# 或
specify init --here --force
```

![Specify CLI 在终端中引导新项目](./media/specify_cli.gif)

系统会提示你选择正在使用的 AI 智能体。你也可以在终端中直接主动指定：

```bash
specify init <project_name> --ai claude
specify init <project_name> --ai gemini
specify init <project_name> --ai copilot
specify init <project_name> --ai cursor
specify init <project_name> --ai qwen
specify init <project_name> --ai opencode
specify init <project_name> --ai codex
specify init <project_name> --ai windsurf
# 或在当前目录中：
specify init . --ai claude
specify init . --ai codex
# 或使用 --here 标志
specify init --here --ai claude
specify init --here --ai codex
# 强制合并到非空的当前目录
specify init . --force --ai claude
# 或
specify init --here --force --ai claude
```

CLI 会检查你是否安装了 Claude Code、Gemini CLI、Cursor CLI、Qwen CLI、opencode 或 Codex CLI。如果没有，或者你更喜欢在不检查正确工具的情况下获取模板，请在命令中使用 `--ignore-agent-tools`：

```bash
specify init <project_name> --ai claude --ignore-agent-tools
```

### **步骤 1：** 建立项目原则

进入项目文件夹并运行你的 AI 智能体。在我们的示例中，我们使用 `claude`。

![引导 Claude Code 环境](./media/bootstrap-claude-code.gif)

如果你看到 `/constitution`、`/specify`、`/plan`、`/tasks` 和 `/implement` 命令可用，你就知道配置正确了。

第一步应该是使用 `/constitution` 命令建立项目的治理原则。这有助于确保在所有后续开发阶段的一致决策：

```text
/constitution 创建专注于代码质量、测试标准、用户体验一致性和性能要求的原则。包括这些原则如何指导技术决策和实现选择的治理。
```

此步骤创建或更新 `.specify/memory/constitution.md` 文件，其中包含 AI 智能体在规范、规划和实现阶段将参考的项目基础指南。

### **步骤 2：** 创建项目规范

建立项目原则后，你现在可以创建功能规范。使用 `/specify` 命令，然后提供你想要开发的项目的具体要求。

>[!IMPORTANT]
>尽可能明确地说明你试图构建的**什么**和**为什么**。**此时不要关注技术栈**。

示例提示：

```text
开发Taskify，一个团队生产力平台。
它应该允许用户创建项目、添加团队成员、分配任务、评论以及看板风格的板块之间移动任务。
在这个功能的初始阶段，我们称之为"创建Taskify"，让我们设置多个用户，但这些用户将预先声明和预定义。
我需要五个用户分为两个不同类别：一个产品经理和四个工程师。
让我们创建三个不同的示例项目。让我们为每个任务的状态设置标准的看板列，如"待办"、"进行中"、"审核中"和"已完成"。
这个应用程序将不需要登录，因为这只是第一个测试版本，用来确保我们的基本功能已经设置好。
在UI的任务卡片中，你应该能够在看板工作区的不同列之间更改任务的当前状态。你应该能够为特定卡片留下无限数量的评论。
你应该能够从该任务卡片中分配一个有效用户。当你首次启动Taskify时，它会给你提供五个用户的列表供选择。不需要密码。
当你点击一个用户时，你会进入主视图，显示项目列表。当你点击一个项目时，你打开该项目的看板。你会看到这些列。你将能够拖拽卡片在不同列之间来回移动。
你会看到分配给你（当前登录用户）的卡片与所有其他卡片显示不同的颜色，这样你可以快速识别出自己的任务。
你可以编辑自己做的任何评论，但不能编辑其他人做的评论。
```

输入此提示后，你应该看到 Claude Code 启动规划和规范起草过程。Claude Code 还会触发一些内置脚本来设置仓库。

完成此步骤后，你应该创建一个新分支（例如 `001-create-taskify`），以及 `specs/001-create-taskify` 目录中的新规范。

生成的规范应包含一组用户故事和功能需求，如模板中定义的。

在此阶段，你的项目文件夹内容应该类似于以下内容：

```text
└── .specify
    ├── memory
    │	 └── constitution.md
    ├── scripts
    │	 ├── check-prerequisites.sh
    │	 ├── common.sh
    │	 ├── create-new-feature.sh
    │	 ├── setup-plan.sh
    │	 └── update-claude-md.sh
    ├── specs
    │	 └── 001-create-taskify
    │	     └── spec.md
    └── templates
        ├── plan-template.md
        ├── spec-template.md
        └── tasks-template.md
```

### **步骤 3：** 功能规范澄清（规划前必需）

创建基线规范后，你可以继续澄清在第一次尝试中未正确捕获的任何需求。

你应该在创建技术计划**之前**运行结构化澄清工作流程，以减少下游的返工。

首选顺序：
1. 使用 `/clarify`（结构化）- 顺序的、基于覆盖率的提问，将答案记录在澄清部分。
2. 如果仍然感觉模糊，可选择进行临时自由形式的细化。

如果你有意想要跳过澄清（例如，尖峰或探索性原型），请明确说明，这样智能体不会因为缺少澄清而阻塞。

示例自由形式细化提示（如果在 `/clarify` 后仍然需要）：

```text
对于你创建的每个示例项目或项目，应该在 5 到 15 个任务之间有可变数量的任务，每个项目随机分布到不同的完成状态。
确保每个完成阶段至少有一个任务。
```

你还应该要求 Claude Code 验证**审查和验收检查表**，勾选验证/通过要求的项目，留下未通过的项目未勾选。可以使用以下提示：

```text
阅读审查和验收检查表，如果功能规范符合标准，请勾选检查表中的每个项目。如果不符合，请留空。
```

重要的是使用与 Claude Code 的交互作为澄清和询问规范问题的机会 - **不要将它的第一次尝试视为最终的**。

### **步骤 4：** 生成计划

你现在可以具体说明技术栈和其他技术要求。你可以使用内置在项目模板中的 `/plan` 命令，使用这样的提示：

```text
我们将使用 .NET Aspire 生成这个，使用 Postgres 作为数据库。
前端应该使用带有拖放任务板、实时更新的 Blazor 服务器。
应该创建一个 REST API，包含项目 API、任务 API 和通知 API。
```

此步骤的输出将包括许多实现细节文档，你的目录树将类似于这样：

```text
.
├── CLAUDE.md
├── memory
│	 └── constitution.md
├── scripts
│	 ├── check-prerequisites.sh
│	 ├── common.sh
│	 ├── create-new-feature.sh
│	 ├── setup-plan.sh
│	 └── update-claude-md.sh
├── specs
│	 └── 001-create-taskify
│	     ├── contracts
│	     │	 ├── api-spec.json
│	     │	 └── signalr-spec.md
│	     ├── data-model.md
│	     ├── plan.md
│	     ├── quickstart.md
│	     ├── research.md
│	     └── spec.md
└── templates
    ├── CLAUDE-template.md
    ├── plan-template.md
    ├── spec-template.md
    └── tasks-template.md
```

检查 `research.md` 文档，确保根据你的指示使用正确的技术栈。如果任何组件突出，你可以要求 Claude Code 完善它，甚至让它检查你想要使用的平台/框架的本地安装版本（例如 .NET）。

此外，如果是快速变化的内容（例如 .NET Aspire、JS 框架），你可能想要求 Claude Code 研究所选技术栈的详细信息，使用这样的提示：

```text
我想让你查看实现计划和实现细节，寻找可能从额外研究中受益的区域，因为 .NET Aspire 是一个快速变化的库。
对于你识别的需要进一步研究的区域，我想让你用我们将在这个 Taskify 应用程序中使用的特定版本的附加详细信息更新研究文档，并产生并行研究任务以使用网络研究澄清任何细节。
```

在此过程中，你可能会发现 Claude Code 卡在研究错误的事情上 - 你可以用这样的提示帮助引导它朝正确方向：

```text
我认为我们需要将此分解为一系列步骤。
首先，识别一个任务列表，在实现过程中你需要做但不确定或将从进一步研究中受益的任务。
写下这些任务的列表。
然后对于这些任务中的每一个，我想让你启动一个单独的研究任务，这样最终结果是我们正在研究所有这些非常具体的任务并行。
我看到你在做的是看起来你在研究一般的 .NET Aspire，我不认为这对我们在这种情况下会有太大帮助。
这是过于无针对性的研究。
研究需要帮助你解决一个具体的针对性问题。
```

>[!NOTE]
>Claude Code 可能过于热心并添加你没有要求的组件。要求它澄清理由和变更的来源。

### **步骤 5：** 让 Claude Code 验证计划

有了计划后，你应该让 Claude Code 检查以确保没有遗漏的部分。你可以使用这样的提示：

```text
现在我想让你去审计实现计划和实现细节文件。
仔细阅读，确定是否有一个明显的任务序列需要做。
因为我不知道这里是否有足够的内容。
例如，当我查看核心实现时，引用实现中的适当位置细节，它可以在核心实现或细化中的每个步骤中找到信息，这将是有用的。
```

这有助于完善实现计划并帮助你避免 Claude Code 在规划周期中错过的潜在盲点。一旦初始细化通过完成，要求 Claude Code 在进入实现之前再次检查清单。

如果你安装了 [GitHub CLI](https://docs.github.com/en/github-cli/github-cli)，你也可以要求 Claude Code 从当前分支到 `main` 创建一个详细描述的拉取请求，以确保工作得到适当跟踪。

>[!NOTE]
>在让智能体实现之前，还值得提示 Claude Code 交叉检查细节，看是否有任何过度工程化的部分（记住 - 它可能过于热心）。如果存在过度工程化的组件或决策，你可以要求 Claude Code 解决它们。确保 Claude Code 遵循[constitution](base/memory/constitution.md)作为在建立计划时必须遵守的基础部分。

### 步骤 6：实现

准备好后，使用 `/implement` 命令执行你的实现计划：

```text
/implement
```

`/implement` 命令将：
- 验证所有前提条件是否到位（constitution、spec、plan 和 tasks）
- 从 `tasks.md` 解析任务分解
- 按正确顺序执行任务，遵守依赖关系和并行执行标记
- 遵循任务计划中定义的 TDD 方法
- 提供进度更新并适当处理错误

>[!IMPORTANT]
>AI 智能体将执行本地 CLI 命令（如 `dotnet`、`npm` 等）- 确保你的机器上安装了所需的工具。

实现完成后，测试应用程序并解决任何在 CLI 日志中可能不可见的运行时错误（例如浏览器控制台错误）。你可以将此类错误复制粘贴回 AI 智能体以进行解决。

</details>

---

## 🔍 故障排除

### Linux 上的 Git 凭据管理器

如果你在 Linux 上遇到 Git 身份验证问题，可以安装 Git 凭据管理器：

```bash
#!/usr/bin/env bash
set -e
echo "正在下载 Git 凭据管理器 v2.6.1..."
wget https://github.com/git-ecosystem/git-credential-manager/releases/download/v2.6.1/gcm-linux_amd64.2.6.1.deb
echo "正在安装 Git 凭据管理器..."
sudo dpkg -i gcm-linux_amd64.2.6.1.deb
echo "配置 Git 使用 GCM..."
git config --global credential.helper manager
echo "正在清理..."
rm gcm-linux_amd64.2.6.1.deb
```

## 👥 维护者

- Den Delimarsky ([@localden](https://github.com/localden))
- John Lam ([@jflam](https://github.com/jflam))

## 💬 支持

如需支持，请打开一个 [GitHub issue](https://github.com/github/spec-kit/issues/new)。我们欢迎错误报告、功能请求和关于使用规范驱动开发的问题。

## 🙏 致谢

此项目深受 [John Lam](https://github.com/jflam) 的工作和研究的影响和基础。

## 📄 许可证

此项目根据 MIT 开源许可证的条款获得许可。请参阅 [LICENSE](./LICENSE) 文件了解完整条款。