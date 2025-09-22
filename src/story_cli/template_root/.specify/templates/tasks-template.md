# Story Tasks: [FEATURE TITLE]

**Input**: Narrative plan `/specs/[###-story-fragment]/plan.md`  
**Prerequisites**: research.md, character-bibles/, world-lore.md, timeline.md (若已生成)

## Execution Flow (story_tasks)
```
1. 读取 plan.md → 若不存在：ERROR "缺少故事实施计划"
2. 收集 Phase 0-2 产出（research, character, world, timeline, quickstart）
3. 按 Story Kit 协作模式拆解任务
4. 标记需要人工确认的节点 (guided/hybrid)
5. 为自动化/实验任务标注 [AUTO] 或 [SANDBOX]
6. 生成任务编号 T001...，注明文件路径与交付标准
7. 构建依赖图与并行建议
8. 验证 Checklist 后写入 tasks.md
```

## 任务格式
- `[ID] [TAG?] 描述 — 输出路径`
- 标签：`[P]` 可并行；`[AUTO]` 自动执行；`[REVIEW]` 等待作者确认；`[SANDBOX]` 平行实验

## Phase 3.1 – 世界观与研究落实
- [ ] T001 汇总 research.md → 更新 world-lore.md 与风险登记
- [ ] T002 [P] 根据研究结果刷新 timeline.md
- [ ] T003 [P][REVIEW] 将关键设定写入 memory/lore/xxx.md 并请求确认

## Phase 3.2 – 角色深潜
- [ ] T010 为主角撰写 character-bibles/hero.md（语气、弧线、秘密）
- [ ] T011 [P] 为反派撰写 character-bibles/villain.md
- [ ] T012 [P] 为关键配角撰写 character-bibles/[name].md
- [ ] T013 [REVIEW] 校对角色关系网，更新 plan.md 的角色表

## Phase 3.3 – 场景与节奏
- [ ] T020 生成章节表 outline/chapters.md（含 POV、目标、冲突）
- [ ] T021 [P] 为关键章节撰写 beat 卡（outline/beats/chXX.md）
- [ ] T022 [REVIEW] 根据 quickstart.md 编写验收脚本（试读要点、QA 表）

## Phase 3.4 – 草稿执行
- [ ] T030 [AUTO] Draft Chapter 1 初稿 → drafts/ch01.md
- [ ] T031 [AUTO] Draft Chapter 2 初稿 → drafts/ch02.md
- [ ] T032 [P][REVIEW] 汇总章节后生成阶段汇报 summaries/arc1.md
- [ ] T033 [SANDBOX] 创建实验分支 drafts/sandbox/what-if-1.md（仅在 sandbox 模式启用）

## Phase 3.5 – 修订与质检
- [ ] T040 对 Chapter 1 进行人物语气回放 → revisions/ch01_voice.md
- [ ] T041 [P] 对 Chapter 2 进行节奏/张力调整 → revisions/ch02_pacing.md
- [ ] T042 [REVIEW] 运行 quickstart.md 验收脚本并记录结果 → reports/acceptance.md
- [ ] T043 整体一致性检查（人物/伏笔/设定）→ reports/continuity.md

## Dependencies
- 研究澄清 (T001-T003) 完成后才能进入角色/大纲阶段
- 角色档案 (T010-T013) 是章节大纲 (T020-T022) 的前置
- 草稿 (T030+) 必须遵守 outline 输出
- 修订 (T040+) 依赖草稿，并需经过 quickstart 验收

## Parallel Suggestions
```
# 并行写作示例（guided/hybrid 模式）
Task T010 + T011 + T012 可并行 → 人物档案由不同助手或批次完成
Task T020 与 T021 需串行完成，T022 需在作者确认后执行
如果选择 auto 模式，可让 T030/T031 顺序执行并在 T032 停顿汇报
```

## Validation Checklist
- [ ] 每个 `[OPEN QUESTION]` 已映射到具体任务或研究事项
- [ ] 所有任务包含输出文件路径
- [ ] `[AUTO]` 任务符合协作模式限制
- [ ] `[REVIEW]` 任务标注明确的暂停/确认点
- [ ] sandbox 任务不会污染主线目录
- [ ] 依赖关系清晰，避免同文件的并行冲突
