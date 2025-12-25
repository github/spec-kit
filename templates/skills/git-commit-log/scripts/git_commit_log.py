#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Git提交记录拉取工具
从Git仓库拉取提交记录，默认只输出到控制台，不创建临时文件

使用方法:
    # 查看当前仓库最近7天的提交
    python git_commit_log.py
    
    # 查看指定用户的提交
    python git_commit_log.py --author zhangsan@ruijie.com
    
    # 查看指定时间范围的提交
    python git_commit_log.py --since 2025-12-01 --until 2025-12-24
    
    # 查看所有分支的提交
    python git_commit_log.py --all-branches
    
    # 只显示提交统计，不显示详细内容
    python git_commit_log.py --stat-only
    
    # 保存输出到文件
    python git_commit_log.py --save --output commits.txt
"""

import os
import sys
import subprocess
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class GitCommitLog:
    """Git提交记录工具类"""
    
    def __init__(
        self,
        repo_path: Optional[str] = None,
        author: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        branch: Optional[str] = None,
        all_branches: bool = False,
        max_count: Optional[int] = None,
        format_type: str = 'detailed',
        show_files: bool = True,
        show_stats: bool = True,
        show_diff: bool = False,
        max_diff_lines: int = 500,
        timeout: int = 30,
        scan_repos: bool = False,
        base_dir: Optional[str] = None,
        scan_depth: int = 2
    ):
        """
        初始化Git提交记录工具
        
        Args:
            repo_path: Git仓库路径，默认为当前目录
            author: 提交作者（支持邮箱或用户名）
            since: 开始日期（格式：YYYY-MM-DD）
            until: 结束日期（格式：YYYY-MM-DD）
            branch: 指定分支，默认当前分支
            all_branches: 是否查看所有分支
            max_count: 最大提交数量
            format_type: 输出格式（detailed/simple/oneline/json）
            show_files: 是否显示文件变更
            show_stats: 是否显示统计信息
            show_diff: 是否显示代码差异
            max_diff_lines: 最大差异行数限制
            timeout: Git命令超时时间（秒）
            scan_repos: 是否扫描多个仓库
            base_dir: 扫描的基础目录
            scan_depth: 扫描深度
        """
        self.author = author
        self.since = since
        self.until = until
        self.branch = branch
        self.all_branches = all_branches
        self.max_count = max_count
        self.format_type = format_type
        self.show_files = show_files
        self.show_stats = show_stats
        self.show_diff = show_diff
        self.max_diff_lines = max_diff_lines
        self.timeout = timeout
        self.scan_repos = scan_repos
        self.scan_depth = scan_depth
        
        # 如果启用扫描模式
        if scan_repos:
            self.base_dir = Path(base_dir) if base_dir else Path.cwd()
            self.repo_path = None
            self.repos = self._find_git_repos(self.base_dir)
        else:
            # 单仓库模式
            if repo_path:
                self.repo_path = Path(repo_path)
            else:
                # 自动查找当前目录或父目录的Git仓库
                self.repo_path = self._find_current_repo()
            
            if self.repo_path and not self._is_git_repo():
                raise ValueError(f"目录不是Git仓库: {self.repo_path}")
            
            self.repos = [self.repo_path] if self.repo_path else []
    
    def _find_current_repo(self) -> Optional[Path]:
        """查找当前目录或父目录的Git仓库"""
        current = Path.cwd()
        
        # 检查当前目录
        if (current / ".git").exists():
            return current
        
        # 检查父目录
        for parent in current.parents:
            if (parent / ".git").exists():
                return parent
        
        return None
    
    def _find_git_repos(self, base_dir: Path, current_depth: int = 0) -> List[Path]:
        """
        递归查找Git仓库
        
        Args:
            base_dir: 基础目录
            current_depth: 当前深度
            
        Returns:
            Git仓库路径列表
        """
        repos = []
        
        # 检查当前目录是否为Git仓库
        if (base_dir / ".git").exists():
            repos.append(base_dir)
            return repos
        
        # 如果达到最大深度，停止扫描
        if current_depth >= self.scan_depth:
            return repos
        
        # 遍历子目录
        try:
            for item in base_dir.iterdir():
                if not item.is_dir() or item.name.startswith('.'):
                    continue
                
                # 递归扫描
                repos.extend(self._find_git_repos(item, current_depth + 1))
        except PermissionError:
            pass
        
        return repos
    
    def _is_git_repo(self) -> bool:
        """检查是否为Git仓库"""
        return self.repo_path and (self.repo_path / ".git").exists()
    
    def _run_git_command(self, args: List[str], repo_path: Path) -> Tuple[bool, str]:
        """
        执行Git命令
        
        Args:
            args: Git命令参数列表
            repo_path: 仓库路径
            
        Returns:
            (是否成功, 输出内容)
        """
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=self.timeout
            )
            return result.returncode == 0, result.stdout
        except subprocess.TimeoutExpired:
            return False, "命令执行超时"
        except Exception as e:
            return False, f"执行命令失败: {str(e)}"
    
    def _build_log_command(self) -> List[str]:
        """构建git log命令参数"""
        args = ["log"]
        
        # 格式化字符串：哈希|作者名|作者邮箱|日期|提交信息
        args.extend(["--pretty=format:%H|%an|%ae|%ad|%s", "--date=iso"])
        
        # 添加作者过滤
        if self.author:
            args.extend(["--author", self.author])
        
        # 添加时间范围
        if self.since:
            args.append(f"--since={self.since}")
        if self.until:
            args.append(f"--until={self.until}")
        
        # 添加分支参数
        if self.all_branches:
            args.append("--all")
        elif self.branch:
            args.append(self.branch)
        
        # 限制提交数量
        if self.max_count:
            args.extend(["-n", str(self.max_count)])
        
        return args
    
    def get_commits(self, repo_path: Optional[Path] = None) -> List[Dict]:
        """
        获取提交记录
        
        Args:
            repo_path: 仓库路径，如果为None则使用self.repo_path
        
        Returns:
            提交记录列表
        """
        if repo_path is None:
            repo_path = self.repo_path
        
        args = self._build_log_command()
        success, output = self._run_git_command(args, repo_path)
        
        if not success:
            print(f"❌ 获取提交记录失败: {output}")
            return []
        
        if not output.strip():
            return []
        
        commits = []
        for line in output.strip().split('\n'):
            if not line:
                continue
            
            parts = line.split('|', 4)
            if len(parts) == 5:
                commit_hash, author_name, author_email, date, message = parts
                
                commit_data = {
                    'hash': commit_hash[:8],
                    'full_hash': commit_hash,
                    'author_name': author_name,
                    'author_email': author_email,
                    'date': date,
                    'message': message
                }
                
                # 获取文件变更信息
                if self.show_files:
                    commit_data['files'] = self._get_commit_files(commit_hash, repo_path)
                
                # 获取代码差异
                if self.show_diff:
                    commit_data['diff'] = self._get_commit_diff(commit_hash, repo_path)
                
                commit_data['repository'] = repo_path.name
                commits.append(commit_data)
        
        return commits
    
    def _get_commit_files(self, commit_hash: str, repo_path: Path) -> List[Dict]:
        """
        获取指定提交的文件变更列表
        
        Args:
            repo_path: 仓库路径
            
        Returns:
            文件变更列表
        """
        args = ["show", "--pretty=", "--name-status", commit_hash]
        success, output = self._run_git_command(args, repo_path)
        
        if not success or not output.strip():
            return []
        
        files = []
        for line in output.strip().split('\n'):
            if not line:
                continue
            
            parts = line.split('\t', 1)
            if len(parts) == 2:
                status, filepath = parts
                files.append({
                    'status': status,
                    'path': filepath
                })
        
        return files
    
    def _get_commit_diff(self, commit_hash: str, repo_path: Path) -> str:
        """
        获取指定提交的代码差异
        
        Args:
            commit_hash: 提交哈希值
            repo_path: 仓库路径
            
        Returns:
            代码差异文本
        """
        args = ["show", "--pretty=", commit_hash]
        success, output = self._run_git_command(args, repo_path)
        
        if not success:
            return ""
        
        # 限制差异行数
        lines = output.split('\n')
        if len(lines) > self.max_diff_lines:
            truncated = '\n'.join(lines[:self.max_diff_lines])
            truncated += f"\n\n... (差异内容过长，已截断。共 {len(lines)} 行，仅显示前 {self.max_diff_lines} 行)"
            return truncated
        
        return output
    
    def _get_commit_stats(self, commit_hash: str) -> str:
        """
        获取指定提交的统计信息
        
        Args:
            commit_hash: 提交哈希值
            
        Returns:
            统计信息文本
        """
        args = ["show", "--stat", "--pretty=", commit_hash]
        success, output = self._run_git_command(args)
        
        if not success:
            return ""
        
        return output
    
    def get_repo_info(self, repo_path: Optional[Path] = None) -> Dict:
        """获取仓库信息"""
        if repo_path is None:
            repo_path = self.repo_path
        
        info = {
            'path': str(repo_path),
            'name': repo_path.name
        }
        
        # 获取当前分支
        success, branch = self._run_git_command(["branch", "--show-current"], repo_path)
        if success:
            info['current_branch'] = branch.strip()
        
        # 获取远程地址
        success, remote = self._run_git_command(["remote", "get-url", "origin"], repo_path)
        if success:
            info['remote_url'] = remote.strip()
        
        return info
    
    def print_header(self, repo_path: Optional[Path] = None):
        """打印头部信息"""
        if repo_path is None:
            repo_path = self.repo_path
        
        repo_info = self.get_repo_info(repo_path)
        
        print("\n" + "="*80)
        print("🔍 Git提交记录查看")
        print("="*80)
        print(f"📂 仓库路径: {repo_info['path']}")
        print(f"📦 仓库名称: {repo_info['name']}")
        
        if 'current_branch' in repo_info:
            print(f"🌿 当前分支: {repo_info['current_branch']}")
        
        if 'remote_url' in repo_info:
            print(f"🔗 远程地址: {repo_info['remote_url']}")
        
        print(f"👤 作者筛选: {self.author if self.author else '全部'}")
        print(f"📅 时间范围: {self.since or '不限'} ~ {self.until or '不限'}")
        print(f"🔢 最大数量: {self.max_count if self.max_count else '不限'}")
        print(f"📋 输出格式: {self.format_type}")
        print("="*80 + "\n")
    
    def format_commit_detailed(self, commit: Dict, index: int) -> str:
        """
        详细格式化提交记录
        
        Args:
            commit: 提交信息字典
            index: 序号
            
        Returns:
            格式化后的字符串
        """
        lines = []
        lines.append(f"\n{'─'*80}")
        lines.append(f"📝 提交 #{index}")
        lines.append(f"{'─'*80}")
        lines.append(f"🔖 哈希: {commit['hash']} ({commit['full_hash']})")
        lines.append(f"👤 作者: {commit['author_name']} <{commit['author_email']}>")
        lines.append(f"📅 日期: {commit['date']}")
        lines.append(f"💬 信息: {commit['message']}")
        
        if commit.get('files'):
            lines.append(f"\n📁 文件变更 ({len(commit['files'])} 个文件):")
            for file_info in commit['files']:
                status = file_info['status']
                status_icon = {
                    'A': '➕',
                    'M': '✏️ ',
                    'D': '🗑️ ',
                    'R': '🔄',
                    'C': '📋'
                }.get(status[0], '📄')
                lines.append(f"   {status_icon} {status:3s} {file_info['path']}")
        
        # 显示代码差异
        if commit.get('diff'):
            lines.append(f"\n📝 代码变更:")
            lines.append("-" * 80)
            lines.append(commit['diff'])
        
        return '\n'.join(lines)
    
    def format_commit_simple(self, commit: Dict) -> str:
        """
        简单格式化提交记录
        
        Args:
            commit: 提交信息字典
            
        Returns:
            格式化后的字符串
        """
        date = commit['date'][:10]  # 只显示日期部分
        message = commit['message']
        if len(message) > 60:
            message = message[:60] + "..."
        
        return f"{commit['hash']} - {date} - {commit['author_name']:20s} - {message}"
    
    def format_commit_oneline(self, commit: Dict) -> str:
        """
        单行格式化提交记录
        
        Args:
            commit: 提交信息字典
            
        Returns:
            格式化后的字符串
        """
        return f"{commit['hash']} {commit['message']}"
    
    def format_commit_json(self, commits: List[Dict]) -> str:
        """
        JSON格式化提交记录
        
        Args:
            commits: 提交记录列表
            
        Returns:
            JSON字符串
        """
        return json.dumps(commits, ensure_ascii=False, indent=2)
    
    def print_commits(self, commits: List[Dict]):
        """
        打印提交记录
        
        Args:
            commits: 提交记录列表
        """
        if not commits:
            print("❌ 未找到符合条件的提交记录\n")
            return
        
        print(f"✅ 找到 {len(commits)} 个提交记录\n")
        
        if self.format_type == 'json':
            print(self.format_commit_json(commits))
        elif self.format_type == 'oneline':
            for commit in commits:
                print(self.format_commit_oneline(commit))
        elif self.format_type == 'simple':
            for commit in commits:
                print(self.format_commit_simple(commit))
        else:  # detailed
            for i, commit in enumerate(commits, 1):
                print(self.format_commit_detailed(commit, i))
        
        # 打印统计信息
        if self.show_stats and self.format_type != 'json':
            self.print_statistics(commits)
    
    def print_statistics(self, commits: List[Dict]):
        """
        打印统计信息
        
        Args:
            commits: 提交记录列表
        """
        print("\n" + "="*80)
        print("📊 统计信息")
        print("="*80)
        
        # 按作者统计
        author_stats = {}
        for commit in commits:
            author = commit['author_name']
            author_stats[author] = author_stats.get(author, 0) + 1
        
        print(f"\n👥 按作者统计:")
        for author, count in sorted(author_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"   {author}: {count} 个提交")
        
        # 按日期统计
        date_stats = {}
        for commit in commits:
            date = commit['date'][:10]
            date_stats[date] = date_stats.get(date, 0) + 1
        
        print(f"\n📅 按日期统计:")
        for date, count in sorted(date_stats.items(), reverse=True):
            print(f"   {date}: {count} 个提交")
        
        # 文件变更统计
        if commits and commits[0].get('files'):
            total_files = sum(len(c.get('files', [])) for c in commits)
            print(f"\n📁 文件变更统计:")
            print(f"   总变更文件数: {total_files}")
            print(f"   平均每次提交: {total_files / len(commits):.1f} 个文件")
        
        print("="*80 + "\n")
    
    def save_to_file(self, commits: List[Dict], output_file: str):
        """
        保存提交记录到文件
        
        Args:
            commits: 提交记录列表
            output_file: 输出文件路径
        """
        try:
            output_path = Path(output_file)
            if not output_path.is_absolute():
                output_path = self.repo_path / output_file
            
            lines = []
            
            # 添加头部信息
            repo_info = self.get_repo_info()
            lines.append("="*80)
            lines.append("Git提交记录")
            lines.append("="*80)
            lines.append(f"仓库: {repo_info['name']}")
            lines.append(f"路径: {repo_info['path']}")
            if 'current_branch' in repo_info:
                lines.append(f"分支: {repo_info['current_branch']}")
            lines.append(f"作者: {self.author if self.author else '全部'}")
            lines.append(f"时间: {self.since or '不限'} ~ {self.until or '不限'}")
            lines.append(f"总计: {len(commits)} 个提交")
            lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append("="*80 + "\n")
            
            # 添加提交记录
            if self.format_type == 'json':
                lines.append(self.format_commit_json(commits))
            else:
                for i, commit in enumerate(commits, 1):
                    if self.format_type == 'oneline':
                        lines.append(self.format_commit_oneline(commit))
                    elif self.format_type == 'simple':
                        lines.append(self.format_commit_simple(commit))
                    else:  # detailed
                        lines.append(self.format_commit_detailed(commit, i))
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            print(f"✅ 提交记录已保存到: {output_path}\n")
            
        except Exception as e:
            print(f"❌ 保存文件失败: {str(e)}\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Git提交记录拉取工具 - 默认只输出到控制台，不创建临时文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查看最近7天的提交（默认）
  python git_commit_log.py
  
  # 查看指定用户的提交
  python git_commit_log.py --author zhangsan@ruijie.com
  
  # 查看指定日期范围的提交
  python git_commit_log.py --since 2025-12-01 --until 2025-12-24
  
  # 简单格式输出
  python git_commit_log.py --format simple
  
  # 单行格式输出（仅哈希和信息）
  python git_commit_log.py --format oneline
  
  # JSON格式输出
  python git_commit_log.py --format json
  
  # 查看所有分支
  python git_commit_log.py --all-branches
  
  # 限制提交数量
  python git_commit_log.py --max-count 10
  
  # 只显示统计信息
  python git_commit_log.py --stat-only
  
  # 保存到文件
  python git_commit_log.py --save --output commits.txt
  
  # 指定仓库路径
  python git_commit_log.py --repo d:/project/myrepo
        """
    )
    
    parser.add_argument(
        '--repo',
        type=str,
        help='Git仓库路径（默认：自动查找当前或父目录的Git仓库）'
    )
    
    parser.add_argument(
        '--scan-repos',
        action='store_true',
        help='扫描多个仓库（在base-dir下查找所有Git仓库）'
    )
    
    parser.add_argument(
        '--base-dir',
        type=str,
        help='扫描的基础目录（配合--scan-repos使用，默认：当前目录）'
    )
    
    parser.add_argument(
        '--scan-depth',
        type=int,
        default=2,
        help='扫描深度（默认：2级子目录）'
    )
    
    parser.add_argument(
        '--author',
        '-a',
        type=str,
        help='提交作者（邮箱或用户名）'
    )
    
    parser.add_argument(
        '--since',
        '-s',
        type=str,
        help='开始日期（格式：YYYY-MM-DD，默认：7天前）'
    )
    
    parser.add_argument(
        '--until',
        '-u',
        type=str,
        help='结束日期（格式：YYYY-MM-DD，默认：今天）'
    )
    
    parser.add_argument(
        '--branch',
        '-b',
        type=str,
        help='指定分支（默认：当前分支）'
    )
    
    parser.add_argument(
        '--all-branches',
        action='store_true',
        help='查看所有分支的提交'
    )
    
    parser.add_argument(
        '--max-count',
        '-n',
        type=int,
        help='最大提交数量'
    )
    
    parser.add_argument(
        '--format',
        '-f',
        type=str,
        default='detailed',
        choices=['detailed', 'simple', 'oneline', 'json'],
        help='输出格式（默认：detailed）'
    )
    
    parser.add_argument(
        '--no-files',
        action='store_true',
        help='不显示文件变更信息'
    )
    
    parser.add_argument(
        '--no-stats',
        action='store_true',
        help='不显示统计信息'
    )
    
    parser.add_argument(
        '--diff',
        action='store_true',
        help='显示代码差异（git diff）'
    )
    
    parser.add_argument(
        '--max-diff-lines',
        type=int,
        default=500,
        help='最大差异行数（默认：500）'
    )
    
    parser.add_argument(
        '--stat-only',
        action='store_true',
        help='只显示统计信息，不显示提交详情'
    )
    
    parser.add_argument(
        '--save',
        action='store_true',
        help='保存输出到文件（需配合--output使用）'
    )
    
    parser.add_argument(
        '--output',
        '-o',
        type=str,
        help='输出文件路径'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='Git命令超时时间（秒，默认：30）'
    )
    
    args = parser.parse_args()
    
    try:
        # 如果没有指定since，默认为7天前
        since = args.since
        if not since:
            since = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        # 创建GitCommitLog实例
        git_log = GitCommitLog(
            repo_path=args.repo,
            author=args.author,
            since=since,
            until=args.until,
            branch=args.branch,
            all_branches=args.all_branches,
            max_count=args.max_count,
            format_type=args.format,
            show_files=not args.no_files,
            show_stats=not args.no_stats,
            show_diff=args.diff,
            max_diff_lines=args.max_diff_lines,
            timeout=args.timeout,
            scan_repos=args.scan_repos,
            base_dir=args.base_dir,
            scan_depth=args.scan_depth
        )
        
        # 扫描模式
        if args.scan_repos:
            if not git_log.repos:
                print("❌ 未找到任何Git仓库\n")
                sys.exit(1)
            
            print(f"✅ 找到 {len(git_log.repos)} 个Git仓库\n")
            
            all_commits = []
            for repo in git_log.repos:
                print(f"{'='*80}")
                print(f"📦 仓库: {repo.name}")
                print(f"{'='*80}\n")
                
                commits = git_log.get_commits(repo)
                if commits:
                    print(f"✅ 找到 {len(commits)} 个提交记录\n")
                    all_commits.extend(commits)
                else:
                    print(f"未找到提交记录\n")
            
            # 统一处理所有提交
            if all_commits:
                # 按时间排序
                all_commits.sort(key=lambda x: x['date'], reverse=True)
                
                if args.stat_only:
                    git_log.print_statistics(all_commits)
                else:
                    # 显示汇总
                    print(f"\n{'='*80}")
                    print(f"📊 汇总：共找到 {len(all_commits)} 个提交记录")
                    print(f"{'='*80}\n")
                    
                    # 打印所有提交
                    if args.format == 'json':
                        print(git_log.format_commit_json(all_commits))
                    else:
                        for i, commit in enumerate(all_commits, 1):
                            if args.format == 'oneline':
                                print(git_log.format_commit_oneline(commit))
                            elif args.format == 'simple':
                                print(f"[{commit['repository']}] {git_log.format_commit_simple(commit)}")
                            else:
                                print(git_log.format_commit_detailed(commit, i))
                    
                    if not args.no_stats:
                        git_log.print_statistics(all_commits)
                
                # 保存文件
                if args.save and args.output:
                    git_log.save_to_file(all_commits, args.output)
            else:
                print("❌ 所有仓库都未找到符合条件的提交记录\n")
        
        # 单仓库模式
        else:
            if not git_log.repo_path:
                print("❌ 未找到Git仓库，请使用 --repo 指定仓库路径或使用 --scan-repos 扫描多个仓库\n")
                sys.exit(1)
            
            # 打印头部信息
            git_log.print_header()
            
            # 获取提交记录
            print("🔍 正在获取提交记录...\n")
            commits = git_log.get_commits()
            
            # 如果只显示统计信息
            if args.stat_only:
                if commits:
                    git_log.print_statistics(commits)
                else:
                    print("❌ 未找到符合条件的提交记录\n")
            else:
                # 打印提交记录
                git_log.print_commits(commits)
            
            # 保存到文件
            if args.save:
                if not args.output:
                    print("⚠️  警告: 需要使用 --output 指定输出文件路径\n")
                elif commits:
                    git_log.save_to_file(commits, args.output)
        
        print("🎉 完成!\n")
        
    except ValueError as e:
        print(f"\n❌ 错误: {str(e)}\n")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n❌ 操作已被用户中断\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
