"""
企微消息格式化
- 企微 markdown 语法限制很多，注意：
  - 不支持表格、图片直接嵌入（图片要发图消息，markdown 里只能放链接）
  - 字数上限 ~4096（实际单条 2048 比较稳）
  - 链接格式：[文字](url)
  - 引用：> 文字
  - 加粗：**文字**
  - 字体颜色：只能用 <font color="info|comment|warning">文字</font>
"""

import logging
from datetime import datetime, timedelta, timezone

from config import SCHEDULES, CATEGORY_META

logger = logging.getLogger(__name__)
CST = timezone(timedelta(hours=8))


def _category_header(cat: str, items: list[dict]) -> str:
    if not items:
        return ""
    meta = CATEGORY_META[cat]
    return f"\n\n**{meta['emoji']} {meta['label']}** ({len(items)} 条)\n"


def _render_article(idx: int, a: dict, cat: str) -> str:
    meta = CATEGORY_META[cat]
    color = meta["color"]
    parts = []

    # 序号 + 标题（链接）
    parts.append(f"\n<font color=\"{color}\">{idx}.</font> [{a['title']}]({a['link']})")

    # 摘要（若有）
    if a.get("summary"):
        parts.append(f"\n> {a['summary']}")

    # 来源标签
    parts.append(f"\n📍 {a['source_name']}")

    return "".join(parts)


def format_message(selected: dict[str, list[dict]], schedule_key: str) -> str:
    """把选定内容渲染成企微 markdown 字符串"""
    schedule = SCHEDULES[schedule_key]
    now = datetime.now(CST).strftime("%Y-%m-%d %A")

    lines = [
        f"# {schedule['title']}",
        f"\n> {now} · {schedule['subtitle']}",
    ]

    for cat in schedule["counts"]:
        items = selected.get(cat, [])
        if not items:
            continue
        lines.append(_category_header(cat, items))
        for i, a in enumerate(items, 1):
            lines.append(_render_article(i, a, cat))

    # 页脚
    lines.append(
        "\n\n---"
        "\n<font color=\"comment\">由 ai-daily-wecom 自动推送 · 数据源见 README</font>"
    )

    msg = "".join(lines)

    # 长度保护：超过 2000 字符，砍掉摘要
    if len(msg) > 2000:
        logger.warning(f"消息过长({len(msg)})，降级精简版")
        msg = _format_minimal(selected, schedule_key, now)

    return msg


def _format_minimal(selected: dict[str, list[dict]], schedule_key: str, now: str) -> str:
    """精简版：只保留标题+链接+来源"""
    schedule = SCHEDULES[schedule_key]
    lines = [f"# {schedule['title']}", f"\n> {now}"]
    for cat in schedule["counts"]:
        items = selected.get(cat, [])
        if not items:
            continue
        meta = CATEGORY_META[cat]
        lines.append(f"\n\n**{meta['emoji']} {meta['label']}**")
        for i, a in enumerate(items, 1):
            lines.append(
                f"\n<font color=\"{meta['color']}\">{i}.</font> "
                f"[{a['title']}]({a['link']})"
            )
    lines.append("\n\n---\n<font color=\"comment\">ai-daily-wecom</font>")
    return "".join(lines)


if __name__ == "__main__":
    demo = {
        "open_source": [
            {"title": "vllm/vllm", "link": "https://github.com/vllm-project/vllm",
             "summary": "高吞吐量 LLM 推理引擎，本周新增 PagedAttention 优化",
             "source_name": "GitHub Trending", "category": "open_source"},
            {"title": "openai/whisper", "link": "https://github.com/openai/whisper",
             "summary": "语音识别模型 v3 发布",
             "source_name": "GitHub Trending", "category": "open_source"},
        ],
        "tutorial": [
            {"title": "Building RAG from scratch",
             "link": "https://huggingface.co/blog/rag",
             "summary": "HuggingFace 出品的 RAG 实战教程",
             "source_name": "HuggingFace Blog", "category": "tutorial"},
        ],
    }
    print(format_message(demo, "morning"))
