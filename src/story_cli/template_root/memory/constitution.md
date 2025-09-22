# {{STORY_TITLE}} Story Constitution
<!-- Story Kit 会引用此文件来判断写作原则与协作边界 -->

<!-- 请用 /constitution 命令更新本文件。所有 [PLACEHOLDER] 栈位都需要被替换成具体内容。-->

<!-- 同步影响报告会自动写在这行上方 -->

## Narrative Guardrails

### [PILLAR_1_TITLE]
[PILLAR_1_DESCRIPTION]

### [PILLAR_2_TITLE]
[PILLAR_2_DESCRIPTION]

### [PILLAR_3_TITLE]
[PILLAR_3_DESCRIPTION]

### [PILLAR_4_TITLE]
[PILLAR_4_DESCRIPTION]

### [PILLAR_5_TITLE]
[PILLAR_5_DESCRIPTION]

> 建议原则覆盖：整体基调 & 价值观、目标读者、禁忌/敏感内容边界、节奏与篇幅标准、语言/文体要求。

## Canon Codex

- **世界观与时代背景**： [WORLD_CONTEXT]
- **科技/魔法体系**： [POWER_SYSTEM]
- **历史与时间线锚点**： [TIMELINE_PILLARS]
- **人物伦理与社会规则**： [SOCIAL_CONTRACT]
- **读者体验与情绪目标**： [READER_PROMISE]
- **扩展宇宙策略**： [EXPANSION_RULES]

任何未确定的设定请标记为 `[OPEN QUESTION: 描述待定事项]`，Story Kit 会在规划阶段主动提醒澄清。

## Collaboration Charter

| 议题 | 约定 |
|------|------|
| 默认协作模式 | **{{DEFAULT_INTERACTION_MODE}}** （guided/auto/hybrid/sandbox）|
| 自动创作允许范围 | [AUTO_BOUNDARIES] |
| 需要人工确认的里程碑 | [REVIEW_GATES] |
| 允许的实验分支 | [SANDBOX_RULES] |
| 角色/情节变更需满足 | [CHANGE_CRITERIA] |
| 写作节奏或交付频率 | [CADENCE] |

当 `/plan` 或 `/implement` 检测到与此表冲突的决定时，会要求提供理由或调整设定。

## Canon Maintenance Workflow

1. **发现**：当 `/specify` 或 `/plan` 标记 `[OPEN QUESTION]`/`[RISK]` 时，需创建澄清任务。
2. **决策**：重大设定更新需记录在 `memory/` 下的对应文档，并在本宪章中留下版本说明。
3. **同步**：运行 `/plan` 后需要执行 `scripts/update-agent-context`，同步最新 canon 至各 AI 助手文件。
4. **回溯**：任何冲突必须说明来源章节与变更策略，必要时创建平行宇宙或番外分支。

## Governance

- Story Kit 宪章优先级高于所有旧文档；冲突时以最新宪章为准。
- 修订流程：提出 → 说明影响 → 更新文档 → 核对模板（spec/plan/tasks）。
- 版本策略：使用 `MAJOR.MINOR.PATCH`。
  - **MAJOR**：基调、受众或世界观发生根本变化。
  - **MINOR**：新增规则、合作模式调优或扩充 canon。
  - **PATCH**：措辞修正或补充例子，不影响行为。
- 审核频率：至少每 `[REVIEW_CYCLE]` 完成一次全面复盘；必要时由 `/tasks` 生成专门的校对任务。

**Version**: [CONSTITUTION_VERSION] | **Ratified**: [RATIFIED_DATE] | **Last Amended**: {{INITIALIZED_AT}}
