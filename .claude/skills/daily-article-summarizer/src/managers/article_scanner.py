"""Article scanner for finding today's articles in mymind directory"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from ..core.models import ArticleMetadata


class ArticleScanner:
    """Scans mymind directory for articles"""

    def __init__(self, article_directory: str):
        self.article_directory = os.path.expanduser(article_directory)

    def get_todays_articles(self) -> List[ArticleMetadata]:
        """Get all articles for today"""
        today = datetime.now().strftime("%Y%m%d")
        return self.get_articles_by_date(today)

    def get_articles_by_date(self, date: str) -> List[ArticleMetadata]:
        """Get all articles for a specific date (YYYYMMDD format)"""
        date_dir = os.path.join(self.article_directory, date)

        if not os.path.exists(date_dir):
            print(f"  No articles found for date {date} (directory: {date_dir})")
            return []

        articles = []
        for filename in os.listdir(date_dir):
            if filename.endswith(".md"):
                file_path = os.path.join(date_dir, filename)
                metadata = self.parse_article_metadata(file_path, filename)
                if metadata:
                    articles.append(metadata)

        return articles

    def parse_article_metadata(
        self, file_path: str, filename: str
    ) -> Optional[ArticleMetadata]:
        """Parse metadata from article markdown file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract title (first line, usually # Title)
            title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else filename

            # Extract metadata section
            link = ""
            author = ""
            published_date = None
            saved_time = None

            # Parse metadata section
            in_metadata = False
            for line in content.split("\n"):
                line = line.strip()

                if line == "## 元数据":
                    in_metadata = True
                    continue

                if in_metadata:
                    if line.startswith("##"):
                        # End of metadata section
                        break

                    if "**链接**:" in line or "Link:" in line:
                        link = re.sub(r".*?\*?\*?链接\*?\*?:\s*", "", line).strip()
                    elif "**作者**:" in line or "Author:" in line:
                        author = (
                            re.sub(r".*?\*?\*?作者\*?\*?:\s*", "", line).strip()
                        )
                    elif "**发布时间**:" in line or "Published:" in line:
                        published_date = re.sub(
                            r".*?\*?\*?发布时间\*?\*?:\s*", "", line
                        ).strip()
                    elif "**保存时间**:" in line or "Saved:" in line:
                        saved_time = re.sub(
                            r".*?\*?\*?保存时间\*?\*?:\s*", "", line
                        ).strip()

            return ArticleMetadata(
                title=title,
                file_path=file_path,
                filename=filename,
                link=link,
                author=author,
                published_date=published_date,
                saved_time=saved_time,
                content=content,
            )

        except Exception as e:
            print(f"  Warning: Failed to parse {file_path}: {e}")
            return None
