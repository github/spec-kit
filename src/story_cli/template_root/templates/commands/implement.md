---
description: Execute the story tasks respecting collaboration mode and checkpoints.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

用户输入（若有）：

$ARGUMENTS

Story Kit 在执行 `/implement` 前需：

1. 运行 `{SCRIPT}`，确认 `tasks.md`、`plan.md` 等文件存在。
2. 读取 `.storykit/storykit.config.json` 获取协作模式；若作者在指令中覆盖，则以指令为准。
3. 解析 `tasks.md`：
   - 识别 `[AUTO]`、`[REVIEW]`、`[SANDBOX]`、`[P]` 标签
   - 按阶段（世界观/角色/大纲/草稿/修订）组织
   - 找出章节参考包、时间线写回、角色档案更新等任务
4. 设定执行策略：
   - **guided**：每阶段完成后暂停，列出成果 & 待确认项
   - **auto**：按顺序执行所有 `[AUTO]` 任务，遇到 `[REVIEW]` 仅记录提醒
   - **hybrid**：自动完成草稿任务，在 `[REVIEW]` 处等待确认
   - **sandbox**：允许写入 `drafts/sandbox/`，但需在阶段末汇报差异
5. 逐任务执行：
   - 明确产出文件、写作要点（语气、长度、节奏）
   - 在草稿前确认参考包任务已完成（上一章确认稿、人物档案、时间线锚点）
   - 对草稿输出提供章节总结 + 下一步建议
   - 对 sandbox 输出标记“不影响主线”
6. 每完成一项任务：
   - 更新 `tasks.md` 的复选框 → `[X]`
   - 若任务失败，写入错误说明并停止后续依赖项
   - 章节确认后立即执行时间线写回与角色档案更新，并注明引用的文件路径
7. 阶段结束时：
   - 汇总成果、剩余风险、需要作者答复的提问
   - 对 guided/hybrid 返回等待提示
8. 最终输出：
   - 已完成 / 未完成任务列表
   - 文档或草稿的路径
   - 下一步推荐（例如提交审稿、生成下一批任务等）

严格遵守宪章与计划，发现冲突时暂停并请求确认。保持中文输出。禁止跳过 `[REVIEW]` 或 `[OPEN QUESTION]`。
