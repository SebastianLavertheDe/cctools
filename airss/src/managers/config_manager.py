"""
配置管理器
"""

import os
import re
import sys
import yaml
from typing import Dict, List

from ..core.models import SimpleUser


class SocialMediaConfig:
    """社交媒体平台配置管理"""
    
    def __init__(self, config_file: str = "config.yaml"):
        """初始化配置，从YAML文件读取"""
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """加载YAML配置文件"""
        try:
            if not os.path.exists(self.config_file):
                raise FileNotFoundError(f"配置文件 {self.config_file} 不存在")
            
            with open(self.config_file, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                print(f"✅ 成功加载配置文件: {self.config_file}")
                return config
        except Exception as e:
            print(f"❌ 加载配置文件失败: {e}")
            sys.exit(1)
    
    def get_users(self) -> List[SimpleUser]:
        """从配置文件获取所有用户"""
        users = []
        platforms = self.config.get('platforms', {})
        
        for platform_name, platform_config in platforms.items():
            names = platform_config.get('names', [])
            for user_config in names:
                if isinstance(user_config, dict):
                    user_id = user_config.get('id', '')
                    user_name = user_config.get('name', f"{platform_name.upper()} 用户")
                    xgoid = user_config.get('xgoid')
                    users.append(SimpleUser(user_id, user_name, platform_name, xgoid))
        
        return users
    
    def get_platforms(self) -> List[str]:
        """获取所有支持的平台"""
        return list(self.config.get('platforms', {}).keys())
    
    def get_rss_templates_for_platform(self, platform: str) -> List[str]:
        """获取指定平台的RSS模板"""
        platforms = self.config.get('platforms', {})
        platform_config = platforms.get(platform, {})
        return platform_config.get('rss_url', [])
    
    def generate_urls_for_user(self, user: SimpleUser) -> List[str]:
        """为用户生成RSS URLs（用户平台固定）"""
        urls = []
        templates = self.get_rss_templates_for_platform(user.platform)
        context = {
            # 兼容旧配置，默认用 id 填充 username
            "username": user.id,
            "id": user.id,
            "name": user.name,
            # Twitter 新增的 xgoid，如不存在则保持 None 以便后续检测
            "xgoid": getattr(user, "xgoid", None),
        }
        
        for template in templates:
            placeholders = re.findall(r"{(.*?)}", template)
            # 检查模板所需的占位符是否都有值
            missing_fields = [
                field for field in placeholders
                if context.get(field) in (None, "")
            ]
            if missing_fields:
                print(f"⚠️ 模板 {template} 缺少字段: {', '.join(missing_fields)}，已跳过")
                continue
            
            try:
                url = template.format(**context)
                urls.append(url)
            except KeyError as e:
                # 捕获未知占位符，便于调试
                print(f"⚠️ 模板 {template} 包含未识别占位符 {e}，已跳过")
        
        return urls
