#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer",
#     "rich",
#     "platformdirs",
#     "readchar",
#     "httpx",
# ]
# ///
"""
Specify CLI - 一个用于设置 Specify 项目的工具

使用方法:
    uvx specify-cli.py init <项目名称>
    uvx specify-cli.py init .
    uvx specify-cli.py init --here
    uvx specify-cli.py update

或者全局安装:
    uv tool install --from specify-cli.py specify-cli
    specify init <项目名称>
    specify init .
    specify init --here
    specify update
"""

# 导入所需的系统模块和第三方库
import os                           # 操作系统相关功能
import subprocess                   # 执行系统命令
import sys                          # 系统相关的参数和函数
import zipfile                      # 处理 ZIP 压缩文件
import tempfile                     # 创建临时文件和目录
import shutil                       # 高级文件操作（复制、移动等）
import shlex                        # 简单的 shell 词法分析器
import json                         # 处理 JSON 数据
from pathlib import Path            # 面向对象的文件系统路径处理
from typing import Optional, Tuple  # 类型提示支持

# 第三方库导入
import typer                        # 命令行界面构建工具
import httpx                        # HTTP 客户端库
from rich.console import Console    # 终端富文本输出
from rich.panel import Panel        # 终端面板显示组件
from rich.progress import Progress, SpinnerColumn, TextColumn  # 进度条组件
from rich.text import Text          # 文本格式化
from rich.live import Live          # 实时更新显示
from rich.align import Align        # 文本对齐
from rich.table import Table        # 表格显示
from rich.tree import Tree          # 树形结构显示
from typer.core import TyperGroup   # Typer 命令组基类

# 跨平台键盘输入支持
import readchar                     # 读取键盘输入字符
import ssl                          # SSL/TLS 加密支持
import truststore                   # 系统信任存储支持

# 创建 SSL 上下文并初始化 HTTP 客户端
ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
client = httpx.Client(verify=ssl_context)

def _github_token(cli_token: str | None = None) -> str | None:
    """
    获取 GitHub 访问令牌（CLI 参数优先）
    
    参数:
        cli_token: 通过命令行传入的 GitHub 令牌
        
    返回:
        str | None: 清理后的 GitHub 令牌，如果没有找到则返回 None
    """
    # 按照优先级获取 GitHub 令牌：
    # 1. 命令行参数传入的令牌
    # 2. 环境变量 GH_TOKEN
    # 3. 环境变量 GITHUB_TOKEN
    # 4. 如果都没有则返回 None
    return ((cli_token or os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN") or "").strip()) or None

def _github_auth_headers(cli_token: str | None = None) -> dict:
    """
    根据是否存在非空令牌返回授权头部字典
    
    参数:
        cli_token: 通过命令行传入的 GitHub 令牌
        
    返回:
        dict: 包含授权信息的字典，如果无令牌则返回空字典
    """
    # 获取 GitHub 令牌
    token = _github_token(cli_token)
    # 如果有令牌，则返回包含授权头的字典，否则返回空字典
    return {"Authorization": f"Bearer {token}"} if token else {}

# AI 助手配置字典
# 每个助手包含以下信息：
# - name: 助手的显示名称
# - folder: 助手在项目中的配置文件夹
# - install_url: 助手的安装链接（如果是基于 IDE 的则为 None）
# - requires_cli: 是否需要命令行工具
AGENT_CONFIG = {
    "copilot": {
        "name": "GitHub Copilot",           # 显示名称
        "folder": ".github/",               # 配置文件夹路径
        "install_url": None,                # IDE 插件形式，无需 CLI 工具检查
        "requires_cli": False,              # 不需要命令行工具
    },
    "claude": {
        "name": "Claude Code",              # 显示名称
        "folder": ".claude/",               # 配置文件夹路径
        "install_url": "https://docs.anthropic.com/en/docs/claude-code/setup",  # 安装链接
        "requires_cli": True,               # 需要命令行工具
    },
    "gemini": {
        "name": "Gemini CLI",               # 显示名称
        "folder": ".gemini/",               # 配置文件夹路径
        "install_url": "https://github.com/google-gemini/gemini-cli",  # 安装链接
        "requires_cli": True,               # 需要命令行工具
    },
    "cursor-agent": {
        "name": "Cursor",                   # 显示名称
        "folder": ".cursor/",               # 配置文件夹路径
        "install_url": None,                # IDE 插件形式
        "requires_cli": False,              # 不需要命令行工具
    },
    "qwen": {
        "name": "Qwen Code",                # 显示名称
        "folder": ".qwen/",                 # 配置文件夹路径
        "install_url": "https://github.com/QwenLM/qwen-code",  # 安装链接
        "requires_cli": True,               # 需要命令行工具
    },
    "opencode": {
        "name": "opencode",                 # 显示名称
        "folder": ".opencode/",             # 配置文件夹路径
        "install_url": "https://opencode.ai",  # 安装链接
        "requires_cli": True,               # 需要命令行工具
    },
    "codex": {
        "name": "Codex CLI",                # 显示名称
        "folder": ".codex/",                # 配置文件夹路径
        "install_url": "https://github.com/openai/codex",  # 安装链接
        "requires_cli": True,               # 需要命令行工具
    },
    "windsurf": {
        "name": "Windsurf",                 # 显示名称
        "folder": ".windsurf/",             # 配置文件夹路径
        "install_url": None,                # IDE 插件形式
        "requires_cli": False,              # 不需要命令行工具
    },
    "kilocode": {
        "name": "Kilo Code",                # 显示名称
        "folder": ".kilocode/",             # 配置文件夹路径
        "install_url": None,                # IDE 插件形式
        "requires_cli": False,              # 不需要命令行工具
    },
    "auggie": {
        "name": "Auggie CLI",               # 显示名称
        "folder": ".augment/",              # 配置文件夹路径
        "install_url": "https://docs.augmentcode.com/cli/setup-auggie/install-auggie-cli",  # 安装链接
        "requires_cli": True,               # 需要命令行工具
    },
    "codebuddy": {
        "name": "CodeBuddy",                # 显示名称
        "folder": ".codebuddy/",            # 配置文件夹路径
        "install_url": "https://www.codebuddy.ai/cli",  # 安装链接
        "requires_cli": True,               # 需要命令行工具
    },
    "roo": {
        "name": "Roo Code",                 # 显示名称
        "folder": ".roo/",                  # 配置文件夹路径
        "install_url": None,                # IDE 插件形式
        "requires_cli": False,              # 不需要命令行工具
    },
    "q": {
        "name": "Amazon Q Developer CLI",   # 显示名称
        "folder": ".amazonq/",              # 配置文件夹路径
        "install_url": "https://aws.amazon.com/developer/learning/q-developer-cli/",  # 安装链接
        "requires_cli": True,               # 需要命令行工具
    },
    "amp": {
        "name": "Amp",                      # 显示名称
        "folder": ".agents/",               # 配置文件夹路径
        "install_url": "https://ampcode.com/manual#install",  # 安装链接
        "requires_cli": True,               # 需要命令行工具
    },
}

# 脚本类型选项配置
# key: 脚本文件扩展名
# value: 脚本类型的描述信息
SCRIPT_TYPE_CHOICES = {"sh": "POSIX Shell (bash/zsh)", "ps": "PowerShell"}

# Claude 本地路径配置
# 定义 Claude CLI 工具在本地系统中的安装路径
CLAUDE_LOCAL_PATH = Path.home() / ".claude" / "local" / "claude"

# ASCII 艺术字 banner，用于在终端显示工具名称
BANNER = """
███████╗██████╗ ███████╗ ██████╗██╗███████╗██╗   ██╗
██╔════╝██╔══██╗██╔════╝██╔════╝██║██╔════╝╚██╗ ██╔╝
███████╗██████╔╝█████╗  ██║     ██║█████╗   ╚████╔╝ 
╚════██║██╔═══╝ ██╔══╝  ██║     ██║██╔══╝    ╚██╔╝  
███████║██║     ███████╗╚██████╗██║██║        ██║   
╚══════╝╚═╝     ╚══════╝ ╚═════╝╚═╝╚═╝        ╚═╝   
"""

# 工具标语
TAGLINE = "GitHub Spec Kit - Spec-Driven Development Toolkit"

# 创建控制台对象，用于在终端输出富文本内容
console = Console()

class BannerGroup(TyperGroup):
    """
    自定义命令组类，在显示帮助信息前展示 banner
    
    继承自 TyperGroup，重写了 format_help 方法
    """

    def format_help(self, ctx, formatter):
        """
        格式化帮助信息，先显示 banner 再显示帮助内容
        
        参数:
            ctx: Typer 上下文对象
            formatter: 帮助信息格式化器
        """
        # 在帮助信息前显示 banner
        show_banner()
        # 调用父类方法显示原有帮助信息
        super().format_help(ctx, formatter)


# 创建 Typer 应用实例
app = typer.Typer(
    name="specify",                                    # 应用名称
    help="Setup tool for Specify spec-driven development projects.\n\nCommands:\n  init    Initialize a new project from template\n  update  Update project files from the latest template\n  check   Check that required tools are installed",  # 帮助信息
    add_completion=False,                              # 禁用自动补全
    invoke_without_command=True,                       # 允许不带子命令调用
    cls=BannerGroup,                                   # 使用自定义的 BannerGroup 类
)

def show_banner():
    """
    显示 ASCII 艺术字 banner
    """
    # 将 banner 文本按行分割
    banner_lines = BANNER.strip().split('\n')
    # 定义每行使用的颜色列表
    colors = ["bright_blue", "blue", "cyan", "bright_cyan", "white", "bright_white"]

    # 创建富文本对象
    styled_banner = Text()
    # 逐行为 banner 添加颜色样式
    for i, line in enumerate(banner_lines):
        color = colors[i % len(colors)]  # 循环使用颜色
        styled_banner.append(line + "\n", style=color)  # 添加带样式的行

    # 居中显示彩色 banner
    console.print(Align.center(styled_banner))
    # 居中显示工具标语，使用斜体和亮黄色
    console.print(Align.center(Text(TAGLINE, style="italic bright_yellow")))
    console.print()  # 打印空行

@app.callback()
def callback(ctx: typer.Context):
    """
    回调函数，当没有提供子命令时显示 banner
    
    参数:
        ctx: Typer 上下文对象
    """
    # 检查是否没有提供子命令且没有使用帮助选项
    if ctx.invoked_subcommand is None and "--help" not in sys.argv and "-h" not in sys.argv:
        show_banner()  # 显示 banner
        # 居中显示使用说明
        console.print(Align.center("[dim]Run 'specify --help' for usage information[/dim]"))
        console.print()  # 打印空行

def run_command(cmd: list[str], check_return: bool = True, capture: bool = False, shell: bool = False) -> Optional[str]:
    """
    执行 shell 命令并可选择捕获输出
    
    参数:
        cmd: 要执行的命令列表（例如 ['git', 'init']）
        check_return: 是否检查返回码，True 表示如果命令失败则抛出异常
        capture: 是否捕获命令输出，True 表示捕获 stdout 并返回
        shell: 是否通过 shell 执行命令
        
    返回:
        Optional[str]: 如果 capture=True 则返回命令输出，否则返回 None
        
    异常:
        subprocess.CalledProcessError: 当 check_return=True 且命令执行失败时抛出
    """
    try:
        # 根据是否需要捕获输出选择不同的执行方式
        if capture:
            # 捕获输出模式：执行命令并捕获标准输出和标准错误
            result = subprocess.run(cmd, check=check_return, capture_output=True, text=True, shell=shell)
            return result.stdout.strip()  # 返回去除首尾空白的标准输出
        else:
            # 非捕获模式：直接执行命令，不捕获输出
            subprocess.run(cmd, check=check_return, shell=shell)
            return None  # 不返回任何内容
    except subprocess.CalledProcessError as e:
        # 处理命令执行错误
        if check_return:
            # 如果设置了检查返回码，则打印错误信息并重新抛出异常
            console.print(f"[red]Error running command:[/red] {' '.join(cmd)}")
            console.print(f"[red]Exit code:[/red] {e.returncode}")
            if hasattr(e, 'stderr') and e.stderr:
                console.print(f"[red]Error output:[/red] {e.stderr}")
            raise  # 重新抛出异常
        return None  # 如果未设置检查返回码，则返回 None

def check_tool(tool: str, tracker: StepTracker = None) -> bool:
    """
    检查工具是否已安装，可选择更新跟踪器
    
    参数:
        tool: 要检查的工具名称
        tracker: 可选的步骤跟踪器，用于更新检查结果
        
    返回:
        bool: 如果找到工具返回 True，否则返回 False
    """
    # Claude CLI 的特殊处理
    # 在执行 `claude migrate-installer` 后，原始可执行文件会从 PATH 中移除
    # 并在 ~/.claude/local/claude 创建一个别名
    # 这个路径应该优先于 PATH 中的其他 claude 可执行文件
    if tool == "claude":
        # 检查 Claude 本地路径是否存在且是文件
        if CLAUDE_LOCAL_PATH.exists() and CLAUDE_LOCAL_PATH.is_file():
            if tracker:
                tracker.complete(tool, "available")  # 更新跟踪器状态为完成
            return True  # 工具可用

    # 使用 shutil.which 检查工具是否在系统 PATH 中
    found = shutil.which(tool) is not None

    # 如果提供了跟踪器，则更新其状态
    if tracker:
        if found:
            tracker.complete(tool, "available")  # 工具找到，标记为完成
        else:
            tracker.error(tool, "not found")     # 工具未找到，标记为错误

    return found  # 返回检查结果

def is_git_repo(path: Path = None) -> bool:
    """
    检查指定路径是否在 git 仓库内
    
    参数:
        path: 要检查的路径，默认为当前工作目录
        
    返回:
        bool: 如果路径在 git 仓库内返回 True，否则返回 False
    """
    # 如果未指定路径，则使用当前工作目录
    if path is None:
        path = Path.cwd()

    # 如果路径不是目录，则返回 False
    if not path.is_dir():
        return False

    try:
        # 使用 git 命令检查是否在工作树内
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            check=True,
            capture_output=True,
            cwd=path,  # 在指定路径下执行命令
        )
        return True  # 命令成功执行，说明在 git 仓库内
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False  # 命令执行失败或 git 未安装，说明不在 git 仓库内

def init_git_repo(project_path: Path, quiet: bool = False) -> Tuple[bool, Optional[str]]:
    """
    在指定路径初始化 git 仓库
    
    参数:
        project_path: 要初始化 git 仓库的路径
        quiet: 是否静默模式，True 表示不输出控制台信息（由跟踪器处理状态）
        
    返回:
        Tuple[bool, Optional[str]]: (成功标志, 错误信息)
        - 成功时返回 (True, None)
        - 失败时返回 (False, 错误信息)
    """
    try:
        # 保存当前工作目录
        original_cwd = Path.cwd()
        # 切换到项目路径
        os.chdir(project_path)
        
        # 如果不是静默模式，则打印初始化信息
        if not quiet:
            console.print("[cyan]Initializing git repository...[/cyan]")
            
        # 执行 git 初始化命令
        subprocess.run(["git", "init"], check=True, capture_output=True, text=True)
        # 添加所有文件到暂存区
        subprocess.run(["git", "add", "."], check=True, capture_output=True, text=True)
        # 提交初始提交
        subprocess.run(["git", "commit", "-m", "Initial commit from Specify template"], check=True, capture_output=True, text=True)
        
        # 如果不是静默模式，则打印成功信息
        if not quiet:
            console.print("[green]✓[/green] Git repository initialized")
        return True, None  # 返回成功标志和空错误信息

    except subprocess.CalledProcessError as e:
        # 处理命令执行错误
        error_msg = f"Command: {' '.join(e.cmd)}\nExit code: {e.returncode}"
        if e.stderr:
            error_msg += f"\nError: {e.stderr.strip()}"
        elif e.stdout:
            error_msg += f"\nOutput: {e.stdout.strip()}"

        # 如果不是静默模式，则打印错误信息
        if not quiet:
            console.print(f"[red]Error initializing git repository:[/red] {e}")
        return False, error_msg  # 返回失败标志和错误信息
    finally:
        # 无论成功与否，都切换回原始工作目录
        os.chdir(original_cwd)

def handle_vscode_settings(sub_item, dest_file, rel_path, verbose=False, tracker=None) -> None:
    """
    处理 .vscode/settings.json 文件的合并或复制
    
    参数:
        sub_item: 源文件路径
        dest_file: 目标文件路径
        rel_path: 相对路径（用于日志输出）
        verbose: 是否输出详细信息
        tracker: 步骤跟踪器（可选）
    """
    def log(message, color="green"):
        """
        内部日志函数，根据 verbose 和 tracker 状态决定是否输出
        
        参数:
            message: 日志消息
            color: 消息颜色
        """
        if verbose and not tracker:
            console.print(f"[{color}]{message}[/] {rel_path}")

    try:
        # 读取新设置文件内容
        with open(sub_item, 'r', encoding='utf-8') as f:
            new_settings = json.load(f)

        # 检查目标文件是否存在
        if dest_file.exists():
            # 如果存在，则合并 JSON 文件
            merged = merge_json_files(dest_file, new_settings, verbose=verbose and not tracker)
            # 将合并后的内容写回目标文件
            with open(dest_file, 'w', encoding='utf-8') as f:
                json.dump(merged, f, indent=4)  # 使用 4 个空格缩进
                f.write('\n')  # 文件末尾添加换行符
            log("Merged:", "green")  # 记录合并操作
        else:
            # 如果目标文件不存在，则直接复制
            shutil.copy2(sub_item, dest_file)
            log("Copied (no existing settings.json):", "blue")  # 记录复制操作

    except Exception as e:
        # 处理合并或复制过程中的异常
        log(f"Warning: Could not merge, copying instead: {e}", "yellow")
        shutil.copy2(sub_item, dest_file)  # 出现异常时直接复制

def merge_json_files(existing_path: Path, new_content: dict, verbose: bool = False) -> dict:
    """
    将新 JSON 内容合并到现有 JSON 文件中

    执行深度合并操作：
    - 添加新键
    - 保留现有键（除非被新内容覆盖）
    - 递归合并嵌套字典
    - 替换列表和其他值（不合并）

    参数:
        existing_path: 现有 JSON 文件的路径
        new_content: 要合并的新 JSON 内容
        verbose: 是否打印合并详情

    返回:
        dict: 合并后的 JSON 内容
    """
    try:
        # 尝试读取现有 JSON 文件
        with open(existing_path, 'r', encoding='utf-8') as f:
            existing_content = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # 如果文件不存在或无效，则直接使用新内容
        return new_content

    def deep_merge(base: dict, update: dict) -> dict:
        """
        递归地将更新字典合并到基础字典中
        
        参数:
            base: 基础字典
            update: 要合并的更新字典
            
        返回:
            dict: 合并后的字典
        """
        result = base.copy()  # 复制基础字典
        # 遍历更新字典中的所有键值对
        for key, value in update.items():
            # 如果键在基础字典中存在，且两个值都是字典，则递归合并
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                # 否则添加新键或替换现有值
                result[key] = value
        return result

    # 执行深度合并
    merged = deep_merge(existing_content, new_content)

    # 如果启用了详细输出，则打印合并信息
    if verbose:
        console.print(f"[cyan]Merged JSON file:[/cyan] {existing_path.name}")

    return merged  # 返回合并后的内容

def download_template_from_github(ai_assistant: str, download_dir: Path, *, script_type: str = "sh", verbose: bool = True, show_progress: bool = True, client: httpx.Client = None, debug: bool = False, github_token: str = None) -> Tuple[Path, dict]:
    """
    从 GitHub 下载指定 AI 助手的模板文件
    
    参数:
        ai_assistant: AI 助手名称
        download_dir: 下载目录路径
        script_type: 脚本类型 ("sh" 或 "ps")
        verbose: 是否显示详细信息
        show_progress: 是否显示下载进度条
        client: HTTP 客户端实例
        debug: 是否显示调试信息
        github_token: GitHub 访问令牌
        
    返回:
        Tuple[Path, dict]: (下载的 ZIP 文件路径, 元数据字典)
    """
    # GitHub 仓库信息
    repo_owner = "rj-wangbin6"
    repo_name = "spec-kit"
    
    # 如果未提供客户端，则创建一个新的
    if client is None:
        client = httpx.Client(verify=ssl_context)

    # 如果启用详细输出，则显示获取发布信息的消息
    if verbose:
        console.print("[cyan]Fetching latest release information...[/cyan]")
        
    # 构建 GitHub API URL
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"

    try:
        # 发送 GET 请求获取最新发布信息
        response = client.get(
            api_url,
            timeout=30,  # 30秒超时
            follow_redirects=True,  # 跟随重定向
            headers=_github_auth_headers(github_token),  # 添加认证头
        )
        status = response.status_code
        
        # 检查响应状态码
        if status != 200:
            msg = f"GitHub API returned {status} for {api_url}"
            if debug:
                msg += f"\nResponse headers: {response.headers}\nBody (truncated 500): {response.text[:500]}"
            raise RuntimeError(msg)
            
        try:
            # 解析 JSON 响应
            release_data = response.json()
        except ValueError as je:
            # 处理解析 JSON 失败的情况
            raise RuntimeError(f"Failed to parse release JSON: {je}\nRaw (truncated 400): {response.text[:400]}")
    except Exception as e:
        # 处理获取发布信息时的异常
        console.print(f"[red]Error fetching release information[/red]")
        console.print(Panel(str(e), title="Fetch Error", border_style="red"))
        raise typer.Exit(1)

    # 获取发布资产列表
    assets = release_data.get("assets", [])
    
    # 构建匹配模式
    pattern = f"spec-kit-template-{ai_assistant}-{script_type}"
    
    # 查找匹配的资产文件
    matching_assets = [
        asset for asset in assets
        if pattern in asset["name"] and asset["name"].endswith(".zip")
    ]

    # 获取第一个匹配的资产或 None
    asset = matching_assets[0] if matching_assets else None

    # 如果未找到匹配的资产，则显示错误信息并退出
    if asset is None:
        console.print(f"[red]No matching release asset found[/red] for [bold]{ai_assistant}[/bold] (expected pattern: [bold]{pattern}[/bold])")
        asset_names = [a.get('name', '?') for a in assets]
        console.print(Panel("\n".join(asset_names) or "(no assets)", title="Available Assets", border_style="yellow"))
        raise typer.Exit(1)

    # 获取下载 URL、文件名和文件大小
    download_url = asset["browser_download_url"]
    filename = asset["name"]
    file_size = asset["size"]

    # 如果启用详细输出，则显示找到的模板信息
    if verbose:
        console.print(f"[cyan]Found template:[/cyan] {filename}")
        console.print(f"[cyan]Size:[/cyan] {file_size:,} bytes")
        console.print(f"[cyan]Release:[/cyan] {release_data['tag_name']}")

    # 构建 ZIP 文件路径
    zip_path = download_dir / filename
    
    # 如果启用详细输出，则显示下载消息
    if verbose:
        console.print(f"[cyan]Downloading template...[/cyan]")

    try:
        # 流式下载文件
        with client.stream(
            "GET",
            download_url,
            timeout=60,  # 60秒超时
            follow_redirects=True,  # 跟随重定向
            headers=_github_auth_headers(github_token),  # 添加认证头
        ) as response:
            # 检查响应状态码
            if response.status_code != 200:
                body_sample = response.text[:400]
                raise RuntimeError(f"Download failed with {response.status_code}\nHeaders: {response.headers}\nBody (truncated): {body_sample}")
                
            # 获取文件总大小
            total_size = int(response.headers.get('content-length', 0))
            
            # 打开文件进行写入
            with open(zip_path, 'wb') as f:
                if total_size == 0:
                    # 如果总大小为0，则直接下载所有数据块
                    for chunk in response.iter_bytes(chunk_size=8192):
                        f.write(chunk)
                else:
                    # 如果总大小已知，则显示进度条（如果启用）
                    if show_progress:
                        with Progress(
                            SpinnerColumn(),  # 旋转动画列
                            TextColumn("[progress.description]{task.description}"),  # 描述文本列
                            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),  # 百分比列
                            console=console,  # 控制台对象
                        ) as progress:
                            # 添加下载任务
                            task = progress.add_task("Downloading...", total=total_size)
                            downloaded = 0
                            # 逐块下载并更新进度
                            for chunk in response.iter_bytes(chunk_size=8192):
                                f.write(chunk)
                                downloaded += len(chunk)
                                progress.update(task, completed=downloaded)
                    else:
                        # 不显示进度条，直接下载
                        for chunk in response.iter_bytes(chunk_size=8192):
                            f.write(chunk)
    except Exception as e:
        # 处理下载异常
        console.print(f"[red]Error downloading template[/red]")
        detail = str(e)
        # 如果 ZIP 文件存在，则删除它
        if zip_path.exists():
            zip_path.unlink()
        console.print(Panel(detail, title="Download Error", border_style="red"))
        raise typer.Exit(1)
        
    # 如果启用详细输出，则显示下载完成消息
    if verbose:
        console.print(f"Downloaded: {filename}")
        
    # 构建元数据字典
    metadata = {
        "filename": filename,
        "size": file_size,
        "release": release_data["tag_name"],
        "asset_url": download_url
    }
    
    # 返回 ZIP 文件路径和元数据
    return zip_path, metadata

def download_and_extract_template(project_path: Path, ai_assistant: str, script_type: str, is_current_dir: bool = False, *, verbose: bool = True, tracker: StepTracker | None = None, client: httpx.Client = None, debug: bool = False, github_token: str = None) -> Path:
    """
    下载最新发布版本并解压以创建新项目
    返回 project_path。如果提供了 tracker 则使用它（键包括：fetch, download, extract, cleanup）
    
    参数:
        project_path: 项目路径
        ai_assistant: AI 助手名称
        script_type: 脚本类型
        is_current_dir: 是否在当前目录初始化
        verbose: 是否显示详细信息
        tracker: 步骤跟踪器（可选）
        client: HTTP 客户端实例
        debug: 是否显示调试信息
        github_token: GitHub 访问令牌
        
    返回:
        Path: 项目路径
    """
    # 获取当前目录
    current_dir = Path.cwd()

    # 如果提供了跟踪器，则开始获取步骤
    if tracker:
        tracker.start("fetch", "contacting GitHub API")
    try:
        # 从 GitHub 下载模板
        zip_path, meta = download_template_from_github(
            ai_assistant,
            current_dir,
            script_type=script_type,
            verbose=verbose and tracker is None,
            show_progress=(tracker is None),
            client=client,
            debug=debug,
            github_token=github_token
        )
        # 如果提供了跟踪器，则更新获取步骤状态并添加下载步骤
        if tracker:
            tracker.complete("fetch", f"release {meta['release']} ({meta['size']:,} bytes)")
            tracker.add("download", "Download template")
            tracker.complete("download", meta['filename'])
    except Exception as e:
        # 处理下载模板时的异常
        if tracker:
            tracker.error("fetch", str(e))
        else:
            if verbose:
                console.print(f"[red]Error downloading template:[/red] {e}")
        raise

    # 如果提供了跟踪器，则添加并开始解压步骤
    if tracker:
        tracker.add("extract", "Extract template")
        tracker.start("extract")
    elif verbose:
        console.print("Extracting template...")

    try:
        # 如果不是在当前目录，则创建项目目录
        if not is_current_dir:
            project_path.mkdir(parents=True)

        # 打开 ZIP 文件进行解压
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # 获取 ZIP 文件内容列表
            zip_contents = zip_ref.namelist()
            # 如果提供了跟踪器，则更新 ZIP 列表步骤
            if tracker:
                tracker.start("zip-list")
                tracker.complete("zip-list", f"{len(zip_contents)} entries")
            elif verbose:
                console.print(f"[cyan]ZIP contains {len(zip_contents)} items[/cyan]")

            # 如果在当前目录初始化
            if is_current_dir:
                # 创建临时目录
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    # 解压到临时目录
                    zip_ref.extractall(temp_path)

                    # 获取解压的项目列表
                    extracted_items = list(temp_path.iterdir())
                    # 如果提供了跟踪器，则更新解压摘要步骤
                    if tracker:
                        tracker.start("extracted-summary")
                        tracker.complete("extracted-summary", f"temp {len(extracted_items)} items")
                    elif verbose:
                        console.print(f"[cyan]Extracted {len(extracted_items)} items to temp location[/cyan]")

                    # 设置源目录
                    source_dir = temp_path
                    # 如果只有一个目录，则使用该目录作为源目录
                    if len(extracted_items) == 1 and extracted_items[0].is_dir():
                        source_dir = extracted_items[0]
                        # 如果提供了跟踪器，则添加并完成扁平化步骤
                        if tracker:
                            tracker.add("flatten", "Flatten nested directory")
                            tracker.complete("flatten")
                        elif verbose:
                            console.print(f"[cyan]Found nested directory structure[/cyan]")

                    # 遍历源目录中的所有项目
                    for item in source_dir.iterdir():
                        # 构建目标路径
                        dest_path = project_path / item.name
                        # 如果是目录
                        if item.is_dir():
                            # 如果目标目录已存在
                            if dest_path.exists():
                                if verbose and not tracker:
                                    console.print(f"[yellow]Merging directory:[/yellow] {item.name}")
                                # 递归遍历目录中的所有文件
                                for sub_item in item.rglob('*'):
                                    # 如果是文件
                                    if sub_item.is_file():
                                        # 计算相对路径
                                        rel_path = sub_item.relative_to(item)
                                        # 构建目标文件路径
                                        dest_file = dest_path / rel_path
                                        # 创建目标文件的父目录
                                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                                        # 对 .vscode/settings.json 文件进行特殊处理 - 合并而不是覆盖
                                        if dest_file.name == "settings.json" and dest_file.parent.name == ".vscode":
                                            handle_vscode_settings(sub_item, dest_file, rel_path, verbose, tracker)
                                        else:
                                            # 复制文件
                                            shutil.copy2(sub_item, dest_file)
                            else:
                                # 如果目标目录不存在，则复制整个目录树
                                shutil.copytree(item, dest_path)
                        else:
                            # 如果是文件
                            # 如果目标文件已存在且启用了详细输出但没有跟踪器，则显示覆盖警告
                            if dest_path.exists() and verbose and not tracker:
                                console.print(f"[yellow]Overwriting file:[/yellow] {item.name}")
                            # 复制文件
                            shutil.copy2(item, dest_path)
                    # 如果启用了详细输出但没有跟踪器，则显示合并完成消息
                    if verbose and not tracker:
                        console.print(f"[cyan]Template files merged into current directory[/cyan]")
            else:
                # 如果不是在当前目录，则直接解压到项目路径
                zip_ref.extractall(project_path)

                # 获取解压的项目列表
                extracted_items = list(project_path.iterdir())
                # 如果提供了跟踪器，则更新解压摘要步骤
                if tracker:
                    tracker.start("extracted-summary")
                    tracker.complete("extracted-summary", f"{len(extracted_items)} top-level items")
                elif verbose:
                    console.print(f"[cyan]Extracted {len(extracted_items)} items to {project_path}:[/cyan]")
                    # 显示解压的项目列表
                    for item in extracted_items:
                        console.print(f"  - {item.name} ({'dir' if item.is_dir() else 'file'})")

                # 如果只有一个目录，则扁平化目录结构
                if len(extracted_items) == 1 and extracted_items[0].is_dir():
                    nested_dir = extracted_items[0]
                    # 创建临时移动目录路径
                    temp_move_dir = project_path.parent / f"{project_path.name}_temp"

                    # 移动嵌套目录到临时位置
                    shutil.move(str(nested_dir), str(temp_move_dir))

                    # 删除项目目录
                    project_path.rmdir()

                    # 将临时目录移动到项目路径
                    shutil.move(str(temp_move_dir), str(project_path))
                    # 如果提供了跟踪器，则添加并完成扁平化步骤
                    if tracker:
                        tracker.add("flatten", "Flatten nested directory")
                        tracker.complete("flatten")
                    elif verbose:
                        console.print(f"[cyan]Flattened nested directory structure[/cyan]")

    except Exception as e:
        # 处理解压模板时的异常
        if tracker:
            tracker.error("extract", str(e))
        else:
            if verbose:
                console.print(f"[red]Error extracting template:[/red] {e}")
                if debug:
                    console.print(Panel(str(e), title="Extraction Error", border_style="red"))

        # 如果不是在当前目录且项目路径存在，则删除项目路径
        if not is_current_dir and project_path.exists():
            shutil.rmtree(project_path)
        raise typer.Exit(1)
    else:
        # 如果没有异常且提供了跟踪器，则完成解压步骤
        if tracker:
            tracker.complete("extract")
    finally:
        # 最终处理步骤
        if tracker:
            tracker.add("cleanup", "Remove temporary archive")

        # 如果 ZIP 文件存在，则删除它
        if zip_path.exists():
            zip_path.unlink()
            # 如果提供了跟踪器，则完成清理步骤
            if tracker:
                tracker.complete("cleanup")
            elif verbose:
                console.print(f"Cleaned up: {zip_path.name}")

    # 返回项目路径
    return project_path


def ensure_executable_scripts(project_path: Path, tracker: StepTracker | None = None) -> None:
    """
    确保 .specify/scripts 下的 POSIX .sh 脚本具有执行权限（在 Windows 上无操作）
    
    参数:
        project_path: 项目路径
        tracker: 步骤跟踪器（可选）
    """
    # 如果是 Windows 系统，则静默跳过
    if os.name == "nt":
        return
        
    # 构建脚本根目录路径
    scripts_root = project_path / ".specify" / "scripts"
    
    # 如果脚本根目录不存在，则返回
    if not scripts_root.is_dir():
        return
        
    # 初始化失败列表和更新计数器
    failures: list[str] = []
    updated = 0
    
    # 递归遍历所有 .sh 脚本文件
    for script in scripts_root.rglob("*.sh"):
        try:
            # 如果是符号链接或不是文件，则跳过
            if script.is_symlink() or not script.is_file():
                continue
                
            try:
                # 打开文件检查是否以 #! 开头（即是否为脚本文件）
                with script.open("rb") as f:
                    if f.read(2) != b"#!":
                        continue
            except Exception:
                continue
                
            # 获取文件状态和权限模式
            st = script.stat()
            mode = st.st_mode
            
            # 如果已经有执行权限，则跳过
            if mode & 0o111:
                continue
                
            # 计算新的权限模式
            new_mode = mode
            # 根据读取权限设置相应的执行权限
            if mode & 0o400: 
                new_mode |= 0o100  # 设置用户执行权限
            if mode & 0o040: 
                new_mode |= 0o010  # 设置组执行权限
            if mode & 0o004: 
                new_mode |= 0o001  # 设置其他用户执行权限
                
            # 确保至少有用户执行权限
            if not (new_mode & 0o100):
                new_mode |= 0o100
                
            # 设置新的权限模式
            os.chmod(script, new_mode)
            updated += 1  # 增加更新计数器
        except Exception as e:
            # 记录失败的脚本和错误信息
            failures.append(f"{script.relative_to(scripts_root)}: {e}")
            
    # 如果提供了跟踪器，则更新 chmod 步骤
    if tracker:
        # 构建详细信息
        detail = f"{updated} updated" + (f", {len(failures)} failed" if failures else "")
        # 添加 chmod 步骤
        tracker.add("chmod", "Set script permissions recursively")
        # 根据是否有失败来完成或标记错误
        (tracker.error if failures else tracker.complete)("chmod", detail)
    else:
        # 如果没有跟踪器但有更新，则显示更新信息
        if updated:
            console.print(f"[cyan]Updated execute permissions on {updated} script(s) recursively[/cyan]")
        # 如果有失败，则显示失败信息
        if failures:
            console.print("[yellow]Some scripts could not be updated:[/yellow]")
            for f in failures:
                console.print(f"  - {f}")

@app.command()
def init(
    project_name: str = typer.Argument(None, help="Name for your new project directory (optional if using --here, or use '.' for current directory)"),
    ai_assistant: str = typer.Option(None, "--ai", help="AI assistant to use: claude, gemini, copilot, cursor-agent, qwen, opencode, codex, windsurf, kilocode, auggie, codebuddy, amp, or q"),
    script_type: str = typer.Option(None, "--script", help="Script type to use: sh or ps"),
    ignore_agent_tools: bool = typer.Option(False, "--ignore-agent-tools", help="Skip checks for AI agent tools like Claude Code"),
    no_git: bool = typer.Option(False, "--no-git", help="Skip git repository initialization"),
    here: bool = typer.Option(False, "--here", help="Initialize project in the current directory instead of creating a new one"),
    force: bool = typer.Option(False, "--force", help="Force merge/overwrite when using --here (skip confirmation)"),
    skip_tls: bool = typer.Option(False, "--skip-tls", help="Skip SSL/TLS verification (not recommended)"),
    debug: bool = typer.Option(False, "--debug", help="Show verbose diagnostic output for network and extraction failures"),
    github_token: str = typer.Option(None, "--github-token", help="GitHub token to use for API requests (or set GH_TOKEN or GITHUB_TOKEN environment variable)"),
):
    """
    从最新模板初始化一个新的 Specify 项目。

    此命令将：
    1. 检查所需工具是否已安装（git 是可选的）
    2. 让您选择 AI 助手
    3. 从 GitHub 下载相应的模板
    4. 将模板解压到新项目目录或当前目录
    5. 初始化新的 git 仓库（如果没有 --no-git 且没有现有仓库）
    6. 可选地设置 AI 助手命令

    示例:
        specify init my-project
        specify init my-project --ai claude
        specify init my-project --ai copilot --no-git
        specify init --ignore-agent-tools my-project
        specify init . --ai claude         # 在当前目录初始化
        specify init .                     # 在当前目录初始化（交互式 AI 选择）
        specify init --here --ai claude    # 当前目录的替代语法
        specify init --here --ai codex
        specify init --here --ai codebuddy
        specify init --here
        specify init --here --force  # 当前目录非空时跳过确认
    """

    # 显示 banner
    show_banner()

    # 如果项目名称是 "."，则设置为当前目录模式
    if project_name == ".":
        here = True
        project_name = None  # 清除项目名称以使用现有的验证逻辑

    # 检查参数冲突
    if here and project_name:
        console.print("[red]Error:[/red] Cannot specify both project name and --here flag")
        raise typer.Exit(1)

    # 检查必需参数
    if not here and not project_name:
        console.print("[red]Error:[/red] Must specify either a project name, use '.' for current directory, or use --here flag")
        raise typer.Exit(1)

    # 处理在当前目录初始化的情况
    if here:
        project_name = Path.cwd().name  # 使用当前目录名称作为项目名称
        project_path = Path.cwd()       # 项目路径为当前目录

        # 检查当前目录是否非空
        existing_items = list(project_path.iterdir())
        if existing_items:
            console.print(f"[yellow]Warning:[/yellow] Current directory is not empty ({len(existing_items)} items)")
            console.print("[yellow]Template files will be merged with existing content and may overwrite existing files[/yellow]")
            # 如果提供了 --force 参数，则跳过确认直接继续
            if force:
                console.print("[cyan]--force supplied: skipping confirmation and proceeding with merge[/cyan]")
            else:
                # 询问用户是否继续
                response = typer.confirm("Do you want to continue?")
                if not response:
                    console.print("[yellow]Operation cancelled[/yellow]")
                    raise typer.Exit(0)
    else:
        # 处理创建新目录的情况
        project_path = Path(project_name).resolve()  # 解析项目路径
        # 检查项目目录是否已存在
        if project_path.exists():
            # 如果已存在，显示错误面板并退出
            error_panel = Panel(
                f"Directory '[cyan]{project_name}[/cyan]' already exists\n"
                "Please choose a different project name or remove the existing directory.",
                title="[red]Directory Conflict[/red]",
                border_style="red",
                padding=(1, 2)
            )
            console.print()
            console.print(error_panel)
            raise typer.Exit(1)

    # 获取当前工作目录
    current_dir = Path.cwd()

    # 构建设置信息行
    setup_lines = [
        "[cyan]Specify Project Setup[/cyan]",
        "",
        f"{'Project':<15} [green]{project_path.name}[/green]",  # 项目名称
        f"{'Working Path':<15} [dim]{current_dir}[/dim]",       # 工作路径
    ]

    # 如果不是在当前目录初始化，则添加目标路径信息
    if not here:
        setup_lines.append(f"{'Target Path':<15} [dim]{project_path}[/dim]")

    # 显示设置信息面板
    console.print(Panel("\n".join(setup_lines), border_style="cyan", padding=(1, 2)))

    # 检查是否需要初始化 git 仓库
    should_init_git = False
    if not no_git:
        should_init_git = check_tool("git")  # 检查 git 是否可用
        if not should_init_git:
            console.print("[yellow]Git not found - will skip repository initialization[/yellow]")

    # 处理 AI 助手选择
    if ai_assistant:
        # 如果通过参数指定了 AI 助手，验证其有效性
        if ai_assistant not in AGENT_CONFIG:
            console.print(f"[red]Error:[/red] Invalid AI assistant '{ai_assistant}'. Choose from: {', '.join(AGENT_CONFIG.keys())}")
            raise typer.Exit(1)
        selected_ai = ai_assistant
    else:
        # 如果未指定 AI 助手，则创建选项字典并让用户选择
        ai_choices = {key: config["name"] for key, config in AGENT_CONFIG.items()}
        selected_ai = select_with_arrows(
            ai_choices, 
            "Choose your AI assistant:", 
            "copilot"  # 默认选择 copilot
        )

    # 检查 AI 助手工具（如果未忽略检查）
    if not ignore_agent_tools:
        agent_config = AGENT_CONFIG.get(selected_ai)
        # 如果 AI 助手需要 CLI 工具
        if agent_config and agent_config["requires_cli"]:
            install_url = agent_config["install_url"]
            # 检查工具是否可用
            if not check_tool(selected_ai):
                # 如果不可用，显示错误面板并退出
                error_panel = Panel(
                    f"[cyan]{selected_ai}[/cyan] not found\n"
                    f"Install from: [cyan]{install_url}[/cyan]\n"
                    f"{agent_config['name']} is required to continue with this project type.\n\n"
                    "Tip: Use [cyan]--ignore-agent-tools[/cyan] to skip this check",
                    title="[red]Agent Detection Error[/red]",
                    border_style="red",
                    padding=(1, 2)
                )
                console.print()
                console.print(error_panel)
                raise typer.Exit(1)

    # 处理脚本类型选择
    if script_type:
        # 如果通过参数指定了脚本类型，验证其有效性
        if script_type not in SCRIPT_TYPE_CHOICES:
            console.print(f"[red]Error:[/red] Invalid script type '{script_type}'. Choose from: {', '.join(SCRIPT_TYPE_CHOICES.keys())}")
            raise typer.Exit(1)
        selected_script = script_type
    else:
        # 如果未指定脚本类型，根据操作系统设置默认值
        default_script = "ps" if os.name == "nt" else "sh"

        # 如果是交互式终端，则让用户选择脚本类型
        if sys.stdin.isatty():
            selected_script = select_with_arrows(SCRIPT_TYPE_CHOICES, "Choose script type (or press Enter)", default_script)
        else:
            # 否则使用默认脚本类型
            selected_script = default_script

    # 显示选择的 AI 助手和脚本类型
    console.print(f"[cyan]Selected AI assistant:[/cyan] {selected_ai}")
    console.print(f"[cyan]Selected script type:[/cyan] {selected_script}")

    # 创建步骤跟踪器
    tracker = StepTracker("Initialize Specify Project")

    # 设置跟踪器活动标志
    sys._specify_tracker_active = True

    # 添加并完成预检查步骤
    tracker.add("precheck", "Check required tools")
    tracker.complete("precheck", "ok")
    
    # 添加并完成 AI 助手选择步骤
    tracker.add("ai-select", "Select AI assistant")
    tracker.complete("ai-select", f"{selected_ai}")
    
    # 添加并完成脚本类型选择步骤
    tracker.add("script-select", "Select script type")
    tracker.complete("script-select", selected_script)
    
    # 添加其他步骤
    for key, label in [
        ("fetch", "Fetch latest release"),
        ("download", "Download template"),
        ("extract", "Extract template"),
        ("zip-list", "Archive contents"),
        ("extracted-summary", "Extraction summary"),
        ("chmod", "Ensure scripts executable"),
        ("cleanup", "Cleanup"),
        ("git", "Initialize git repository"),
        ("final", "Finalize")
    ]:
        tracker.add(key, label)

    # 跟踪 git 错误消息，在 Live 上下文外以便持久化显示
    git_error_message = None

    # 使用 Live 组件显示实时更新的跟踪器
    with Live(tracker.render(), console=console, refresh_per_second=8, transient=True) as live:
        # 附加刷新回调函数
        tracker.attach_refresh(lambda: live.update(tracker.render()))
        try:
            # 设置 SSL 上下文
            verify = not skip_tls
            local_ssl_context = ssl_context if verify else False
            local_client = httpx.Client(verify=local_ssl_context)

            # 下载并解压模板
            download_and_extract_template(project_path, selected_ai, selected_script, here, verbose=False, tracker=tracker, client=local_client, debug=debug, github_token=github_token)

            # 确保脚本具有执行权限
            ensure_executable_scripts(project_path, tracker=tracker)

            # 处理 git 初始化
            if not no_git:
                tracker.start("git")
                # 检查是否已存在 git 仓库
                if is_git_repo(project_path):
                    tracker.complete("git", "existing repo detected")
                elif should_init_git:
                    # 初始化 git 仓库
                    success, error_msg = init_git_repo(project_path, quiet=True)
                    if success:
                        tracker.complete("git", "initialized")
                    else:
                        tracker.error("git", "init failed")
                        git_error_message = error_msg
                else:
                    tracker.skip("git", "git not available")
            else:
                tracker.skip("git", "--no-git flag")

            # 完成最终步骤
            tracker.complete("final", "project ready")
        except Exception as e:
            # 处理异常
            tracker.error("final", str(e))
            console.print(Panel(f"Initialization failed: {e}", title="Failure", border_style="red"))
            # 如果启用调试模式，则显示环境信息
            if debug:
                _env_pairs = [
                    ("Python", sys.version.split()[0]),
                    ("Platform", sys.platform),
                    ("CWD", str(Path.cwd())),
                ]
                _label_width = max(len(k) for k, _ in _env_pairs)
                env_lines = [f"{k.ljust(_label_width)} → [bright_black]{v}[/bright_black]" for k, v in _env_pairs]
                console.print(Panel("\n".join(env_lines), title="Debug Environment", border_style="magenta"))
            # 如果不是在当前目录且项目路径存在，则删除项目路径
            if not here and project_path.exists():
                shutil.rmtree(project_path)
            raise typer.Exit(1)
        finally:
            pass

    # 显示最终的跟踪器状态
    console.print(tracker.render())
    console.print("\n[bold green]Project ready.[/bold green]")
    
    # 如果 git 初始化失败，显示错误详情
    if git_error_message:
        console.print()
        git_error_panel = Panel(
            f"[yellow]Warning:[/yellow] Git repository initialization failed\n\n"
            f"{git_error_message}\n\n"
            f"[dim]You can initialize git manually later with:[/dim]\n"
            f"[cyan]cd {project_path if not here else '.'}[/cyan]\n"
            f"[cyan]git init[/cyan]\n"
            f"[cyan]git add .[/cyan]\n"
            f"[cyan]git commit -m \"Initial commit\"[/cyan]",
            title="[red]Git Initialization Failed[/red]",
            border_style="red",
            padding=(1, 2)
        )
        console.print(git_error_panel)

    # 显示代理文件夹安全提醒
    agent_config = AGENT_CONFIG.get(selected_ai)
    if agent_config:
        agent_folder = agent_config["folder"]
        security_notice = Panel(
            f"Some agents may store credentials, auth tokens, or other identifying and private artifacts in the agent folder within your project.\n"
            f"Consider adding [cyan]{agent_folder}[/cyan] (or parts of it) to [cyan].gitignore[/cyan] to prevent accidental credential leakage.",
            title="[yellow]Agent Folder Security[/yellow]",
            border_style="yellow",
            padding=(1, 2)
        )
        console.print()
        console.print(security_notice)

    # 构建下一步操作指南
    steps_lines = []
    if not here:
        steps_lines.append(f"1. Go to the project folder: [cyan]cd {project_name}[/cyan]")
        step_num = 2
    else:
        steps_lines.append("1. You're already in the project directory!")
        step_num = 2

    # 如果选择了 Codex，添加特定的设置步骤
    if selected_ai == "codex":
        codex_path = project_path / ".codex"
        quoted_path = shlex.quote(str(codex_path))
        if os.name == "nt":  # Windows
            cmd = f"setx CODEX_HOME {quoted_path}"
        else:  # Unix-like systems
            cmd = f"export CODEX_HOME={quoted_path}"
        
        steps_lines.append(f"{step_num}. Set [cyan]CODEX_HOME[/cyan] environment variable before running Codex: [cyan]{cmd}[/cyan]")
        step_num += 1

    # 添加基本使用步骤
    steps_lines.append(f"{step_num}. Start using slash commands with your AI agent:")

    steps_lines.append("   2.1 [cyan]/speckit.constitution[/] - Establish project principles")
    steps_lines.append("   2.2 [cyan]/speckit.specify[/] - Create baseline specification")
    steps_lines.append("   2.3 [cyan]/speckit.plan[/] - Create implementation plan")
    steps_lines.append("   2.4 [cyan]/speckit.tasks[/] - Generate actionable tasks")
    steps_lines.append("   2.5 [cyan]/speckit.implement[/] - Execute implementation")

    # 显示下一步操作面板
    steps_panel = Panel("\n".join(steps_lines), title="Next Steps", border_style="cyan", padding=(1,2))
    console.print()
    console.print(steps_panel)

    # 构建增强命令指南
    enhancement_lines = [
        "Optional commands that you can use for your specs [bright_black](improve quality & confidence)[/bright_black]",
        "",
        f"○ [cyan]/speckit.clarify[/] [bright_black](optional)[/bright_black] - Ask structured questions to de-risk ambiguous areas before planning (run before [cyan]/speckit.plan[/] if used)",
        f"○ [cyan]/speckit.analyze[/] [bright_black](optional)[/bright_black] - Cross-artifact consistency & alignment report (after [cyan]/speckit.tasks[/], before [cyan]/speckit.implement[/])",
        f"○ [cyan]/speckit.checklist[/] [bright_black](optional)[/bright_black] - Generate quality checklists to validate requirements completeness, clarity, and consistency (after [cyan]/speckit.plan[/])"
    ]
    
    # 显示增强命令面板
    enhancements_panel = Panel("\n".join(enhancement_lines), title="Enhancement Commands", border_style="cyan", padding=(1,2))
    console.print()
    console.print(enhancements_panel)

@app.command()
def update():
    """
    从仓库拉取最新的 .github、.specify 和 .vscode 目录，
    覆盖现有文件但保留本地新增的文件。
    
    此命令会:
    1. 从 GitHub 下载最新的模板
    2. 更新 .github、.specify 和 .vscode 目录中的文件
    3. 覆盖同名文件，但保留本地新增的文件
    4. 不会删除本地额外的文件
    """
    show_banner()
    console.print("[bold]Updating project files from template...[/bold]\n")

    # 检查当前目录是否为 git 仓库
    if not is_git_repo(Path.cwd()):
        console.print("[red]Error:[/red] This command must be run from within a git repository")
        raise typer.Exit(1)

    # 创建步骤跟踪器
    tracker = StepTracker("Update Project Files")
    
    try:
        # 添加步骤
        tracker.add("fetch", "Fetch latest template")
        tracker.add("extract", "Extract template files")
        tracker.add("merge", "Merge files")
        tracker.add("chmod", "Set script permissions")
        tracker.add("cleanup", "Cleanup")
        tracker.add("final", "Finalize")

        # 开始获取步骤
        tracker.start("fetch", "contacting GitHub API")
        
        # 获取当前 AI 助手和脚本类型信息
        selected_ai = "copilot"  # 默认使用 copilot
        selected_script = "sh" if os.name != "nt" else "ps"  # 根据操作系统选择默认脚本类型
        
        # 尝试从现有配置中获取 AI 助手和脚本类型
        for agent_key, agent_config in AGENT_CONFIG.items():
            agent_folder = agent_config["folder"]
            if Path(agent_folder.strip("/")).exists():
                selected_ai = agent_key
                break
        
        # 从 GitHub 下载模板
        current_dir = Path.cwd()
        zip_path, meta = download_template_from_github(
            selected_ai,
            current_dir,
            script_type=selected_script,
            verbose=False,
            show_progress=False,
            client=client,
        )
        
        tracker.complete("fetch", f"release {meta['release']} ({meta['size']:,} bytes)")
        
        # 开始解压步骤
        tracker.start("extract")
        
        # 创建临时目录用于解压
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 解压 ZIP 文件
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_path)
            
            tracker.complete("extract", f"{len(list(temp_path.rglob('*')))} items")
            
            # 开始合并步骤
            tracker.start("merge")
            merged_count = 0
            
            # 定义需要更新的目录
            update_dirs = [".github", ".specify", ".vscode"]
            
            for dir_name in update_dirs:
                source_dir = temp_path / dir_name
                target_dir = current_dir / dir_name
                
                # 如果源目录存在
                if source_dir.exists():
                    # 如果目标目录不存在，则直接复制整个目录
                    if not target_dir.exists():
                        shutil.copytree(source_dir, target_dir)
                        count = len(list(source_dir.rglob('*')))
                        console.print(f"[green]✓[/green] Copied {dir_name} directory ({count} items)")
                        merged_count += count
                    else:
                        # 如果目标目录存在，则逐个文件覆盖
                        for source_file in source_dir.rglob('*'):
                            if source_file.is_file():
                                # 计算相对路径
                                rel_path = source_file.relative_to(source_dir)
                                target_file = target_dir / rel_path
                                
                                # 创建目标文件的父目录
                                target_file.parent.mkdir(parents=True, exist_ok=True)
                                
                                # 复制文件（覆盖现有文件）
                                shutil.copy2(source_file, target_file)
                                
                                # 特殊处理 .vscode/settings.json 文件
                                if dir_name == ".vscode" and source_file.name == "settings.json":
                                    handle_vscode_settings(source_file, target_file, rel_path, verbose=False)
                                
                        count = len(list(source_dir.rglob('*')))
                        console.print(f"[green]✓[/green] Updated {dir_name} directory ({count} items)")
                        merged_count += count
                else:
                    console.print(f"[yellow]⚠[/yellow] {dir_name} directory not found in template")
            
            tracker.complete("merge", f"{merged_count} files updated")
            
            # 确保脚本具有执行权限
            tracker.start("chmod")
            ensure_executable_scripts(current_dir, tracker=None)
            tracker.complete("chmod")
            
            # 清理步骤
            tracker.start("cleanup")
            if zip_path.exists():
                zip_path.unlink()
            tracker.complete("cleanup")
            
            # 完成最终步骤
            tracker.complete("final", "update completed")
            
        console.print(tracker.render())
        console.print("\n[bold green]Project files updated successfully![/bold green]")
        console.print("[dim]Existing files have been overwritten, but local additions are preserved.[/dim]")
        
    except Exception as e:
        tracker.error("final", str(e))
        console.print(Panel(f"Update failed: {e}", title="Failure", border_style="red"))
        raise typer.Exit(1)

@app.command()
def check():
    """
    检查所有必需的工具是否已安装。
    """
    # 显示 banner
    show_banner()
    # 显示检查工具的消息
    console.print("[bold]Checking for installed tools...[/bold]\n")

    # 创建步骤跟踪器
    tracker = StepTracker("Check Available Tools")

    # 添加并检查 git 工具
    tracker.add("git", "Git version control")
    git_ok = check_tool("git", tracker=tracker)

    # 初始化 AI 助手检查结果字典
    agent_results = {}
    
    # 遍历所有 AI 助手配置
    for agent_key, agent_config in AGENT_CONFIG.items():
        agent_name = agent_config["name"]  # 获取助手名称
        requires_cli = agent_config["requires_cli"]  # 检查是否需要 CLI 工具

        # 添加助手到跟踪器
        tracker.add(agent_key, agent_name)

        # 如果需要 CLI 工具，则检查工具是否可用
        if requires_cli:
            agent_results[agent_key] = check_tool(agent_key, tracker=tracker)
        else:
            # 基于 IDE 的助手 - 跳过 CLI 检查并标记为可选
            tracker.skip(agent_key, "IDE-based, no CLI check")
            agent_results[agent_key] = False  # 不将 IDE 助手计为"找到"

    # 检查 VS Code 变体（不在助手配置中）
    tracker.add("code", "Visual Studio Code")
    code_ok = check_tool("code", tracker=tracker)

    tracker.add("code-insiders", "Visual Studio Code Insiders")
    code_insiders_ok = check_tool("code-insiders", tracker=tracker)

    # 显示跟踪器结果
    console.print(tracker.render())

    # 显示完成消息
    console.print("\n[bold green]Specify CLI is ready to use![/bold green]")

    # 如果 git 不可用，显示提示
    if not git_ok:
        console.print("[dim]Tip: Install git for repository management[/dim]")

    # 如果没有找到任何 AI 助手，显示提示
    if not any(agent_results.values()):
        console.print("[dim]Tip: Install an AI assistant for the best experience[/dim]")

def main():
    """
    主函数，运行 Typer 应用
    """
    app()

if __name__ == "__main__":
    """
    当脚本作为主程序运行时，调用 main 函数
    """
    main()

