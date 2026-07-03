"""
企微 Webhook 推送
- 文档：https://developer.work.weixin.qq.com/document/path/91770
- 频率限制：每个机器人 20 条/分钟，单条消息 markdown 上限 4096 字节
- 错误处理：限频(45009)/IP 限制(45002) 等
"""

import sys
import io
import json
import time
import logging

import requests

from config import get_webhook_url

logger = logging.getLogger(__name__)

# Windows 终端默认 GBK，emoji 会编码失败；强制 stdout/stderr 走 UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def send_markdown(content: str, dry_run: bool = False) -> bool:
    """
    推送一条 markdown 消息到企微群
    dry_run=True 时只打印不发
    """
    if dry_run:
        print("\n" + "=" * 60)
        print("[DRY-RUN] 以下为待推送消息预览：")
        print("=" * 60)
        print(content)
        print("=" * 60 + "\n")
        return True

    url = get_webhook_url()
    if not url:
        logger.error("Webhook URL 未配置，跳过推送")
        return False

    payload = {
        "msgtype": "markdown",
        "markdown": {"content": content},
    }

    for attempt in range(3):
        try:
            resp = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            data = resp.json()

            if data.get("errcode") == 0:
                logger.info("✅ 推送成功")
                return True

            if data.get("errcode") == 45009:
                # 限频，等 30s 重试
                logger.warning(f"触发限频，30s 后重试 ({attempt+1}/3)")
                time.sleep(30)
                continue

            logger.error(f"推送失败: {data}")
            return False

        except requests.RequestException as e:
            logger.warning(f"网络异常 {e}，5s 后重试 ({attempt+1}/3)")
            time.sleep(5)

    logger.error("推送最终失败（3 次重试均失败）")
    return False


if __name__ == "__main__":
    send_markdown("# 测试消息\n\nhello from ai-daily-wecom", dry_run=True)
