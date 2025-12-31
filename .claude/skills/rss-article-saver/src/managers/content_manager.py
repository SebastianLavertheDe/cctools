"""
Content Manager - Full content extraction using trafilatura
"""

import trafilatura
import requests
import re
import os
from typing import Optional, Dict, List
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


class FirecrawlExtractor:
    """Fallback extractor using Firecrawl for JavaScript-rendered pages"""

    def __init__(self):
        self.api_key = os.getenv('FIRECRAWL_API_KEY')
        self.enabled = bool(self.api_key)

    def scrape(self, url: str) -> Optional[str]:
        """Scrape URL using Firecrawl"""
        if not self.enabled:
            return None
        try:
            from firecrawl import FirecrawlApp

            app = FirecrawlApp(api_key=self.api_key)
            result = app.scrape_url(url, params={'formats': ['markdown']})

            if result and 'markdown' in result:
                return result['markdown']
            return None
        except ImportError:
            print("  Firecrawl not installed, skipping")
            return None
        except Exception as e:
            print(f"  Firecrawl extraction failed: {e}")
            return None


class ContentExtractor:
    """Extract full content from article URLs"""

    def __init__(self, config: dict):
        self.extractor = config.get('extractor', 'trafilatura')
        self.include_images = config.get('include_images', True)
        self.max_length = config.get('max_content_length', 50000)
        self.firecrawl = FirecrawlExtractor()

    def extract_content(self, url: str) -> Dict:
        """
        Extract full content from article URL

        Returns:
            dict with 'content', 'images', 'author'
        """
        result = {
            'content': None,
            'images': [],
            'author': None
        }

        try:
            # Download the page
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                # Fallback to requests
                response = requests.get(url, timeout=30, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                downloaded = response.text

            # Extract images list first
            image_list = []
            if self.include_images:
                image_list = self._extract_images(downloaded, url)

            # Use BeautifulSoup to extract content with embedded images
            content = self._extract_content_with_images(downloaded, image_list)

            # If content is too short, it might be JavaScript-rendered
            # Try Firecrawl as fallback
            if not content or len(content) < 200:
                print(f"    Content too short ({len(content) if content else 0} chars), trying Firecrawl...")
                markdown_content = self.firecrawl.scrape(url)
                if markdown_content:
                    content = markdown_content
                    print(f"    Firecrawl extraction got {len(content)} chars")
                    # Extract images from markdown
                    if self.include_images:
                        image_list = self._extract_images_from_markdown(markdown_content)
                    result['images'] = image_list

            if content:
                # Truncate if too long
                if len(content) > self.max_length:
                    content = content[:self.max_length] + "\n\n...(内容过长已截断)"
                result['content'] = content

            # Store images list
            result['images'] = image_list

            # Extract author from metadata
            metadata = trafilatura.metadata.extract_metadata(downloaded)
            if metadata and metadata.author:
                result['author'] = metadata.author

        except Exception as e:
            print(f"  Content extraction failed: {e}")

        return result

    def _extract_images_from_markdown(self, markdown: str) -> List[str]:
        """Extract image URLs from markdown content"""
        try:
            # Match markdown image syntax: ![alt](url)
            img_pattern = r'!\[.*?\]\(([^)]+)\)'
            images = re.findall(img_pattern, markdown)

            # Deduplicate and filter
            unique_images = []
            seen = set()
            for img in images:
                if img not in seen:
                    seen.add(img)
                    if img.startswith('http'):
                        unique_images.append(img)

            return unique_images
        except Exception as e:
            print(f"  Markdown image extraction failed: {e}")
            return []

    def _extract_images(self, html: str, base_url: str) -> List[str]:
        """Extract image URLs from HTML using regex"""
        try:
            base = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"

            # Find all img tags with src attribute
            img_pattern = r'<img[^>]+src=[\'"]([^\'">]+)[\'"]'
            images = re.findall(img_pattern, html)

            # Convert to absolute URLs and deduplicate
            unique_images = set()
            for img in images:
                # Skip tracking pixels, analytics, and non-content images
                skip_patterns = ['adsct', 'analytics', 'pixel', 'facebook.com/tr', 'twitter.com/i']
                if any(x in img for x in skip_patterns):
                    continue
                if img.endswith('.gif') or 'icon' in img.lower():
                    continue

                # Skip small avatars/icons (check for size in URL like w_32, h_80, etc.)
                # Typical small sizes: w_32, w_36, w_80, h_32, h_36, h_80, w_64, h_64
                small_size_patterns = ['w_32', 'w_36', 'w_64', 'w_80', 'h_32', 'h_36', 'h_64', 'h_80']
                if any(x in img for x in small_size_patterns):
                    continue

                if img.startswith('http'):
                    unique_images.add(img)
                elif img.startswith('//'):
                    unique_images.add(f"https:{img}")
                else:
                    unique_images.add(urljoin(base, img))

            return list(unique_images)  # Return all content images
        except Exception as e:
            print(f"  Image extraction failed: {e}")
            return []

    def clean_content(self, content: str) -> str:
        """Clean and format extracted content"""
        if not content:
            return ""
        return content.strip()

    def _extract_content_with_images(self, html: str, image_list: List[str]) -> str:
        """Extract content using BeautifulSoup, preserving image positions"""
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Remove script, style, nav, footer, header elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
                element.decompose()

            # Find the main content (try common content containers)
            main_content = (soup.find('article') or
                           soup.find('main') or
                           soup.find('div', class_=re.compile(r'content|article|post|entry', re.I)) or
                           soup.body)

            if not main_content:
                return ""

            # Build text with embedded images
            content_parts = []

            # Extract base URL from image_list (all from same domain)
            base = ""
            if image_list:
                # Use the first image to determine base URL
                first_img = image_list[0]
                if first_img.startswith('http'):
                    parsed = urlparse(first_img)
                    base = f"{parsed.scheme}://{parsed.netloc}"
                elif first_img.startswith('/'):
                    # Relative path, need to get from HTML context
                    # Try to find base tag or use common domain
                    base_tag = soup.find('base')
                    if base_tag and base_tag.get('href'):
                        base = base_tag['href']
                    else:
                        base = "https://www.anthropic.com"

            # Build filename mapping for faster matching
            filename_to_idx = {}
            for i, img_url in enumerate(image_list):
                parsed = urlparse(img_url)
                # Extract filename from URL
                filename = parsed.path.split('/')[-1]
                # Also try with query parameter (Next.js URLs)
                if 'url=' in img_url:
                    from urllib.parse import unquote
                    # Extract the real URL from Next.js proxy
                    match = re.search(r'url=([^&]+)', img_url)
                    if match:
                        real_url = unquote(match.group(1))
                        real_parsed = urlparse(real_url)
                        filename = real_parsed.path.split('/')[-1]
                if filename:
                    filename_to_idx[filename] = i + 1

            for elem in main_content.descendants:
                if elem.name == 'img':
                    src = elem.get('src', '')
                    if not src:
                        continue
                    # Convert to absolute for matching
                    if src.startswith('http'):
                        abs_src = src
                    elif src.startswith('//'):
                        abs_src = f"https:{src}"
                    else:
                        abs_src = urljoin(base, src)

                    # Extract filename and find matching index
                    parsed_src = urlparse(abs_src)
                    src_filename = parsed_src.path.split('/')[-1]

                    # Also check for Next.js proxy URLs
                    if 'url=' in abs_src:
                        from urllib.parse import unquote, parse_qs
                        qs = parse_qs(parsed_src.query)
                        if 'url' in qs:
                            real_url = unquote(qs['url'][0])
                            real_parsed = urlparse(real_url)
                            src_filename = real_parsed.path.split('/')[-1]
                            # Use the real URL for display
                            abs_src = real_url

                    # Find matching index by filename
                    idx = filename_to_idx.get(src_filename, len(filename_to_idx) + 1)

                    content_parts.append(f'\n\n![图片{idx}]({abs_src})\n\n')
                elif elem.name in ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote', 'pre', 'code']:
                    text = elem.get_text(strip=True)
                    if text:
                        # Add heading markers
                        if elem.name == 'h1':
                            content_parts.append(f'\n# {text}\n')
                        elif elem.name == 'h2':
                            content_parts.append(f'\n## {text}\n')
                        elif elem.name == 'h3':
                            content_parts.append(f'\n### {text}\n')
                        elif elem.name == 'h4':
                            content_parts.append(f'\n#### {text}\n')
                        elif elem.name in ['li']:
                            content_parts.append(f'- {text}\n')
                        elif elem.name == 'blockquote':
                            content_parts.append(f'> {text}\n')
                        else:
                            content_parts.append(f'{text}\n')
                elif elem.name == 'br':
                    content_parts.append('\n')

            # Clean up excessive newlines
            result = '\n'.join(content_parts)
            result = re.sub(r'\n{3,}', '\n\n', result)
            return result.strip()

        except Exception as e:
            print(f"  BeautifulSoup extraction failed: {e}")
            # Fallback to trafilatura
            return trafilatura.extract(html) or ""
