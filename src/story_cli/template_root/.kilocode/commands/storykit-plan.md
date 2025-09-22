# /plan — Story Kit

1. 概括 Story Kit 对当前目标的理解（含信心等级），列出仍待确认的问题。
2. 调用 `scripts/bash/setup-plan.sh --json` 获取计划文件路径与分支信息。
3. 结合故事蓝图、宪章与 `.storykit/storykit.config.json`，填充 `templates/plan-template.md`：
   - 协作模式、审核节点
   - Phase 0~3 的行动项
   - research.md / character-bibles / world-lore / timeline / quickstart 骨架
   - Complexity Tracker 与 Progress Tracking
4. 生成或更新相应文档，确保 `[OPEN QUESTION]` 与 `[RISK]` 均被记录。
5. 输出：计划文件路径、生成的 artefact 清单、作者需要确认的事项。

若作者要求自动模式，务必注明自动执行范围及停顿条件。保持中文输出。
