---
description: 执行实现计划, 处理并执行 tasks.md 中定义的所有任务.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## 用户输入

```text
$ARGUMENTS
```

You **MUST** consider 用户输入 (如果不为空) 前的所有内容.

## 实现计划大纲

1. 从仓库根目录运行 `{SCRIPT}` 并解析 FEATURE_DIR 和 AVAILABLE_DOCS 列表。所有路径必须为绝对路径。例如，对于像 "I'm Groot" 这样的参数中的单引号，使用转义语法：例如 'I'\''m Groot'（或如果可能，使用双引号："I'm Groot"）。

2. **Check checklists 状态** (如果 FEATURE_DIR/checklists/ 存在):
   - 扫描 checklists/ 目录中的所有 checklist 文件
   - 对于每个 checklist，计算：
     - 总项目数：所有匹配 `- [ ]` 或 `- [X]` 或 `- [x]` 的行
     - 已完成项目数：匹配 `- [X]` 或 `- [x]` 的行
     - 未完成项目数：匹配 `- [ ]` 的行
   - 创建状态表格：

     ```text
     | Checklist | Total | Completed | Incomplete | Status |
     |-----------|-------|-----------|------------|--------|
     | ux.md     | 12    | 12        | 0          | ✓ PASS |
     | test.md   | 8     | 5         | 3          | ✗ FAIL |
     | security.md | 6   | 6         | 0          | ✓ PASS |
     ```

   - 计算总体状态：
     - **PASS**: 所有 checklist 都有 0 个未完成项目
     - **FAIL**: 一个或多个 checklist 有未完成项目

   - **如果有 checklist 未完成**:
     - 显示未完成项目数的表格
     - **STOP** 并询问："某些 checklist 未完成。您是否仍要继续实现？(是/否)"
     - 在继续之前等待用户响应
     - 如果用户说 "no" 或 "wait" 或 "stop"，则停止执行
     - 如果用户说 "yes" 或 "proceed" 或 "continue"，则继续执行步骤 3

   - **如果所有 checklist 都已完成**:
     - 显示所有已通过 checklist 的表格
     - 自动继续执行步骤 3

3. **加载并分析实现上下文**:
   - **REQUIRED**: 读取 tasks.md 以获取完整任务列表和执行计划
   - **REQUIRED**: 读取 plan.md 以获取技术栈、架构和文件结构
   - **IF EXISTS**: 读取 data-model.md 以获取实体和关系
   - **IF EXISTS**: 读取 contracts/ 以获取 API 规范和测试要求
   - **IF EXISTS**: 读取 research.md 以获取技术决策和约束
   - **IF EXISTS**: Read quickstart.md for integration scenarios

4. **项目设置验证**:
   - **REQUIRED**: 根据实际项目设置创建/验证忽略文件:

   **检测和创建逻辑**:
   - 检查以下命令是否成功以确定存储库是否为 git 存储库（如果成功，则创建/验证 .gitignore）：

     ```sh
     git rev-parse --git-dir 2>/dev/null
     ```

   - Check if Dockerfile* exists or Docker in plan.md → create/verify .dockerignore
   - Check if .eslintrc* exists → create/verify .eslintignore
   - Check if eslint.config.* exists → ensure the config's `ignores` entries cover required patterns
   - Check if .prettierrc* exists → create/verify .prettierignore
   - Check if .npmrc or package.json exists → create/verify .npmignore (if publishing)
   - Check if terraform files (*.tf) exist → create/verify .terraformignore
   - Check if .helmignore needed (helm charts present) → create/verify .helmignore

   **如果ignores文件已存在**: 验证它包含必要的模式，仅追加缺失的关键模式
   **如果ignores文件缺失**: 根据检测到的技术创建完整的模式集

   **按技术的通用模式**(来自 plan.md 技术栈):
   - **Node.js/JavaScript/TypeScript**: `node_modules/`, `dist/`, `build/`, `*.log`, `.env*`
   - **Python**: `__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `dist/`, `*.egg-info/`
   - **Java**: `target/`, `*.class`, `*.jar`, `.gradle/`, `build/`
   - **C#/.NET**: `bin/`, `obj/`, `*.user`, `*.suo`, `packages/`
   - **Go**: `*.exe`, `*.test`, `vendor/`, `*.out`
   - **Ruby**: `.bundle/`, `log/`, `tmp/`, `*.gem`, `vendor/bundle/`
   - **PHP**: `vendor/`, `*.log`, `*.cache`, `*.env`
   - **Rust**: `target/`, `debug/`, `release/`, `*.rs.bk`, `*.rlib`, `*.prof*`, `.idea/`, `*.log`, `.env*`
   - **Kotlin**: `build/`, `out/`, `.gradle/`, `.idea/`, `*.class`, `*.jar`, `*.iml`, `*.log`, `.env*`
   - **C++**: `build/`, `bin/`, `obj/`, `out/`, `*.o`, `*.so`, `*.a`, `*.exe`, `*.dll`, `.idea/`, `*.log`, `.env*`
   - **C**: `build/`, `bin/`, `obj/`, `out/`, `*.o`, `*.a`, `*.so`, `*.exe`, `Makefile`, `config.log`, `.idea/`, `*.log`, `.env*`
   - **Swift**: `.build/`, `DerivedData/`, `*.swiftpm/`, `Packages/`
   - **R**: `.Rproj.user/`, `.Rhistory`, `.RData`, `.Ruserdata`, `*.Rproj`, `packrat/`, `renv/`
   - **Universal**: `.DS_Store`, `Thumbs.db`, `*.tmp`, `*.swp`, `.vscode/`, `.idea/`

   **Tool-Specific Patterns**:
   - **Docker**: `node_modules/`, `.git/`, `Dockerfile*`, `.dockerignore`, `*.log*`, `.env*`, `coverage/`
   - **ESLint**: `node_modules/`, `dist/`, `build/`, `coverage/`, `*.min.js`
   - **Prettier**: `node_modules/`, `dist/`, `build/`, `coverage/`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`
   - **Terraform**: `.terraform/`, `*.tfstate*`, `*.tfvars`, `.terraform.lock.hcl`
   - **Kubernetes/k8s**: `*.secret.yaml`, `secrets/`, `.kube/`, `kubeconfig*`, `*.key`, `*.crt`

5. 解析 tasks.md 结构并提取:
   - **任务阶段**: 设置、测试、核心、集成、完善
   - **任务依赖**: 顺序执行规则 vs 并行执行规则
   - **任务详情**: ID、描述、文件路径、并行标记 [P]
   - **执行流程**: 顺序和依赖要求

6. 按照任务计划执行实施:
   - **按阶段执行**: 完成每个阶段后再移动到下一个阶段
   - **尊重依赖关系**: 按顺序执行顺序任务, 并行任务 [P] 可以同时运行
   - **遵循 TDD 方法**: 在实现任务之前执行测试任务
   - **基于文件的协调**: 影响相同文件的任务必须按顺序运行
   - **验证检查点**: 在继续之前验证每个阶段的完成

7. 实施执行规则:
   - **先设置**: 初始化项目结构、依赖项、配置
   - **先测试**: 如果需要为合约、实体和集成场景编写测试
   - **核心开发**: 实现模型、服务、CLI 命令、端点
   - **集成工作**: 数据库连接、中间件、日志记录、外部服务
   - **完善和验证**: 单元测试、性能优化、文档

8. 进度跟踪和错误处理:
   - 每个任务完成后报告进度
   - 如果任何非并行任务失败, 则立即停止执行
   - 对于并行任务 [P], 继续执行成功的任务, 报告失败的任务
   - 提供清晰的错误消息, 包含上下文信息, 方便调试
   - 如果实施无法继续, 则建议下一步操作
   - **IMPORTANT** 完成任务后, 确保在 tasks 文件中标记任务为 [X]

9. 完成验证:
   - 验证所有必要的任务都已完成
   - 检查已实现的功能是否与原始规格匹配
   - 验证测试是否通过, 覆盖率是否符合要求
   - 确认实施遵循技术计划
   - 报告最终状态, 包含已完成工作的摘要

Note: 此命令假设 tasks.md 中存在完整的任务分解。如果任务不完整或缺失，请先运行 `/speckit.tasks` 以重新生成任务列表。
