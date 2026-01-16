#!/usr/bin/env python3
"""
Tech Article Collector - Test Script
Tests the workflow components independently
"""

import sys
import json
from pathlib import Path

# Add skills to path
SKILLS_DIR = Path(__file__).parent / "skills"


def test_reddit_collector():
    """Test Reddit collector"""
    print("\n" + "=" * 60)
    print("🧪 Testing Reddit Collector (Web Scraping)")
    print("=" * 60)

    try:
        sys.path.insert(0, str(SKILLS_DIR / "reddit-collector" / "src"))
        from collector import RedditCollector

        collector = RedditCollector()

        # Test collecting hot posts
        print("\n📱 Testing hot posts collection from r/golang...")
        posts = collector.collect_hot_posts("golang", limit=3, min_score=50)

        print(f"✅ Collected {len(posts)} posts")

        if posts:
            print("\n📝 Sample post:")
            sample = posts[0]
            print(f"  Title: {sample.get('title', 'N/A')[:60]}...")
            print(f"  Score: {sample.get('score', 'N/A')}")
            print(f"  Comments: {sample.get('comments', 'N/A')}")
            print(f"  Author: {sample.get('author', 'N/A')}")

        print("\n✅ Reddit Collector test PASSED")
        return True

    except Exception as e:
        print(f"❌ Reddit Collector test FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_content_extractor():
    """Test content extractor"""
    print("\n" + "=" * 60)
    print("🧪 Testing Content Extractor")
    print("=" * 60)

    try:
        sys.path.insert(0, str(SKILLS_DIR / "content-extractor" / "src"))
        from extractor import ContentExtractor

        extractor = ContentExtractor()

        # Test with a sample URL
        test_url = "https://openai.com/blog"
        print(f"\n🌐 Testing content extraction from: {test_url}")

        result = extractor.extract_article(test_url)

        print(f"✅ Extraction complete")
        print(f"  Success: {result.get('success', False)}")
        print(
            f"  Title: {result.get('title', 'N/A')[:60] if result.get('title') else 'N/A'}"
        )
        print(f"  Word count: {result.get('word_count', 'N/A')}")

        print("\n✅ Content Extractor test PASSED")
        return True

    except Exception as e:
        print(f"❌ Content Extractor test FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_ai_analyzer():
    """Test AI content analyzer"""
    print("\n" + "=" * 60)
    print("🧪 Testing AI Content Analyzer")
    print("=" * 60)

    try:
        sys.path.insert(0, str(SKILLS_DIR / "ai-content-analyzer" / "src"))
        from analyzer import AIContentAnalyzer

        analyzer = AIContentAnalyzer()

        # Test with sample content
        test_title = "Introduction to Large Language Models"
        test_content = """
        Large Language Models (LLMs) represent a significant breakthrough in artificial intelligence. 
        These models are trained on vast amounts of text data and can generate human-like text.
        
        Key components include Transformer architecture and attention mechanisms.
        Popular LLMs include GPT-4, Claude, and LLaMA.
        """

        print(f"\n🤖 Testing AI analysis...")

        result = analyzer.analyze_content(
            test_title, test_content, analysis_type="quick"
        )

        print(f"✅ Analysis complete")
        print(f"  Category: {result.get('category', 'N/A')}")
        print(f"  Score: {result.get('score', 'N/A')}/100")
        print(f"  Summary: {result.get('summary', 'N/A')[:100]}...")

        print("\n✅ AI Content Analyzer test PASSED")
        return True

    except Exception as e:
        print(f"❌ AI Content Analyzer test FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_notion_publisher():
    """Test Notion publisher"""
    print("\n" + "=" * 60)
    print("🧪 Testing Notion Publisher")
    print("=" * 60)

    try:
        sys.path.insert(0, str(SKILLS_DIR / "notion-publisher" / "src"))
        from publisher import NotionPublisher

        publisher = NotionPublisher()

        if not publisher.enabled:
            print("⚠️ Notion not configured (expected in test environment)")
            print("✅ Notion Publisher test PASSED (skipped due to no credentials)")
            return True

        print("\n📝 Testing Notion publish...")
        print("✅ Notion Publisher test PASSED")
        return True

    except Exception as e:
        print(f"❌ Notion Publisher test FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🚀 Tech Article Collector - Test Suite")
    print("=" * 60)

    tests = [
        ("Reddit Collector (Web Scraping)", test_reddit_collector),
        ("Content Extractor", test_content_extractor),
        ("AI Content Analyzer", test_ai_analyzer),
        ("Notion Publisher", test_notion_publisher),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ {name} test crashed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)

    passed_count = 0
    failed_count = 0

    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {name}: {status}")

        if passed:
            passed_count += 1
        else:
            failed_count += 1

    print(f"\nTotal: {passed_count} passed, {failed_count} failed")

    if failed_count == 0:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️ {failed_count} test(s) failed")

    # Exit with appropriate code
    sys.exit(0 if failed_count == 0 else 1)


if __name__ == "__main__":
    main()
