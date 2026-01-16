# Reddit Collector - Quick Start Guide

## 快速开始

### 基本用法

```bash
cd /home/say/work/github/cctools/.claude/skills/reddit-collector

# 运行所有演示
python3 demo.py

# 运行特定演示
python3 demo.py hot      # 热门帖子
python3 demo.py new      # 最新帖子
python3 demo.py rss      # RSS 订阅
python3 demo.py batch    # 批量收集
python3 demo.py filter   # 过滤和排序
```

### 实用示例

```bash
# 运行实用示例
python3 examples.py              # 运行所有示例
python3 examples.py 1            # 收集科技新闻
python3 examples.py 2            # 查找高质量讨论
python3 examples.py 3            # 提取外部文章链接
python3 examples.py 4            # 监控热门话题
python3 examples.py 5            # 创建每日摘要
```

## Python API

### 简单示例

```python
from src.collector import RedditCollector

collector = RedditCollector()

# 收集热门帖子
posts = collector.collect_hot_posts("Python", limit=10, min_score=50)

# 查看结果
for post in posts:
    print(f"{post['title']} - Score: {post['score']}")
```

### 批量收集

```python
collector = RedditCollector()

subreddits = ["Python", "golang", "rust"]
all_posts = []

for sub in subreddits:
    posts = collector.collect_hot_posts(sub, limit=5)
    all_posts.extend(posts)

print(f"Collected {len(all_posts)} posts")
```

### 过滤和排序

```python
posts = collector.collect_hot_posts("ArtificialIntelligence", limit=30)

# 高评分帖子
top_posts = [p for p in posts if p['score'] > 200]

# 高参与度帖子
engaging = [p for p in posts if p['comments'] > 50]

# 排序
top_posts.sort(key=lambda x: x['score'], reverse=True)
```

## 输出文件

收集的帖子保存在 `output/` 目录：

- `reddit_posts.json` - 批量收集的结果
- `tech_news.json` - 科技新闻聚合
- `articles_to_extract.json` - 待提取的外部文章
- `daily_digest.json` - 每日摘要

## 数据结构

```json
{
  "title": "帖子标题",
  "link": "https://old.reddit.com/r/...",
  "author": "用户名",
  "score": 1500,
  "comments": 250,
  "subreddit": "ArtificialIntelligence",
  "created_date": "2024-01-15T10:30:00Z"
}
```

## 集成工作流

### 完整流程

```bash
# 1. 收集 Reddit 帖子
python3 .claude/skills/reddit-collector/examples.py 3

# 2. 提取文章内容
# (使用 content-extractor 技能)

# 3. AI 分析
# (使用 ai-content-analyzer 技能)

# 4. 发布到 Notion
# (使用 notion-publisher 技能)
```

## 常用子版块

### AI/机器学习
- `ArtificialIntelligence` - AI
- `MachineLearning` - ML
- `deeplearning` - 深度学习
- `LocalLLaMA` - 本地 LLM

### 编程
- `Python` - Python
- `golang` - Go
- `rust` - Rust
- `programming` - 编程

### 科技
- `technology` - 科技
- `Programming` - 编程
- `DataScience` - 数据科学

## 注意事项

1. **依赖**：需要安装 `httpx beautifulsoup4 feedparser` 才能获取真实数据
2. **限制**：避免过于频繁的请求
3. **RSS**：推荐使用 RSS 模式，更稳定
4. **模拟数据**：未安装依赖时使用模拟数据

## 故障排除

### 缺少依赖

```bash
pip install httpx beautifulsoup4 feedparser
```

### 请求过多

```python
import time
for sub in subreddits:
    posts = collector.collect_hot_posts(sub)
    time.sleep(1)  # 添加延迟
```

### 空结果

- 检查子版块名称拼写
- 降低 `min_score` 阈值
- 尝试其他排序方式

## 更多信息

查看完整文档：`README.md`
