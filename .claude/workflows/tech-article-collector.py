"""
Tech Article Collector Workflow
Collects articles from various sources, analyzes with AI, and publishes to Notion
"""

import os
import sys
import json
import yaml
import time
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Add skills to path
SKILLS_DIR = Path(__file__).parent.parent / "skills"


class TechArticleCollectorWorkflow:
    """Main workflow for collecting and processing tech articles"""

    def __init__(self, config_path: str = None):
        self.config_path = config_path or str(
            Path(__file__).parent / "tech-article-collector.yaml"
        )
        self.config = self._load_config()

        # Initialize components
        self.reddit_collector = None
        self.content_extractor = None
        self.ai_analyzer = None
        self.notion_publisher = None

        self._initialize_components()

    def _load_config(self) -> Dict:
        """Load workflow configuration"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

                # Replace environment variables
                config = self._replace_env_vars(config)
                return config
        except Exception as e:
            print(f"Failed to load config: {e}")
            return {}

    def _replace_env_vars(self, obj):
        """Recursively replace environment variables in config"""
        if isinstance(obj, dict):
            return {k: self._replace_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._replace_env_vars(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            env_var = obj[2:-1]
            return os.getenv(env_var, obj)
        return obj

    def _initialize_components(self):
        """Initialize all skill components"""
        print("Initializing workflow components...")

        # Initialize Reddit Collector
        try:
            sys.path.insert(0, str(SKILLS_DIR / "reddit-collector"))
            from src.collector import RedditCollector

            self.reddit_collector = RedditCollector()
        except Exception as e:
            print(f"Warning: Failed to initialize Reddit Collector: {e}")

        # Initialize Content Extractor
        try:
            sys.path.insert(0, str(SKILLS_DIR / "content-extractor"))
            from src.extractor import ContentExtractor

            extraction_config = self.config.get("extraction", {})
            self.content_extractor = ContentExtractor(
                use_firecrawl=extraction_config.get("use_firecrawl", False)
            )
        except Exception as e:
            print(f"Warning: Failed to initialize Content Extractor: {e}")

        # Initialize AI Content Analyzer
        try:
            sys.path.insert(0, str(SKILLS_DIR / "ai-content-analyzer"))
            from src.analyzer import AIContentAnalyzer

            ai_config = self.config.get("ai_analysis", {})
            processing_config = self.config.get("processing", {})
            self.ai_analyzer = AIContentAnalyzer(
                provider=processing_config.get("ai_provider", "deepseek"),
                model=processing_config.get("ai_model"),
            )
        except Exception as e:
            print(f"Warning: Failed to initialize AI Analyzer: {e}")

        # Initialize Notion Publisher
        try:
            sys.path.insert(0, str(SKILLS_DIR / "notion-publisher"))
            from src.publisher import NotionPublisher

            notion_config = self.config.get("notion", {})
            if notion_config.get("enabled", True):
                self.notion_publisher = NotionPublisher(
                    database_id=notion_config.get("database_id")
                )
        except Exception as e:
            print(f"Warning: Failed to initialize Notion Publisher: {e}")

        print("✓ Component initialization complete")

    def run(self, limit: int = None, sources: List[str] = None):
        """
        Run the complete workflow

        Args:
            limit: Maximum articles to process
            sources: List of source types to collect from (e.g., ['reddit', 'rss'])
        """
        print("\n" + "=" * 60)
        print("🚀 Tech Article Collector Workflow")
        print("=" * 60)
        print(f"Started at: {datetime.now().isoformat()}")

        all_articles = []
        sources = sources or ["reddit", "rss"]

        # Step 1: Collect articles
        print("\n📥 Step 1: Collecting articles...")
        collected_count = self._collect_articles(all_articles, sources)
        print(f"✓ Collected {collected_count} articles")

        # Step 2: Extract content
        print("\n📄 Step 2: Extracting content...")
        extracted_count = self._extract_content(all_articles)
        print(f"✓ Extracted content from {extracted_count} articles")

        # Step 3: AI Analysis
        print("\n🤖 Step 3: AI Analysis...")
        analyzed_count = self._analyze_with_ai(all_articles)
        print(f"✓ Analyzed {analyzed_count} articles")

        # Step 4: Quality filtering
        print("\n⭐ Step 4: Quality filtering...")
        filtered_articles = self._filter_by_quality(all_articles)
        print(f"✓ Filtered to {len(filtered_articles)} high-quality articles")

        # Limit results
        if limit and len(filtered_articles) > limit:
            filtered_articles = filtered_articles[:limit]

        # Step 5: Publish to Notion
        print("\n📝 Step 5: Publishing to Notion...")
        published_count = self._publish_to_notion(filtered_articles)
        print(f"✓ Published {published_count} articles to Notion")

        # Summary
        print("\n" + "=" * 60)
        print("📊 Workflow Summary")
        print("=" * 60)
        print(f"Total collected: {collected_count}")
        print(f"Content extracted: {extracted_count}")
        print(f"AI analyzed: {analyzed_count}")
        print(f"Quality filtered: {len(filtered_articles)}")
        print(f"Notion published: {published_count}")
        print(f"Completed at: {datetime.now().isoformat()}")

        return {
            "collected": collected_count,
            "extracted": extracted_count,
            "analyzed": analyzed_count,
            "filtered": len(filtered_articles),
            "published": published_count,
        }

    def _collect_articles(self, articles_list: List, sources: List[str]):
        """Collect articles from configured sources"""
        count = 0

        if "reddit" in sources and self.reddit_collector:
            count += self._collect_reddit_articles(articles_list)

        if "rss" in sources:
            count += self._collect_rss_articles(articles_list)

        return count

    def _collect_reddit_articles(self, articles_list: List):
        """Collect articles from Reddit"""
        reddit_sources = self.config.get("sources", {}).get("reddit_subreddits", [])
        count = 0

        print(f"  Collecting from {len(reddit_sources)} Reddit subreddits...")

        for source in reddit_sources:
            subreddit = source["subreddit"]
            limit = source.get("post_limit", 20)
            min_score = source.get("min_score", 50)

            print(f"    📱 r/{subreddit} (limit={limit}, min_score={min_score})")

            posts = self.reddit_collector.collect_hot_posts(
                subreddit=subreddit, limit=limit, min_score=min_score
            )

            for post in posts:
                post["source_type"] = "reddit"
                post["category"] = source.get("category", "AI")
                post["source"] = f"Reddit r/{subreddit}"

            articles_list.extend(posts)
            count += len(posts)
            print(f"      ✓ Collected {len(posts)} posts")

            # Rate limiting
            time.sleep(1)

        return count

    def _collect_rss_articles(self, articles_list: List):
        """Collect articles from RSS feeds"""
        rss_sources = self.config.get("sources", {}).get("rss_feeds", [])
        count = 0

        print(f"  Collecting from {len(rss_sources)} RSS feeds...")

        # Try to use existing RSS manager
        try:
            sys.path.insert(0, str(SKILLS_DIR / "rss-article-saver"))
            from src.managers.rss_manager import RSSManager
            from src.managers.config_manager import RSSConfig

            config = RSSConfig()
            rss_manager = RSSManager(config)

            for source in rss_sources:
                print(f"    📡 {source['name']}")

                # Create temporary feed object
                from src.managers.opml_parser import RSSFeed

                feed = RSSFeed(
                    title=source["name"],
                    url=source["url"],
                    category=source.get("category", "AI"),
                )

                parsed_feed = rss_manager.fetch_feed(feed)
                if parsed_feed:
                    max_articles = source.get("max_articles", 10)
                    for entry in parsed_feed.entries[:max_articles]:
                        article = {
                            "title": entry.get("title"),
                            "link": entry.get("link"),
                            "author": entry.get("author", source["name"]),
                            "summary": entry.get("summary", ""),
                            "source": source["name"],
                            "category": source.get("category", "AI"),
                            "source_type": "rss",
                        }
                        articles_list.append(article)
                        count += 1

                    print(
                        f"      ✓ Collected {min(len(parsed_feed.entries), source.get('max_articles', 10))} articles"
                    )

                time.sleep(0.5)

        except Exception as e:
            print(f"    ⚠️ RSS collection failed: {e}")
            print("    📡 Falling back to simple RSS parsing...")

            # Fallback: Simple RSS parsing
            import feedparser

            for source in rss_sources:
                print(f"    📡 {source['name']}")

                try:
                    parsed = feedparser.parse(source["url"])
                    max_articles = source.get("max_articles", 10)

                    for entry in parsed.entries[:max_articles]:
                        article = {
                            "title": entry.get("title"),
                            "link": entry.get("link"),
                            "author": entry.get("author", source["name"]),
                            "summary": entry.get("summary", ""),
                            "source": source["name"],
                            "category": source.get("category", "AI"),
                            "source_type": "rss",
                        }
                        articles_list.append(article)
                        count += 1

                    print(
                        f"      ✓ Collected {min(len(parsed.entries), max_articles)} articles"
                    )
                    time.sleep(0.5)

                except Exception as e:
                    print(f"      ⚠️ Failed to parse RSS: {e}")

        return count

    def _extract_content(self, articles: List[Dict]):
        """Extract full content from article URLs"""
        if not self.content_extractor:
            print("  ⚠️ Content extractor not available, using summaries only")
            return 0

        count = 0
        extraction_config = self.config.get("extraction", {})
        max_length = extraction_config.get("max_content_length", 50000)

        for article in articles:
            link = article.get("link")
            if not link:
                continue

            # Skip non-article links (images, videos, etc.)
            if link.endswith((".jpg", ".png", ".gif", ".mp4", ".pdf")):
                continue

            print(f"    📄 Extracting: {article.get('title', 'Untitled')[:50]}...")

            try:
                result = self.content_extractor.extract_article(link)

                if result["success"] and result["content"]:
                    # Update article with extracted content
                    article["full_content"] = result["content"][:max_length]
                    article["extracted_title"] = result["title"]
                    article["extracted_author"] = result["author"]
                    article["extracted_date"] = result["publish_date"]
                    article["images"] = result.get("images", [])[:5]  # Limit images
                    article["word_count"] = result["word_count"]
                    article["reading_time"] = result["reading_time"]
                    count += 1
                    print(f"      ✓ Extracted {result['word_count']} words")
                else:
                    # Use existing summary
                    article["full_content"] = article.get("summary", "")[:max_length]
                    print(f"      ⚠️ Extraction failed, using summary")

            except Exception as e:
                article["full_content"] = article.get("summary", "")[:max_length]
                print(f"      ⚠️ Extraction error: {e}")

            time.sleep(0.3)  # Rate limiting

        return count

    def _analyze_with_ai(self, articles: List[Dict]):
        """Analyze articles with AI"""
        if not self.ai_analyzer:
            print("  ⚠️ AI analyzer not available, using mock analysis")
            for article in articles:
                article["ai_score"] = 75
                article["ai_summary"] = (
                    f"AI分析: {article.get('title', 'Unknown article')}"
                )
                article["ai_category"] = article.get("category", "AI")
            return len(articles)

        count = 0
        ai_config = self.config.get("ai_analysis", {})
        analysis_type = ai_config.get("analysis_type", "comprehensive")
        max_content_length = ai_config.get("max_content_length_for_analysis", 3000)

        for article in articles:
            title = article.get("title", "")
            content = article.get("full_content", "")[
                :max_content_length
            ] or article.get("summary", "")

            if not content:
                print(f"    ⚠️ No content to analyze: {title[:50]}")
                continue

            print(f"    🤖 Analyzing: {title[:50]}...")

            try:
                result = self.ai_analyzer.analyze_content(title, content, analysis_type)

                # Update article with AI results
                article["ai_score"] = result.get("score", 0)
                article["ai_summary"] = result.get("summary", "")
                article["ai_category"] = result.get(
                    "category", article.get("category", "AI")
                )
                article["translated_title"] = result.get("translated_title")
                article["key_points"] = result.get("key_points", [])
                article["tags"] = result.get("tags", [])
                article["difficulty"] = result.get("difficulty", "Intermediate")
                article["reading_time"] = result.get(
                    "reading_time", article.get("reading_time", 5)
                )

                # Score breakdown
                if result.get("score_breakdown"):
                    article["information_density"] = result["score_breakdown"].get(
                        "information_density"
                    )
                    article["evidence_quality"] = result["score_breakdown"].get(
                        "evidence_quality"
                    )
                    article["practicality"] = result["score_breakdown"].get(
                        "practicality"
                    )
                    article["novelty_insight"] = result["score_breakdown"].get(
                        "novelty_insight"
                    )

                count += 1
                print(f"      ✓ Score: {result.get('score', 0)}/100")

            except Exception as e:
                print(f"      ⚠️ AI analysis failed: {e}")
                # Set default values
                article["ai_score"] = 60
                article["ai_summary"] = f"AI分析失败: {e}"

            time.sleep(0.5)  # Rate limiting for API calls

        return count

    def _filter_by_quality(self, articles: List[Dict]) -> List[Dict]:
        """Filter articles by AI score"""
        min_score = self.config.get("processing", {}).get("min_score_threshold", 60)

        filtered = []
        for article in articles:
            score = article.get("ai_score", 0)
            if score >= min_score:
                filtered.append(article)
            else:
                print(
                    f"    ⚠️ Filtered out (score {score}): {article.get('title', 'Untitled')[:50]}"
                )

        # Sort by score descending
        filtered.sort(key=lambda x: x.get("ai_score", 0), reverse=True)

        return filtered

    def _publish_to_notion(self, articles: List[Dict]) -> int:
        """Publish filtered articles to Notion"""
        if not self.notion_publisher or not self.notion_publisher.enabled:
            print("  ⚠️ Notion publisher not available, skipping publish")
            return 0

        notion_config = self.config.get("notion", {})
        template = notion_config.get("template", "default")

        count = 0
        for article in articles:
            print(f"    📝 Publishing: {article.get('title', 'Untitled')[:50]}...")

            try:
                success = self.notion_publisher.publish_article(article, template)
                if success:
                    count += 1
                    print(f"      ✓ Published to Notion")
                else:
                    print(f"      ⚠️ Failed to publish")

            except Exception as e:
                print(f"      ⚠️ Publish error: {e}")

            time.sleep(0.5)  # Rate limiting

        return count


def run_workflow(limit: int = None, sources: List[str] = None):
    """Run the workflow"""
    workflow = TechArticleCollectorWorkflow()
    return workflow.run(limit=limit, sources=sources)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Tech Article Collector Workflow")
    parser.add_argument(
        "--limit", type=int, default=None, help="Maximum articles to process"
    )
    parser.add_argument(
        "--sources",
        type=str,
        nargs="+",
        default=None,
        help="Sources to collect from (reddit, rss)",
    )
    parser.add_argument("--config", type=str, default=None, help="Path to config file")

    args = parser.parse_args()

    workflow = TechArticleCollectorWorkflow(config_path=args.config)
    result = workflow.run(limit=args.limit, sources=args.sources)

    print("\n✅ Workflow completed!")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
