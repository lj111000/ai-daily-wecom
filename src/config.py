"""
配置文件：RSS 源 + Webhook + 推送策略
所有源按类别分组，方便后续增删。
"""

import os

# ============ Webhook 配置 ============
# 从环境变量读，避免硬编码到 git
WECOM_WEBHOOK_KEY = os.environ.get("WECOM_WEBHOOK_KEY", "YOUR_WEBHOOK_KEY_HERE")

# 完整 Webhook URL（不要把 key 写死在这里！）
def get_webhook_url() -> str:
    if WECOM_WEBHOOK_KEY == "YOUR_WEBHOOK_KEY_HERE":
        print("[WARN] WECOM_WEBHOOK_KEY 未设置，将仅打印不推送")
        return ""
    return f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={WECOM_WEBHOOK_KEY}"

# ============ 推送策略 ============
# 9:00 推：开源项目 + 教程博客（早上看技术内容更专注）
# 14:00 推：行业新闻 + 论文速递（下午看资讯更轻松）
SCHEDULES = {
    "morning": {  # UTC 1:00 = 北京 9:00
        "categories": ["open_source", "tutorial"],
        "counts": {"open_source": 3, "tutorial": 2},
        "title": "🌅 早安 · 今日 AI 工程动态",
        "subtitle": "开源项目 + 教程博客",
    },
    "afternoon": {  # UTC 6:00 = 北京 14:00
        "categories": ["news", "paper"],
        "counts": {"news": 4, "paper": 1},
        "title": "☀️ 下午茶 · AI 行业快讯",
        "subtitle": "行业新闻 + 前沿论文",
    },
}

# ============ RSS 源 ============
# weight 越高优先级越高（1-5），影响排序
# lang: zh/en，影响是否需要翻译摘要
RSS_SOURCES = {
    # ============ 开源项目 ============
    "open_source": [
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
            "name": "InfoQ 中文",
            "url": "https://www.infoq.cn/feed",
            "weight": 3,
            "lang": "zh",
        },
    ],

    # ============ 教程与博客 ============
    "tutorial": [
        {
            "name": "OpenAI Blog",
            "url": "https://openai.com/news/rss.xml",
            "weight": 5,
            "lang": "en",
        },
        {
            "name": "Sebastian Raschka (LLM 深度教程)",
            "url": "https://magazine.sebastianraschka.com/feed",
            "weight": 5,
            "lang": "en",
        },
        {
            "name": "Lilian Weng (前沿综述)",
            "url": "https://lilianweng.github.io/index.xml",
            "weight": 4,
            "lang": "en",
        },
        {
            "name": "机器之心",
            "url": "https://www.jiqizhixin.com/rss",
            "weight": 3,
            "lang": "zh",
        },
    ],

    # ============ 行业新闻 ============
    "news": [
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
            "weight": 3,
            "lang": "en",
        },
        {
            "name": "量子位",
            "url": "https://www.qbitai.com/feed",
            "weight": 3,
            "lang": "zh",
        },
    ],

    # ============ 前沿论文 ============
    "paper": [
        {
            "name": "ArXiv cs.AI",
            "url": "https://export.arxiv.org/rss/cs.AI",
            "weight": 4,
            "lang": "en",
        },
        {
            "name": "ArXiv cs.CL (NLP)",
            "url": "https://export.arxiv.org/rss/cs.CL",
            "weight": 4,
            "lang": "en",
        },
        {
            "name": "ArXiv cs.LG",
            "url": "https://export.arxiv.org/rss/cs.LG",
            "weight": 3,
            "lang": "en",
        },
    ],
}

# ============ 分类 Emoji 标 ============
CATEGORY_META = {
    "open_source": {"label": "开源项目", "emoji": "🔧", "color": "info"},
    "tutorial":    {"label": "教程博客", "emoji": "📚", "color": "warning"},
    "news":        {"label": "行业新闻", "emoji": "📰", "color": "comment"},
    "paper":       {"label": "前沿论文", "emoji": "📄", "color": "warning"},
}

# ============ 热词加权（命中加分，影响排序）============
HOT_KEYWORDS = [
    "gpt", "claude", "gemini", "llama", "qwen", "deepseek",
    "agent", "rag", "rlhf", "sft", "lora", "moe",
    "diffusion", "transformer", "mamba", "rag",
    "开源", "国产", "突破", "首发", "全球首", "sota", "scale",
]

# ============ 运行参数 ============
MAX_SUMMARY_LEN = 120    # 摘要截断长度（字符）
FETCH_TIMEOUT = 10       # 单源抓取超时（秒）
LOOKBACK_HOURS = 72      # 抓最近 3 天，去重靠 seen.json（部分博客更新慢）
SEEN_FILE = os.path.join(os.path.dirname(__file__), "..", "seen.json")
