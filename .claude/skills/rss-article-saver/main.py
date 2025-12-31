#!/usr/bin/env python3
"""
RSS to Notion Monitor - Entry point
"""

from dotenv import load_dotenv

load_dotenv()

from src.core.monitor import RSSMonitor


def main():
    try:
        monitor = RSSMonitor()
        monitor.monitor()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
