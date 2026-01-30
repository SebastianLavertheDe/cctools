"""
NVIDIA AI Translation Client
使用 NVIDIA API 的 minimax 模型进行文本翻译
"""

import os
import time
import requests
import re
import html
from typing import Optional
from bs4 import BeautifulSoup


class NVIDIATranslator:
    """NVIDIA minimax 翻译客户端"""

    def __init__(self):
        self.api_key = os.getenv("NVIDIA_API_KEY")
        self.model = os.getenv("NVIDIA_MODEL", "minimaxai/minimax-m2.1")
        self.base_url = "https://integrate.api.nvidia.com/v1/chat/completions"

        if not self.api_key or not self.api_key.strip():
            raise ValueError("NVIDIA_API_KEY 未设置或为空")

    def _clean_html_tags(self, text: str) -> str:
        """清理文本中的 HTML 标签"""
        try:
            # 使用 BeautifulSoup 清理 HTML
            soup = BeautifulSoup(text, 'html.parser')

            # 移除所有标签但保留文本
            clean_text = soup.get_text(separator='\n', strip=True)

            # 清理多余的空行
            clean_text = re.sub(r'\n{3,}', '\n\n', clean_text)

            return clean_text.strip()
        except:
            # 如果 BeautifulSoup 失败，使用正则表达式作为后备
            clean_text = re.sub(r'<[^>]+>', '\n', text)
            clean_text = re.sub(r'\n{3,}', '\n\n', clean_text)
            return clean_text.strip()

    def translate_to_chinese(self, text: str, max_retries: int = 3) -> Optional[str]:
        """
        将文本翻译成中文（一次性翻译，不切割）

        Args:
            text: 要翻译的文本
            max_retries: 最大重试次数

        Returns:
            翻译后的中文文本，失败时返回None
        """
        if not text or len(text.strip()) < 1:
            return text

        # Translate the entire text at once
        return self._translate_chunk(text, max_retries)

    def _translate_chunk(self, text: str, max_retries: int) -> Optional[str]:
        """
        翻译单个文本块

        Args:
            text: 要翻译的文本块
            max_retries: 最大重试次数

        Returns:
            翻译后的文本，失败时返回None
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # Build the translation prompt
        prompt = f"""将以下文章翻译成中文。

IMPORTANT RULES:
- Output ONLY the translated text
- NO explanations, notes, or thinking process
- NO bullet points of instructions
- NO planning or analysis
- Start directly with the translated content
- Keep Markdown format
- Do not translate code blocks
- Do not translate URLs
- Keep technical terms accurate

{text}"""

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
                    translated_text = (
                        data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                        .strip()
                    )

                    # Remove any potential markdown code block wrappers
                    if translated_text.startswith("```"):
                        # Remove ```markdown or ``` at start
                        lines = translated_text.split("\n")
                        if lines[0].startswith("```"):
                            lines = lines[1:]
                        if lines and lines[-1].strip() == "```":
                            lines = lines[:-1]
                        translated_text = "\n".join(lines)

                    lines = translated_text.split("\n")
                    content_start = 0

                    # Patterns that indicate non-content lines (AI thinking, instructions, etc.)
                    skip_patterns = [
                        "translate",
                        "翻译",
                        "let me",
                        "i need to",
                        "i'll",
                        "first",
                        "next",
                        "then",
                        "important",
                        "keep",
                        "规则",
                        "要求",
                        "output",
                        "start",
                        "planning",
                        "analysis",
                        "example",
                        "technical"
                    ]

                    # Find first actual content line
                    in_thinking_process = True  # Assume we start in thinking process
                    consecutive_content_lines = 0
                    min_content_lines = 3  # Need at least 3 lines of real content to confirm

                    for i, line in enumerate(lines):
                        stripped = line.strip()
                        if not stripped:
                            if in_thinking_process:
                                continue
                            else:
                                break  # Empty line after content means we're done

                        # Skip lines that look like instructions or thinking
                        line_lower = stripped.lower()

                        # Check if this looks like a term/definition list (thinking pattern)
                        is_term_list = (
                            stripped.startswith(("-", "*", "•")) and
                            ('"' in stripped or "'" in stripped) and
                            (" - " in stripped or " — " in stripped or " – " in stripped)
                        )

                        if is_term_list:
                            consecutive_content_lines = 0
                            continue

                        # Skip lines with thinking keywords
                        if any(pattern in line_lower for pattern in skip_patterns):
                            # But don't skip if it's a heading or substantial Chinese content
                            has_chinese = any("\u4e00" <= char <= "\u9fff" for char in stripped)
                            is_heading = stripped.startswith(("#", "##", "###"))

                            if is_heading:
                                content_start = i
                                in_thinking_process = False
                                break

                            if has_chinese and len(stripped) > 15 and not stripped.startswith("-"):
                                # Substantial Chinese text, likely real content
                                consecutive_content_lines += 1
                                if consecutive_content_lines >= min_content_lines:
                                    content_start = i - consecutive_content_lines + 1
                                    in_thinking_process = False
                                    break
                            else:
                                consecutive_content_lines = 0
                                continue
                        else:
                            # No skip patterns found
                            if stripped.startswith(("#", "##", "###")):
                                content_start = i
                                in_thinking_process = False
                                break

                            has_chinese = any("\u4e00" <= char <= "\u9fff" for char in stripped)
                            if has_chinese and len(stripped) > 10:
                                consecutive_content_lines += 1
                                if consecutive_content_lines >= min_content_lines:
                                    content_start = i - consecutive_content_lines + 1
                                    in_thinking_process = False
                                    break

                    if content_start > 0:
                        translated_text = "\n".join(lines[content_start:])

                    # Clean any HTML tags that might be in the translation
                    translated_text = self._clean_html_tags(translated_text)

                    return translated_text

                else:
                    print(
                        f"    Warning: Translation failed (status {response.status_code}), attempt {attempt + 1}/{max_retries}"
                    )
                    if attempt < max_retries - 1:
                        time.sleep(2**attempt)  # Exponential backoff

            except requests.exceptions.Timeout:
                print(
                    f"    Warning: Translation timeout, attempt {attempt + 1}/{max_retries}"
                )
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)
            except Exception as e:
                print(
                    f"    Warning: Translation error: {e}, attempt {attempt + 1}/{max_retries}"
                )
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)

        print(f"    Error: Translation failed after {max_retries} attempts")
        return None
