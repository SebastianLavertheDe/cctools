"""
智谱 AI (Zhipu AI / GLM) 客户端
"""

import os
import json
import time
from typing import Dict, List, Optional, Tuple
from openai import OpenAI
import re


def extract_json_from_response(response: str) -> str:
    """
    从 AI 响应中提取 JSON 字符串，处理各种 markdown 代码块包装情况
    包括处理被截断的响应（没有结尾的 ```）
    """
    if not response:
        return response

    text = response.strip()

    # 尝试用正则提取 ```json ... ``` 或 ``` ... ``` 中的内容（完整的代码块）
    patterns = [
        r'```json\s*([\s\S]*?)\s*```',  # ```json ... ```
        r'```\s*([\s\S]*?)\s*```',       # ``` ... ```
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()

    # 如果没有匹配到完整的代码块，可能是被截断了
    # 尝试提取 ```json 或 ``` 之后的所有内容
    if '```json' in text:
        # 找到 ```json 的位置，提取之后的内容
        idx = text.find('```json')
        text = text[idx + 7:].strip()
    elif text.startswith('```'):
        text = text[3:].strip()

    # 去除可能存在的结尾 ```
    if text.endswith('```'):
        text = text[:-3].strip()

    # 尝试找到 JSON 对象的开始（第一个 {）
    if '{' in text:
        idx = text.find('{')
        text = text[idx:]

    return text.strip()


class ZhipuClient:
    """智谱 AI (GLM) 客户端"""

    def __init__(self):
        self.api_key = os.getenv('ZHIPU_API_KEY')
        # Use ZHIPU_MODEL if set, otherwise use glm-4.7
        self.model = os.getenv('ZHIPU_MODEL', 'glm-4.7')

        if not self.api_key or not self.api_key.strip():
            raise ValueError("ZHIPU_API_KEY 未设置或为空")

        # 初始化OpenAI客户端，指向智谱AI API
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://open.bigmodel.cn/api/paas/v4"
        )

    def analyze_content(self, title: str, content: str) -> Dict:
        """
        分析文章内容

        Args:
            title: 文章标题
            content: 文章内容

        Returns:
            包含 summary, score 等的字典
        """
        if not content or len(content.strip()) < 10:
            return {
                'summary': "内容过短，无需分析",
                'score': 0,
                'ai_processed': False
            }

        full_text = f"# {title}\n\n{content}"

        analysis_prompt = """你是一名严谨的技术/行业内容编辑 + 选题评审员（面向程序员内容与 AI/Agent 方向）。请对我提供的**单篇文章全文**进行总结与评分，并且**只输出一个合法 JSON**，只包含两个字段：`summary` 与 `score`。

## 我的目标读者

* Go 工程师、后端工程师、想入门/跟进 AI 与 AI Agent 的程序员
* AI 技术爱好者：关注 LLM 应用、RAG、Agent 工作流、评测与工程化落地
* Prompt 玩法人群：喜欢提示词技巧、工作流提示词、结构化输出、提示词模板与可复用套路
* 共同偏好：落地实践、工程方案、工具链、踩坑、可复用框架、可讲清楚的案例

## 我的偏好选题（优先加权）

1. AI / AI Agent 工程化落地：记忆、工具调用、工作流编排、多智能体协作、评估与观测、成本/延迟优化
2. Go + LLM 实战：RAG 服务、LLM 网关、异步队列/任务执行、缓存、并发与限流、可观测性（Tracing/Logging/Metrics）、线上稳定性
3. Prompt 玩儿法与可复用模板：结构化输出、链式/分步提示、工具调用提示、角色/约束/评分提示、对比与迭代方法、可直接套用的 prompt 模板
4. 框架/工具对比与选型：LangGraph / AutoGen / CrewAI / DSPy / LlamaIndex 等（能力、复杂度、生态、可维护性、成本）
5. 适合公众号/小红书的内容形态：踩坑清单、最佳实践、对比评测、从 0-1 教程、模板/脚手架、案例复盘

> 评分时请"优先加权"这些偏好：若文章与偏好高度匹配，在**新颖性/实用性/信息密度**的打分理由中体现；若明显不匹配，在"文章的意义/价值"与"判定"中明确说明"不适合我的选题库"的原因（必须基于原文）。

---

# 总规则

* **只基于原文**输出，不要加入外部背景或推测；不确定就写"文中未提及/无法确定"。
* 不要杜撰数据、机构、时间、人物、引用。
* "400-500字摘要"建议在 **400-500字** 范围内（尽量全面覆盖文章核心内容）。
* 输出必须是**严格 JSON**：

  * 不要用 Markdown 代码块包裹
  * 不要输出任何额外解释文字
  * 只能有 `summary`、`score` 两个字段
* `score` 必须是**数字**（0–100）。

---

# summary 字段要求（中文Markdown 字符串，适合 Notion）

`summary` 的值是一个 **Markdown 格式字符串**，按下面结构输出（标题与小标题固定）：

# [中文翻译的标题]

（请将文章标题翻译成中文，保持简洁准确）

## 核心结论

（1句：说明文章讨论什么 + 作者核心结论；必须基于原文）

## 400-500字摘要

（400-500字，全面覆盖：背景/问题→核心论点/技术细节→实现方法/架构→证据/数据→结论/实践建议；确保读者无需阅读原文也能理解文章全貌）

## 要点（3–5条）

* （优先包含：时间、人物/机构、因果链、数据/对比、关键定义）
* …
* …

## 证据与数据

* （把原文出现的数字、研究、案例或引用逐条列出）
* …
  （若没有：无明确数据）

## 文章的意义/价值

（说明它对"我的目标读者/偏好选题"有什么启发或可行动建议；必须能从文中推导；否则写：文中未明确说明）

## 评分依据

* 信息密度（0-20）：x（1句理由，结合目标读者/偏好选题）
* 证据质量（0-20）：x（1句理由；无来源/无数据要扣分）
* 逻辑与结构（0-15）：x（1句理由）
* 新颖性/洞察（0-15）：x（1句理由；与偏好匹配可加分）
* 实用性/可行动性（0-20）：x（1句理由；能否落地到工程/Prompt/Agent实践）
* 表达清晰度（0-10）：x（1句理由）

**总分 = 上述分项之和（0-100）**

## 判定

* （基于上述评分，给出最终建议：✅保留 或 ❌跳过，以及1句理由）

---

# 现在请分析以下文章

"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": analysis_prompt + "\n\n" + full_text[:20000]}
                ],
                temperature=0.3,
                max_tokens=4000
            )

            ai_response = response.choices[0].message.content

            # Parse JSON response
            summary_text = None
            score = None
            translated_title = None

            if ai_response:
                # Use helper function to extract JSON from markdown code blocks
                response_to_parse = extract_json_from_response(ai_response)

                try:
                    parsed = json.loads(response_to_parse)
                    summary_text = parsed.get('summary', '')
                    score = parsed.get('score')
                except json.JSONDecodeError as e:
                    # Fallback: treat as plain text
                    summary_text = ai_response
                    score = 50

            # Extract translated title from summary
            if summary_text:
                lines = summary_text.split('\n')
                for line in lines:
                    if line.startswith('# '):
                        translated_title = line[1:].strip()
                        break
                    elif line.startswith('## '):
                        # h2 heading - stop here, we passed the title
                        break

            if translated_title:
                translated_title = translated_title.strip('*').strip()

            result = {
                'translated_title': translated_title,
                'summary': summary_text or "总结生成失败",
                'score': score if score is not None else 50,
                'category': 'Other',
                'confidence': 0.0,
                'ai_processed': True,
                'timestamp': time.time()
            }

            return result

        except Exception as e:
            print(f"  Zhipu AI analysis failed: {e}")
            return {
                'summary': f"AI 分析失败: {str(e)}",
                'score': 50,
                'ai_processed': False,
                'timestamp': time.time()
            }

    def classify_text(self, text: str) -> Tuple[str, float]:
        """对文本进行分类（简单实现）"""
        categories = [
            "System Design", "Distributed Systems", "Database", "Network",
            "Architecture", "Algorithms", "Backend", "Frontend", "DevOps",
            "Machine Learning", "AI", "Golang", "Other"
        ]
        return ("Other", 0.0)
