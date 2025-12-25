# -*- coding: utf-8 -*-
import sys
import os
import mysql.connector
from mysql.connector import errorcode
import argparse
import json
from decimal import Decimal
from datetime import datetime, date
from pathlib import Path

def decimal_date_handler(obj):
    """
    JSON序列化处理器，用于处理Decimal和日期时间类型。
    """
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def load_db_config():
    """
    从配置文件加载数据库配置
    
    Returns:
        dict: 数据库配置字典
    """
    # 获取脚本所在目录的父目录（技能根目录）
    script_dir = Path(__file__).parent
    skill_root = script_dir.parent
    config_file = skill_root / "config" / "db_config.json"
    
    if not config_file.exists():
        print(f"错误: 配置文件不存在: {config_file}", file=sys.stderr)
        print("请复制 config/db_config.json.template 为 config/db_config.json 并填写数据库连接信息", file=sys.stderr)
        sys.exit(1)
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 验证必需的配置项
        required_keys = ['host', 'port', 'user', 'password', 'database']
        missing_keys = [key for key in required_keys if key not in config]
        
        if missing_keys:
            print(f"错误: 配置文件缺少必需项: {', '.join(missing_keys)}", file=sys.stderr)
            sys.exit(1)
        
        return config
    except json.JSONDecodeError as e:
        print(f"错误: 配置文件JSON格式错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"错误: 读取配置文件失败: {e}", file=sys.stderr)
        sys.exit(1)

def execute_query(sql_query):
    """
    Connects to the MySQL database, validates, and executes a SELECT query.

    Args:
        sql_query (str): The SQL query to execute.
    """
    # --- 加载数据库配置 ---
    db_config = load_db_config()

    # --- 安全验证 ---
    # 确保只执行 SELECT 查询语句。
    # .strip() 用于移除字符串首尾的空白字符
    # .lower() 用于将字符串转为小写，以便进行不区分大小写的比较
    if not sql_query.strip().lower().startswith('select'):
        print("错误: 出于安全考虑，只允许执行 SELECT 查询。", file=sys.stderr)
        sys.exit(1)

    connection = None
    cursor = None
    try:
        # --- 连接数据库 ---
        print("正在连接到数据库...")
        connection = mysql.connector.connect(**db_config)
        print("数据库连接成功。")

        # --- 执行查询 ---
        cursor = connection.cursor(dictionary=True) # 使用 dictionary=True 让结果以字典形式返回
        print(f"正在执行查询: {sql_query}")
        cursor.execute(sql_query)

        # --- 获取并打印结果 ---
        results = cursor.fetchall()
        
        if results:
            print("查询结果:")
            # 将结果格式化为 JSON 字符串并打印，确保中文等非 ASCII 字符正常显示
            print(json.dumps(results, indent=4, ensure_ascii=False, default=decimal_date_handler))
        else:
            print("查询未返回任何结果。")

    except mysql.connector.Error as err:
        # --- 错误处理 ---
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("错误: 用户名或密码不正确。", file=sys.stderr)
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("错误: 数据库不存在。", file=sys.stderr)
        else:
            print(f"执行查询时发生错误: {err}", file=sys.stderr)
        sys.exit(1)
    finally:
        # --- 清理资源 ---
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
            print("数据库连接已关闭。")

def main():
    """
    主函数，用于解析命令行参数并调用查询执行函数。
    """
    # 创建一个命令行参数解析器
    parser = argparse.ArgumentParser(description='连接到MySQL数据库并执行一个只读查询。')
    # 添加一个必需的参数 'sql'，用于接收SQL查询语句
    parser.add_argument('sql', help='需要执行的SQL SELECT查询语句。')
    
    # 解析命令行传入的参数
    args = parser.parse_args()
    
    # 调用函数执行查询
    execute_query(args.sql)

if __name__ == "__main__":
    # 确保此脚本作为主程序运行时才执行main()
    main()
