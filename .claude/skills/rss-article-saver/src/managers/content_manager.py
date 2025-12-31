"""
Content Manager - Full content extraction using trafilatura
"""

import trafilatura
import requests
import re
from typing import Optional, Dict, List
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


class ContentExtractor:
    """Extract full content from article URLs"""

    def __init__(self, config: dict):
        self.extractor = config.get('extractor', 'trafilatura')
        self.include_images = config.get('include_images', True)
        self.max_length = config.get('max_content_length', 50000)

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
            image_set = set(image_list)

            for elem in main_content.descendants:
                if elem.name == 'img':
                    src = elem.get('src', '')
                    if src in image_set:
                        idx = image_list.index(src)
                        content_parts.append(f'\n\n![图片{idx+1}]({src})\n\n')
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
