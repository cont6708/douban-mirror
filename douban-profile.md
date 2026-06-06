---
name: douban-profile
description: Analyzes a person's Douban reading/watching/listening history to generate a Big Five (OCEAN) personality profile, value orientations, and aesthetic preferences. Use when a user asks about what their cultural consumption says about their personality, shares their Douban data, or invokes "/douban-profile" (or "豆瓣画像", "分析我的书影音").
---

# Douban Personality Profile

## Overview

What you read, watch, and listen to leaves a fingerprint on your personality — and vice versa. Decades of research in personality psychology (Rentfrow & Gosling, 2003; Kraaykamp & van Eijck, 2005) show that cultural consumption patterns correlate reliably with the Big Five personality dimensions.

This skill uses Claude's built-in knowledge of psychology, literature, film, and music to analyze a person's Douban history and produce a nuanced, evidence-grounded personality profile. No ML training, no external APIs — pure inference from structured observation.

## When to Use

- User explicitly invokes `/douban-profile`, "豆瓣画像", "分析我的书影音"
- User asks "what does my Douban history say about me?"
- User shares their book/movie/music lists and wants an interpretation
- User wants a Big Five personality profile based on their cultural taste

**When NOT to use:**
- User wants a clinical/diagnostic personality assessment (this is not a psychological test)
- User has never used Douban and has no cultural consumption data to share
- User is asking for Douban API technical questions (this is a profiling skill, not a Douban developer guide)

## The Psychological Framework

### Big Five (OCEAN) — Primary Framework

| Dimension | High indicators | Low indicators |
|-----------|----------------|----------------|
| **Openness** | Genre diversity, literary/experimental works, foreign-language content, philosophy/art books, avant-garde music | Strong genre loyalty, primarily mainstream, disinterest in translated works, few non-fiction categories |
| **Conscientiousness** | Systematic ratings (uses full 1-5 scale), detailed reviews, completes series, non-fiction how-to books | Many "want to read" but never completed, sparse/inconsistent ratings, abandoned long works |
| **Extraversion** | Popular/trending items, active in discussions, energetic/fast-paced content, comedy preference | Introspective/solitary themes, quiet music, literary fiction over genre fiction, internal psychological states |
| **Agreeableness** | Heartwarming/optimistic works, social justice themes, generous ratings (skews high), empathetic reviews | Dark/cynical/transgressive works, critical reviews, anti-hero narratives, low average ratings |
| **Neuroticism** | Angst/existential themes, melancholic music, re-reading as comfort, self-help/psychology books, emotionally intense reviews | Even rating distribution, plot-driven preferences, stable tastes over time, stoic/calm themes |

### Tier 2 — Value Orientations (Schwartz-inspired)

- **Self-Transcendence vs. Self-Enhancement**: Social justice content vs. success/achievement/business content
- **Openness to Change vs. Conservation**: Experimental art consumption vs. canonical/traditional works
- **Intellectual vs. Aesthetic**: Non-fiction ratio vs. fiction/art preference

### Tier 3 — Aesthetic Signature

- **Complexity tolerance**: Nonlinear narratives, ambiguous endings, dense prose — embraced or avoided?
- **Sensory vs. Conceptual**: Visceral/visual/auditory works vs. idea-driven works
- **Temporal orientation**: Historical / Contemporary / Futuristic patterns
- **Cultural breadth**: Ratio of translated or non-Chinese-language works

## The Process

### Phase 1: Data Acquisition — Strategy Overview

The data acquisition has multiple layers. Follow this strategy in order. Always aim for completeness — do NOT settle for partial data if more can be obtained.

#### Step 0: Get the Douban ID

Ask the user for the target person's Douban ID (numeric, visible in profile URL: `douban.com/people/{ID}/`). All subsequent fetches use this ID.

If the profile is the user's own, they can also provide their login cookie (`dbcl2`) to access private data (statuses, doulists, annotations).

#### Step 1: Fetch Main Profile (Baseline Stats)

Use WebFetch on `https://www.douban.com/people/{ID}/` to get:
- Username, registration date, IP location
- Total counts: books read/reading/want-to-read, movies watched/want-to-watch, music listened/want-to-listen
- Book/movie reviews count
- Recently read/watched items (first batch)

This gives you the **target scope** — how many pages of data you need to fetch for each category.

#### Step 2: Fetch Books — CORE DATA (use curl if needed)

Books are the richest personality signal. You MUST collect the complete "读过" (books read) list.

**Path A (Try first): WebFetch**
- `https://book.douban.com/people/{ID}/collect?sort=time&start=0&mode=grid&tags_sort=count`
- Paginate with `start=0,15,30,...` (15 items per page, grid mode)
- **IMPORTANT**: book.douban.com frequently returns 403 to WebFetch's default User-Agent. If this happens, immediately switch to Path B.

**Path B (Fallback): curl with browser headers**
If WebFetch returns 403, use bash curl with browser-like headers:
```bash
curl -s "https://book.douban.com/people/{ID}/collect?sort=time&start={start}&mode=grid&tags_sort=count" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  -H "Accept: text/html,application/xhtml+xml" \
  -H "Accept-Language: zh-CN,zh;q=0.9" \
  -H "Referer: https://www.douban.com/people/{ID}/"
```

Parse the HTML to extract for each book:
- Title, author/publisher info
- Star rating (from `<span class="ratingN-t"></span>` where N=1-5)
- Date read
- Comment/review text (short notes)

**Additional book data to collect:**
- `https://book.douban.com/people/{ID}/do` — currently reading (全部)
- `https://book.douban.com/people/{ID}/wish?start=0` — want-to-read (全部页面)
- `https://book.douban.com/people/{ID}/reviews` — long-form book reviews (全部页面)

**Books "want-to-read" can be 1000+ items.** You MUST collect ALL of them — the aspirational self is a crucial signal. Use a Python script with urllib (see `scripts/fetch_books.py`) to batch fetch efficiently with polite delays (0.3-0.5s between requests).

#### Step 3: Fetch Movies

Use WebFetch on `https://movie.douban.com/people/{ID}/collect?start={start}&sort=time&mode=grid&tags_sort=count` — movies typically work fine with WebFetch.

**Also collect:**
- `https://movie.douban.com/people/{ID}/wish?start={start}` — want-to-watch (全部页面)

Extract: title, star rating (from special entities), date, comment.

#### Step 4: Fetch Music

Use WebFetch on `https://music.douban.com/people/{ID}/collect?start={start}` — grid mode shows albums with artist and genre.

Also collect:
- `https://music.douban.com/people/{ID}/wish` — want-to-listen

#### Step 5: Fetch Statuses/Dynamics (REQUIRES LOGIN COOKIE)

Statuses (动态/广播) contain the user's complete activity timeline with **star ratings that are NOT visible on collection pages**. This is critical for movies where the collection view often hides ratings.

**This requires the user to provide their `dbcl2` cookie.** Ask the user:
- "你的豆瓣动态数据需要登录才能访问。如果你方便，可以导出浏览器的 dbcl2 cookie 给我。步骤：Chrome → 安装 Cookie-Editor 插件 → 登录豆瓣 → 导出 cookie → 找到 dbcl2 的值。或者你直接手动复制动态内容给我。"

If cookie is provided:
```bash
curl -sL "https://www.douban.com/people/{ID}/statuses?p={page}" \
  -H "Cookie: dbcl2=\"VALUE\"" \
  -H "User-Agent: Mozilla/5.0 ..." \
  -H "Referer: https://www.douban.com/people/{ID}/"
```

**Pagination**: Statuses use `?p=N` (NOT `?start=N`). Pages start at `p=1`. Each page shows ~20 items. Fetch until a page returns 0 unique status IDs.

Extract from each status:
- Action type (看过/想看/想读/在读)
- Item title (book or movie name)
- **Star rating** (HTML entities: `&#9733;` = ★, count 3-5)
- Date/timestamp
- Any comment text

#### Step 6: Fetch Doulists (REQUIRES LOGIN COOKIE)

Doulists (豆列) reveal how the user organizes their cultural consumption:
- `https://www.douban.com/people/{ID}/subject_doulists/book` — book lists
- `https://www.douban.com/people/{ID}/subject_doulists/movie` — movie lists

If a doulist has a specific theme (e.g., "2023待读书目"), fetch its contents — the curation principles are personality signals.

#### Step 7: Fetch Annotations (REQUIRES LOGIN COOKIE)

`https://book.douban.com/people/{ID}/annotation/` — reading notes/highlights. May be empty (0 notes), which is itself a signal.

### Phase 2: Data Structuring

Before analyzing, organize the data into a mental table:

```
Item | Category | Rating | Genre/Tags | Review keywords | Year consumed
```

Note the following patterns in the data *before* jumping to inference:
- Rating distribution shape (flat? skewed high? harsh?)
- Category breakdown (books % / movies % / music %)
- Genre/tag clusters
- Cultural origin clusters (Chinese / translated / foreign-language)
- **Any notable absences** (e.g., "zero poetry", "no films before 2000", "no business/finance books")
- **Want-to-read vs. actually-read ratio** — reveals aspiration vs. execution gap
- **Reading evolution over time** — trace how tastes/concerns shifted across years
- **Self-corrections in reviews** — user editing old reviews to update opinions is a strong signal
- **Taste divergence** — e.g., someone with highly international book taste but exclusively domestic music

### Phase 3: Analysis Rules

**CRITICAL — follow these rules or the output will be Barnum-effect flattery:**

1. **Evidence-before-score rule**: For every dimension score (1-10), cite at least 3 specific items or patterns from the user's data. If you can't find 3, reduce the score or mark confidence as Low.

2. **Contradiction rule**: If signals conflict (e.g., someone who reads ambitious literary fiction but watches only blockbuster action films), present the tension explicitly rather than averaging it away. The tension itself is the insight.

3. **Confidence rule**: Attach a confidence label to every dimension:
   - **High**: 10+ items support the signal, pattern is consistent across categories
   - **Medium**: 3-9 items support it, or mixed signals
   - **Low**: Fewer than 3 items, or data is from a single category

4. **Blind-spot rule**: If a dimension cannot be inferred from the available data, say so explicitly. Example: "Your Douban history doesn't reveal much about Extraversion — your social activity on the platform is minimal, and your media choices don't strongly point either way."

5. **Chinese cultural context**: Interpret the data within Chinese cultural norms. What counts as "literary" or "experimental" or "mainstream" in the Chinese cultural landscape may differ from Western defaults. References to Chinese authors, directors, and cultural movements must be understood accurately.

6. **Base-rate awareness**: Note when a pattern is common among Douban users generally vs. distinctive to this specific person. "Like many Douban users, you favor..." vs. "Unlike most Douban users who tend to..., you..."

7. **Temporal trajectory**: Don't just describe the snapshot — trace the evolution. What did the user read in 2019 vs. 2024? How did their ratings change? This reveals personality development, not just static traits.

8. **Cross-category comparison**: Music vs. books vs. movies may show different facets. Someone's music may be their emotional comfort zone while books are their intellectual frontier. Note this asymmetry.

### Phase 4: Report Generation

Generate the report using the template below. Replace bracketed sections with analysis.

---

## Output Template

```markdown
# 🎭 你的豆瓣人格画像

## 总览

[2-3 sentence synthesis. Start with the most distinctive finding.]

---

## Big Five 人格剖面

| 维度 | 得分 (1-10) | 置信度 | 核心证据 |
|------|------------|--------|---------|
| 开放性 Openness | [N] | [High/Med/Low] | [3 bullet points] |
| 尽责性 Conscientiousness | [N] | [High/Med/Low] | [3 bullet points] |
| 外向性 Extraversion | [N] | [High/Med/Low] | [3 bullet points] |
| 宜人性 Agreeableness | [N] | [High/Med/Low] | [3 bullet points] |
| 情绪稳定性 Neuroticism | [N] | [High/Med/Low] | [3 bullet points] |

### 逐维度解读

**[Openness 开放性 — N/10]**
[1 paragraph that connects the dots. Don't just repeat the evidence — explain what the pattern means.]

**[Conscientiousness 尽责性 — N/10]**
[1 paragraph]

**[Extraversion 外向性 — N/10]**
[1 paragraph]

**[Agreeableness 宜人性 — N/10]**
[1 paragraph]

**[Neuroticism 情绪稳定性 — N/10]**
[1 paragraph]

---

## 价值观取向

| 维度 | 倾向 | 证据 |
|------|------|------|
| 自我超越 vs. 自我增强 | [Leaning] | [1-2 data points] |
| 对变化的开放 vs. 保守 | [Leaning] | [1-2 data points] |
| 智识倾向 vs. 审美倾向 | [Leaning] | [1-2 data points] |

---

## 审美签名

- **复杂度容忍度**：[High/Med/Low] — [1 sentence evidence]
- **感官 vs. 概念**：[Leaning] — [1 sentence evidence]
- **时间取向**：[Pattern] — [1 sentence evidence]
- **文化广度**：[Pattern] — [1 sentence evidence]

---

## 意识形态觉醒轨迹

[If the data spans multiple years, trace how their reading/viewing evolved:
- What was the starting point?
- When and how did key interests emerge?
- What were the turning points?
- Where are they heading?]

## 完整评分生态

| 评分 | 数量 | 占比 | 典型代表 |
|------|------|------|---------|
| ★★★★★ | [N] | [X%] | [2-3 examples] |
| ★★★★ | [N] | [X%] | [theme] |
| ★★★ | [N] | [X%] | [theme] |
| ★★ | [N] | [X%] | [2-3 examples with reasons] |
| ★ | [N] | [X%] | — |

---

## ⚠️ 这不代表什么

[Important caveats, specific to this analysis:]

- 本次分析基于 **[N] 条数据**（[books] 本书 + [movies] 部电影 + [music] 张唱片 + [reviews] 篇书评 + [statuses] 条动态），是较大采样但仍非全貌。
- 文化消费只是人格的一扇窗——它最容易揭示**开放性**和**价值观**，对**外向性**和**情绪稳定性**的推断需更多实际行为数据。
- [Any specific data gaps: missing categories, uncollected data types]
- 豆瓣作为半公开平台，存在社会称许偏差。
- 这个分析是概率性的推测，**不是心理诊断**。

---

## 🔍 有趣发现

[3-7 observations that don't fit neatly into the framework but are worth surfacing:]

1. [Pattern + brief reflection]
2. [Pattern + brief reflection]
3. [Pattern + brief reflection]

---

## 想深入探索？

[2-3 optional follow-up suggestions, tailored to the user's profile:]
```

---

## Edge Cases

| Scenario | Response |
|----------|----------|
| Private profile (WebFetch fails) | Fall back to Path B (curl) automatically |
| book.douban.com returns 403 to WebFetch | Switch to curl with browser headers — this is the most common blocker |
| < 10 items total | Refuse to profile: "I need at least 10 items to find meaningful patterns." Offer guided Q&A to collect more data. |
| All items from one category | Proceed but add strong caveat: "This profile is heavily weighted toward [movies/books]. Your music and other tastes might tell a different story." |
| All ratings are 4-5 stars | Flag it: "Your ratings show very limited differentiation. This itself is a signal — but it limits what I can infer about certain dimensions." |
| Data looks "performative" (all canonical/smart/intellectual works) | Note the possibility of social desirability bias. Be tactful. |
| User asks for MBTI instead of Big Five | Explain: "Big Five is the scientific standard in personality psychology. MBTI has poor test-retest reliability." |
| WebFetch returns JavaScript-rendered incomplete page | Detect by comparing expected vs. actual item count. Fall back to curl. |
| Statuses pagination doesn't work with `?start=` | Try `?p=N` — Douban statuses use a different pagination scheme than collect pages |
| User provides cookie but doulists return 403 | Doulists may require additional session cookies beyond dbcl2. Fall back gracefully. |
| User provides only Want to Read/Watch (no completed items) | This is useful in itself — analyze but heavily caveat: "This is your aspirational self, not your actual consumption." |

## Red Flags

- **Jumping to inference without enumeration**: Don't say "you're high in Openness" before listing specific items that support it.
- **Barnum-effect language**: Avoid vague statements that would apply to anyone. Cite specific works.
- **Psychological jargon without translation**: Write for a general reader. Explain what scores mean in plain Chinese.
- **Ignoring contradictions**: If someone reads dense philosophy but watches only Marvel movies, don't smooth that over — explore it.
- **Confidence inflation**: Don't claim High confidence on a dimension derived from 2 items and a guess.
- **Making up data**: If WebFetch/curl didn't return it and the user didn't say it, don't invent it.
- **Over-pathologizing**: Don't frame personality dimensions as good/bad.
- **Western-centric assumptions**: "Literary fiction" and "experimental music" mean different things in Chinese cultural context.
- **Not collecting want-to-read data**: The ratio of aspirational vs. actual reading is a key conscientiousness/openness signal.
- **Not checking for self-corrections**: User edits to old reviews are growth markers — don't miss them.

## Verification Checklist

Before presenting the final report, confirm:

- [ ] At least 10 distinct items were analyzed
- [ ] Every Big Five dimension has 3+ cited evidence points, OR a blind-spot declaration
- [ ] Every dimension has a confidence label (High/Medium/Low)
- [ ] At least one contradiction or tension is surfaced in the analysis
- [ ] At least 3 "Curious Patterns" are identified
- [ ] The "这并不代表什么" section is present and tailored (not boilerplate)
- [ ] No Barnum-effect statements appear in the report
- [ ] Chinese cultural references are correctly interpreted
- [ ] Scores are based on evidence, not stereotypes about genres
- [ ] Reading/watching evolution over time is analyzed (if data spans multiple years)
- [ ] Cross-category comparisons (books vs. movies vs. music) are considered
- [ ] User was given an opportunity to add more data before finalizing
- [ ] Report invites follow-up rather than claiming to be definitive
