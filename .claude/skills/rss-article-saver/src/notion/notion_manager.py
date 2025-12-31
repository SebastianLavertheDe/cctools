"""
Notion Manager - Blog articles sync to existing database
"""

import os
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

    def push_article_to_notion(self, article: 'Article') -> bool:
        """Push article to Notion database"""
        if not self.enabled:
            return False

        try:
            from ..utils.text_utils import parse_published_time, build_paragraph_blocks

            # Build page properties - mapped to Reading List database schema
            # Use translated title if available, otherwise use original title
            title_to_use = article.translated_title if article.translated_title else article.title
            properties = {
                "Title": {
                    "title": [{
                        "text": {"content": title_to_use[:100]}
                    }]
                },
                "Link": {
                    "url": article.link
                },
                "Author": {
                    "rich_text": [{"text": {"content": article.author}}]
                }
            }

            # Add AI summary if available (only first sentence)
            if article.ai_summary:
                # Extract first sentence
                first_sentence = article.ai_summary.split('。')[0].split('！')[0].split('？')[0].split('. ')[0].split('!')[0].split('?')[0].strip()
                if not first_sentence:
                    first_sentence = article.ai_summary[:200]
                properties["Summary"] = {
                    "rich_text": [{"text": {"content": first_sentence[:500]}}]
                }

            # Add AI category if available
            if article.ai_category:
                properties["Category"] = {
                    "select": {"name": article.ai_category}
                }

            # Add AI score if available
            if article.ai_score is not None:
                properties["Score"] = {
                    "number": article.ai_score
                }

            # Set Status to "Not Started" (common status in Reading List)
            properties["Status"] = {
                "status": {"name": "Not Started"}
            }

            # Create page with content
            children = self._build_page_content(article)

            # Add cover image (first image)
            page_data = {
                "parent": {"database_id": self.database_id},
                "properties": properties,
                "children": children
            }

            if article.image_urls:
                page_data["cover"] = {
                    "type": "external",
                    "external": {"url": article.image_urls[0]}
                }

            self.client.pages.create(**page_data)

            print(f"  Synced to Notion")
            return True

        except Exception as e:
            print(f"  Notion sync failed: {e}")
            # Try to provide helpful error message
            if "object not found" in str(e).lower():
                print("  Hint: Check NOTION_DATABASE_ID and database permissions")
            elif "property" in str(e).lower():
                print("  Hint: Property names may not match your database schema")
            return False

    def _build_page_content(self, article: 'Article') -> list:
        """Build Notion page content blocks from Markdown"""
        children = []

        # Use AI analysis if available, otherwise use full content
        content_to_use = article.ai_summary if article.ai_summary else article.full_content

        if content_to_use:
            md_blocks = self._markdown_to_blocks(content_to_use)
            children.extend(md_blocks)

        # Add images (all content images)
        if article.image_urls:
            for img_url in article.image_urls:
                children.append({
                    "type": "image",
                    "image": {
                        "type": "external",
                        "external": {"url": img_url}
                    }
                })

        return children

    def _markdown_to_blocks(self, md_text: str) -> list:
        """Convert Markdown text to Notion blocks"""
        import re

        blocks = []
        lines = md_text.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i].rstrip()

            # Empty line - skip
            if not line:
                i += 1
                continue

            # Heading 1-3
            if line.startswith('### '):
                blocks.append({
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"type": "text", "text": {"content": line[4:]}}]
                    }
                })
                i += 1
            elif line.startswith('## '):
                blocks.append({
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": line[3:]}}]
                    }
                })
                i += 1
            elif line.startswith('# '):
                blocks.append({
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"type": "text", "text": {"content": line[2:]}}]
                    }
                })
                i += 1

            # Horizontal rule
            elif line.strip() == '---':
                blocks.append({
                    "type": "divider",
                    "divider": {}
                })
                i += 1

            # Unordered list (- *)
            elif line.startswith(('- ', '* ')):
                text = line[2:]
                blocks.append({
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": self._parse_inline_formatting(text)
                    }
                })
                i += 1

            # Ordered list (1. 2. 3.)
            elif re.match(r'^\d+\.\s', line):
                text = re.sub(r'^\d+\.\s', '', line)
                blocks.append({
                    "type": "numbered_list_item",
                    "numbered_list_item": {
                        "rich_text": self._parse_inline_formatting(text)
                    }
                })
                i += 1

            # Regular paragraph - might span multiple lines
            else:
                paragraph_lines = [line]
                i += 1
                # Collect consecutive non-empty lines that aren't special
                while i < len(lines):
                    next_line = lines[i].rstrip()
                    if not next_line:
                        break
                    if (next_line.startswith(('#', '- ', '* ')) or
                        re.match(r'^\d+\.\s', next_line) or
                        next_line.strip() == '---'):
                        break
                    paragraph_lines.append(next_line)
                    i += 1

                paragraph_text = '\n'.join(paragraph_lines)
                blocks.append({
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": self._parse_inline_formatting(paragraph_text)
                    }
                })

        return blocks

    def _parse_inline_formatting(self, text: str) -> list:
        """Parse inline Markdown formatting (bold, italic) to Notion rich text array"""
        # First, parse all bold/regular segments from the entire text
        def parse_segments(t: str) -> list:
            """Recursively parse text into (type, content) tuples"""
            if not t:
                return []

            # Check for bold at the start
            if t.startswith('**'):
                end = t.find('**', 2)
                if end != -1:
                    bold_content = t[2:end]
                    # Recursively parse the rest
                    return [("bold", bold_content)] + parse_segments(t[end+2:])
                else:
                    # Unmatched **, treat as regular text
                    return [("text", t)]

            # Find next ** marker
            next_bold = t.find('**')
            if next_bold == -1:
                return [("text", t)]

            # Text before the next **
            if next_bold > 0:
                return [("text", t[:next_bold])] + parse_segments(t[next_bold:])
            else:
                return parse_segments(t[2:])

        # Parse all segments
        segments = parse_segments(text)

        # Now chunk each segment if needed
        parts = []
        for ptype, pcontent in segments:
            if len(pcontent) <= 1999:
                # No chunking needed
                if ptype == "bold":
                    parts.append({
                        "type": "text",
                        "text": {"content": pcontent},
                        "annotations": {"bold": True}
                    })
                else:
                    parts.append({
                        "type": "text",
                        "text": {"content": pcontent}
                    })
            else:
                # Chunk this segment - use 1900 to be safe
                for j in range(0, len(pcontent), 1900):
                    chunk = pcontent[j:j+1900]
                    if ptype == "bold":
                        parts.append({
                            "type": "text",
                            "text": {"content": chunk},
                            "annotations": {"bold": True}
                        })
                    else:
                        parts.append({
                            "type": "text",
                            "text": {"content": chunk}
                        })

        # Debug: check for oversized parts
        for i, part in enumerate(parts):
            content_len = len(part.get("text", {}).get("content", ""))
            if content_len > 1999:
                print(f"  WARNING: Part {i} has {content_len} chars (exceeds 1999)!")

        return parts if parts else [{"type": "text", "text": {"content": text[:1900]}}]
