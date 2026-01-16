---
name: reddit-collector
description: Collects hot posts from Reddit subreddits via web scraping and RSS feeds. Use this when you need to gather trending posts from subreddits like r/ArtificialIntelligence, r Programming, r/MachineLearning, etc.
allowed-tools: Bash,Read,Write,Grep
---

# Reddit Collector

从 Reddit 子版块收集热门帖子，支持通过网页爬取和 RSS 订阅。

## 使用场景

- 收集 Reddit 子版块的热门帖子
- 监控特定话题的讨论
- 获取技术社区的最新动态
- 通过 RSS 订阅子版块更新

## 工作目录

```
/home/say/work/github/cctools/.claude/skills/reddit-collector/
```

## 环境准备

无需 API key，使用网页爬取技术：

```bash
# 可选：配置 User Agent
REDDIT_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
```

## 支持的数据源

### Reddit 子版块
- r/ArtificialIntelligence
- r Programming
- r/MachineLearning
- r/deeplearning
- r/LocalLLaMA
- r/ClaudeAI
- r/OpenAI
- r/golang
- r/Python
- 任意其他子版块

### 排序方式
- Hot（热门）
- New（最新）
- Top（最热）

### 数据来源
- RSS 订阅（推荐，稳定）
- 网页爬取（备选）

## 核心功能

### 1. 帖子收集
- 标题、链接
- 作者
- 评分（upvotes）
- 评论数
- 子版块信息

### 2. 数据过滤
- 按评分过滤
- 按评论数过滤
- 排除自荐帖（self-post）
- 排除链接帖

### 3. 批量收集
- 支持多个子版块
- 可配置数量限制
- 增量更新

## 使用方法

```python
from collector import RedditCollector

# 初始化
collector = RedditCollector()

# 收集单个子版块
posts = collector.collect_subreddit(
    subreddit="ArtificialIntelligence",
    sort="hot",
    limit=20,
    min_score=50
)

# 收集多个子版块
all_posts = collector.collect_multiple([
    {"subreddit": "ArtificialIntelligence", "category": "AI"},
    {"subreddit": "Programming", "category": "Programming"},
    {"subreddit": "golang", "category": "Golang"},
])
```

## 输出示例

```json
[
    {
        "title": "Post title",
        "link": "https://old.reddit.com/r/ArtificialIntelligence/comments/xxx",
        "author": "username",
        "score": 1500,
        "comments": 250,
        "subreddit": "ArtificialIntelligence",
        "category": "AI",
        "source": "Reddit r/ArtificialIntelligence",
        "source_type": "reddit",
        "published_at": "2024-01-15T10:30:00Z"
    }
]
```

## 配置示例

在 `tech-article-collector.yaml` 中：

```yaml
sources:
  reddit_subreddits:
    - name: "AI Hot"
      subreddit: "ArtificialIntelligence"
      category: "AI"
      post_limit: 20
      min_score: 100
      sort: "hot"

    - name: "Golang"
      subreddit: "golang"
      category: "Golang"
      post_limit: 15
      min_score: 50

    - name: "ML"
      subreddit: "MachineLearning"
      category: "Machine Learning"
      post_limit: 20
      min_score: 100
```

## RSS 备用方案

如果网页爬取被屏蔽，可以使用 RSS：

```bash
# 访问子版块 RSS
https://old.reddit.com/r/{subreddit}/hot.rss
https://old.reddit.com/r/{subreddit}/new.rss
https://old.reddit.com/r/{subreddit}/top.rss
```

## 集成到工作流

在 `tech-article-collector` 工作流中：

1. 收集文章（reddit-collector）
2. 提取内容（content-extractor）
3. AI 分析（ai-content-analyzer）
4. 发布到 Notion（notion-publisher）

## 注意事项

- Reddit 可能会封禁大量请求，建议设置延迟（0.5-1秒）
- 优先使用 RSS 订阅，更稳定
- 设置合理的 `min_score` 过滤低质量内容
- 尊重 Reddit 的 robots.txt 和服务条款
