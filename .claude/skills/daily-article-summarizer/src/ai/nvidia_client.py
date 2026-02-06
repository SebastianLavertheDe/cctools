"""
NVIDIA AI Summarization Client
使用 NVIDIA API 的 minimax 模型进行文章总结
"""

import os
import time
import json
import requests
import re
from typing import Optional, Dict


class NVIDIASummarizer:
    """NVIDIA minimax 总结客户端"""

    def __init__(self):
        self.api_key = os.getenv("NVIDIA_API_KEY")
        self.model = os.getenv("NVIDIA_MODEL", "minimaxai/minimax-m2.1")
        self.base_url = "https://integrate.api.nvidia.com/v1/chat/completions"

        if not self.api_key or not self.api_key.strip():
            raise ValueError("NVIDIA_API_KEY 未设置或为空")

    def _extract_json_from_response(self, text: str) -> str:
        """从AI响应中提取JSON内容"""
        # Handle ```json ... ``` or ``` ... ```
        patterns = [
            r'```json\s*([\s\S]*?)\s*```',
            r'```\s*([\s\S]*?)\s*```',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()

        # Handle truncated responses (no closing ```)
        if '```json' in text:
            idx = text.find('```json')
            text = text[idx + 7:].strip()
        elif '```' in text:
            idx = text.find('```')
            text = text[idx + 3:].strip()

        # Find first { for JSON object start
        if '{' in text:
            idx = text.find('{')
            text = text[idx:]

        return text.strip()

    def summarize_article(
        self, title: str, content: str, max_retries: int = 3
    ) -> Optional[Dict]:
        """
        总结文章内容

        Args:
            title: 文章标题
            content: 文章内容
            max_retries: 最大重试次数

        Returns:
            包含 summary, key_points, category, score 的字典
        """
        # Truncate content if too long (max 8000 chars for API)
        if len(content) > 8000:
            content = content[:8000] + "..."

        prompt = f"""请总结以下文章，并以专业AI自媒体视角（更偏向传播与增长）对内容质量进行评分。

## 文章标题
{title}

## 文章内容
{content}

## 要求
请以JSON格式输出总结，包含以下字段：
- translated_title: 翻译后的中文标题（更偏传播：有点击欲但不标题党，能准确概括核心）
- summary: 200-300字的摘要（中文；面向大众/从业者均可读，强调“看点+价值+结论”）
- key_points: 3-5个关键点（数组；每条20-50字，尽量“可转述、可截图、可做成短视频分镜”）
- category: 文章分类（只能从 AI, System Design, Backend, Frontend, DevOps, Science, Writing, Startup, Prompt, Other 之一选择）
- score: 文章质量评分（0-100的整数；评分口径更倾向传播度与增长潜力）

## 评分维度与权重（用于你内部计算score，不要在JSON中额外输出这些字段）
1) 选题与受众匹配（15分）：是否抓痛点、是否对目标受众有价值、是否具传播性  
2) 信息密度与准确性（20分）：观点是否有料、信息是否可靠、是否有关键缺失/误导风险  
3) 结构与叙事（15分）：开头抓人、逻辑清晰、节奏合理、结尾是否有收束  
4) 表达与可读性（10分）：语言简洁、口语化/专业度平衡、是否有冗余  
5) 差异化与观点力度（15分）：是否有独特视角、是否敢下结论并自洽  
6) 标题/封面/导语策略（10分）：是否有点击欲、是否准确不标题党、是否可A/B测  
7) 转化与互动设计（15分）：是否有CTA、引导评论/关注、是否适合平台算法与传播

## 输出约束
- 只输出一个JSON对象，不要包含其他说明、前后缀文本或代码块标记
- translated_title、summary 必须为中文
- key_points 必须是字符串数组
- category 必须严格匹配枚举值之一
- score 必须是整数（0-100）

只输出JSON，不要包含其他说明或代码块标记。"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "model": self.model,
            "stream": False,
            "temperature": 0.3,
        }

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.base_url, headers=headers, json=payload, timeout=60
                )

                if response.status_code == 200:
                    data = response.json()
                    content_text = (
                        data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                        .strip()
                    )

                    # Extract JSON from response
                    json_str = self._extract_json_from_response(content_text)

                    # Parse JSON
                    try:
                        result = json.loads(json_str)

                        # Validate required fields
                        if not all(key in result for key in ["translated_title", "summary", "key_points", "category", "score"]):
                            print(f"    Warning: Missing required fields in AI response")
                            return None

                        return {
                            "translated_title": result.get("translated_title", title),
                            "summary": result.get("summary", ""),
                            "key_points": result.get("key_points", []),
                            "category": result.get("category", "Other"),
                            "score": int(result.get("score", 70)),
                        }

                    except json.JSONDecodeError as e:
                        print(f"    Warning: Failed to parse JSON response: {e}")
                        print(f"    Response was: {json_str[:200]}...")
                        return None

                else:
                    print(
                        f"    Warning: Summarization failed (status {response.status_code}), attempt {attempt + 1}/{max_retries}"
                    )
                    if attempt < max_retries - 1:
                        time.sleep(2**attempt)

            except requests.exceptions.Timeout:
                print(
                    f"    Warning: Summarization timeout, attempt {attempt + 1}/{max_retries}"
                )
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)
            except Exception as e:
                print(
                    f"    Warning: Summarization error: {e}, attempt {attempt + 1}/{max_retries}"
                )
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)

        print(f"    Error: Summarization failed after {max_retries} attempts")
        return None
