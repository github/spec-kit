---
description: Transform a raw story idea into a structured Story Blueprint.
scripts:
  sh: scripts/bash/create-new-feature.sh --json "{ARGS}"
  ps: scripts/powershell/create-new-feature.ps1 -Json "{ARGS}"
---

用户输入（故事简述）如下：

$ARGUMENTS

Story Kit 必须在行动前先「复述理解」。执行步骤：

1. **理解校验**：列出 3-5 点 Story Kit 对故事的理解，逐项注明信心值（High/Medium/Low）。
2. **澄清问题**：任何模糊处使用 `[OPEN QUESTION: ...]` 格式列出，禁止猜测。
3. 运行 `{SCRIPT}` 创建新的故事分支，取得 JSON 输出中的 `BRANCH_NAME` 与 `SPEC_FILE`。
4. 打开模板 `templates/spec-template.md`，按照模板结构填入信息：
   - 作者意图与读者承诺
   - Story Kit 的理解清单
   - Canon 基础、角色网络、剧情架构
   - 未知 & 研究议题
5. 所有尚未确认的内容必须保留 `[OPEN QUESTION]` 或 `[RESEARCH TASK]` 标记。
6. 保存至 `SPEC_FILE`。
7. 汇总输出：
   - 分支名、蓝图路径
   - Story Kit 的理解摘要
   - 待澄清问题清单
   - 建议的下一步（通常是 `/plan` 或回答澄清）。

注意：本阶段不写任何最终文稿或场景细节，只负责结构化蓝图。保持中文输出。若用户没有给出信息，不要编造。
