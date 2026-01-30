"""
RSS Monitor - Main orchestrator for multi-feed RSS to Notion sync
"""

import sys
from ..managers.config_manager import RSSConfig
from ..managers.opml_parser import OPMLParser
from ..managers.rss_manager import RSSManager


class RSSMonitor:
    """Multi-feed RSS monitor"""

    def __init__(self):
        """Initialize the RSS monitor"""
        self.config = RSSConfig()
        self.rss_manager = RSSManager(self.config)
        self.opml_parser = OPMLParser(self.config.get_opml_file())

    def monitor(self) -> None:
        """Main monitoring workflow"""
        print("=" * 50)
        print("RSS to Notion Monitor")
        print("=" * 50)

        # Load RSS feeds from OPML
        feeds = self.opml_parser.parse()

        if not feeds:
            print("No RSS feeds found. Please check your subscriptions.opml file.")
            sys.exit(1)

        # Process each feed
        for feed in feeds:
            print(f"\n{'=' * 50}")
            print(f"Feed: {feed.title}")
            print(f"URL: {feed.url}")
            print("=" * 50)

            parsed_feed = self.rss_manager.fetch_feed(feed)
            if parsed_feed:
                if isinstance(parsed_feed, dict) and parsed_feed.get("type") == "opml":
                    print(f"Processing nested OPML feeds...")
                    nested_feeds = parsed_feed.get("feeds", [])
                    parent_title = parsed_feed.get("parent_title", feed.title)
                    parent_category = parsed_feed.get("parent_category", feed.category)

                    for nested_feed in nested_feeds:
                        print(f"\n  {'-' * 40}")
                        print(f"  Nested Feed: {nested_feed.title}")
                        print(f"  URL: {nested_feed.url}")
                        print(f"  Parent: {parent_title}")
                        print("  " + "-" * 40)

                        nested_parsed = self.rss_manager.fetch_feed(nested_feed)
                        if nested_parsed:
                            print(f"  Entries: {len(nested_parsed.entries)}")
                            self.rss_manager.process_feed(
                                nested_parsed, nested_feed, parent_category
                            )
                        else:
                            print(f"  Failed to fetch nested feed: {nested_feed.title}")
                else:
                    print(f"Entries: {len(parsed_feed.entries)}")
                    self.rss_manager.process_feed(parsed_feed, feed)
            else:
                print(f"Failed to fetch feed: {feed.title}")

        print("\n" + "=" * 50)
        print("Done!")
        print("=" * 50)
