# 🚀 คู่มือ Setup — Web Version

setup ตั้งแต่เริ่ม จนได้ URL ของตัวเอง — ใช้เวลา **5-7 นาที** ทำผ่านเบราว์เซอร์ทั้งหมด **ไม่ต้องลงโปรแกรมอะไรเลย**

> ✅ คุณมีบัญชี GitHub แล้ว เริ่มที่ขั้น 1 ได้เลย
>
> 🎯 **ไม่ต้องตั้ง Gmail** เพราะเวอร์ชันนี้ไม่ส่งอีเมล — ดูผ่านเว็บอย่างเดียว

---

## ขั้นที่ 1️⃣ — สร้าง Repository *(1 นาที)*

1. มุมขวาบน GitHub กด **➕** → **New repository**
2. กรอก:
   - **Repository name:** `cdc-report` *(ชื่อนี้จะอยู่ใน URL ตลอดไป — ตั้งสั้นๆ ได้)*
   - **Public** ⚠️ — **ต้องเลือก Public** เพราะ GitHub Pages ฟรีต้องการ Public repo
   - ⚠️ **อย่าติ๊ก** README / gitignore / license
3. กด **Create repository** สีเขียว

> 💡 อยากซ่อนไม่ให้คนอื่นเห็น? Public repo ก็เห็นได้แค่คนรู้ URL ของหน้าเว็บ และโค้ดในนี้ไม่มีรหัสผ่าน

---

## ขั้นที่ 2️⃣ — อัพโหลดไฟล์ *(2 นาที)*

### 2.1 แตก zip

ดับเบิลคลิก `cdc-report-v2.zip` จะได้ 4 อย่าง:
- `report.py`
- `requirements.txt`
- `README.md`
- `.github/` ← **โฟลเดอร์ซ่อน สำคัญมาก!**

> 🚨 **ต้องเปิดให้เห็นไฟล์ซ่อนก่อน:**
> - **macOS Finder:** กด `Cmd + Shift + .`
> - **Windows File Explorer:** View → ติ๊ก **Hidden items**

### 2.2 อัพผ่านเว็บ

1. ในหน้า repo ที่เพิ่งสร้าง → คลิกลิงก์ **"uploading an existing file"**
   - หาไม่เจอ? เติม `/upload/main` ต่อท้าย URL
2. **เลือกไฟล์ทั้งหมด** (Ctrl+A หรือ Cmd+A) → ลากใส่หน้าเว็บ
3. **เช็คว่ามี `.github/workflows/daily-report.yml`** ในรายการ ⚠️
4. commit message: `Initial commit`
5. กด **Commit changes** สีเขียว

> ✅ กลับไปหน้า repo ต้องเห็นโฟลเดอร์ `.github` ถ้าไม่เห็น = อัพไม่สำเร็จ ทำใหม่

---

## ขั้นที่ 3️⃣ — เปิด GitHub Pages *(1 นาที)*

> ขั้นนี้คือ "เปิดเว็บ" ของคุณ

1. ในหน้า repo → กดแท็บ **Settings**
2. แถบซ้ายมือ → **Pages**
3. ในส่วน **Build and deployment** → **Source** → เลือก **GitHub Actions**

   หน้าตาที่ถูกต้อง:
   ```
   Source: GitHub Actions ▼
   ```

4. **ไม่ต้องกด Save** — เลือกปุ๊บมีผลทันที

> ที่เลือก "GitHub Actions" ไม่ใช่ "Deploy from a branch" เพราะ workflow ของเราจะ deploy ให้เอง

---

## ขั้นที่ 4️⃣ — รันครั้งแรกเพื่อสร้างเว็บ *(2-3 นาที)*

1. กดแท็บ **Actions**
2. ครั้งแรกอาจมีปุ่ม **"I understand my workflows, go ahead and enable them"** → กด
3. แถบซ้ายมือ → คลิก **Daily CDC Report**
4. กลางหน้า → **Run workflow** ▼ → main → กด **Run workflow** สีเขียว
5. รอ 3-5 วิ → กด **F5** → จะเห็น run ใหม่ที่ขึ้นวงกลมเหลืองหมุน 🟡
6. คลิกเข้าไปดู run นั้น → รอ ~1-2 นาที → ขึ้น **✅ ติ๊กเขียว** ทุก step

   ทั้ง 4 step ต้องเขียวหมด:
   - ✅ Generate report
   - ✅ Setup Pages
   - ✅ Upload artifact
   - ✅ Deploy to GitHub Pages

---

## ขั้นที่ 5️⃣ — เปิดเว็บของคุณ! 🎉 *(30 วินาที)*

1. กลับไป **Settings** → **Pages**
2. ที่ด้านบนจะเห็นข้อความเขียวๆ:

   ```
   ✅ Your site is live at https://yourname.github.io/cdc-report/
   ```

3. กดปุ่ม **Visit site** หรือคัดลอก URL นั้น
4. **เปิดดู** → จะเห็นรายงาน CDC ของวันนี้!

5. **Bookmark URL ไว้:**
   - **มือถือ Safari (iOS):** กด Share → "Add to Home Screen" → ได้ icon บนหน้าจอเหมือนแอป
   - **มือถือ Chrome (Android):** เมนู ⋮ → "Add to Home screen"
   - **Desktop:** Ctrl+D หรือ Cmd+D

✅ **เสร็จเรียบร้อย!** ตั้งแต่พรุ่งนี้เป็นต้นไป ระบบจะอัพเดทเว็บอัตโนมัติทุก 7:00 น.

---

## ขั้นที่ 6️⃣ *(ทางเลือก)* — เปิดฟีเจอร์ข่าววิเคราะห์ตลาด 📰

ระบบจะดึงข่าวเชิงวิเคราะห์จาก Reuters / CNBC / CoinDesk / MarketWatch / The Conversation มาให้ **Claude สรุปเป็นภาษาไทยอัตโนมัติ** ทุกรอบเช้า — แต่ต้องมี Anthropic API key

> ค่าใช้จ่ายโดยประมาณ ~$4/เดือน (5 ข่าว/วัน · Sonnet 4.6) — ถ้าไม่ตั้ง key ระบบจะข้าม section ข่าวไปเอง รายงาน BUY/SELL/HOLD ยังทำงานปกติ

### 6.1 ขอ Anthropic API key

1. ไป https://console.anthropic.com → Sign up / Sign in
2. **Settings → API Keys → Create Key** → คัดลอกค่าที่ขึ้นต้น `sk-ant-...`
3. **Billing → Plans & billing** → เติม credit ขั้นต่ำ $5

### 6.2 ใส่ key ใน GitHub Secrets

1. ในหน้า repo → **Settings → Secrets and variables → Actions**
2. กด **New repository secret**
3. กรอก:
   - **Name:** `ANTHROPIC_API_KEY`
   - **Secret:** วาง key ที่คัดลอกมา
4. กด **Add secret**

### 6.3 รัน workflow อีกครั้ง

Actions → Daily CDC Report → Run workflow → รอ ~3 นาที → refresh เว็บ → จะเห็น section "📰 ข่าววิเคราะห์ตลาด" ขึ้นมาเหนือตารางสัญญาณ

> 🔄 **Token หมดกลางคัน?** ระบบจะ defer ข่าวที่ยังไม่ได้ประมวลผลโดยอัตโนมัติ — workflow "Resume Pending News" จะรันทุก 30 นาทีและประมวลผลต่อให้เมื่อ token refresh

---

## 🐛 Troubleshooting

### ❌ Action รันแล้วขึ้นกากบาทแดง

คลิกเข้าไปดู log มักเป็น:

| Error | สาเหตุ | แก้ |
|---|---|---|
| "Get Pages site failed" | ยังไม่ได้เปิด GitHub Pages | ทำขั้นที่ 3 |
| "ModuleNotFoundError" | `requirements.txt` ไม่ขึ้น | อัพไฟล์ใหม่ |
| "Permission denied" | repo เป็น Private | เปลี่ยนเป็น Public ใน Settings |

### ❌ ไม่เห็นแท็บ Actions ทำงาน

→ โฟลเดอร์ `.github` ไม่ได้อัพ → กลับไปขั้น 2 ทำใหม่

### ❌ Settings → Pages ไม่เห็นเมนู Pages

→ Repo เป็น Private + บัญชี Free → เปลี่ยนเป็น Public

### ❌ เปิด URL แล้วขึ้น 404

- รออีก 1-2 นาที (Pages ใช้เวลาตั้งค่าครั้งแรก)
- ตรวจว่า Action **Deploy to GitHub Pages** ขึ้นเขียวแล้ว
- Refresh หน้า browser (Ctrl+Shift+R เพื่อ clear cache)

### ❌ เปิดเว็บได้แต่บางเหรียญขึ้น "⚠️"

→ ปกติ — บางครั้ง API ของ exchange ตอบช้า รอบหน้า (พรุ่งนี้) จะกลับมา หรือกด Run workflow ด้วยมืออีกครั้ง

### ❌ ตั้ง `ANTHROPIC_API_KEY` แล้วแต่ section ข่าวไม่ขึ้น

- ตรวจว่า key ขึ้นต้นด้วย `sk-ant-`
- ตรวจ Billing ว่ามี credit เหลือ
- ดู log step **Generate report** จะมีบรรทัด `⚠️ ข้าม news section: ...` บอกสาเหตุ
- ถ้าเห็น `🔄 deferred` แปลว่าโดน rate-limit — workflow `Resume Pending News` จะมาเก็บให้ภายใน 30 นาที

---

## 💡 Tips

- **อยากเพิ่ม/ลบเหรียญ** → แก้ `report.py` บน GitHub ได้เลย (กดดินสอ ✏️ มุมขวาบน) → commit → Action จะรันรอบถัดไปเอง
- **อยาก force update เดี๋ยวนั้น** → Actions → Run workflow → รอ 1-2 นาที → refresh เว็บ
- **เปลี่ยนเวลารัน** → แก้ `.github/workflows/daily-report.yml` ดูที่ cron
- **ทดสอบบ่อยๆ ได้** → GitHub Actions ฟรี 2,000 นาที/เดือน เราใช้แค่ ~30 นาที/เดือน

---

## ❓ FAQ

**Q: เปิดให้เป็น Private ได้ไหม?**
A: GitHub Pages ฟรี = ต้อง Public แต่โค้ดในนี้ไม่มีข้อมูลส่วนตัว — แค่สูตรคำนวณสาธารณะ และคนอื่นจะหา URL คุณไม่เจอถ้าคุณไม่บอก (เพราะชื่อ repo เป็น username/cdc-report)

**Q: ใครบ้างเห็นเว็บนี้?**
A: ใครก็ตามที่รู้ URL — แต่ Google index ช้า และไม่มี link ชี้ไปที่เว็บคุณจากที่ไหน คนเข้าได้แค่คุณกับคนที่คุณบอกเท่านั้น

**Q: รับ notification ได้ไหม?**
A: เวอร์ชันนี้ดูเองอย่างเดียว ถ้าอยาก noti กลับมาอ่านขอเวอร์ชัน Email ได้

**Q: ฟรีจริงไหม?**
A: ฟรีถาวร — GitHub Pages และ Actions ฟรีสำหรับ Public repo

**Q: หยุดรันชั่วคราว?**
A: Settings → Actions → General → Disable Actions
