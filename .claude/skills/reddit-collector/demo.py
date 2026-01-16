#!/usr/bin/env python3
"""
Reddit Collector Demo Script

This script demonstrates how to use the Reddit Collector skill to gather posts
from various subreddits.

Usage:
    python3 demo.py                    # Run all examples
    python3 demo.py hot                # Collect hot posts
    python3 demo.py new                # Collect new posts
    python3 demo.py rss                # Collect via RSS
    python3 demo.py batch              # Collect from multiple subreddits
"""

import json
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import collector directly
import collector
RedditCollector = collector.RedditCollector


def print_separator(title=""):
    """Print a visual separator"""
    print("\n" + "=" * 60)
    if title:
        print(f"  {title}")
        print("=" * 60)


def demo_hot_posts():
    """Demo: Collect hot posts from a subreddit"""
    print_separator("🔥 Collecting Hot Posts")

    collector = RedditCollector()
    posts = collector.collect_hot_posts(
        subreddit="ArtificialIntelligence",
        limit=5,
        min_score=50
    )

    print(f"\n✓ Collected {len(posts)} hot posts from r/ArtificialIntelligence")
    print("\nTop 3 posts:")
    for i, post in enumerate(posts[:3], 1):
        print(f"\n{i}. {post['title']}")
        print(f"   Score: {post['score']} | Comments: {post['comments']}")
        print(f"   Author: {post['author']}")

    return posts


def demo_new_posts():
    """Demo: Collect new posts from a subreddit"""
    print_separator("🆕 Collecting New Posts")

    collector = RedditCollector()
    posts = collector.collect_new_posts(
        subreddit="Python",
        limit=5,
        min_score=10
    )

    print(f"\n✓ Collected {len(posts)} new posts from r/Python")
    print("\nLatest posts:")
    for i, post in enumerate(posts[:3], 1):
        print(f"\n{i}. {post['title']}")
        print(f"   Score: {post['score']} | Comments: {post['comments']}")
        print(f"   Link: {post['link']}")

    return posts


def demo_rss_feed():
    """Demo: Collect posts via RSS feed"""
    print_separator("📡 Collecting via RSS Feed")

    collector = RedditCollector()
    posts = collector.collect_via_rss(
        subreddit="golang",
        feed_type="hot",
        limit=5
    )

    print(f"\n✓ Collected {len(posts)} posts via RSS from r/golang")
    print("\nPosts from RSS:")
    for i, post in enumerate(posts[:3], 1):
        print(f"\n{i}. {post['title']}")
        print(f"   Published: {post.get('created_date', 'Unknown')}")

    return posts


def demo_batch_collection():
    """Demo: Collect from multiple subreddits"""
    print_separator("📦 Batch Collection from Multiple Subreddits")

    collector = RedditCollector()

    subreddits = [
        {"name": "ArtificialIntelligence", "category": "AI", "limit": 3},
        {"name": "Programming", "category": "Programming", "limit": 3},
        {"name": "MachineLearning", "category": "ML", "limit": 3},
    ]

    all_posts = []

    for sub_config in subreddits:
        print(f"\n📥 Collecting from r/{sub_config['name']}...")
        posts = collector.collect_hot_posts(
            subreddit=sub_config['name'],
            limit=sub_config['limit'],
            min_score=50
        )

        # Add category to each post
        for post in posts:
            post['category'] = sub_config['category']

        all_posts.extend(posts)
        print(f"   ✓ Got {len(posts)} posts")

    print_separator(f"✓ Total: {len(all_posts)} posts collected")

    # Save to file
    output_file = Path(__file__).parent / "output" / "reddit_posts.json"
    output_file.parent.mkdir(exist_ok=True)
    output_file.write_text(json.dumps(all_posts, indent=2, ensure_ascii=False))
    print(f"\n💾 Saved to: {output_file}")

    return all_posts


def demo_filter_and_sort():
    """Demo: Filter and sort posts"""
    print_separator("🔍 Filtering and Sorting Posts")

    collector = RedditCollector()
    posts = collector.collect_hot_posts(
        subreddit="LocalLLaMA",
        limit=10,
        min_score=100
    )

    # Filter posts with high engagement
    high_engagement = [p for p in posts if p['comments'] > 10]
    print(f"\n📊 High engagement posts ({len(high_engagement)} posts):")

    # Sort by score
    high_engagement.sort(key=lambda x: x['score'], reverse=True)

    for i, post in enumerate(high_engagement[:5], 1):
        print(f"\n{i}. {post['title']}")
        print(f"   Score: {post['score']} | Comments: {post['comments']}")
        print(f"   Ratio: {post.get('upvote_ratio', 0):.2f}")

    return high_engagement


def print_post_summary(posts, title="Post Summary"):
    """Print a summary of collected posts"""
    print_separator(title)

    if not posts:
        print("No posts collected")
        return

    # Stats
    total_score = sum(p.get('score', 0) for p in posts)
    total_comments = sum(p.get('comments', 0) for p in posts)
    avg_score = total_score / len(posts) if posts else 0

    print(f"\n📈 Statistics:")
    print(f"   Total posts: {len(posts)}")
    print(f"   Total score: {total_score}")
    print(f"   Total comments: {total_comments}")
    print(f"   Average score: {avg_score:.1f}")

    # Top post
    if posts:
        top_post = max(posts, key=lambda x: x.get('score', 0))
        print(f"\n🏆 Top post:")
        print(f"   Title: {top_post['title']}")
        print(f"   Score: {top_post['score']}")
        print(f"   Link: {top_post['link']}")


def main():
    """Main entry point"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║          Reddit Collector - Demo & Examples               ║
╚═══════════════════════════════════════════════════════════╝
    """)

    # Determine which demo to run
    demo = sys.argv[1] if len(sys.argv) > 1 else "all"

    if demo == "hot":
        posts = demo_hot_posts()
        print_post_summary(posts)

    elif demo == "new":
        posts = demo_new_posts()
        print_post_summary(posts)

    elif demo == "rss":
        posts = demo_rss_feed()
        print_post_summary(posts)

    elif demo == "batch":
        posts = demo_batch_collection()

    elif demo == "filter":
        posts = demo_filter_and_sort()
        print_post_summary(posts)

    else:  # Run all demos
        print("\n🚀 Running all demos...\n")

        demo_hot_posts()
        demo_new_posts()
        demo_rss_feed()
        demo_batch_collection()
        demo_filter_and_sort()

        print_separator("✅ All demos completed!")
        print("""
💡 Tips:
  - Install dependencies for real data: pip install httpx beautifulsoup4 feedparser
  - Currently using mock data for demonstration
  - Adjust min_score parameter to filter by quality
  - Use RSS mode for more stable collection
  - Check the output/ directory for saved results
        """)


if __name__ == "__main__":
    main()
