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
        
        # 确保比例参数完全匹配 MultipickBlock 的选项
        if aspect not in ["1:1", "3:4", "4:3", "9:16", "16:9"]:
            aspect = "1:1"  # 如果不匹配，使用默认值
            
        # 使用数组形式传递参数，顺序与 Ultra 节点的 inputValues 对应
        data = {
            "id": "cm3735hi6000bv4ww8b41h712",  # 使用 Ultra 节点的 glif ID
            "inputs": [
                prompt,     # 对应 Enhanced_prompt
                aspect,     # 对应第二个参数（比例）
                str(is_raw).lower()  # 对应第三个参数（模式）
            ]
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
        """从提示词中提取宽高比
        根据 MultipickBlock 的预定义选项严格匹配
        """
        # 严格按照 MultipickBlock 中定义的选项顺序和格式
        valid_ratios = [
            "1:1",   # 默认值
            "3:4",
            "4:3", 
            "9:16",
            "16:9"
        ]
        
        # 将用户输入的比例格式标准化（移除多余空格）
        normalized_prompt = ' ' + prompt.strip() + ' '
        
        # 严格匹配完整的比例格式（确保前后有空格，避免部分匹配）
        for ratio in valid_ratios:
            pattern = f' {ratio} '
            if pattern in normalized_prompt:
                logger.debug(f"[FluxUltra] 提取的比例: {ratio}")
                return ratio
                
        # 未找到有效比例时返回默认值
        logger.debug("[FluxUltra] 未找到有效比例，使用默认比例: 1:1")
        return "1:1"

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
        # 标准化空格
        prompt = ' ' + prompt.strip() + ' '
        
        # 清理比例格式（确保前后有空格，避免误清理）
        for ratio in ["1:1", "3:4", "4:3", "9:16", "16:9"]:
            prompt = prompt.replace(f' {ratio} ', ' ')
            
        # 清理模式标记
        prompt = re.sub(r'--raw', '', prompt, flags=re.IGNORECASE)
        prompt = re.sub(r'--default', '', prompt, flags=re.IGNORECASE)
        
        return prompt.strip()

    def get_help_text(self, **kwargs):
        help_text = "FluxUltra绘图插件使用指南：\n"
        help_text += f"1. 使用 {', '.join(self.drawing_prefixes)} 作为命令前缀\n"
        help_text += "2. 支持的图片比例格式（需要空格分隔）：1:1 (默认值)，3:4 ，4:3 ，9:16 ，16:9 \n"
        help_text += "3. 使用 '--raw' 选择写实照片模式或 '--default' 选择默认模式（默认为default）\n"
        help_text += "4. 示例： FU画图 一只可爱的小猫 3:4 --raw\n"
        return help_text