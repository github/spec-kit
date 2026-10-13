<div align="center">
    <img src="https://raw.githubusercontent.com/github/spec-kit/main/media/logo_large.webp" alt="Spec Kit 标志" width="200" height="200"/>
    <h1>🌱 Spec Kit</h1>
    <h3><em>与你的编码助手一起，依据规范开发、修复缺陷，或评估想法。</em></h3>
</div>

<p align="center">
    <a href="https://github.com/github/spec-kit/releases/latest"><img src="https://img.shields.io/github/v/release/github/spec-kit" alt="最新版本"/></a>
    <a href="https://github.com/github/spec-kit/stargazers"><img src="https://img.shields.io/github/stars/github/spec-kit?style=social" alt="GitHub stars"/></a>
    <a href="https://github.com/github/spec-kit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/github/spec-kit" alt="许可证"/></a>
    <a href="https://github.github.io/spec-kit/"><img src="https://img.shields.io/badge/docs-GitHub_Pages-blue" alt="文档"/></a>
</p>

<p align="center">
    <a href="./README.md">English</a> ·
    <strong>简体中文</strong> ·
    <a href="./README.ja.md">日本語</a>
</p>

Spec Kit 是一个开源工具套件，为 AI 编码助手提供结构化流程、可复用模板和有据可查的成果。
你可以从以下三种流程中任选一种开始，按需定制，也可以引入自己的流程。

## 选择你的流程

| 你的需求 | 流程 | 产出 |
| --- | --- | --- |
| 构建功能或应用 | [规范驱动开发](#规范驱动开发) | 从规范出发，完成规划、实现与收敛 |
| 排查并修复异常行为 | [缺陷修复](#缺陷修复) | 经评估的原因、范围明确的修复与验证记录 |
| 判断一个想法是否值得投入 | [想法评估](#想法评估) | 基于证据决定推进、澄清或停止 |

这三种流程是**彼此独立的入口**，不是必须依次完成的三个阶段。
SDD 内置于核心；缺陷修复和想法评估由随工具提供的扩展实现，需要时再安装。

<a id="-快速开始"></a>
<a id="-环境要求"></a>
<a id="1-安装-specify-cli"></a>
<a id="2-初始化项目"></a>

## 快速开始

你需要 **Python 3.11+**、**[uv](https://github.github.io/spec-kit/install/uv.html)**
以及受支持的 AI 编码助手，可在 Linux、macOS 或 Windows 上使用。
**仅 CLI 配置步骤在终端中执行**：从 PyPI 安装 Spec Kit 并创建项目：

```bash
uv tool install specify-cli
specify init my-project --integration copilot
cd my-project
```

CLI 只需安装一次，项目只需初始化一次；以下三种流程共用这套准备步骤。

<a id="-支持的-ai-编码助手集成"></a>

示例采用 **GitHub Copilot 默认的技能（skills）模式**。
如需使用其他助手，将 `copilot` 替换为对应的
[集成标识](https://github.github.io/spec-kit/reference/integrations.html)。

已有代码？请参阅[现有项目指南](https://github.github.io/spec-kit/guides/existing-projects.html)。
锁定版本、其他安装方式、CI 与故障排查见[安装指南](https://github.github.io/spec-kit/installation.html)；
更新已安装的 CLI 和项目文件见[升级指南](https://github.github.io/spec-kit/upgrade.html)。

现在，在**项目目录中启动编码助手**，选择以下一种流程。
在**助手的聊天界面中逐个调用 `/speckit-*` 技能**，检查结果后再继续。
这些是助手技能，不是终端命令。其他助手或模式可能采用[不同的调用语法](https://github.github.io/spec-kit/reference/integrations.html#command-invocation)。

<a id="-什么是规范驱动开发"></a>
<a id="3-确立项目准则"></a>
<a id="4-编写规范"></a>
<a id="5-制定技术实现方案"></a>
<a id="6-拆解为任务"></a>
<a id="7-执行实现"></a>

## 规范驱动开发

先明确**做什么、为什么做**，再决定**怎么实现**。
规范驱动开发（SDD）将需求转化为规范、技术方案和可执行任务，再依据这些制品指导实现。

**每个项目先确立一次准则；每个功能依次完成：规范 → 方案 → 任务 → 实现 → 收敛。**

在助手的聊天界面中调用以下技能：

```text
/speckit-constitution Create principles focused on code quality, testing, and maintainability.
/speckit-specify Build a photo organizer with albums grouped by date and a tile preview of each album.
/speckit-plan Use Vite with vanilla JavaScript. Keep images local and store metadata in SQLite.
/speckit-tasks
/speckit-implement
/speckit-converge
```

反复执行 **implement → converge**，直到收敛报告给出 **Converged**。
需要额外的质量把关时，可加入需求澄清、检查清单和一致性分析。

[SDD 实战指南](https://github.github.io/spec-kit/quickstart.html) ·
[命令参考](https://github.github.io/spec-kit/reference/agentic-sdd.html)

## 缺陷修复

将诊断、修复和验证分开，让助手针对评估出的原因修复，并检查最初出现的症状。
无需先走一遍 SDD 功能开发流程。

**CLI 配置（终端）**：在项目目录下安装这个可选扩展：

```bash
specify extension add bug
```

然后在助手的聊天界面中依次调用 **assess → fix → test**（评估 → 修复 → 测试）技能：

```text
/speckit-bug-assess "Submitting an empty password crashes the login form." slug=login-crash
/speckit-bug-fix slug=login-crash
/speckit-bug-test slug=login-crash
```

报告保存在 `.specify/bugs/login-crash/`。请检查最终结论：
`verified`（已验证）、`partial`（部分验证）或 `failed`（失败）。缺少验证不算修复成功。

[缺陷修复指南](https://github.github.io/spec-kit/guides/bugfix.html) ·
[命令参考](https://github.github.io/spec-kit/reference/agentic-bugfix.html)

## 想法评估

在投入之前先收集证据，无论这个想法最终是否会成为软件。
这是一个独立流程，也适用于非软件类想法，即使项目中没有源代码也能使用。

**CLI 配置（终端）**：在项目目录下安装这个可选扩展：

```bash
specify extension add assess
```

然后在助手的聊天界面中依次调用 **intake → research → define → shape → decide**
（收集想法 → 调研 → 定义问题 → 形成方案 → 决策）技能：

```text
/speckit-assess-intake "Let users work offline and sync when they reconnect." slug=offline-mode
/speckit-assess-research slug=offline-mode
/speckit-assess-define slug=offline-mode
/speckit-assess-shape slug=offline-mode
/speckit-assess-decide slug=offline-mode
```

制品保存在 `.specify/assessments/offline-mode/`，最终给出
**go / needs-clarification / kill**（推进 / 需要澄清 / 停止）的决策。
遇到待澄清问题时，直接完善已有的 Markdown 制品，或请助手协助修改，而不是重新生成整个阶段。
如果决定开发，可将 `go` 的评估结果交给 `/speckit-specify`；记录理由后停止，同样是有价值的结果。

[想法评估指南](https://github.github.io/spec-kit/guides/assessment.html) ·
[命令参考](https://github.github.io/spec-kit/reference/agentic-assessment.html)

<a id="-打造你自己的-spec-kit扩展与预设"></a>
<a id="-捆绑包面向角色的一键配置"></a>
<a id="-社区"></a>

## 定制或引入自己的流程

**扩展**新增能力，**预设**调整现有行为，**工作流**自动执行步骤，**捆绑包**打包面向角色的配置。
单个项目的一次性模板调整可使用项目本地覆盖；流程或术语的本地化可使用预设。

[定制指南](https://github.github.io/spec-kit/guides/customization.html) ·
[社区扩展、预设、捆绑包与实战演练](https://github.github.io/spec-kit/community/overview.html)

<a id="-specify-cli-参考"></a>
<a id="可用的斜杠命令"></a>
<a id="-核心理念"></a>
<a id="-开发阶段"></a>
<a id="-实验目标"></a>
<a id="️-视频概览"></a>
<a id="-深入了解"></a>

## 文档

以下链接指向英文指南。工具升级与功能规范演进是两件事：升级时更新工具文件，需求变化时更新 `specs/` 制品。

- [CLI 参考](https://github.github.io/spec-kit/reference/overview.html)与[流程命令](https://github.github.io/spec-kit/reference/agentic-sdd.html#command-overview)
- [SDD 理念](https://github.github.io/spec-kit/concepts/sdd.html)、[完整方法论](./spec-driven.md)与[现有规范演进](https://github.github.io/spec-kit/guides/evolving-specs.html)
- [视频概览](https://github.github.io/spec-kit/quickstart.html#video-overview)与[项目历史](https://github.github.io/spec-kit/history.html)
- [Spec Kit 如何使用 Spec Kit](./CONTRIBUTING.md#does-spec-kit-use-spec-kit)

<a id="-支持"></a>

## 支持与贡献

[报告缺陷或提出功能建议](https://github.com/github/spec-kit/issues/new) ·
[贡献指南](./CONTRIBUTING.md) · [行为准则](./CODE_OF_CONDUCT.md)

<a id="-许可证"></a>

Spec Kit 采用 [MIT 许可证](./LICENSE)。
