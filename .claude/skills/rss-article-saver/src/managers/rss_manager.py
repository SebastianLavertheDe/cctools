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
        self.notion_sync_enabled = notion_settings.get("sync", True)

        # Only initialize Notion manager if sync is enabled
        if self.notion_sync_enabled:
            self.notion_manager = BlogNotionManager()
        else:
            self.notion_manager = None
            print("Notion sync disabled (notion.sync: false)")

        # Setup article directory (in project mymind, organized by week)
        # Go up from .claude/skills/rss-article-saver/ to project root
        project_root = Path(__file__).parent.parent.parent.parent.parent.parent
        self.article_base_dir = project_root / "mymind" / "article"
        self.article_base_dir.mkdir(parents=True, exist_ok=True)

        # Initialize AI client based on config
        try:
            ai_config = config.get_ai_settings()
            if ai_config.get("enabled", True):
                ai_provider = ai_config.get("provider", "deepseek").lower()
                if ai_provider == "gemini" or ai_provider == "google":
                    from ..ai.google_client import GeminiClient

                    self.ai_client = GeminiClient()
                    print(f"AI client initialized (Gemini)")
                elif ai_provider == "zhipu" or ai_provider == "glm":
                    from ..ai.zhipu_client import ZhipuClient

                    self.ai_client = ZhipuClient()
                    print(f"AI client initialized (Zhipu AI)")
                else:
                    from ..ai.deepseek_client import DeepSeekClient

                    self.ai_client = DeepSeekClient()
                    print(f"AI client initialized (DeepSeek)")
            else:
                self.ai_client = None
        except Exception as e:
            print(f"AI client init failed: {e}")
            self.ai_client = None

        # Initialize translator based on config
        try:
            translation_config = config.get_translation_settings()
            self.translation_enabled = translation_config.get("enabled", False)
            if self.translation_enabled:
                translation_provider = translation_config.get(
                    "provider", "nvidia"
                ).lower()
                if translation_provider == "nvidia":
                    from ..ai.nvidia_client import NVIDIATranslator

                    self.translator = NVIDIATranslator()
                    print(f"Translation enabled (NVIDIA minimax)")
                else:
                    self.translator = None
                    print(
                        f"Translation provider '{translation_provider}' not supported"
                    )
            else:
                self.translator = None
        except Exception as e:
            print(f"Translator init failed: {e}")
            self.translator = None
            self.translation_enabled = False

    def fetch_feed(self, feed: RSSFeed):
        """Fetch a single RSS feed"""
        import requests
        import tempfile
        from ..managers.opml_parser import OPMLParser

        try:
            # First, fetch the URL content to check if it's an OPML file
            print(f"  Fetching URL to check content type...")

            # Convert GitHub blob URLs to raw URLs
            url_to_fetch = feed.url
            if "github.com" in url_to_fetch and "/blob/" in url_to_fetch:
                url_to_fetch = url_to_fetch.replace(
                    "github.com", "raw.githubusercontent.com"
                ).replace("/blob/", "/")
                print(f"  Converted GitHub blob URL to raw URL")

            response = requests.get(url_to_fetch, timeout=10)
            response.raise_for_status()
            content = response.text

            # Check if the content is OPML format (contains <opml> tag)
            if "<opml" in content.lower():
                print(f"  Detected OPML file, parsing nested feeds...")
                # Save content to a temporary file
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".opml", delete=False
                ) as tmp_file:
                    tmp_file.write(content)
                    tmp_file_path = tmp_file.name

                try:
                    # Parse the OPML file
                    opml_parser = OPMLParser(tmp_file_path)
                    nested_feeds = opml_parser.parse()

                    if nested_feeds:
                        print(f"  Found {len(nested_feeds)} nested RSS feeds in OPML")
                        # Return special structure to indicate OPML type
                        return {
                            "type": "opml",
                            "feeds": nested_feeds,
                            "parent_title": feed.title,
                        }
                    else:
                        print(
                            f"  Warning: OPML file contains no RSS feeds, falling back to RSS parser"
                        )
                finally:
                    # Clean up temporary file
                    try:
                        import os

                        os.unlink(tmp_file_path)
                    except:
                        pass

            # If not OPML, parse as regular RSS feed
            parsed = feedparser.parse(url_to_fetch)

            if parsed.bozo:
                print(f"  Feed parse warning: {parsed.bozo_exception}")

            return parsed

        except requests.RequestException as e:
            print(f"  Warning: Could not check if URL is OPML: {e}")
            # Fall through to feedparser
            try:
                # Convert GitHub blob URLs to raw URLs
                url_to_fetch = feed.url
                if "github.com" in url_to_fetch and "/blob/" in url_to_fetch:
                    url_to_fetch = url_to_fetch.replace(
                        "github.com", "raw.githubusercontent.com"
                    ).replace("/blob/", "/")
                    print(f"  Converted GitHub blob URL to raw URL (fallback)")

                parsed = feedparser.parse(url_to_fetch)
                if parsed.bozo:
                    print(f"  Feed parse warning: {parsed.bozo_exception}")
                return parsed
            except Exception as e2:
                print(f"  Failed to fetch feed after fallback: {e2}")
                return None

        except Exception as e:
            print(f"  Failed to fetch feed: {e}")
            import traceback

            traceback.print_exc()
            return None

    def process_feed(self, parsed_feed, feed_info: RSSFeed) -> None:
        """Process feed entries"""
        max_articles = self.config.get_max_articles_per_feed()

        # First, filter out cached articles, then limit
        new_articles = []

        for entry in parsed_feed.entries:
            # Stop if we've reached the max limit
            if len(new_articles) >= max_articles:
                break

            link = entry.get("link", "")

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
            title=entry.get("title", "No Title"),
            link=entry.get("link", ""),
            author=entry.get("author", feed_info.title),
            published=entry.get("published", ""),
            summary=entry.get("summary", entry.get("description", "")),
        )

    def _process_article(self, article: Article) -> None:
        """Process single article: extract content, translate, sync to Notion, save to local"""
        print(f"\n  Processing: {article.title[:50]}...")

        # Extract full content
        print("    Extracting content...")
        extracted = self.content_extractor.extract_content(article.link)
        article.full_content = extracted.get("content", "")
        if extracted.get("images"):
            article.image_urls = extracted["images"]
        if extracted.get("author"):
            article.author = extracted["author"]

        # Translate content to Chinese if enabled
        if self.translation_enabled and self.translator and article.full_content:
            print("    Translating to Chinese...")
            try:
                translated_content = self.translator.translate_to_chinese(
                    article.full_content
                )
                if translated_content:
                    article.full_content = translated_content
                    print("    Translation completed")
                else:
                    print("    Warning: Translation failed, using original content")
            except Exception as e:
                print(f"    Warning: Translation error: {e}, using original content")

        # Sync to Notion
        if (
            self.notion_sync_enabled
            and self.notion_manager
            and self.notion_manager.enabled
        ):
            print("    Syncing to Notion...")
            self.notion_manager.push_article_to_notion(article)

        # Add to cache
        self.cache_manager.add_article_to_cache(article)

        # Save article to file
        self._save_article(article)

    def _save_article(self, article: Article) -> None:
        """Save article to mymind/article directory organized by week as Markdown"""
        try:
            # Use original title for filename
            title_for_filename = article.title[:100]

            # Create safe filename (keep Chinese characters)
            safe_title = title_for_filename.replace("/", "-").replace("\\", "-")
            safe_title = safe_title.replace(":", "").replace("?", "").replace("*", "")
            safe_title = (
                safe_title.replace('"', "")
                .replace("<", "")
                .replace(">", "")
                .replace("|", "")
            )
            # Only replace special characters, keep alphanumeric and Chinese
            safe_title = "".join(
                c
                if c.isalnum() or c > "\u4e00" and c < "\u9fff" or c in (" ", "-", "_")
                else "_"
                for c in safe_title
            )

            # Use title as filename (without timestamp)
            filename = f"{safe_title}.md"

            # Get week directory (format: YYYY-Www)
            now = datetime.now()
            year, week, _ = now.isocalendar()
            week_dir_name = f"{year}-W{week:02d}"
            week_dir = self.article_base_dir / week_dir_name
            week_dir.mkdir(exist_ok=True)

            filepath = week_dir / filename

            # Build Markdown content
            md_content = []

            # Title
            md_content.append(f"# {article.title}\n")

            # Metadata
            md_content.append("## 元数据\n")
            md_content.append(f"- **链接**: {article.link}")
            md_content.append(f"- **作者**: {article.author}")
            md_content.append(f"- **发布时间**: {article.published}")
            md_content.append(
                f"- **保存时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )

            # Original Content (images are embedded in content)
            md_content.append("## 正文\n")
            md_content.append(f"{article.full_content}\n")

            # Save to file
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(md_content))

            print(f"    Saved to: {filepath}")
        except Exception as e:
            print(f"    Warning: Failed to save article: {e}")

    def _analyze_article(self, article: Article) -> None:
        """Analyze article with AI"""
        content_for_ai = article.full_content or article.summary

        ai_result = self.ai_client.analyze_content(
            title=article.title, content=content_for_ai
        )

        article.translated_title = ai_result.get("translated_title")
        article.ai_summary = ai_result.get("summary")
        article.ai_score = ai_result.get("score")
        article.ai_category = ai_result.get("category")
        article.ai_tags = ai_result.get("categories", [ai_result.get("category")])
