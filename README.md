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

## 🛠 ปรับแต่ง

### เพิ่ม/ลบเหรียญ

แก้ตัวแปร `ASSETS` ใน `report.py`:

```python
ASSETS = [
    ("ETH/USD", "binance", "ETHUSDT"),
    ("ADA/THB", "bitkub", "thb_ada"),
    ("AAPL", "yfinance", "AAPL"),
    # ...
]
```

### เปลี่ยนเวลา

แก้ cron ใน `.github/workflows/daily-report.yml`:
- `'0 0 * * *'` = 7:00 ICT (default)
- `'30 22 * * *'` = 5:30 ICT
- ใช้เครื่องช่วย: https://crontab.guru/

> หมายเหตุ: GitHub Actions อาจ delay 5-15 นาที ในช่วงโหลดสูง

### เปลี่ยนค่า EMA

แก้ที่หัว `report.py`:
```python
FAST_EMA = 12
SLOW_EMA = 26
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
