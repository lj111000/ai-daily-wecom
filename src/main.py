"""
ai-daily-wecom 主入口
用法：
    python main.py              # 正常推送（GitHub Actions 调用）
    python main.py --dry-run    # 只打印不推送
    python main.py --count 5    # 改推送条数（默认 15）
"""

import logging
import argparse

from config import PUSH_TITLE, PUSH_COUNT
from fetcher import fetch_all
from selector import load_seen, save_seen, filter_seen, select
from summarizer import summarize_batch
from formatter import format_message
from notifier import send_markdown

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("ai-daily")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="只打印不推送")
    p.add_argument("--count", type=int, default=PUSH_COUNT, help="推送条数")
    args = p.parse_args()

    logger.info(f"🏃 开始聚合 ({args.count} 条)")

    # 1. 抓取所有类别
    from config import RSS_SOURCES
    all_articles = fetch_all(list(RSS_SOURCES.keys()))
    if not all_articles:
        logger.warning("⚠️ 没抓到任何文章，推送空通知")
        send_markdown(
            f"# {PUSH_TITLE}\n\n<font color=\"comment\">本次抓取失败，所有源均无数据。</font>",
            dry_run=args.dry_run,
        )
        return

    # 2. 去重
    seen = load_seen()
    fresh, new_hashes = filter_seen(all_articles, seen)
    logger.info(f"📥 总抓取 {len(all_articles)} 篇，去重后 {len(fresh)} 篇")

    if not fresh:
        logger.warning("所有文章都推送过了，本次跳过")
        return

    # 3. 打分+选片（混排）
    selected = select(fresh, count=args.count)
    if not selected:
        logger.warning("选片后无内容")
        return
    logger.info(f"📝 选出 {len(selected)} 条")

    # 4. LLM 改写成简讯 + 微语
    briefs, quote = summarize_batch(selected)
    logger.info(f"✍️ LLM 改写完成 ({len(briefs)} 条简讯)")

    # 5. 格式化
    message = format_message(selected, briefs, quote)
    logger.info(f"📝 生成消息 ({len(message)} 字符)")

    # 6. 推送
    ok = send_markdown(message, dry_run=args.dry_run)

    # 7. 推送成功才更新 seen
    if ok and not args.dry_run:
        save_seen(seen | new_hashes)
        logger.info(f"💾 记录 {len(new_hashes)} 条新 hash")
    elif args.dry_run:
        logger.info("🔍 dry-run 模式，不更新 seen.json")

    logger.info("✨ 完成")


if __name__ == "__main__":
    main()
