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
            print('=' * 50)

            parsed_feed = self.rss_manager.fetch_feed(feed)
            if parsed_feed:
                print(f"Entries: {len(parsed_feed.entries)}")
                self.rss_manager.process_feed(parsed_feed, feed)
            else:
                print(f"Failed to fetch feed: {feed.title}")

        print("\n" + "=" * 50)
        print("Done!")
        print("=" * 50)
