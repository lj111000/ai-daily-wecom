"""
LLM 简讯改写模块（GLM-4-Flash）
- 一次 API 调用把 N 篇文章标题改写成「编号 + 一句话简讯」格式
- 同时生成每日微语
- 失败时降级：返回原标题，不阻塞推送
"""

import json
import re
import logging

import requests

from config import GLM_API_KEY, GLM_BASE_URL, GLM_MODEL, GLM_TIMEOUT

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """你是中文 AI 资讯编辑，专门把 RSS 标题改写成早报简讯。

规则：
1. 每条简讯严格 15-25 字，一句话讲清「谁 + 干了什么 / 怎么样」
2. 不要营销腔，不要感叹号，不要"重磅""震撼""颠覆"这种词
3. 不要句号结尾
4. 保留关键数字（金额/比例/型号）
5. 专有名词保留原文（GPT/Claude/GLM/HBM 等）
6. 不要前缀编号，正文里也不要带"序号X"
7. 每条独立改写，绝不合并或省略任何一条
"""

USER_TEMPLATE = """请把下面 {n} 条 AI 资讯的标题改写成早报简讯。

原始标题列表（每行一条，格式：序号|标题|来源）：
{items}

输出格式（严格 JSON，不要 markdown 代码块，不要任何解释）：
{{
  "briefs": [
    "第一条改写后的简讯",
    "第二条改写后的简讯"
  ],
  "quote": "一句收尾的每日微语，关于 AI 趋势或技术人成长，15-25字，要具体有锋芒，不要鸡汤"
}}

严格要求：
- briefs 数组长度必须严格等于 {n}，逐条对应输入顺序，不能合并、不能跳过、不能省略
- 每条 15-25 字，超字数会被拒收
- quote 必须有观点、有锋芒，比如"真问题不在模型大小，在产品定义"；禁止出现"AI进化"、"拥抱未来"、"无限可能"这种空话
"""


def _build_user_prompt(items: list[dict]) -> str:
    lines = []
    for i, a in enumerate(items, 1):
        # 来源作为上下文，但简讯里不带
        lines.append(f"{i}|{a['title']}|{a['source_name']}")
    return USER_TEMPLATE.format(n=len(items), items="\n".join(lines))


def _call_glm(messages: list[dict]) -> dict | None:
    """调用 GLM，返回解析后的 JSON dict 或 None"""
    if not GLM_API_KEY:
        logger.warning("GLM_API_KEY 未配置，跳过 LLM 改写")
        return None

    url = f"{GLM_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {GLM_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GLM_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "response_format": {"type": "json_object"},
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=GLM_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        # 防御：模型偶尔会包 ```json ... ``` 壳
        content = re.sub(r"^```json\s*|\s*```$", "", content.strip(), flags=re.M)
        return json.loads(content)
    except requests.RequestException as e:
        logger.error(f"GLM 调用失败: {e}")
        return None
    except (KeyError, json.JSONDecodeError) as e:
        logger.error(f"GLM 返回解析失败: {e}")
        return None


def summarize_batch(items: list[dict]) -> tuple[list[str], str]:
    """
    批量改写。
    返回 (briefs, quote)。
    briefs 长度严格等于 items；失败时降级用原标题，quote 用兜底。
    """
    if not items:
        return [], ""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": _build_user_prompt(items)},
    ]
    result = _call_glm(messages)

    # 兜底 quote
    fallback_quote = "看清趋势，把能力打厚"

    if not result:
        # 完全失败，用原标题
        logger.warning("LLM 改写失败，降级使用原标题")
        return [a["title"] for a in items], fallback_quote

    briefs = result.get("briefs", [])
    quote = result.get("quote", "").strip() or fallback_quote

    # 长度对齐：缺的补原标题，多的截断
    if len(briefs) < len(items):
        logger.warning(f"LLM 返回 briefs 不足 ({len(briefs)}/{len(items)})，缺的用原标题")
        briefs = briefs + [items[i]["title"] for i in range(len(briefs), len(items))]
    elif len(briefs) > len(items):
        briefs = briefs[: len(items)]

    # 清洗：去掉可能出现的开头序号
    briefs = [re.sub(r"^\s*\d+[\.\、\)\s]+", "", b).strip() for b in briefs]

    return briefs, quote


if __name__ == "__main__":
    # 自测
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if not GLM_API_KEY:
        print("请先设置 GLM_API_KEY 环境变量")
        sys.exit(1)

    test_items = [
        {"title": "OpenAI 据报道正在讨论向美国政府出售 5% 股权以换取监管友好环境",
         "source_name": "量子位"},
        {"title": "Anthropic 发布 Claude Sonnet 5，编码能力对标 GPT-5 但价格腰斩",
         "source_name": "机器之心"},
        {"title": "国产 GLM-5.2 亮相：200K 上下文，推理成本仅为 GPT-4 的 1/10",
         "source_name": "雷锋网"},
    ]
    briefs, quote = summarize_batch(test_items)
    for i, b in enumerate(briefs, 1):
        print(f"{i}. {b}")
    print(f"\n【每日微语】{quote}")
