"""Notion manager for pushing daily summaries"""

import os
from notion_client import Client
from typing import List, Optional
from datetime import datetime
from ..core.models import ArticleSummary


class NotionSummaryManager:
    """Manages pushing daily summaries to Notion"""

    def __init__(self, database_id: str = None):
        self.notion_key = os.getenv("notion_key")
        self.database_id = database_id or os.getenv("NOTION_DATABASE_ID")

        if self.notion_key and self.database_id:
            self.client = Client(auth=self.notion_key)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False
            print("  Warning: Notion integration disabled (missing credentials)")

    def push_daily_summary(
        self, date: str, summaries: List[ArticleSummary]
    ) -> Optional[str]:
        """
        Push daily summary to Notion

        Args:
            date: Date string (YYYYMMDD)
            summaries: List of article summaries

        Returns:
            Notion page ID or None if failed
        """
        if not self.enabled or not self.client:
            return None

        if not summaries:
            print("  No summaries to push to Notion")
            return None

        try:
            # Format date for title (YYYY-MM-DD)
            formatted_date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"

            # Create page
            page_data = {
                "parent": {"database_id": self.database_id},
                "properties": {
                    "Title": {
                        "title": [
                            {"text": {"content": f"Daily Summary - {formatted_date}"}}
                        ]
                    },
                    "Author": {"rich_text": [{"text": {"content": "Daily Summarizer"}}]},
                    "type": {"rich_text": [{"text": {"content": "blog"}}]},
                },
                "children": self._build_summary_content(date, summaries),
            }

            response = self.client.pages.create(**page_data)
            page_id = response.get("id")
            print(f"  Created Notion page: {page_id}")

            return page_id

        except Exception as e:
            print(f"  Warning: Failed to push to Notion: {e}")
            return None

    def _build_summary_content(
        self, date: str, summaries: List[ArticleSummary]
    ) -> List[dict]:
        """Build Notion blocks for daily summary"""
        blocks = []

        # Header
        formatted_date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
        blocks.append(
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {"type": "text", "text": {"content": f"📅 {formatted_date} 每日总结"}}
                    ]
                },
            }
        )

        blocks.append(
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": f"共总结 {len(summaries)} 篇文章\n"}}
                    ]
                },
            }
        )

        # Group by category
        by_category = {}
        for summary in summaries:
            if summary.category not in by_category:
                by_category[summary.category] = []
            by_category[summary.category].append(summary)

        # Add summaries by category
        for category, category_summaries in sorted(by_category.items()):
            blocks.append({"object": "block", "type": "divider", "divider": {}})
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"type": "text", "text": {"content": f"📚 {category}"}}]
                    },
                }
            )

            for summary in category_summaries:
                # Article title with score
                score_emoji = "⭐" if summary.score >= 80 else "📖" if summary.score >= 60 else "📄"
                blocks.append(
                    {
                        "object": "block",
                        "type": "heading_3",
                        "heading_3": {
                            "rich_text": [
                                {"type": "text", "text": {"content": f"{score_emoji} {summary.title}"}}
                            ]
                        },
                    }
                )

                # Summary
                blocks.append(
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {"type": "text", "text": {"content": summary.summary}}
                            ]
                        },
                    }
                )

                # Key points
                if summary.key_points:
                    for point in summary.key_points:
                        blocks.append(
                            {
                                "object": "block",
                                "type": "bulleted_list_item",
                                "bulleted_list_item": {
                                    "rich_text": [
                                        {"type": "text", "text": {"content": point}}
                                    ]
                                },
                            }
                        )

                # Source link
                if summary.source_url:
                    blocks.append(
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {
                                        "type": "text",
                                        "text": {"content": "🔗 "},
                                        "annotations": {"code": True},
                                    },
                                    {
                                        "type": "text",
                                        "text": {"content": summary.source_url},
                                        "href": summary.source_url,
                                    },
                                ]
                            },
                        }
                    )

        return blocks
