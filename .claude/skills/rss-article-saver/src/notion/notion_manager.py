"""
Notion Manager - Blog articles sync to existing database
"""

import os
import requests
import mimetypes
import tempfile
from notion_client import Client
from typing import Optional


class BlogNotionManager:
    """Notion manager for blog articles"""

    def __init__(self):
        self.database_id = os.getenv("NOTION_DATABASE_ID")
        notion_key = os.getenv("notion_key")

        if not notion_key or not self.database_id:
            print("Notion credentials not found, sync disabled")
            self.client = None
            self.enabled = False
            return

        try:
            self.client = Client(auth=notion_key)
            self.enabled = True
            self._verify_database()
        except Exception as e:
            print(f"Notion init failed: {e}")
            self.enabled = False

    def _verify_database(self) -> bool:
        """Verify database exists"""
        try:
            response = self.client.databases.retrieve(database_id=self.database_id)
            print(f"Connected to Notion database")
            return True
        except Exception as e:
            print(f"Database verification failed: {e}")
            self.enabled = False
            return False

    def push_article_to_notion(self, article: "Article") -> bool:
        """Push article to Notion database"""
        if not self.enabled:
            return False

        try:
            # Debug: Check article content
            if article.full_content:
                print(f"    Article content length: {len(article.full_content)} chars")
                print(f"    Article content preview: {article.full_content[:100]}...")
            else:
                print(f"    Warning: article.full_content is empty or None")

            # Build page properties
            properties = {
                "Title": {"title": [{"text": {"content": article.title[:100]}}]},
                "Link": {"url": article.link},
                "Author": {"rich_text": [{"text": {"content": article.author}}]},
                "type": {"rich_text": [{"text": {"content": "blog"}}]},
                "Status": {"status": {"name": "Not Started"}},
            }

            # Create page with content
            children = self._build_page_content(article)
            print(f"    Generated {len(children)} Notion blocks for content")

            # Build page data
            page_data = {
                "parent": {"database_id": self.database_id},
                "properties": properties,
                "children": children,
            }

            # Add cover image (first image) - use parsed real URL
            if article.image_urls:
                # Parse real URL from Next.js proxy URLs
                cover_url = self._parse_image_url(article.image_urls[0])
                page_data["cover"] = {
                    "type": "external",
                    "external": {"url": cover_url},
                }

            self.client.pages.create(**page_data)

            print(f"  Synced to Notion")
            return True

        except Exception as e:
            print(f"  Notion sync failed: {e}")
            if "object not found" in str(e).lower():
                print("  Hint: Check NOTION_DATABASE_ID and database permissions")
            elif "property" in str(e).lower():
                print("  Hint: Property names may not match your database schema")
            return False

    def _build_page_content(self, article: "Article") -> list:
        """Build Notion page content blocks - article text and images"""
        children = []

        # Add article full content
        if article.full_content:
            # Convert markdown to Notion blocks
            content_blocks = self._markdown_to_blocks(article.full_content)
            children.extend(content_blocks)

        # Add images from original article
        if article.image_urls:
            # Add a divider before images
            children.append({"type": "divider", "divider": {}})
            # Add section header
            children.append(
                {
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "文章图片"}}]
                    },
                }
            )
            # Add images using external URLs (limit to 10 for performance)
            for img_url in article.image_urls[:10]:
                # Parse real URL from proxy URLs
                real_url = self._parse_image_url(img_url)
                children.append(
                    {
                        "type": "image",
                        "image": {"type": "external", "external": {"url": real_url}},
                    }
                )

        # Notion API limit: max 100 children per page
        if len(children) > 100:
            children = children[:100]
            print(f"    Content truncated to 100 blocks (Notion API limit)")

        return children

    def _upload_image_to_notion(self, image_url: str) -> Optional[str]:
        """Upload image to Notion and return file URL"""
        try:
            # Parse real image URL from Next.js proxy URLs
            real_url = self._parse_image_url(image_url)

            # 1. Download image to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                response = requests.get(
                    real_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15
                )
                response.raise_for_status()
                tmp.write(response.content)
                tmp_path = tmp.name

            # 2. Create upload object
            notion_key = os.getenv("notion_key")
            resp = requests.post(
                "https://api.notion.com/v1/file_uploads",
                headers={
                    "Authorization": f"Bearer {notion_key}",
                    "Notion-Version": "2022-06-28",
                    "Content-Type": "application/json",
                },
                json={},
            )
            resp.raise_for_status()
            upload_obj = resp.json()
            upload_id = upload_obj["id"]

            # 3. Send file content
            mime = mimetypes.guess_type(tmp_path)[0] or "image/jpeg"
            with open(tmp_path, "rb") as f:
                resp = requests.post(
                    f"https://api.notion.com/v1/file_uploads/{upload_id}/send",
                    headers={
                        "Authorization": f"Bearer {notion_key}",
                        "Notion-Version": "2022-06-28",
                    },
                    files={"file": (os.path.basename(tmp_path), f, mime)},
                )
            resp.raise_for_status()
            result = resp.json()

            # 4. Clean up temp file
            os.remove(tmp_path)

            # Return the upload_id for Notion to use
            # Notion will use this to reference the uploaded file
            return upload_id

        except Exception as e:
            print(f"    Image upload failed: {e}")
            return None

    def _parse_image_url(self, url: str) -> str:
        """Parse real image URL from Next.js proxy URLs"""
        try:
            from urllib.parse import urlparse, parse_qs, unquote_plus

            # Check if it's a Next.js image proxy URL
            if "/_next/image" in url:
                parsed = urlparse(url)
                query = parse_qs(parsed.query)
                # Get the real URL from the 'url' parameter
                real_url = query.get("url", [url])[0]
                return unquote_plus(real_url)

            return url
        except:
            return url

    def _markdown_to_blocks(self, md_text: str) -> list:
        """Convert Markdown text to Notion blocks"""
        import re

        blocks = []
        lines = md_text.split("\n")

        i = 0
        while i < len(lines):
            line = lines[i].rstrip()

            # Empty line - skip
            if not line:
                i += 1
                continue

            # Heading 1-3
            if line.startswith("### "):
                blocks.append(
                    {
                        "type": "heading_3",
                        "heading_3": {
                            "rich_text": [
                                {"type": "text", "text": {"content": line[4:]}}
                            ]
                        },
                    }
                )
                i += 1
            elif line.startswith("## "):
                blocks.append(
                    {
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [
                                {"type": "text", "text": {"content": line[3:]}}
                            ]
                        },
                    }
                )
                i += 1
            elif line.startswith("# "):
                blocks.append(
                    {
                        "type": "heading_1",
                        "heading_1": {
                            "rich_text": [
                                {"type": "text", "text": {"content": line[2:]}}
                            ]
                        },
                    }
                )
                i += 1

            # Horizontal rule
            elif line.strip() == "---":
                blocks.append({"type": "divider", "divider": {}})
                i += 1

            # Unordered list (- *)
            elif line.startswith(("- ", "* ")):
                text = line[2:]
                blocks.append(
                    {
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": self._parse_inline_formatting(text)
                        },
                    }
                )
                i += 1

            # Ordered list (1. 2. 3.)
            elif re.match(r"^\d+\.\s", line):
                text = re.sub(r"^\d+\.\s", "", line)
                blocks.append(
                    {
                        "type": "numbered_list_item",
                        "numbered_list_item": {
                            "rich_text": self._parse_inline_formatting(text)
                        },
                    }
                )
                i += 1

            # Regular paragraph
            else:
                blocks.append(
                    {
                        "type": "paragraph",
                        "paragraph": {"rich_text": self._parse_inline_formatting(line)},
                    }
                )
                i += 1

        return blocks

    def _parse_inline_formatting(self, text: str) -> list:
        """Parse inline Markdown formatting (bold) to Notion rich text array"""
        parts = []
        remaining = text

        while remaining:
            # Find bold markers
            if remaining.startswith("**"):
                end = remaining.find("**", 2)
                if end != -1:
                    bold_content = remaining[2:end]
                    parts.append(
                        {
                            "type": "text",
                            "text": {"content": bold_content[:1999]},
                            "annotations": {"bold": True},
                        }
                    )
                    remaining = remaining[end + 2 :]
                    continue

            # No more bold, add rest as plain text
            if remaining:
                parts.append({"type": "text", "text": {"content": remaining[:1999]}})
                break

        return parts if parts else [{"type": "text", "text": {"content": text[:1999]}}]
