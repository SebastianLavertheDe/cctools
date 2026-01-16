---
name: content-extractor
description: Extracts full article content from web URLs using trafilatura or BeautifulSoup. Use this when you need to parse article text, author, publish date, images, and metadata from web pages.
allowed-tools: Bash,Read,Write,Grep
---

# Content Extractor

从网页 URL 中提取完整的文章内容，包括标题、作者、发布日期、正文、图片等。

## 使用场景

- 需要从 URL 提取文章正文
- 需要获取文章的作者和发布日期
- 需要提取文章中的图片链接
- 需要计算文章字数和阅读时间
- 需要提取文章中的外部链接

## 工作目录

```
/home/say/work/github/cctools/.claude/skills/content-extractor/
```

## 环境准备

### 可选依赖

```bash
# 主要提取库（推荐）
pip install trafilatura

# 备选方案
pip install beautifulsoup4

# 高级提取（需要 API key）
pip install firecrawl
export FIRECRAWL_API_KEY=your_api_key
```

## 核心功能

### 1. 智能正文提取
- 使用 trafilatura 进行结构化提取
- 降级到 BeautifulSoup 解析
- 去除广告、导航等无关内容

### 2. 元数据提取
- 标题（title）
- 作者（author）
- 发布日期（publish_date）
- 网站名称（site_name）

### 3. 内容统计
- 字数统计（word_count）
- 预计阅读时间（reading_time）
- 链接数量

### 4. 资源提取
- 文章配图（images）
- 外部链接（links）

## 使用方法

```python
from extractor import ContentExtractor

# 初始化
extractor = ContentExtractor()

# 提取文章
result = extractor.extract_article("https://example.com/article")

# 获取结果
if result['success']:
    title = result['title']
    content = result['content']
    author = result['author']
    date = result['publish_date']
    images = result['images']
    word_count = result['word_count']
    reading_time = result['reading_time']
else:
    error = result['error']
```

## 输出示例

```json
{
    "success": true,
    "url": "https://example.com/article",
    "title": "文章标题",
    "content": "文章正文内容...",
    "author": "作者名",
    "publish_date": "2024-01-15",
    "images": [
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg"
    ],
    "links": [
        "https://example.com/link1",
        "https://example.com/link2"
    ],
    "word_count": 2500,
    "reading_time": 10,
    "extraction_method": "trafilatura"
}
```

## 集成到工作流

在 `tech-article-collector` 工作流中：

1. 收集文章（reddit-collector）
2. 提取内容（content-extractor）
3. AI 分析（ai-content-analyzer）
4. 发布到 Notion（notion-publisher）
