"""
Reddit Collector Skill
Collects posts from Reddit using web scraping
"""

import os
import json
from typing import List, Dict, Optional
from datetime import datetime


class RedditCollector:
    """Reddit content collector using web scraping"""

    def __init__(self):
        self.web_scraper = None
        self.rss_collector = None
        self._init_scrapers()

    def _init_scrapers(self):
        """Initialize web scraper and RSS collector"""
        try:
            from .web_scraper import RedditWebScraper, RedditRSSCollector

            self.web_scraper = RedditWebScraper()
            self.rss_collector = RedditRSSCollector()
        except Exception as e:
            print(f"Warning: Failed to initialize Reddit scrapers: {e}")

    def collect_hot_posts(
        self, subreddit: str, limit: int = 20, min_score: int = 50
    ) -> List[Dict]:
        """Collect hot posts from a subreddit"""
        if not self.web_scraper:
            return self._get_mock_posts(subreddit, limit, min_score)

        posts = self.web_scraper.collect_hot_posts(subreddit, limit, min_score)
        return posts

    def collect_new_posts(
        self, subreddit: str, limit: int = 20, min_score: int = 10
    ) -> List[Dict]:
        """Collect new posts from a subreddit"""
        if not self.web_scraper:
            return self._get_mock_posts(subreddit, limit, min_score)

        posts = self.web_scraper.collect_new_posts(subreddit, limit, min_score)
        return posts

    def collect_via_rss(
        self, subreddit: str, feed_type: str = "hot", limit: int = 20
    ) -> List[Dict]:
        """Collect posts via RSS feed"""
        if not self.rss_collector:
            return self._get_mock_posts(subreddit, limit, 50)

        posts = self.rss_collector.collect_via_rss(subreddit, feed_type, limit)
        return posts

    def _get_mock_posts(self, subreddit: str, limit: int, min_score: int) -> List[Dict]:
        """Generate mock posts for testing"""
        print(f"  📱 Using mock data for r/{subreddit}")

        mock_posts = []
        for i in range(min(limit, 5)):
            post = {
                "title": f"Sample Post from r/{subreddit} #{i + 1}",
                "link": f"https://old.reddit.com/r/{subreddit}/comments/example{i}",
                "author": f"User{i % 5 + 1}",
                "score": min_score + 10,
                "comments": 5,
                "upvote_ratio": 0.85,
                "created_utc": datetime.now().timestamp(),
                "created_date": datetime.now().isoformat(),
                "self_text": f"This is a sample post about AI and technology from r/{subreddit}",
                "url": "",
                "subreddit": subreddit,
                "is_self": True,
                "domain": "reddit.com",
                "source_type": "reddit",
            }
            mock_posts.append(post)

        return mock_posts


def main():
    """Main entry point for CLI usage"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m reddit_collector <command> [args]")
        print("Commands: hot, new, rss")
        return

    command = sys.argv[1]
    collector = RedditCollector()

    if command == "hot":
        if len(sys.argv) < 3:
            print("Usage: hot <subreddit> [limit] [min_score]")
            return
        subreddit = sys.argv[2]
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
        min_score = int(sys.argv[4]) if len(sys.argv) > 4 else 50

        posts = collector.collect_hot_posts(subreddit, limit, min_score)
        print(json.dumps(posts, indent=2, ensure_ascii=False))

    elif command == "new":
        if len(sys.argv) < 3:
            print("Usage: new <subreddit> [limit] [min_score]")
            return
        subreddit = sys.argv[2]
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
        min_score = int(sys.argv[4]) if len(sys.argv) > 4 else 10

        posts = collector.collect_new_posts(subreddit, limit, min_score)
        print(json.dumps(posts, indent=2, ensure_ascii=False))

    elif command == "rss":
        if len(sys.argv) < 3:
            print("Usage: rss <subreddit> [feed_type] [limit]")
            return
        subreddit = sys.argv[2]
        feed_type = sys.argv[3] if len(sys.argv) > 3 else "hot"
        limit = int(sys.argv[4]) if len(sys.argv) > 4 else 20

        posts = collector.collect_via_rss(subreddit, feed_type, limit)
        print(json.dumps(posts, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
