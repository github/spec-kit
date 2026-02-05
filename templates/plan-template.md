# 实现计划：[功能名称]

**分支**: `[###-feature-name]` | **日期**: [DATE] | **规格**: [link]
**输入**: `/specs/[###-feature-name]/spec.md` 中的功能规格

**注意**: 此模板由 `/speckit.plan` 命令填充。有关执行工作流程，请参阅 `.specify/templates/commands/plan.md`。

## 摘要

[从功能规格中提取：主要需求 + 研究(research.md)中的技术方法]

## 技术上下文

<!--
  需要操作: 将此部分内容替换为项目的技术细节. 此处的结构以咨询性质呈现, 用于指导迭代过程.
-->

**语言/版本**: [例如: Python 3.11、Swift 5.9、Rust 1.75 或 NEEDS CLARIFICATION]
**主要依赖**: [例如: FastAPI、UIKit、LLVM 或 NEEDS CLARIFICATION]
**存储**: [如适用, 例如: PostgreSQL、CoreData、文件 或 N/A]
**测试**: [例如: pytest、XCTest、cargo test 或 NEEDS CLARIFICATION]
**目标平台**: [例如: Linux 服务器、iOS 15+、WASM 或 NEEDS CLARIFICATION]
**项目类型**: [单一/网页/移动 - 决定源代码结构]
**性能目标**: [领域特定, 例如: 1000 请求/秒、10k 行/秒、60 fps 或 NEEDS CLARIFICATION]
**约束条件**: [领域特定, 例如: <200ms p95、<100MB 内存、离线可用 或 NEEDS CLARIFICATION]
**规模/范围**: [领域特定, 例如: 10k 用户、1M 行代码、50 个屏幕 或 NEEDS CLARIFICATION]

## Constitution Check

*GATE: 必须在 阶段 0 研究前通过. 在 阶段 1 设计后重新检查.*

[根据 Constitution 文件确定Gates]

## 项目结构

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # 此文件 (/speckit.plan 命令输出)
├── research.md          # 阶段 0 输出 (/speckit.plan 命令)
├── data-model.md        # 阶段 1 输出 (/speckit.plan 命令)
├── quickstart.md        # 阶段 1 输出 (/speckit.plan 命令)
├── contracts/           # 阶段 1 输出 (/speckit.plan 命令)
└── tasks.md             # 阶段 2 输出 (/speckit.tasks 命令 - 非 /speckit.plan 创建)
```

### 源代码(仓库根目录)
<!--
  操作要求: 将下面的占位符树结构替换为此功能的具体布局. 删除未使用的选项, 并使用真实路径(例如: apps/admin、packages/something)扩展所选结构.
  交付的计划不得包含选项标签.
-->

```text
# [如未使用请删除] 选项 1: 单项目(默认)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [如未使用请删除] 选项 2: Web 应用程序(检测到 "frontend" + "backend" 时)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [如未使用请删除] 选项 3: 移动端 + API(检测到 "iOS/Android" 时)
api/
└── [同上后端结构]

ios/ or android/
└── [平台特定结构: 功能模块, UI 流程, 平台测试]
```

**结构决策**: [Document the selected structure and reference the real
directories captured above]

## 复杂性跟踪

> **仅在 Constitution Check 存在必须解释的违规项时填写**

| 违规 | 为什么需要 | 拒绝更简单替代方案的原因 |
|-----------|------------|-------------------------------------|
| [例如: 第 4 个项目] | [当前需求] | [为什么 3 个项目不够] |
| [例如: 仓储模式] | [特定问题] | [为什么直接数据库访问不够] |
