---
description: "Story Kit narrative implementation plan"
scripts:
  sh: scripts/bash/update-agent-context.sh __AGENT__
  ps: scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__
---

# Story Plan: [FEATURE TITLE]

**Branch**: `[###-story-fragment]` | **Date**: [DATE] | **Spec**: [link]  
**Input**: Blueprint `/specs/[###-story-fragment]/spec.md`

## Execution Flow (story_plan)
```
1. 加载 blueprint → 若不存在：ERROR "未找到故事规格"
2. 同步最新宪章 (memory/constitution.md)
3. 读取 Story Kit 配置 (.storykit/storykit.config.json)
4. 设定协作模式 (guided/auto/hybrid/sandbox)
5. Phase 0: 澄清未解决问题 → 生成 research.md
6. Phase 1: 构建 canon 文档 (角色档案、世界规则、时间线)
7. Phase 2: 制定章节/场景大纲与节奏 → quickstart.md
8. Phase 3 准备草稿执行策略与质量门槛
9. 更新 Progress Tracking & Collaboration Gates
```

---

## Summary
- **故事目标**： [PLAN_SUMMARY]
- **协作模式**： {{DEFAULT_INTERACTION_MODE}} （可在此调整）
- **作者确认点**： [REVIEW_GATES]

## Collaboration Gate Check
| 项目 | 验证 | 备注 |
|------|------|------|
| 宪章原则满足 | [ ] | 若违反，请记录在 “Complexity Tracker” 中 |
| 触发自动创作 | [ ] | 说明自动执行范围 |
| 需要暂停审核的阶段 | [ ] | guided/hybrid 模式必填 |
| sandbox 分支影响主线？ | [ ] | 若 YES，请列风险缓解措施 |

## Project Structure
```
story/
├── memory/
│   ├── constitution.md
│   ├── lore/               # 扩展世界设定（可由 Phase 1 创建）
│   └── characters/         # 角色档案 (Phase 1 输出)
├── specs/
│   └── [###-story-fragment]/
│       ├── plan.md         # 本文件
│       ├── research.md     # Phase 0
│       ├── character-bibles/
│       ├── world-lore.md
│       ├── timeline.md
│       ├── quickstart.md   # 验收与试读脚本
│       └── tasks.md        # /tasks 输出
```

## Phase 0 – Clarify & Research
- 汇总 blueprint 中的 `[OPEN QUESTION]` / `[RESEARCH TASK]`
- 每个问题生成 research 条目：
  - **Question**、**Why it matters**、**Proposed next step**
- 对关键风险使用标签：`[RISK: ...]`
- 输出 `research.md`
- 若仍有未分配负责人/方向 → 标记并告警

## Phase 1 – Canon Assembly
- 生成 `character-bibles/`：每个关键角色一个 Markdown，包含动机、弧线、角色声音、禁忌
- 生成 `world-lore.md`：地图、社会结构、资源、冲突规则
- 生成 `timeline.md`：主线节点 + 支线插入点
- 更新 `.storykit/storykit.config.json` 中的 `canon_timestamp`
- 运行 `{SCRIPT}` 同步至各 AI 助手指令文件

## Phase 2 – Outline & Pace
- 选择结构模板（默认三幕，可自定义）
- 构建章节/场景表：列出 POV、场景意图、冲突、伏笔、调用的研究
e.g.
```
| 序号 | POV | 场景目的 | 冲突 | 伏笔/暗线 | 升级路径 |
```
- 在 `quickstart.md` 中创建试读脚本：
  - 章节摘要
  - 预期情绪检查列表
  - 验收问题（用于人工或自动检查）

## Phase 3 – Drafting Strategy
- 明确写作顺序与任务切片（对接 `/tasks`）
- 指定：
  - 自动生成范围（auto/hybrid 模式）
  - 需要人工确认的输出（guided/hybrid）
  - sandbox 实验如何汇报并进入主线
- 定义质量门槛：语言风格、长度、节奏、校对流程

## Complexity Tracker
| 偏离项 | 需要的原因 | 更简单方案为何不可行 |
|--------|------------|------------------------|
| [VARIANCE_1] | [RATIONALE_1] | [ALTERNATIVE_REJECT] |

## Progress Tracking
- [ ] Phase 0: Research complete
- [ ] Phase 1: Canon assembled
- [ ] Phase 2: Outline ready
- [ ] Phase 3: Drafting strategy ready
- [ ] Collaboration gates reviewed
- [ ] 所有 `[OPEN QUESTION]` 已有处理计划

## Story Kit Signals
- **Auto mode ready?** [YES/NO]
- **Need author review before drafting?** [YES/NO]
- **Risks to highlight**:
  - [RISK_1]
  - [RISK_2]

更新本计划后，请运行 `/tasks` 生成任务，或视需要回到 `/specify` 补充设定。
