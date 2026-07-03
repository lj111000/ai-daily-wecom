"""
内容筛选 + 去重 + 打分 + 选片
- 去重：标题 hash 持久化到 seen.json，跨次运行
- 打分：来源权重(1-5) + 热词命中(+0.5 each) + 时间衰减
- 选片：所有源混排，按打分取 top N
"""

import json
import os
import re
import hashlib
import logging
from datetime import datetime, timezone, timedelta

from config import HOT_KEYWORDS, SEEN_FILE, PUSH_COUNT

logger = logging.getLogger(__name__)
CST = timezone(timedelta(hours=8))


# ============ 去重 ============

def _title_hash(title: str) -> str:
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
    trimmed = sorted(hashes)[-5000:]
    tmp = SEEN_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"hashes": trimmed}, f)
    os.replace(tmp, SEEN_FILE)


def filter_seen(articles: list[dict], seen: set[str]) -> tuple[list[dict], set[str]]:
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
    t = title.lower()
    return sum(1 for kw in HOT_KEYWORDS if kw.lower() in t)


def _recency_score(published: datetime | None) -> float:
    if not published:
        return 1.0
    age_h = (datetime.now(timezone.utc) - published).total_seconds() / 3600
    if age_h < 6:
        return 2.0
    if age_h < 24:
        return 1.0
    if age_h < 48:
        return 0.7
    return 0.4


def score_article(a: dict) -> float:
    return (
        a["source_weight"]
        + _hot_keyword_score(a["title"]) * 0.5
        + _recency_score(a["published"])
    )


# ============ 选片（混排，不分类）============

def select(articles: list[dict], count: int = PUSH_COUNT) -> list[dict]:
    """按打分取 top N，混排（不分类别）"""
    scored = sorted(
        articles,
        key=lambda a: (score_article(a), a.get("fetched_at", 0)),
        reverse=True,
    )
    top = scored[:count]
    # 截断摘要
    for a in top:
        if len(a["summary"]) > 120:
            a["summary"] = a["summary"][:120] + "..."
    return top
