"""
Content Extractor
Extracts full content from web pages
"""

import os
import requests
import json
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse
from datetime import datetime

try:
    import trafilatura

    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False
    print(
        "Warning: trafilatura library not installed. Content extraction will be limited."
    )


class ContentExtractor:
    """Intelligent content extractor"""

    def __init__(self, use_firecrawl: bool = False):
        self.use_firecrawl = use_firecrawl and os.getenv("FIRECRAWL_API_KEY")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def extract_article(self, url: str) -> Dict:
        """Extract article content from URL"""
        result = {
            "url": url,
            "title": None,
            "content": None,
            "author": None,
            "publish_date": None,
            "images": [],
            "links": [],
            "word_count": 0,
            "reading_time": 0,
            "extraction_method": None,
            "success": False,
            "error": None,
        }

        try:
            # Method 1: Use trafilatura if available
            if TRAFILATURA_AVAILABLE:
                extracted = self._extract_with_trafilatura(url)
                if extracted["content"]:
                    result.update(extracted)
                    result["extraction_method"] = "trafilatura"
                    result["success"] = True

            # Method 2: Fallback to simple requests
            if not result["success"]:
                extracted = self._extract_with_requests(url)
                if extracted["content"]:
                    result.update(extracted)
                    result["extraction_method"] = "requests"
                    result["success"] = True

            # Calculate word count and reading time
            if result["content"]:
                result["word_count"] = len(result["content"].split())
                result["reading_time"] = max(1, result["word_count"] // 200)

        except Exception as e:
            result["error"] = str(e)
            print(f"Content extraction failed for {url}: {e}")

        return result

    def _extract_with_trafilatura(self, url: str) -> Dict:
        """Extract content using trafilatura"""
        try:
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return {"content": None}

            # Extract content
            extracted = trafilatura.extract(
                downloaded,
                with_metadata=True,
                include_comments=False,
                include_tables=True,
            )

            if not extracted or len(extracted) < 100:
                return {"content": None}

            # Extract metadata
            metadata = trafilatura.metadata.extract_metadata(downloaded)

            # Extract images
            images = self._extract_images(url, downloaded)

            # Extract links
            links = self._extract_links(downloaded)

            return {
                "content": extracted,
                "title": metadata.title if metadata else None,
                "author": metadata.author if metadata else None,
                "publish_date": str(metadata.date)
                if metadata and metadata.date
                else None,
                "images": images,
                "links": links,
            }

        except Exception as e:
            print(f"Trafilatura extraction failed: {e}")
            return {"content": None}

    def _extract_with_requests(self, url: str) -> Dict:
        """Extract content using simple requests"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Try trafilatura on the HTML
            if TRAFILATURA_AVAILABLE:
                extracted = trafilatura.extract(response.text, with_metadata=True)

                if extracted and len(extracted) > 100:
                    metadata = trafilatura.metadata.extract_metadata(response.text)

                    return {
                        "content": extracted,
                        "title": metadata.title if metadata else None,
                        "author": metadata.author if metadata else None,
                        "publish_date": str(metadata.date)
                        if metadata and metadata.date
                        else None,
                        "images": self._extract_images(url, response.text),
                        "links": self._extract_links(response.text),
                    }

            # Fallback: extract title from HTML
            import re

            title_match = re.search(
                r"<title[^>]*>([^<]+)</title>", response.text, re.IGNORECASE
            )
            title = title_match.group(1).strip() if title_match else None

            return {
                "content": response.text[:5000],  # Limit content
                "title": title,
                "author": None,
                "publish_date": None,
                "images": [],
                "links": [],
            }

        except Exception as e:
            print(f"Requests extraction failed: {e}")
            return {"content": None}

    def _extract_images(self, base_url: str, html: str) -> List[str]:
        """Extract image URLs from HTML"""
        if not html:
            return []

        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "html.parser")

            base = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
            images = []

            for img in soup.find_all("img"):
                src = img.get("src")
                if src:
                    # Skip small images and tracking pixels
                    skip_patterns = ["pixel", "analytics", "adsct", "icon", ".gif"]
                    if any(pattern in src.lower() for pattern in skip_patterns):
                        continue

                    # Normalize URL
                    if src.startswith("http"):
                        images.append(src)
                    elif src.startswith("//"):
                        images.append(f"https:{src}")
                    elif src.startswith("/"):
                        images.append(urljoin(base, src))

            # Deduplicate
            return list(set(images))

        except ImportError:
            # Fallback if BeautifulSoup not available
            import re

            img_pattern = r'<img[^>]+src=[\'"]([^\'">]+)[\'"]'
            return list(set(re.findall(img_pattern, html)))

        except Exception as e:
            print(f"Image extraction failed: {e}")
            return []

    def _extract_links(self, html: str) -> List[str]:
        """Extract links from HTML"""
        if not html:
            return []

        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "html.parser")

            links = []
            for a in soup.find_all("a"):
                href = a.get("href")
                if href and href.startswith("http"):
                    links.append(href)

            return list(set(links))

        except ImportError:
            # Fallback regex
            import re

            link_pattern = r'<a[^>]+href=[\'"]([^\'">]+)[\'"]'
            return list(set(re.findall(link_pattern, html)))

        except Exception as e:
            print(f"Link extraction failed: {e}")
            return []

    def extract_multiple(self, urls: List[str]) -> List[Dict]:
        """Extract content from multiple URLs"""
        results = []
        for url in urls:
            result = self.extract_article(url)
            results.append(result)
        return results


def main():
    """Main entry point for CLI usage"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m content_extractor <url>")
        return

    url = sys.argv[1]
    extractor = ContentExtractor()
    result = extractor.extract_article(url)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
