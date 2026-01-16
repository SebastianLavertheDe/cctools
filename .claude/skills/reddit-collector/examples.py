#!/usr/bin/env python3
"""
Reddit Collector - Practical Examples

This script shows practical use cases for collecting and processing Reddit posts.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import collector
RedditCollector = collector.RedditCollector


def example_collect_tech_news():
    """
    Example 1: Collect tech news from multiple subreddits
    Useful for daily tech news aggregation
    """
    print("\n" + "="*60)
    print("Example 1: Collecting Tech News")
    print("="*60)

    collector = RedditCollector()

    tech_subreddits = [
        {"subreddit": "ArtificialIntelligence", "category": "AI"},
        {"subreddit": "MachineLearning", "category": "ML"},
        {"subreddit": "programming", "category": "Programming"},
        {"subreddit": "technology", "category": "Tech"},
    ]

    all_posts = []

    for config in tech_subreddits:
        print(f"\n📥 Collecting from r/{config['subreddit']}...")
        posts = collector.collect_hot_posts(
            subreddit=config['subreddit'],
            limit=5,
            min_score=100
        )

        for post in posts:
            post['category'] = config['category']

        all_posts.extend(posts)

    # Save results
    output = Path(__file__).parent / "output" / "tech_news.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(all_posts, indent=2, ensure_ascii=False))

    print(f"\n✅ Saved {len(all_posts)} posts to {output.name}")

    # Print summary
    print("\n📊 Summary by category:")
    categories = {}
    for post in all_posts:
        cat = post.get('category', 'Unknown')
        categories[cat] = categories.get(cat, 0) + 1

    for cat, count in sorted(categories.items()):
        print(f"   {cat}: {count} posts")

    return all_posts


def example_find_quality_discussions():
    """
    Example 2: Find high-quality discussions
    Filter for posts with high engagement (score + comments)
    """
    print("\n" + "="*60)
    print("Example 2: Finding Quality Discussions")
    print("="*60)

    collector = RedditCollector()

    # Collect more posts to filter
    posts = collector.collect_hot_posts(
        subreddit="ArtificialIntelligence",
        limit=30,
        min_score=50
    )

    # Calculate engagement score
    for post in posts:
        post['engagement'] = post['score'] + (post['comments'] * 2)

    # Filter for high engagement
    quality_posts = [p for p in posts if p['engagement'] > 200]

    # Sort by engagement
    quality_posts.sort(key=lambda x: x['engagement'], reverse=True)

    print(f"\n🎯 Found {len(quality_posts)} high-quality discussions")
    print("\nTop 5 by engagement:")

    for i, post in enumerate(quality_posts[:5], 1):
        print(f"\n{i}. {post['title'][:80]}...")
        print(f"   Score: {post['score']} | Comments: {post['comments']}")
        print(f"   Engagement: {post['engagement']}")
        print(f"   Link: {post['link']}")

    return quality_posts


def example_extract_external_articles():
    """
    Example 3: Extract external article links
    Find posts that link to external articles (not self posts)
    """
    print("\n" + "="*60)
    print("Example 3: Extracting External Articles")
    print("="*60)

    collector = RedditCollector()

    posts = collector.collect_hot_posts(
        subreddit="MachineLearning",
        limit=20,
        min_score=50
    )

    # Filter for external links
    external_articles = []
    for post in posts:
        # Skip self posts and reddit links
        if not post.get('is_self') and post.get('url'):
            url = post['url']
            if 'reddit.com' not in url and url.startswith('http'):
                external_articles.append({
                    'title': post['title'],
                    'url': url,
                    'score': post['score'],
                    'source': f"r/{post['subreddit']}",
                    'comments': post['comments']
                })

    print(f"\n📰 Found {len(external_articles)} external articles")

    # Save article list for content extraction
    output = Path(__file__).parent / "output" / "articles_to_extract.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(external_articles, indent=2, ensure_ascii=False))

    print(f"\n💾 Saved article list to {output.name}")
    print("\nYou can now use content-extractor skill on these URLs")

    for i, article in enumerate(external_articles[:5], 1):
        print(f"\n{i}. {article['title'][:70]}...")
        print(f"   URL: {article['url']}")
        print(f"   Score: {article['score']}")

    return external_articles


def example_monitor_trending_topics():
    """
    Example 4: Monitor trending topics by frequency
    Analyze post titles to find trending keywords
    """
    print("\n" + "="*60)
    print("Example 4: Monitoring Trending Topics")
    print("="*60)

    collector = RedditCollector()

    # Collect from multiple AI-related subreddits
    subreddits = ["ArtificialIntelligence", "MachineLearning", "deeplearning"]
    all_posts = []

    for sub in subreddits:
        posts = collector.collect_hot_posts(sub, limit=15, min_score=50)
        all_posts.extend(posts)

    # Extract keywords from titles
    keywords = {}

    common_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
        'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are',
        'this', 'that', 'it', 'new', 'how', 'what', 'why', 'use'
    }

    for post in all_posts:
        words = post['title'].lower().split()
        for word in words:
            # Clean word
            word = ''.join(c for c in word if c.isalnum())
            if len(word) > 3 and word not in common_words:
                keywords[word] = keywords.get(word, 0) + 1

    # Sort by frequency
    trending = sorted(keywords.items(), key=lambda x: x[1], reverse=True)

    print(f"\n📈 Analyzed {len(all_posts)} posts from {len(subreddits)} subreddits")
    print("\n🔥 Top 10 trending keywords:")

    for i, (keyword, count) in enumerate(trending[:10], 1):
        print(f"{i:2d}. {keyword:20s} ({count} posts)")

    return trending


def example_daily_digest():
    """
    Example 5: Create a daily digest
    Collect top posts and format as a readable digest
    """
    print("\n" + "="*60)
    print("Example 5: Creating Daily Digest")
    print("="*60)

    collector = RedditCollector()

    # Collect from various tech subreddits
    sources = {
        "ArtificialIntelligence": "AI & ML",
        "programming": "Programming",
        "golang": "Golang",
        "Python": "Python"
    }

    digest = {
        'date': datetime.now().isoformat(),
        'sections': []
    }

    for subreddit, section_name in sources.items():
        posts = collector.collect_hot_posts(subreddit, limit=3, min_score=100)

        section = {
            'name': section_name,
            'subreddit': subreddit,
            'posts': []
        }

        for post in posts:
            section['posts'].append({
                'title': post['title'],
                'score': post['score'],
                'comments': post['comments'],
                'link': post['link']
            })

        digest['sections'].append(section)

    # Save digest
    output = Path(__file__).parent / "output" / "daily_digest.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(digest, indent=2, ensure_ascii=False))

    print(f"\n📰 Daily Digest - {digest['date'][:10]}")
    print("="*60)

    for section in digest['sections']:
        print(f"\n📌 {section['name']} (r/{section['subreddit']})")
        print("-" * 40)

        for i, post in enumerate(section['posts'], 1):
            print(f"\n{i}. {post['title'][:70]}...")
            print(f"   ⬆️  {post['score']} | 💬 {post['comments']}")

    print(f"\n\n💾 Full digest saved to {output.name}")

    return digest


def main():
    """Run all examples"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║        Reddit Collector - Practical Examples               ║
╚═══════════════════════════════════════════════════════════╝
    """)

    examples = [
        ("1", "Collect Tech News", example_collect_tech_news),
        ("2", "Find Quality Discussions", example_find_quality_discussions),
        ("3", "Extract External Articles", example_extract_external_articles),
        ("4", "Monitor Trending Topics", example_monitor_trending_topics),
        ("5", "Create Daily Digest", example_daily_digest),
    ]

    # If argument provided, run that example
    if len(sys.argv) > 1:
        example_num = sys.argv[1]
        for num, name, func in examples:
            if num == example_num:
                func()
                return
        print(f"Unknown example: {example_num}")
        return

    # Run all examples
    for num, name, func in examples:
        try:
            func()
        except Exception as e:
            print(f"\n❌ Error in {name}: {e}")
            continue

    print("\n" + "="*60)
    print("✅ All examples completed!")
    print("="*60)

    print("""
💡 Tips:
  - Check the output/ directory for saved results
  - Modify parameters to customize collection
  - Integrate with content-extractor for full article text
  - Use ai-content-analyzer to score and categorize
  - Publish to Notion with notion-publisher

📚 Available examples:
  python3 examples.py 1    # Collect tech news
  python3 examples.py 2    # Find quality discussions
  python3 examples.py 3    # Extract external articles
  python3 examples.py 4    # Monitor trending topics
  python3 examples.py 5    # Create daily digest
    """)


if __name__ == "__main__":
    main()
