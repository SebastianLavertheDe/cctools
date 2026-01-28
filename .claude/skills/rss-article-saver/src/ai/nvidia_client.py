"""
NVIDIA AI Translation Client
使用 NVIDIA API 的 minimax 模型进行文本翻译
"""

import os
import time
import requests
from typing import Optional


class NVIDIATranslator:
    """NVIDIA minimax 翻译客户端"""

    def __init__(self):
        self.api_key = os.getenv("NVIDIA_API_KEY")
        self.model = os.getenv("NVIDIA_MODEL", "minimaxai/minimax-m2.1")
        self.base_url = "https://integrate.api.nvidia.com/v1/chat/completions"

        if not self.api_key or not self.api_key.strip():
            raise ValueError("NVIDIA_API_KEY 未设置或为空")

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
        prompt = f"""请将以下 Markdown 文章翻译成中文。直接输出翻译结果，不要有任何分析、解释或思考过程。

要求：
- 保持 Markdown 格式
- 代码块不翻译
- URL 不翻译
- 专业术语保持准确

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

                    # Find first line with Chinese characters (highest priority)
                    for i, line in enumerate(lines):
                        stripped = line.strip()
                        if not stripped:
                            continue

                        has_chinese = any(
                            "\u4e00" <= char <= "\u9fff" for char in stripped
                        )
                        if has_chinese:
                            content_start = i
                            break

                    # If no Chinese found, fall back to heading markers
                    if content_start == 0:
                        for i, line in enumerate(lines):
                            stripped = line.strip()
                            if not stripped:
                                continue
                            if stripped.startswith(("#", "##", "###", "!", "- ", "* ")):
                                content_start = i
                                break

                    if content_start > 0:
                        translated_text = "\n".join(lines[content_start:])

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
