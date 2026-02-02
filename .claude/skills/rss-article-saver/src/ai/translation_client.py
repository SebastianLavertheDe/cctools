"""
Fallback Translation Client
自动在多个翻译服务之间切换 (NVIDIA -> Google Gemini)
"""

import os
import time
from typing import Optional


class FallbackTranslator:
    """带回退机制的翻译客户端"""

    def __init__(self, primary_provider="nvidia", fallback_provider="google"):
        self.primary_provider = primary_provider
        self.fallback_provider = fallback_provider
        self.primary_client = None
        self.fallback_client = None

        # Initialize primary client
        if primary_provider == "nvidia":
            try:
                from .nvidia_client import NVIDIATranslator
                self.primary_client = NVIDIATranslator()
                print("Translation primary client: NVIDIA minimax")
            except Exception as e:
                print(f"Warning: NVIDIA client init failed: {e}")

        # Initialize fallback client
        if fallback_provider == "google" or fallback_provider == "gemini":
            try:
                from .google_client import GeminiTranslator
                self.fallback_client = GeminiTranslator()
                print("Translation fallback client: Google Gemini")
            except Exception as e:
                print(f"Warning: Google Gemini client init failed: {e}")

        if not self.primary_client and not self.fallback_client:
            print("Error: No translation client available")

    def translate_title(self, title: str) -> Optional[str]:
        """翻译标题，支持自动切换"""
        # Try primary first
        if self.primary_client:
            try:
                result = self.primary_client.translate_title(title)
                if result:
                    return result
                print("  Primary translator returned None, trying fallback...")
            except Exception as e:
                print(f"  Primary translator error: {e}, trying fallback...")

        # Try fallback
        if self.fallback_client:
            try:
                result = self.fallback_client.translate_title(title)
                if result:
                    print("  ✓ Used fallback: Google Gemini")
                    return result
            except Exception as e:
                print(f"  Fallback translator error: {e}")

        return None

    def translate_to_chinese(self, text: str, max_retries: int = 3) -> Optional[str]:
        """翻译内容，支持自动切换"""
        # Try primary first
        if self.primary_client:
            try:
                result = self.primary_client.translate_to_chinese(text, max_retries=max_retries)
                if result:
                    return result
                print("  Primary translator returned None, trying fallback...")
            except Exception as e:
                print(f"  Primary translator error: {e}, trying fallback...")

        # Add delay before switching providers (to avoid rate limits)
        if self.fallback_client:
            print("  Waiting 2 seconds before trying fallback provider...")
            time.sleep(2)
            try:
                result = self.fallback_client.translate_to_chinese(text, max_retries=max_retries)
                if result:
                    print("  ✓ Used fallback: Google Gemini")
                    return result
            except Exception as e:
                print(f"  Fallback translator error: {e}")

        return None
