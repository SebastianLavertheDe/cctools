---
name: rss-article-saver
description: RSS article subscription, syncs articles to Notion and saves as local Markdown
allowed-tools: Bash,Write,Read
---

# RSS Article Saver

Subscribes to RSS feeds (configured via OPML), syncs articles to Notion (with images), and saves as local Markdown files.

## Features

- 📡 **RSS Support**: Subscribe to feeds via OPML file
- 📝 **Markdown Export**: Saves articles as Markdown with embedded images to ~/mymind/article/
- 📊 **Notion Sync**: Syncs articles to Notion database with images
- 🔄 **Deduplication**: Skips already synced articles using cache
- 🖼️ **Image Support**: Extracts and includes article images

## Usage

```bash
cd /home/say/cctools/.claude/skills/rss-article-saver
uv sync
uv run --env-file .env python main.py
```

## Configuration

### 1. Environment Variables (.env)

Required:
```bash
notion_key=secret_xxx      # Notion integration token
NOTION_DATABASE_ID=xxx     # Target Notion database ID
```

### 2. OPML File (subscriptions.opml)

Define your RSS subscriptions in OPML format:

```xml
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<opml version="2.0">
    <head>
        <title>My RSS Subscriptions</title>
    </head>
    <body>
        <outline text="ByteByteGo Newsletter" type="rss" xmlUrl="https://blog.bytebytego.com/feed"/>
        <outline text="Last Week in AI" type="rss" xmlUrl="https://lastweekin.ai/feed/"/>
        <!-- Add more feeds here -->
    </body>
</opml>
```

### 3. Notion Database Setup

Create a Notion database with these properties:
- **Title** (Title)
- **Link** (URL)
- **Author** (Text)
- **Status** (Status) - Optional

### 4. Config File (config.yaml)

Adjust settings in `config.yaml`:
- `opml_file`: Path to your OPML file
- `max_articles_per_feed`: Max articles per feed (default: 999)
- `ai.enabled`: AI features disabled by default
- `notion.sync`: Enable/disable Notion sync

## Output

### Saved Articles

Articles are saved to `~/mymind/article/` as Markdown files:
```
YYYYMMDD_HHMMSS_Article Title.md
```

Each article contains:
- **元数据**: Link, author, published date, saved time
- **文章图片**: List of image URLs
- **正文**: Full content with images embedded in Markdown format

### Deduplication

- Uses `article_cache.json` to track processed articles
- Already synced articles are skipped automatically
