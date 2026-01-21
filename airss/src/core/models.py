"""
核心数据模型
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class SimpleUser:
    """极简用户配置"""
    id: str  # 用于RSS URL填充（通常是用户名）
    name: str  # 用于显示的用户名
    platform: str  # 用户所属平台
    xgoid: str | None = None  # Twitter 可能使用的 xgoid，占位符缺失时可为空
