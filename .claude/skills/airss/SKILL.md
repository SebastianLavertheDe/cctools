---
name: airss
description: 智能社交媒体 RSS 监控工具，抓取 Twitter/微博等平台的 RSS 内容，调用 DeepSeek AI 生成总结与分类，并自动推送到 Notion 数据库。使用场景：需要监控社交媒体更新、自动聚合内容、或将信息推送到 Notion 进行管理时。
allowed-tools: Bash,Write
---

# AIRSS - 智能社交媒体 RSS 监控

RSS 监控工具，从多个社交媒体平台获取内容并自动推送到 Notion 数据库。

## 何时使用此 Skill

当用户需要：
- 监控 Twitter/X、微博等社交媒体的更新
- 将 RSS 内容自动推送到 Notion 数据库
- 使用 AI 对内容进行总结和分类
- 追踪关注的内容创作者动态

## 工作目录

```
/home/say/tools/.claude/skills/airss/
```

## 环境准备

### 1. 安装依赖

```bash
cd /home/say/tools/.claude/skills/airss
uv sync
```

### 2. 配置环境变量

在项目根目录创建 `.env` 文件：

```bash
DEEPSEEK_API_KEY=你的_deepseek_api_key
notion_key=你的_notion_integration_token
NOTION_DATABASE_ID=你的_notion_数据库_id
# 可选：AI_MODEL=deepseek-chat
```

### 3. 配置监控用户

编辑 `config.yaml` 文件配置要监控的用户：

```yaml
platforms:
  twitter:
    names:
      - id: "GitHub_Daily"
        name: "GitHub每日精选推文"
      - id: "用户ID"
        name: "显示名称"
    rss_url:
      - "https://rsshub.pseudoyu.com/twitter/user/{username}"
      - "https://rsshub.pseudoyu.com/x/user/{username}"
  
  weibo:
    names:
      - id: "微博用户ID"
        name: "微博用户名称"
    rss_url:
      - "https://rsshub.app/weibo/user/{username}"
```

## 运行命令

### 基本运行

```bash
cd /home/say/tools/.claude/skills/airss
uv run --env-file .env python main.py
```

### 清除缓存后重新运行

```bash
cd /home/say/tools/.claude/skills/airss
echo '{}' > feed_cache.json
uv run --env-file .env python main.py
```

## 功能说明

### 支持的平台

- **Twitter/X**: 获取用户推文内容
- **微博**: 获取微博用户动态
- 可扩展添加新平台

### 核心功能

1. **智能 RSS 获取**
   - 多 RSSHub 实例自动切换
   - 60 秒超时设置
   - 自动重试机制

2. **Notion 集成**
   - 自动创建/推送到数据库
   - 结构化存储（标题、链接、作者、时间、摘要）
   - 智能去重

3. **缓存管理**
   - 本地缓存避免重复处理
   - 30 天自动清理
   - 增量更新

4. **AI 总结**（可选）
   - 使用 DeepSeek 生成内容总结
   - 自动分类

## 文件结构

```
airss/
├── main.py              # 入口文件
├── config.yaml          # 平台与用户配置
├── feed_cache.json      # 去重缓存
├── notion_config.json   # Notion 数据库配置
├── pyproject.toml       # 项目配置
├── SKILL.md             # 本文件
└── src/                 # 业务代码
    ├── ai/              # AI 总结模块
    ├── core/            # 核心监控逻辑
    ├── managers/        # 配置/缓存/RSS 管理
    ├── notion/          # Notion 集成
    ├── parsers/         # 内容解析器
    └── utils/           # 工具函数
```

## 代码修改指南

### 监控特定用户

修改 `main.py` 中的调用：

```python
# 监控特定用户
monitor.monitor_specific_user("用户ID")

# 监控所有配置的用户
monitor.monitor_all_users()
```

### 添加新用户

```python
# 动态添加用户
monitor.add_user("elonmusk", "Elon Musk", "twitter")
monitor.add_user("5722964389", "某微博用户", "weibo")
```

### 添加新平台

在 `config.yaml` 中添加：

```yaml
platforms:
  新平台:
    names:
      - id: "用户ID"
        name: "显示名称"
    rss_url:
      - "RSS模板URL，{username}会被替换"
```

## Notion 设置

### 1. 创建 Notion 集成

1. 访问 [Notion Developers](https://www.notion.so/my-integrations)
2. 创建新集成，复制 Token

### 2. 配置页面权限

1. 创建 Notion 页面
2. 邀请集成到该页面
3. 复制页面 ID 到 `.env`

## 定时运行

### 使用 cron

```bash
# 每小时运行
0 * * * * cd /home/say/tools/.claude/skills/airss && uv run --env-file .env python main.py

# 每天早上 9 点运行
0 9 * * * cd /home/say/tools/.claude/skills/airss && uv run --env-file .env python main.py
```

## 错误处理

- **网络问题**: 自动切换 RSSHub 实例
- **Notion API 错误**: 检查 Token 和权限
- **配置错误**: 验证 YAML 格式

## 注意事项

- `.env` 文件包含敏感信息，不要提交到版本控制
- Notion API 有速率限制，避免频繁调用
- RSSHub 实例可能不稳定，配置多个备用源

