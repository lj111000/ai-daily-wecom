"""
企微消息格式化（纯文本早报版）
- 顶部：标题 + 当天日期
- 中间：编号 + 一句话简讯（纯文本，无链接）
- 底部：【每日微语】收尾
"""

import logging
from datetime import datetime, timedelta, timezone

from config import PUSH_TITLE

logger = logging.getLogger(__name__)
CST = timezone(timedelta(hours=8))


def format_message(items: list[dict], briefs: list[str], quote: str) -> str:
    """
    纯文本早报：不包链接、不带来源标注。
    items 和 briefs 等长、一一对应。
    """
    now = datetime.now(CST).strftime("%m月%d日 %A")

    lines = [
        f"# {PUSH_TITLE}",
        f"<font color=\"comment\">{now}</font>",
    ]

    for i, a in enumerate(items):
        brief = briefs[i] if i < len(briefs) else a["title"]
        lines.append(f"\n<font color=\"info\">{i + 1}.</font> {brief}")

    if quote:
        lines.append(f"\n\n【每日微语】<font color=\"info\">{quote}</font>")

    return "".join(lines)
