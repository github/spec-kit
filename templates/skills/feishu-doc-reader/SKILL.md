---
name: feishu-doc-reader
description: 飞书云文档读取工具。当用户需要读取飞书云文档内容、获取飞书文档数据、分析飞书文档时使用。支持新版docx格式文档，自动提取文本、标题、列表、代码块等内容。
license: MIT
---

# 飞书云文档读取技能

## 技能用途

帮助用户通过飞书开放API读取飞书云文档内容。适用于以下场景：
- 用户需要读取飞书云文档的内容
- 用户需要提取飞书文档中的文本数据
- 用户需要分析飞书文档结构
- 用户需要将飞书文档内容用于其他处理
- 用户提供了飞书文档链接或文档token

## 核心工具脚本

项目中的飞书文档读取工具位于：`scripts\feishu_doc_reader.py`

## 前置准备

### 1. 创建飞书应用并获取凭证

在使用此技能前，需要创建飞书应用并配置权限：

**步骤 1: 创建应用**
1. 访问飞书开放平台：https://open.feishu.cn/app
2. 点击"创建自建应用"
3. 填写应用名称和描述
4. 创建成功后，记录 **App ID** 和 **App Secret**

**步骤 2: 配置应用权限（重要）**

需要在应用管理后台申请以下权限：

| 权限名称 | 权限标识 | 用途 |
|---------|---------|------|
| 查看、评论、编辑和管理云空间中所有文件 | drive:drive | 访问文档的基础权限 |
| 查看、评论和导出文档 | docx:document | 读取新版文档内容 |
| 查看、评论、编辑和管理文档 | docx:document:write | 完整文档操作权限（可选） |

**申请权限步骤：**
1. 在应用管理后台，进入"权限管理"
2. 搜索上述权限
3. 点击"申请权限"
4. 提交申请并等待管理员审批（如果需要）

**步骤 3: 授权文档访问**

对于非应用创建的文档，还需要文档所有者授权：

**方式一：使用 tenant_access_token（机器人方式）**
1. 在应用管理后台，开启"机器人"功能
2. 文档所有者打开要访问的文档
3. 点击右上角"..."→"更多"→"添加应用"
4. 搜索并添加你的应用

**方式二：使用 user_access_token（用户授权方式）**
1. 文档所有者打开文档
2. 点击右上角"分享"
3. 添加应用访问权限

### 2. 配置应用凭证

复制配置模板并填写凭证：

```powershell
# 复制配置模板
Copy-Item "config\config.json.template" -Destination "config\config.json"

# 编辑配置文件，填入你的 App ID 和 App Secret
notepad config\config.json
```

配置文件格式：
```json
{
  "app_id": "cli_a1b2c3d4e5f6g7h8",
  "app_secret": "abcdefghijklmnopqrstuvwxyz123456"
}
```

## 使用指南

### 1. 基本使用

**⚠️ 重要提示：**
- **禁止产生任何临时文件**：直接运行脚本让其输出到终端
- **禁止重定向到文件**：不要使用 `> file.txt` 或 `Out-File` 等操作
- **正确做法**：直接执行命令，脚本已处理好输出编码

```powershell
# 切换到scripts目录
cd .claude/skills/feishu-doc-reader/scripts

# ✅ 正确：直接读取文档内容（纯文本格式）
python feishu_doc_reader.py <doc_token>

# ✅ 正确：读取文档内容（JSON格式）
python feishu_doc_reader.py <doc_token> json

# ✅ 正确：直接使用URL
python feishu_doc_reader.py "https://example.feishu.cn/docx/xxxxx"

# ❌ 错误：禁止重定向到文件
# python feishu_doc_reader.py <doc_token> > temp.txt
# python feishu_doc_reader.py <doc_token> | Out-File result.txt
```

### 2. 如何获取文档token

文档token是文档URL中的标识符：

**新版文档（docx）URL格式：**
```
https://example.feishu.cn/docx/doxcnABCDEFGHIJKLMNOPQRST
                               ^^^^^^^^^^^^^^^^^^^^^^^^
                               这部分就是 doc_token
```

**示例：**
- URL: `https://bytedance.feishu.cn/docx/doxcnH1234567890abcdefg`
- Token: `doxcnH1234567890abcdefg`

### 3. 输出格式

#### 文本格式（默认）

提取文档的纯文本内容，自动识别并格式化：
- 标题（# ## ###）
- 段落文本
- 有序列表
- 无序列表
- 代码块

```powershell
python feishu_doc_reader.py doxcnABCDEFGHIJKLMN
```

输出示例：
```
# 文档标题

这是段落内容...

## 二级标题

  - 列表项1
  - 列表项2

```python
# 代码示例
print("Hello")
```
```

#### JSON格式

获取完整的文档结构数据：

```powershell
python feishu_doc_reader.py doxcnABCDEFGHIJKLMN json
```

返回文档块的完整JSON结构，包含所有元数据。

### 4. 常用场景

#### 场景1：读取需求文档

```powershell
# 用户说："帮我读取这个飞书文档的内容：https://example.feishu.cn/docx/doxcnXXXXX"
# 提取token并读取
python feishu_doc_reader.py doxcnXXXXX
```

#### 场景2：提取文档内容用于分析

```powershell
# 读取文档并保存到文件
python feishu_doc_reader.py doxcnXXXXX > document_content.txt
```

#### 场景3：获取文档结构数据

```powershell
# 获取JSON格式数据用于程序处理
python feishu_doc_reader.py doxcnXXXXX json > document_data.json
```

## 工作流程

当用户请求读取飞书文档时，按以下步骤执行：

### 步骤 1: 提取文档token

从用户提供的信息中提取doc_token：
- 如果用户提供URL，从URL中提取token（docx/后面的部分）
- 如果用户直接提供token，验证格式（通常以doxcn开头）

### 步骤 2: 验证配置

检查配置文件是否存在并正确配置：
```powershell
if (!(Test-Path "config\config.json")) {
    Write-Host "配置文件不存在，请先配置应用凭证"
}
```

### 步骤 3: 执行读取

```powershell
cd .specify/skills/feishu-doc-reader/scripts
python feishu_doc_reader.py <doc_token>
```

### 步骤 4: 处理结果

- 如果成功，展示文档内容
- 如果失败，根据错误信息指导用户：
  - 权限不足：提示配置权限或添加应用到文档
  - 鉴权失败：检查app_id和app_secret配置
  - 文档不存在：检查token是否正确

## 支持的文档类型

### 当前支持

✅ **新版飞书文档（docx）**
- 文本段落
- 各级标题（H1-H9）
- 有序列表
- 无序列表
- 代码块
- 待办事项（TODO）

### 计划支持

⏳ **后续可扩展支持：**
- 表格内容
- 图片信息
- 附件链接
- 嵌入式内容
- 旧版文档（doc格式）
- 飞书电子表格（sheet）
- 飞书多维表格（bitable）

## 权限说明

### 必需权限

| 权限 | 说明 | 必需性 |
|------|------|--------|
| drive:drive | 云空间文件访问 | ✓ 必需 |
| docx:document | 文档读取 | ✓ 必需 |

### 可选权限

| 权限 | 说明 | 使用场景 |
|------|------|----------|
| docx:document:write | 文档编辑 | 如果需要修改文档 |
| sheets:spreadsheet | 电子表格访问 | 如果需要读取表格 |
| bitable:app | 多维表格访问 | 如果需要读取多维表格 |

### 鉴权方式

当前实现使用 **tenant_access_token**（应用身份）：
- 优点：简单易用，适合自动化场景
- 限制：需要将应用添加到文档才能访问非自建文档

**如需访问用户个人文档，可升级为 user_access_token 方式**

## 故障排查

### 常见错误

#### 1. 鉴权失败（code: 99991663）

```
✗ 鉴权失败: tenant token invalid
```

**原因与解决：**
- App ID 或 App Secret 错误 → 检查配置文件
- 应用被停用 → 在开放平台检查应用状态
- 网络连接问题 → 检查网络访问

#### 2. 权限不足（code: 99991672）

```
✗ 获取文档内容失败: permission denied
```

**原因与解决：**
- 缺少必需权限 → 在应用管理后台申请权限
- 未授权文档访问 → 将应用添加到文档（见"授权文档访问"）
- 文档所有者未授权 → 联系文档所有者授权

#### 3. 文档不存在（code: 99991404）

```
✗ 获取文档内容失败: document not found
```

**原因与解决：**
- Token错误 → 检查从URL提取的token是否正确
- 文档已删除 → 确认文档是否还存在
- 文档类型不匹配 → 确认是新版文档（docx格式）

#### 4. 配置文件不存在

```
✗ 配置文件不存在，请先创建 config/config.json 文件
```

**解决：**
```powershell
Copy-Item "config\config.json.template" -Destination "config\config.json"
notepad config\config.json
# 填入你的 app_id 和 app_secret
```

### 调试技巧

#### 检查应用状态

```powershell
# 访问开放平台查看应用信息
# https://open.feishu.cn/app
```

#### 测试鉴权

```powershell
# 单独测试是否能获取 token
python -c "from feishu_doc_reader import FeishuDocReader; import json; config = json.load(open('../config/config.json')); reader = FeishuDocReader(config['app_id'], config['app_secret']); print('Success' if reader.get_tenant_access_token() else 'Failed')"
```

#### 验证权限

1. 登录开放平台：https://open.feishu.cn/app
2. 选择你的应用
3. 进入"权限管理"
4. 检查所需权限的状态（已启用/待审批/未申请）

## 安全注意事项

⚠️ **重要提醒**：

1. **保护应用凭证**
   - 不要将 config.json 提交到版本控制
   - App Secret 应妥善保管，不要泄露
   - 定期更换 App Secret

2. **权限最小化原则**
   - 只申请必需的权限
   - 不要申请超出需求的权限范围

3. **数据安全**
   - 读取的文档内容可能包含敏感信息
   - 注意数据存储和传输安全
   - 遵守公司数据安全规范

4. **访问控制**
   - 应用只能访问已授权的文档
   - 文档所有者可随时撤销应用权限

## 扩展功能

### 计划中的功能

- [ ] 支持批量读取多个文档
- [ ] 支持读取文档评论
- [ ] 支持导出为Markdown格式
- [ ] 支持读取文档变更历史
- [ ] 支持读取文档元信息（创建者、修改时间等）
- [ ] 缓存机制以提升性能

### 如何扩展

如需添加新功能，可以：
1. 参考飞书开放平台文档：https://open.feishu.cn/document/server-docs/docs/docs-overview
2. 在 `feishu_doc_reader.py` 中添加新的方法
3. 更新此SKILL.md文档说明

## 相关资源

### 官方文档
- [飞书开放平台](https://open.feishu.cn/)
- [云文档概述](https://open.feishu.cn/document/server-docs/docs/docs-overview)
- [新版文档API](https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/overview)
- [鉴权指南](https://open.feishu.cn/document/server-docs/authentication-management/access-token/tenant_access_token_internal)

### 常见问题
- [权限配置FAQ](https://open.feishu.cn/document/server-docs/docs/permission/faq)
- [文档API FAQ](https://open.feishu.cn/document/server-docs/docs/faq)

## 许可证

MIT License
