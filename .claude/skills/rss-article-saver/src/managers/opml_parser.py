"""
OPML Parser - Parse OPML files to extract RSS feed subscriptions
"""

import os
import xml.etree.ElementTree as ET
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class RSSFeed:
    """RSS feed subscription"""

    text: str
    title: str
    url: str
    type: str = "rss"
    category: str = "article"


class OPMLParser:
    """Parse OPML files to extract RSS feed subscriptions"""

    def __init__(self, opml_file: str = "subscriptions.opml"):
        self.opml_file = opml_file

    def parse(self) -> List[RSSFeed]:
        """
        Parse OPML file and extract RSS feed subscriptions

        Returns:
            List of RSSFeed objects
        """
        if not os.path.exists(self.opml_file):
            raise FileNotFoundError(f"OPML file not found: {self.opml_file}")

        feeds = []

        try:
            tree = ET.parse(self.opml_file)
            root = tree.getroot()

            # Find all outline elements with type="rss", type="post", etc.
            rss_outlines = root.findall(".//outline[@type='rss']")
            post_outlines = root.findall(".//outline[@type='post']")
            all_outlines = rss_outlines + post_outlines

            for outline in all_outlines:
                text = outline.get("text", "")
                title = outline.get("title", text)
                url = outline.get("xmlUrl", "")
                feed_type = outline.get("type", "rss")
                feed_category = outline.get("category", "article")

                if url:
                    feeds.append(
                        RSSFeed(
                            text=text,
                            title=title,
                            url=url,
                            type=feed_type,
                            category=feed_category,
                        )
                    )

            print(f"Loaded {len(feeds)} RSS feeds from {self.opml_file}")

            # If no RSS feeds found, check for xmlUrl attribute without type
            if not feeds:
                for outline in root.findall(".//outline[@xmlUrl]"):
                    text = outline.get("text", "")
                    title = outline.get("title", text)
                    url = outline.get("xmlUrl", "")
                    feed_type = outline.get("type", "rss")
                    feed_category = outline.get("category", "article")

                    if url:
                        feeds.append(
                            RSSFeed(
                                text=text,
                                title=title,
                                url=url,
                                type=feed_type,
                                category=feed_category,
                            )
                        )

                if feeds:
                    print(
                        f"Loaded {len(feeds)} RSS feeds from {self.opml_file} (without type attribute)"
                    )

            if not feeds:
                print(f"Warning: No RSS feeds found in {self.opml_file}")

            return feeds

        except ET.ParseError as e:
            print(f"Error parsing OPML file: {e}")
            return []
        except Exception as e:
            print(f"Error reading OPML file: {e}")
            return []
