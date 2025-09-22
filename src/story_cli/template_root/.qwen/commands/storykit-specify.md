# /specify — Story Kit

1. 读取用户输入的故事构想，先以 bullet 列出 3-5 条 Story Kit 对设定的理解，并为每条标注信心高/中/低。
2. 将所有未知或需要确认的点记录成 `[OPEN QUESTION: ...]`。
3. 运行 `scripts/bash/create-new-feature.sh --json "{ARGS}"`（由代理执行），获取 `BRANCH_NAME` 与 `SPEC_FILE`。
4. 按 `templates/spec-template.md` 填充 Story Blueprint：
   - 作者意图与读者承诺
   - Canon 基础、角色网络、情节架构
   - Story Kit 理解清单
   - 未知 & 研究议题
5. 保存至 `SPEC_FILE`，并输出：分支名、文件路径、理解摘要、问题清单与推荐下一步。

禁止直接写章节内容；保持中文输出。
