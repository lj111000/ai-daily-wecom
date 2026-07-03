# ai-daily-wecom

每日 AI 早报，定时推送到企业微信群。**全中文 / LLM 改写 / 零服务器 / GitHub Actions 托管。**

> 部署位置：定时任务在 **GitHub Actions** 上跑（gitee 仅作镜像展示）。本地同时配 gitee + github 两个 remote，用 `./push-all.sh` 一键推送。

## 推送效果

```
# 🤖 AI 今日速递 07月03日 Friday

1. AReaL 2.0开源，自演进智能体RL基础设施升级 · 量子位
2. Claude Sonnet 5性价比受挫，千问和 Minimax成对手 · 雷锋网
3. 世界模型新用，AI当裁判非选手 · 量子位
...
15. 自变量发布X-Tokenizer，多模态对齐性能提升 · 雷锋网

【每日微语】AI技术迭代，产品定义才是关键
```

特点：
- **15 条简讯**：从 50+ 篇原始 RSS 文章里打分挑出 top 15
- **LLM 改写**：每条用 GLM-4-Flash 压成 15-25 字一句话
- **每日微语**：LLM 生成，带观点不鸡汤
- **跨分类去重**：同一篇文章不会被两个分类重复推
- **失败降级**：LLM 挂了用原标题，源挂了跳过该条

## 快速部署（10 分钟）

### 1. 建企微群机器人

群里右键 → 群设置 → 群机器人 → 添加 → 起名 → 复制 Webhook URL 末尾的 `key=xxxx` 部分。

### 2. 申请 GLM API Key

智谱开放平台（https://open.bigmodel.cn/）→ 注册 → 控制台 → API Keys → 创建。
**GLM-4-Flash 模型免费**，日推 15 条足够用。

### 3. 配置两个 GitHub Secret

仓库 Settings → Secrets and variables → Actions → New：

| Name | Value |
|---|---|
| `WECOM_WEBHOOK_KEY` | 企微 Webhook URL 末尾的 key（不带 `?key=`） |
| `GLM_API_KEY` | 智谱 GLM 的 API Key |

### 4. Fork / Clone 后 push 到 GitHub

```bash
git clone <仓库地址>
cd ai-daily-wecom
# 改完代码或 RSS 源
./push-all.sh
```

### 5. 启用 GitHub Actions

push 后到 GitHub 仓库 Actions 标签页 → Enable workflows → Run workflow 手动测一次。

## 本地测试

```bash
pip install -r requirements.txt
cd src

# 设环境变量（任选其一）
export GLM_API_KEY="你的key"
export WECOM_WEBHOOK_KEY="你的企微key"   # 不设也能 dry-run

# dry-run，只打印不推送
python main.py --dry-run

# 改条数
python main.py --dry-run --count 10

# 真的推送到群
python main.py
```

## 自定义

### 改 RSS 源

编辑 `src/config.py` 的 `RSS_SOURCES`：

```python
"frontier": [
    {"name": "我的源", "url": "https://...", "weight": 5, "lang": "zh"},
],
```

`weight` 1-5，影响打分排序。当前国内 AI 站点很多没原生 RSS（智东西/AIbase/新智元/AIGC开放社区），真正稳定可用的就是机器之心/雷锋网/量子位 这 3 家。

### 改条数 / 标题 / 微语风格

`src/config.py`：
- `PUSH_COUNT`：推送条数（默认 15）
- `PUSH_TITLE`：顶部标题

`src/summarizer.py`：调整 `SYSTEM_PROMPT` 改简讯风格（更狠 / 更稳 / 更口语）。

### 改 LLM 模型

`src/config.py`：
- `GLM_MODEL = "glm-4-flash"` 免费，想要更强用 `"glm-4-plus"`（计费）

### 改推送时间

`.github/workflows/daily.yml` 里 cron 表达式：
```yaml
- cron: '0 1 * * *'    # 北京 09:00（UTC 1:00）
```

## 文件结构

```
ai-daily-wecom/
├── .github/workflows/daily.yml   # GitHub Actions 定时
├── src/
│   ├── config.py                  # 配置（**主要改这里**）
│   ├── fetcher.py                 # RSS 抓取（并发+超时）
│   ├── selector.py                # 去重 + 打分 + 选片 + 跨分类相似去重
│   ├── summarizer.py              # GLM 改写简讯 + 微语
│   ├── formatter.py               # 企微 markdown 格式化
│   ├── notifier.py                # Webhook 推送（重试+限频兜底）
│   └── main.py                    # 主入口
├── requirements.txt
├── push-all.sh                    # 一键推 gitee + github
└── README.md
```

## 常见问题

**Q: 推送失败 errcode=45009？**
A: 触发限频（每机器人 20 条/分钟）。代码里有 30s 重试。如果你同时配了多个 cron 撞时间就会冲突。

**Q: LLM 改写偶尔少几条？**
A: GLM 数数偶尔抽风。代码做了兜底：缺的用原标题补齐，不影响整体推送。

**Q: 想换群 / 换 Key？**
A: GitHub Secret 改完立即生效，代码不用动。

**Q: seen.json 怎么管理？**
A: workflow 每次跑完会自动 commit 回仓库做去重。想"重新推一遍"删 `src/seen.json` 即可。

**Q: 机器之心 RSS 经常失败？**
A: 站点 XML 偶尔格式错误。代码做了单源失败兜底，机器之心挂了不影响量子位+雷锋网。

## 已知限制

- 企微 markdown 不支持图片直接嵌入，当前纯文字
- 15 条 + 链接偶尔超 2000 字符，会自动降级去掉来源标注（链接保留）
- GitHub Actions cron 不保证准时，通常延迟 5-15 分钟
