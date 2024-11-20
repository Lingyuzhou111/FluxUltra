import os
import re
import json
import requests
from io import BytesIO

import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from plugins import *
from config import conf

@plugins.register(
    name="FluxUltra",
    desire_priority=200,
    hidden=False,
    desc="A plugin for generating images using Glif API",
    version="1.0",
    author="Lingyuzhou",
)
class FluxUltra(Plugin):
    def __init__(self):
        super().__init__()
        try:
            conf = super().load_config()
            if not conf:
                raise Exception("配置未找到")
            
            # 从配置文件只加载API token
            self.api_token = conf.get("api_token")
            if not self.api_token:
                raise Exception("在配置中未找到API令牌")
            
            self.drawing_prefixes = ["FU画图"]
            
            # 注册消息处理器
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
            
            logger.info("[FluxUltra] 插件初始化成功")
            
        except Exception as e:
            logger.error(f"[FluxUltra] 初始化失败: {e}")
            raise e

    def on_handle_context(self, e_context: EventContext):
        if e_context["context"].type != ContextType.TEXT:
            return
            
        content = e_context["context"].content
        if not content.startswith(tuple(self.drawing_prefixes)):
            return
            
        logger.debug(f"[FluxUltra] 收到消息: {content}")
        
        try:
            # 移除前缀
            for prefix in self.drawing_prefixes:
                if content.startswith(prefix):
                    content = content[len(prefix):].strip()
                    break
                    
            # 解析用户输入
            aspect = self.extract_aspect_ratio(content)
            is_raw = self.extract_mode(content)
            clean_prompt = self.clean_prompt_string(content)
            
            # 调用Glif API生成图片
            image_url = self.generate_image(clean_prompt, aspect, is_raw)
            
            if image_url:
                # 直接返回图片URL
                reply = Reply(ReplyType.TEXT, f"图片生成成功，URL: {image_url}")
            else:
                reply = Reply(ReplyType.ERROR, "生成图片失败")
                
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            
        except Exception as e:
            logger.error(f"[FluxUltra] 发生错误: {e}")
            reply = Reply(ReplyType.ERROR, f"发生错误: {str(e)}")
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS

    def generate_image(self, prompt: str, aspect: str, is_raw: bool) -> str:
        """调用Glif API生成图片"""
        logger.debug(f"[FluxUltra] 生成图片参数: prompt='{prompt}', 比例={aspect}, is_raw={is_raw}")
        
        url = "https://simple-api.glif.app"
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            "id": "cm3o6bpn000117v6qbl4frhsu",
            "inputs": [prompt, aspect, str(is_raw).lower()]
        }
        
        try:
            logger.debug(f"[FluxUltra] 发送API请求: {json.dumps(data, ensure_ascii=False)}")
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            if 'error' in result:
                raise Exception(result['error'])
            
            logger.debug(f"[FluxUltra] API响应成功")
            return result['output']
            
        except Exception as e:
            logger.error(f"[FluxUltra] API请求失败: {e}")
            raise

    def extract_aspect_ratio(self, prompt: str) -> str:
        """从提示词中提取宽高比"""
        match = re.search(r'--ar (\d+:\d+)', prompt)
        ratio = match.group(1) if match else "1:1"
        logger.debug(f"[FluxUltra] 提取的比例: {ratio}")
        return ratio

    def extract_mode(self, prompt: str) -> bool:
        """从提示词中提取模式参数
        --raw 对应参数 true
        --default 对应参数 false
        默认为 false (default模式)
        """
        if "--raw" in prompt.lower():
            return True  # --raw 对应 true
        if "--default" in prompt.lower():
            return False  # --default 对应 false
        return False  # 默认为 false (default模式)

    def clean_prompt_string(self, prompt: str) -> str:
        """清理提示词中的参数标记"""
        prompt = re.sub(r'--ar \d+:\d+', '', prompt)
        prompt = re.sub(r'--raw', '', prompt, flags=re.IGNORECASE)
        prompt = re.sub(r'--default', '', prompt, flags=re.IGNORECASE)
        return prompt.strip()

    def get_help_text(self, **kwargs):
        help_text = "FluxUltra绘图插件使用指南：\n"
        help_text += f"1. 使用 {', '.join(self.drawing_prefixes)} 作为命令前缀\n"
        help_text += "2. 使用 '--ar' 指定图片比例，例如：--ar 16:9（支持的比例：1:1、16:9、9:16、4:3、3:4，默认为1:1）\n"
        help_text += "3. 使用 '--raw' 选择写实照片模式，'--default' 或留空选择默认模式\n"
        help_text += "4. 示例：FU画图 一只机甲熊猫 --ar 16:9 --raw\n"
        return help_text
