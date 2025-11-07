---
description: Generate an actionable, dependency-ordered tasks.md for the feature based on available design artifacts.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Load design documents**: Read from FEATURE_DIR:
   - **Required**: plan.md (tech stack, libraries, structure), spec.md (user stories with priorities)
   - **Optional**: data-model.md (entities), contracts/ (API endpoints), research.md (decisions), quickstart.md (test scenarios)
   - Note: Not all projects have all documents. Generate tasks based on what's available.

3. **Execute task generation workflow**:
   - Load plan.md and extract tech stack, libraries, project structure
   - Load spec.md and extract user stories with their priorities (P1, P2, P3, etc.)
   - If data-model.md exists: Extract entities and map to user stories
   - If contracts/ exists: Map endpoints to user stories
   - 如果存在 api 相关部分，需要在 api 的 phase 后紧跟一个 生成 api mock server phase 
     - 这是为了在后端服务没有 ready 前，前端可以独立进行开发
   - If research.md exists: Extract decisions for setup tasks
   - Generate tasks organized by user story (see Task Generation Rules below)
   - Validate task completeness (each user story has all needed tasks, independently testable)

4. **Generate tasks.md**: Use `.specify/templates/tasks-template.md` as structure, fill with:
   - Correct feature name from plan.md
   - Phase 1: i18n 部分
     - 如果 spec 中包含 i18n 相关内容，则单独作为一个任务作为阶段 1.
   - Phase 2: api 部分
     - 如果 spec 中包含 api 相关内容，则单独作为一个任务作为阶段 2. （如没 i18n 则为阶段 1.）
   - Phase 3: api mock server 部分
     - 如果包含 api 部分变更， 则必须需要包含该 phase。专门用于后端服务未实现之前，前端可以先基于 mock server 进行开发。
     - 需要有人工确认阶段，并且输出一份支持的 mock 的 api 文档，输入输出事例等
   - Phase 4: 组件/模块/hooks 的使用和封装部分（可以不止一个 phase）
     - 需要特别关注可以复用/独立的前端组件/模块
     - 即使需要复用原有的组件/模块/hooks，也需要单独作为一个任务进行 check。
     - 如果有多个 user sotry 中的组件/模块/hooks，都需要前置专门先实现。
     - 如果其中有组件过于复杂，可以单独作为一个 phase 来拆分实现。
     - 最后需要有人工确认阶段，将这次任务变更的组件/模块/hooks 单独整理一份文档供人检查。
       - 如果是独立组件，则需要提供一个 story book 或者新增一个 url 专门渲染组件，供人方便检查试用
         - 如果项目本身没有 story book，则可以使用新增一个 url 来渲染组件。
   - Phase 5: 集成阶段（可以不止一个 phase）
     - 根据 user sotry 来进行拆分阶段，每个 user story 单独作为一个 phase。
     - 在该阶段，只能使用前面已经完成的组件/模块/hooks/api/i18n 来进行业务流串联。
     - 在该阶段严格禁止实现任何新的组件/模块/hooks/api/i18n。
     - 最后需要有人工确认阶段，在进入这个阶段的时候需要提供一个可以预览的 url，和冒烟测试 case，供人检查确认。
   - Each phase includes: story goal(required), independent test criteria(optional), tests (if requested), implementation tasks
   - Final Phase: 全面 review 代码，确认没有遗漏的地方。并且检查代码是否符合规范。
   - All tasks must follow the strict checklist format (see Task Generation Rules below)

5. **Report**: Output path to generated tasks.md and summary:
   - Total task count
   - Task count per user story
   - Independent test criteria for each story

## Task Generation Rules

**CRITICAL**: Tasks MUST be organized by user story to enable independent implementation and testing.

**Tests are OPTIONAL**: 在实现 组件/模块/hooks/按照userstory集成 等部分时，需要在 phase 维度的最末尾设置人工卡点，这里会要求人工确认是否符合预期。只有人工确认之后才可以执行下一个 phase

**额外的测试环境 tasks** 在 组件/模块/hooks 的 phase 开发末尾，需要专门注意提供一个可以供人检查的测试环境。包括但不限于新增一个 url path / storybook 专门用于渲染组件/模块/hooks。

### Checklist Format (REQUIRED)

Every task MUST strictly follow this format:

```text
- [ ] [TaskID] [Story?] Description with file path
```

**Format Components**:

1. **Checkbox**: ALWAYS start with `- [ ]` (markdown checkbox)
2. **Task ID**: Sequential number (T001, T002, T003...) in execution order
4. **[Story] label**: REQUIRED for user story phase tasks only
   - Format: [US1], [US2], [US3], etc. (maps to user stories from spec.md)
   - Setup phase: NO story label
   - Foundational phase: NO story label  
   - User Story phases: MUST have story label
5. **Description**: Clear action with exact file path

**Examples**:

- ✅ CORRECT: `- [ ] T001 Create project structure per implementation plan`
- ✅ CORRECT: `- [ ] T005 [US1] Implement authentication middleware in src/middleware/auth.py`
- ✅ CORRECT: `- [ ] T012 [US1] Create User model in src/models/user.py`
- ✅ CORRECT: `- [ ] T014 [US1] Implement UserService in src/services/user_service.py`
- ❌ WRONG: `- [ ] Create User model` (missing ID and Story label)
- ❌ WRONG: `T001 [US1] Create model` (missing checkbox)
- ❌ WRONG: `- [ ] [US1] Create User model` (missing Task ID)
- ❌ WRONG: `- [ ] T001 [US1] Create model` (missing file path)

### Task Organization

1. **From User Stories (spec.md)** - PRIMARY ORGANIZATION:
   - Each user story (P1, P2, P3...) gets its own phase
   - Map all related components to their story:
     - Models needed for that story
     - Services needed for that story
     - Endpoints/UI needed for that story
     - If tests requested: Tests specific to that story
   - Mark story dependencies (most stories should be independent)

2. **From Contracts**:
   - Map each contract/endpoint → to the user story it serves
   - If tests requested: Each contract → contract test task before implementation in that story's phase

3. **From Data Model**:
   - Map each entity to the user story(ies) that need it
   - If entity serves multiple stories: Put in earliest story or Setup phase
   - Relationships → service layer tasks in appropriate story phase

### Phase Structure
- **Phase 1**: i18n 部分 （如有）
- **Phase 2**: api 部分 （如有）
- **Phase 3**: api mock server 部分 （如有 api 部分）
- **Phase 4**: 组件/模块/hooks 的使用和封装部分（可以不止一个 phase）
- **Phase 5**: 按照 user story 进行集成（可以不止一个 phase）
- **Final Phase**: Review & Lint
