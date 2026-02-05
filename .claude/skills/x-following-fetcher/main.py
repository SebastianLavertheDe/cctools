"""
X Following Fetcher - Fetches latest posts from X (Twitter) users you follow
and saves them to Markdown format.
"""
import json
import re
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

OUTPUT_DIR = Path("/home/say/work/github/cctools/mymind/post")
X_CURL_FILE = Path(__file__).parent / "curl.txt"
CACHE_FILE = Path(__file__).parent / "posted_ids.json"


def parse_twitter_date(twitter_date: str) -> str:
    """Convert Twitter date format to ISO 8601 format"""
    try:
        # Twitter format: "Wed Jan 21 13:59:24 +0000 2026"
        dt = datetime.strptime(twitter_date, "%a %b %d %H:%M:%S %z %Y")
        return dt.isoformat()
    except Exception:
        return twitter_date


def execute_curl_from_file() -> subprocess.CompletedProcess:
    """从 curl.txt 读取 curl 命令并执行"""
    if not X_CURL_FILE.exists():
        raise FileNotFoundError(f"curl 文件不存在: {X_CURL_FILE}")

    with open(X_CURL_FILE, "r", encoding="utf-8") as f:
        curl_content = f.read().strip()

    curl_cmd = curl_content.replace("\\\n", " ").replace("\\\r\n", " ")
    cmd_list = shlex.split(curl_cmd)
    return subprocess.run(
        cmd_list,
        capture_output=True,
        text=True,
        timeout=120,
    )


def parse_tweet_entry(entry: dict[str, Any]) -> dict[str, Any] | None:
    try:
        content = entry.get("content", {})
        tweet = content.get("itemContent", {})

        if tweet.get("__typename") == "TweetTombstone":
            return None

        tweet_results = tweet.get("tweet_results", {})
        if not tweet_results:
            return None

        result = tweet_results.get("result", {})
        legacy = result.get("legacy", {})
        if not legacy:
            return None

        core = result.get("core", {})
        user_results = core.get("user_results", {}).get("result", {})
        user_core = user_results.get("core", {})
        user_legacy = user_results.get("legacy", {})
        user = user_core or user_legacy or {}

        user_name = user.get("name", "")
        user_screen_name = user.get("screen_name", "")
        user_verified = user_results.get("is_blue_verified", False) if user_results else False

        avatar = user_results.get("avatar", {}) if user_results else {}
        profile_image_url = avatar.get("image_url", "") if avatar else ""

        extended_entities = legacy.get("extended_entities", {})
        media = extended_entities.get("media", [])
        image_urls = [
            m.get("media_url_https", m.get("media_url", ""))
            for m in media
            if m.get("type") == "photo"
        ]

        tweet_id = legacy.get("id_str", "")
        tweet_url = (
            f"https://x.com/{user_screen_name}/status/{tweet_id}"
            if user_screen_name and tweet_id
            else ""
        )

        return {
            "id": tweet_id,
            "user_name": user_name,
            "user_screen_name": user_screen_name,
            "user_verified": user_verified,
            "profile_image_url": profile_image_url,
            "content": legacy.get("full_text", ""),
            "created_at": parse_twitter_date(legacy.get("created_at", "")),
            "retweet_count": legacy.get("retweet_count", 0),
            "like_count": legacy.get("favorite_count", 0),
            "reply_count": legacy.get("reply_count", 0),
            "quote_count": legacy.get("quote_count", 0),
            "bookmark_count": legacy.get("bookmark_count", 0),
            "lang": legacy.get("lang", ""),
            "source": "x.com",
            "image_urls": image_urls,
            "link": tweet_url,
            "title": "",
        }
    except Exception as e:
        print(f"  ⚠️ Parse error: {e}")
        return None


def fetch_tweets() -> list[dict[str, Any]]:
    try:
        result = execute_curl_from_file()
        if result.returncode != 0:
            print(f"Error fetching tweets: {result.stderr}", file=sys.stderr)
            return []

        response = json.loads(result.stdout)
        instructions = (
            response.get("data", {})
            .get("home", {})
            .get("home_timeline_urt", {})
            .get("instructions", [])
        )

        tweets = []
        seen_ids = set()
        for instruction in instructions:
            if instruction.get("type") == "TimelineAddEntries":
                entries = instruction.get("entries", [])
                for entry in entries:
                    content = entry.get("content", {})
                    if content.get("__typename") == "TimelineTimelineItem":
                        tweet_data = parse_tweet_entry(entry)
                        if tweet_data and tweet_data["id"] not in seen_ids:
                            seen_ids.add(tweet_data["id"])
                            tweets.append(tweet_data)
        return tweets
    except subprocess.TimeoutExpired:
        print("Error: Request timed out", file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Error fetching tweets: {e}", file=sys.stderr)
        return []


def load_cached_ids() -> set:
    if not CACHE_FILE.exists():
        return set()
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data.get("ids", []))
    except Exception:
        return set()


def save_cached_ids(ids: set) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump({"ids": sorted(ids)}, f, ensure_ascii=False, indent=2)


def sanitize_filename(name: str) -> str:
    """Sanitize username for filename"""
    # Remove invalid filesystem characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, "_")
    # Remove protocol prefixes if present
    name = re.sub(r'^https?[_:]', '', name)
    # Clean up multiple underscores
    name = re.sub(r'_+', '_', name)
    return name.strip('_').strip()


def clean_tweet_id(tweet_id: str) -> str:
    """Clean tweet ID for filename use"""
    # Remove RAW_ prefix if present
    if tweet_id.startswith("RAW_"):
        tweet_id = tweet_id[4:]
    # Extract numeric ID if it's a URL
    # Pattern: https://www.bestblogs.dev/feeds/123456789
    match = re.search(r'/(\d{10,})', tweet_id)
    if match:
        return match.group(1)
    # Fallback: just sanitize the ID
    return sanitize_filename(tweet_id)


def tweet_to_markdown(tweet: dict[str, Any]) -> str:
    """Convert tweet dict to markdown format"""
    lines = []

    # Title: use title if available, otherwise use first line of content
    title = tweet.get("title") or ""
    content = tweet.get("content", "")

    # Clean up title by removing extra whitespace
    if title:
        title = re.sub(r'\s+', ' ', title).strip()
        lines.append(f"# {title}\n")
    else:
        # Use first line of content as title
        first_line = content.split('\n')[0].strip()
        if first_line:
            lines.append(f"# {first_line}\n")

    # Metadata section
    lines.append("## 元数据\n")
    lines.append(f"- **链接**: {tweet.get('link', '')}")
    lines.append(f"- **作者**: {tweet.get('user_name', '')} (@{tweet.get('user_screen_name', '')})")
    lines.append(f"- **发布时间**: {tweet.get('created_at', '')}")
    lines.append(f"- **保存时间**: {tweet.get('fetched_at', '')}")
    lines.append(f"- **来源**: {tweet.get('source', '')}")
    lines.append(f"- **ID**: {tweet.get('id', '')}\n")

    # Images section
    image_urls = tweet.get("image_urls", [])
    if image_urls:
        lines.append("## 图片\n")
        for img_url in image_urls:
            lines.append(f"![]({img_url})")
        lines.append("")

    # Content section
    if content:
        lines.append("## 正文\n")
        lines.append(content)
        lines.append("")

    # Metrics section
    lines.append("## 互动数据\n")
    lines.append(f"- 👍 点赞: {tweet.get('like_count', 0)}")
    lines.append(f"- 🔄 转发: {tweet.get('retweet_count', 0)}")
    lines.append(f"- 💬 回复: {tweet.get('reply_count', 0)}")
    lines.append(f"- 📎 引用: {tweet.get('quote_count', 0)}")
    lines.append("")

    # Tweet embed link
    lines.append("---")
    lines.append(f"\n[查看原推]({tweet.get('link', '')})\n")

    return "\n".join(lines)


def save_to_markdown(tweets: list[dict[str, Any]]) -> tuple[int, int]:
    existing_ids = load_cached_ids()
    new_tweets = [t for t in tweets if t["id"] not in existing_ids]

    if not new_tweets:
        print("没有新增帖子")
        return 0, 0

    print(f"发现 {len(new_tweets)} 条新帖子")

    # Create date directory
    date_str = datetime.now().strftime("%Y%m%d")
    date_dir = OUTPUT_DIR / date_str
    date_dir.mkdir(parents=True, exist_ok=True)

    # Sort new tweets by created_at (ascending) for stable numbering
    def sort_key(t: dict[str, Any]):
        return (t.get("created_at", ""), t.get("id", ""))

    new_tweets.sort(key=sort_key)

    # Determine starting index based on existing files in today's directory
    start_index = 0
    for md_file in date_dir.glob("*.md"):
        match = re.match(r'(\d+)_', md_file.name)
        if match:
            try:
                start_index = max(start_index, int(match.group(1)))
            except Exception:
                continue

    for i, tweet in enumerate(new_tweets, start=start_index + 1):
        print(f"  处理 {i-start_index}/{len(new_tweets)}: @{tweet['user_screen_name']}")
        tweet["fetched_at"] = datetime.now().isoformat()

        # Generate filename: HHMMSS_username_id.md
        try:
            created_dt = datetime.fromisoformat(tweet["created_at"])
        except Exception:
            created_dt = datetime.now()
        time_str = created_dt.strftime("%H%M%S")
        username = sanitize_filename(tweet["user_screen_name"])
        clean_id = clean_tweet_id(tweet["id"])
        filename = f"{i}_{username}_{clean_id}.md"
        output_file = date_dir / filename

        # Convert tweet to markdown and save
        markdown_content = tweet_to_markdown(tweet)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        existing_ids.add(tweet["id"])

    print(f"\n已保存到: {date_dir}")
    print(f"新增: {len(new_tweets)} 条")

    # Count total tweets in date directory
    total_count = len(list(date_dir.glob("*.md")))
    print(f"目录总计: {total_count} 条")

    save_cached_ids(existing_ids)
    return len(new_tweets), total_count


def main():
    print("Fetching latest posts from X (Twitter)...\n")

    tweets = fetch_tweets()

    if not tweets:
        print("Failed to fetch tweets. Please check curl.txt and credentials.")
        sys.exit(1)

    new_count, total_count = save_to_markdown(tweets)

    print(f"\n完成！新增 {new_count} 条，总计 {total_count} 条")

if __name__ == "__main__":
    main()
