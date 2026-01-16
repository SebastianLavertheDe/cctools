#!/usr/bin/env python3
"""
Tech Article Collector - Simplified Runner
Collects articles from Reddit and RSS, analyzes with AI, publishes to Notion
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

# Add skills to path
SKILLS_DIR = Path(__file__).parent.parent / "skills"
sys.path.insert(0, str(SKILLS_DIR / "reddit-collector" / "src"))
sys.path.insert(0, str(SKILLS_DIR / "notion-publisher" / "src"))


def print_banner():
    """Print banner"""
    print("\n" + "=" * 60)
    print("🚀 Tech Article Collector")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


def load_config():
    """Load configuration"""
    config_path = Path(__file__).parent / "tech-article-collector.yaml"

    if not config_path.exists():
        print("❌ Config file not found")
        return None

    try:
        import yaml

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Replace env vars
        if "sources" in config:
            for key in ["reddit_subreddits", "rss_feeds"]:
                if key in config["sources"]:
                    for item in config["sources"][key]:
                        for k, v in item.items():
                            if (
                                isinstance(v, str)
                                and v.startswith("${")
                                and v.endswith("}")
                            ):
                                item[k] = os.getenv(v[2:-1], v)

        return config
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return None


def collect_reddit_articles(config):
    """Collect articles from Reddit (web scraping)"""
    from collector import RedditCollector

    print("📱 Collecting from Reddit...")

    collector = RedditCollector()
    all_posts = []

    reddit_sources = config.get("sources", {}).get("reddit_subreddits", [])

    for source in reddit_sources:
        subreddit = source["subreddit"]
        limit = source.get("post_limit", 10)
        min_score = source.get("min_score", 50)
        category = source.get("category", "AI")

        print(f"  🌐 r/{subreddit} (limit={limit}, min_score={min_score})")

        posts = collector.collect_hot_posts(subreddit, limit, min_score)

        for post in posts:
            post["category"] = category
            post["source"] = f"Reddit r/{subreddit}"

        print(f"    ✓ Collected {len(posts)} posts")
        all_posts.extend(posts)
        time.sleep(1)  # Rate limiting

    print(f"📱 Reddit: {len(all_posts)} posts collected\n")
    return all_posts


def collect_rss_articles(config):
    """Collect articles from RSS feeds"""
    import httpx
    from bs4 import BeautifulSoup

    print("📡 Collecting from RSS feeds...")

    all_articles = []
    rss_sources = config.get("sources", {}).get("rss_feeds", [])

    for source in rss_sources:
        name = source["name"]
        url = source["url"]
        category = source.get("category", "AI")
        max_articles = source.get("max_articles", 5)

        print(f"  📰 {name}")

        try:
            response = httpx.get(url, timeout=30.0)
            response.raise_for_status()

            # Parse RSS/Atom
            soup = BeautifulSoup(response.text, "xml")

            entries = soup.find_all(["entry", "item"])[:max_articles]

            for entry in entries:
                try:
                    article = {
                        "title": entry.title.text if entry.title else "No Title",
                        "link": entry.link.get("href") if entry.link else "",
                        "author": entry.author.text
                        if entry.author and hasattr(entry.author, "text")
                        else name,
                        "summary": entry.summary.text
                        if entry.summary
                        else entry.get("content", ""),
                        "published": entry.published.text
                        if entry.published
                        else datetime.now().isoformat(),
                        "source": name,
                        "category": category,
                        "source_type": "rss",
                    }
                    all_articles.append(article)
                except Exception as e:
                    print(f"    ⚠️ Error parsing entry: {e}")
                    continue

            print(f"    ✓ Collected {len(entries)} articles")

        except Exception as e:
            print(f"    ⚠️ Failed to fetch RSS: {e}")

        time.sleep(0.5)

    print(f"📡 RSS: {len(all_articles)} articles collected\n")
    return all_articles


def analyze_with_ai(articles):
    """Analyze articles with AI"""
    print("🤖 Analyzing with AI...")

    # Try MiniMax first
    ai_client = None
    try:
        sys.path.insert(0, str(SKILLS_DIR / "ai-content-analyzer" / "src"))
        from minimax_client import MiniMaxAIClient

        ai_client = MiniMaxAIClient()
        print("  ✓ Using MiniMax AI")
    except Exception as e:
        print(f"  ⚠️ MiniMax not available: {e}")

    analyzed = 0
    for i, article in enumerate(articles):
        title = article.get("title", "")
        content = (
            article.get("summary", "")[:2000] or article.get("self_text", "")[:2000]
        )

        print(f"  📄 [{i + 1}/{len(articles)}] {title[:40]}...")

        if ai_client and ai_client.enabled:
            try:
                result = ai_client.analyze_content(title, content, "quick")

                article["ai_score"] = result.get("score", 60)
                article["ai_summary"] = result.get("summary", "")
                article["ai_category"] = result.get(
                    "category", article.get("category", "AI")
                )
                article["translated_title"] = result.get("translated_title")
                article["key_points"] = result.get("key_points", [])
                article["tags"] = result.get("tags", [])
                article["difficulty"] = result.get("difficulty", "Intermediate")
                article["reading_time"] = result.get("reading_time", 5)

                analyzed += 1
                print(f"    ✓ Score: {article['ai_score']}/100")

            except Exception as e:
                print(f"    ⚠️ AI analysis failed: {e}")
                article["ai_score"] = 60
        else:
            # Use mock analysis
            article["ai_score"] = 75
            article["ai_summary"] = f"AI分析: {title}"
            article["ai_category"] = article.get("category", "AI")
            article["key_points"] = ["要点1", "要点2"]
            article["tags"] = ["AI", "技术"]
            article["difficulty"] = "Intermediate"
            article["reading_time"] = 5
            analyzed += 1
            print(f"    ✓ Mock score: 75/100")

        time.sleep(0.3)

    print(f"🤖 AI: {analyzed}/{len(articles)} articles analyzed\n")
    return articles


def filter_by_quality(articles, min_score=60):
    """Filter articles by quality score"""
    print(f"⭐ Filtering (min_score={min_score})...")

    filtered = [a for a in articles if a.get("ai_score", 0) >= min_score]
    filtered.sort(key=lambda x: x.get("ai_score", 0), reverse=True)

    print(f"  ✓ {len(filtered)}/{len(articles)} articles passed filter\n")
    return filtered


def publish_to_notion(articles):
    """Publish filtered articles to Notion"""
    from publisher import NotionPublisher

    print("📝 Publishing to Notion...")

    publisher = NotionPublisher()

    if not publisher.enabled:
        print("  ⚠️ Notion not configured, skipping publish")
        print("  💡 To enable Notion sync:")
        print("     1. Create integration: https://www.notion.so/my-integrations")
        print("     2. Share your database with the integration")
        print("     3. Add NOTION_DATABASE_ID and notion_key to .env")
        return 0

    published = 0
    for i, article in enumerate(articles):
        title = (
            article.get("translated_title") or article.get("title", "Untitled")[:100]
        )
        print(f"  📝 [{i + 1}/{len(articles)}] {title[:40]}...")

        try:
            success = publisher.publish_article(article, "default")
            if success:
                published += 1
                print(f"    ✓ Published")
            else:
                print(f"    ⚠️ Failed")
        except Exception as e:
            print(f"    ❌ Error: {e}")

        time.sleep(0.5)

    print(f"📝 Notion: {published}/{len(articles)} articles published\n")
    return published


def print_summary(collected, analyzed, filtered, published):
    """Print summary"""
    print("=" * 60)
    print("📊 Summary")
    print("=" * 60)
    print(f"  Collected: {collected}")
    print(f"  Analyzed:  {analyzed}")
    print(f"  Filtered:  {filtered}")
    print(f"  Published: {published}")
    print(f"\n  Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


def main():
    """Main entry point"""
    print_banner()

    # Load config
    config = load_config()
    if not config:
        print("❌ Config load failed")
        sys.exit(1)

    # Get parameters
    limit = None
    sources = ["reddit", "rss"]

    for arg in sys.argv[1:]:
        if arg.isdigit():
            limit = int(arg)
        elif arg.startswith("--"):
            parts = arg[2:].split("=")
            if parts[0] == "limit":
                limit = int(parts[1]) if len(parts) > 1 else 20
            elif parts[0] == "sources":
                sources = parts[1].split(",") if len(parts) > 1 else ["reddit"]

    # Collect articles
    all_articles = []

    if "reddit" in sources:
        reddit_articles = collect_reddit_articles(config)
        all_articles.extend(reddit_articles)

    if "rss" in sources:
        rss_articles = collect_rss_articles(config)
        all_articles.extend(rss_articles)

    if not all_articles:
        print("❌ No articles collected")
        sys.exit(1)

    # Apply limit
    if limit and len(all_articles) > limit:
        all_articles = all_articles[:limit]

    # AI Analysis
    analyzed_articles = analyze_with_ai(all_articles)

    # Quality filter
    min_score = config.get("processing", {}).get("min_score_threshold", 60)
    filtered_articles = filter_by_quality(analyzed_articles, min_score)

    # Publish to Notion
    published_count = publish_to_notion(filtered_articles)

    # Summary
    print_summary(
        collected=len(all_articles),
        analyzed=len(analyzed_articles),
        filtered=len(filtered_articles),
        published=published_count,
    )

    # Exit
    sys.exit(0 if published_count > 0 else 1)


if __name__ == "__main__":
    main()
