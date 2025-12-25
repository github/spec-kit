#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
技能创建脚本

自动创建符合标准的技能目录结构和基础文件

使用方法:
    python create_skill.py --name skill-name --description "技能描述"
    
示例:
    python create_skill.py --name log-analyzer --description "日志分析工具"
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path
import shutil

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 技能根目录
SKILLS_ROOT = Path(__file__).parent.parent.parent.absolute()
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def validate_skill_name(name):
    """
    验证技能名称是否符合规范
    
    Args:
        name: 技能名称
        
    Returns:
        bool: 是否有效
    """
    # 检查是否为kebab-case格式
    if not name:
        return False
    
    # 只能包含小写字母、数字和连字符
    if not all(c.islower() or c.isdigit() or c == '-' for c in name):
        return False
    
    # 不能以连字符开头或结尾
    if name.startswith('-') or name.endswith('-'):
        return False
    
    # 不能有连续的连字符
    if '--' in name:
        return False
    
    return True


def create_skill_directory(skill_name):
    """
    创建技能目录结构
    
    Args:
        skill_name: 技能名称
        
    Returns:
        Path: 技能根目录路径
    """
    skill_path = SKILLS_ROOT / skill_name
    
    # 检查目录是否已存在
    if skill_path.exists():
        raise FileExistsError(f"技能目录已存在: {skill_path}")
    
    # 创建主目录
    skill_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"✓ 创建技能目录: {skill_path}")
    
    # 创建子目录
    subdirs = ['templates', 'scripts', 'config']
    for subdir in subdirs:
        subdir_path = skill_path / subdir
        subdir_path.mkdir(exist_ok=True)
        logger.info(f"✓ 创建子目录: {subdir}")
    
    return skill_path


def create_skill_md(skill_path, skill_name, description):
    """
    创建 SKILL.md 文件
    
    Args:
        skill_path: 技能目录路径
        skill_name: 技能名称
        description: 技能描述
    """
    template_path = TEMPLATES_DIR / "SKILL.md.template"
    
    if not template_path.exists():
        logger.warning(f"模板文件不存在: {template_path}，使用基础模板")
        content = f"""---
name: {skill_name}
description: {description}
license: MIT
---

# {skill_name.replace('-', ' ').title()}

## 技能用途

{description}

## 使用指南

待完善...

## 注意事项

- Windows环境，使用PowerShell命令
- 确保所有路径使用绝对路径
"""
    else:
        # 读取模板
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换占位符
        content = content.replace('{SKILL_NAME}', skill_name)
        content = content.replace('{技能简短描述。说明用途和触发场景。}', description)
        content = content.replace('{技能标题}', skill_name.replace('-', ' ').title())
    
    # 写入文件
    output_path = skill_path / "SKILL.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"✓ 创建 SKILL.md")


def create_readme(skill_path, skill_name, description):
    """
    创建 README.md 文件
    
    Args:
        skill_path: 技能目录路径
        skill_name: 技能名称
        description: 技能描述
    """
    template_path = TEMPLATES_DIR / "README.md.template"
    
    if not template_path.exists():
        logger.warning(f"模板文件不存在: {template_path}，使用基础模板")
        content = f"""# {skill_name.replace('-', ' ').title()}

> {description}

## 快速开始

待完善...

## 目录结构

```
{skill_name}/
├── SKILL.md
├── LICENSE.txt
├── README.md
├── templates/
├── scripts/
└── config/
```

## 许可证

MIT License
"""
    else:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = content.replace('{技能名称}', skill_name.replace('-', ' ').title())
        content = content.replace('{技能的一句话描述}', description)
        content = content.replace('{SKILL_NAME}', skill_name)
    
    output_path = skill_path / "README.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"✓ 创建 README.md")


def create_license(skill_path):
    """
    创建 LICENSE.txt 文件
    
    Args:
        skill_path: 技能目录路径
    """
    template_path = TEMPLATES_DIR / "LICENSE.txt.template"
    output_path = skill_path / "LICENSE.txt"
    
    if template_path.exists():
        shutil.copy(template_path, output_path)
    else:
        # 默认MIT许可证
        content = """MIT License

Copyright (c) 2025 ECP Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    logger.info(f"✓ 创建 LICENSE.txt")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='创建新的AI技能目录结构和基础文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python create_skill.py --name log-analyzer --description "日志分析工具"
  python create_skill.py --name api-tester --description "API接口测试工具"
        """
    )
    
    parser.add_argument(
        '--name',
        type=str,
        required=True,
        help='技能名称（kebab-case格式，如: log-analyzer）'
    )
    
    parser.add_argument(
        '--description',
        type=str,
        required=True,
        help='技能描述（简短说明技能用途）'
    )
    
    args = parser.parse_args()
    
    try:
        # 验证技能名称
        if not validate_skill_name(args.name):
            logger.error("❌ 技能名称格式不正确")
            logger.error("   要求: kebab-case格式（全小写，单词用连字符分隔）")
            logger.error("   示例: log-analyzer, database-query, api-tester")
            sys.exit(1)
        
        logger.info(f"开始创建技能: {args.name}")
        logger.info(f"技能描述: {args.description}")
        logger.info("")
        
        # 创建目录结构
        skill_path = create_skill_directory(args.name)
        
        # 创建文件
        create_skill_md(skill_path, args.name, args.description)
        create_readme(skill_path, args.name, args.description)
        create_license(skill_path)
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ 技能创建完成！")
        logger.info("=" * 60)
        logger.info(f"技能路径: {skill_path}")
        logger.info("")
        logger.info("接下来的步骤:")
        logger.info("1. 编辑 SKILL.md 完善技能提示词")
        logger.info("2. 将相关脚本复制到 scripts/ 目录")
        logger.info("3. 创建配置文件到 config/ 目录")
        logger.info("4. 添加模板文件到 templates/ 目录")
        logger.info("5. 完善 README.md 文档")
        logger.info("")
        logger.info(f"快速导航:")
        logger.info(f"  cd {skill_path}")
        
    except FileExistsError as e:
        logger.error(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 创建技能失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
