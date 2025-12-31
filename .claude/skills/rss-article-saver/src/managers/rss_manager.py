"""
RSS Manager - Main processing workflow for multiple RSS feeds
"""

import feedparser
import os
import json
from pathlib import Path
from datetime import datetime
from ..core.models import Article
from ..managers.opml_parser import RSSFeed
from ..managers.cache_manager import ArticleCacheManager
from ..managers.content_manager import ContentExtractor
from ..notion.notion_manager import BlogNotionManager


class RSSManager:
    """Multi-feed RSS manager"""

    def __init__(self, config):
        self.config = config
        self.cache_manager = ArticleCacheManager()
        self.content_extractor = ContentExtractor(config.get_content_settings())

        # Get Notion sync settings
        notion_settings = config.get_notion_settings()
        self.notion_sync_enabled = notion_settings.get('sync', True)

        # Only initialize Notion manager if sync is enabled
        if self.notion_sync_enabled:
            self.notion_manager = BlogNotionManager()
        else:
            self.notion_manager = None
            print("Notion sync disabled (notion.sync: false)")

        # Setup article directory (in cctools root)
        self.article_dir = Path(__file__).parent.parent.parent.parent.parent.parent / "article"
        self.article_dir.mkdir(exist_ok=True)

        # Initialize AI client based on config
        try:
            ai_config = config.get_ai_settings()
            if ai_config.get('enabled', True):
                ai_provider = ai_config.get('provider', 'deepseek').lower()
                if ai_provider == 'gemini' or ai_provider == 'google':
                    from ..ai.google_client import GeminiClient
                    self.ai_client = GeminiClient()
                    print(f"AI client initialized (Gemini)")
                else:
                    from ..ai.deepseek_client import DeepSeekClient
                    self.ai_client = DeepSeekClient()
                    print(f"AI client initialized (DeepSeek)")
            else:
                self.ai_client = None
        except Exception as e:
            print(f"AI client init failed: {e}")
            self.ai_client = None

    def fetch_feed(self, feed: RSSFeed):
        """Fetch a single RSS feed"""
        try:
            parsed = feedparser.parse(feed.url)

            if parsed.bozo:
                print(f"  Feed parse warning: {parsed.bozo_exception}")

            return parsed
        except Exception as e:
            print(f"  Failed to fetch feed: {e}")
            return None

    def process_feed(self, parsed_feed, feed_info: RSSFeed) -> None:
        """Process feed entries"""
        max_articles = self.config.get_max_articles_per_feed()
        entries = parsed_feed.entries[:max_articles]

        new_articles = []

        for entry in entries:
            link = entry.get('link', '')

            if self.cache_manager.is_article_cached(link):
                continue

            article = self._create_article_from_entry(entry, feed_info)
            new_articles.append(article)

        print(f"  New articles: {len(new_articles)}")

        for article in new_articles:
            self._process_article(article)

        # Save cache
        self.cache_manager.save()

    def _create_article_from_entry(self, entry, feed_info: RSSFeed) -> Article:
        """Create Article from RSS entry"""
        return Article(
            title=entry.get('title', 'No Title'),
            link=entry.get('link', ''),
            author=entry.get('author', feed_info.title),
            published=entry.get('published', ''),
            summary=entry.get('summary', entry.get('description', ''))
        )

    def _process_article(self, article: Article) -> None:
        """Process single article: extract content, AI analyze, sync to Notion"""
        print(f"\n  Processing: {article.title[:50]}...")

        # Extract full content
        print("    Extracting content...")
        extracted = self.content_extractor.extract_content(article.link)
        article.full_content = extracted.get('content', '')
        if extracted.get('images'):
            article.image_urls = extracted['images']
        if extracted.get('author'):
            article.author = extracted['author']

        # AI Analysis
        if self.ai_client:
            print("    Analyzing with AI...")
            self._analyze_article(article)

        # Check score threshold (skip if score < 30) - NOTE: Lowered for testing
        if article.ai_score is not None and article.ai_score < 30:
            print(f"    Score: {article.ai_score}/100 - Skipped (below threshold)")
            # Still add to cache to avoid reprocessing
            self.cache_manager.add_article_to_cache(article)
            return

        # Sync to Notion
        if self.notion_sync_enabled and self.notion_manager and self.notion_manager.enabled:
            print("    Syncing to Notion...")
            self.notion_manager.push_article_to_notion(article)

        # Add to cache
        self.cache_manager.add_article_to_cache(article)

        # Save original article to file (only if score >= 62)
        self._save_article(article)

    def _save_article(self, article: Article) -> None:
        """Save article to articles directory as Markdown"""
        try:
            # Create safe filename from title
            safe_title = article.title[:100]
            safe_title = safe_title.replace('/', '-').replace('\\', '-')
            safe_title = safe_title.replace(':', '').replace('?', '').replace('*', '')
            safe_title = safe_title.replace('"', '').replace('<', '').replace('>', '').replace('|', '')
            safe_title = ''.join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in safe_title)

            # Create filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{safe_title}.md"
            filepath = self.article_dir / filename

            # Build Markdown content
            md_content = []

            # Title
            md_content.append(f"# {article.title}\n")

            # Metadata
            md_content.append("## 元数据\n")
            md_content.append(f"- **链接**: {article.link}")
            md_content.append(f"- **作者**: {article.author}")
            md_content.append(f"- **发布时间**: {article.published}")
            if article.ai_score is not None:
                md_content.append(f"- **评分**: {article.ai_score}/100")
            if article.ai_category:
                md_content.append(f"- **分类**: {article.ai_category}")
            md_content.append(f"- **保存时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

            # AI Analysis (if available)
            if article.ai_summary:
                md_content.append("## AI 分析\n")
                md_content.append(f"{article.ai_summary}\n")

            # Original Content (images are embedded in content now)
            md_content.append("## 正文\n")
            md_content.append(f"{article.full_content}\n")

            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(md_content))

            print(f"    Saved to: {filename}")
        except Exception as e:
            print(f"    Warning: Failed to save article: {e}")

    def _analyze_article(self, article: Article) -> None:
        """Analyze article with AI"""
        content_for_ai = article.full_content or article.summary

        ai_result = self.ai_client.analyze_content(
            title=article.title,
            content=content_for_ai
        )

        article.translated_title = ai_result.get('translated_title')
        article.ai_summary = ai_result.get('summary')
        article.ai_score = ai_result.get('score')
        article.ai_category = ai_result.get('category')
        article.ai_tags = ai_result.get('categories', [ai_result.get('category')])
