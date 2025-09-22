---
description: Build or amend the story constitution with collaborative guardrails.
---

用户输入：

$ARGUMENTS

Story Kit 需要把上述说明融合进 `memory/constitution.md`。执行步骤：

1. 读取当前宪章，提取已有原则、协作设定、版本信息。
2. 根据用户输入梳理：
   - Story Kit 的理解（列出 bullet list）。
   - 任何模糊信息以 `[OPEN QUESTION: ...]` 标记。
3. 如有关键缺失（读者目标、禁忌内容、默认协作模式等），提出澄清问题。
4. 生成「同步影响报告」（HTML 注释）：
   - 版本号：旧 → 新（根据变更严重度决定 MAJOR/MINOR/PATCH）。
   - 新增/修改/删除的原则与章节。
   - 仍待补充的 TODO。
5. 用新内容替换 `memory/constitution.md` 中对应 placeholder，不留未解释的 `[PLACEHOLDER]`。
6. 更新结尾的版本与日期（ISO 8601）。若用户未确认 ratified date，则保留原值。
7. 输出：
   - 新版本号。
   - Story Kit 的理解要点。
   - 清单形式的 TODO / OPEN QUESTION。

注意：宪章应覆盖创作原则、世界观边界、敏感内容限制、协作模式、审核节奏等。不要写成具体剧情。保持中文输出，除非作者另有指示。
