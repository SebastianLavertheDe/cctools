"""
Core data models for ByteByteGo RSS
"""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Article:
    """Blog article data model"""
    title: str
    link: str
    author: str
    published: str
    summary: str  # RSS excerpt
    full_content: Optional[str] = None  # Extracted full content
    image_urls: List[str] = field(default_factory=list)  # Extracted images

    # AI processed fields
    translated_title: Optional[str] = None  # AI translated title
    ai_summary: Optional[str] = None
    ai_score: Optional[int] = None  # AI score (0-100)
    ai_category: Optional[str] = None
    ai_tags: List[str] = field(default_factory=list)
