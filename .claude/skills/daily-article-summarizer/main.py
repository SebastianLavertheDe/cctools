#!/usr/bin/env python3
"""
Daily Article Summarizer
Scans ~/mymind/article/ for today's articles, summarizes them with AI, and pushes to Notion
"""

import os
import sys
from dotenv import load_dotenv
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.managers.article_scanner import ArticleScanner
from src.managers.cache_manager import CacheManager
from src.managers.summarizer import ArticleSummarizer
from src.managers.notion_manager import NotionSummaryManager
import yaml

load_dotenv()


def load_config(config_file: str = "config.yaml") -> dict:
    """Load configuration from YAML file"""
    try:
        with open(config_file, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}


def main():
    """Main execution pipeline"""
    try:
        print("=" * 50)
        print("Daily Article Summarizer")
        print("=" * 50)

        # Load configuration
        config = load_config()
        article_dir = config.get("article_directory", "~/mymind/article")
        ai_config = config.get("ai", {})
        notion_config = config.get("notion", {})
        cache_file = config.get("cache_file", "summary_cache.json")

        # Get today's date
        today = datetime.now().strftime("%Y%m%d")
        print(f"\n📅 Date: {today}")

        # Step 1: Scan for articles
        print(f"\n📂 Scanning articles from {article_dir}/{today}...")
        scanner = ArticleScanner(article_dir)
        articles = scanner.get_todays_articles()
        print(f"  Found {len(articles)} articles")

        if not articles:
            print("\n✅ No articles to process")
            return

        # Step 2: Check cache
        print(f"\n💾 Checking cache...")
        cache_manager = CacheManager(cache_file)
        new_articles = [
            a for a in articles if not cache_manager.is_summarized(today, a.filename)
        ]
        cached_summaries = cache_manager.get_all_summaries_for_date(today)

        print(f"  New articles: {len(new_articles)}")
        print(f"  Cached summaries: {len(cached_summaries)}")

        if not new_articles:
            print("\n✅ All articles already summarized")
            # Still push to Notion if enabled
            if cached_summaries and notion_config.get("sync", False):
                print(f"\n📤 Pushing cached summaries to Notion...")
                notion_manager = NotionSummaryManager(notion_config.get("database_id"))
                all_summaries = list(cached_summaries.values())
                notion_manager.push_daily_summary(today, all_summaries)
            return

        # Step 3: Summarize new articles
        print(f"\n🤖 Summarizing {len(new_articles)} new articles...")
        summarizer = ArticleSummarizer()
        batch_size = ai_config.get("batch_size", 5)
        new_summaries = summarizer.batch_summarize(
            new_articles, today, batch_size=batch_size
        )

        print(f"\n  Successfully summarized: {len(new_summaries)}/{len(new_articles)}")

        # Step 4: Update cache
        print(f"\n💾 Updating cache...")
        for summary in new_summaries:
            filename = os.path.basename(summary.file_path)
            cache_manager.mark_as_summarized(today, filename, summary)

        # Step 5: Save daily summary to local Markdown
        print(f"\n📄 Saving daily summary to local Markdown...")

        # Save to project root ./mymind/daily-summary directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up three levels: skill -> skills -> .claude -> project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
        summary_dir = os.path.join(project_root, "mymind", "daily-summary")
        os.makedirs(summary_dir, exist_ok=True)

        summary_file = os.path.join(summary_dir, f"{today}_daily_summary.md")
        all_summaries = new_summaries + list(cached_summaries.values())

        # Group by category
        by_category = {}
        for summary in all_summaries:
            if summary.category not in by_category:
                by_category[summary.category] = []
            by_category[summary.category].append(summary)

        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(f"# 📅 {today[:4]}-{today[4:6]}-{today[6:8]} 每日总结\n\n")
            f.write(f"**共总结 {len(all_summaries)} 篇文章**\n\n")
            f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")

            for category, category_summaries in sorted(by_category.items()):
                f.write(f"## 📚 {category}\n\n")

                for summary in category_summaries:
                    score_emoji = "⭐" if summary.score >= 80 else "📖" if summary.score >= 60 else "📄"
                    f.write(f"### {score_emoji} {summary.title}\n\n")
                    f.write(f"**评分**: {summary.score}/100\n\n")
                    f.write(f"**摘要**:\n{summary.summary}\n\n")

                    if summary.key_points:
                        f.write("**关键要点**:\n")
                        for point in summary.key_points[:5]:
                            f.write(f"- {point}\n")
                        f.write("\n")

                    if summary.source_url:
                        f.write(f"**链接**: [{summary.source_url}]({summary.source_url})\n\n")

                    f.write("---\n\n")

        print(f"  ✅ Saved to: {summary_file}")

        # Step 6: Push to Notion
        if notion_config.get("sync", False):
            print(f"\n📤 Pushing to Notion...")

            notion_manager = NotionSummaryManager(notion_config.get("database_id"))
            page_id = notion_manager.push_daily_summary(today, all_summaries)

            if page_id:
                print(f"  ✅ Notion page created: {page_id}")

        print(f"\n✅ Done! Processed {len(new_summaries)} new articles")

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
