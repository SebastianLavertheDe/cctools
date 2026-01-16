#!/usr/bin/env python3
"""
Tech Article Collector - NVIDIA AI Version
Collects articles from Reddit and RSS, analyzes with NVIDIA AI, publishes to Notion
"""

import os
import sys
import json
import time
import asyncio
from datetime import datetime
from pathlib import Path

# Add skills to path
SKILLS_DIR = Path(__file__).parent.parent / "skills"
sys.path.insert(0, str(SKILLS_DIR / "reddit-collector" / "src"))
sys.path.insert(0, str(SKILLS_DIR / "notion-publisher" / "src"))
sys.path.insert(0, str(SKILLS_DIR / "ai-content-analyzer" / "src"))


def print_banner():
    """Print banner"""
    print("\n" + "=" * 60)
    print("🚀 Tech Article Collector - NVIDIA AI Edition")
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
        time.sleep(1)

    print(f"📱 Reddit: {len(all_posts)} posts collected\n")
    return all_posts


def collect_rss_articles(config):
    """Collect articles from RSS feeds"""
    try:
        import httpx

        HTTPX_AVAILABLE = True
    except ImportError:
        HTTPX_AVAILABLE = False
        print("⚠️ httpx not available, using mock RSS data")
        return mock_rss_articles(config)

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

            # Simple XML parsing
            content = response.text

            # Find all item entries
            import re

            items = re.findall(r"<item[^>]*>(.*?)</item>", content, re.DOTALL)

            for item_xml in items[:max_articles]:
                try:
                    title_match = re.search(r"<title[^>]*>([^<]+)</title>", item_xml)
                    link_match = re.search(r"<link[^>]*>([^<]+)</link>", item_xml)
                    desc_match = re.search(
                        r"<description[^>]*>([^<]+)</description>", item_xml
                    )
                    pub_match = re.search(r"<pubDate[^>]*>([^<]+)</pubDate>", item_xml)

                    article = {
                        "title": title_match.group(1).strip()
                        if title_match
                        else "No Title",
                        "link": link_match.group(1).strip() if link_match else "",
                        "author": name,
                        "summary": desc_match.group(1).strip()[:500]
                        if desc_match
                        else "",
                        "published": pub_match.group(1).strip()
                        if pub_match
                        else datetime.now().isoformat(),
                        "source": name,
                        "category": category,
                        "source_type": "rss",
                    }
                    all_articles.append(article)
                except Exception as e:
                    continue

            print(f"    ✓ Collected {len(items[:max_articles])} articles")

        except Exception as e:
            print(f"    ⚠️ Failed to fetch RSS: {e}")

        time.sleep(0.5)

    print(f"📡 RSS: {len(all_articles)} articles collected\n")
    return all_articles


def mock_rss_articles(config):
    """Mock RSS data"""
    print("📡 Using mock RSS data...")

    all_articles = []
    rss_sources = config.get("sources", {}).get("rss_feeds", [])

    for source in rss_sources:
        name = source["name"]
        category = source.get("category", "AI")
        max_articles = min(source.get("max_articles", 5), 3)

        print(f"  📰 {name} (mock)")

        for i in range(max_articles):
            article = {
                "title": f"{name} - Article #{i + 1}: Latest AI Developments",
                "link": f"https://example.com/{name.lower().replace(' ', '-')}/article{i}",
                "author": f"Author at {name}",
                "summary": f"This is a sample article from {name} about artificial intelligence and machine learning.",
                "published": datetime.now().isoformat(),
                "source": name,
                "category": category,
                "source_type": "rss",
            }
            all_articles.append(article)

        print(f"    ✓ Created {max_articles} mock articles")

    return all_articles


async def analyze_with_nvidia(articles):
    """Analyze articles with NVIDIA AI"""
    print("🤖 Analyzing with NVIDIA AI...")

    # Try to import NVIDIA client
    nvidia_client = None
    try:
        from nvidia_client import NVIDIAAIClient

        nvidia_client = NVIDIAAIClient()
        print("  ✓ NVIDIA client initialized")
    except Exception as e:
        print(f"  ⚠️ NVIDIA client failed: {e}")
        print("  💡 Using mock analysis")

    analyzed = 0
    for i, article in enumerate(articles):
        title = article.get("title", "")
        content = (
            article.get("summary", "")[:2000] or article.get("self_text", "")[:2000]
        )

        print(f"  📄 [{i + 1}/{len(articles)}] {title[:40]}...")

        if nvidia_client and nvidia_client.enabled:
            try:
                result = await nvidia_client.analyze_content(title, content, "quick")

                article["ai_score"] = result.get("score", 70)
                article["ai_summary"] = result.get("summary", f"AI分析: {title}")
                article["ai_category"] = result.get(
                    "category", article.get("category", "AI")
                )
                article["translated_title"] = result.get("translated_title")
                article["key_points"] = result.get("key_points", ["要点1", "要点2"])
                article["tags"] = result.get("tags", ["AI", "技术"])
                article["difficulty"] = result.get("difficulty", "Intermediate")
                article["reading_time"] = result.get("reading_time", 5)

                analyzed += 1
                print(f"    ✓ Score: {article['ai_score']}/100")

            except Exception as e:
                print(f"    ⚠️ NVIDIA analysis failed: {e}")
                article["ai_score"] = 70
        else:
            # Mock analysis
            article["ai_score"] = 75
            article["ai_summary"] = f"AI分析摘要: 这是一篇关于{title}的技术文章。"
            article["ai_category"] = article.get("category", "AI")
            article["key_points"] = ["文章主题明确", "包含技术细节", "有参考价值"]
            article["tags"] = ["AI", "技术文章", article.get("category", "AI")]
            article["difficulty"] = "Intermediate"
            article["reading_time"] = 5
            analyzed += 1
            print(f"    ✓ Mock score: 75/100")

        await asyncio.sleep(0.5)  # Rate limiting

    print(f"🤖 AI: {analyzed}/{len(articles)} articles analyzed\n")
    return articles


def analyze_with_ai(articles):
    """Sync wrapper for AI analysis"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(analyze_with_nvidia(articles))
    finally:
        loop.close()
    return result


def filter_by_quality(articles, min_score=60):
    """Filter articles by quality score"""
    print(f"⭐ Filtering (min_score={min_score})...")

    before = len(articles)
    filtered = [a for a in articles if a.get("ai_score", 0) >= min_score]
    filtered.sort(key=lambda x: x.get("ai_score", 0), reverse=True)

    print(f"  ✓ {len(filtered)}/{before} articles passed filter\n")
    return filtered


def publish_to_notion(articles):
    """Publish filtered articles to Notion"""
    from publisher import NotionPublisher

    print("📝 Publishing to Notion...")

    publisher = NotionPublisher()

    if not publisher.enabled:
        print("  ⚠️ Notion not configured properly")
        print("  💡 Check your .env file for:")
        print("     - notion_key (Integration Token)")
        print("     - NOTION_DATABASE_ID")
        print("\n  📋 To set up Notion:")
        print("     1. Go to https://www.notion.so/my-integrations")
        print("     2. Create new integration")
        print("     3. Copy the Internal Integration Token")
        print("     4. Share your database with the integration")
        print("     5. Copy the database ID from the URL")
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
                print(f"    ✓ Published to Notion!")
            else:
                print(f"    ⚠️ Publish failed (check Notion permissions)")
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
        sys.exit(1)

    # Get parameters
    limit = 20  # Default limit
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
        print(f"📌 Limited to {limit} articles\n")

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

    if published_count > 0:
        print("\n🎉 Successfully published to Notion!")
        print("📱 Check your Notion database for new articles.")
    else:
        print("\n⚠️ No articles published. Check Notion configuration.")
        print("💡 Make sure your database is shared with the integration.")

    sys.exit(0 if published_count > 0 else 1)


if __name__ == "__main__":
    main()
