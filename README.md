forked from [github/spec-kit](https://github.com/github/spec-kit)

## ⚡ Get Started

### 1. Install Specify CLI

Choose your preferred installation method:

#### Option 1: Persistent Installation (Recommended)

Install once and use everywhere:

```bash
uv tool install specify-cli --from git+https://github.com/ykg3211/x-spec-kit.git
```

Then use the tool directly:

```bash
specify init <PROJECT_NAME>
specify check
```

To upgrade specify run:

```bash
uv tool install specify-cli --force --from git+https://github.com/ykg3211/x-spec-kit.git
```

#### Option 2: One-time Usage

Run directly without installing:

```bash
uvx --from git+https://github.com/ykg3211/x-spec-kit.git specify init <PROJECT_NAME>
```

**Benefits of persistent installation:**

- Tool stays installed and available in PATH
- No need to create shell aliases
- Better tool management with `uv tool list`, `uv tool upgrade`, `uv tool uninstall`
- Cleaner shell configuration

## Init Project

To initialize a new Specify project, run:

```bash
specify init <PROJECT_NAME>
```

如果需要使用基础模板，添加 `--base` 参数：
带 `--base` 参数会从 [github/spec-kit](https://github.com/github/spec-kit) 初始化项目
如果不带则在本仓库初始化项目

```bash
specify init <PROJECT_NAME> --base
```

# 开发流程

clone 该仓库修改相应的 prompt 之后 push 到 main 分支
然后跟随一下路径执行 workflow 
![操作路径](https://lf3-static.bytednsdoc.com/obj/eden-cn/lnphrbf/speckit/Snipaste_2025-11-07_14-34-24.jpg)

随后重新使用 `specify init <PROJECT_NAME>` 初始化项目即可生效