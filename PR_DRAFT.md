feat(templates): add /speckit.ui blueprint, fail-fast scripts, JSON Schema, and smoke CI

摘要

新增可选命令 /speckit.ui 及配套模板与脚本，生成框架无关的 UI 蓝图（设计令牌、组件 API、状态机、语义 HTML 骨架、BDD、数据契约）；修复打包路径幂等（避免 .specify.specify），新增跨平台烟测工作流，杜绝“静默空文件”。

背景/动机

- 现状与痛点：
  - UI/UX 仅靠自然语言，机器理解空间大，易在样式/结构/交互与数据契约上产生偏差。
  - 打包时路径替换过度可能出现 .specify.specify/。
  - 模板缺失时旧脚本会“touch 空文件”，属于“静默降级”，与仓库质量基调不符。
- 目标与原则（规格先行、技术中立、可复制验证）：
  - 用 Tokens/组件表/流程图/HTML 骨架/BDD/数据契约把 UI 决策工程化。
  - 不绑定具体框架（HTML + ARIA，注明如何映射到各框架）。
  - 打包后命令/模板即插即用，CI 端到端“体检+冒烟”验证。

变更内容

- 代码/脚本
  - scripts/bash/setup-ui.sh：双路径探测（.specify/templates/ui 与 templates/ui）、缺失即 fail-fast、输出 JSON 键：UI_DIR、TOKENS_FILE、COMPONENTS_SPEC、FLOWS_FILE、HTML_SKELETON、BDD_FILE、TYPES_SCHEMA、TYPES_TS、README_FILE
  - scripts/powershell/setup-ui.ps1：同上
  - .github/workflows/scripts/create-release-packages.sh：rewrite_paths 增加幂等折叠，避免 .specify.specify/
- 命令模板
  - templates/commands/ui.md：改为只使用脚本 JSON 键，不再硬编码路径；数据契约默认优先 JSON Schema（types.schema.json），TS 接口可选
- 模板
  - templates/ui/README.md（约定与路径使用）、templates/ui/tokens.json（扩展 breakpoints/zIndex/opacity/motion）、templates/ui/components.md、templates/ui/flows.mmd、templates/ui/skeleton.html、templates/ui/stories.feature、templates/ui/types.ts、templates/ui/types.schema.json
- 文档
  - README.md：Available Slash Commands 增加 /speckit.ui；新增 “UI Command Usage” 小节（分支/环境、只用 JSON 键、Schema 优先）
- 兼容性
  - 非破坏性（不改 CLI 内核）
- 与版本/日志（仅当触及 CLI 核心）
  - 是否修改 src/specify_cli/__init__.py：否
  - 版本/CHANGELOG：不适用

如何验证（可复现步骤）

- 环境要求：Python 3.11+、uv、Git
- 本地快速演示（不 init，Bash）
  - export SPECIFY_FEATURE=001-ui-blueprint
  - bash scripts/bash/setup-ui.sh | tee /tmp/ui.json
  - 真实 JSON 输出（示例）：
    - {"UI_DIR":"/abs/specs/001-ui-blueprint/ui","TOKENS_FILE":"/abs/specs/001-ui-blueprint/ui/tokens.json","COMPONENTS_SPEC":"/abs/specs/001-ui-blueprint/ui/components.md","FLOWS_FILE":"/abs/specs/001-ui-blueprint/ui/flows.mmd","HTML_SKELETON":"/abs/specs/001-ui-blueprint/ui/skeleton.html","BDD_FILE":"/abs/specs/001-ui-blueprint/ui/stories.feature","TYPES_TS":"/abs/specs/001-ui-blueprint/ui/types.ts","TYPES_SCHEMA":"/abs/specs/001-ui-blueprint/ui/types.schema.json","README_FILE":"/abs/specs/001-ui-blueprint/ui/README.md"}
  - 校验（Linux）：
    - jq -e '.README_FILE and .TOKENS_FILE and .COMPONENTS_SPEC and .FLOWS_FILE and .HTML_SKELETON and .BDD_FILE' /tmp/ui.json
    - for k in TOKENS_FILE COMPONENTS_SPEC FLOWS_FILE HTML_SKELETON BDD_FILE README_FILE; do f=$(jq -r .${k} /tmp/ui.json); test -s "$f" || echo "Empty: $f"; done
- 打包产物验证（Linux）
  - bash .github/workflows/scripts/create-release-packages.sh v0.0.5
  - unzip -p .genreleases/spec-kit-template-claude-sh-v0.0.5.zip .claude/commands/speckit.ui.md | grep -qv '.specify.specify/'
  - 解包后运行 .specify/scripts/.../setup-ui.*，重复“JSON 键齐备 + 文件非空”检查
- CI 冒烟
  - .github/workflows/ui-smoke.yml（Ubuntu + Windows）：
    - 构建包、检查无 .specify.specify、执行 create-new-feature + setup-ui、校验 JSON 键存在与文件非空、JSON 合法性（jq），并做脚本静态分析（shellcheck/PSScriptAnalyzer 警告级）

风险与回滚

- 风险：路径重写规则微调、增加 CI 工作流
- 回滚：如有问题，可快速 revert 本 PR；或保留 UI 模板与命令，移除幂等折叠/CI 后再观察

文档与工作流

- README 是否更新：是（Available Slash Commands 与 UI Command Usage）
- docs 是否更新：否
- CI/CD 影响：是（新增 .github/workflows/ui-smoke.yml）

性能与安全

- 性能：仅模板与脚本文本；无运行时开销
- 安全：不引入凭据；路径输出为本地绝对路径，仅供本地生成与编辑

AI 使用披露

- 此 PR 使用了 AI 辅助起草与整理模板/脚本，所有改动已人工审阅并在本地与打包环境中验证通过。

关联项

- 建议评审人：@localden
- 重点希望评审的部分：
  - 命令说明“只用 JSON 键”的稳健性
  - fail-fast 行为是否符合仓库质量预期
  - JSON Schema/TS 双模板的技术中立性与默认策略（Schema 优先）

