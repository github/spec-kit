# Story Kit — Agent Notes

Story Kit 在项目初始化时已经为常见的 AI 助手放置好 Slash Command/Prompt 文件：

- `.claude/commands/storykit-*.md`
- `.gemini/commands/storykit-*.md`
- `.cursor/commands/storykit-*.md`
- `.qwen/commands/storykit-*.md`
- `.opencode/commands/storykit-*.md`
- `.windsurf/workflows/storykit-*.md`
- `.github/prompts/storykit-*.md`

如果你采用其他 IDE/CLI，请把 `templates/commands/` 内的模板复制到对应目录。关键是保持以下命令可用：

| Slash Command | 功能 | 必需脚本 |
|---------------|------|----------|
| `/constitution` | 更新故事宪章 | `memory/constitution.md` |
| `/specify` | 生成 Story Blueprint | `scripts/create-new-feature.*` |
| `/plan` | 构建故事实施计划 | `scripts/setup-plan.*` |
| `/tasks` | 拆分写作任务 | `scripts/check-prerequisites.*` |
| `/implement` | 执行任务 | `scripts/check-prerequisites.*` |

Command 文件默认使用中文撰写。如需英文/其他语言，可以复制模板后自行调整。
