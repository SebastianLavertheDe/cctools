"""
NVIDIA AI Translation Client
使用 NVIDIA API 的 minimax 模型进行文本翻译
"""

import os
import time
import requests
import re
import html
import json
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

    def _extract_json_translation(self, content: str) -> Optional[str]:
        """
        Extract translation from JSON response, handling AI thinking process

        Args:
            content: Raw response from AI

        Returns:
            Extracted translation or None
        """
        if not content:
            return None

        # First, try to find JSON object at the end (after any thinking process)
        # Split by common thinking process markers
        lines = content.split('\n')

        # Find where JSON likely starts (look for "{")
        json_start_idx = -1
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Skip thinking process patterns
            if stripped.startswith("The user wants") or stripped.startswith("Let me") or \
               stripped.startswith("I need to") or stripped.startswith("Looking at"):
                continue
            # Look for JSON start
            if '{' in stripped:
                json_start_idx = i
                break

        if json_start_idx >= 0:
            # Extract from JSON start to end
            json_content = '\n'.join(lines[json_start_idx:])

            # Try to find the JSON object
            try:
                # Find the first { and last }
                start = json_content.find('{')
                end = json_content.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = json_content[start:end]
                    result = json.loads(json_str)
                    translation = result.get('translation')
                    if translation:
                        return translation
            except json.JSONDecodeError:
                pass  # Try alternative methods

        # Fallback: try to extract JSON using regex
        json_match = re.search(r'\{[^{}]*"translation"\s*:\s*"[^"]*"[^{}]*\}', content)
        if json_match:
            try:
                result = json.loads(json_match.group(0))
                return result.get('translation')
            except json.JSONDecodeError:
                pass

        return None
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

    def translate_title(self, title: str) -> Optional[str]:
        """
        将标题翻译成中文

        Args:
            title: 要翻译的标题

        Returns:
            翻译后的中文标题，失败时返回None
        """
        if not title or len(title.strip()) < 1:
            return title

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # JSON format prompt for cleaner output
        prompt = f"""Translate the following title to Chinese.

Original title: {title}

Output format (JSON only):
{{"translation": "translated_title_here"}}

Rules:
- Return ONLY the JSON object
- Do NOT include any explanations or thinking process
- Keep it concise and accurate"""

        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "model": self.model,
            "stream": False,
            "temperature": 0.1,
            "max_tokens": 150,
        }

        for attempt in range(3):
            try:
                response = requests.post(
                    self.base_url, headers=headers, json=payload, timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    content = (
                        data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                        .strip()
                    )

                    # Parse JSON response using helper function
                    translation = self._extract_json_translation(content)
                    if translation:
                        return translation

            except Exception as e:
                if attempt < 2:
                    time.sleep(1)

        return None

    def translate_to_chinese(self, text: str, max_retries: int = 3) -> Optional[str]:
        """
        将文本翻译成中文

        Args:
            text: 要翻译的文本
            max_retries: 最大重试次数

        Returns:
            翻译后的中文文本，失败时返回None
        """
        if not text or len(text.strip()) < 1:
            return text

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # JSON format prompt for cleaner output
        prompt = f"""Translate the following text to Chinese.

Text:
{text}

Output format (JSON only):
{{"translation": "translated_text_here"}}

Rules:
- Return ONLY the JSON object
- Do NOT include any explanations or thinking process
- Keep Markdown format
- Do not translate code blocks or URLs
- Keep technical terms accurate"""

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
                    content = (
                        data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                        .strip()
                    )

                    # Parse JSON response using helper function
                    translation = self._extract_json_translation(content)
                    if translation:
                        return translation

                else:
                    print(
                        f"    Warning: Translation failed (status {response.status_code}), attempt {attempt + 1}/{max_retries}"
                    )
                    if attempt < max_retries - 1:
                        time.sleep(2**attempt)

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

        # Build the translation prompt using JSON format to force clean output
        # Escape the text for JSON
        import json
        escaped_text = text.replace('"', '\\"').replace('\n', '\\n')

        prompt = f"""You are a professional translator. Translate the following text to Chinese.

Text to translate:
{escaped_text}

Output format (JSON):
{{"translation": "translated_text_here}}

Rules:
- Return ONLY the JSON object
- Do NOT include any explanations or thinking process
- Keep Markdown format
- Do not translate code blocks or URLs
- Keep technical terms accurate"""

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

                    # minimax model outputs: thinking process \n\n\n\n actual content
                    # Split by multiple newlines and take the last substantial part
                    if '\n\n\n\n' in translated_text:
                        parts = translated_text.split('\n\n\n\n')
                        # Take the last part that has content
                        translated_text = parts[-1].strip()

                    # Try to parse as JSON first (for title translation)
                    import json
                    try:
                        # Look for ```json code block
                        if '```json' in translated_text:
                            start = translated_text.find('```json') + 7
                            end = translated_text.find('```', start)
                            if end > start:
                                json_str = translated_text[start:end].strip()
                                result = json.loads(json_str)
                                if 'translation' in result:
                                    return result['translation'].strip()

                        # Look for JSON object anywhere
                        if '{' in translated_text and 'translation' in translated_text:
                            start = translated_text.find('{')
                            end = translated_text.rfind('}') + 1
                            json_str = translated_text[start:end]
                            result = json.loads(json_str)
                            if 'translation' in result:
                                return result['translation'].strip()
                    except:
                        pass  # Fall through to regular cleaning

                    # Remove any potential markdown code block wrappers
                    if translated_text.startswith("```"):
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
                        "the user wants me to",
                        "let me",
                        "i need to",
                        "i'll",
                        "i will",
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
                        "analyze",
                        "analyzing",
                        "example",
                        "technical",
                        "this is an",
                        "this is a",
                        "here's a",
                        "here is",
                        "check if",
                        "make sure"
                    ]

                    # Find first actual content line
                    # Special handling for "The user wants me to translate" pattern
                    has_thinking_pattern = any("the user wants me to" in line.lower() for line in lines[:20])

                    if has_thinking_pattern:
                        # Aggressive mode: skip everything until we find substantial Chinese content
                        in_thinking = True
                        consecutive_chinese_lines = 0
                        min_chinese_lines = 3

                        for i, line in enumerate(lines):
                            stripped = line.strip()
                            if not stripped:
                                continue

                            line_lower = stripped.lower()

                            # Check if we're still in thinking mode
                            if in_thinking:
                                # Look for end of thinking patterns
                                if any(marker in line_lower for marker in ["i'll translate", "here's the translation:", "translation:"]):
                                    in_thinking = False
                                    consecutive_chinese_lines = 0
                                    continue

                                # Skip thinking lines
                                if any(pattern in line_lower for pattern in skip_patterns):
                                    continue

                                # Check if this line has substantial Chinese content
                                chinese_count = sum(1 for c in stripped if "\u4e00" <= c <= "\u9fff")
                                if chinese_count >= 5 and (chinese_count / len(stripped)) > 0.4:
                                    consecutive_chinese_lines += 1
                                    if consecutive_chinese_lines >= min_chinese_lines:
                                        content_start = i - consecutive_chinese_lines + 1
                                        break
                                else:
                                    consecutive_chinese_lines = 0
                            else:
                                # After thinking ended, find first real content
                                chinese_count = sum(1 for c in stripped if "\u4e00" <= c <= "\u9fff")
                                if chinese_count >= 3:
                                    content_start = i
                                    break
                    else:
                        # Original logic for non-pattern cases
                        in_thinking_process = True
                        consecutive_content_lines = 0
                        min_content_lines = 5
                        thinking_ended = False

                        for i, line in enumerate(lines):
                            stripped = line.strip()
                            if not stripped:
                                if in_thinking_process:
                                    continue
                                else:
                                    break

                            line_lower = stripped.lower()

                            is_term_list = (
                                stripped.startswith(("-", "*", "•")) and
                                ('"' in stripped or "'" in stripped) and
                                (" - " in stripped or " — " in stripped or " – " in stripped)
                            )

                            if is_term_list:
                                consecutive_content_lines = 0
                                continue

                            if not thinking_ended:
                                if any(marker in line_lower for marker in ["i'll translate", "let me translate", "here's the translation"]):
                                    thinking_ended = True
                                    consecutive_content_lines = 0
                                    continue

                            if not thinking_ended and any(pattern in line_lower for pattern in skip_patterns):
                                consecutive_content_lines = 0
                                continue
                            else:
                                has_chinese = any("\u4e00" <= char <= "\u9fff" for char in stripped)
                                is_heading = stripped.startswith(("#", "##", "###"))

                                if is_heading:
                                    content_start = i
                                    in_thinking_process = False
                                    break

                                chinese_char_count = sum(1 for c in stripped if "\u4e00" <= c <= "\u9fff")
                                total_char_count = len(stripped)

                                if has_chinese and chinese_char_count >= 3 and (chinese_char_count / max(total_char_count, 1)) > 0.3:
                                    consecutive_content_lines += 1
                                    if consecutive_content_lines >= min_content_lines:
                                        content_start = i - consecutive_content_lines + 1
                                        in_thinking_process = False
                                        break
                                else:
                                    consecutive_content_lines = 0

                    if content_start > 0:
                        translated_text = "\n".join(lines[content_start:])

                        # Additional cleanup: remove any remaining thinking patterns after content
                        # Split by double newlines and keep only paragraphs with substantial Chinese
                        paragraphs = translated_text.split("\n\n")
                        clean_paragraphs = []
                        for para in paragraphs:
                            para = para.strip()
                            if not para:
                                continue
                            # Skip paragraphs with thinking patterns
                            para_lower = para.lower()
                            if any(pattern in para_lower for pattern in ["actually, looking", "let me refine", "i'll refine", "given the context"]):
                                continue
                            # Keep paragraphs with substantial Chinese content
                            chinese_count = sum(1 for c in para if "\u4e00" <= c <= "\u9fff")
                            if chinese_count >= 10:
                                clean_paragraphs.append(para)

                        if clean_paragraphs:
                            translated_text = "\n\n".join(clean_paragraphs)

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
