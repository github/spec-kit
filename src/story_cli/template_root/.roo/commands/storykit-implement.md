# /implement — Story Kit

1. 确认 `.storykit/storykit.config.json` 中的协作模式，若用户临时指定则以最新指令为准。
2. 调用 `scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` 确认 tasks.md 存在。
3. 解析 `tasks.md`，按阶段分组任务，识别 `[AUTO]`、`[REVIEW]`、`[SANDBOX]`、`[P]`。
4. 根据模式执行：
   - guided：阶段完成即暂停，输出成果 & 待确认项。
   - auto：依序完成 `[AUTO]` 任务，遇到 `[REVIEW]` 仅记录提醒。
   - hybrid：草稿自动完成，但在 `[REVIEW]` 或章节点等待指示。
   - sandbox：生成内容到 `drafts/sandbox/` 并标记不影响主线。
5. 每完成任务：
   - 更新 `tasks.md` 复选框为 `[X]`
   - 附上产出文件路径与摘要
   - 若失败记录原因并停止依赖任务
6. 阶段收尾输出：完成任务、剩余风险、建议下一步。
7. 结束时给出：
   - 已完成/待完成任务列表
   - 需要作者输入的问题
   - 下一步建议（例如运行 `/tasks` 继续拆分或请求审稿）。

始终遵守宪章/计划，发现冲突立即暂停询问。保持中文输出。
