"""
AI Content Analyzer
Analyzes and scores content using MiniMax AI
"""

import os
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class AIContentAnalyzer:
    """AI-powered content analyzer using MiniMax"""

    def __init__(self, provider: str = "minimax"):
        self.provider = provider
        self.client = None
        self.enabled = False
        self._init_client()

    def _init_client(self):
        """Initialize AI client"""
        # Try MiniMax first
        try:
            from minimax_client import MiniMaxAIClient

            self.client = MiniMaxAIClient()
            if self.client.enabled:
                self.enabled = True
                print("✓ AI Analyzer initialized with MiniMax")
                return
        except ImportError:
            pass

        # Try OpenAI as fallback
        try:
            from openai import OpenAI

            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.client = OpenAI(api_key=api_key)
                self.enabled = True
                print("✓ AI Analyzer initialized with OpenAI")
            else:
                print("⚠️ No AI API key configured, using mock analysis")
        except ImportError:
            print("⚠️ No AI library available, using mock analysis")

    def analyze_content(
        self, title: str, content: str, analysis_type: str = "comprehensive"
    ) -> Dict:
        """Analyze content and return comprehensive results"""
        if not self.enabled:
            return self._get_mock_analysis(title, content)

        try:
            if hasattr(self.client, "analyze_content"):
                return self.client.analyze_content(title, content, analysis_type)
            else:
                return self._openai_analysis(title, content, analysis_type)
        except Exception as e:
            print(f"AI analysis failed: {e}")
            return self._get_mock_analysis(title, content)

    def _openai_analysis(self, title: str, content: str, analysis_type: str) -> Dict:
        """OpenAI-based analysis (fallback)"""
        prompt = f"""
分析这篇技术文章：

标题: {title}
内容: {content[:3000]}

返回JSON:
{{
    "translated_title": "中文标题",
    "summary": "摘要",
    "key_points": ["要点1", "要点2"],
    "category": "分类",
    "tags": ["标签"],
    "difficulty": "Intermediate",
    "reading_time": 5,
    "score": 75,
    "information_density": 15,
    "evidence_quality": 14,
    "practicality": 15,
    "novelty_insight": 11,
    "logical_structure": 12,
    "clarity": 8
}}
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
            )

            result = self._parse_json(response.choices[0].message.content)
            if result:
                result["analysis_type"] = analysis_type
                result["analyzed_at"] = datetime.now().isoformat()
                return result

        except Exception as e:
            print(f"OpenAI API call failed: {e}")

        return self._get_mock_analysis(title, content)

    def _parse_json(self, response: str) -> Optional[Dict]:
        """Parse JSON from response"""
        if not response:
            return None
        try:
            import re

            match = re.search(r"\{[^{}]*\}", response, re.DOTALL)
            if match:
                return json.loads(match.group())
            return json.loads(response)
        except:
            return None

    def _get_mock_analysis(self, title: str, content: str) -> Dict:
        """Mock analysis when AI is not available"""
        return {
            "translated_title": f"[AI分析] {title}",
            "summary": f"这是一篇关于{title}的技术文章。{content[:200]}...",
            "key_points": [f"文章主题: {title}", "包含技术细节", "有参考价值"],
            "category": "AI",
            "tags": ["技术文章", "AI"],
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


def main():
    """Main entry point"""
    import sys

    if len(sys.argv) < 3:
        print("Usage: python -m ai_content_analyzer <title> <content>")
        return

    title = sys.argv[1]
    content = sys.argv[2]

    analyzer = AIContentAnalyzer()
    result = analyzer.analyze_content(title, content)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
