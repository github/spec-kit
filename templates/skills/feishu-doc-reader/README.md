# 飞书云文档读取技能

通过飞书开放API读取飞书云文档内容的AI技能。

## 快速开始

### ⚠️ 使用注意事项

**禁止产生临时文件：**
- ✅ 直接运行脚本，输出会自动显示在终端
- ❌ 不要创建临时文件来中转输出
- ❌ 不要使用 `>` 或 `Out-File` 重定向
- ❌ 不要创建 temp.txt、result.txt 等临时文件

脚本已经正确处理了UTF-8编码，可以直接在Windows终端显示中文。

### 1. 配置应用凭证

```bash
# 复制配置模板
cp config/config.json.template config/config.json

# 编辑配置文件，填入你的飞书应用凭证
vim config/config.json
```

配置文件格式：
```json
{
  "app_id": "cli_xxxxxxxxxxxxxxxx",
  "app_secret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

⚠️ **安全提示**：
- 不要将 `config/config.json` 提交到版本控制系统
- 确保配置文件权限设置正确，仅当前用户可读
- 在生产环境中考虑使用环境变量或密钥管理服务

### 2. 创建飞书应用

1. 访问 [飞书开放平台](https://open.feishu.cn/app)
2. 创建自建应用
3. 获取 App ID 和 App Secret
4. 申请以下权限：
   - `drive:drive` - 查看云空间文件
   - `docx:document` - 查看文档内容

### 3. 使用示例

```powershell
cd scripts

# ✅ 读取文档（文本格式）- 直接执行
python feishu_doc_reader.py doxcnABCDEFGHIJKLMN

# ✅ 读取文档（JSON格式）- 直接执行
python feishu_doc_reader.py doxcnABCDEFGHIJKLMN json

# ✅ 使用完整URL - 直接执行
python feishu_doc_reader.py "https://ruijie.feishu.cn/docx/xxxxx"

# ❌ 错误示例 - 禁止这样做
# python feishu_doc_reader.py xxx > temp.txt
# python feishu_doc_reader.py xxx | Out-File result.txt
```

## 功能特性

- ✅ 读取新版飞书文档（docx格式）
- ✅ 自动提取文本、标题、列表、代码块
- ✅ 支持文本和JSON两种输出格式
- ✅ 自动处理分页，获取完整文档
- ✅ 友好的错误提示和故障排查

## 文档结构

```
feishu-doc-reader/
├── SKILL.md                    # 技能详细说明文档
├── README.md                   # 本文件
├── LICENSE.txt                 # MIT许可证
├── config/
│   ├── config.json.template    # 配置模板
│   └── config.json             # 实际配置（需自行创建）
└── scripts/
    └── feishu_doc_reader.py    # 核心读取脚本
```

## 依赖安装

```bash
pip install requests
```

## 权限说明

需要在飞书应用中申请以下权限：

| 权限 | 说明 | 必需性 |
|------|------|--------|
| drive:drive | 云空间文件访问 | ✓ 必需 |
| docx:document | 文档读取 | ✓ 必需 |

## 授权文档访问

对于非应用创建的文档，需要文档所有者授权：

1. 在应用中开启"机器人"功能
2. 文档所有者打开文档
3. 点击右上角"..."→"更多"→"添加应用"
4. 选择你的应用

## 常见问题

### Q: 如何获取文档token？

A: 文档token在URL中：
```
https://example.feishu.cn/docx/doxcnABCDEFGHIJKLMN
                               ^^^^^^^^^^^^^^^^^^^
                               这部分就是token
```

### Q: 提示权限不足怎么办？

A: 
1. 检查应用是否申请了必需权限
2. 确认文档是否已添加应用
3. 联系文档所有者授权

### Q: 支持哪些文档类型？

A: 当前支持新版飞书文档（docx格式）。旧版文档、电子表格、多维表格的支持计划中。

## 更多信息

详细使用说明请查看 [SKILL.md](SKILL.md)

## 许可证

MIT License
