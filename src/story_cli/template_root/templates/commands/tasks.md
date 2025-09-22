---
description: Generate a Story Kit task list aligned with the narrative plan.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

用户输入（若有）：

$ARGUMENTS

Story Kit 需要产出 `tasks.md`：

1. 运行 `{SCRIPT}`，获取 `FEATURE_DIR` 与 `AVAILABLE_DOCS`。
2. 读取 `plan.md`，掌握协作模式、阶段目标、已标注的 `[AUTO]`/`[REVIEW]` 建议。
3. 根据可用文档（research, character-bibles, world-lore, timeline, quickstart）：
   - 将每个 `[OPEN QUESTION]` 或 `research` 映射为 T00X 任务。
   - 为每个角色、章节、草稿、修订生成对应任务。
4. 按 `templates/tasks-template.md` 的结构输出，确保：
   - 指明输出路径，例如 `drafts/ch01.md`。
   - 需要人工确认的任务标记 `[REVIEW]`。
   - 可自动执行的任务标记 `[AUTO]`。
   - sandbox 实验任务标记 `[SANDBOX]` 并放入独立目录。
   - 可并行的任务标记 `[P]`。
   - 每章在草稿前有“章节参考包”任务（上一章确认稿、人物档案、主时间线锚点）
   - 章节确认后需有更新 `timeline/master-*.md` 与 `memory/characters/*.md` 的任务
5. 构建依赖说明与并行示例。
6. 检查 Checklist，确保没有遗漏角色/章节/风险，且所有参考包/写回任务符合时间线分段规则。
7. 写入 `FEATURE_DIR/tasks.md`。
8. 输出任务统计、待作者确认的节点与下一步建议。

保持中文输出；不要提前执行任何创作任务。
