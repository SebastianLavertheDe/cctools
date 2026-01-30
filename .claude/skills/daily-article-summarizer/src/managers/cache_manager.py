"""Cache manager for tracking summarized articles"""

import json
import os
from datetime import datetime
from typing import Dict, Optional
from ..core.models import ArticleSummary


class CacheManager:
    """Manages cache of summarized articles"""

    def __init__(self, cache_file: str = "summary_cache.json"):
        self.cache_file = cache_file
        self.cache: Dict = self._load_cache()

    def _load_cache(self) -> Dict:
        """Load cache from file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"  Warning: Failed to load cache: {e}")
                return {}
        return {}

    def _save_cache(self) -> None:
        """Save cache to file"""
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"  Warning: Failed to save cache: {e}")

    def is_summarized(self, date: str, filename: str) -> bool:
        """Check if an article has been summarized"""
        return date in self.cache and filename in self.cache[date]

    def get_summary(self, date: str, filename: str) -> Optional[ArticleSummary]:
        """Get cached summary for an article"""
        if self.is_summarized(date, filename):
            data = self.cache[date][filename]
            return ArticleSummary.from_dict(data)
        return None

    def mark_as_summarized(
        self, date: str, filename: str, summary: ArticleSummary, notion_page_id: str = ""
    ) -> None:
        """Mark an article as summarized"""
        if date not in self.cache:
            self.cache[date] = {}

        self.cache[date][filename] = {
            **summary.to_dict(),
            "notion_page_id": notion_page_id,
        }

        self._save_cache()

    def get_all_summaries_for_date(self, date: str) -> Dict[str, ArticleSummary]:
        """Get all summaries for a specific date"""
        if date not in self.cache:
            return {}

        return {
            filename: ArticleSummary.from_dict(data)
            for filename, data in self.cache[date].items()
        }

    def clear_date(self, date: str) -> None:
        """Clear all summaries for a specific date"""
        if date in self.cache:
            del self.cache[date]
            self._save_cache()
