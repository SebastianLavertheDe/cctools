"""
Notion Publisher
Publishes content to Notion databases
"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime

try:
    from notion_client import Client

    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False
    print(
        "Warning: notion-client library not installed. Notion publishing will be disabled."
    )


class NotionPublisher:
    """Notion content publisher"""

    def __init__(self, database_id: str = None):
        self.database_id = database_id or os.getenv("NOTION_DATABASE_ID")
        self.api_key = os.getenv("notion_key")

        self.client = None
        self.enabled = False

        if not NOTION_AVAILABLE:
            print("Warning: notion-client library not installed")
            return

        if not all([self.database_id, self.api_key]):
            print("Warning: Notion credentials not configured")
            return

        try:
            self.client = Client(auth=self.api_key)

            # Verify database access
            self.client.databases.retrieve(database_id=self.database_id)
            self.enabled = True
            print("✓ Notion client initialized successfully")

        except Exception as e:
            print(f"✗ Notion client initialization failed: {e}")

    def publish_article(self, article_data: Dict, template: str = "default") -> bool:
        """Publish an article to Notion"""
        if not self.enabled:
            print("Warning: Notion not enabled, skipping publish")
            return False

        try:
            page_data = self._build_page_data(article_data, template)
            self.client.pages.create(**page_data)
            return True

        except Exception as e:
            print(f"Notion publish failed: {e}")
            return False

    def publish_batch(self, articles: List[Dict], template: str = "default") -> int:
        """Publish multiple articles to Notion"""
        success_count = 0

        for article in articles:
            if self.publish_article(article, template):
                success_count += 1

        return success_count

    def _build_page_data(self, article: Dict, template: str) -> Dict:
        """Build Notion page data from article"""
        title = article.get("translated_title") or article.get("title", "Untitled")

        properties = {
            "Title": {"title": [{"text": {"content": title[:100]}}]},
            "Link": {"url": article.get("link", "")},
            "Author": {
                "rich_text": [{"text": {"content": article.get("author", "Unknown")}}]
            },
            "Date Added": {"date": {"start": datetime.now().isoformat()}},
            "Status": {"status": {"name": "To Read"}},
        }

        # Add optional fields
        optional_mappings = {
            "Category": "category",
            "Score": "ai_score",
            "Reading Time": "reading_time",
            "Difficulty": "difficulty",
            "Source": "source",
            "Word Count": "word_count",
            "Tags": "tags",
        }

        for notion_field, article_field in optional_mappings.items():
            if article_field in article and article[article_field]:
                value = article[article_field]

                if notion_field == "Tags" and isinstance(value, list):
                    # Handle tags as multi-select
                    properties[notion_field] = {
                        "multi_select": [{"name": tag} for tag in value[:10]]
                    }
                elif isinstance(value, (int, float)):
                    properties[notion_field] = {"number": value}
                elif isinstance(value, str):
                    properties[notion_field] = {"select": {"name": value}}

        # Build content blocks
        children = self._build_content(article, template)

        page_data = {
            "parent": {"database_id": self.database_id},
            "properties": properties,
            "children": children,
        }

        # Add cover image if available
        if article.get("images") and len(article["images"]) > 0:
            page_data["cover"] = {
                "type": "external",
                "external": {"url": article["images"][0]},
            }

        return page_data

    def _build_content(self, article: Dict, template: str) -> List[Dict]:
        """Build Notion content blocks"""
        children = []

        if template == "default":
            children = self._build_default_content(article)
        elif template == "minimal":
            children = self._build_minimal_content(article)
        elif template == "detailed":
            children = self._build_detailed_content(article)
        else:
            children = self._build_default_content(article)

        return children

    def _build_default_content(self, article: Dict) -> List[Dict]:
        """Build default content layout"""
        children = []

        # AI Summary section
        if article.get("ai_summary"):
            children.append(
                {
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"text": {"content": "🤖 AI 摘要"}}]},
                }
            )

            summary_blocks = self._markdown_to_blocks(article["ai_summary"])
            children.extend(summary_blocks)

        # Key Points section
        if article.get("key_points") and isinstance(article["key_points"], list):
            children.append(
                {
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"text": {"content": "🔑 关键要点"}}]},
                }
            )

            for point in article["key_points"][:10]:
                children.append(
                    {
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [{"text": {"content": point}}]
                        },
                    }
                )

        # Tags section
        if article.get("tags") and isinstance(article["tags"], list):
            children.append(
                {
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"text": {"content": "🏷️ 标签"}}]},
                }
            )

            for tag in article["tags"][:10]:
                children.append(
                    {
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "text": {"content": f"#{tag} "},
                                    "annotations": {"color": "blue"},
                                }
                            ]
                        },
                    }
                )

        # Metadata section
        children.append({"type": "divider", "divider": {}})

        children.append(
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "text": {
                                "content": f"📊 评分: {article.get('ai_score', 'N/A')}/100 | "
                            }
                        },
                        {
                            "text": {
                                "content": f"⏱️ 阅读时间: {article.get('reading_time', 'N/A')}分钟 | "
                            }
                        },
                        {
                            "text": {
                                "content": f"🎯 难度: {article.get('difficulty', 'N/A')}"
                            }
                        },
                    ]
                },
            }
        )

        return children

    def _build_minimal_content(self, article: Dict) -> List[Dict]:
        """Build minimal content layout"""
        children = []

        if article.get("ai_summary"):
            # Show only first paragraph
            first_para = article["ai_summary"].split("\n\n")[0]
            children.append(
                {
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": first_para}}]},
                }
            )

        return children

    def _build_detailed_content(self, article: Dict) -> List[Dict]:
        """Build detailed content layout"""
        children = []

        # Info card
        children.append(
            {
                "type": "column_list",
                "column_list": {
                    "columns": [
                        {
                            "type": "column",
                            "column": {
                                "children": [
                                    {
                                        "type": "heading_3",
                                        "heading_3": {
                                            "rich_text": [
                                                {"text": {"content": "📊 基本信息"}}
                                            ]
                                        },
                                    },
                                    {
                                        "type": "paragraph",
                                        "paragraph": {
                                            "rich_text": [
                                                {
                                                    "text": {
                                                        "content": f"📝 字数: {article.get('word_count', 'N/A')}"
                                                    }
                                                }
                                            ]
                                        },
                                    },
                                    {
                                        "type": "paragraph",
                                        "paragraph": {
                                            "rich_text": [
                                                {
                                                    "text": {
                                                        "content": f"⏱️ 阅读时间: {article.get('reading_time', 'N/A')}分钟"
                                                    }
                                                }
                                            ]
                                        },
                                    },
                                    {
                                        "type": "paragraph",
                                        "paragraph": {
                                            "rich_text": [
                                                {
                                                    "text": {
                                                        "content": f"🎯 难度: {article.get('difficulty', 'N/A')}"
                                                    }
                                                }
                                            ]
                                        },
                                    },
                                    {
                                        "type": "paragraph",
                                        "paragraph": {
                                            "rich_text": [
                                                {
                                                    "text": {
                                                        "content": f"📅 发布日期: {article.get('publish_date', 'N/A')}"
                                                    }
                                                }
                                            ]
                                        },
                                    },
                                ]
                            },
                        },
                        {
                            "type": "column",
                            "column": {
                                "children": [
                                    {
                                        "type": "heading_3",
                                        "heading_3": {
                                            "rich_text": [
                                                {"text": {"content": "🎯 质量评分"}}
                                            ]
                                        },
                                    },
                                    {
                                        "type": "paragraph",
                                        "paragraph": {
                                            "rich_text": [
                                                {
                                                    "text": {
                                                        "content": f"⭐ 总分: {article.get('ai_score', 'N/A')}/100"
                                                    }
                                                }
                                            ]
                                        },
                                    },
                                    {
                                        "type": "paragraph",
                                        "paragraph": {
                                            "rich_text": [
                                                {
                                                    "text": {
                                                        "content": f"📈 信息密度: {article.get('information_density', 'N/A')}/20"
                                                    }
                                                }
                                            ]
                                        },
                                    },
                                    {
                                        "type": "paragraph",
                                        "paragraph": {
                                            "rich_text": [
                                                {
                                                    "text": {
                                                        "content": f"🔧 实用性: {article.get('practicality', 'N/A')}/20"
                                                    }
                                                }
                                            ]
                                        },
                                    },
                                    {
                                        "type": "paragraph",
                                        "paragraph": {
                                            "rich_text": [
                                                {
                                                    "text": {
                                                        "content": f"💡 新颖性: {article.get('novelty_insight', 'N/A')}/15"
                                                    }
                                                }
                                            ]
                                        },
                                    },
                                ]
                            },
                        },
                    ]
                },
            }
        )

        # Divider
        children.append({"type": "divider", "divider": {}})

        # Add default content
        children.extend(self._build_default_content(article))

        return children

    def _markdown_to_blocks(self, markdown: str) -> List[Dict]:
        """Convert markdown to Notion blocks"""
        blocks = []
        lines = markdown.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("# "):
                blocks.append(
                    {
                        "type": "heading_1",
                        "heading_1": {"rich_text": [{"text": {"content": line[2:]}}]},
                    }
                )
            elif line.startswith("## "):
                blocks.append(
                    {
                        "type": "heading_2",
                        "heading_2": {"rich_text": [{"text": {"content": line[3:]}}]},
                    }
                )
            elif line.startswith("### "):
                blocks.append(
                    {
                        "type": "heading_3",
                        "heading_3": {"rich_text": [{"text": {"content": line[4:]}}]},
                    }
                )
            elif line.startswith(("- ", "* ")):
                blocks.append(
                    {
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [{"text": {"content": line[2:]}}]
                        },
                    }
                )
            elif (
                line.startswith("1. ")
                or line.startswith("2. ")
                or line.startswith("3. ")
            ):
                # Ordered list - remove number
                import re

                cleaned = re.sub(r"^\d+\.\s", "", line)
                blocks.append(
                    {
                        "type": "numbered_list_item",
                        "numbered_list_item": {
                            "rich_text": [{"text": {"content": cleaned}}]
                        },
                    }
                )
            else:
                blocks.append(
                    {
                        "type": "paragraph",
                        "paragraph": {"rich_text": [{"text": {"content": line}}]},
                    }
                )

        return blocks


def main():
    """Main entry point for CLI usage"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m notion_publisher <article_json> [template]")
        return

    article_json = sys.argv[1]
    template = sys.argv[2] if len(sys.argv) > 2 else "default"

    try:
        article_data = json.loads(article_json)
        publisher = NotionPublisher()

        success = publisher.publish_article(article_data, template)

        if success:
            print("✓ Publish successful")
        else:
            print("✗ Publish failed")

    except json.JSONDecodeError:
        print("✗ Invalid JSON format")
    except Exception as e:
        print(f"✗ Error: {e}")


if __name__ == "__main__":
    main()
