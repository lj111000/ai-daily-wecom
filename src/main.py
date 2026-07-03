"""
ai-daily-wecom 主入口
用法：
    python main.py              # 按当前北京时间自动选时段（GitHub Actions 调用）
    python main.py --morning    # 强制走早间策略
    python main.py --afternoon  # 强制走午后策略
    python main.py --dry-run    # 只打印不推送
"""

import sys
import logging
import argparse

from config import SCHEDULES
from fetcher import fetch_all
from selector import (
    load_seen, save_seen, filter_seen, select, current_schedule_key,
)
from formatter import format_message
from notifier import send_markdown

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("ai-daily")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--morning", action="store_true", help="强制走早间策略")
    p.add_argument("--afternoon", action="store_true", help="强制走午后策略")
    p.add_argument("--dry-run", action="store_true", help="只打印不推送")
    return p.parse_args()


def get_schedule_key(args) -> str:
    if args.morning:
        return "morning"
    if args.afternoon:
        return "afternoon"
    return current_schedule_key()


def main():
    args = parse_args()
    schedule_key = get_schedule_key(args)
    schedule = SCHEDULES[schedule_key]
    logger.info(f"🏃 当前时段: {schedule_key} ({schedule['title']})")

    # 1. 抓取
    categories = list(schedule["counts"].keys())
    all_articles = fetch_all(categories)
    if not all_articles:
        logger.warning("⚠️ 没抓到任何文章，跳过本次推送")
        send_markdown(
            f"# {schedule['title']}\n\n"
            f"<font color=\"comment\">本次抓取失败，所有源均无数据。</font>",
            dry_run=args.dry_run,
        )
        return

    # 2. 去重（跨次运行，seen.json 持久化）
    seen = load_seen()
    fresh, new_hashes = filter_seen(all_articles, seen)
    logger.info(f"📥 总抓取 {len(all_articles)} 篇，去重后 {len(fresh)} 篇")

    if not fresh:
        logger.warning("所有文章都推送过了，本次跳过")
        return

    # 3. 打分+选片
    selected = select(fresh, schedule_key)
    total = sum(len(v) for v in selected.values())
    if total == 0:
        logger.warning("选片后无内容可推")
        return

    # 4. 格式化
    message = format_message(selected, schedule_key)
    logger.info(f"📝 生成消息 ({len(message)} 字符)")

    # 5. 推送
    ok = send_markdown(message, dry_run=args.dry_run)

    # 6. 推送成功才更新 seen（避免失败后跳过下次推送）
    if ok and not args.dry_run:
        save_seen(seen | new_hashes)
        logger.info(f"💾 已记录 {len(new_hashes)} 条新 hash")
    elif args.dry_run:
        logger.info("🔍 dry-run 模式，不更新 seen.json")

    logger.info("✨ 完成")


if __name__ == "__main__":
    main()
