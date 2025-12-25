#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书云文档读取工具
用于通过飞书开放API读取飞书云文档内容
"""

import requests
import json
import sys
import os
from typing import Optional, Dict, List

# 设置Windows控制台输出编码为UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class FeishuDocReader:
    """飞书文档读取器"""
    
    def __init__(self, app_id: str, app_secret: str):
        """
        初始化飞书文档读取器
        
        Args:
            app_id: 飞书应用ID
            app_secret: 飞书应用密钥
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.tenant_access_token = None
        self.base_url = "https://open.feishu.cn/open-apis"
        
    def get_tenant_access_token(self) -> bool:
        """
        获取tenant_access_token
        
        Returns:
            bool: 是否成功获取token
        """
        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            result = response.json()
            
            if result.get("code") == 0:
                self.tenant_access_token = result.get("tenant_access_token")
                print("✓ 鉴权成功")
                return True
            else:
                print(f"✗ 鉴权失败: {result.get('msg')}")
                return False
        except Exception as e:
            print(f"✗ 鉴权请求失败: {str(e)}")
            return False
    
    def get_wiki_node_info(self, space_id: str, node_token: str = None) -> Optional[Dict]:
        """
        获取Wiki节点信息
        
        Args:
            space_id: Wiki空间ID
            node_token: 节点token，如果为空则获取根节点
            
        Returns:
            Optional[Dict]: 节点信息
        """
        if node_token:
            url = f"{self.base_url}/wiki/v2/spaces/{space_id}/nodes/{node_token}"
        else:
            # 获取空间信息
            url = f"{self.base_url}/wiki/v2/spaces/{space_id}"
        
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        try:
            response = requests.get(url, headers=headers)
            result = response.json()
            
            if result.get("code") == 0:
                return result.get("data")
            else:
                print(f"✗ 获取Wiki节点信息失败: {result.get('msg')}")
                return None
        except Exception as e:
            print(f"✗ 请求Wiki节点信息失败: {str(e)}")
            return None
    
    def get_document_raw_content(self, doc_token: str) -> Optional[str]:
        """
        获取文档原始内容（新版docx格式）
        
        Args:
            doc_token: 文档token
            
        Returns:
            Optional[str]: 文档内容的JSON字符串
        """
        url = f"{self.base_url}/docx/v1/documents/{doc_token}/raw_content"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        try:
            response = requests.get(url, headers=headers)
            result = response.json()
            
            if result.get("code") == 0:
                return json.dumps(result.get("data"), ensure_ascii=False, indent=2)
            else:
                print(f"✗ 获取文档内容失败: {result.get('msg')}")
                return None
        except Exception as e:
            print(f"✗ 请求文档内容失败: {str(e)}")
            return None
    
    def list_document_blocks(self, doc_token: str, page_size: int = 500) -> Optional[List[Dict]]:
        """
        获取文档所有块内容（新版docx格式）
        
        Args:
            doc_token: 文档token
            page_size: 每页数量
            
        Returns:
            Optional[List[Dict]]: 文档块列表
        """
        url = f"{self.base_url}/docx/v1/documents/{doc_token}/blocks"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        all_blocks = []
        page_token = None
        
        try:
            while True:
                params = {
                    "page_size": page_size,
                    "document_revision_id": -1  # -1表示获取最新版本
                }
                if page_token:
                    params["page_token"] = page_token
                
                response = requests.get(url, headers=headers, params=params)
                result = response.json()
                
                if result.get("code") != 0:
                    print(f"✗ 获取文档块失败: {result.get('msg')}")
                    return None
                
                data = result.get("data", {})
                blocks = data.get("items", [])
                all_blocks.extend(blocks)
                
                # 检查是否还有更多数据
                if not data.get("has_more", False):
                    break
                    
                page_token = data.get("page_token")
            
            return all_blocks
        except Exception as e:
            print(f"✗ 请求文档块失败: {str(e)}")
            return None
    
    def extract_text_from_blocks(self, blocks: List[Dict]) -> str:
        """
        从文档块中提取纯文本内容
        
        Args:
            blocks: 文档块列表
            
        Returns:
            str: 提取的文本内容
        """
        text_parts = []
        
        for block in blocks:
            block_type = block.get("block_type")
            
            # 处理页面标题（block_type 1）
            if block_type == 1 and "page" in block:
                elements = block.get("page", {}).get("elements", [])
                for element in elements:
                    text_run = element.get("text_run", {})
                    content = text_run.get("content", "")
                    if content:
                        text_parts.append(f"\n# {content}\n")
            
            # 处理普通文本段落（block_type 2）
            elif block_type == 2 and "text" in block:
                elements = block.get("text", {}).get("elements", [])
                para_text = []
                for element in elements:
                    text_run = element.get("text_run", {})
                    content = text_run.get("content", "")
                    if content:
                        para_text.append(content)
                if para_text:
                    text_parts.append(''.join(para_text))
            
            # 处理一级标题（block_type 3）
            elif block_type == 3 and "heading1" in block:
                elements = block.get("heading1", {}).get("elements", [])
                heading_text = []
                for element in elements:
                    text_run = element.get("text_run", {})
                    content = text_run.get("content", "")
                    if content:
                        heading_text.append(content)
                if heading_text:
                    text_parts.append(f"\n## {''.join(heading_text)}\n")
            
            # 处理二级标题（block_type 4）
            elif block_type == 4 and "heading2" in block:
                elements = block.get("heading2", {}).get("elements", [])
                heading_text = []
                for element in elements:
                    text_run = element.get("text_run", {})
                    content = text_run.get("content", "")
                    if content:
                        heading_text.append(content)
                if heading_text:
                    text_parts.append(f"\n### {''.join(heading_text)}\n")
            
            # 处理三级标题（block_type 5）
            elif block_type == 5 and "heading3" in block:
                elements = block.get("heading3", {}).get("elements", [])
                heading_text = []
                for element in elements:
                    text_run = element.get("text_run", {})
                    content = text_run.get("content", "")
                    if content:
                        heading_text.append(content)
                if heading_text:
                    text_parts.append(f"\n#### {''.join(heading_text)}\n")
            
            # 处理代码块（block_type 17）
            elif block_type == 17 and "code" in block:
                code_data = block.get("code", {})
                elements = code_data.get("elements", [])
                code_text = []
                for element in elements:
                    text_run = element.get("text_run", {})
                    content = text_run.get("content", "")
                    if content:
                        code_text.append(content)
                if code_text:
                    language = code_data.get("style", {}).get("language", "")
                    text_parts.append(f"\n```{language}\n{''.join(code_text)}\n```\n")
            
            # 处理有序列表（block_type 6）
            elif block_type == 6 and "ordered" in block:
                elements = block.get("ordered", {}).get("elements", [])
                list_text = []
                for element in elements:
                    text_run = element.get("text_run", {})
                    content = text_run.get("content", "")
                    if content:
                        list_text.append(content)
                if list_text:
                    text_parts.append(f"  * {''.join(list_text)}")
            
            # 处理无序列表（block_type 7）
            elif block_type == 7 and "bullet" in block:
                elements = block.get("bullet", {}).get("elements", [])
                list_text = []
                for element in elements:
                    text_run = element.get("text_run", {})
                    content = text_run.get("content", "")
                    if content:
                        list_text.append(content)
                if list_text:
                    text_parts.append(f"  - {''.join(list_text)}")
            
            # 处理图片（block_type 27）
            elif block_type == 27 and "image" in block:
                text_parts.append("[图片]")
            
            # 处理项目卡片（block_type 54）
            elif block_type == 54 and "project" in block:
                project_data = block.get("project", {})
                title = project_data.get("title", "")
                url = project_data.get("url", "")
                if title:
                    text_parts.append(f"\n[项目卡片] {title}")
                    if url:
                        text_parts.append(f"链接: {url}")
        
        return '\n'.join(text_parts)
    
    def read_document(self, doc_token: str, output_format: str = "text", is_wiki: bool = False) -> Optional[str]:
        """
        读取飞书文档
        
        Args:
            doc_token: 文档token (从URL中提取，如 https://example.feishu.cn/docx/xxxxx 中的 xxxxx)
                      或Wiki space_id (从URL中提取，如 https://example.feishu.cn/wiki/xxxxx 中的 xxxxx)
            output_format: 输出格式 ('text' 或 'json')
            is_wiki: 是否为Wiki文档
            
        Returns:
            Optional[str]: 文档内容
        """
        print(f"正在读取{'Wiki' if is_wiki else '文档'} {doc_token}...")
        
        # 获取访问令牌
        if not self.tenant_access_token:
            if not self.get_tenant_access_token():
                return None
        
        # 如果是Wiki，先获取Wiki信息和绑定的文档token
        actual_doc_token = doc_token
        if is_wiki:
            print("检测到Wiki链接，正在获取Wiki节点信息...")
            wiki_info = self.get_wiki_node_info(doc_token)
            if wiki_info is None:
                print("提示：Wiki访问需要额外权限，请确保：")
                print("  1. 已申请 wiki:wiki:readonly 权限")
                print("  2. 应用已被添加到Wiki空间（需Wiki管理员授权）")
                return None
            
            # 从Wiki信息中获取绑定的文档token
            space_info = wiki_info.get("space", {})
            obj_token = space_info.get("obj_token")
            obj_type = space_info.get("obj_type")
            
            if not obj_token:
                print("✗ 无法获取Wiki绑定的文档token")
                return None
            
            print(f"✓ Wiki绑定文档类型: {obj_type}")
            print(f"✓ 文档token: {obj_token}")
            actual_doc_token = obj_token
        
        # 获取文档块内容
        blocks = self.list_document_blocks(actual_doc_token)
        if blocks is None:
            if not is_wiki:
                print("提示：文档访问需要权限，请确保：")
                print("  1. 已申请 drive:drive 和 docx:document 权限")
                print("  2. 应用已被添加到文档（需文档所有者授权）")
            return None
        
        print(f"✓ 成功获取 {len(blocks)} 个文档块")
        
        # 根据输出格式处理
        if output_format == "json":
            return json.dumps(blocks, ensure_ascii=False, indent=2)
        else:
            # 提取纯文本
            text_content = self.extract_text_from_blocks(blocks)
            return text_content


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python feishu_doc_reader.py <doc_token_or_url> [output_format]")
        print("  doc_token_or_url: 文档token或完整URL")
        print("  output_format: 输出格式 (text/json，默认为text)")
        print("\n支持的URL格式:")
        print("  - 新版文档: https://xxx.feishu.cn/docx/doxcnXXXXX")
        print("  - Wiki文档: https://xxx.feishu.cn/wiki/YgXyXXXXX")
        print("\n示例:")
        print("  python feishu_doc_reader.py doxcnABCDEFGHIJKLMN")
        print("  python feishu_doc_reader.py https://xxx.feishu.cn/docx/doxcnABCDEFGHIJKLMN")
        print("  python feishu_doc_reader.py https://xxx.feishu.cn/wiki/YgXyXXXXX")
        sys.exit(1)
    
    input_str = sys.argv[1]
    output_format = sys.argv[2] if len(sys.argv) > 2 else "text"
    
    # 判断是URL还是token
    is_wiki = False
    doc_token = input_str
    
    if "feishu.cn" in input_str or "larksuite.com" in input_str:
        # 是完整URL，需要提取token
        if "/wiki/" in input_str:
            is_wiki = True
            # 提取wiki token
            parts = input_str.split("/wiki/")
            if len(parts) > 1:
                doc_token = parts[1].split("?")[0].split("#")[0]
        elif "/docx/" in input_str:
            # 提取docx token
            parts = input_str.split("/docx/")
            if len(parts) > 1:
                doc_token = parts[1].split("?")[0].split("#")[0]
        print(f"从URL提取token: {doc_token}")
    else:
        # 直接是token，判断是否为wiki (wiki token通常较短且不以doxcn开头)
        if not doc_token.startswith("doxcn") and len(doc_token) < 30:
            print("提示：如果这是Wiki链接，请提供完整URL或确认token正确")
    
    # 从配置文件读取应用凭证
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.json")
    
    if not os.path.exists(config_path):
        print("✗ 配置文件不存在，请先创建 config/config.json 文件")
        print("配置文件格式:")
        print(json.dumps({
            "app_id": "cli_xxxxxxxxx",
            "app_secret": "xxxxxxxxxxxxx"
        }, indent=2))
        sys.exit(1)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    app_id = config.get("app_id")
    app_secret = config.get("app_secret")
    
    if not app_id or not app_secret:
        print("✗ 配置文件中缺少 app_id 或 app_secret")
        sys.exit(1)
    
    # 创建读取器并读取文档
    reader = FeishuDocReader(app_id, app_secret)
    content = reader.read_document(doc_token, output_format, is_wiki)
    
    if content:
        print("\n" + "="*80)
        print("文档内容:")
        print("="*80 + "\n")
        print(content)
    else:
        print("✗ 读取文档失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
