# Reddit Collector Skill

从 Reddit 子版块收集热门帖子，支持通过网页爬取和 RSS 订阅。

## 功能特性

- **多种收集方式**：支持网页爬取和 RSS 订阅
- **灵活的过滤选项**：按评分、评论数过滤
- **批量收集**：从多个子版块同时收集
- **无需 API Key**：使用网页爬取技术，无需申请 Reddit API
- **降级方案**：依赖未安装时自动使用模拟数据

## 快速开始

### 基本使用

```bash
# 运行演示脚本
cd .claude/skills/reddit-collector
python3 demo.py                    # 运行所有演示
python3 demo.py hot                # 收集热门帖子
python3 demo.py new                # 收集最新帖子
python3 demo.py batch              # 批量收集多个子版块
```

### Python API 使用

```python
from src.collector import RedditCollector

# 初始化收集器
collector = RedditCollector()

# 收集热门帖子
posts = collector.collect_hot_posts(
    subreddit="ArtificialIntelligence",
    limit=20,          # 收集数量
    min_score=50       # 最低评分
)

# 收集最新帖子
posts = collector.collect_new_posts(
    subreddit="Python",
    limit=20,
    min_score=10
)

# 通过 RSS 收集
posts = collector.collect_via_rss(
    subreddit="golang",
    feed_type="hot",   # hot, new, top
    limit=20
)
```

## 安装依赖（可选）

如果要使用真实的 Reddit 数据，需要安装以下依赖：

```bash
# 使用 pip
pip install httpx beautifulsoup4 feedparser

# 或使用系统包管理器
# Ubuntu/Debian
sudo apt-get install python3-pip
python3 -m pip install httpx beautifulsoup4 feedparser

# Fedora/RHEL
sudo dnf install python3-pip
python3 -m pip install httpx beautifulsoup4 feedparser
```

### 依赖说明

- `httpx`: HTTP 客户端，用于网页爬取
- `beautifulsoup4`: HTML 解析库
- `feedparser`: RSS 订阅解析

## 数据结构

每个帖子包含以下字段：

```json
{
  "title": "帖子标题",
  "link": "https://old.reddit.com/r/...",
  "author": "作者用户名",
  "score": 1500,                    // 评分（upvotes）
  "comments": 250,                  // 评论数
  "upvote_ratio": 0.85,             // 点赞比例
  "created_utc": 1705316400.0,      // 创建时间戳
  "created_date": "2024-01-15T10:30:00Z",
  "self_text": "帖子内容摘要",
  "url": "外部链接（如果有）",
  "subreddit": "ArtificialIntelligence",
  "is_self": true,                  // 是否为自贴（非链接）
  "domain": "reddit.com",
  "source_type": "reddit"
}
```

## 使用场景

### 1. 技术资讯收集

```python
# 收集 AI 相关技术资讯
collector = RedditCollector()

ai_sources = [
    "ArtificialIntelligence",
    "MachineLearning",
    "deeplearning",
    "LocalLLaMA"
]

for subreddit in ai_sources:
    posts = collector.collect_hot_posts(subreddit, limit=10)
    # 处理帖子...
```

### 2. 编程社区监控

```python
# 监控编程语言社区
programming_subreddits = [
    ("Python", "Python"),
    ("golang", "Golang"),
    ("rust", "Rust"),
    ("javascript", "JavaScript"),
]

for subreddit, category in programming_subreddits:
    posts = collector.collect_hot_posts(subreddit, limit=5)
    for post in posts:
        post['category'] = category
    # 保存或发送到其他工具
```

### 3. 批量收集和过滤

```python
# 批量收集并过滤高质量内容
collector = RedditCollector()

all_posts = []

# 收集多个子版块
subreddits = ["Programming", "ArtificialIntelligence", "DataScience"]
for sub in subreddits:
    posts = collector.collect_hot_posts(sub, limit=20, min_score=100)
    all_posts.extend(posts)

# 过滤高参与度帖子
high_engagement = [p for p in all_posts if p['comments'] > 50]

# 按评分排序
high_engagement.sort(key=lambda x: x['score'], reverse=True)
```

## 集成到工作流

Reddit Collector 可以作为技术文章收集流水线的一部分：

```
Reddit Collector → Content Extractor → AI Analyzer → Notion Publisher
     (收集帖子)        (提取内容)          (AI分析)        (发布到Notion)
```

### 示例：完整的文章收集流程

```python
from src.collector import RedditCollector
import json

# 1. 收集 Reddit 帖子
collector = RedditCollector()
posts = collector.collect_hot_posts("ArtificialIntelligence", limit=20)

# 2. 提取文章链接（过滤外部文章）
articles = [p for p in posts if not p['is_self'] and p['url']]

# 3. 调用 content-extractor 提取内容
# extracted = extract_content(article['url'] for article in articles)

# 4. 调用 ai-content-analyzer 分析
# analyzed = analyze_content(extracted)

# 5. 发布到 Notion
# publish_to_notion(analyzed)

# 保存结果
with open('reddit_posts.json', 'w') as f:
    json.dump(posts, f, indent=2, ensure_ascii=False)
```

## 配置选项

### 环境变量

```bash
# 可选：自定义 User Agent
export REDDIT_USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
```

### 收集参数

- `subreddit`: 子版块名称（不带 r/ 前缀）
- `limit`: 收集帖子数量（默认 20）
- `min_score`: 最低评分阈值（过滤低质量内容）
- `feed_type`: RSS 类型（hot, new, top）

## 支持的子版块示例

### AI/机器学习
- r/ArtificialIntelligence
- r/MachineLearning
- r/deeplearning
- r/LocalLLaMA
- r/ClaudeAI
- r/OpenAI

### 编程语言
- r/Python
- r/golang
- r/rust
- r/javascript
- r/Programming

### 数据科学
- r/DataScience
- r/datasets
- r/learnmachinelearning

## 注意事项

1. **请求频率**：避免过于频繁的请求，建议在批量收集时添加延迟
2. **使用 RSS**：对于稳定收集，推荐使用 RSS 模式
3. **模拟数据**：未安装依赖时会使用模拟数据，结构相同
4. **子版块限制**：某些子版块可能有访问限制
5. **数据时效性**：Reddit 数据实时变化，建议定期收集

## 故障排除

### 问题：ImportError 或缺少依赖

**解决方案**：安装所需依赖
```bash
pip install httpx beautifulsoup4 feedparser
```

### 问题：HTTP 429 错误（请求过多）

**解决方案**：
- 减少请求频率
- 使用 RSS 模式代替网页爬取
- 更换 User-Agent

### 问题：返回空数据

**可能原因**：
- 子版块名称错误
- 网络连接问题
- Reddit 访问限制

**解决方案**：
- 检查子版块名称拼写
- 尝试使用 RSS 模式
- 查看错误日志

## 输出示例

### 控制台输出

```
✓ Reddit web scraper initialized
  🌐 Fetching r/ArtificialIntelligence/hot...
    ✓ Found 25 posts, 20 meet score threshold
```

### JSON 输出

保存到 `output/reddit_posts.json`，格式见上文数据结构部分。

## 高级用法

### 自定义过滤逻辑

```python
posts = collector.collect_hot_posts("Python", limit=50)

# 只保留包含特定关键词的帖子
keyword_filtered = [
    p for p in posts
    if 'tutorial' in p['title'].lower() or 'guide' in p['title'].lower()
]

# 只保留链接帖（非自贴）
link_posts = [p for p in posts if not p['is_self'] and p['url']]

# 只保留高评分高评论的帖子
quality_posts = [
    p for p in posts
    if p['score'] > 100 and p['comments'] > 20
]
```

### 与其他技能集成

```bash
# 1. 收集 Reddit 帖子
python3 .claude/skills/reddit-collector/demo.py batch

# 2. 提取文章内容
# 使用 content-extractor 技能

# 3. AI 分析
# 使用 ai-content-analyzer 技能

# 4. 发布到 Notion
# 使用 notion-publisher 技能
```

## 许可和注意事项

- 遵守 Reddit 的服务条款和 robots.txt
- 尊重用户隐私和版权
- 不要用于商业目的的批量爬取
- 建议设置合理的请求间隔

## 相关技能

- `content-extractor`: 从 URL 提取完整文章内容
- `ai-content-analyzer`: 使用 AI 分析和评分内容
- `notion-publisher`: 发布内容到 Notion 数据库
- `tech-article-collector`: 完整的技术文章收集流水线

## 更新日志

- **v1.0**: 初始版本
  - 支持网页爬取和 RSS 收集
  - 基本的过滤和排序功能
  - 批量收集多个子版块
