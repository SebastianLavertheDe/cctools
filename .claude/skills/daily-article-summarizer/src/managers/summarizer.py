"""Summarizer for processing articles with AI"""

from datetime import datetime
from typing import List, Optional
from ..ai.nvidia_client import NVIDIASummarizer
from ..core.models import ArticleMetadata, ArticleSummary


class ArticleSummarizer:
    """Manages article summarization using AI"""

    def __init__(self):
        try:
            self.ai_client = NVIDIASummarizer()
            self.enabled = True
        except Exception as e:
            print(f"  Warning: AI client initialization failed: {e}")
            self.ai_client = None
            self.enabled = False

    def summarize_article(
        self, article: ArticleMetadata, date: str
    ) -> Optional[ArticleSummary]:
        """
        Summarize a single article

        Args:
            article: Article metadata with content
            date: Date string (YYYYMMDD)

        Returns:
            ArticleSummary or None if failed
        """
        if not self.enabled or not self.ai_client:
            print("  AI summarization disabled")
            return None

        if not article.content:
            print(f"  Warning: No content to summarize for {article.filename}")
            return None

        print(f"  Summarizing: {article.title[:50]}...")

        result = self.ai_client.summarize_article(article.title, article.content)

        if not result:
            print(f"  Warning: Failed to summarize {article.filename}")
            return None

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
