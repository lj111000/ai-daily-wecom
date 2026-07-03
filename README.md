# ai-daily-wecom

每日 AI 前沿动态，定时推送到企业微信群。**全免费 / 零服务器 / GitHub Actions 托管。**

- 北京时间 **9:00**：开源项目 + 教程博客（早上看技术更专注）
- 北京时间 **14:00**：行业新闻 + 前沿论文（下午看资讯更轻松）

## 推送效果

```
🌅 早安 · 今日 AI 工程动态
> 2026-07-03 Thursday · 开源项目 + 教程博客

🔧 开源项目 (3 条)

1. vllm/vllm · PagedAttention 优化
> 本周新增显存分页机制，吞吐量提升 30%...
📍 GitHub Trending (Python · AI/ML)

2. ...

📚 教程博客 (2 条)
...

---
由 ai-daily-wecom 自动推送 · 数据源见 README
```

## 快速部署（10 分钟）

### 1. 创建企微群机器人

1. 企业微信群里：右键群 → 群设置 → 群机器人 → 添加机器人
2. 起个名字（比如 `AI 日报`），拿到 Webhook URL：
   `https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxxxxx-xxxx-xxxx`
3. **复制 URL 末尾的 key 部分**（`?key=` 后面那一串）

### 2. Fork / Clone 本仓库

```bash
git clone <你的仓库地址>
cd ai-daily-wecom
```

### 3. 配置 GitHub Secret

仓库 → Settings → Secrets and variables → Actions → New repository secret

- Name：`WECOM_WEBHOOK_KEY`
- Value：第 1 步复制的 key（**只填 key，不要带 `?key=`**）

### 4. 本地测试（可选但推荐）

```bash
pip install -r requirements.txt
cd src

# dry-run，只打印不推送
python main.py --dry-run

# 强制走早间策略
python main.py --morning --dry-run

# 真的推送到群里（确认 Webhook Key 已设置）
python main.py
```

### 5. 启用 GitHub Actions

- push 到 GitHub 后，Actions 标签页应该能看到 `AI Daily Push` workflow
- 点 `Enable workflows`
- 想立刻测试？点 `Run workflow` 手动触发一次

## 自定义

### 加 / 删 RSS 源

编辑 `src/config.py` 里的 `RSS_SOURCES`，按类别加：

```python
"news": [
    ...
    {
        "name": "我的新源",
        "url": "https://example.com/rss",
        "weight": 4,   # 1-5，越高越优先
        "lang": "zh",
    },
],
```

### 改推送时段 / 数量

编辑 `src/config.py` 里的 `SCHEDULES`：

```python
SCHEDULES = {
    "morning": {
        "categories": ["open_source", "tutorial"],
        "counts": {"open_source": 3, "tutorial": 2},  # 各推几条
        ...
    },
    ...
}
```

同时改 `.github/workflows/daily.yml` 里的 cron 表达式。

### 改热词（影响排序）

编辑 `src/config.py` 里的 `HOT_KEYWORDS`，命中的文章会加分排前面。

## 数据源

| 类别 | 源 |
|---|---|
| 开源项目 | GitHub Trending (AI/ML, Jupyter)、HuggingFace |
| 教程博客 | OpenAI Blog、Anthropic News、HuggingFace Blog、Sebastian Raschka、Lilian Weng、机器之心 |
| 行业新闻 | 量子位、新智元、TLDR AI、The Batch、Reddit r/artificial |
| 前沿论文 | HuggingFace Daily Papers、ArXiv cs.AI、ArXiv cs.CL |

## 常见问题

**Q: 推送失败，errcode=45009？**
A: 触发限频（每机器人 20 条/分钟）。代码里有自动重试，但如果你配了多个 cron 同时跑就会冲突。改 cron 错开几分钟。

**Q: 推送内容是空的？**
A: 检查 Actions 日志，看是不是 RSS 源全挂了。可以临时跑 `python main.py --morning --dry-run` 看抓取情况。

**Q: 想换群 / 换 Key？**
A: 改 GitHub Secret 即可，不用改代码。

**Q: seen.json 怎么管理？**
A: workflow 每次跑完会自动 commit 回仓库，跨次运行时去重靠它。如果你想"重新推一遍所有内容"，删掉 `src/seen.json` 即可。

## 文件结构

```
ai-daily-wecom/
├── .github/workflows/daily.yml   # GitHub Actions 定时任务
├── src/
│   ├── config.py                  # RSS 源 + 推送策略（**主要改这里**）
│   ├── fetcher.py                 # RSS 抓取
│   ├── selector.py                # 去重 + 打分 + 选片
│   ├── formatter.py               # 企微 markdown 格式化
│   ├── notifier.py                # Webhook 推送
│   └── main.py                    # 主入口
├── requirements.txt
└── README.md
```

## 已知限制

- 企微 markdown 不支持图片直接嵌入；当前方案只发文字链接
- 部分国内 RSS 源可能间歇性 503，代码里做了并发+超时兜底，但单源挂了就少一条
- GitHub Actions cron 不保证准时，通常延迟 5-15 分钟，介意可换云服务器 cron
