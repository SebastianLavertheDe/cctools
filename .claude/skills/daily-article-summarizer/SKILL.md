---
name: daily-article-summarizer
description: Summarize daily articles from ~/mymind and push to Notion
allowed-tools: Bash,Write,Read
---

# Daily Article Summarizer

Automatically scans, summarizes, and syncs daily articles from your `~/mymind/article/` directory to Notion.

## Features

- 📅 **Daily Scanning**: Automatically finds today's articles in `~/mymind/article/YYYYMMDD/`
- 🤖 **AI Summarization**: Uses NVIDIA AI (minimax model) to generate Chinese summaries
- 💾 **Smart Caching**: Tracks summarized articles to avoid reprocessing
- 📊 **Notion Sync**: Pushes daily summaries to your Notion database

## Usage

```bash
cd /home/say/work/github/cctools/.claude/skills/daily-article-summarizer

# Install dependencies
uv sync

# Setup environment
cp .env.example .env
# Edit .env with your API keys

# Run the summarizer
uv run --env-file .env python main.py
```

## Configuration

### 1. Environment Variables (.env)

Required:
```bash
# NVIDIA API for AI summarization
NVIDIA_API_KEY=nvapi-xxx
NVIDIA_API_BASE=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=minimaxai/minimax-m2.1

# Notion API
notion_key=secret_xxx
NOTION_DATABASE_ID=xxx
```

### 2. Config File (config.yaml)

```yaml
# Article source directory
article_directory: "~/mymind/article"

# AI settings
ai:
  provider: nvidia
  model: minimaxai/minimax-m2.1
  max_articles_per_day: 20
  batch_size: 5

# Notion settings
notion:
  sync: true
  database_id: "2d83c1497bd580b7824de65c408b11f8"

# Cache file
cache_file: "summary_cache.json"
```

## How It Works

1. **Scan**: Reads all markdown files from `~/mymind/article/YYYYMMDD/`
2. **Filter**: Checks cache to skip already summarized articles
3. **Summarize**: Uses NVIDIA AI to generate summaries for new articles
4. **Cache**: Saves summary results to `summary_cache.json`
5. **Sync**: Creates a daily summary page in Notion

## Output

### Cache File Structure

```json
{
  "20260130": {
    "article_file.md": {
      "summary": "...",
      "key_points": ["...", "..."],
      "category": "AI",
      "score": 85,
      "processed_at": "2026-01-30 10:30:00",
      "notion_page_id": "page-id"
    }
  }
}
```

### Notion Page

Each day creates a new page with:
- **Title**: "Daily Summary - YYYY-MM-DD"
- **Date**: The summary date
- **Summary**: Consolidated summary of all articles
- **Article Count**: Number of articles summarized
