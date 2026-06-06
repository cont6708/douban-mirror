<p align="center">
  <a href="#english"><img src="https://img.shields.io/badge/🌐-English-blue" alt="English"></a>
  &nbsp;
  <a href="#中文"><img src="https://img.shields.io/badge/🌐-中文-red" alt="中文"></a>
</p>

---

<h1 id="english">🪞 douban-mirror</h1>

> Your bookshelf is a mirror. What you read, watch, and listen to reflects who you are.

A **Claude Code Skill** that analyzes a person's Douban (豆瓣) cultural consumption history — books, films, music — and generates a comprehensive personality profile using the **Big Five (OCEAN)** framework, Schwartz value orientations, and aesthetic signature analysis.

<p align="right"><a href="#中文">中文 →</a></p>

## What It Does

1. **Collects** all publicly available Douban data for a given user (books read, movies watched, music listened, reviews, statuses, doulists)
2. **Analyzes** consumption patterns through the lens of academic personality psychology
3. **Generates** a structured, evidence-grounded personality profile report covering:
   - **Big Five (OCEAN)** — Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism (1–10 with confidence labels)
   - **Value Orientations** — Self-transcendence vs. self-enhancement, openness to change vs. conservation
   - **Aesthetic Signature** — Complexity tolerance, sensory vs. conceptual, temporal orientation, cultural breadth
   - **Ideological Evolution** — How tastes and concerns shifted across years
   - **Rating Ecology** — Full distribution of star ratings

## Why Douban?

Douban is the definitive cultural consumption platform in the Chinese-speaking world. A user's history — often spanning 5–10 years and thousands of items — constitutes one of the richest behavioral datasets for personality inference outside clinical settings.

## How It Works

```
Data Collection → Structuring → Big Five → Value Analysis → Aesthetic Signature → Report
```

**Psychological foundations:** Big Five (OCEAN), Schwartz Value Theory, Rentfrow & Gosling (2003).

## Data Collected

| Category | Login Required | Target |
|----------|---------------|--------|
| 📚 Books read / reading / want-to-read | No* | 100% |
| 📝 Book reviews | No | 100% |
| 🎬 Movies watched / want-to-watch | No | 100% |
| 🎵 Music listened / want-to-listen | No | 100% |
| 📊 Statuses / activity feed | **Yes** (dbcl2 cookie) | 100%** |
| 📋 Doulists | **Yes** (dbcl2 cookie) | Max |

> \* Falls back to `curl` with browser headers when WebFetch returns 403.
> \*\* Contains star ratings not visible on collection pages.

## Install

```bash
# As a Claude Code Skill
cp douban-profile.md ~/.claude/skills/
```

Then invoke: `/douban-profile`

## Scripts

```bash
# Collect all books
python scripts/fetch_books.py <douban_id>

# Collect statuses with ratings (requires login)
export DB_CL2='dbcl2="your_cookie_value"'
python scripts/fetch_statuses.py <douban_id>
```

## Project Structure

```
douban-mirror/
├── README.md
├── douban-profile.md          # Claude Code Skill
├── scripts/
│   ├── fetch_books.py
│   └── fetch_statuses.py
├── .gitignore
└── LICENSE
```

## Privacy

All collection and analysis runs **locally**. No data is stored or uploaded. The `dbcl2` cookie is ephemeral.

## Limitations

This is **probabilistic inference**, not clinical diagnosis. Cultural consumption best reveals **Openness** and **Values**; Extraversion and Neuroticism inferences are weaker. Douban is semi-public — displayed tastes may reflect social desirability.

## License

MIT

<p align="center"><a href="#中文">↓ 中文版本 ↓</a></p>

---

<h1 id="中文">🪞 douban-mirror（豆瓣镜）</h1>

> 豆瓣如镜，照见人格。你的书架，就是你的倒影。

一个 **Claude Code Skill**，基于目标用户在豆瓣的书影音消费记录，使用心理学 **Big Five (OCEAN)** 框架生成人格画像、价值观取向和审美偏好分析。

<p align="right"><a href="#english">English →</a></p>

## 它做什么

1. **全量采集**目标用户的豆瓣公开（及登录后可见）数据——书籍、电影、音乐、书评、动态、豆列
2. **分析**消费模式背后的人格信号
3. **生成**结构化报告，涵盖：
   - **Big Five 人格维度** — 开放性、尽责性、外向性、宜人性、情绪稳定性（1-10 分 + 置信度）
   - **价值观取向** — 自我超越 vs. 自我增强、开放 vs. 保守、智识 vs. 审美
   - **审美签名** — 复杂度容忍度、感官 vs. 概念偏好、时间取向、文化广度
   - **意识形态进化轨迹** — 品味和关注点如何随时间演变
   - **评分生态** — 完整评分分布 + 代表性案例

## 为什么是豆瓣？

豆瓣是中文世界最权威的文化消费记录平台。一个用户的豆瓣历史——往往跨越 5-10 年、涵盖数千条记录——构成了临床环境之外最丰富的人格推断行为数据集之一。

## 工作原理

```
数据采集 → 结构化 → Big Five 分析 → 价值观分析 → 审美签名 → 完整报告
```

**理论基础**：Big Five 人格模型、Schwartz 价值观理论、Rentfrow & Gosling 文化消费-人格相关性研究。

## 采集数据

| 类别 | 需要登录 | 目标 |
|------|---------|------|
| 📚 读过/在读/想读 | 否* | 100% |
| 📝 书评 | 否 | 100% |
| 🎬 看过/想看 | 否 | 100% |
| 🎵 听过/想听 | 否 | 100% |
| 📊 动态/广播 | **需要** dbcl2 cookie | 100%** |
| 📋 豆列 | **需要** dbcl2 cookie | 尽可能多 |

> \* 书籍页面可能返回 403，skill 会自动切换 curl + 浏览器头绕过。
> \*\* 动态数据包含收藏页不显示的星级评分。

## 安装

```bash
# 安装为 Claude Code Skill
cp douban-profile.md ~/.claude/skills/
```

调用：`/douban-profile`

## 脚本

```bash
# 采集全部书籍
python scripts/fetch_books.py <豆瓣ID>

# 采集动态（需要登录 cookie）
export DB_CL2='dbcl2="你的cookie值"'
python scripts/fetch_statuses.py <豆瓣ID>
```

## 隐私

所有采集和分析**完全在本地**运行。不存储、不上传任何用户数据。`dbcl2` cookie 仅当次会话使用。

## 局限性

这是**概率性推测**，不是临床诊断。文化消费最能揭示**开放性**和**价值观**；外向性和情绪稳定性的推断较弱。豆瓣是半公开平台，展示的品味可能反映社会称许偏差。

## License

MIT

<p align="center"><a href="#english">↑ English ↑</a></p>
