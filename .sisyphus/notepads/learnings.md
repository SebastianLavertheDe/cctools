# Learnings - RSS Article Saver Nested OPML Support

## Implementation Summary
Successfully modified RSS article saver to automatically detect and handle nested OPML files.

## Key Changes Made

### 1. Modified `src/managers/rss_manager.py` - `fetch_feed` method
- Added OPML detection logic before feedparser parsing
- Uses `requests` library to fetch URL content
- Checks if content contains `<opml>` tag (case-insensitive)
- If OPML detected:
  - Creates temporary file to store OPML content
  - Uses `OPMLParser` to parse nested feeds
  - Returns special dict structure: `{'type': 'opml', 'feeds': nested_feeds, 'parent_title': feed.title}`
  - Cleans up temporary file in finally block
- Falls back to feedparser for regular RSS feeds
- Proper exception handling with graceful fallback

### 2. Modified `src/core/monitor.py` - `monitor` method
- Added check for OPML type in returned `parsed_feed`
- When OPML detected:
  - Iterates through all nested feeds
  - For each nested feed:
    - Displays feed info with parent title
    - Calls `fetch_feed` again to fetch actual RSS content
    - Calls `process_feed` to process articles
- Maintains original behavior for regular RSS feeds

## Testing Results

### Successful Detection
```
Feed: Blog RSS
URL: https://raw.githubusercontent.com/SebastianLavertheDe/blog-rss-feed/main/blog_rss.xml
==================================================
  Fetching URL to check content type...
  Detected OPML file, parsing nested feeds...
Loaded 8 RSS feeds from /tmp/tmp_7p1x9td.opml
  Found 8 nested RSS feeds in OPML
Processing nested OPML feeds...
```

### Nested Feeds Detected
The code successfully parsed 8 technical blog RSS feeds:
1. Anthropic Engineering Blog
2. Cursor Blog
3. Claude Blog
4. OpenAI Blog
5. LangChain Blog
6. Andrej Karpathy Blog
7. MarkTechPost
8. Azure Blog

## Important Discovery

### GitHub Blob URL Issue
The blog_rss.xml file contains GitHub blob URLs (e.g., `https://github.com/.../blob/main/rss/file.xml`) which are HTML pages, not raw XML content. When accessed via blob URLs:
- feedparser returns 0 entries
- Parse warnings: "not well-formed (invalid token)"

### Solution
Raw GitHub URLs should be used instead (e.g., `https://raw.githubusercontent.com/.../main/rss/file.xml`). When using raw URLs, RSS feeds are parsed correctly with multiple entries.

**Note**: This URL conversion issue is NOT part of the current task scope. The nested OPML handling is working correctly - it's the source URLs in the OPML file that need correction.

## Code Quality
- Both files pass Python syntax validation (`python -m py_compile`)
- Proper exception handling with fallback mechanisms
- Temporary file cleanup implemented
- Clear console logging for debugging
- Preserves existing functionality for regular RSS feeds

## Future Improvements
1. Add automatic GitHub blob-to-raw URL conversion
2. Add better error messages for invalid feed URLs
3. Consider adding validation for OPML feed URLs
4. Add metrics to track OPML vs regular feed processing

## GitHub Blob URL Conversion Fix

### Problem
Nested RSS feeds in blog_rss.xml used GitHub blob URLs (e.g., `https://github.com/user/repo/blob/branch/file.xml`), which return HTML pages instead of raw XML content. This caused feedparser to return 0 entries.

### Solution Implemented
Modified `src/managers/rss_manager.py` in the `fetch_feed` method to:
1. Add URL conversion logic before fetching content (line 103-109)
2. Detect GitHub blob URLs containing `github.com` and `/blob/`
3. Automatically convert to raw GitHub URLs: `github.com/user/repo/blob/branch/path` → `raw.githubusercontent.com/user/repo/branch/path`
4. Apply conversion in both main code path and exception fallback path (lines 152, 171)
5. Log conversion for debugging: "Converted GitHub blob URL to raw URL"

### Testing Results
Direct test of fetch_feed method:
```
Fetching nested feed...
  Fetching URL to check content type...
  Converted GitHub blob URL to raw URL
  Feed parse warning: text/plain; charset=utf-8 is not an XML media type
Result type: <class 'feedparser.util.FeedParserDict'>
Entries: 14
First entry: What's new in Claude: Turning Claude into your thi
```

✅ URL conversion working correctly
✅ Feed now returns 14 entries (was 0 before)
✅ Content is being parsed successfully
✅ Warning about media type is informational, not an error

### Code Changes
- Line 103-109: Added URL conversion in main path
- Line 152: Use converted URL in feedparser call
- Line 163-169: Added URL conversion in exception fallback
- Line 171: Use converted URL in fallback feedparser call

### Note
When running python scripts with heredoc or stdin, `load_dotenv()` may fail with AssertionError due to frame inspection. This is a known issue with python-dotenv and doesn't affect normal execution via `python main.py` or `uv run --env-file .env python main.py`.
