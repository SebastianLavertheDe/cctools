#!/usr/bin/env python3
"""
Notion Database Creator and Article Publisher
Creates a beautiful, readable Notion database and publishes articles
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import ssl
import re
from datetime import datetime
from pathlib import Path

# Load .env file
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    for line in open(env_path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ[key.strip()] = value.strip()


class NotionManager:
    """Manage Notion database creation and article publishing"""

    def __init__(self):
        self.notion_key = os.getenv("notion_key")
        self.base_url = "https://api.notion.com/v1"
        self.database_id = os.getenv("NOTION_DATABASE_ID")
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE

    def make_request(self, url, data=None, method=None):
        """Make HTTP request to Notion API"""
        if not self.notion_key:
            return None, "Notion key not configured"

        headers = {
            "Authorization": f"Bearer {self.notion_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode("utf-8") if data else None,
                headers=headers,
                method=method or ("POST" if data else "GET"),
            )

            with urllib.request.urlopen(req, timeout=30, context=self.ctx) as response:
                return json.loads(response.read().decode("utf-8")), None

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            return None, f"HTTP {e.code}: {error_body}"
        except Exception as e:
            return None, str(e)

    def create_database(self, parent_page_id=None):
        """Create a new Notion database for articles"""
        print("📊 Creating Notion database...")

        # Try to find a parent page
        if not parent_page_id:
            # Search for user's pages
            search_url = f"{self.base_url}/search"
            search_data = {
                "query": "",
                "filter": {"value": "page", "property": "object"},
                "page_size": 1,
            }

            result, error = self.make_request(search_url, search_data)

            if error:
                print(f"  ⚠️ Failed to search pages: {error}")
                # Try to use a known page ID format
                parent_page_id = None
            elif result and result.get("results") and len(result["results"]) > 0:
                parent_page_id = result["results"][0]["id"]
                print(f"  ✓ Using parent page: {parent_page_id[:8]}...")
            else:
                print("  ⚠️ No pages found, will try workspace parent")
                parent_page_id = None

        # Database schema
        database_schema = {
            "parent": {"page_id": parent_page_id}
            if parent_page_id
            else {"type": "workspace"},
            "title": [
                {"type": "text", "text": {"content": "📚 Tech Articles Collection"}}
            ],
            "properties": {
                "Title": {"title": {}},
                "Link": {"url": {}},
                "Author": {"rich_text": {}},
                "Source": {
                    "select": {
                        "options": [
                            {"name": "Reddit", "color": "red"},
                            {"name": "RSS", "color": "blue"},
                            {"name": "OpenAI Blog", "color": "green"},
                            {"name": "Anthropic Blog", "color": "purple"},
                            {"name": "Cursor Blog", "color": "orange"},
                            {"name": "Claude Code", "color": "gray"},
                        ]
                    }
                },
                "Category": {
                    "select": {
                        "options": [
                            {"name": "AI", "color": "blue"},
                            {"name": "Golang", "color": "green"},
                            {"name": "Developer Tools", "color": "orange"},
                            {"name": "Machine Learning", "color": "purple"},
                            {"name": "Architecture", "color": "red"},
                        ]
                    }
                },
                "Score": {"number": {"format": "number"}},
                "Difficulty": {
                    "select": {
                        "options": [
                            {"name": "Beginner", "color": "green"},
                            {"name": "Intermediate", "color": "yellow"},
                            {"name": "Advanced", "color": "red"},
                        ]
                    }
                },
                "Reading Time": {"number": {"name": "minutes"}},
                "Status": {"status": {}},
                "Date Added": {"date": {}},
                "Tags": {
                    "multi_select": {
                        "options": [
                            {"name": "AI", "color": "blue"},
                            {"name": "LLM", "color": "purple"},
                            {"name": "Tutorial", "color": "green"},
                            {"name": "News", "color": "yellow"},
                            {"name": "Opinion", "color": "red"},
                            {"name": "Code", "color": "orange"},
                        ]
                    }
                },
            },
        }

        result, error = self.make_request(f"{self.base_url}/databases", database_schema)

        if error:
            print(f"  ❌ Failed to create database: {error}")
            return None

        if result and result.get("id"):
            self.database_id = result["id"]
            print(f"  ✓ Database created: {self.database_id}")
            print(f"  🔗 URL: https://notion.so/{self.database_id.replace('-', '')}")
            return self.database_id

        print("  ❌ Failed to create database")
        return None

        if result and result.get("id"):
            self.database_id = result["id"]
            print(f"  ✓ Database created: {self.database_id}")
            print(f"  🔗 URL: https://notion.so/{self.database_id.replace('-', '')}")
            return self.database_id

        print("  ❌ Failed to create database")
        return None

    def publish_article(self, article):
        """Publish a single article to Notion"""
        if not self.database_id:
            return False, "Database not created"

        title = (
            article.get("translated_title") or article.get("title", "Untitled")[:100]
        )

        # Build page data compatible with user's database schema
        page_data = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "Title": {"title": [{"text": {"content": title}}]},
                "Link": {"url": article.get("link", "")},
                "Author": {
                    "rich_text": [
                        {"text": {"content": article.get("author", "Unknown")[:50]}}
                    ]
                },
                "Score": {"number": article.get("ai_score", 0)},
                "Category": {"select": {"name": article.get("category", "AI")}},
                "Summary": {
                    "rich_text": [
                        {"text": {"content": article.get("ai_summary", "")[:1900]}}
                    ]
                },
            },
            "children": self._build_simple_page(article),
        }

        result, error = self.make_request(f"{self.base_url}/pages", page_data)

        if error:
            return False, error

        return True, result.get("id")

    def _build_simple_page(self, article):
        """Build simple page content"""
        blocks = []

        # Key points
        if article.get("key_points"):
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"text": {"content": "🔑 关键要点"}}]},
                }
            )

            for point in article["key_points"][:5]:
                blocks.append(
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [{"text": {"content": point}}]
                        },
                    }
                )

        # Tags
        if article.get("tags"):
            blocks.append({"object": "block", "type": "divider", "divider": {}})
            tags_text = " ".join([f"#{tag}" for tag in article["tags"][:10]])
            blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": tags_text}}]},
                }
            )

        # Original link
        blocks.append({"object": "block", "type": "divider", "divider": {}})
        blocks.append(
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"text": {"content": f"🔗 原文: {article.get('link', 'N/A')}"}}
                    ]
                },
            }
        )

        return blocks

    def _build_beautiful_page(self, article):
        """Build a beautiful, readable Notion page"""
        blocks = []

        # Header
        blocks.append(
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"text": {"content": "📖 文章详情"}}]},
            }
        )

        # Divider
        blocks.append({"object": "block", "type": "divider", "divider": {}})

        # Basic Info
        blocks.append(
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "📊 基本信息"}}]},
            }
        )

        blocks.append(
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "text": {
                                "content": f"⏱️ 阅读时间: {article.get('reading_time', 5)} 分钟 | "
                            }
                        },
                        {
                            "text": {
                                "content": f"🎯 难度: {article.get('difficulty', 'Intermediate')} | "
                            }
                        },
                        {
                            "text": {
                                "content": f"📅 {datetime.now().strftime('%Y-%m-%d')}"
                            }
                        },
                    ]
                },
            }
        )

        # Quality Score
        blocks.append(
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "text": {
                                "content": f"⭐ AI评分: {article.get('ai_score', 0)}/100 | "
                            }
                        },
                        {
                            "text": {
                                "content": f"🏷️ 分类: {article.get('category', 'AI')} | "
                            }
                        },
                        {
                            "text": {
                                "content": f"🔗 来源: {article.get('source', 'RSS')}"
                            }
                        },
                    ]
                },
            }
        )

        # Divider
        blocks.append({"object": "block", "type": "divider", "divider": {}})

        # AI Summary
        if article.get("ai_summary"):
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "🤖 AI 智能摘要"}}]
                    },
                }
            )

            summary = article["ai_summary"]
            paragraphs = summary.split("。")
            for para in paragraphs:
                if para.strip():
                    blocks.append(
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {"text": {"content": para.strip() + "。"}}
                                ]
                            },
                        }
                    )

        # Key Points
        if article.get("key_points"):
            blocks.append({"object": "block", "type": "divider", "divider": {}})
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"text": {"content": "🔑 关键要点"}}]},
                }
            )

            for point in article["key_points"][:5]:
                blocks.append(
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [{"text": {"content": point}}]
                        },
                    }
                )

        # Tags
        if article.get("tags"):
            blocks.append({"object": "block", "type": "divider", "divider": {}})
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"text": {"content": "🏷️ 标签"}}]},
                }
            )

            tags_text = " ".join([f"#{tag}" for tag in article["tags"][:10]])
            blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": tags_text}}]},
                }
            )

        # Original Link
        blocks.append({"object": "block", "type": "divider", "divider": {}})
        blocks.append(
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "icon": {"emoji": "🔗"},
                    "color": "gray_background",
                    "rich_text": [
                        {"text": {"content": f"原文链接: {article.get('link', 'N/A')}"}}
                    ],
                },
            }
        )

        return blocks


def main():
    """Main entry point"""
    print("\n" + "=" * 60)
    print("🚀 Creating Notion Database and Publishing Articles")
    print("=" * 60 + "\n")

    manager = NotionManager()

    # Check if we have API key
    if not manager.notion_key:
        print("❌ Notion integration token not configured")
        print("💡 Set notion_key in .env file")
        sys.exit(1)

    # Create database if not exists
    if (
        not manager.database_id
        or manager.database_id == "请在这里填入你的Notion数据库ID"
    ):
        print("📝 No database found, creating new one...")
        database_id = manager.create_database()
        if not database_id:
            print("❌ Failed to create database")
            sys.exit(1)

        # Save database ID
        print("\n💾 Saving database ID to .env file...")
        env_path = Path(__file__).parent / ".env"
        if env_path.exists():
            content = open(env_path).read()
            content = re.sub(
                r"NOTION_DATABASE_ID=.*", f"NOTION_DATABASE_ID={database_id}", content
            )
            open(env_path, "w").write(content)
            print(f"  ✓ Saved: {database_id}")

    # Check if we have articles to publish
    articles_file = Path(__file__).parent / "collected_articles.json"

    if not articles_file.exists():
        print("\n📄 No collected articles found.")
        print(
            "💡 Run 'python run_standalone.py --collect-only' first to collect articles"
        )
        sys.exit(1)

    # Load articles
    with open(articles_file) as f:
        articles = json.load(f)

    if not articles:
        print("❌ No articles to publish")
        sys.exit(1)

    print(f"\n📤 Publishing {len(articles)} articles to Notion...")

    published = 0
    for i, article in enumerate(articles):
        title = article.get("translated_title") or article.get("title", "Untitled")[:50]
        print(f"  📝 [{i + 1}/{len(articles)}] {title}...")

        success, result = manager.publish_article(article)
        if success:
            published += 1
            print(f"    ✓ Published!")
        else:
            print(f"    ❌ Failed: {result}")

        time.sleep(0.5)

    print("\n" + "=" * 60)
    print(f"📊 Published: {published}/{len(articles)} articles")
    print(f"🗄️ Database ID: {manager.database_id}")
    print(f"🔗 URL: https://notion.so/{manager.database_id.replace('-', '')}")
    print("=" * 60)

    if published > 0:
        print("\n🎉 Check your Notion database for new articles!")
    else:
        print("\n⚠️ No articles published. Check API permissions.")


if __name__ == "__main__":
    main()
