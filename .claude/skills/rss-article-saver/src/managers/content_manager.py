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
        """Extract image URLs from HTML using regex, filtering out logos and icons"""
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

                # Skip logos
                logo_patterns = ['logo', 'brand', 'header-logo', 'site-logo', 'footer-logo']
                img_lower = img.lower()
                if any(pattern in img_lower for pattern in logo_patterns):
                    continue

                # Skip small avatars/icons (check for size in URL like w_32, h_80, etc.)
                # Typical small sizes: w_32, w_36, w_80, h_32, h_36, h_80, w_64, h_64
                small_size_patterns = ['w_32', 'w_36', 'w_64', 'w_80', 'h_32', 'h_36', 'h_64', 'h_80']
                if any(x in img for x in small_size_patterns):
                    continue

                # Skip placeholder images
                if 'placeholder' in img_lower:
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

            # Remove script, style, nav, footer, header elements (but keep iframe for videos)
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript']):
                element.decompose()

            # Find the main content (try common content containers)
            main_content = (soup.find('article') or
                           soup.find('main') or
                           soup.find('div', class_=re.compile(r'content|article|post|entry', re.I)) or
                           soup.body)

            if not main_content:
                return ""

            # Remove unrelated sections (ads, related posts, recommendations, etc.)
            self._remove_unrelated_sections(main_content)

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

            # Track processed elements to avoid duplicates
            processed = set()

            # Process elements in DOM order to preserve image positions in content
            # Get all relevant elements in order
            all_elements = main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'pre', 'ul', 'ol', 'img', 'iframe'])
            
            for elem in all_elements:
                elem_id = id(elem)
                if elem_id in processed:
                    continue

                # Check if this element is nested inside another list/block element
                parent = elem.find_parent(['ul', 'ol', 'li', 'p', 'blockquote', 'pre'])
                if parent and id(parent) in processed:
                    continue

                # Handle images
                if elem.name == 'img':
                    src = elem.get('src', '')
                    if not src:
                        continue

                    # Skip placeholder images
                    if 'placeholder' in src.lower():
                        continue

                    # Skip logo images
                    if any(pattern in src.lower() for pattern in ['logo', 'brand', 'header-logo', 'site-logo', 'footer-logo']):
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
                    processed.add(elem_id)
                
                # Handle iframes (videos)
                elif elem.name == 'iframe':
                    src = elem.get('src', '')
                    if src:
                        # Convert embed URLs to watchable URLs
                        video_url = src
                        if 'youtube.com/embed/' in src:
                            # Convert https://www.youtube.com/embed/VIDEO_ID
                            # to https://www.youtube.com/watch?v=VIDEO_ID
                            import re as re_module
                            match = re_module.search(r'/embed/([a-zA-Z0-9_-]+)', src)
                            if match:
                                video_id = match.group(1)
                                video_url = f"https://www.youtube.com/watch?v={video_id}"
                        elif 'youtu.be/' in src:
                            # Short URL already watchable
                            video_url = src
                        elif 'player.vimeo.com/video/' in src:
                            # Convert https://player.vimeo.com/video/VIDEO_ID
                            # to https://vimeo.com/VIDEO_ID
                            match = re_module.search(r'/video/([0-9]+)', src)
                            if match:
                                video_id = match.group(1)
                                video_url = f"https://vimeo.com/{video_id}"

                        # Add video link
                        if any(domain in src for domain in ['youtube.com', 'youtu.be', 'vimeo.com', 'player.vimeo.com']):
                            content_parts.append(f'\n[视频]({video_url})\n')
                    processed.add(elem_id)

                # Handle lists
                elif elem.name in ['ul', 'ol']:
                    # Check if this is a metadata list (skip it)
                    elem_classes = elem.get('class', []) or []
                    if any('details' in str(c).lower() for c in elem_classes):
                        processed.add(elem_id)
                        continue

                    # Process list items
                    for li in elem.find_all('li', recursive=False):
                        # Check if this is a metadata list item
                        li_classes = li.get('class', []) or []
                        if any('details' in str(c).lower() or 'hero_blog_post' in str(c).lower() for c in li_classes):
                            continue

                        text = li.get_text(strip=True)
                        if text:
                            # Also skip by content patterns
                            if any(text.startswith(p) for p in ['Category', 'Product', 'Date', 'Reading time', 'Copy link']):
                                continue

                            if elem.name == 'ul':
                                content_parts.append(f'- {text}\n')
                            else:
                                # Get the index from the parent
                                idx = 1
                                for prev_li in li.find_previous_siblings('li'):
                                    idx += 1
                                content_parts.append(f'{idx}. {text}\n')
                        processed.add(id(li))
                    processed.add(elem_id)
                
                # Handle text elements (headings, paragraphs, blockquotes, code)
                elif elem.name in ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'pre', 'code']:
                    # Skip h1 titles since they're already added at the file level
                    if elem.name == 'h1':
                        processed.add(elem_id)
                        continue
                    
                    if elem.name in ['pre', 'code']:
                        # Preserve original formatting for code blocks
                        text = elem.get_text()
                        if text:
                            # Use markdown code block format
                            content_parts.append(f'\n```\n{text}\n```\n')
                    else:
                        text = elem.get_text(strip=True)
                        if text:
                            # Skip metadata items (short, label-value pairs)
                            # These are typically things like "CategoryCoding", "ProductClaude Code", "DateNovember 25, 2025"
                            if elem.name == 'p':
                                # Skip if text starts with known metadata labels
                                metadata_prefixes = ['Category', 'Product', 'Date', 'Reading time', 'Copy link', 'CategoryCoding', 'ProductClaude']
                                if any(text.startswith(prefix) or text.replace(' ', '') == prefix for prefix in metadata_prefixes):
                                    processed.add(elem_id)
                                    continue
                            # Add heading markers with proper newlines
                            if elem.name == 'h2':
                                content_parts.append(f'\n\n## {text}\n\n')
                            elif elem.name == 'h3':
                                content_parts.append(f'\n\n### {text}\n\n')
                            elif elem.name == 'h4':
                                content_parts.append(f'\n\n#### {text}\n\n')
                            elif elem.name == 'blockquote':
                                content_parts.append(f'\n> {text}\n')
                            else:
                                content_parts.append(f'\n{text}\n')
                    processed.add(elem_id)

            # Handle line breaks
            for br in main_content.find_all('br'):
                # Only process br if not inside a processed element
                parent = br.find_parent(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'pre', 'li'])
                if not parent or id(parent) not in processed:
                    content_parts.append('\n')

            # Clean up excessive newlines
            result = '\n'.join(content_parts)
            result = re.sub(r'\n{3,}', '\n\n', result)

            # Clean up unrelated sections from markdown result
            result = self._clean_markdown_content(result)

            return result.strip()

        except Exception as e:
            print(f"  BeautifulSoup extraction failed: {e}")
            # Fallback to trafilatura
            return trafilatura.extract(html) or ""

    def _remove_unrelated_sections(self, soup) -> None:
        """Remove unrelated sections like ads, related posts, recommendations"""
        if not soup:
            return

        try:
            # Patterns to identify unrelated content
            unrelated_patterns = [
                # Related posts / recommendations
                r'related[\s_-]?posts?',
                r'recommended',
                r'you\s+might\s+also\s+like',
                r'read\s+more',
                r'see\s+also',
                r'popular\s+posts',
                r'recent\s+posts',
                r'more\s+from',
                r'up\s+next',
                r'further\s+reading',
                r'explore\s+more',

                # Comments
                r'comments?',
                r'discussion',
                r'replies?',
                r'faq',  # FAQ sections

                # Share buttons
                r'share',
                r'social[\s_-]?share?',
                r'twitter',
                r'facebook',
                r'linkedin',
                r'email\s+this',

                # Subscription / Newsletter
                r'subscribe',
                r'newsletter',
                r'follow\s+us',
                r'developer\s+newsletter',

                # Author info boxes (if separate)
                r'author[\s_-]?box',
                r'about\s+the\s+author',

                # Footer / end of article sections
                r'product\s+news',
                r'best\s+practices',

                # Ads
                r'advertisement?',
                r'sponsored',
                r'promoted',
            ]

            # Combine patterns into a single regex
            pattern = re.compile('|'.join(unrelated_patterns), re.IGNORECASE)

            # Remove elements with matching classes, ids, or text content
            for element in soup.find_all(True):
                if not element:
                    continue

                # Check class and id attributes
                classes = element.get('class', []) or []
                class_str = ' '.join(classes) if isinstance(classes, list) else str(classes)
                elem_id = element.get('id', '') or ''

                # Check if element matches unrelated patterns
                text_content = element.string
                if text_content and pattern.search(text_content):
                    # Found matching text content
                    should_remove = True
                elif pattern.search(class_str) or pattern.search(elem_id):
                    should_remove = True
                else:
                    should_remove = False

                if should_remove:
                    # Check if it's a heading followed by unrelated content
                    # Only remove if it's clearly an unrelated section
                    if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        text = element.get_text(strip=True).lower()
                        if any(keyword in text for keyword in [
                            'related posts', 'recommended', 'you might also like',
                            'read more', 'see also', 'popular posts', 'more from',
                            'comments', 'share', 'subscribe', 'newsletter'
                        ]):
                            element.decompose()
                    elif element.name in ['div', 'section', 'aside', 'nav']:
                        element.decompose()

            # Remove specific common container classes/ids for unrelated content
            for selector in [
                {'class_': re.compile(r'related|recommended|more-reading|see-also', re.I)},
                {'class_': re.compile(r'share|social|follow|subscribe|newsletter', re.I)},
                {'class_': re.compile(r'comments?|discussion|replies?', re.I)},
                {'id': re.compile(r'related|recommended|comments?|share', re.I)},
            ]:
                for elem in soup.find_all(**selector):
                    if elem:
                        elem.decompose()

            # Also remove headings with specific keywords and all content after them
            for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                heading_text = heading.get_text(strip=True).lower()
                if any(keyword in heading_text for keyword in [
                    'related posts', 'recommended', 'you might also like',
                    'read more', 'see also', 'popular posts', 'more from',
                    'explore more', 'faq', 'newsletter', 'subscribe',
                    'product news', 'best practices', 'get the developer'
                ]):
                    # Remove this heading and all following siblings
                    current = heading
                    while current:
                        next_elem = current.next_sibling
                        current.decompose()
                        current = next_elem
                        # Stop if we hit another heading at same or higher level
                        if current and current.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                            # Check if it's same or higher level (lower number)
                            try:
                                current_level = int(current.name[1])
                                heading_level = int(heading.name[1])
                                if current_level <= heading_level:
                                    break
                            except:
                                break
        except Exception as e:
            print(f"  Warning: Error removing unrelated sections: {e}")

    def _clean_markdown_content(self, markdown: str) -> str:
        """Remove unrelated sections from markdown content"""
        # Find headings that indicate unrelated content starts
        stop_patterns = [
            r'^## Related posts',
            r'^## Related Posts',
            r'^## Recommended',
            r'^## You might also like',
            r'^## Read more',
            r'^## See also',
            r'^## Popular posts',
            r'^## More from',
            r'^## Explore more',
            r'^## FAQ',
            r'^## Frequently Asked Questions',
            r'^## Get the developer',
            r'^## Subscribe',
            r'^## Newsletter',
            r'^## Product news',
            r'^## Transform how your organization',
        ]

        lines = markdown.split('\n')
        result_lines = []

        for line in lines:
            # Check if this line matches any stop pattern
            should_stop = False
            for pattern in stop_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    should_stop = True
                    break

            if should_stop:
                # Stop adding lines
                break

            result_lines.append(line)

        return '\n'.join(result_lines)
