# Story Kit 说明

Story Kit 是 Spec Kit 上延伸出的小说创作流程套件，核心理念是把故事创作拆分为可以与 AI 协作的结构化阶段。

## 核心差异

- **故事导向模板**：`spec-template.md`、`plan-template.md`、`tasks-template.md` 分别面向 Story Blueprint、Canon 计划和写作任务。
- **协作模式**：支持 `guided`（阶段停顿）、`auto`（完全自动）、`hybrid`（草稿自动 + 审核停顿）、`sandbox`（平行试验）。
- **章节参考包与写回**：每章开写前生成 `references/chXX.md`（上一章确认稿、人物档案、主时间线锚点），章节确认后自动有任务更新时间线与角色档案。
- **时间线分段**：主时间线按 `timeline_span`（默认 50 章）分段保存，如 `timeline/master-001-050.md`、`timeline/master-051-100.md`。
- **命令文件**：`.claude/commands/`、`.gemini/commands/` 等目录下提供 Story Kit 版本的 slash command。
- **Canon 文档**：`memory/` 下新增 `characters/` 与 `lore/` 目录，用于长期维护角色档案与世界设定。

## CLI 使用

```bash
uvx --from git+https://github.com/github/spec-kit.git storyfy init saga-one --ai claude --interaction guided
```

参数说明：
- `--ai`：首选 AI 助手（claude、gemini、cursor…）。用于记入配置，方便自定义提示词。
- `--interaction`：协作模式（guided/auto/hybrid/sandbox）。`plan.md` 与 `/implement` 会引用。
- `--timeline-span`：主时间线每个文件覆盖的章节数，决定 `timeline/master-*.md` 的范围（默认 50 章）。
- `--here`：在当前目录初始化 Story Kit 文件。
- `--no-git`：跳过 git 初始化。

初始化后会生成 `.storykit/storykit.config.json`，记录基本元数据（标题、协作模式、AI 助手）。

## 推荐工作流

1. `/constitution`：定义故事创作原则和协作边界。
2. `/specify`：输入故事构想，得到结构化的 Story Blueprint。
3. `/plan`：生成 `research.md`、`character-bibles/`、`world-lore.md`、按 `timeline_span` 分段的主时间线文件，以及包含章节参考包模板的 `quickstart.md`。
4. `/tasks`：拆分为按阶段执行的任务列表，自动添加章节参考包任务、章节确认后写回时间线/角色档案的任务，并设置 `[AUTO]` / `[REVIEW]` 标签。
5. `/implement`：按协作模式执行任务；guided/hybrid 会在阶段结束时等待确认；章节确认通过后立即写回时间线与角色档案。

## 目录结构

```
.storykit/               # CLI 元数据
.specify/                # slash 命令模板与脚本
memory/
  ├─ constitution.md     # 宪章
  ├─ characters/         # 角色档案（含近期事件）
  └─ lore/               # 世界观补充
specs/
  └─ 001-story-fragment/
       ├─ spec.md
       ├─ plan.md
       ├─ research.md
       ├─ character-bibles/
       ├─ world-lore.md
       ├─ timeline/       # 分段主时间线（如 master-001-050.md）
       ├─ quickstart.md
       └─ tasks.md
outline/
 drafts/
   ├─ chXX.md            # 草稿工作文件
   └─ confirm/           # 章节确认稿
 references/             # 章节参考包（上一章、人物、时间线）
 revisions/
 reports/
 timeline/               # 汇总入口，可索引 specs 中的主时间线
```

## 自定义

- 若需新增协作模式，可修改 `templates/plan-template.md` 与 `templates/tasks-template.md` 中的逻辑，并在 CLI 配置中加入选项。
- 如果希望在 `/implement` 中植入更多 checkpoint，可调整 `templates/commands/implement.md`。
- 推荐将自己的世界设定或研究资料长期保存在 `memory/`，Story Kit 会在 `/plan` 和 `/tasks` 阶段自动引用。

祝写作顺利！
