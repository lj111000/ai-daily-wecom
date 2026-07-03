"""
配置文件：RSS 源 + Webhook + 推送策略
"""

import os

# ============ Webhook 配置 ============
WECOM_WEBHOOK_KEY = os.environ.get("WECOM_WEBHOOK_KEY", "YOUR_WEBHOOK_KEY_HERE")


def get_webhook_url() -> str:
    if WECOM_WEBHOOK_KEY == "YOUR_WEBHOOK_KEY_HERE":
        print("[WARN] WECOM_WEBHOOK_KEY 未设置，将仅打印不推送")
        return ""
    return f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={WECOM_WEBHOOK_KEY}"


# ============ 推送策略 ============
# 每天 9:00 一次，推 10 条混排（按打分排序）
PUSH_TITLE = "🤖 AI 前沿 · 今日 10 条速递"
PUSH_SUBTITLE = "前沿技术 + 行业动态 · 自动聚合"
PUSH_COUNT = 10

# ============ RSS 源 ============
# weight 越高优先级越高（1-5），影响打分排序
# lang: zh/en，影响是否需要翻译摘要
RSS_SOURCES = {
    # ============ AI 前沿技术（论文 + 教程）============
    "frontier": [
        {
            "name": "Sebastian Raschka",
            "url": "https://magazine.sebastianraschka.com/feed",
            "weight": 5,
            "lang": "en",
        },
        {
            "name": "Lilian Weng (前沿综述)",
            "url": "https://lilianweng.github.io/index.xml",
            "weight": 5,
            "lang": "en",
        },
        {
            "name": "OpenAI Research",
            "url": "https://openai.com/news/rss.xml",
            "weight": 5,
            "lang": "en",
        },
        {
            "name": "NVIDIA Deep Learning Blog",
            "url": "https://blogs.nvidia.com/blog/category/deep-learning/feed/",
            "weight": 4,
            "lang": "en",
        },
        {
            "name": "MIT AI News",
            "url": "https://news.mit.edu/rss/topic/artificial-intelligence2",
            "weight": 4,
            "lang": "en",
        },
        {
            "name": "ArXiv cs.AI",
            "url": "https://export.arxiv.org/rss/cs.AI",
            "weight": 3,
            "lang": "en",
        },
        {
            "name": "ArXiv cs.CL (NLP/LLM)",
            "url": "https://export.arxiv.org/rss/cs.CL",
            "weight": 3,
            "lang": "en",
        },
        {
            "name": "ArXiv cs.LG",
            "url": "https://export.arxiv.org/rss/cs.LG",
            "weight": 2,
            "lang": "en",
        },
    ],

    # ============ AI 行业动态（新闻 + 产品）============
    "industry": [
        {
            "name": "TechCrunch AI",
            "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
            "weight": 5,
            "lang": "en",
        },
        {
            "name": "VentureBeat AI",
            "url": "https://venturebeat.com/category/ai/feed/",
            "weight": 4,
            "lang": "en",
        },
        {
            "name": "MarkTechPost",
            "url": "https://www.marktechpost.com/feed/",
            "weight": 4,
            "lang": "en",
        },
        {
            "name": "量子位",
            "url": "https://www.qbitai.com/feed",
            "weight": 4,
            "lang": "zh",
        },
        {
            "name": "机器之心",
            "url": "https://www.jiqizhixin.com/rss",
            "weight": 3,
            "lang": "zh",
        },
    ],
}

# ============ 分类 Emoji 标 ============
# 用于在标题前显示来源类型（用 category 判断）
SOURCE_META = {
    "frontier": {"emoji": "🔬"},
    "industry": {"emoji": "📰"},
}

# ============ 热词加权（命中加分，影响排序）============
HOT_KEYWORDS = [
    "gpt", "claude", "gemini", "llama", "qwen", "deepseek",
    "agent", "rag", "rlhf", "sft", "lora", "moe",
    "diffusion", "transformer", "mamba", "reasoning", "o1", "o3",
    "scaling", "benchmark", "open source", "open-source",
    "开源", "国产", "突破", "首发", "全球首", "sota",
]

# ============ 运行参数 ============
MAX_SUMMARY_LEN = 120    # 摘要截断长度（字符）
FETCH_TIMEOUT = 10       # 单源抓取超时（秒）
LOOKBACK_HOURS = 72      # 抓最近 3 天，去重靠 seen.json
SEEN_FILE = os.path.join(os.path.dirname(__file__), "..", "seen.json")
