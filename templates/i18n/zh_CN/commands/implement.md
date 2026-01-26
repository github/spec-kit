---
description: 通过处理和执行 tasks.md 中定义的所有任务来执行实施计划
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## 用户输入

```text
$ARGUMENTS
```

在继续之前，您**必须**考虑用户输入（如果不为空）。

## 流程概要

1. 从仓库根目录运行 `{SCRIPT}` 并解析 FEATURE_DIR 和 AVAILABLE_DOCS 列表。所有路径必须是绝对路径。对于参数中的单引号，如"I'm Groot"，使用转义语法：例如 'I'\''m Groot'（或如果可能使用双引号："I'm Groot"）。

2. **检查检查清单状态**（如果存在 FEATURE_DIR/checklists/）:
   - 扫描 checklists/ 目录中的所有检查清单文件
   - 对于每个检查清单，计数:
     - 总项目: 匹配 `- [ ]` 或 `- [X]` 或 `- [x]` 的所有行
     - 完成项目: 匹配 `- [X]` 或 `- [x]` 的行
     - 未完成项目: 匹配 `- [ ]` 的行
   - 创建状态表:

     ```text
     | 检查清单 | 总计 | 已完成 | 未完成 | 状态 |
     |---------|------|--------|--------|------|
     | ux.md   | 12   | 12     | 0      | ✓ 通过 |
     | test.md | 8    | 5      | 3      | ✗ 失败 |
     | security.md | 6 | 6    | 0      | ✓ 通过 |
     ```

   - 计算总体状态:
     - **通过**: 所有检查清单都有0个未完成项目
     - **失败**: 一个或多个检查清单有未完成项目

   - **如果任何检查清单未完成**:
     - 显示带有未完成项目计数的表
     - **停止**并询问: "某些检查清单未完成。您是否仍要继续实施？（是/否）"
     - 在继续之前等待用户响应
     - 如果用户说"否"、"等待"或"停止"，则停止执行
     - 如果用户说"是"、"继续"或"proceed"，则继续到步骤3

   - **如果所有检查清单都完成**:
     - 显示表格显示所有检查清单通过
     - 自动继续到步骤3

3. 加载并分析实施上下文:
   - **必需**: 读取 tasks.md 以获取完整的任务列表和执行计划
   - **必需**: 读取 plan.md 以获取技术栈、架构和文件结构
   - **如果存在**: 读取 data-model.md 以获取实体和关系
   - **如果存在**: 读取 contracts/ 以获取API规格和测试要求
   - **如果存在**: 读取 research.md 以获取技术决策和约束
   - **如果存在**: 读取 quickstart.md 以获取集成场景

4. **项目设置验证**:
   - **必需**: 根据实际项目设置创建/验证忽略文件:

   **检测和创建逻辑**:
   - 检查以下命令是否成功以确定仓库是否为git仓库（如果是则创建/验证 .gitignore）:

     ```sh
     git rev-parse --git-dir 2>/dev/null
     ```

   - 检查是否存在 Dockerfile* 或 plan.md 中有Docker → 创建/验证 .dockerignore
   - 检查是否存在 .eslintrc* → 创建/验证 .eslintignore
   - 检查是否存在 eslint.config.* → 确保配置的 `ignores` 条目覆盖所需模式
   - 检查是否存在 .prettierrc* → 创建/验证 .prettierignore
   - 检查是否存在 .npmrc 或 package.json → 创建/验证 .npmignore（如果发布）
   - 检查是否存在 terraform 文件（*.tf）→ 创建/验证 .terraformignore
   - 检查是否需要 .helmignore（存在 helm charts）→ 创建/验证 .helmignore

   **如果忽略文件已存在**: 验证它包含必要的模式，仅追加缺少的关键模式
   **如果忽略文件缺失**: 使用检测到的技术的完整模式集创建

   **按技术的常见模式**（来自 plan.md 技术栈）:
   - **Node.js/JavaScript/TypeScript**: `node_modules/`、`dist/`、`build/`、`*.log`、`.env*`
   - **Python**: `__pycache__/`、`*.pyc`、`.venv/`、`venv/`、`dist/`、`*.egg-info/`
   - **Java**: `target/`、`*.class`、`*.jar`、`.gradle/`、`build/`
   - **C#/.NET**: `bin/`、`obj/`、`*.user`、`*.suo`、`packages/`
   - **Go**: `*.exe`、`*.test`、`vendor/`、`*.out`
   - **Ruby**: `.bundle/`、`log/`、`tmp/`、`*.gem`、`vendor/bundle/`
   - **PHP**: `vendor/`、`*.log`、`*.cache`、`*.env`
   - **Rust**: `target/`、`debug/`、`release/`、`*.rs.bk`、`*.rlib`、`*.prof*`、`.idea/`、`*.log`、`.env*`
   - **Kotlin**: `build/`、`out/`、`.gradle/`、`.idea/`、`*.class`、`*.jar`、`*.iml`、`*.log`、`.env*`
   - **C++**: `build/`、`bin/`、`obj/`、`out/`、`*.o`、`*.so`、`*.a`、`*.exe`、`*.dll`、`.idea/`、`*.log`、`.env*`
   - **C**: `build/`、`bin/`、`obj/`、`out/`、`*.o`、`*.a`、`*.so`、`*.exe`、`Makefile`、`config.log`、`.idea/`、`*.log`、`.env*`
   - **Swift**: `.build/`、`DerivedData/`、`*.swiftpm/`、`Packages/`
   - **R**: `.Rproj.user/`、`.Rhistory`、`.RData`、`.Ruserdata`、`*.Rproj`、`packrat/`、`renv/`
   - **通用**: `.DS_Store`、`Thumbs.db`、`*.tmp`、`*.swp`、`.vscode/`、`.idea/`

   **工具特定模式**:
   - **Docker**: `node_modules/`、`.git/`、`Dockerfile*`、`.dockerignore`、`*.log*`、`.env*`、`coverage/`
   - **ESLint**: `node_modules/`、`dist/`、`build/`、`coverage/`、`*.min.js`
   - **Prettier**: `node_modules/`、`dist/`、`build/`、`coverage/`、`package-lock.json`、`yarn.lock`、`pnpm-lock.yaml`
   - **Terraform**: `.terraform/`、`*.tfstate*`、`*.tfvars`、`.terraform.lock.hcl`
   - **Kubernetes/k8s**: `*.secret.yaml`、`secrets/`、`.kube/`、`kubeconfig*`、`*.key`、`*.crt`

5. 解析 tasks.md 结构并提取:
   - **任务阶段**: 设置、测试、核心、集成、优化
   - **任务依赖关系**: 顺序与并行执行规则
   - **任务详情**: ID、描述、文件路径、并行标记 [P]
   - **执行流程**: 顺序和依赖关系要求

6. 按照任务计划执行实施:
   - **逐阶段执行**: 完成每个阶段后再进入下一个
   - **尊重依赖关系**: 按顺序运行顺序任务，并行任务 [P] 可以一起运行  
   - **遵循TDD方法**: 在相应的实施任务之前执行测试任务
   - **基于文件的协调**: 影响相同文件的任务必须按顺序运行
   - **验证检查点**: 在继续之前验证每个阶段的完成

7. 实施执行规则:
   - **首先设置**: 初始化项目结构、依赖关系、配置
   - **代码之前的测试**: 如果需要为契约、实体和集成场景编写测试
   - **核心开发**: 实施模型、服务、CLI命令、端点
   - **集成工作**: 数据库连接、中间件、日志记录、外部服务
   - **优化和验证**: 单元测试、性能优化、文档

8. 进度跟踪和错误处理:
   - 在每个完成的任务后报告进度
   - 如果任何非并行任务失败则停止执行
   - 对于并行任务 [P]，继续执行成功的任务，报告失败的任务
   - 提供带有调试上下文的清晰错误消息
   - 如果实施无法继续，建议下一步
   - **重要** 对于完成的任务，确保在任务文件中将任务标记为 [X]

9. 完成验证:
   - 验证所有必需的任务已完成
   - 检查实施的特性是否符合原始规格
   - 验证测试通过并且覆盖率符合要求
   - 确认实施遵循技术计划
   - 报告最终状态和完成工作的摘要

注意: 此命令假定 tasks.md 中存在完整的任务分解。如果任务不完整或缺失，建议首先运行 `/speckit.tasks` 重新生成任务列表。
