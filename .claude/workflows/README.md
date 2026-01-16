# Tech Article Collector

A Claude Code workflow for collecting articles from various sources (Reddit, RSS feeds), analyzing them with AI, and publishing to Notion.

## Features

- 📥 **Multi-source Collection**: Collect articles from Reddit (web scraping) and RSS feeds
- 🤖 **AI-Powered Analysis**: Automatic scoring, categorization, and summarization using DeepSeek or OpenAI
- ⭐ **Quality Filtering**: Filter articles based on AI-generated quality scores
- 📝 **Notion Publishing**: Publish curated articles to Notion with structured layouts
- ⚙️ **Configuration Management**: Easy configuration via YAML files

## Skills

This workflow uses the following Claude Code skills:

1. **reddit-collector**: Collects hot posts from Reddit subreddits (via web scraping)
2. **content-extractor**: Extracts full content from web pages
3. **ai-content-analyzer**: Analyzes content using AI (scoring, categorization, summarization)
4. **notion-publisher**: Publishes formatted content to Notion databases

## Installation

```bash
# Install required dependencies
pip install httpx beautifulsoup4 openai notion-client pyyaml requests trafilatura feedparser

# Optional: for advanced content extraction
pip install firecrawl
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Reddit Collection (web scraping, no API needed)
REDDIT_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36

# AI Provider (choose one)
DEEPSEEK_API_KEY=your_deepseek_api_key
# OR
OPENAI_API_KEY=your_openai_api_key

# Notion (for publishing)
NOTION_DATABASE_ID=your_notion_database_id
notion_key=your_notion_integration_token

# Optional
AI_MODEL=deepseek-chat  # or gpt-3.5-turbo
FIRECRAWL_API_KEY=your_firecrawl_api_key
```

### Workflow Configuration

Edit `.claude/workflows/tech-article-collector.yaml` to configure:

- Data sources (Reddit subreddits, RSS feeds)
- Processing rules (score thresholds, limits)
- AI analysis settings
- Notion publishing options

## Usage

### Run the Complete Workflow

```bash
# Run with default settings
python .claude/workflows/tech-article-collector.py

# Limit to 20 articles
python .claude/workflows/tech-article-collector.py --limit 20

# Collect from specific sources only
python .claude/workflows/tech-article-collector.py --sources reddit rss

# Collect from Reddit only
python .claude/workflows/tech-article-collector.py --sources reddit
```

### Use Individual Skills

```bash
# Collect Reddit posts (web scraping)
python -m reddit_collector hot golang 20 50

# Collect via RSS
python -m reddit_collector rss ArtificialIntelligence hot 20

# Extract content from URL
python -m content_extractor https://example.com/article

# Analyze content with AI
python -m ai_content_analyzer "Article Title" "Article content..."

# Publish to Notion
python -m notion_publisher '{"title": "...", "content": "..."}'
```

## Workflow Steps

1. **Collection**: Gather articles from configured Reddit subreddits and RSS feeds
   - Reddit: Uses web scraping (httpx + BeautifulSoup) instead of API
   - RSS: Uses feedparser for standard RSS/Atom feeds

2. **Extraction**: Extract full content from article URLs
   - Primary: trafilatura for structured extraction
   - Fallback: BeautifulSoup for HTML parsing

3. **AI Analysis**: Score, categorize, and summarize using AI
   - Comprehensive analysis with scoring breakdown
   - Automatic category and tag assignment
   - Difficulty level estimation

4. **Filtering**: Filter by quality score (default threshold: 60)
   - Multi-dimensional scoring
   - Customizable thresholds

5. **Publishing**: Publish to Notion with structured formatting
   - Rich page layouts
   - Multiple template options

## Notion Integration

The workflow publishes articles to Notion with:

- **Properties**: Title, Link, Author, Category, Score, Reading Time, Difficulty, Tags
- **Content**: AI summary, Key points, Tags, Metadata
- **Templates**: Default, Minimal, Detailed layouts

## Reddit Collection (Web Scraping)

Instead of using the Reddit API (which requires authentication and has rate limits), this workflow uses web scraping to collect posts:

- **Method**: httpx + BeautifulSoup to parse Reddit HTML
- **Fallback**: Regex-based parsing if BeautifulSoup unavailable
- **Alternative**: RSS feed collection via feedparser

### Supported Reddit URLs:
- `https://old.reddit.com/r/{subreddit}/hot/`
- `https://old.reddit.com/r/{subreddit}/new/`
- `https://old.reddit.com/r/{subreddit}/top.rss`

## Customization

### Add New Reddit Subreddit

Add to `sources.reddit_subreddits` in the config:

```yaml
- name: "r/newsubreddit"
  subreddit: "newsubreddit"
  category: "AI"
  priority: "high"
  post_limit: 20
  min_score: 50
```

### Add New RSS Feed

Add to `sources.rss_feeds` in the config:

```yaml
- name: "New Blog"
  url: "https://example.com/rss.xml"
  category: "Technology"
  priority: "medium"
  max_articles: 10
```

### Adjust AI Scoring

Modify `processing.min_score_threshold` to change quality filtering:

```yaml
processing:
  min_score_threshold: 70  # Only publish articles with score >= 70
```

## Project Structure

```
.claude/
├── workflows/
│   ├── tech-article-collector.py      # Main workflow
│   └── tech-article-collector.yaml    # Configuration
├── skills/
│   ├── reddit-collector/              # Reddit collection skill
│   │   └── src/
│   │       ├── collector.py           # Main collector
│   │       └── web_scraper.py         # Web scraping implementation
│   ├── content-extractor/             # Content extraction skill
│   ├── ai-content-analyzer/           # AI analysis skill
│   ├── notion-publisher/              # Notion publishing skill
│   └── rss-article-saver/             # Existing RSS skill (reused)
```

## Dependencies

- `httpx`: Modern HTTP client for web scraping
- `beautifulsoup4`: HTML parsing
- `feedparser`: RSS/Atom feed parsing
- `trafilatura`: Web content extraction
- `requests`: HTTP requests
- `openai`: AI API client
- `notion-client`: Notion API client
- `pyyaml`: Configuration management

## License

MIT License
