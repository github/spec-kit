# Feature Specification: 公司特定标准模板

**Feature Branch**: `001-company-standards`  
**Created**: 2026-01-26  
**Status**: Draft  
**Input**: 用户描述: "阅读@ENHANCEMENT_REQUIREMENTS.md ,实现3.1公司特定模版功能"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 应用公司代码规范 (Priority: P1)

作为开发人员,我需要访问公司的代码规范模板,以便在编写代码时遵循统一的标准,确保代码质量和一致性。

**为什么是这个优先级**: 这是最基础和最常用的功能。每个开发人员每天都需要参考代码规范,它直接影响代码质量和团队协作效率。这是可以独立交付的最小价值单元。

**独立测试**: 可以通过以下方式独立测试:开发人员能够访问 `templates/company-standards/code-style/` 目录,查看特定语言(如 JavaScript、Python)的代码规范文档,并根据其中的示例和规则编写符合标准的代码。价值体现:即使其他功能未实现,开发人员也能立即使用规范改善代码质量。

**Acceptance Scenarios**:

1. **Given** 开发人员需要编写 JavaScript 代码, **When** 访问 `templates/company-standards/code-style/javascript.md`, **Then** 看到清晰的命名规范、代码格式、最佳实践和示例代码
2. **Given** 开发人员不确定如何处理错误处理, **When** 查阅相应语言的代码规范, **Then** 找到错误处理的标准模式和示例
3. **Given** 团队成员在代码审查时发现不符合规范的代码, **When** 引用规范文档中的具体条款, **Then** 提供明确的改进建议和参考示例
4. **Given** 新成员加入团队, **When** 阅读代码规范文档, **Then** 在30分钟内理解团队的编码标准和约定

---

### User Story 2 - 使用架构原则指南 (Priority: P2)

作为架构师或技术负责人,我需要参考公司的技术架构原则(Constitution),以便在做技术决策时保持一致性,避免技术栈混乱和过度工程。

**为什么是这个优先级**: 这是技术决策的指导文档,虽然不如日常代码规范使用频繁,但对于确保技术选型的一致性和避免技术债务至关重要。可以在 P1 完成后独立交付。

**独立测试**: 可以通过以下方式独立测试:技术负责人在选择新技术栈或做架构决策时,能够查阅 `templates/company-standards/constitution-template.md`,获取核心原则、批准的技术栈列表和禁止使用的技术,并据此做出符合公司标准的决策。

**Acceptance Scenarios**:

1. **Given** 需要为新项目选择前端框架, **When** 查阅 constitution 文档的"技术栈标准"章节, **Then** 看到批准使用的框架列表和版本要求
2. **Given** 开发人员想使用某个新库, **When** 检查"禁止使用"章节, **Then** 确认该库是否在黑名单中
3. **Given** 团队讨论是否采用微服务架构, **When** 参考"核心原则"中的"简单优于复杂"原则, **Then** 基于项目实际需求做出合理决策
4. **Given** 新项目启动, **When** 按照 constitution 中的要求设置项目, **Then** 所有配置符合公司安全、性能和质量标准

---

### User Story 3 - 执行安全审查清单 (Priority: P3)

作为开发人员或安全审查员,我需要使用标准化的安全审查清单,以便在代码审查或发布前系统地检查安全问题,确保不遗漏关键安全检查项。

**为什么是这个优先级**: 安全审查是发布流程的重要环节,但相比日常开发规范和架构决策使用频率较低。可以在前两个功能完成后独立交付和使用。

**独立测试**: 可以通过以下方式独立测试:在代码审查或发布前,审查员能够打开 `templates/company-standards/security-checklist.md`,逐项检查清单内容(如认证、授权、数据加密、输入验证等),确保所有安全要求都已满足。

**Acceptance Scenarios**:

1. **Given** 准备发布新功能, **When** 使用安全审查清单进行检查, **Then** 逐项验证认证、授权、加密、日志等安全要求是否满足
2. **Given** 发现代码中包含敏感信息, **When** 参考清单中的"敏感信息处理"章节, **Then** 按照标准流程修复问题(如使用环境变量、密钥管理服务)
3. **Given** 新增 API 端点, **When** 对照清单检查, **Then** 确认已实现 rate limiting、输入验证、错误处理等安全措施
4. **Given** 审查员完成安全检查, **When** 所有清单项都已勾选通过, **Then** 生成审查报告并批准发布

---

### User Story 4 - 遵循代码审查指南 (Priority: P4)

作为代码审查员,我需要参考统一的审查指南,以便提供一致性的审查反馈,确保审查质量和效率,避免主观性过强或遗漏重要检查项。

**为什么是这个优先级**: 审查指南帮助标准化代码审查流程,提高审查质量,但可以在基础规范建立后再引入。它增强了 P1 代码规范的执行效果。

**独立测试**: 可以通过以下方式独立测试:审查员在进行代码审查时,能够参考 `templates/company-standards/review-guidelines.md` 中的检查清单、常见问题和反馈模板,提供结构化的审查意见,并确保覆盖代码质量、安全性、性能等关键方面。

**Acceptance Scenarios**:

1. **Given** 收到 Pull Request, **When** 按照审查指南中的步骤进行审查, **Then** 系统地检查代码风格、逻辑正确性、测试覆盖率、安全问题等方面
2. **Given** 发现需要改进的代码, **When** 使用指南中提供的反馈模板, **Then** 给出清晰、建设性的改进建议(包含问题描述、影响和建议方案)
3. **Given** 不确定某个改动是否需要提出异议, **When** 参考指南中的"严重性分类", **Then** 判断问题等级(Critical/Major/Minor)并决定是否阻止合并
4. **Given** 新成员担任审查员, **When** 学习审查指南, **Then** 在一周内能够独立完成高质量的代码审查

---

### User Story 5 - 使用事故响应模板 (Priority: P5)

作为 DevOps 或运维人员,我需要使用标准化的事故响应模板,以便在生产事故发生时快速、有序地响应,确保记录完整并进行事后分析。

**为什么是这个优先级**: 事故响应模板在紧急情况下非常重要,但使用频率相对较低。这是一个增强功能,可以在核心规范都建立后再添加。

**独立测试**: 可以通过以下方式独立测试:当生产环境发生事故时,响应团队能够使用 `templates/company-standards/incident-response.md` 模板,记录事故详情(时间、影响、根因、解决方案),进行事后回顾,并生成完整的事故报告。

**Acceptance Scenarios**:

1. **Given** 生产环境发生服务中断, **When** 使用事故响应模板记录, **Then** 模板指导团队记录事故发生时间、影响范围、严重级别、响应步骤等关键信息
2. **Given** 事故已解决, **When** 使用模板进行事后分析(Post-Mortem), **Then** 生成包含根因分析、改进措施和时间线的完整报告
3. **Given** 需要通知利益相关者, **When** 使用模板中的通知指南, **Then** 根据事故严重级别选择合适的通知渠道和内容模板
4. **Given** 团队进行事故响应演练, **When** 按照模板流程操作, **Then** 在30分钟内完成从发现到记录的完整流程

---

### Edge Cases

- 当某种编程语言没有对应的代码规范文档时,开发人员应该如何处理?(提供通用规范或参考相似语言)
- 如果公司技术栈标准与项目特殊需求冲突,如何申请例外?(需要定义例外审批流程)
- 当模板内容过时或与实际情况不符时,如何更新模板?(需要定义模板维护和版本控制流程)
- 多语言团队如何使用这些模板?(考虑国际化或提供多语言版本)
- 外包团队或第三方开发者是否需要遵循这些标准?(需要明确适用范围)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统必须在 `templates/company-standards/` 目录下提供结构化的模板文件
- **FR-002**: 系统必须提供 constitution-template.md,包含公司技术架构核心原则、批准的技术栈和禁止使用的技术
- **FR-003**: 系统必须为至少 4 种主流编程语言提供代码规范文档(JavaScript/TypeScript、Python、Java、Go)
- **FR-004**: 每个代码规范文档必须包含:命名规范、代码格式、错误处理、最佳实践和反模式示例
- **FR-005**: 系统必须提供 security-checklist.md,涵盖 OWASP Top 10 和常见安全漏洞检查项
- **FR-006**: 系统必须提供 review-guidelines.md,包含代码审查流程、检查清单和反馈模板
- **FR-007**: 系统必须提供 incident-response.md,包含事故分类、响应流程和事后分析模板
- **FR-008**: 所有模板文档必须使用 Markdown 格式,易于版本控制和查看
- **FR-009**: Constitution 文档必须包含代码质量要求(如测试覆盖率阈值、复杂度限制)
- **FR-010**: 安全清单必须包含具体的检查项和通过标准,支持勾选完成状态
- **FR-011**: 模板必须包含实际示例代码和反例,便于理解和应用
- **FR-012**: 审查指南必须定义问题严重性分类(Critical/Major/Minor/Trivial)和处理建议

### Key Entities

- **代码规范 (Code Standard)**: 代表特定编程语言的编码规范,包含规则、示例、最佳实践。每个规范对应一种语言(如 JavaScript、Python)
- **架构原则 (Constitution)**: 代表公司级别的技术架构指导原则,包含核心价值观、技术栈标准、质量要求和禁用清单
- **安全清单 (Security Checklist)**: 代表标准化的安全审查项目列表,包含检查项、通过标准和参考文档
- **审查指南 (Review Guidelines)**: 代表代码审查的标准流程和方法,包含检查清单、反馈模板和严重性分类规则
- **事故响应 (Incident Response)**: 代表生产事故的标准处理流程,包含事故分类、响应步骤、通知机制和事后分析模板

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 开发人员能够在 5 分钟内找到并理解所需编程语言的代码规范
- **SC-002**: 90% 的新项目在启动时使用 constitution 模板定义技术栈,避免技术选型偏差
- **SC-003**: 代码审查周期缩短 30%,因为审查员有明确的审查指南和检查清单
- **SC-004**: 安全相关缺陷在发布前检出率提高 50%,归功于标准化的安全审查清单
- **SC-005**: 新成员在加入团队后 2 周内能够独立编写符合公司规范的代码
- **SC-006**: 代码规范违规率在实施后 3 个月内降低 60%
- **SC-007**: 生产事故响应时间从平均 45 分钟缩短到 20 分钟,因为有标准化的响应流程
- **SC-008**: 团队代码风格一致性评分达到 85% 以上(通过静态分析工具测量)
- **SC-009**: 事故事后报告完成率达到 100%,所有事故都有完整的根因分析文档
- **SC-010**: 跨团队代码协作冲突减少 40%,因为统一的代码规范降低了理解成本

## Assumptions *(optional)*

- 假设开发团队主要使用 JavaScript/TypeScript、Python、Java 和 Go 这四种语言
- 假设团队使用 Git 进行版本控制,可以方便地访问项目中的 Markdown 文档
- 假设团队有基本的代码审查流程,这些模板是在现有流程基础上的标准化增强
- 假设公司已经有部分非正式的编码规范或最佳实践,这些模板是对现有知识的系统化整理
- 假设团队成员具备基本的英文阅读能力,可以理解技术文档(如需要,未来可提供中文版)
- 假设开发环境中可以方便地访问项目仓库中的文档(通过 IDE、命令行或 Web 界面)

## Dependencies *(optional)*

- 依赖项目仓库的文档目录结构(需要创建 `templates/company-standards/` 目录)
- 可能依赖现有的公司技术文档或规范,作为模板内容的来源
- 未来可能与 CI/CD 工具集成,自动检查代码是否符合规范
- 未来可能与静态分析工具(如 ESLint、Pylint、SonarQube)集成,自动化检查规范遵循情况

## Agent Context File Standardization *(新增需求)*

### 问题背景

当前 Spec Kit 为不同 AI 代理生成不同的上下文文件：
- Claude: `CLAUDE.md`
- Gemini: `GEMINI.md`
- Cursor: `.cursor/rules/specify-rules.mdc`
- Windsurf: `.windsurf/rules/specify-rules.md`
- 等等...

**存在的问题**：
1. **项目臃肿**：每个代理一个文件，导致根目录或各代理目录充斥着重复内容的文件
2. **维护困难**：内容相同但分散在多个文件中，更新时容易遗漏或不同步
3. **团队协作问题**：团队成员使用不同代理时，各自维护自己的上下文文件，造成分歧
4. **违反标准趋势**：新代理（Amp、Q、Bob）已经开始使用 `AGENTS.md`，但旧代理仍在使用各自的文件

### 改进方案：统一使用 AGENTS.md

#### 核心原则
1. **AGENTS.md 作为唯一真实来源 (Single Source of Truth)**
   - 所有项目必须生成 `AGENTS.md` 作为核心上下文文件
   - 位置：项目根目录 `./AGENTS.md`

2. **代理特定文件作为符号链接或引用 (可选)**
   - 如果某些代理必须使用特定位置的文件（如 Cursor 的 `.cursor/rules/`），应该：
     - 创建符号链接指向 `AGENTS.md`
     - 或在特定位置文件中简单引用主文件
   
3. **渐进式迁移策略**
   - 新项目：默认只生成 `AGENTS.md`
   - 现有项目：提供迁移工具，合并现有代理文件到 `AGENTS.md`

#### 具体实现要求

**FR-AGENT-001**: `specify init` 命令必须默认生成 `AGENTS.md`，而不是代理特定文件

**FR-AGENT-002**: `update-agent-context.sh` 和 `update-agent-context.ps1` 必须只更新 `AGENTS.md`

**FR-AGENT-003**: 对于有特殊路径要求的代理（如 Cursor、Windsurf），在其特定目录创建简洁的引用文件：

```markdown
<!-- .cursor/rules/specify-rules.mdc -->
# Cursor Rules

Please refer to the main agent context file: [AGENTS.md](../../AGENTS.md)

All project guidelines, technologies, and standards are centralized there.
```

**FR-AGENT-004**: 提供迁移命令 `specify migrate-agents`，自动将现有的 `CLAUDE.md`、`GEMINI.md` 等合并为 `AGENTS.md`

**FR-AGENT-005**: 在 `.gitignore` 中明确不排除 `AGENTS.md`，确保团队共享

#### 模板结构

`AGENTS.md` 应包含所有代理通用的内容：

```markdown
# [Project Name] - AI Agent Context

> **Note**: This file serves as the universal context for all AI coding assistants.
> Whether you use Claude, Cursor, Copilot, Gemini, or any other agent, 
> refer to this document for project guidelines.

**Last Updated**: [DATE]

## Active Technologies

- [技术栈列表，从所有 plan.md 提取]

## Project Structure

[项目结构]

## Build & Test Commands

[构建和测试命令]

## Code Standards

[代码规范]

## Recent Changes

[最近的功能变更]

## Agent-Specific Notes

### For Cursor Users
- Additional cursor-specific configurations: `.cursor/rules/cursor-config.mdc`

### For Claude Code Users
- CLI command examples: `claude --command implement`

### For Windsurf Users  
- Windsurf workflows: `.windsurf/workflows/`

[其他代理特定说明]
```

#### 迁移路径

**阶段 1 - 立即改进 (Current)**
- 修改 `specify init` 默认生成 `AGENTS.md`
- 修改 `update-agent-context` 脚本只更新 `AGENTS.md`
- 更新文档说明新标准

**阶段 2 - 兼容过渡 (Next 2 releases)**
- 继续支持读取旧格式文件（如 `CLAUDE.md`）
- 添加警告：检测到旧格式时提示用户迁移
- 提供 `specify migrate-agents` 命令

**阶段 3 - 完全标准化 (Future)**
- 移除对旧格式的支持
- 所有模板和示例只展示 `AGENTS.md`

### 成功标准

- **SC-AGENT-001**: 新创建的项目只包含 `AGENTS.md`，根目录不再有 `CLAUDE.md`、`GEMINI.md` 等文件
- **SC-AGENT-002**: 团队成员使用不同代理时，都参考同一个 `AGENTS.md`，不会产生内容分歧
- **SC-AGENT-003**: 项目根目录看起来更整洁，代理相关文件减少 80%
- **SC-AGENT-004**: `update-agent-context` 脚本执行时间减少 70%（只需更新一个文件）
- **SC-AGENT-005**: 100% 的新代理默认使用 `AGENTS.md` 标准

---

## Out of Scope *(optional)*

- 自动化执行代码规范检查(如 linter 配置)不在本功能范围内,本功能仅提供文档指南
- 自动化的安全扫描工具集成不在本功能范围内,安全清单是手动审查指南
- 针对特定框架或库的详细最佳实践指南(如 React、Django)不在本功能范围内
- 多语言版本(如中文、日文)的模板翻译不在本功能范围内,首个版本仅提供英文
- 交互式的模板编辑或填写工具不在本功能范围内,模板以静态 Markdown 文件形式提供
- 模板使用情况的统计和分析不在本功能范围内

## Notes *(optional)*

- **为什么选择 Markdown**: Markdown 格式易于编写、版本控制和跨平台查看,适合开发团队使用
- **模板 vs 自动化**: 本功能提供的是指导性模板,不强制自动化执行。这允许团队在不同场景下灵活应用,同时为未来的自动化集成预留空间
- **渐进式实施**: 建议团队按照优先级逐步实施:先应用代码规范(P1),再引入架构原则(P2),最后完善安全和事故响应流程
- **社区参考**: 模板内容可以参考行业最佳实践,如 Airbnb JavaScript Style Guide、Google Python Style Guide、OWASP Security Guidelines 等
- **持续更新**: 模板应该是"活文档",需要定期根据团队反馈和行业变化进行更新。建议每季度审查一次。
