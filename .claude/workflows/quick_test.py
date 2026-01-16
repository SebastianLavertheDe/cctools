#!/usr/bin/env python3
"""
Tech Article Collector - Self-contained Test Script
Tests all components with mock data
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path


def print_banner():
    print("\n" + "=" * 60)
    print("🚀 Tech Article Collector - Test Mode")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


def mock_reddit_collector():
    """Mock Reddit collector (returns sample data)"""
    print("📱 Collecting from Reddit (mock)...")

    subreddits = [
        ("golang", "Golang", 10, 50),
        ("ArtificialIntelligence", "AI", 15, 100),
        ("ChatGPT", "AI", 10, 80),
    ]

    all_posts = []

    for subreddit, category, limit, min_score in subreddits:
        print(f"  🌐 r/{subreddit} (limit={limit})")

        for i in range(limit):
            post = {
                "title": f"[r/{subreddit}] Sample Article #{i + 1} about AI and Technology",
                "link": f"https://old.reddit.com/r/{subreddit}/comments/example{i}",
                "author": f"User{i % 5 + 1}",
                "score": min_score + (i * 5),
                "comments": i * 3,
                "upvote_ratio": 0.85 + (i % 3) * 0.05,
                "created_utc": datetime.now().timestamp(),
                "created_date": datetime.now().isoformat(),
                "self_text": f"This is a sample post about {subreddit} and technology topics including AI, LLMs, and development.",
                "url": "",
                "subreddit": subreddit,
                "is_self": True,
                "domain": "reddit.com",
                "source_type": "reddit",
                "category": category,
                "source": f"Reddit r/{subreddit}",
            }
            all_posts.append(post)

        print(f"    ✓ Collected {limit} posts")
        time.sleep(0.2)

    print(f"📱 Reddit: {len(all_posts)} posts collected\n")
    return all_posts


def mock_rss_collector():
    """Mock RSS collector (returns sample data)"""
    print("📡 Collecting from RSS feeds (mock)...")

    feeds = [
        ("OpenAI Blog", "AI", 5),
        ("Anthropic Blog", "AI", 5),
        ("Google AI Blog", "AI", 3),
    ]

    all_articles = []

    for name, category, limit in feeds:
        print(f"  📰 {name}")

        for i in range(limit):
            article = {
                "title": f"{name} - Article #{i + 1}: The Future of AI",
                "link": f"https://example.com/{name.lower().replace(' ', '-')}/article{i}",
                "author": f"Author{i % 3 + 1}",
                "summary": f"This is a sample article from {name} about artificial intelligence, machine learning, and technology. It discusses the latest developments in the field and provides insights for developers.",
                "published": datetime.now().isoformat(),
                "source": name,
                "category": category,
                "source_type": "rss",
            }
            all_articles.append(article)

        print(f"    ✓ Collected {limit} articles")
        time.sleep(0.2)

    print(f"📡 RSS: {len(all_articles)} articles collected\n")
    return all_articles


def mock_ai_analyzer(articles):
    """Mock AI analyzer (returns sample analysis)"""
    print("🤖 Analyzing with AI (mock)...")

    for i, article in enumerate(articles):
        title = article.get("title", "Unknown")
        print(f"  📄 [{i + 1}/{len(articles)}] {title[:40]}...")

        # Generate mock analysis
        article["ai_score"] = 70 + (i % 30)  # Score 70-99
        article["ai_summary"] = (
            f"AI分析摘要: 这是一篇关于{title}的技术文章。文章涵盖人工智能、机器学习等热门话题，对开发者有重要参考价值。文章结构清晰，论证充分。"
        )
        article["ai_category"] = article.get("category", "AI")
        article["translated_title"] = f"[AI分析] {title}"
        article["key_points"] = [
            "文章主题明确，讨论AI技术发展",
            "包含实际案例和代码示例",
            "对开发者有实际指导意义",
        ]
        article["tags"] = ["AI", "技术文章", "开发", article.get("category", "AI")]
        article["difficulty"] = "Intermediate"
        article["reading_time"] = 5 + (i % 10)

        print(f"    ✓ Score: {article['ai_score']}/100")
        time.sleep(0.1)

    print(f"🤖 AI: {len(articles)} articles analyzed\n")
    return articles


def filter_by_quality(articles, min_score=60):
    """Filter articles by quality score"""
    print(f"⭐ Filtering (min_score={min_score})...")

    before = len(articles)
    filtered = [a for a in articles if a.get("ai_score", 0) >= min_score]
    filtered.sort(key=lambda x: x.get("ai_score", 0), reverse=True)

    print(f"  ✓ {len(filtered)}/{before} articles passed filter\n")
    return filtered


def mock_notion_publisher(articles):
    """Mock Notion publisher"""
    print("📝 Publishing to Notion (mock)...")

    if not articles:
        print("  ⚠️ No articles to publish\n")
        return 0

    print("  💡 Notion配置检查:")
    print("     - 需要配置: NOTION_DATABASE_ID")
    print("     - 需要配置: notion_key (Integration Token)")
    print("     - 数据库需要与Integration共享")
    print()

    published = 0
    for i, article in enumerate(articles[:5]):  # Limit to 5 for demo
        title = article.get("translated_title") or article.get("title", "Untitled")[:80]
        score = article.get("ai_score", 0)
        category = article.get("ai_category", "AI")

        print(f"  📝 [{i + 1}/{min(len(articles), 5)}] {title}")
        print(f"      Score: {score}/100 | Category: {category}")
        print(f"      📄 Would create Notion page with:")
        print(f"         - Title: {title}")
        print(f"         - Link: {article.get('link', 'N/A')[:50]}...")
        print(f"         - AI Summary: {article.get('ai_summary', 'N/A')[:60]}...")
        print()

        published += 1

    print(
        f"📝 Notion: {published}/{min(len(articles), 5)} articles would be published\n"
    )
    return published


def print_summary(collected, analyzed, filtered, published):
    print("=" * 60)
    print("📊 Summary")
    print("=" * 60)
    print(f"  Collected: {collected}")
    print(f"  Analyzed:  {analyzed}")
    print(f"  Filtered:  {filtered}")
    print(f"  Published: {published}")
    print(f"\n  ✅ Test completed successfully!")
    print(f"  💡 To run with real data, configure API keys in .env")
    print(f"  📖 See .claude/workflows/.env.example for instructions")
    print("=" * 60)


def check_dependencies():
    """Check available dependencies"""
    print("🔍 Checking dependencies...")

    deps = {
        "httpx": False,
        "beautifulsoup4": False,
        "openai": False,
        "notion-client": False,
        "pyyaml": False,
    }

    for dep in deps:
        try:
            __import__(dep.replace("-", "_"))
            deps[dep] = True
            print(f"  ✓ {dep}")
        except ImportError:
            print(f"  ✗ {dep} (will use mock)")

    print()
    return deps


def main():
    """Main entry point"""
    print_banner()

    # Check dependencies
    deps = check_dependencies()

    # Collect articles
    all_articles = []

    # Try real Reddit collection if httpx available
    if deps["httpx"]:
        try:
            sys.path.insert(
                0,
                str(
                    Path(__file__).parent.parent / "skills" / "reddit-collector" / "src"
                ),
            )
            from collector import RedditCollector

            collector = RedditCollector()
            posts = collector.collect_hot_posts("golang", limit=3, min_score=50)
            if posts:
                all_articles.extend(posts)
                print("📱 Using real Reddit data\n")
        except Exception as e:
            print(f"  ⚠️ Real Reddit collection failed: {e}\n")

    # Use mock data if no real data
    if not all_articles:
        print("📱 Using mock Reddit data...")
        all_articles.extend(mock_reddit_collector())

    # Collect RSS
    if deps["httpx"]:
        try:
            import httpx

            response = httpx.get("https://openai.com/blog/rss.xml", timeout=10)
            if response.status_code == 200:
                print("📡 Real RSS available, using mock for demo\n")
        except:
            pass

    all_articles.extend(mock_rss_collector())

    # AI Analysis
    analyzed_articles = mock_ai_analyzer(all_articles)

    # Quality filter
    filtered_articles = filter_by_quality(analyzed_articles, min_score=60)

    # Notion publish
    published_count = mock_notion_publisher(filtered_articles)

    # Summary
    print_summary(
        collected=len(all_articles),
        analyzed=len(analyzed_articles),
        filtered=len(filtered_articles),
        published=published_count,
    )

    print("\n🎉 Test completed!")
    print("\n📋 Next steps:")
    print("   1. Copy .env.example to .env")
    print("   2. Fill in your API keys (MiniMax, Notion)")
    print("   3. Run: python .claude/workflows/run.py")
    print()


if __name__ == "__main__":
    main()
