---
name: rss-article-saver
description: RSS article subscription with AI scoring, save high-quality articles (score>=70) to local Markdown and Notion
allowed-tools: Bash,Write,Read
---

# RSS Article Saver

Subscribes to multiple RSS feeds (configured via OPML), uses AI to score articles, and saves high-quality articles (score>=70) as local Markdown files and syncs to Notion.

## Features

- 📡 **Multi-RSS Support**: Subscribe to multiple feeds via OPML file
- 🤖 **AI Scoring**: Uses DeepSeek AI to score articles (0-100)
- 🎯 **Smart Filtering**: Only saves articles with score >= 70
- 📝 **Markdown Export**: Saves articles as Markdown with embedded images
- 📊 **Notion Sync**: Syncs high-quality articles to Notion database
- 🔍 **AI Analysis**: Generates Chinese summary, title translation, and categorization

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
DEEPSEEK_API_KEY=sk-xxx  # For AI analysis and scoring
notion_key=secret_xxx      # Notion integration token
NOTION_DATABASE_ID=xxx     # Target Notion database ID
```

Optional:
```bash
AI_MODEL=deepseek-chat      # AI model (default: deepseek-chat)
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
- **Summary** (Text)
- **Category** (Select)
- **Score** (Number)
- **Status** (Status)

### 4. Config File (config.yaml)

Adjust settings in `config.yaml`:
- `opml_file`: Path to your OPML file
- `max_articles_per_feed`: Max articles per feed (default: 1)
- `ai.enabled`: Enable/disable AI features
- `ai.categories`: Available article categories

## Output

### Saved Articles

Articles are saved to `/home/say/cctools/article/` as Markdown files:
```
YYYYMMDD_HHMMSS_Article Title.md
```

Each article contains:
- **元数据**: Link, author, published date, score, category
- **AI 分析**: Full AI analysis (summary, key points, evidence, value, scoring)
- **正文**: Full content with images embedded in Markdown format

### Filtering

- Articles with **score < 70** are skipped (not saved, not synced)
- Articles with **score >= 70** are saved as Markdown and synced to Notion
