---
name: ai-content-analyzer
description: AI-powered content analyzer that scores, categorizes, and summarizes articles using MiniMax or OpenAI. Use this when you need to analyze content quality, generate summaries, or extract key points from articles.
allowed-tools: Bash,Read,Write,Grep
---

# AI Content Analyzer

使用 AI（MiniMax 或 OpenAI）对文章进行质量分析、评分、分类和摘要生成。

## 使用场景

- 需要对文章进行质量评分
- 需要生成文章摘要（中文）
- 需要提取文章关键要点
- 需要判断文章难度级别
- 需要给文章打标签

## 工作目录

```
/home/say/work/github/cctools/.claude/skills/ai-content-analyzer/
```

## 环境准备

配置以下环境变量之一：

```bash
# 方案1: MiniMax（推荐）
MINIMAX_API_KEY=your_minimax_api_key

# 方案2: OpenAI
OPENAI_API_KEY=your_openai_api_key
```

## 核心功能

### 1. 质量评分
- 多维度评分（相关性、深度、实用性、新颖性）
- 综合评分（0-100分）
- 评分理由说明

### 2. 内容摘要
- 智能摘要生成
- 支持中英文内容
- 摘要长度可配置

### 3. 关键要点提取
- 自动提取3-5个关键点
- 便于快速了解文章核心内容

### 4. 难度评估
- Beginner（入门）
- Intermediate（中级）
- Advanced（高级）

### 5. 自动分类
- AI
- Machine Learning
- Golang
- Developer Tools
- Architecture
- 其他技术分类

## 使用方法

```python
from analyzer import AIContentAnalyzer

# 初始化
analyzer = AIContentAnalyzer()

# 分析内容
result = analyzer.analyze_content(
    title="文章标题",
    content="文章内容...",
    analysis_type="comprehensive"  # 或 "quick"
)

# 获取结果
score = result['ai_score']           # 评分 (0-100)
summary = result['ai_summary']       # 摘要
category = result['ai_category']     # 分类
difficulty = result['difficulty']    # 难度
key_points = result['key_points']    # 关键点
tags = result['tags']                # 标签
```

## 输出示例

```json
{
    "ai_score": 85,
    "ai_summary": "这篇文章介绍了...",
    "ai_category": "AI",
    "difficulty": "Intermediate",
    "key_points": [
        "要点1",
        "要点2",
        "要点3"
    ],
    "tags": ["AI", "Tutorial", "Machine Learning"]
}
```

## 集成到工作流

在 `tech-article-collector` 工作流中：

1. 收集文章（reddit-collector）
2. 提取内容（content-extractor）
3. AI 分析（ai-content-analyzer）
4. 发布到 Notion（notion-publisher）
