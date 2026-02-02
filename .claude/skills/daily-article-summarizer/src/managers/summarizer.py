"""Summarizer for processing articles with AI"""

from datetime import datetime
from typing import List, Optional
from ..ai.nvidia_client import NVIDIASummarizer
from ..ai.google_client import GeminiSummarizer
from ..core.models import ArticleMetadata, ArticleSummary


class ArticleSummarizer:
    """Manages article summarization using AI with fallback"""

    def __init__(self):
        self.primary_client = None
        self.fallback_client = None
        self.enabled = False

        # Initialize primary client (NVIDIA)
        try:
            self.primary_client = NVIDIASummarizer()
            self.enabled = True
            print(f"  ✓ Primary AI client: NVIDIA")
        except Exception as e:
            print(f"  Warning: NVIDIA client initialization failed: {e}")

        # Initialize fallback client (Google Gemini)
        try:
            self.fallback_client = GeminiSummarizer()
            if not self.enabled:
                self.enabled = True
                print(f"  ✓ Fallback AI client: Google Gemini")
        except Exception as e:
            print(f"  Warning: Google Gemini client initialization failed: {e}")

        if not self.enabled:
            print(f"  Error: No AI client available")

    def summarize_article(
        self, article: ArticleMetadata, date: str
    ) -> Optional[ArticleSummary]:
        """
        Summarize a single article with fallback

        Args:
            article: Article metadata with content
            date: Date string (YYYYMMDD)

        Returns:
            ArticleSummary or None if failed
        """
        if not self.enabled:
            print("  AI summarization disabled")
            return None

        if not article.content:
            print(f"  Warning: No content to summarize for {article.filename}")
            return None

        print(f"  Summarizing: {article.title[:50]}...")

        # Try primary client first
        if self.primary_client:
            result = self.primary_client.summarize_article(article.title, article.content)
            if result:
                return self._create_summary(article, result, date)
            print(f"  Primary client failed, trying fallback...")

        # Try fallback client
        if self.fallback_client:
            result = self.fallback_client.summarize_article(article.title, article.content)
            if result:
                print(f"  ✓ Used fallback: Google Gemini")
                return self._create_summary(article, result, date)

        print(f"  Warning: Failed to summarize {article.filename}")
        return None

    def _create_summary(
        self, article: ArticleMetadata, result: dict, date: str
    ) -> ArticleSummary:
        """Create ArticleSummary from AI result"""
        return ArticleSummary(
            title=result.get("translated_title", article.title),
            file_path=article.file_path,
            source_url=article.link,
            author=article.author,
            summary=result["summary"],
            key_points=result["key_points"],
            category=result["category"],
            score=result["score"],
            processed_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            date=date,
        )

        return ArticleSummary(
            title=result.get("translated_title", article.title),  # Use translated title
            file_path=article.file_path,
            source_url=article.link,
            author=article.author,
            summary=result["summary"],
            key_points=result["key_points"],
            category=result["category"],
            score=result["score"],
            processed_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            date=date,
        )

    def batch_summarize(
        self, articles: List[ArticleMetadata], date: str, batch_size: int = 5
    ) -> List[ArticleSummary]:
        """
        Summarize multiple articles in batches

        Args:
            articles: List of article metadata
            date: Date string (YYYYMMDD)
            batch_size: Number of articles to process in each batch

        Returns:
            List of ArticleSummary objects
        """
        summaries = []

        for i in range(0, len(articles), batch_size):
            batch = articles[i : i + batch_size]
            print(f"\n  Processing batch {i // batch_size + 1}/{(len(articles) + batch_size - 1) // batch_size}")

            for article in batch:
                summary = self.summarize_article(article, date)
                if summary:
                    summaries.append(summary)

        return summaries
