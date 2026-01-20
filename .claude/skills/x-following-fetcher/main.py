"""
X Following Fetcher - Fetches latest posts from X (Twitter) users you follow
and saves them to JSON format and Notion database.
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent / ".env")

OUTPUT_DIR = Path("/home/say/cctools/x")

NOTION_KEY = os.getenv("notion_key") or ""
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID") or ""
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID") or ""

notion_client = None
image_uploader = None


def init_notion():
    global notion_client, image_uploader
    try:
        from notion_client import Client
        notion_client = Client(auth=NOTION_KEY)
        image_uploader = NotionImageUploader()
        print("✅ Notion 客户端初始化成功")
        return True
    except Exception as e:
        print(f"❌ Notion 客户端初始化失败: {e}")
        notion_client = None
        image_uploader = None
        return False


class NotionImageUploader:
    """Notion 图片上传器"""
    
    def __init__(self):
        pass
    
    def extract_image_urls(self, text: str) -> list:
        if not text:
            return []
        img_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+\.(?:jpg|jpeg|png|gif|webp)[^\s<>"{}|\\^`\[\]]*'
        matches = re.findall(img_pattern, text, re.IGNORECASE)
        unique_urls = []
        for url in matches:
            if url not in unique_urls:
                unique_urls.append(url)
        return unique_urls
    
    def upload_image(self, image_url: str) -> Optional[str]:
        try:
            resp = requests.post(
                "https://api.notion.com/v1/file_uploads",
                headers={
                    "Authorization": f"Bearer {NOTION_KEY}",
                    "Notion-Version": "2022-06-28",
                    "Content-Type": "application/json"
                },
                json={}
            )
            resp.raise_for_status()
            upload_id = resp.json()["id"]
            
            import mimetypes
            headers = {"User-Agent": "Mozilla/5.0"}
            img_resp = requests.get(image_url, headers=headers, timeout=30)
            img_resp.raise_for_status()
            
            mime = mimetypes.guess_type(image_url)[0] or "image/png"
            filename = f"image_{upload_id}.{mime.split('/')[-1]}"
            
            requests.post(
                f"https://api.notion.com/v1/file_uploads/{upload_id}/send",
                headers={
                    "Authorization": f"Bearer {NOTION_KEY}",
                    "Notion-Version": "2022-06-28"
                },
                files={"file": (filename, img_resp.content, mime)}
            ).raise_for_status()
            
            return upload_id
        except Exception as e:
            print(f"    ⚠️ 图片上传失败: {e}")
            return None


X_CURL_FILE = Path(__file__).parent / "x_curl.txt"


def parse_tweet_entry(entry: dict[str, Any]) -> dict[str, Any] | None:
    try:
        content = entry.get("content", {})
        tweet = content.get("itemContent", {})

        if tweet.get("__typename") != "TweetTombstone":
            tweet_results = tweet.get("tweet_results", {})
            if tweet_results:
                result = tweet_results.get("result", {})
                legacy = result.get("legacy", {})
                
                # Extract user info from the correct location
                # X API stores user data in result.core.user_results.result.core
                user = {}
                user_core = {}
                
                core = result.get("core", {})
                user_results = core.get("user_results", {}).get("result", {})
                
                # Try the new path: result.core.user_results.result.core
                if user_results:
                    user_core = user_results.get("core", {})
                    if user_core:
                        user = user_core
                
                # Fallback: try result.core.user_results.result.legacy
                if not user.get("screen_name"):
                    user_legacy = user_results.get("legacy", {})
                    if user_legacy:
                        user = user_legacy
                
                user_name = user.get("name", "")
                user_screen_name = user.get("screen_name", "")
                user_verified = user_results.get("is_blue_verified", False) if user_results else False
                
                # Profile image from avatar
                avatar = user_results.get("avatar", {}) if user_results else {}
                profile_image_url = avatar.get("image_url", "") if avatar else ""
                
                # If still empty, try to extract from content (@mention)
                if not user_screen_name:
                    content_text = legacy.get("full_text", "")
                    import re
                    match = re.search(r'@(\w+)', content_text)
                    if match:
                        user_screen_name = match.group(1)
                        user_name = user_screen_name  # Use screen_name as fallback
                
                extended_entities = legacy.get("extended_entities", {})
                media = extended_entities.get("media", [])
                image_urls = []
                for m in media:
                    if m.get("type") == "photo":
                        image_urls.append(m.get("media_url_https", m.get("media_url", "")))

                return {
                    "id": legacy.get("id_str", ""),
                    "user_name": user_name,
                    "user_screen_name": user_screen_name,
                    "user_verified": user_verified,
                    "profile_image_url": profile_image_url,
                    "content": legacy.get("full_text", ""),
                    "created_at": legacy.get("created_at", ""),
                    "retweet_count": legacy.get("retweet_count", 0),
                    "like_count": legacy.get("favorite_count", 0),
                    "reply_count": legacy.get("reply_count", 0),
                    "quote_count": legacy.get("quote_count", 0),
                    "bookmark_count": legacy.get("bookmark_count", 0),
                    "lang": legacy.get("lang", ""),
                    "source": legacy.get("source", "").replace("<a href=", "").replace("</a>", "").split(">")[-1] if legacy.get("source") else "",
                    "image_urls": image_urls
                }

        return None
    except Exception as e:
        print(f"  ⚠️ Parse error: {e}")
        return None


def execute_curl_from_file() -> subprocess.CompletedProcess:
    """从 x_curl.txt 读取 curl 命令并执行"""
    if not X_CURL_FILE.exists():
        raise FileNotFoundError(f"curl 文件不存在: {X_CURL_FILE}")

    with open(X_CURL_FILE, "r", encoding="utf-8") as f:
        curl_content = f.read().strip()

    # 将多行 curl 命令转换为单行命令
    # 移除行尾的换行符和反斜杠，保留参数
    curl_cmd = curl_content.replace("\\\n", " ").replace("\\\r\n", " ")

    # 解析 curl 命令
    import shlex
    cmd_list = shlex.split(curl_cmd)

    return subprocess.run(
        cmd_list,
        capture_output=True,
        text=True,
        timeout=30
    )


def fetch_tweets() -> list[dict[str, Any]]:
    try:
        result = execute_curl_from_file()

        if result.returncode != 0:
            print(f"Error fetching tweets: {result.stderr}", file=sys.stderr)
            return []

        response = json.loads(result.stdout)

        instructions = response.get("data", {}).get("home", {}).get("home_timeline_urt", {}).get("instructions", [])

        tweets = []
        seen_ids = set()

        for instruction in instructions:
            if instruction.get("type") == "TimelineAddEntries":
                entries = instruction.get("entries", [])
                for entry in entries:
                    content = entry.get("content", {})
                    typename = content.get("__typename")
                    if typename == "TimelineTimelineItem":
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


def get_existing_ids() -> set:
    existing_ids = set()
    if OUTPUT_DIR.exists():
        for f in OUTPUT_DIR.glob("*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    posts = data.get("posts", [])
                    for post in posts:
                        if "id" in post:
                            existing_ids.add(post["id"])
            except Exception:
                continue
    return existing_ids


def save_to_json(tweets: list[dict[str, Any]]) -> tuple[int, int]:
    existing_ids = get_existing_ids()
    new_tweets = [t for t in tweets if t["id"] not in existing_ids]

    if not new_tweets:
        print("没有新增帖子")
        return 0, 0

    print(f"发现 {len(new_tweets)} 条新帖子")

    for i, tweet in enumerate(new_tweets):
        print(f"  处理 {i+1}/{len(new_tweets)}: @{tweet['user_screen_name']}")
        tweet["fetched_at"] = datetime.now().isoformat()

    date_str = datetime.now().strftime("%Y%m%d")
    output_file = OUTPUT_DIR / f"{date_str}.json"

    if output_file.exists():
        with open(output_file, "r", encoding="utf-8") as fp:
            existing_data = json.load(fp)
    else:
        existing_data = {"date": date_str, "updated_at": datetime.now().isoformat(), "posts": []}

    existing_ids_in_file = {p["id"] for p in existing_data["posts"]}
    for tweet in new_tweets:
        if tweet["id"] not in existing_ids_in_file:
            existing_data["posts"].append(tweet)

    existing_data["updated_at"] = datetime.now().isoformat()

    with open(output_file, "w", encoding="utf-8") as fp:
        json.dump(existing_data, fp, ensure_ascii=False, indent=2)

    print(f"\n已保存到: {output_file}")
    print(f"新增: {len(new_tweets)} 条")
    print(f"总计: {len(existing_data['posts'])} 条")

    return len(new_tweets), len(existing_data["posts"])


def push_to_notion(tweet: dict) -> bool:
    if not notion_client:
        return False
    
    try:
        tweet_url = "https://x.com/" + tweet['user_screen_name'] + "/status/" + tweet['id']
        user_name = tweet.get('user_name', tweet['user_screen_name'])
        content = tweet['content'][:1900]
        
        properties = {
            'Title': {'title': [{'text': {'content': '@' + tweet['user_screen_name'] + ' - ' + user_name}}]},
            'type': {'rich_text': [{'type': 'text', 'text': {'content': 'x'}}]},
        }
        
        children = [
            {'object': 'block', 'type': 'paragraph', 'paragraph': {'rich_text': [{'type': 'text', 'text': {'content': 'Link: ' + tweet_url}}]}},
            {'object': 'block', 'type': 'paragraph', 'paragraph': {'rich_text': [{'type': 'text', 'text': {'content': 'Time: ' + tweet['created_at']}}]}},
            {'object': 'block', 'type': 'divider', 'divider': {}},
        ]
        
        if content:
            children.append({'object': 'block', 'type': 'paragraph', 'paragraph': {'rich_text': [{'type': 'text', 'text': {'content': content}}]}})
        
        # Add images from tweet
        image_urls = tweet.get('image_urls', [])
        
        for img_url in image_urls[:4]:
            children.append({
                'object': 'block',
                'type': 'image',
                'image': {
                    'type': 'external',
                    'external': {'url': img_url}
                }
            })
        
        children.append({'object': 'block', 'type': 'paragraph', 'paragraph': {'rich_text': [{'type': 'text', 'text': {'content': 'Likes: ' + str(tweet.get('like_count', 0)) + ' | RTs: ' + str(tweet.get('retweet_count', 0)) + ' | Replies: ' + str(tweet.get('reply_count', 0))}}]}})
        
        notion_client.pages.create(
            parent={'database_id': NOTION_DATABASE_ID},
            properties=properties,
            children=children
        )
        
        print(f"  ✅ 已推送到 Notion: @{tweet['user_screen_name']}")
        return True
        
    except Exception as e:
        print(f"  ❌ Notion 推送失败: {e}")
        return False


def main():
    print("Fetching latest posts from X (Twitter)...\n")

    tweets = fetch_tweets()

    if not tweets:
        print("Failed to fetch tweets. Please check your cookies and credentials.")
        sys.exit(1)

    new_count, total_count = save_to_json(tweets)
    
    print(f"\n完成！新增 {new_count} 条，总计 {total_count} 条")
    
    if new_count > 0 and init_notion():
        print("\n推送到 Notion...")
        # Check what's already in Notion by querying pages
        notion_ids = set()
        try:
            resp = requests.post(
                'https://api.notion.com/v1/databases/' + NOTION_DATABASE_ID + '/query',
                headers={
                    'Authorization': f'Bearer {NOTION_KEY}',
                    'Notion-Version': '2022-06-28',
                    'Content-Type': 'application/json'
                },
                json={'page_size': 100}
            )
            if resp.status_code == 200:
                for page in resp.json()['results']:
                    # Get tweet ID from page content
                    page_id = page['id']
                    blocks_resp = requests.get(
                        f'https://api.notion.com/v1/blocks/{page_id}/children',
                        headers={
                            'Authorization': f'Bearer {NOTION_KEY}',
                            'Notion-Version': '2022-06-28'
                        }
                    )
                    if blocks_resp.status_code == 200:
                        for block in blocks_resp.json().get('results', []):
                            if block.get('type') == 'paragraph':
                                for text in block.get('paragraph', {}).get('rich_text', []):
                                    link = text.get('text', {}).get('content', '')
                                    if 'x.com/' in link and '/status/' in link:
                                        parts = link.split('/status/')
                                        if len(parts) > 1:
                                            tweet_id = parts[1].split('?')[0].split()[0]
                                            if tweet_id:
                                                notion_ids.add(tweet_id)
        except Exception as e:
            print(f"  ⚠️ 无法检查Notion已有帖子: {e}")
        
        print(f"  Notion已有帖子: {len(notion_ids)} 条")
        
        new_tweets = [t for t in tweets if t["id"] not in notion_ids]
        print(f"  待推送新帖子: {len(new_tweets)}")
        
        for i, tweet in enumerate(new_tweets):
            print(f"  推送 {i+1}/{len(new_tweets)}: @{tweet['user_screen_name']}")
            push_to_notion(tweet)


if __name__ == "__main__":
    main()
