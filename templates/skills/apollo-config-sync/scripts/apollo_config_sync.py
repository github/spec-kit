#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Apollo配置拉取脚本
从Apollo配置中心拉取最新配置,支持多模块

使用方法:
    # 拉取op-api模块的配置(默认生产环境,仅输出到控制台)
    python apollo_config_sync.py --module op-api
    
    # 拉取并保存配置到文件
    python apollo_config_sync.py --module op-api --save
    
    # 拉取op-order模块的配置
    python apollo_config_sync.py --module op-order
    
    # 指定环境拉取
    python apollo_config_sync.py --module op-api --env test
    
    # 自定义Apollo地址
    python apollo_config_sync.py --module op-api --apollo-url http://custom.apollo.com:8080
    
    # 拉取所有可用的namespace
    python apollo_config_sync.py --module op-api --all
    
    # 不输出到控制台(仅保存文件)
    python apollo_config_sync.py --module op-api --no-print --save
"""

import os
import sys
import json
import argparse
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            os.path.join(os.path.dirname(__file__), 'apollo_sync.log'),
            encoding='utf-8'
        )
    ]
)
logger = logging.getLogger(__name__)


def load_env_config():
    """
    从配置文件加载环境配置
    
    Returns:
        dict: 环境配置字典
    """
    # 获取脚本所在目录的父目录（技能根目录）
    script_dir = Path(__file__).parent
    skill_root = script_dir.parent
    config_file = skill_root / "config" / "apollo_env.json"
    
    if not config_file.exists():
        logger.error(f"配置文件不存在: {config_file}")
        logger.error("请复制 config/apollo_env.json.template 为 config/apollo_env.json 并填写Apollo环境地址")
        sys.exit(1)
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 验证必需的配置项
        if 'environments' not in config:
            logger.error("配置文件缺少 'environments' 配置")
            sys.exit(1)
        
        return config
    except json.JSONDecodeError as e:
        logger.error(f"配置文件JSON格式错误: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"读取配置文件失败: {e}")
        sys.exit(1)


class ApolloConfig:
    """Apollo配置类"""
    
    def __init__(
        self,
        app_id: str,
        cluster: str = 'default',
        env: str = 'pro',
        apollo_url: Optional[str] = None,
        secret: Optional[str] = None
    ):
        """
        初始化Apollo配置
        
        Args:
            app_id: 应用ID/模块名(如: op-api, op-order, op-user等)
            cluster: 集群名称,默认为default
            env: 环境(dev/test/uat/pro),默认为pro
            apollo_url: 自定义Apollo地址,如果指定则覆盖默认配置
            secret: 访问密钥(如果Apollo开启了访问密钥机制)
        """
        self.app_id = app_id
        self.cluster = cluster
        self.env = env
        self.secret = secret
        
        # 从配置文件加载环境配置
        env_config = load_env_config()
        environments = env_config.get('environments', {})
        
        # 如果指定了自定义Apollo地址,使用自定义地址
        if apollo_url:
            self.config_server_url = apollo_url
            self.env_name = f'自定义环境({apollo_url})'
        else:
            if env not in environments:
                available_envs = list(environments.keys())
                raise ValueError(f"不支持的环境: {env}, 支持的环境: {available_envs}")
            self.config_server_url = environments[env]
            self.env_name = f'{env}环境'
        
        # 设置超时时间(从配置文件读取,默认10秒)
        self.timeout = env_config.get('timeout', 10)
        
        # 常用的namespaces(从配置文件读取)
        self.common_namespaces = env_config.get('common_namespaces', [
            'application',
            'bootstrap',
            'datasources.json',
            'application.yml',
            'bootstrap.yml'
        ])
        
        logger.info(f"初始化Apollo配置: 模块={app_id}, 集群={cluster}, 环境={self.env_name}")
        logger.info(f"配置服务地址: {self.config_server_url}")
    
    def _get_headers(self, url: str) -> Dict[str, str]:
        """
        获取请求头(如果配置了访问密钥,需要添加签名)
        
        Args:
            url: 请求的URL
            
        Returns:
            请求头字典
        """
        headers = {
            'Content-Type': 'application/json;charset=UTF-8'
        }
        
        # 如果配置了secret,需要添加签名
        if self.secret:
            import hashlib
            import time
            
            timestamp = str(int(time.time() * 1000))
            # 简化的签名实现(实际使用时需要根据Apollo的签名算法调整)
            path_with_query = url.split(self.config_server_url)[1] if self.config_server_url in url else url
            string_to_sign = f"{timestamp}\n{path_with_query}"
            signature = hashlib.sha1(f"{string_to_sign}{self.secret}".encode()).hexdigest()
            
            headers['Authorization'] = f"Apollo {self.app_id}:{signature}"
            headers['Timestamp'] = timestamp
        
        return headers
    
    def fetch_config_with_cache(
        self,
        namespace: str = 'application',
        client_ip: Optional[str] = None
    ) -> Optional[Dict]:
        """
        通过带缓存的Http接口从Apollo读取配置(适合频率较高的配置拉取)
        
        Args:
            namespace: namespace名称
            client_ip: 客户端IP(用于灰度发布)
            
        Returns:
            配置字典,失败返回None
        """
        url = f"{self.config_server_url}/configfiles/json/{self.app_id}/{self.cluster}/{namespace}"
        
        if client_ip:
            url += f"?ip={client_ip}"
        
        try:
            logger.info(f"拉取配置(带缓存): namespace={namespace}")
            headers = self._get_headers(url)
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                config = response.json()
                logger.info(f"成功拉取配置: namespace={namespace}, 配置项数量={len(config)}")
                return config
            elif response.status_code == 404:
                logger.warning(f"Namespace不存在或未发布: {namespace}")
                return None
            else:
                logger.error(f"拉取配置失败: status_code={response.status_code}, response={response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"请求超时: namespace={namespace}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: namespace={namespace}, error={e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"解析JSON失败: namespace={namespace}, error={e}")
            return None
    
    def fetch_config_without_cache(
        self,
        namespace: str = 'application',
        release_key: Optional[str] = None,
        client_ip: Optional[str] = None
    ) -> Optional[Dict]:
        """
        通过不带缓存的Http接口从Apollo读取配置(实时获取,适合配合推送通知使用)
        
        Args:
            namespace: namespace名称
            release_key: 上一次的releaseKey,用于版本比较
            client_ip: 客户端IP(用于灰度发布)
            
        Returns:
            包含配置和元信息的字典,失败返回None
        """
        url = f"{self.config_server_url}/configs/{self.app_id}/{self.cluster}/{namespace}"
        
        params = {}
        if release_key:
            params['releaseKey'] = release_key
        if client_ip:
            params['ip'] = client_ip
        
        try:
            logger.info(f"拉取配置(不带缓存): namespace={namespace}")
            headers = self._get_headers(url)
            response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                config = data.get('configurations', {})
                logger.info(f"成功拉取配置: namespace={namespace}, 配置项数量={len(config)}, releaseKey={data.get('releaseKey')}")
                return data
            elif response.status_code == 304:
                logger.info(f"配置无变化: namespace={namespace}")
                return None
            elif response.status_code == 404:
                logger.warning(f"Namespace不存在或未发布: {namespace}")
                return None
            else:
                logger.error(f"拉取配置失败: status_code={response.status_code}, response={response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"请求超时: namespace={namespace}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: namespace={namespace}, error={e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"解析JSON失败: namespace={namespace}, error={e}")
            return None
    
    def list_all_namespaces(self) -> List[str]:
        """
        列出所有可用的namespaces(尝试拉取常用的namespace)
        
        Returns:
            可用的namespace列表
        """
        available_namespaces = []
        
        logger.info("检查可用的namespaces...")
        for namespace in self.common_namespaces:
            config = self.fetch_config_with_cache(namespace)
            if config is not None:
                available_namespaces.append(namespace)
                logger.info(f"  ✓ {namespace}")
            else:
                logger.debug(f"  ✗ {namespace} (不可用)")
        
        return available_namespaces
    
    def print_config_to_console(
        self,
        config: Dict,
        namespace: str,
        format_type: str = 'json'
    ):
        """
        在控制台打印配置内容
        
        Args:
            config: 配置字典
            namespace: namespace名称
            format_type: 输出格式(json/yaml/raw)
        """
        # 设置控制台编码为UTF-8(Windows兼容)
        import sys
        if sys.platform == 'win32':
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        
        print(f"\n{'='*80}")
        print(f"模块: {self.app_id}")
        print(f"环境: {self.env_name}")
        print(f"Namespace: {namespace}")
        print(f"配置项数量: {len(config)}")
        print(f"{'='*80}\n")
        
        if format_type == 'json':
            # JSON格式输出
            print(json.dumps(config, ensure_ascii=False, indent=2))
        elif format_type == 'yaml':
            # YAML格式输出
            try:
                import yaml
                print(yaml.dump(config, allow_unicode=True, default_flow_style=False))
            except ImportError:
                logger.warning("未安装pyyaml库,使用JSON格式输出")
                print(json.dumps(config, ensure_ascii=False, indent=2))
        elif format_type == 'raw':
            # 原始格式输出(如果配置是YAML content字段)
            if 'content' in config and len(config) == 1:
                # 移除特殊字符以避免编码问题
                content = config['content']
                # 替换可能导致编码问题的特殊字符
                content = content.replace('\u26a0', '!')  # 替换警告符号
                print(content)
            else:
                # 否则使用JSON格式
                print(json.dumps(config, ensure_ascii=False, indent=2))
        else:
            # 默认JSON格式
            print(json.dumps(config, ensure_ascii=False, indent=2))
        
        print(f"\n{'='*80}\n")
    
    def save_config_to_file(
        self,
        config: Dict,
        namespace: str,
        output_dir: Optional[str] = None,
        save_timestamped: bool = False
    ) -> str:
        """
        保存配置到文件
        
        Args:
            config: 配置字典
            namespace: namespace名称
            output_dir: 输出目录,默认为当前脚本目录下的apollo_configs
            save_timestamped: 是否保存带时间戳的文件,默认为False(只保存latest)
            
        Returns:
            保存的文件路径
        """
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(__file__), 'apollo_configs')
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 准备保存的数据
        save_data = {
            'meta': {
                'appId': self.app_id,
                'cluster': self.cluster,
                'namespace': namespace,
                'env': self.env,
                'env_name': self.env_name,
                'fetch_time': datetime.now().isoformat(),
                'config_server_url': self.config_server_url
            },
            'configurations': config
        }
        
        # 最新配置文件名(不带时间戳)
        safe_namespace = namespace.replace('.', '_').replace('/', '_')
        latest_filename = f"{self.env}_{self.app_id}_{safe_namespace}_latest.json"
        latest_filepath = os.path.join(output_dir, latest_filename)
        
        # 保存最新配置
        with open(latest_filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"配置已保存到: {latest_filepath}")
        
        # 可选:保存带时间戳的副本
        if save_timestamped:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.env}_{self.app_id}_{safe_namespace}_{timestamp}.json"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"带时间戳的配置已保存到: {filepath}")
            return filepath
        
        return latest_filepath


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='从Apollo配置中心拉取配置(支持多模块)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 拉取op-api模块的配置(默认生产环境,默认bootstrap.yml,仅输出到控制台)
  python apollo_config_sync.py --module op-api
  
  # 拉取并保存配置到文件
  python apollo_config_sync.py --module op-api --save
  
  # 保存配置并生成带时间戳的副本
  python apollo_config_sync.py --module op-api --save --save-timestamped
  
  # 拉取op-order模块的配置
  python apollo_config_sync.py --module op-order
  
  # 拉取op-user模块的测试环境配置
  python apollo_config_sync.py --module op-user --env test
  
  # 指定namespace
  python apollo_config_sync.py --module op-api --namespace application
  
  # 拉取所有可用的namespace
  python apollo_config_sync.py --module op-api --all
  
  # 自定义Apollo地址
  python apollo_config_sync.py --module op-api --apollo-url http://custom.apollo.com:8080
  
  # 不输出到控制台(仅保存文件)
  python apollo_config_sync.py --module op-api --no-print --save
  
  # 指定输出格式(json/yaml/raw)
  python apollo_config_sync.py --module op-api --format yaml
        """
    )
    
    parser.add_argument(
        '--module',
        '-m',
        type=str,
        required=True,
        help='模块名称 (必填,如: op-api, op-order, op-user, op-biz等)'
    )
    
    parser.add_argument(
        '--env',
        '-e',
        type=str,
        default='pro',
        choices=['dev', 'test', 'uat', 'pro'],
        help='环境 (默认: pro 生产环境)'
    )
    
    parser.add_argument(
        '--apollo-url',
        type=str,
        help='自定义Apollo服务器地址 (如: http://apollo.example.com:8080)'
    )
    
    parser.add_argument(
        '--cluster',
        type=str,
        default='default',
        help='集群名称 (默认: default)'
    )
    
    parser.add_argument(
        '--namespace',
        '-n',
        type=str,
        default='bootstrap.yml',
        help='Namespace名称 (默认: bootstrap.yml)'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='拉取所有可用的namespaces'
    )
    
    parser.add_argument(
        '--output-dir',
        '-o',
        type=str,
        help='配置文件输出目录 (默认: ./apollo_configs)'
    )
    
    parser.add_argument(
        '--no-print',
        action='store_true',
        help='不在控制台输出配置内容(仅保存到文件)'
    )
    
    parser.add_argument(
        '--format',
        '-f',
        type=str,
        default='json',
        choices=['json', 'yaml', 'raw'],
        help='控制台输出格式 (默认: json, raw适用于YAML配置文件)'
    )
    
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='不保存到文件(仅输出到控制台)'
    )
    
    parser.add_argument(
        '--save',
        action='store_true',
        help='保存配置到文件(默认不保存)'
    )
    
    parser.add_argument(
        '--save-timestamped',
        action='store_true',
        help='保存带时间戳的配置文件副本(需要配合--save使用)'
    )
    
    parser.add_argument(
        '--secret',
        type=str,
        help='访问密钥(如果Apollo开启了访问密钥机制)'
    )
    
    parser.add_argument(
        '--with-cache',
        action='store_true',
        help='使用带缓存的接口(默认使用不带缓存的接口)'
    )
    
    args = parser.parse_args()
    
    try:
        # 创建Apollo配置实例
        apollo = ApolloConfig(
            app_id=args.module,
            cluster=args.cluster,
            env=args.env,
            apollo_url=args.apollo_url,
            secret=args.secret
        )
        
        # 确定要拉取的namespaces
        if args.all:
            namespaces = apollo.list_all_namespaces()
            if not namespaces:
                logger.error("未找到任何可用的namespace")
                return 1
            logger.info(f"找到 {len(namespaces)} 个可用的namespace")
        else:
            namespaces = [args.namespace]
        
        # 拉取配置
        success_count = 0
        for namespace in namespaces:
            logger.info(f"\n{'='*60}")
            logger.info(f"开始拉取: {namespace}")
            logger.info(f"{'='*60}")
            
            # 拉取配置
            if args.with_cache:
                config = apollo.fetch_config_with_cache(namespace)
            else:
                result = apollo.fetch_config_without_cache(namespace)
                config = result.get('configurations') if result else None
            
            if config:
                # 输出到控制台
                if not args.no_print:
                    apollo.print_config_to_console(config, namespace, args.format)
                
                # 保存到文件(只有明确指定--save时才保存)
                if args.save:
                    apollo.save_config_to_file(
                        config, 
                        namespace, 
                        args.output_dir,
                        save_timestamped=args.save_timestamped
                    )
                
                success_count += 1
            else:
                logger.warning(f"跳过: {namespace}")
        
        # 输出总结
        logger.info(f"\n{'='*60}")
        logger.info(f"拉取完成: 成功 {success_count}/{len(namespaces)}")
        logger.info(f"{'='*60}")
        
        return 0 if success_count > 0 else 1
        
    except Exception as e:
        logger.error(f"执行失败: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
