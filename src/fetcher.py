"""
RSS 抓取模块
统一返回 Article 字典列表，方便后续筛选/打分/格式化。
"""

import time
import socket
import logging
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

import feedparser

from config import RSS_SOURCES, FETCH_TIMEOUT, LOOKBACK_HOURS

logger = logging.getLogger(__name__)

# feedparser 不读 config 里的超时，必须设 socket 默认超时
socket.setdefaulttimeout(FETCH_TIMEOUT)

# 北京时区
CST = timezone(timedelta(hours=8))


def _parse_published(entry) -> datetime | None:
    """feedparser 解析发布时间，失败返回 None"""
    for field in ("published_parsed", "updated_parsed"):
        t = entry.get(field)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                continue
    return None


def _strip_html(text: str) -> str:
    """粗暴去 HTML 标签，够用"""
    import re
    text = re.sub(r"<[^>]+>", "", text or "")
    return re.sub(r"\s+", " ", text).strip()


def fetch_one(source: dict, category: str) -> list[dict]:
    """
    抓单个 RSS 源，返回标准化的文章列表
    source: {"name", "url", "weight", "lang"}
    """
    articles = []
    try:
        # feedparser 自带 socket 超时不太靠谱，用 ThreadPool 兜底
        parsed = feedparser.parse(
            source["url"],
            request_headers={"User-Agent": "Mozilla/5.0 ai-daily-wecom/1.0"},
        )
        if parsed.bozo and not parsed.entries:
            logger.warning(f"[{source['name']}] 解析失败: {parsed.bozo_exception}")
            return []

        cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)

        for entry in parsed.entries:
            pub = _parse_published(entry)
            # 超过回溯窗口的跳过；解析失败也放进来（宁可多推不漏推）
            if pub and pub < cutoff:
                continue

            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            summary = _strip_html(
                entry.get("summary") or entry.get("description", "")
            )
            if not title or not link:
                continue

            articles.append({
                "title": title,
                "link": link,
                "summary": summary,
                "source_name": source["name"],
                "source_weight": source["weight"],
                "lang": source["lang"],
                "category": category,
                "published": pub,
                "fetched_at": time.time(),
            })
    except Exception as e:
        logger.warning(f"[{source['name']}] 抓取异常: {e}")

    return articles


def fetch_all(categories: list[str]) -> list[dict]:
    """
    并发抓取多个类别的所有源
    返回所有文章的大杂烩，交给 selector 去重打分
    """
    tasks = []
    for cat in categories:
        for src in RSS_SOURCES.get(cat, []):
            tasks.append((src, cat))

    all_articles = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(fetch_one, src, cat): src["name"] for src, cat in tasks}
        # 注意：as_completed 的 timeout 抛异常会让整个流程挂掉
        # 改用逐个 fut.result(timeout=...) 容错，单个超时不影响其他源
        for fut in as_completed(futures):
            name = futures[fut]
            try:
                result = fut.result(timeout=FETCH_TIMEOUT + 5)
                all_articles.extend(result)
            except TimeoutError:
                logger.warning(f"抓取 {name} 超时（>{FETCH_TIMEOUT+5}s）")
            except Exception as e:
                logger.warning(f"抓取 {name} 失败: {e}")

    logger.info(f"共抓到 {len(all_articles)} 篇 (类别: {categories})")
    return all_articles


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    arts = fetch_all(["open_source", "tutorial"])
    for a in arts[:5]:
        print(f"[{a['source_name']}] {a['title']}")
        print(f"  {a['link']}")
        print(f"  摘要: {a['summary'][:80]}")
