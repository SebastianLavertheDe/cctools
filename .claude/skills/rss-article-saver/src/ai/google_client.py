"""
Google Gemini AI 客户端
负责与 Google Gemini API 进行交互，实现文本总结和分类功能
"""

import os
import json
import time
from typing import Dict, List, Optional, Tuple
import google.generativeai as genai
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


class GeminiClient:
    """Google Gemini AI 客户端"""

    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.model_name = os.getenv('AI_MODEL', 'gemini-2.0-flash')

        if not self.api_key or not self.api_key.strip():
            raise ValueError("GEMINI_API_KEY 未设置或为空")

        # 初始化 Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

    def _make_request(self, prompt: str, max_tokens: int = 1000, max_retries: int = 3) -> Optional[str]:
        """
        发起API请求，带重试逻辑

        Args:
            prompt: 完整的提示词
            max_tokens: 最大token数
            max_retries: 最大重试次数

        Returns:
            API响应内容，失败时返回None
        """
        import time as time_module
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=max_tokens,
                        temperature=0.3,
                    )
                )

                return response.text.strip()

            except Exception as e:
                error_str = str(e)
                # Check if it's a rate limit error (429)
                if '429' in error_str or 'quota' in error_str.lower():
                    wait_time = (attempt + 1) * 30  # 30s, 60s, 90s
                    print(f"  Rate limit hit, waiting {wait_time}s before retry ({attempt + 1}/{max_retries})...")
                    time_module.sleep(wait_time)
                    continue
                else:
                    print(f"Gemini API 请求失败: {e}")
                    return None
        
        print(f"Gemini API 请求失败: 重试 {max_retries} 次后仍然失败")
        return None

    def summarize_text(self, text: str, max_length: int = 200) -> Optional[str]:
        """
        文本深度分析（使用详细的分析框架）

        Args:
            text: 要分析的文本
            max_length: 最大长度（此处忽略，使用详细分析）

        Returns:
            分析结果，失败时返回None
        """
        if not text or len(text.strip()) < 10:
            return "内容过短，无需分析"

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

# summary 字段要求（Markdown 字符串，适合 Notion）

`summary` 的值是一个 **Markdown 格式字符串**，按下面结构输出（标题与小标题固定）：

# [文章标题]

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
* 风险分（0-10，单独，不计入score）：x（标题党/带货/夸大/偷换概念/无来源等，列1-2点）
* 判定：✅保留/⚠️可选/❌淘汰（1-2句原因；如不匹配偏好要说明）

---

# score 字段（数字）

* `score` = 前六项加总（满分100），**不要**把风险分计入 score。
* 判定规则（写在 summary 里即可）：

  * ✅保留：score ≥ 80 且 风险 ≤ 3
  * ⚠️可选：score 60-79 或 风险 4-6
  * ❌淘汰：score < 60 或 风险 ≥ 7

---

# JSON 输出要求（必须遵守）

* 必须返回形如：`{"summary":"...markdown...","score":82}`
* `summary` 内部换行必须用 `\n` 表示，确保 JSON 合法。
* `summary` 中如出现双引号 `"`，必须用 `\"` 转义。

请分析以下文章：

""" + text

        # Increase max_tokens for detailed analysis
        return self._make_request(analysis_prompt, max_tokens=4000)

    def classify_text(self, text: str) -> Optional[Tuple[str, float]]:
        """
        文本分类

        Args:
            text: 要分类的文本

        Returns:
            (分类标签, 置信度)，失败时返回None
        """
        categories = [
            "System Design", "Distributed Systems", "Database", "Network",
            "Architecture", "Algorithms", "Backend", "Frontend",
            "DevOps", "Machine Learning", "AI", "Golang", "Other"
        ]

        prompt = f"""你是一个专业的文本分类专家。请对用户提供的文本进行分类。

可选分类：{', '.join(categories)}

要求：
1. 从上述分类中选择最合适的一个
2. 返回JSON格式：{{"category": "分类名称", "confidence": 置信度(0-1的小数)}}
3. 置信度表示分类的确信程度
4. 如果不确定，选择"Other"类别

请对以下内容进行分类：

{text}"""

        result = self._make_request(prompt, max_tokens=100)
        if not result:
            return None

        try:
            # Use helper function to extract JSON from markdown code blocks
            response_to_parse = extract_json_from_response(result)

            parsed = json.loads(response_to_parse)
            category = parsed.get('category', 'Other')
            confidence = float(parsed.get('confidence', 0.5))

            if category not in categories:
                category = 'Other'
                confidence = 0.3

            return category, confidence

        except (json.JSONDecodeError, ValueError, TypeError):
            for cat in categories:
                if cat in result:
                    return cat, 0.6
            return 'Other', 0.3

    def analyze_content(self, title: str, content: str) -> Dict:
        """
        综合内容分析（总结+分类+标题翻译+评分）

        Args:
            title: 文章标题
            content: 文章内容

        Returns:
            包含翻译标题、总结、评分和分类结果的字典
        """
        full_text = f"{title}\n\n{content}" if title else content

        ai_response = self.summarize_text(full_text)
        classification = self.classify_text(full_text)

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
                # Print diagnostic info for debugging
                print(f"  JSON解析失败: {e}")
                print(f"  响应前100字符: {response_to_parse[:100] if response_to_parse else 'None'}...")
                # Fallback: treat as plain text
                summary_text = ai_response
        else:
            print(f"  AI未返回响应")

        # Extract title from summary (first line should be "# [title]")
        if summary_text:
            lines = summary_text.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('# '):
                    # Markdown h1 heading
                    translated_title = line[1:].strip()
                    break
                elif line.startswith('## '):
                    # h2 heading - stop here, we passed the title
                    break

        # Clean up markdown symbols from title
        if translated_title:
            translated_title = translated_title.strip('*').strip()

        result = {
            'translated_title': translated_title,
            'summary': summary_text or "总结生成失败",
            'score': score,
            'category': 'Other',
            'confidence': 0.0,
            'ai_processed': True,
            'timestamp': time.time()
        }

        if classification:
            result['category'] = classification[0]
            result['confidence'] = classification[1]

        return result
