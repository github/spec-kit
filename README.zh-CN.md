<div align="center">
    <img src="./media/logo_large.webp" alt="Spec Kit Logo" width="200" height="200"/>
    <h1>🌱 Spec Kit</h1>
    <h3><em>在动手编码之前，先定义要构建什么 —— 适配任意 AI 编码助手。</em></h3>
</div>

<p align="center">
    <strong>一个开源工具套件，帮助你借助任意 AI 编码助手构建高质量软件 —— 内置开箱即用的规范驱动流程（也可自带流程），可无限扩展、由社区驱动，并为整个组织的协作而设计。</strong>
</p>

<p align="center">
    <a href="https://github.com/github/spec-kit/releases/latest"><img src="https://img.shields.io/github/v/release/github/spec-kit" alt="Latest Release"/></a>
    <a href="https://github.com/github/spec-kit/stargazers"><img src="https://img.shields.io/github/stars/github/spec-kit?style=social" alt="GitHub stars"/></a>
    <a href="https://github.com/github/spec-kit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/github/spec-kit" alt="License"/></a>
    <a href="https://github.github.io/spec-kit/"><img src="https://img.shields.io/badge/docs-GitHub_Pages-blue" alt="Documentation"/></a>
</p>

<p align="center">
    <a href="./README.md">English</a> ·
    <strong>简体中文</strong>
</p>

---

## 目录

- [🤔 什么是规范驱动开发？](#-什么是规范驱动开发)
- [⚡ 快速开始](#-快速开始)
- [📽️ 视频概览](#️-视频概览)
- [🌍 社区](#-社区)
- [🤖 支持的 AI 编码助手集成](#-支持的-ai-编码助手集成)
- [🔧 Specify CLI 参考](#-specify-cli-参考)
- [🧩 打造你自己的 Spec Kit：扩展与预设](#-打造你自己的-spec-kit扩展与预设)
- [📦 捆绑包：面向角色的一键配置](#-捆绑包面向角色的一键配置)
- [📚 核心理念](#-核心理念)
- [🌟 开发阶段](#-开发阶段)
- [🎯 实验目标](#-实验目标)
- [🔧 环境要求](#-环境要求)
- [📖 深入了解](#-深入了解)
- [💬 支持](#-支持)
- [🙏 致谢](#-致谢)
- [📄 许可证](#-许可证)

## 🤔 什么是规范驱动开发？

规范驱动开发（Spec-Driven Development）**颠覆了**传统软件开发的思路。几十年来，代码一直是核心 —— 规范只是编码这项"正事"开始前搭起、随后就被丢弃的脚手架。规范驱动开发改变了这一点：**规范本身变得可执行**，它不再只是引导实现，而是直接生成可运行的实现。

## ⚡ 快速开始

### 1. 安装 Specify CLI

需要 **[uv](https://docs.astral.sh/uv/)**（[安装 uv](./docs/install/uv.md)）。将 `vX.Y.Z` 替换为 [Releases](https://github.com/github/spec-kit/releases) 中最新的发布标签 —— 记得保留开头的 `v`（例如 `v0.12.11`，而不是 `0.12.11`）：

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z
```

更倾向从 PyPI 安装？`specify-cli` 包同样发布在那里：

```bash
uv tool install specify-cli
```

其他安装方式、安装校验、升级以及故障排查，请参阅[安装指南](./docs/installation.md)。

### 2. 初始化项目

```bash
specify init my-project --integration copilot
cd my-project
```

要检查更新或升级已安装的 CLI，可使用自管理命令。更详细的场景和自定义选项请参阅[升级指南](./docs/upgrade.md)。

```bash
# 检查是否有更新版本可用（只读操作 —— 不会修改任何内容）
specify self check

# 预览升级将执行的操作，但不实际升级
specify self upgrade --dry-run

# 就地升级到最新稳定版（自动识别 uv tool 与 pipx 安装方式）
specify self upgrade

# 或锁定到指定的发布标签（将 vX.Y.Z[suffix] 替换为你想要的标签）
specify self upgrade --tag vX.Y.Z[suffix]
```

直接运行 `specify self upgrade` 会立即执行，与 `pip install -U`、`npm update` 等命令一样无需额外确认。对于 `uv tool` 安装的情况，它在底层会执行 `uv tool install specify-cli --force --from <git ref>`，因此锁定的发布标签同样有效，包括 dev、alpha/beta/rc 或带构建元数据的后缀。`uvx`（临时运行）和源码检出会被自动识别，此时会给出针对具体路径的操作建议，而不会执行安装程序。可通过设置 `SPECIFY_UPGRADE_TIMEOUT_SECS` 来限制安装子进程的最长运行时间（默认无超时限制 —— 必要时用 `Ctrl+C` 中断）。

### 3. 确立项目准则

在项目目录下启动你的编码助手。大多数助手将 spec-kit 暴露为 `/speckit.*` 斜杠命令；处于技能（skills）模式的 Codex CLI 则使用 `$speckit-*`；GitHub Copilot CLI 使用 `/agents` 来选择助手，或直接在提示词中指定它。

使用 **`/speckit.constitution`** 命令来创建项目的治理准则和开发指南，它们将指导后续所有开发工作。

```bash
/speckit.constitution Create principles focused on code quality, testing standards, user experience consistency, and performance requirements
```

### 4. 编写规范

使用 **`/speckit.specify`** 命令描述你想构建什么。聚焦于**做什么**和**为什么做**，而不是技术栈。

```bash
/speckit.specify Build an application that can help me organize my photos in separate photo albums. Albums are grouped by date and can be re-organized by dragging and dropping on the main page. Albums are never in other nested albums. Within each album, photos are previewed in a tile-like interface.
```

### 5. 制定技术实现方案

使用 **`/speckit.plan`** 命令提供你的技术栈和架构选择。

```bash
/speckit.plan The application uses Vite with minimal number of libraries. Use vanilla HTML, CSS, and JavaScript as much as possible. Images are not uploaded anywhere and metadata is stored in a local SQLite database.
```

### 6. 拆解为任务

使用 **`/speckit.tasks`** 从实现方案生成一份可执行的任务清单。

```bash
/speckit.tasks
```

### 7. 执行实现

使用 **`/speckit.implement`** 执行所有任务，按方案构建你的功能。

```bash
/speckit.implement
```

详细的分步说明，请参阅我们的[完整指南](./spec-driven.md)。

## 📽️ 视频概览

想看看 Spec Kit 的实际效果？观看我们的[视频概览](https://www.youtube.com/watch?v=a9eR1xsfvHg&pp=0gcJCckJAYcqIYzv)！

[![Spec Kit video header](/media/spec-kit-video-header.jpg)](https://www.youtube.com/watch?v=a9eR1xsfvHg&pp=0gcJCckJAYcqIYzv)

## 🌍 社区

在 [Spec Kit 文档站点](https://github.github.io/spec-kit/)上探索由社区贡献的资源：

- [扩展（Extensions）](https://github.github.io/spec-kit/community/extensions.html) —— 命令、钩子与各类能力
- [预设（Presets）](https://github.github.io/spec-kit/community/presets.html) —— 模板与术语覆盖
- [捆绑包（Bundles）](https://github.github.io/spec-kit/community/bundles.html) —— 由现有组件组合而成的角色与团队技术栈
- [实战演练（Walkthroughs）](https://github.github.io/spec-kit/community/walkthroughs.html) —— 端到端的 SDD 场景
- [伙伴项目（Friends）](https://github.github.io/spec-kit/community/friends.html) —— 扩展 Spec Kit 或基于它构建的项目

> [!NOTE]
> 社区贡献由各自的作者独立创建和维护。请在安装前审阅源代码，并自行斟酌使用。

想要参与贡献？请参阅[扩展发布指南](extensions/EXTENSION-PUBLISHING-GUIDE.md)、[预设发布指南](presets/PUBLISHING.md)或[社区捆绑包指南](docs/community/bundles.md)。

## 🤖 支持的 AI 编码助手集成

Spec Kit 可与 30 多个 AI 编码助手协作 —— 既包括 CLI 工具，也包括基于 IDE 的助手。完整列表以及相关说明和使用细节，请参阅[支持的 AI 编码助手集成](https://github.github.io/spec-kit/reference/integrations.html)指南。

运行 `specify integration list` 可查看当前安装版本中所有可用的集成。

## 可用的斜杠命令

运行 `specify init` 后，你的 AI 编码助手就能使用这些斜杠命令来进行结构化开发。对于支持技能模式的集成，传入 `--integration <agent> --integration-options="--skills"` 会安装助手技能，而不是斜杠命令的提示词文件。

### 核心命令

规范驱动开发工作流中必不可少的命令：

| 命令                     | 助手技能               | 说明                                                       |
| ------------------------ | ---------------------- | ---------------------------------------------------------- |
| `/speckit.constitution`  | `speckit-constitution` | 创建或更新项目的治理准则和开发指南                         |
| `/speckit.specify`       | `speckit-specify`      | 定义你想构建什么（需求与用户故事）                         |
| `/speckit.plan`          | `speckit-plan`         | 结合所选技术栈制定技术实现方案                             |
| `/speckit.tasks`         | `speckit-tasks`        | 生成可执行的实现任务清单                                   |
| `/speckit.taskstoissues` | `speckit-taskstoissues`| 将生成的任务清单转换为 GitHub issue，便于跟踪与执行        |
| `/speckit.implement`     | `speckit-implement`    | 执行所有任务，按方案构建功能                               |
| `/speckit.converge`      | `speckit-converge`     | 对照规范/方案/任务评估代码库，并将剩余工作追加为新任务     |

### 可选命令

用于提升质量与做校验的额外命令：

| 命令                 | 助手技能               | 说明                                                                                              |
| -------------------- | ---------------------- | ------------------------------------------------------------------------------------------------- |
| `/speckit.clarify`   | `speckit-clarify`      | 澄清描述不充分的部分（建议在 `/speckit.plan` 之前使用；旧称 `/quizme`）                            |
| `/speckit.analyze`   | `speckit-analyze`      | 跨制品的一致性与覆盖度分析（在 `/speckit.tasks` 之后、`/speckit.implement` 之前运行）              |
| `/speckit.checklist` | `speckit-checklist`    | 生成自定义质量清单，校验需求的完整性、清晰度与一致性（好比"为自然语言写单元测试"）                 |

## 🔧 Specify CLI 参考

完整的命令详情、选项与示例，请参阅 [CLI 参考文档](https://github.github.io/spec-kit/reference/overview.html)。

## 🧩 打造你自己的 Spec Kit：扩展与预设

Spec Kit 可通过两套互补的机制进行深度定制 —— **扩展（extensions）** 和 **预设（presets）** —— 以及面向单个项目的本地覆盖，用于临时性调整：

| 优先级 | 组件类型                           | 位置                             |
| -----: | ---------------------------------- | -------------------------------- |
|   ⬆ 1 | 项目本地覆盖                       | `.specify/templates/overrides/`  |
|      2 | 预设 —— 定制核心与扩展             | `.specify/presets/templates/`    |
|      3 | 扩展 —— 新增能力                   | `.specify/extensions/templates/` |
|   ⬇ 4 | Spec Kit 核心 —— 内置 SDD 命令与模板 | `.specify/templates/`            |

- **模板**在**运行时**解析 —— Spec Kit 从高到低遍历优先级栈，使用第一个匹配项。
- 项目本地覆盖（`.specify/templates/overrides/`）允许对单个项目做一次性调整，无需创建完整的预设。
- **扩展/预设命令**在**安装时**生效 —— 当你运行 `specify extension add` 或 `specify preset add` 时，命令文件会被写入助手目录（如 `.claude/commands/`）。
- 若多个预设或扩展提供了同一命令，优先级最高的版本生效。移除时，次优先级的版本会自动恢复。
- 若不存在任何覆盖或自定义，Spec Kit 使用核心默认配置。

### 扩展 —— 新增能力

当你需要 Spec Kit 核心之外的功能时，使用**扩展**。扩展可引入新命令和模板 —— 例如添加核心 SDD 命令未覆盖的领域特定工作流、集成外部工具，或新增全新的开发阶段。它们扩展了 *Spec Kit 能做什么*。

```bash
# 搜索可用扩展
specify extension search

# 安装扩展
specify extension add <extension-name>
```

举例来说，扩展可以添加 Jira 集成、实现后代码审查、V 模型测试追溯性，或项目健康诊断等功能。

完整命令指南请参阅[扩展参考文档](https://github.github.io/spec-kit/reference/extensions.html)。浏览[社区扩展](https://github.github.io/spec-kit/community/extensions.html)了解现有资源。

### 预设 —— 定制现有工作流

当你想改变 Spec Kit 的*工作方式*而不是新增能力时，使用**预设**。预设会覆盖核心及已安装扩展中附带的模板和命令 —— 例如强制使用面向合规的规范格式、采用领域特定术语，或对方案和任务应用组织规范。预设定制的是 Spec Kit 及其扩展生成的制品与指令。

```bash
# 搜索可用预设
specify preset search

# 安装预设
specify preset add <preset-name>
```

举例来说，预设可以重构规范模板以要求监管追溯性，将工作流适配为你所用的方法论（如敏捷、看板、瀑布、用户任务驱动或领域驱动设计），在方案中添加强制安全审查关卡，强制要求测试优先的任务排序，或将整个工作流本地化为其他语言。[海盗语演示](https://github.com/mnriem/spec-kit-pirate-speak-preset-demo)充分展示了定制的深度。多个预设可按优先级叠加使用。

完整命令指南以及解析顺序和优先级叠加说明，请参阅[预设参考文档](https://github.github.io/spec-kit/reference/presets.html)。

## 📦 捆绑包：面向角色的一键配置

扩展和预设是独立的构建模块。而**捆绑包（bundle）**将一组精选的扩展、预设、步骤和工作流打包成一个带版本、面向角色的配置，从而可以用一条命令为整个团队角色（产品经理、业务分析师、安全研究员、开发者……）完成配置。

捆绑包由一份手写的 `bundle.yml` 清单描述。它将每个组件锁定到具体版本，并可选择性地面向特定集成；未指定 `integration` 的捆绑包是**中立的**，会沿用项目当前已使用的集成。

```bash
# 在当前激活的目录栈中发现捆绑包
specify bundle search [<query>]

# 查看捆绑包将添加的确切组件集合（与实际安装的内容一致）
specify bundle info <bundle-id>

# 一步安装捆绑包的完整组件集合
specify bundle install <bundle-id>

# 查看已安装内容，然后以非破坏性方式更新或移除
specify bundle list
specify bundle update <bundle-id>     # 或 --all
specify bundle remove <bundle-id>     # 仅移除此捆绑包的组件
```

捆绑包从一个**按优先级排序的目录栈**（项目 > 用户 > 内置）中解析。每个来源都带有安装策略：`install-allowed` 来源可用于安装，而 `discovery-only` 来源在 `search`/`info` 中可见但拒绝安装。可通过 `specify bundle catalog list|add|remove` 管理目录栈。

作者在本地校验并打包捆绑包。分发方式是托管构建产物并添加一个目录来源；社区捆绑包投稿请使用 [Bundle Submission](https://github.com/github/spec-kit/issues/new?template=bundle_submission.yml) issue 模板，以便对所需的组件目录和安装证据进行审阅：

```bash
specify bundle validate --path ./my-bundle      # 结构与引用检查
specify bundle build --path ./my-bundle         # 生成带版本的 .zip 产物
```

[`examples/bundles/`](examples/bundles/) 目录下有四份可直接阅读的示例清单（产品经理、业务分析师、安全研究员、开发者）。

关键保证：`info` 展示的内容与 `install` 添加的内容完全一致（透明性）；安装是幂等的，且限定在项目根目录内；`remove` 绝不会触碰其他已安装捆绑包仍需要的组件；所有消费/创作命令都能针对本地或锁定的来源**离线**工作。

### 何时用哪个

| 目标 | 使用 |
| --- | --- |
| 添加全新的命令或工作流 | 扩展 |
| 定制规范、方案或任务的格式 | 预设 |
| 集成外部工具或服务 | 扩展 |
| 强制执行组织或监管规范 | 预设 |
| 交付可复用的领域特定模板 | 均可 —— 预设用于模板覆盖，扩展用于随新命令一起打包的模板 |
| 用一条命令完成完整的角色配置 | 捆绑包 |

## 📚 核心理念

规范驱动开发是一套结构化流程，它强调：

- **意图驱动开发** —— 让规范先定义"*做什么*"，再谈"*怎么做*"
- **丰富的规范撰写** —— 借助护栏与组织准则来编写规范
- **多步精炼** —— 而非从提示词一次性生成代码
- **充分依赖**先进 AI 模型对规范的解读能力

## 🌟 开发阶段

| 阶段                                      | 侧重点             | 关键活动                                                                                                                                             |
| ----------------------------------------- | ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **从 0 到 1 开发**（"绿地/Greenfield"）   | 从零生成           | <ul><li>从高层需求出发</li><li>生成规范</li><li>规划实现步骤</li><li>构建生产就绪的应用</li></ul>                                                    |
| **创意探索**                              | 并行实现           | <ul><li>探索多样化的解决方案</li><li>支持多种技术栈与架构</li><li>试验不同的用户体验模式</li></ul>                                                   |
| **迭代增强**（"棕地/Brownfield"）         | 存量系统现代化     | <ul><li>迭代式添加功能</li><li>现代化改造遗留系统</li><li>调整流程</li></ul>                                                                         |

对于已有项目，请将 Spec Kit 工具本身的更新与功能制品的演进分开处理：升级时刷新受管理的项目文件，而在预期行为发生变化时更新 `specs/` 制品。[规范演进指南](./docs/guides/evolving-specs.md)介绍了推荐的棕地迭代循环。

## 🎯 实验目标

我们的研究与实验聚焦于：

### 技术无关性

- 使用多样化的技术栈构建应用
- 验证这一假设：规范驱动开发是一套流程，不与特定技术、编程语言或框架绑定

### 企业级约束

- 展示关键业务应用的开发
- 纳入组织层面的约束（云服务商、技术栈、工程实践）
- 支持企业设计系统与合规要求

### 以用户为中心的开发

- 为不同的用户群体和偏好构建应用
- 支持多种开发方式（从"氛围编码"到 AI 原生开发）

### 创意与迭代流程

- 验证并行实现探索的理念
- 提供稳健的迭代式功能开发工作流
- 将流程扩展到升级与现代化改造任务

## 🔧 环境要求

- **Linux/macOS/Windows**
- [受支持的](#-支持的-ai-编码助手集成) AI 编码助手。
- [uv](https://docs.astral.sh/uv/) 用于包管理（推荐），或 [pipx](https://pipx.pypa.io/) 用于持久化安装
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

如果你在使用某个助手时遇到问题，欢迎提交 issue，以便我们完善相应集成。

## 📖 深入了解

- **[完整的规范驱动开发方法论](./spec-driven.md)** —— 深入了解整个流程
- **[快速上手指南](https://github.github.io/spec-kit/quickstart.html)** —— 分步实现演练

---

## 💬 支持

如需帮助，请提交 [GitHub issue](https://github.com/github/spec-kit/issues/new)。我们欢迎缺陷报告、功能建议，以及关于使用规范驱动开发的各类问题。

## 🙏 致谢

本项目深受 [John Lam](https://github.com/jflam) 的工作与研究的影响，并在其基础上构建。

## 📄 许可证

本项目基于 MIT 开源许可证的条款授权。完整条款请参阅 [LICENSE](./LICENSE) 文件。
