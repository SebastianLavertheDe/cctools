---
name: tech-article-collector
description: Collect AI/Tech articles from Reddit and RSS feeds, analyze with AI, and publish to Notion database. Use this when user wants to gather tech articles or publish to Notion.
allowed-tools: Bash,Read,Write,Glob,Grep
---

# Tech Article Collector

从 Reddit 和 RSS 收集 AI/科技文章，用 AI 分析质量，并发布到 Notion 数据库。

## 使用场景

- 用户想"收集 AI 文章"
- 用户想"从 RSS 抓取文章并发布到 Notion"
- 用户想"获取最新的技术文章"
- 用户想"运行 tech article collector"

## 工作目录

```
/home/say/work/github/cctools/.claude/workflows/
```

## 使用方法

```bash
# 收集并分析文章
python3 run_standalone.py --limit 20

# 只收集，不分析
python3 run_standalone.py --collect-only

# 发布到 Notion
python3 notion_manager.py
```

## 配置

在 `.claude/workflows/.env` 中配置：
- `NVIDIA_API_KEY` 或 `DEEPSEEK_API_KEY` - AI 分析
- `notion_key` - Notion API key
- `NOTION_DATABASE_ID` - Notion 数据库 ID

## 流程

1. 从 Reddit RSS 和其他 RSS feeds 收集文章
2. 用 AI 分析并评分（标题、难度、摘要、关键点）
3. 过滤低于阈值的文章（默认 60 分）
4. 发布高质量文章到 Notion 数据库

## 输出

- `collected_articles.json` - 收集的文章
- Notion 数据库中的新页面
