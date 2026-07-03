"""
内容筛选 + 去重 + 打分模块
- 去重：标题 hash 持久化到 seen.json，跨次运行
- 打分：来源权重(1-5) + 热词命中(+1 each) + 时间衰减(越新越高)
- 选片：按类别配额挑选
"""

import json
import os
import re
import hashlib
import logging
from datetime import datetime, timezone, timedelta

from config import HOT_KEYWORDS, SEEN_FILE, SCHEDULES, MAX_SUMMARY_LEN

logger = logging.getLogger(__name__)
CST = timezone(timedelta(hours=8))


# ============ 去重 ============

def _title_hash(title: str) -> str:
    """标题归一化后哈希，去掉大小写/空格/标点差异"""
    norm = re.sub(r"[\s\W_]+", "", title.lower())
    return hashlib.md5(norm.encode("utf-8")).hexdigest()


def load_seen() -> set[str]:
    if not os.path.exists(SEEN_FILE):
        return set()
    try:
        with open(SEEN_FILE, "rb") as f:
            data = json.load(f)
        return set(data.get("hashes", []))
    except Exception:
        return set()


def save_seen(hashes: set[str]) -> None:
    # 限制 seen.json 体量，避免无限膨胀；保留最近 5000 条
    trimmed = sorted(hashes)[-5000:]
    tmp = SEEN_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"hashes": trimmed}, f)
    os.replace(tmp, SEEN_FILE)


def filter_seen(articles: list[dict], seen: set[str]) -> tuple[list[dict], set[str]]:
    """返回 (未推过的文章, 本次新加入 seen 的新 hash)"""
    fresh, new_hashes = [], set()
    for a in articles:
        h = _title_hash(a["title"])
        if h in seen:
            continue
        fresh.append(a)
        new_hashes.add(h)
    return fresh, new_hashes


# ============ 打分 ============

def _hot_keyword_score(title: str) -> int:
    """标题命中热词加分"""
    t = title.lower()
    return sum(1 for kw in HOT_KEYWORDS if kw.lower() in t)


def _recency_score(published: datetime | None) -> float:
    """时间衰减：6 小时内 +2，24 小时内 +1，更早 0"""
    if not published:
        return 1.0
    age_h = (datetime.now(timezone.utc) - published).total_seconds() / 3600
    if age_h < 6:
        return 2.0
    if age_h < 24:
        return 1.0
    return 0.5


def score_article(a: dict) -> float:
    return (
        a["source_weight"]            # 1-5，主要权重
        + _hot_keyword_score(a["title"]) * 0.5  # 热词 0.5/命中
        + _recency_score(a["published"])        # 0.5-2
    )


# ============ 选片 ============

def select(articles: list[dict], schedule_key: str) -> dict[str, list[dict]]:
    """
    按排程配额选片
    返回 {category: [articles...]}
    """
    schedule = SCHEDULES[schedule_key]
    counts = schedule["counts"]

    # 打分
    scored = sorted(
        articles,
        key=lambda a: (score_article(a), a.get("fetched_at", 0)),
        reverse=True,
    )

    # 按类别装桶
    result = {cat: [] for cat in counts}
    for a in scored:
        cat = a["category"]
        if cat not in counts:
            continue
        if len(result[cat]) >= counts[cat]:
            continue
        # 截断摘要
        if len(a["summary"]) > MAX_SUMMARY_LEN:
            a = {**a, "summary": a["summary"][:MAX_SUMMARY_LEN] + "..."}
        result[cat].append(a)

    return result


# ============ 决定当前是哪个时段 ============

def current_schedule_key() -> str:
    """根据北京时间小时返回 morning/afternoon"""
    hour = datetime.now(CST).hour
    return "morning" if hour < 12 else "afternoon"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    # 简单冒烟
    fake = [
        {"title": "GPT-5 release", "link": "x", "summary": "", "source_name": "test",
         "source_weight": 5, "lang": "en", "category": "news", "published": None,
         "fetched_at": 0},
        {"title": "无聊的新闻", "link": "y", "summary": "", "source_name": "test",
         "source_weight": 2, "lang": "zh", "category": "news", "published": None,
         "fetched_at": 0},
    ]
    print(select(fake + fake, "afternoon"))
