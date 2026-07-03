"""
企微消息格式化
- 企微 markdown 限制：不支持图片直接嵌入、单条 ~2048 字符较稳
- 字体颜色：info(绿)/comment(灰)/warning(橙)
"""

import logging
from datetime import datetime, timedelta, timezone

from config import PUSH_TITLE, PUSH_SUBTITLE, SOURCE_META, MAX_SUMMARY_LEN

logger = logging.getLogger(__name__)
CST = timezone(timedelta(hours=8))


def _render_item(idx: int, a: dict) -> str:
    emoji = SOURCE_META.get(a.get("category", ""), {}).get("emoji", "•")
    parts = [
        f"\n\n<font color=\"info\">{idx}.</font> {emoji} [{a['title']}]({a['link']})",
    ]
    if a.get("summary"):
        parts.append(f"\n> {a['summary']}")
    parts.append(f"\n📍 {a['source_name']}")
    return "".join(parts)


def format_message(items: list[dict]) -> str:
    now = datetime.now(CST).strftime("%Y-%m-%d %A")

    lines = [
        f"# {PUSH_TITLE}",
        f"\n> {now} · {PUSH_SUBTITLE}",
    ]
    for i, a in enumerate(items, 1):
        lines.append(_render_item(i, a))

    lines.append(
        "\n\n---"
        "\n<font color=\"comment\">由 ai-daily-wecom 自动聚合 · 数据源见 README</font>"
    )

    msg = "".join(lines)

    # 长度保护：超 2000 字符降级精简版（去摘要）
    if len(msg) > 2000:
        logger.warning(f"消息过长({len(msg)})，降级精简版")
        msg = _format_minimal(items, now)
    return msg


def _format_minimal(items: list[dict], now: str) -> str:
    lines = [f"# {PUSH_TITLE}", f"\n> {now}"]
    for i, a in enumerate(items, 1):
        emoji = SOURCE_META.get(a.get("category", ""), {}).get("emoji", "•")
        lines.append(
            f"\n<font color=\"info\">{i}.</font> {emoji} [{a['title']}]({a['link']})"
        )
    lines.append("\n\n---\n<font color=\"comment\">ai-daily-wecom</font>")
    return "".join(lines)
