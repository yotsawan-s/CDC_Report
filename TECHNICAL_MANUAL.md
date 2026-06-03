# 📘 Technical Manual — CDC Report Project

คู่มือทางเทคนิคสำหรับโปรเจกต์ CDC ActionZone Daily Report — อธิบายโครงสร้างไฟล์, การไหลของข้อมูล, และวิธีแก้ไขแต่ละจุด

> 📂 **Path:** `D:\Claude AI_Work\CDC_Report`
> 🌐 **Repo:** https://github.com/yotsawan-s/CDC_Report
> 📦 **Live:** https://yotsawan-s.github.io/CDC_Report/

---

## 📑 สารบัญ

1. [ภาพรวมระบบ](#1-ภาพรวมระบบ)
2. [โครงสร้างโฟลเดอร์](#2-โครงสร้างโฟลเดอร์)
3. [การไหลของข้อมูล](#3-การไหลของข้อมูล)
4. [รายละเอียดแต่ละไฟล์](#4-รายละเอียดแต่ละไฟล์)
5. [Common edit scenarios](#5-common-edit-scenarios)
6. [การพัฒนาในเครื่อง](#6-การพัฒนาในเครื่อง)
7. [Deployment & Workflows](#7-deployment--workflows)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. ภาพรวมระบบ

โปรเจกต์นี้ทำงาน 3 อย่างหลัก:

| ฟังก์ชัน | ทำงานเมื่อไหร่ | output |
|---|---|---|
| 📊 **คำนวณสัญญาณ CDC** (BUY/SELL/HOLD) | 6:20 + 11:20 ICT ทุกวัน | ตารางสัญญาณ + sparkline 14 วัน |
| 📰 **สรุปข่าววิเคราะห์ตลาด** *(ถ้ามี API key)* | พร้อมรอบสัญญาณ | 5 ข่าวต่อวัน แปลไทยโดย Claude |
| 🔄 **Resume ข่าวที่ token หมด** | ทุก 30 นาที | เก็บข่าวที่ถูก defer ไว้ |

ผลลัพธ์ทั้งหมดถูก render เป็น **`docs/index.html`** ไฟล์เดียว → GitHub Pages serve ออกไป

---

## 2. โครงสร้างโฟลเดอร์

```
CDC_Report/
│
├── 🎛️ config.py                  ⭐ ทุกค่าที่ปรับบ่อย แก้ที่นี่ที่เดียว
├── 🎬 report.py                  orchestrator หลัก ~100 บรรทัด
├── 📦 requirements.txt           Python dependencies
├── 📕 README.md                  เอกสารผู้ใช้
├── 📗 SETUP_GUIDE_TH.md          คู่มือ setup ครั้งแรก
├── 📘 TECHNICAL_MANUAL.md        เอกสารนี้
├── 🚫 .gitignore                 ไฟล์ที่ไม่ commit
│
├── 📥 data/                      ดึงราคาจาก exchanges
│   ├── __init__.py              dispatcher fetch_data(source, symbol)
│   ├── binance.py               BTC/USD ผ่าน data-api.binance.vision
│   ├── bitkub.py                BTC/DOGE/KUB THB
│   └── yfinance_src.py          ทอง + หุ้นเทค US
│
├── 🧮 signals/                   CDC ActionZone logic
│   ├── __init__.py
│   └── cdc.py                   calculate_signals_history()
│
├── 📰 news/                      ฟีเจอร์ข่าว (ทั้งหมดอยู่ที่นี่)
│   ├── __init__.py              expose build_daily_news
│   ├── pipeline.py              orchestrator: fetch → rank → summarize → cache
│   ├── sources.py               RSS parser
│   ├── rank.py                  ให้คะแนน relevance vs ASSETS
│   ├── fetch.py                 extract body via r.jina.ai
│   ├── summarize.py             ⭐ Claude API + rate-limit handling
│   ├── cache.py                 ⭐ state machine ใน docs/news.json
│   ├── exceptions.py            TokenLimitDeferred, FetchError, SummarizeError
│   ├── resume.py                CLI สำหรับ retry workflow
│   └── prompts/
│       └── summarize_th.txt     ⭐ prompt แปลไทย (แก้ง่าย ไม่ต้อง re-deploy)
│
├── 🎨 render/                    ทำ HTML จาก data
│   ├── __init__.py
│   ├── builder.py               Jinja2 env + inline CSS/JS + render()
│   ├── helpers.py               format_price, sparkline, history_cells, ...
│   └── templates/
│       ├── layout.html          โครงหลัก {% include %} partials
│       ├── styles.css           ⭐ CSS ทั้งหมด แต่งสีที่นี่
│       ├── app.js               theme toggle + expand row JS
│       └── partials/
│           ├── header.html              ส่วนหัว + theme button
│           ├── summary_cards.html       3 card: BUY/HOLD/SELL count
│           ├── alert.html               🚨 banner สัญญาณใหม่
│           ├── news_section.html        ⭐ section ข่าว (ทั้งหมด)
│           ├── news_card.html           ⭐ card ข่าว 1 ใบ
│           ├── signal_table.html        ตารางสินทรัพย์
│           ├── signal_row.html          แถวสรุป 1 แถว
│           ├── detail_row.html          แถว detail (เปิดเมื่อคลิก)
│           └── footer.html              footer
│
├── 🚀 .github/workflows/         GitHub Actions
│   ├── daily-report.yml         รันทุกเช้า (6:20 + 11:20 ICT)
│   └── retry-news.yml           รันทุก 30 นาที — resume pending
│
├── 📤 docs/                      output (GitHub Pages serve)
│   ├── index.html               ❌ gitignored — regenerate ทุกรอบ
│   ├── data.json                ❌ gitignored — debug data
│   └── news.json                ✅ tracked — state machine (สำคัญ)
│
└── 📂 ShareFiles/                placeholder (legacy, อย่าลบ)
```

> ⭐ = ไฟล์ที่แก้บ่อย / สำคัญ

---

## 3. การไหลของข้อมูล

### รอบหลัก (`daily-report.yml`)

```
┌──────────────────────────────────────────────────────────────┐
│ 1. GitHub Actions ทริกเกอร์ (cron 23:20 UTC = 06:20 ICT)     │
└──────────┬───────────────────────────────────────────────────┘
           ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. checkout repo (รวม docs/news.json จากรอบก่อน)             │
└──────────┬───────────────────────────────────────────────────┘
           ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. python report.py                                          │
│                                                              │
│    a) compute_signals()                                      │
│       config.ASSETS → data.fetch_data() → signals.cdc        │
│       → list of {name, history[14]}                          │
│                                                              │
│    b) build_news_safely() (skip ถ้าไม่มี ANTHROPIC_API_KEY)  │
│       news.pipeline.build_daily_news():                      │
│         1. news.cache.load()  ← docs/news.json               │
│         2. news.sources.fetch_all_rss()  (5 แหล่ง)           │
│         3. news.rank.pick_top(n=5, diverse=True)             │
│         4. for each picked:                                  │
│            news.fetch.extract_body(url)  (r.jina.ai)         │
│            news.summarize.summarize()                        │
│            ├─ ok → cache.mark_summarized()                   │
│            ├─ TokenLimitDeferred → cache.mark_pending()      │
│            └─ SummarizeError → skip                          │
│         5. news.cache.save()                                 │
│                                                              │
│    c) render.builder.build_html()                            │
│       → Jinja2 render layout.html + inline CSS/JS            │
│       → docs/index.html                                      │
│                                                              │
│    d) write docs/data.json (debug)                           │
└──────────┬───────────────────────────────────────────────────┘
           ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. git commit docs/news.json + push (state ขั้นต่อไป)        │
│ 5. upload docs/ as Pages artifact → deploy                   │
└──────────────────────────────────────────────────────────────┘
```

### รอบ retry (`retry-news.yml` ทุก 30 นาที)

```
1. checkout (พร้อม docs/news.json)
2. python -c "has_due_pending()"
   ├─ False → exit 1 → step ถัดไปทั้งหมด skip (no-op)
   └─ True  → continue
3. python -m news.resume
   - load pending items ที่ retry_after <= now()
   - call Claude → mark_summarized() หรือ mark_pending() อีก
4. python report.py --news-only
   - reuse docs/data.json (signals) — ไม่ refetch market
   - rebuild docs/index.html
5. commit + push + deploy
```

---

## 4. รายละเอียดแต่ละไฟล์

### 🎛️ `config.py`

ค่าทุกค่าที่ต้องปรับบ่อย รวมที่นี่ ไม่ต้องเปิดไฟล์อื่น

| ตัวแปร | ความหมาย |
|---|---|
| `ASSETS` | list of `(display_name, source, symbol)` — เพิ่ม/ลบเหรียญที่นี่ |
| `FAST_EMA`, `SLOW_EMA` | EMA periods (default 12/26) |
| `SMOOTH`, `LOOKBACK_DAYS`, `HISTORY_DAYS` | CDC params |
| `OUTPUT_DIR` | path output (default `docs/`) |
| `NEWS_ENABLED` | toggle ฟีเจอร์ข่าว |
| `NEWS_COUNT` | จำนวนข่าว/วัน (default 5) |
| `NEWS_CACHE_DAYS` | เก็บประวัติข่าวกี่วัน |
| `NEWS_SOURCES` | list of `{name, rss}` แหล่งข่าว |
| `NEWS_ASSET_ALIASES` | keyword สำหรับกรองข่าวที่เกี่ยวข้อง |
| `CLAUDE_MODEL` | `claude-sonnet-4-6` |
| `CLAUDE_MAX_TOKENS` | จำกัด output token (default 1500) |
| `CLAUDE_INLINE_RETRY_WAIT` | เวลาสูงสุดที่ยอม sleep ใน process (90 วิ) |

---

### 🎬 `report.py`

Orchestrator — เรียก module ตามลำดับ ไม่มี logic ของ business เอง

**Functions:**
- `compute_signals()` — for ทุก asset → fetch + calculate, return list
- `load_cached_signals()` — อ่าน `docs/data.json` แทน (สำหรับ `--news-only`)
- `build_news_safely()` — wrapper รอบ `news.build_daily_news()` ที่ swallow exception (ถ้า news ล้ม รายงานหลักยังไป)
- `write_outputs()` — เขียน `index.html` + `data.json`
- `main()` — entry point มี argparse `--news-only`

**Modes:**
- `python report.py` — full run
- `python report.py --news-only` — ใช้ signals จาก cache, รัน news ใหม่อย่างเดียว (retry workflow ใช้)

---

### 📥 `data/`

แต่ละ source แยกไฟล์ — เพิ่ม source ใหม่ = สร้างไฟล์ใหม่ + register ใน `__init__.py`

**Contract:** ทุกฟังก์ชันคืน DataFrame ที่มี 2 columns: `date`, `close`

| ไฟล์ | API | หมายเหตุ |
|---|---|---|
| `binance.py` | `data-api.binance.vision` | ใช้ตัวนี้แทน `api.binance.com` เพราะ blocked จาก US IP (GitHub Actions runs on MS US infra) |
| `bitkub.py` | `api.bitkub.com/tradingview/history` | คืน OHLC arrays |
| `yfinance_src.py` | `yfinance` library | สำหรับ ทอง + หุ้น US |

---

### 🧮 `signals/cdc.py`

Pure logic ของ CDC ActionZone V3 (port จาก Pine Script ของ piriya33)

**Functions:**
- `ema(series, length)` — exponential moving average
- `rsi(series, period=14)` — Wilder's RSI (ใช้ EMA-style smoothing) → แสดงใน detail row
- `_classify(price, fast, slow)` — helper map ค่า 1 แท่ง → `(zone, signal, color)` (ใช้ซ้ำทั้งตอน build history และตอนไล่ย้อนหา B/S ล่าสุด)
- `calculate_signals_history(df, n_history)` — คำนวณสัญญาณ n_history แท่งล่าสุด

**Output element:**
```python
{
  "date": "2026-05-18", "close": 76349.66,
  "fast_ma": 75000.0, "slow_ma": 73000.0,
  "zone": "Green", "signal": "BUY", "color_emoji": "🟢",
  "trend": "Bullish",
  "rsi": 62.5,                               # ทุกแท่ง (NaN → fallback 50.0)
  "fresh_buy": False, "fresh_sell": False,  # last item only
}
```

**Zone logic** (สำคัญ — ตาม Pine Script ต้นฉบับ):

| Condition | Zone | Signal |
|---|---|---|
| `fast > slow AND price > fast` | Green | BUY |
| `fast < slow AND price < fast` | Red | SELL |
| `fast > slow AND slow < price < fast` | Yellow | HOLD |
| `fast > slow AND price < slow` | Orange | HOLD |
| `fast < slow AND price > fast` | Blue | HOLD |
| `fast < slow AND fast < price < slow` | LightBlue | HOLD |

**NEW logic** (`fresh_buy` / `fresh_sell` — ใส่เฉพาะแท่งล่าสุด):
- เป็น `True` เฉพาะตอนสัญญาณ BUY/SELL **สลับจริง** เทียบกับ B/S ครั้งล่าสุด
- ไล่ย้อนหลังบน**ข้อมูลเต็ม** (ไม่ใช่แค่ window 14 แท่ง) เพื่อ **ข้าม HOLD** — HOLD ที่คั่นยาวกี่วันก็ไม่ทำให้ลืม B/S ก่อนหน้า
- ตัวอย่าง `S,B,H,H,B` → B ตัวท้าย **ไม่** ใช่ของใหม่ (B/S ล่าสุดก่อนหน้าก็คือ B); จะ NEW ก็ต่อเมื่อสลับ B↔S จริงเท่านั้น

---

### 📰 `news/`

#### `pipeline.py` — ตัวประสานหลัก
- `build_daily_news()` — รันรอบเช้า
- `resume_pending()` — รันรอบ retry

#### `sources.py` — RSS parser
- `fetch_all_rss(max_per_source=15)` — ดึงทุก feed → list of items
- คืน `{id (sha1 hash), url, source, title, summary, published}`

#### `rank.py` — ให้คะแนน
- `score_and_tag(item)` — count alias matches + ใน title คูณ 2
- `pick_top(items, n, diverse_sources)` — sort by score, cap 2/source

#### `fetch.py` — ดึง body
- `extract_body(url, fallback)` — proxy ผ่าน `r.jina.ai` (ฟรี, รองรับ paywall เบื้องต้น)
- Fallback → RSS summary ถ้า proxy fail

#### `summarize.py` — Claude API ⭐
- `summarize(item, body, asset_keys, client)` — 3 retries
- จัดการ:
  - `RateLimitError` + `retry_after ≤ 90s` → sleep + retry
  - `RateLimitError` + `retry_after > 90s` → raise `TokenLimitDeferred`
  - `APIStatusError 529/503` → treat as defer (10 min)
  - `JSONDecodeError` → 1 retry

#### `cache.py` — State machine ⭐
ทุก item ใน `docs/news.json` มี `status`:
- `"summarized"` — ครบ render ได้
- `"pending"` — body fetched, รอ retry หลัง `retry_after`

**Functions:**
| ฟังก์ชัน | ใช้เมื่อ |
|---|---|
| `load()`, `save(state)` | i/o |
| `trim(state, days)` | ตัดของเก่ากว่า NEWS_CACHE_DAYS |
| `existing_ids(state)` | skip ข่าวที่เคยเห็น |
| `mark_pending(state, item, body, retry_after_seconds)` | summarize ล้มเหลว defer |
| `mark_summarized(state, item, summary_dict)` | สำเร็จ |
| `due_pending(state)` | items ที่ retry_after ≤ now |
| `summarized_today(state)` | สำหรับ render |
| `pending_count(state)` | สำหรับ banner |

#### `exceptions.py`
- `FetchError` — ดึง body ไม่ได้
- `TokenLimitDeferred(retry_after_seconds)` — Claude rate-limit หนัก
- `SummarizeError` — error อื่นๆ ของ Claude

#### `resume.py` — CLI สำหรับ retry workflow
- `has_due_pending()` → bool (workflow ใช้เช็คก่อนรัน)
- `main()` — เรียก `pipeline.resume_pending()`
- รัน: `python -m news.resume`

#### `prompts/summarize_th.txt`
Prompt แม่แบบ ใช้ Python `.format()` ใส่ `{assets}`, `{source}`, `{title}`, `{body}`
แก้ tone, format, ภาษาที่ใช้ ได้ที่ไฟล์นี้ — **ไม่ต้อง re-deploy** (รอบถัดไปก็ใช้ทันที)

---

### 🎨 `render/`

#### `builder.py`
- สร้าง Jinja2 `Environment` + register helpers เป็น globals
- `build_html(all_results, news)` — render layout.html → string
- **Inline CSS/JS** — อ่านไฟล์ `styles.css` + `app.js` มาแปะใน `<style>` + `<script>` ตอน build (single-file output)

#### `helpers.py` — เปิดเป็น Jinja globals
| ฟังก์ชัน | ใช้ทำอะไร |
|---|---|
| `format_price(p)` | 1,234.56 หรือ 0.00012345 |
| `format_date_short(date_str)` | "18 May", "today", days_ago |
| `build_sparkline(history)` | SVG กราฟเส้นเล็ก 14 วัน |
| `build_history_cells(history)` | แถวสี่เหลี่ยมเล็กๆ B/S/H |
| `asset_chart_id(name)` | DOM-safe id "XAU/USD (Gold)" → "XAU_USD_Gold" |
| `pct_change(history)` | "↑ 2.34%", "pct-up" |
| `rsi_icon_and_class(rsi_val)` | RSI → `(icon, css_class, label)`: ≤30 🟢 Oversold · >70 🔴 Overbought · กลาง 🟡 Neutral |

#### `templates/layout.html`
- โครงหลักเพียง 27 บรรทัด
- `{{ inline_css }}` / `{{ inline_js }}` — builder ใส่ให้
- `{% include %}` partials ตามลำดับ:
  1. header → 2. summary_cards → 3. alert → 4. **news_section** → 5. signal_table → 6. footer

#### `templates/styles.css`
CSS ทั้งหมด ~550 บรรทัด แบ่งเป็น:
1. Design tokens (light + dark theme variables)
2. Header / Summary cards / Alert
3. Table (signal rows, expand, detail)
4. **News section** (cards, asset chips, key points)
5. Footer / Responsive (`@media max-width:640px`)

#### `templates/app.js`
- Theme toggle (localStorage)
- Zebra striping
- **Generic expand**: `.row-clickable` + `data-target` → toggle target's display
  - ใช้ pattern เดียวกันทั้ง signal rows และ news cards

#### `templates/partials/`
แต่ละ partial มี **single responsibility**:

| Partial | ตัวแปร context ที่ใช้ |
|---|---|
| `header.html` | `date_str`, `fast_ema`, `slow_ema` |
| `summary_cards.html` | `summary.buys/holds/sells` |
| `alert.html` | `fresh_signals` (list of (name, sig)) |
| `news_section.html` | `news['items']`, `news.pending_count` |
| `news_card.html` | `n.title_th`, `n.summary_th`, `n.key_points_th`, ... |
| `signal_table.html` | `assets` (list) — loop เรียก signal_row + detail_row |
| `signal_row.html` | `r` (single asset), helpers |
| `detail_row.html` | `r`, `fast_ema`, `slow_ema`, `history_days` — แสดง EMA, RSI(14) + label, ประวัติ |
| `footer.html` | `history_days` |

> ⚠️ ระวัง Jinja: `news.items` ชนกับ `dict.items()` method → ใช้ `news['items']` ใน template

---

### 🚀 `.github/workflows/`

#### `daily-report.yml`
```yaml
schedule:
  - cron: '20 23 * * *'   # 06:20 ICT
  - cron: '20 4 * * *'    # 11:20 ICT
permissions:
  contents: write   # commit docs/news.json
  pages: write
  id-token: write
```

Steps: checkout → setup python → install → **`python report.py`** (with `ANTHROPIC_API_KEY` env) → commit news.json → upload Pages artifact → deploy

#### `retry-news.yml`
```yaml
schedule:
  - cron: '*/30 * * * *'  # ทุก 30 นาที
```

Steps: checkout → install → **`has_due_pending()`** (exit 1 = no-op) → ถ้ามี → `python -m news.resume` → `python report.py --news-only` → commit + deploy

`concurrency: pages` ทำให้ทั้งสอง workflow ไม่รันพร้อมกัน

---

### 📤 `docs/`

| ไฟล์ | tracked? | คำอธิบาย |
|---|---|---|
| `index.html` | ❌ | ผลลัพธ์สุดท้ายที่ Pages serve regenerate ทุกรอบ |
| `data.json` | ❌ | signal history + last update timestamp (debug) |
| `news.json` | ✅ | state machine cache — commit กลับ repo เพื่อให้ retry workflow อ่านได้ |

---

## 5. Common edit scenarios

### ➕ เพิ่มเหรียญใหม่
```python
# config.py
ASSETS = [
    # ...
    ("ETH/USD", "binance", "ETHUSDT"),
]
# ถ้าเปิดข่าวด้วย
NEWS_ASSET_ALIASES["ETH"] = ["ethereum", "eth", "vitalik"]
```

### 🎨 เปลี่ยนสี theme
แก้ `:root` หรือ `[data-theme="dark"]` ใน `render/templates/styles.css`

### 📝 ปรับ tone ของบทวิเคราะห์
แก้ `news/prompts/summarize_th.txt` → push → รอบหน้าใช้ทันที (ข่าวเก่าใน cache ไม่เปลี่ยน)

### 📰 เพิ่มแหล่งข่าว
```python
# config.py
NEWS_SOURCES.append(
    {"name": "Bloomberg", "rss": "https://feeds.bloomberg.com/markets/news.rss"}
)
```

### ⏰ เปลี่ยนเวลารัน
แก้ `cron` ใน `.github/workflows/daily-report.yml`
ใช้ https://crontab.guru/ ช่วย

### 🔇 ปิดข่าวชั่วคราว
```python
# config.py
NEWS_ENABLED = False
```

### 🗑️ ล้าง cache ข่าวเริ่มใหม่
ลบไฟล์ `docs/news.json` แล้ว push — รอบถัดไปจะสร้างใหม่

---

## 6. การพัฒนาในเครื่อง

### Setup ครั้งแรก
```powershell
cd "D:\Claude AI_Work\CDC_Report"
py -3.10 -m pip install -r requirements.txt
```

> ⚠️ **อย่าใช้ Python 3.13 จาก Microsoft Store** — pip install ทำไม่ได้
> ใช้ `py -3.10` (regular installer) เท่านั้น

### รันทดสอบ
```powershell
$env:PYTHONIOENCODING="utf-8"     # PowerShell — กัน emoji ใน console crash
py -3.10 report.py                # full run
py -3.10 report.py --news-only    # ทดสอบ retry flow
py -3.10 -m news.resume           # ทดสอบ resume entry
```

### ทดสอบฟีเจอร์ข่าวในเครื่อง
```powershell
$env:ANTHROPIC_API_KEY="sk-ant-..."
py -3.10 report.py
```

### Preview เว็บในเครื่อง
```powershell
py -3.10 -m http.server 8765 --directory docs
# เปิด http://localhost:8765/
```

---

## 7. Deployment & Workflows

### Secrets ที่ต้องตั้งบน GitHub
**Settings → Secrets and variables → Actions → New repository secret**

| Name | Value | จำเป็น? |
|---|---|---|
| `ANTHROPIC_API_KEY` | `sk-ant-...` | ไม่ (ถ้าไม่ตั้ง = ปิดข่าว) |

### Flow การ deploy
```
git add .
git commit -m "ข้อความ"
git push                              # → trigger workflow
                                      # → 1-3 นาที → Pages อัพเดท
```

### Manual trigger
GitHub → Actions tab → เลือก workflow → Run workflow

### ดู log
GitHub → Actions → คลิก run ล่าสุด → expand step "Generate report"

---

## 8. Troubleshooting

### News section ไม่ขึ้นบนเว็บ
- ดู log workflow → ถ้าเห็น `⚠️ ข้าม news section: ANTHROPIC_API_KEY not set` → ตั้ง secret
- ถ้าเห็น `🔄 deferred` → token หมด รอ retry workflow มาเก็บ (≤30 นาที)
- ถ้าเห็น `RSS fetch failed` → แหล่งข่าวล่ม (ไม่ critical, รอบหน้าได้)

### Asset ขึ้น "⚠️"
แหล่งข้อมูล (binance/bitkub/yfinance) ตอบไม่ทัน — ปกติ รอบหน้าได้

### Commit ไม่ผ่านเพราะ docs/news.json conflict
รอบ daily + รอบ retry แก้ไฟล์เดียวกัน — `concurrency: pages` ป้องกันได้แต่ถ้ายัง conflict:
```powershell
git pull --rebase
git push
```

### Local run: `ModuleNotFoundError: pandas`
ใช้ Python ผิดตัว — ต้องเป็น `py -3.10` ไม่ใช่ Store edition

### Local run: `UnicodeEncodeError`
ลืม set `PYTHONIOENCODING=utf-8`

### Expand row ไม่ทำงาน
ตรวจว่า `app.js` มี `.row-clickable` listener — generic pattern ใช้กับทั้ง signal row และ news card

---

## 📎 References

- **CDC ActionZone V3 logic:** Pine Script โดย piriya33 — https://www.tradingview.com/u/piriya33/ (MPL 2.0)
- **r.jina.ai** — ฟรี article reader: https://jina.ai/reader/
- **Anthropic API docs:** https://docs.anthropic.com/
- **Jinja2 docs:** https://jinja.palletsprojects.com/
