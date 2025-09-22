# Story Blueprint: [FEATURE TITLE]

**Story Branch**: `[###-story-fragment]`  
**Created**: [DATE]  
**Status**: Draft  
**Input**: Story brief: "$ARGUMENTS"

## Execution Flow (story_main)
```
1. 读取故事简述 → 若为空：ERROR "没有提供故事描述"
2. 提炼目标：主题、受众、情绪、类型
3. 解析 Canon：角色、世界观、冲突、悬念
4. 记录 Story Kit 的理解清单
   → 对每一项与原描述的差异提出问题
5. 标注所有不确定性为 [OPEN QUESTION: 具体疑问]
6. 填充下列章节
7. 运行 Review Checklist，若存在未解决问题 → WARN
8. 输出 Blueprint，待作者确认后进入 /plan
```

---

## 📜 作者意图 & 读者承诺 *(必填)*
- **故事一句话概述**： [LOG_LINE]
- **核心主题**： [THEMES]
- **主要情绪/体验**： [MOOD]
- **目标读者 & 年龄层**： [AUDIENCE]
- **必达成果**： [SUCCESS_CRITERIA]

## 🧭 Story Kit 的理解清单 *(必填)*
1. [STORY_KIT_INTERPRETATION_1]
2. [STORY_KIT_INTERPRETATION_2]
3. [STORY_KIT_INTERPRETATION_3]

> 若作者描述与理解存在差异，标记为 `[OPEN QUESTION: ...]` 并在下一轮澄清。

## 🧩 Canon Foundations *(必填)*
- **时代 / 地理 / 文化背景**： [SETTING]
- **世界规则 / 魔法 / 科技**： [SYSTEM_RULES]
- **社会结构与冲突源**： [SOCIAL_DYNAMICS]
- **禁忌与限制**： [BOUNDARIES]
- **现实世界参考**： [INSPIRATIONS]

## 🧑‍🤝‍🧑 角色网络 *(必填)*
| 角色 | 原型/动机 | 想要 vs 需要 | 冲突与弧线 | 未知点 |
|------|-----------|--------------|-------------|--------|
| 主角 | [PROTAGONIST_ARCHETYPE] | [PROTAGONIST_WANT_NEED] | [PROTAGONIST_CONFLICT_ARC] | [PROTAGONIST_OPEN_QUESTION] |
| 对手 | [ANTAGONIST_ARCHETYPE] | [ANTAGONIST_WANT_NEED] | [ANTAGONIST_CONFLICT_ARC] | [ANTAGONIST_OPEN_QUESTION] |
| 关键配角 | [ALLY_ARCHETYPE] | [ALLY_WANT_NEED] | [ALLY_CONTRIBUTION] | [ALLY_OPEN_QUESTION] |
| 其他 | [SUPPORTING_ARCHETYPE] | [SUPPORTING_BEATS] | [SUPPORTING_CONFLICT] | [SUPPORTING_OPEN_QUESTION] |

## 🪜 情节架构 *(必填)*
- **结构模型**： [STRUCTURE] （三幕/起承转合/英雄之旅/原创等）
- **关键节点**：
  1. 序幕 → [BEAT1]
  2. 引发事件 → [BEAT2]
  3. 中点/逆转 → [BEAT3]
  4. 高潮 → [BEAT4]
  5. 结局余韵 → [BEAT5]
- **悬念与伏笔**：
  - [FORESHADOW_1]
  - [FORESHADOW_2]
  - [FORESHADOW_3]

## 🌌 未知与研究议题 *(必填)*
- [OPEN QUESTION: 角色背景尚未确定]
- [OPEN QUESTION: 世界规则待确认]
- [RESEARCH TASK: 需搜集的历史/科学/文化资料]

## 🎯 成功验收标准 *(必填)*
- [CRITERION_1]
- [CRITERION_2]
- [CRITERION_3]

---

## Review Checklist
- [ ] Story Kit 已列出自身理解并等待作者确认
- [ ] 所有不确定项已用 `[OPEN QUESTION]` 或 `[RESEARCH TASK]` 标记
- [ ] 没有直接写出创作实现细节（保持在故事层面）
- [ ] 情节结构与角色弧线一致，无矛盾
- [ ] 接下来所需的澄清与研究列表完整

## Execution Status
- [ ] Story brief parsed
- [ ] Intent map ready
- [ ] Canon foundations drafted
- [ ] Character web drafted
- [ ] Plot architecture drafted
- [ ] Unknowns tracked
- [ ] Review checklist passed
