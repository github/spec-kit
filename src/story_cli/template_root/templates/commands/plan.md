---
description: Create the Story Plan with canon artefacts and collaboration gates.
scripts:
  sh: scripts/bash/setup-plan.sh --json
  ps: scripts/powershell/setup-plan.ps1 -Json
---

用户输入（偏好/补充要求）：

$ARGUMENTS

Story Kit 应：

1. **重复确认**：概括已确认的故事意图（来自 blueprint 与宪章），列出 Story Kit 对当前目标的理解，标注信心度。
2. 运行 `{SCRIPT}`，解析 JSON 获取 `FEATURE_SPEC`, `IMPL_PLAN`, `SPECS_DIR`, `BRANCH`。
3. 读取 `FEATURE_SPEC`、`memory/constitution.md` 与 `.storykit/storykit.config.json`，合并以下信息：
   - 协作模式 (guided/auto/hybrid/sandbox)
   - 宪章限制、读者承诺
   - 待澄清问题与研究任务
   - 时间线分段规则（`timeline_span`，例：每 {{TIMELINE_SEGMENT}} 章生成一个 master 文件）
4. 按 `templates/plan-template.md` 填写：
   - Summary & Collaboration Gate Check
   - Phase 0~3 细化
   - Canon 文档（character-bibles、world-lore、timeline）规划，并根据分段创建 `timeline/master-001-{{TIMELINE_SEGMENT_PAD}}.md` 占位
   - Drafting Strategy 与风险列表
5. Phase 0: 将 `[OPEN QUESTION]` & `[RESEARCH TASK]` 投射到 `research.md`
6. Phase 1: 为每个关键角色生成 character-bibles/xx.md 的骨架
7. Phase 2: 在 quickstart.md 中记录试读脚本与验收检查表，并定义“章节参考包”结构（上一章确认稿、人物档案、时间线锚点、章节目标）
8. 在 Chapter Reference Playbook 中明确创作前/后需要引用与回写的步骤
9. 更新 Progress Tracking，所有未完成项保持未勾选但给出下一步
10. 输出：
   - Story Plan 路径
   - 生成/更新的文件列表
   - Story Kit 的理解摘要 + 待确认事项

若作者要求全自动创作，需在计划中注明自动执行的边界，并提醒 `/tasks` 与 `/implement` 会按相同模式执行。保持中文输出。
