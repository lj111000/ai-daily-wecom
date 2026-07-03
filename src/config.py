"""
配置文件：RSS 源 + Webhook + LLM + 推送策略
"""

import os

# ============ Webhook 配置 ============
WECOM_WEBHOOK_KEY = os.environ.get("WECOM_WEBHOOK_KEY", "YOUR_WEBHOOK_KEY_HERE")


def get_webhook_url() -> str:
    if WECOM_WEBHOOK_KEY == "YOUR_WEBHOOK_KEY_HERE":
        print("[WARN] WECOM_WEBHOOK_KEY 未设置，将仅打印不推送")
        return ""
    return f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={WECOM_WEBHOOK_KEY}"


# ============ LLM 配置（用于改写简讯）============
# 智谱 GLM-4-Flash：国内访问稳，免费额度足够日推
# 控制台：https://open.bigmodel.cn/  →  API Keys
GLM_API_KEY = os.environ.get("GLM_API_KEY", "")
GLM_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
GLM_MODEL = "glm-4-flash"      # 免费、快；想要更强用 "glm-4-plus"
GLM_TIMEOUT = 30               # 单次 API 超时（秒）


# ============ 推送策略 ============
# 每天 9:00 一次，推 15 条简讯 + 1 句每日微语（LLM 改写）
PUSH_TITLE = "🤖 AI 今日速递"
PUSH_COUNT = 15

# ============ RSS 源（中文 AI 资讯）============
# weight 越高优先级越高（1-5），影响打分排序
# 经验证：国内 AI 站点很多没有 RSS（智东西/AIbase/新智元/AIGC开放社区）
# 真正可用的只有以下 3 个，质量足够
RSS_SOURCES = {
    # ============ AI 前沿技术（深度解读/论文）============
    "frontier": [
        {
            "name": "机器之心",
            "url": "https://www.jiqizhixin.com/rss",
            "weight": 5,
            "lang": "zh",
        },
        {
            "name": "雷锋网 AI 频道",
            "url": "https://www.leiphone.com/feed/",
            "weight": 4,
            "lang": "zh",
        },
    ],

    # ============ AI 行业动态（产品/公司/资本）============
    "industry": [
        {
            "name": "量子位",
            "url": "https://www.qbitai.com/feed",
            "weight": 5,
            "lang": "zh",
        },
        {
            "name": "雷锋网 AI 频道",
            "url": "https://www.leiphone.com/feed/",
            "weight": 4,
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
    # 国产模型/产品
    "deepseek", "qwen", "通义", "千问", "文心", "豆包", "kimi", "智谱",
    "glm", "minimax", "百川", "零一", "step", "阶跃", "幻方",
    # 海外模型/产品
    "gpt", "chatgpt", "claude", "gemini", "llama", "grok", "midjourney",
    "sora", "o1", "o3", "sonnet",
    # 技术热词
    "agent", "智能体", "rag", "mcp", "rlhf", "sft", "lora", "moe",
    "diffusion", "transformer", "mamba", "reasoning", "推理",
    "scaling", "训推", "微调", "开源",
    # 行业热词
    "突破", "首发", "全球首", "国产", "超越", "碾压",
    "发布", "上线", "开源", "免费",
]

# ============ 运行参数 ============
FETCH_TIMEOUT = 10       # 单源抓取超时（秒）
LOOKBACK_HOURS = 72      # 抓最近 3 天，去重靠 seen.json
SEEN_FILE = os.path.join(os.path.dirname(__file__), "..", "seen.json")
