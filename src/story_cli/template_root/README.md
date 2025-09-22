# Story Kit 工作区

欢迎来到 **Story Kit** 项目模板。这个模板是基于 Spec-Driven Development 思想演化而来，用于管理长篇或系列小说的完整创作流程。核心流程保持和 Spec Kit 相同：

1. `/constitution` 先定义创作原则与世界观边界；
2. `/specify` 把灵感或大纲转化为结构化的故事蓝图；
3. `/plan` 生成技术化（叙事化）的实施计划与配套文档；
4. `/tasks` 把创作拆分为可执行的任务；
5. `/implement` 根据任务节奏推进创作，可选择自动或等待指令的模式。

Story Kit 的目标是：

- 让 AI 深度理解作者的创意、角色、世界观、写作目标；
- 在故事创作各阶段主动列出理解、疑问和风险，让作者确认；
- 支持多种创作节奏：全自动冲刺、分阶段审核、或实验性探索；
- 保持所有叙事设定、剧情推进、修订记录在同一树状结构内，方便追踪。

## 目录概览

```
.storykit/               # Story Kit CLI 生成的元数据
.specify/                # Slash command 运行依赖的脚本与模板
memory/                  # 宪章与可长期保存的世界观资料
specs/                   # 每个故事增量（章节/支线）都会生成一个编号目录
scripts/                 # create-new-feature 等脚本
templates/               # Story Kit 的 Markdown 模板（spec, plan, tasks）
```

## 重要文件

- `memory/constitution.md`：创作宪章模板。保持它最新，Story Kit 的所有决策都会参考这里。
- `templates/spec-template.md`：故事规格书模板，/specify 会基于它生成 `specs/编号/spec.md`。
- `templates/plan-template.md`：实施计划模板，聚焦于世界观、角色弧线、章节结构与协作模式。
- `templates/tasks-template.md`：任务模板，把创作拆成「世界观整理 → 人物深潜 → 大纲 → 草稿 → 修订」等阶段。
- `templates/commands/*.md`：Slash command 的提示词。不同命令会加载不同的文件。

## 协作模式

Story Kit 在 `plan.md` 中允许选择四种协作模式：

- **guided**：每完成一个主要阶段就停下来等待作者确认（默认）。
- **auto**：AI 按任务顺序自动推进，适合快速出初稿。
- **hybrid**：自动推进草稿，但在关键节点暂停寻求确认。
- **sandbox**：面向平行世界或番外内容，允许大量分叉实验，不写入主时间线。

模式在 CLI 初始化时可以指定，也可以在 `plan.md` 中随时调整。

## 下一步建议

1. 打开 `memory/constitution.md`，用 `/constitution` 定义或更新创作宪章。
2. 用 `/specify` 讲述你正在构思的故事或章节，Story Kit 会产出结构化蓝图。
3. 在确认蓝图无误后，用 `/plan` 生成可执行的写作路线图与角色/世界观文档。
4. `/tasks` 生成任务列表，并依据想要的协作模式调度创作。
5. `/implement` 按任务推进创作；若是 guided/hybrid 模式，Story Kit 会在阶段间主动汇报。

写作愉快！
