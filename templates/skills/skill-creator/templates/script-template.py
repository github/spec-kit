#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
{脚本名称}

{脚本描述}

使用方法:
    python {SCRIPT_NAME}.py --param value
    
示例:
    python {SCRIPT_NAME}.py --input data.txt --output result.txt
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            os.path.join(os.path.dirname(__file__), 'script.log'),
            encoding='utf-8'
        )
    ]
)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    # 创建参数解析器
    parser = argparse.ArgumentParser(
        description='{脚本描述}',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # 添加参数
    parser.add_argument(
        '--param1',
        type=str,
        required=True,
        help='参数1的说明'
    )
    
    parser.add_argument(
        '--param2',
        type=str,
        default='default_value',
        help='参数2的说明（可选）'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='显示详细输出'
    )
    
    # 解析参数
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    try:
        logger.info("开始执行...")
        logger.info(f"参数1: {args.param1}")
        logger.info(f"参数2: {args.param2}")
        
        # 主要逻辑
        result = process_data(args.param1, args.param2)
        
        logger.info(f"执行完成: {result}")
        
    except Exception as e:
        logger.error(f"执行失败: {e}", exc_info=True)
        sys.exit(1)


def process_data(param1, param2):
    """
    处理数据的主要函数
    
    Args:
        param1: 参数1
        param2: 参数2
        
    Returns:
        处理结果
    """
    # 实现你的逻辑
    result = f"Processed {param1} with {param2}"
    return result


if __name__ == '__main__':
    main()
