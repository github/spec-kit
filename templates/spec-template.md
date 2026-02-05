# 功能规范: [功能名称]

**功能分支**: `[###-feature-name]`  
**创建日期**: [DATE]  
**状态**: Draft  
**输入**: 用户描述: "$ARGUMENTS"

## 用户场景 & 测试 *(必须)*

<!--
  重要提示: 用户故事应按用户旅程的重要性进行优先排序.
  每个用户故事/旅程必须是独立可测试的 - 这意味着如果您仅实现其中之一,
  您仍应具有可行的 MVP (最小可行产品) 来交付价值.
  
  为每个故事分配优先级 (P1, P2, P3 等.)，其中 P1 是最关键的.
  考虑每个故事都是功能的独立切片, 可以:
  - 独立开发
  - 独立测试
  - 独立部署
  - 独立演示给用户
-->

### 用户故事 1 - [简要标题] (优先级: P1)

[用通俗语言描述这个用户故事]

**为什么这个优先级**: [解释价值和为什么它有这个优先级水平]

**独立测试**: [描述如何独立测试 - 例如, "可以通过 [特定操作] 完全测试, 并交付 [特定价值]"]

**验收场景**:

1. **给定** [初始状态], **当** [操作], **然后** [预期结果]
2. **给定** [初始状态], **当** [操作], **然后** [预期结果]

---

### 用户故事 2 - [简要标题] (优先级: P2)

[用通俗语言描述这个用户故事]

**为什么这个优先级**: [解释价值和为什么它有这个优先级水平]

**独立测试**: [描述如何独立测试 - 例如, "可以通过 [特定操作] 完全测试, 并交付 [特定价值]"]

**验收场景**:

1. **给定** [初始状态], **当** [操作], **然后** [预期结果]

---

### 用户故事 3 - [简要标题] (优先级: P3)

[用通俗语言描述这个用户故事]

**为什么这个优先级**: [解释价值和为什么它有这个优先级水平]

**独立测试**: [描述如何独立测试 - 例如, "可以通过 [特定操作] 完全测试, 并交付 [特定价值]"]

**验收场景**:

1. **给定** [初始状态], **当** [操作], **然后** [预期结果]

---

[根据需要添加更多用户故事, 每个都分配优先级]

### 边界情况

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right edge cases.
-->

- 当 [边界条件] 时, 系统应 [预期行为]
- 当 [错误场景] 时, 系统应 [预期行为]

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: 系统必须 [具体能力, 例如: "允许用户创建账户"]
- **FR-002**: 系统必须 [具体能力, 例如: "验证电子邮件地址"]
- **FR-003**: 用户必须能够 [关键交互, 例如: "重置密码"]
- **FR-004**: 系统必须 [数据需求, 例如: "持久化用户偏好设置"]
- **FR-005**: 系统必须 [行为, 例如: "记录所有安全事件"]

*示例: 标记不清晰的需求:*

- **FR-006**: 系统必须通过 [NEEDS CLARIFICATION: auth method not specified - email/password, SSO, OAuth?] 认证用户
- **FR-007**: 系统必须保留用户数据 for [NEEDS CLARIFICATION: retention period not specified]  

### 关键实体 *(如果功能涉及数据则包含)*

- **[Entity 1]**: [What it represents, key attributes without implementation]
- **[Entity 2]**: [What it represents, relationships to other entities]

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### 可测量指标

- **SC-001**: [可测量指标, 例如: "用户可以在2分钟内完成账户创建"]
- **SC-002**: [可测量指标, 例如: "系统在1000个并发用户下无降级"]
- **SC-003**: [用户满意度指标, 例如: "90%的用户首次尝试成功完成主要任务"]
- **SC-004**: [业务指标, 例如: "将[X]相关的支持工单减少50%"]
