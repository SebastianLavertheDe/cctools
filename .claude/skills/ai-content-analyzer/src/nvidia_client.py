"""
NVIDIA AI Client
AI content analyzer using NVIDIA API
"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    print("Warning: httpx library not available")


class NVIDIAAIClient:
    """NVIDIA AI-powered content analyzer"""

    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        self.base_url = base_url or os.getenv(
            "NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1"
        )
        self.model = model or os.getenv("NVIDIA_MODEL", "meta/llama-3.1-405b-instruct")

        self.client = None
        self.enabled = False
        self._init_client()

    def _init_client(self):
        """Initialize NVIDIA client"""
        if not HTTPX_AVAILABLE:
            print("Warning: httpx not available")
            return

        if not self.api_key:
            print("Warning: NVIDIA_API_KEY not set")
            return

        try:
            self.client = httpx.AsyncClient(timeout=120.0)
            self.enabled = True
            print(f"✓ NVIDIA AI client initialized (model: {self.model})")
        except Exception as e:
            print(f"✗ NVIDIA client initialization failed: {e}")

    async def analyze_content(
        self, title: str, content: str, analysis_type: str = "comprehensive"
    ) -> Dict:
        """Analyze content using NVIDIA API"""
        if not self.enabled:
            return self._get_mock_analysis(title, content)

        if analysis_type == "comprehensive":
            return await self._comprehensive_analysis(title, content)
        else:
            return await self._quick_analysis(title, content)

    async def _comprehensive_analysis(self, title: str, content: str) -> Dict:
        """Perform comprehensive analysis"""
        prompt = f"""
你是一个专业的技术内容分析师。请对以下文章进行分析并评分。

标题: {title}
内容: {content[:3000]}

请按以下JSON格式返回分析结果：
{{
    "translated_title": "中文翻译的标题",
    "summary": "详细的中文摘要（300-500字）",
    "key_points": ["要点1", "要点2", "要点3"],
    "category": "文章分类（AI、Golang、架构、编程等）",
    "tags": ["标签1", "标签2", "标签3"],
    "difficulty": "难度等级（Beginner/Intermediate/Advanced）",
    "reading_time": 预估阅读时间（分钟）,
    "score": 评分(0-100),
    "information_density": 信息密度(0-20),
    "evidence_quality": 证据质量(0-20),
    "practicality": 实用性(0-20),
    "novelty_insight": 新颖性(0-15),
    "logical_structure": 逻辑结构(0-15),
    "clarity": 表达清晰度(0-10)
}}

只返回JSON格式，不要包含其他文字。
"""

        response = await self._call_nvidia(prompt, max_tokens=3000)
        result = self._parse_json(response)

        if result:
            result["analysis_type"] = "comprehensive"
            result["analyzed_at"] = datetime.now().isoformat()

        return result or self._get_mock_analysis(title, content)

    async def _quick_analysis(self, title: str, content: str) -> Dict:
        """Perform quick analysis"""
        prompt = f"""
快速分析这篇技术文章：

标题: {title}
内容: {content[:1000]}

返回JSON格式：
{{
    "category": "分类",
    "score": 评分(0-100),
    "summary": "简要摘要（100-200字）",
    "tags": ["标签1", "标签2"]
}}
"""

        response = await self._call_nvidia(prompt, max_tokens=500)
        result = self._parse_json(response)

        if result:
            result["analysis_type"] = "quick"
            result["analyzed_at"] = datetime.now().isoformat()

        return result or self._get_mock_analysis(title, content)

    async def _call_nvidia(self, prompt: str, max_tokens: int = 2000) -> str:
        """Make API call to NVIDIA"""
        if not self.client:
            return ""

        try:
            url = f"{self.base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.3,
            }

            response = await self.client.post(url, headers=headers, json=data)
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"].strip()

        except Exception as e:
            print(f"NVIDIA API call failed: {e}")
            return ""

    def _parse_json(self, response: str) -> Optional[Dict]:
        """Parse JSON from AI response"""
        if not response:
            return None

        try:
            import re

            json_match = re.search(r"\{[^{}]*\}", response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return json.loads(response)

        except (json.JSONDecodeError, TypeError) as e:
            print(f"Failed to parse AI response as JSON: {e}")
            return None

    def _get_mock_analysis(self, title: str, content: str) -> Dict:
        """Get mock analysis when AI is not available"""
        return {
            "translated_title": f"[AI分析] {title}",
            "summary": f"这是一篇关于{title}的技术文章。文章内容涵盖{content[:200]}...",
            "key_points": [
                f"文章主题: {title}",
                "包含重要的技术细节",
                "对读者有参考价值",
            ],
            "category": "AI",
            "tags": ["技术文章", "AI", "开发"],
            "difficulty": "Intermediate",
            "reading_time": max(1, len(content) // 200),
            "score": 75,
            "information_density": 15,
            "evidence_quality": 14,
            "practicality": 15,
            "novelty_insight": 11,
            "logical_structure": 12,
            "clarity": 8,
            "analysis_type": "mock",
            "analyzed_at": datetime.now().isoformat(),
        }


# Synchronous wrapper
class NVIDIAAIClientSync:
    """Synchronous wrapper for NVIDIA AI client"""

    def __init__(self):
        self.async_client = None
        self.enabled = False
        self._init_async_client()

    def _init_async_client(self):
        """Initialize async client"""
        try:
            self.async_client = NVIDIAAIClient()
            self.enabled = self.async_client.enabled
        except Exception as e:
            print(f"Failed to initialize NVIDIA client: {e}")

    def analyze_content(
        self, title: str, content: str, analysis_type: str = "comprehensive"
    ) -> Dict:
        """Analyze content (sync wrapper)"""
        import asyncio

        if not self.enabled:
            return (
                self.async_client._get_mock_analysis(title, content)
                if self.async_client
                else {
                    "translated_title": f"[AI分析] {title}",
                    "summary": f"AI分析: {title}",
                    "score": 75,
                    "category": "AI",
                }
            )

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.async_client.analyze_content(title, content, analysis_type)
            )
            loop.close()
            return result
        except Exception as e:
            print(f"NVIDIA analysis failed: {e}")
            return self.async_client._get_mock_analysis(title, content)


# Alias
class AIContentAnalyzer(NVIDIAAIClientSync):
    """Alias for compatibility"""

    pass


def main():
    """Main entry point"""
    import sys

    if len(sys.argv) < 3:
        print("Usage: python -m nvidia_client <title> <content>")
        return

    title = sys.argv[1]
    content = sys.argv[2]

    client = NVIDIAAIClientSync()
    result = client.analyze_content(title, content)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
