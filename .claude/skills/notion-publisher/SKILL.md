---
name: notion-publisher
description: Publishes formatted articles to Notion databases with properties like title, link, author, score, category, and summary. Use this when you need to create Notion pages from articles or sync content to a Notion database.
allowed-tools: Bash,Read,Write,Grep
---

# Notion Publisher

将文章发布到 Notion 数据库，创建格式化的页面，包含属性和内容块。

## 使用场景

- 将分析后的文章发布到 Notion
- 创建结构化的 Notion 数据库条目
- 同步内容到 Notion 进行管理
- 将文章渲染为美观的 Notion 页面

## 工作目录

```
/home/say/work/github/cctools/.claude/skills/notion-publisher/
```

## 环境准备

在 `.env` 中配置：

```bash
# Notion Integration Token
notion_key=your_notion_integration_token

# Notion Database ID
NOTION_DATABASE_ID=your_database_id
```

### 获取 Notion API Key

1. 访问 https://www.notion.so/my-integrations
2. 点击 "New integration"
3. 填写名称，选择 capabilities（建议全选）
4. 复制 Internal Integration Token

### 获取 Database ID

1. 在 Notion 中打开数据库
2. 点击右上角 "..." → "Copy link"
3. Database ID 是链接中 `.../` 和 `?v=` 之间的 32 位字符

## 核心功能

### 1. 属性设置
- Title（标题）
- Link（原文链接）
- Author（作者）
- Score（AI 评分）
- Category（分类）
- Summary（AI 摘要）
- Rating（评级）
- Status（状态）
- Tags（标签）

### 2. 内容渲染
- 页面标题
- AI 摘要
- 关键要点列表
- 标签
- 原文链接
- 各种 Notion Block（heading、paragraph、bulleted_list_item、divider、callout 等）

### 3. 数据库操作
- 创建页面
- 查询数据库
- 更新属性

## 使用方法

```python
from publisher import NotionPublisher

# 初始化
publisher = NotionPublisher()

# 发布文章
article = {
    "title": "文章标题",
    "link": "https://example.com/article",
    "author": "作者名",
    "ai_score": 85,
    "ai_category": "AI",
    "ai_summary": "文章摘要...",
    "key_points": ["要点1", "要点2"],
    "tags": ["AI", "Tutorial"]
}

success, page_id = publisher.publish_article(article)

if success:
    print(f"Published! Page ID: {page_id}")
else:
    print(f"Failed: {page_id}")
```

## 输出示例

```json
{
    "success": true,
    "page_id": "16d83c1497bd580b7824de65c408b11f8",
    "url": "https://notion.so/16d83c1497bd580b7824de65c408b11f8"
}
```

## 数据库模板

推荐创建以下属性的数据库：

| 属性名 | 类型 | 说明 |
|--------|------|------|
| Title | Title | 文章标题 |
| Link | URL | 原文链接 |
| Author | Rich Text | 作者 |
| Score | Number | AI 评分 (0-100) |
| Category | Select | AI、机器学习、架构等 |
| Summary | Rich Text | AI 生成的摘要 |
| Rating | Select | ⭐⭐⭐⭐⭐ |
| Status | Status | Not started / In progress / Done |
| Tags | Multi-select | AI、LLM、教程等 |

## 集成到工作流

在 `tech-article-collector` 工作流中：

1. 收集文章（reddit-collector）
2. 提取内容（content-extractor）
3. AI 分析（ai-content-analyzer）
4. 发布到 Notion（notion-publisher）
