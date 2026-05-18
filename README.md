# 📊 CDC ActionZone Daily Report (Web Version)

ระบบสร้างรายงาน BUY/SELL/HOLD ทุกวัน **ผ่านเว็บไซต์ของตัวเอง** (ฟรี ไม่ต้องเชื่อมต่ออีเมล)

ระบบจะ:
- รันอัตโนมัติทุกวัน 7:00 น. (เวลาไทย) บน GitHub
- คำนวณสัญญาณ CDC ActionZone ของสินทรัพย์ที่กำหนด
- สร้าง `index.html` ใหม่ → publish ขึ้น GitHub Pages
- คุณ bookmark URL ไว้ที่มือถือ/คอม → กดเข้าไปดูได้ทุกเมื่อ

> **URL ตัวอย่าง:** `https://yourname.github.io/cdc-report/`

## 🎯 สินทรัพย์ที่ติดตาม

| Symbol | แหล่งข้อมูล |
|---|---|
| BTC/USD | Binance |
| BTC/THB | Bitkub |
| DOGE/THB | Bitkub |
| XAU/USD (ทอง) | Yahoo Finance (GC=F) |
| TSM, AMD, NVDA, TSLA, GOOGL | Yahoo Finance |

> แก้รายการได้ที่ตัวแปร `ASSETS` ใน `report.py`

## ⚡ ฟีเจอร์ของหน้าเว็บ

- **ตารางสรุป** — ราคา · สัญญาณ · zone
- **NEW badge** — โชว์เฉพาะวันที่เพิ่งเปลี่ยนสัญญาณ
- **Sparkline** — กราฟเส้นเล็ก 14 วันข้างชื่อแต่ละสินทรัพย์
- **คลิกแถวเพื่อดูรายละเอียด** — EMA12/26, ประวัติสัญญาณรายวัน 14 วัน
- **📰 ข่าววิเคราะห์ตลาด** *(ทางเลือก)* — Claude สรุปข่าวจาก Reuters/CNBC/CoinDesk/MarketWatch เป็นภาษาไทย กดไอคอนเพื่ออ่านบทวิเคราะห์เต็ม + ประเด็นสำคัญ
- **Mobile responsive** — เปิดบนมือถือก็สวย
- **Auto refresh** — refresh ทุก 1 ชม.

## ⚙️ Setup (ครั้งเดียว ใช้เวลา ~5-7 นาที)

ดูรายละเอียดทีละขั้นที่ **`SETUP_GUIDE_TH.md`**

โดยสรุป:
1. สร้าง repo ใหม่บน GitHub
2. อัพโหลดไฟล์โปรเจกต์ทั้งหมด
3. เปิด GitHub Pages ใน Settings
4. ทดสอบ Run workflow
5. Bookmark URL ที่ได้

## 📁 โครงสร้างโปรเจกต์ (หลัง refactor)

```
CDC_Report/
├── config.py              # 🎛️ ทุกค่าที่ปรับบ่อย — แก้ที่นี่ที่เดียว
├── report.py              # 🎬 orchestrator (~90 บรรทัด)
├── data/                  # 📥 fetch ราคาจาก binance / bitkub / yfinance
├── signals/cdc.py         # 🧮 CDC ActionZone V3 logic
├── news/                  # 📰 ข่าว — fetch + rank + Claude summarize + retry state
│   ├── prompts/           #    prompt แปลไทย (text file — แก้ง่าย)
│   ├── pipeline.py        #    main + resume
│   ├── summarize.py       #    Claude API + rate-limit handling
│   └── cache.py           #    docs/news.json state machine
├── render/
│   ├── builder.py         # 🎨 Jinja2 render + inline CSS/JS
│   └── templates/
│       ├── layout.html, styles.css, app.js
│       └── partials/      # header, summary_cards, alert, news_*, signal_table, ...
└── .github/workflows/
    ├── daily-report.yml   # รันทุกเช้า — full pipeline
    └── retry-news.yml     # รันทุก 30 นาที — resume news ที่ token deferred
```

**แก้จุดไหน กระทบจุดเดียว:**
| อยากแก้ | ไปที่ |
|---|---|
| เพิ่ม/ลบเหรียญ, ค่า EMA, แหล่งข่าว | [`config.py`](config.py) |
| Prompt ภาษาไทย | [`news/prompts/summarize_th.txt`](news/prompts/summarize_th.txt) |
| สี/font/layout | [`render/templates/styles.css`](render/templates/styles.css) |
| ข้อความ section ต่างๆ | [`render/templates/partials/`](render/templates/partials/) |
| เวลา cron | [`.github/workflows/daily-report.yml`](.github/workflows/daily-report.yml) |

## 🛠 ปรับแต่งบ่อยๆ

### เพิ่ม/ลบเหรียญ

แก้ตัวแปร `ASSETS` ใน [`config.py`](config.py):

```python
ASSETS = [
    ("ETH/USD", "binance", "ETHUSDT"),
    ("ADA/THB", "bitkub", "ADA_THB"),
    ("AAPL", "yfinance", "AAPL"),
    # ...
]
```

> ถ้าเปิดฟีเจอร์ข่าว อย่าลืมเพิ่ม alias ใน `NEWS_ASSET_ALIASES` ด้วย เพื่อให้กรองข่าวที่เกี่ยวข้องได้

### เปลี่ยนเวลา

แก้ cron ใน `.github/workflows/daily-report.yml`:
- `'20 23 * * *'` = 6:20 ICT (default)
- `'30 22 * * *'` = 5:30 ICT
- ใช้เครื่องช่วย: https://crontab.guru/

### เปลี่ยนค่า EMA

แก้ที่ `config.py`:
```python
FAST_EMA = 12
SLOW_EMA = 26
```

### ปิด/เปิดฟีเจอร์ข่าว

แก้ `config.py`:
```python
NEWS_ENABLED = False   # ปิดข่าว ใช้แค่ BUY/SELL/HOLD
```

## 🆚 เปรียบเทียบกับเวอร์ชัน Email

| | Email Version | **Web Version (เวอร์ชันนี้)** |
|---|---|---|
| ต้องตั้ง Gmail App Password | ✅ ต้อง | ❌ ไม่ต้อง |
| ต้องใส่ Secrets | 3 ตัว | 0 ตัว |
| ดูย้อนหลังได้ | ❌ | ✅ ดูใน Gmail |
| คลิกขยายดูรายละเอียด | ❌ | ✅ |
| Sparkline | ❌ | ✅ |
| ดูบนมือถือ | ✅ | ✅ |
| ความเร็วการ setup | 15-20 นาที | **5-7 นาที** |

## 📜 Credit

- CDC ActionZone V3 — [piriya33](https://www.tradingview.com/u/piriya33/) (MPL 2.0)
- ⚠️ เพื่อการศึกษาเท่านั้น ไม่ใช่คำแนะนำการลงทุน
