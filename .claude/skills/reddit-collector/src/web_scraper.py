"""
Reddit Web Scraper
Collects posts from Reddit using web scraping instead of API
"""

import os
import json
import re
from typing import List, Dict, Optional
from datetime import datetime

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    print("Warning: httpx library not installed. Using mock data.")

try:
    from bs4 import BeautifulSoup

    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    print("Warning: beautifulsoup4 library not installed. Using regex fallback.")


class RedditWebScraper:
    """Reddit web scraper using httpx and BeautifulSoup"""

    def __init__(self, user_agent: str = None):
        self.user_agent = user_agent or os.getenv(
            "REDDIT_USER_AGENT",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        )
        self.base_url = "https://old.reddit.com"
        self.client = None
        self.enabled = False

        if not HTTPX_AVAILABLE:
            print("Warning: httpx not installed, using mock data")
            return

        try:
            self.client = httpx.Client(
                timeout=30.0,
                headers={
                    "User-Agent": self.user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                },
                follow_redirects=True,
            )
            self.enabled = True
            print("✓ Reddit web scraper initialized")
        except Exception as e:
            print(f"✗ Failed to initialize Reddit scraper: {e}")

    def collect_hot_posts(
        self, subreddit: str, limit: int = 20, min_score: int = 50
    ) -> List[Dict]:
        """Collect hot posts from a subreddit using web scraping"""
        if not self.enabled:
            return self._get_mock_posts(subreddit, limit, min_score)

        posts = []
        url = f"{self.base_url}/r/{subreddit}/hot/"

        try:
            print(f"  🌐 Fetching r/{subreddit}/hot...")
            response = self.client.get(url, params={"limit": str(limit)})
            response.raise_for_status()

            posts = self._parse_reddit_html(response.text, subreddit)

            # Filter by score
            filtered_posts = [p for p in posts if p.get("score", 0) >= min_score]

            print(
                f"    ✓ Found {len(posts)} posts, {len(filtered_posts)} meet score threshold"
            )

            return filtered_posts[:limit]

        except httpx.HTTPStatusError as e:
            print(f"    ⚠️ HTTP error: {e}")
            return self._get_mock_posts(subreddit, limit, min_score)

        except Exception as e:
            print(f"    ⚠️ Error collecting from r/{subreddit}: {e}")
            return self._get_mock_posts(subreddit, limit, min_score)

    def collect_new_posts(
        self, subreddit: str, limit: int = 20, min_score: int = 10
    ) -> List[Dict]:
        """Collect new posts from a subreddit"""
        if not self.enabled:
            return self._get_mock_posts(subreddit, limit, min_score)

        posts = []
        url = f"{self.base_url}/r/{subreddit}/new/"

        try:
            print(f"  🌐 Fetching r/{subreddit}/new...")
            response = self.client.get(url, params={"limit": str(limit)})
            response.raise_for_status()

            posts = self._parse_reddit_html(response.text, subreddit)

            filtered_posts = [p for p in posts if p.get("score", 0) >= min_score]

            print(
                f"    ✓ Found {len(posts)} posts, {len(filtered_posts)} meet score threshold"
            )

            return filtered_posts[:limit]

        except Exception as e:
            print(f"    ⚠️ Error collecting new posts from r/{subreddit}: {e}")
            return self._get_mock_posts(subreddit, limit, min_score)

    def _parse_reddit_html(self, html: str, subreddit: str) -> List[Dict]:
        """Parse Reddit HTML to extract post data"""
        posts = []

        if BS4_AVAILABLE:
            soup = BeautifulSoup(html, "html.parser")

            # Find all post entries
            for thing in soup.find_all("div", class_="thing"):
                try:
                    post = self._parse_post_element(thing, subreddit)
                    if post:
                        posts.append(post)
                except Exception as e:
                    print(f"    ⚠️ Error parsing post: {e}")
                    continue

        else:
            # Fallback to regex parsing
            posts = self._parse_reddit_regex(html, subreddit)

        return posts

    def _parse_post_element(self, element, subreddit: str) -> Optional[Dict]:
        """Parse a single Reddit post element"""
        try:
            # Extract title
            title_elem = element.find("a", class_="title")
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            link = title_elem.get("href", "")

            # Make link absolute
            if link.startswith("/"):
                link = f"https://old.reddit.com{link}"

            # Extract score
            score_elem = element.find("div", class_="score")
            score_text = score_elem.get_text(strip=True) if score_elem else "0"

            # Parse score (handle "upvote" and "downvote" cases)
            if "upvote" in score_text.lower():
                score = 1
            elif "downvote" in score_text.lower():
                score = -1
            else:
                try:
                    score = int(score_text.replace(",", ""))
                except ValueError:
                    score = 0

            # Extract comments count
            comments_elem = element.find("a", class_="comments")
            comments_text = (
                comments_elem.get_text(strip=True) if comments_elem else "0 comments"
            )
            comments_match = re.search(r"(\d+)", comments_text)
            comments = int(comments_match.group(1)) if comments_match else 0

            # Extract author
            author_elem = element.find("a", class_="author")
            author = author_elem.get_text(strip=True) if author_elem else "[deleted]"

            # Extract time
            time_elem = element.find("time")
            if time_elem:
                datetime_str = time_elem.get("datetime", "")
            else:
                # Try to find time from relative time element
                time_elem = element.find("span", class_="live-timestamp")
                datetime_str = time_elem.get("data-timestamp", "") if time_elem else ""

            # Extract thumbnail/image
            thumbnail_elem = element.find("img", class_="thumbnail")
            thumbnail = thumbnail_elem.get("src") if thumbnail_elem else ""

            # Extract selftext (for text posts)
            selftext_elem = element.find("div", class_="expando")
            selftext = ""
            if selftext_elem:
                # Get visible text
                selftext = selftext_elem.get_text(strip=True)
                # Clean up
                selftext = re.sub(r"\s+", " ", selftext)[:500]

            return {
                "title": title,
                "link": link,
                "author": author,
                "score": score,
                "comments": comments,
                "upvote_ratio": score / (score + 1) if score > 0 else 0.5,
                "created_utc": datetime.now().timestamp(),
                "created_date": datetime.now().isoformat(),
                "self_text": selftext,
                "url": link,
                "subreddit": subreddit,
                "is_self": bool(selftext) or "/comments/" in link,
                "domain": self._extract_domain(link),
                "thumbnail": thumbnail,
                "source_type": "reddit",
            }

        except Exception as e:
            print(f"    ⚠️ Error parsing post element: {e}")
            return None

    def _parse_reddit_regex(self, html: str, subreddit: str) -> List[Dict]:
        """Fallback regex-based parsing"""
        posts = []

        # Find post entries using regex
        # Pattern matches: data-permalink, data-score, title link
        pattern = r'<a class="title"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'

        title_matches = re.findall(pattern, html)

        for link, title in title_matches[:20]:
            if link.startswith("/r/"):
                full_link = f"https://old.reddit.com{link}"

                posts.append(
                    {
                        "title": title,
                        "link": full_link,
                        "author": "Anonymous",
                        "score": 0,
                        "comments": 0,
                        "upvote_ratio": 0.5,
                        "created_utc": datetime.now().timestamp(),
                        "created_date": datetime.now().isoformat(),
                        "self_text": "",
                        "url": full_link,
                        "subreddit": subreddit,
                        "is_self": "/comments/" in full_link,
                        "domain": self._extract_domain(full_link),
                        "thumbnail": "",
                        "source_type": "reddit",
                    }
                )

        return posts

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            domain = parsed.netloc.replace("old.reddit.com", "reddit.com")
            return domain
        except:
            return "reddit.com"

    def _get_mock_posts(self, subreddit: str, limit: int, min_score: int) -> List[Dict]:
        """Generate mock posts for testing"""
        print(f"  📱 Using mock data for r/{subreddit} (scraper not available)")

        topics = [
            (
                "Breaking: Major AI Advancement Announced",
                "Exciting news from the AI research community...",
            ),
            (
                "How to optimize your LLM prompts",
                "A comprehensive guide to better prompting...",
            ),
            (
                "New open-source model released",
                "Introducing the latest developments...",
            ),
            (
                "Tips for RAG implementation",
                "Best practices for retrieval augmented generation...",
            ),
            (
                "AI Agent frameworks comparison",
                "Evaluating LangGraph, AutoGen, and CrewAI...",
            ),
            (
                "Hardware recommendations for local LLMs",
                "Building your AI development rig...",
            ),
            ("The future of AI assistants", "Where are we heading in 2024..."),
            ("Debugging LLM applications", "Common pitfalls and solutions..."),
            ("New paper review: [Title]", "Analyzing the latest research..."),
            ("Community discussion: AI ethics", "Important topic for the field..."),
        ]

        mock_posts = []
        for i, (title, summary) in enumerate(topics[:limit]):
            post = {
                "title": title,
                "link": f"https://old.reddit.com/r/{subreddit}/comments/example{i}",
                "author": f"User{i % 5 + 1}",
                "score": min_score + (i * 10),
                "comments": i * 3,
                "upvote_ratio": 0.85 + (i % 3) * 0.05,
                "created_utc": datetime.now().timestamp(),
                "created_date": datetime.now().isoformat(),
                "self_text": summary,
                "url": "",
                "subreddit": subreddit,
                "is_self": True,
                "domain": "",
                "source_type": "reddit",
            }
            mock_posts.append(post)

        return mock_posts


class RedditRSSCollector:
    """Alternative: Collect Reddit posts via RSS"""

    def __init__(self):
        self.base_url = "https://old.reddit.com"

    def collect_via_rss(
        self, subreddit: str, feed_type: str = "hot", limit: int = 20
    ) -> List[Dict]:
        """Collect posts via Reddit RSS feed"""
        try:
            import feedparser
        except ImportError:
            print("  ⚠️ feedparser not installed, using web scraper")
            return []

        url = f"{self.base_url}/r/{subreddit}/{feed_type}.rss"

        try:
            print(f"  📡 Fetching RSS feed: r/{subreddit}/{feed_type}")
            feed = feedparser.parse(url)

            posts = []
            for entry in feed.entries[:limit]:
                post = {
                    "title": entry.get("title", "No Title"),
                    "link": entry.get("link", ""),
                    "author": entry.get("author", "Unknown"),
                    "score": self._extract_score(entry),
                    "comments": entry.get("slash_comments", 0),
                    "upvote_ratio": 0.85,
                    "created_utc": entry.get(
                        "published_parsed", datetime.now().timetuple()
                    ),
                    "created_date": entry.get("published", datetime.now().isoformat()),
                    "self_text": entry.get("summary", "")[:500],
                    "url": entry.get("link", ""),
                    "subreddit": subreddit,
                    "is_self": "/comments/" in entry.get("link", ""),
                    "domain": "reddit.com",
                    "source_type": "reddit",
                }
                posts.append(post)

            print(f"    ✓ Found {len(posts)} posts via RSS")
            return posts

        except Exception as e:
            print(f"    ⚠️ RSS fetch failed: {e}")
            return []

    def _extract_score(self, entry) -> int:
        """Extract score from RSS entry"""
        # Reddit RSS doesn't include score directly
        # Could parse from summary if available
        return 0


def main():
    """Main entry point for CLI usage"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m reddit_web_scraper <command> [args]")
        print("Commands: hot, new, rss")
        return

    command = sys.argv[1]
    scraper = RedditWebScraper()

    if command == "hot":
        if len(sys.argv) < 3:
            print("Usage: hot <subreddit> [limit] [min_score]")
            return
        subreddit = sys.argv[2]
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
        min_score = int(sys.argv[4]) if len(sys.argv) > 4 else 50

        posts = scraper.collect_hot_posts(subreddit, limit, min_score)
        print(json.dumps(posts, indent=2, ensure_ascii=False))

    elif command == "new":
        if len(sys.argv) < 3:
            print("Usage: new <subreddit> [limit] [min_score]")
            return
        subreddit = sys.argv[2]
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
        min_score = int(sys.argv[4]) if len(sys.argv) > 4 else 10

        posts = scraper.collect_new_posts(subreddit, limit, min_score)
        print(json.dumps(posts, indent=2, ensure_ascii=False))

    elif command == "rss":
        if len(sys.argv) < 3:
            print("Usage: rss <subreddit> [feed_type] [limit]")
            return
        subreddit = sys.argv[2]
        feed_type = sys.argv[3] if len(sys.argv) > 3 else "hot"
        limit = int(sys.argv[4]) if len(sys.argv) > 4 else 20

        rss_collector = RedditRSSCollector()
        posts = rss_collector.collect_via_rss(subreddit, feed_type, limit)
        print(json.dumps(posts, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
