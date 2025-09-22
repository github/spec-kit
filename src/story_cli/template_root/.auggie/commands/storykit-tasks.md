# /tasks — Story Kit

1. 调用 `scripts/bash/check-prerequisites.sh --json` 获取 `FEATURE_DIR` 与可用文档。
2. 读取 `plan.md`，识别协作模式及需要 `[AUTO]` / `[REVIEW]` 的节点。
3. 根据 `templates/tasks-template.md` 生成任务：
   - Phase 3.1~3.5（研究→角色→大纲→草稿→修订）
   - 每个任务写明输出路径与具体目标
   - 需要人工批准的任务加 `[REVIEW]`，可自动执行的加 `[AUTO]`，可并行的加 `[P]`
   - sandbox 实验任务放入 `drafts/sandbox/`
4. 构建依赖说明和并行建议。
5. 写入 `FEATURE_DIR/tasks.md`，并汇报任务统计、待确认事项、下一步建议。

保持中文输出，不要提前完成任务内容。
