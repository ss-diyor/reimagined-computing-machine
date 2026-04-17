# 📋 Exam Registration Bot

Telegram bot orqali imtihonlarga (SAT, Milliy sertifikat va h.k.) ro'yxatdan o'tish tizimi.

---

## 🗂 Papka tuzilmasi

```
exam_bot/
├── bot.py              # Asosiy fayl
├── config.py           # Sozlamalar
├── database.py         # SQLite amaliyotlari
├── handlers/
│   ├── user.py         # Foydalanuvchi handerlari
│   └── admin.py        # Admin handlerlari
├── keyboards/
│   ├── user_kb.py      # Foydalanuvchi klaviaturalari
│   └── admin_kb.py     # Admin klaviaturalari
├── states/
│   └── states.py       # FSM holatlari
├── requirements.txt
├── Procfile            # Railway uchun
└── .env.example
```

---

## ⚙️ O'rnatish

### 1. `.env` fayl yaratish
```bash
cp .env.example .env
```
`.env` faylni tahrirlang:
```
BOT_TOKEN=sizning_token
ADMIN_IDS=sizning_telegram_id
```
> Telegram ID ni [@userinfobot](https://t.me/userinfobot) orqali bilib oling.

### 2. Kutubxonalarni o'rnatish
```bash
pip install -r requirements.txt
```

### 3. Ishga tushirish
```bash
python bot.py
```

---

## 🚀 Railway ga deploy qilish

1. GitHub repoga push qiling
2. Railway → New Project → Deploy from GitHub
3. **Environment Variables** bo'limiga qo'shing:
   - `BOT_TOKEN`
   - `ADMIN_IDS`
4. Deploy bo'ladi ✅

---

## 👤 Foydalanuvchi imkoniyatlari

| Amal | Tavsif |
|------|--------|
| `/start` | Botni ishga tushirish / ro'yxatdan o'tish |
| 📝 Imtihonga ro'yxatdan o'tish | Imtihon turi va sanasini tanlash |
| 📋 Mening ro'yxatlarim | Faol ro'yxatlarni ko'rish va bekor qilish |
| ℹ️ Ma'lumot | Bot haqida ma'lumot |
| `/cancel` | Joriy amalni bekor qilish |

---

## 🔧 Admin imkoniyatlari

`/admin` buyrug'i bilan admin panelni oching.

| Amal | Tavsif |
|------|--------|
| 📚 Imtihon turlari | Qo'shish, faollashtirish/o'chirish |
| 📅 Imtihon sanalari | Sana, joy, o'rinlar sonini boshqarish |
| 👥 Ro'yxatlar | Barcha yoki imtihon bo'yicha ko'rish |
| 📊 Statistika | Umumiy hisobot |
| 📢 Xabar yuborish | Barcha foydalanuvchilarga broadcast |

---

## 🗃 Ma'lumotlar bazasi

SQLite (`exam_bot.db`) — Railway `tmp` papkasiga saqlanadi.

> **Eslatma:** Railway free tier da fayl tizimi ephemeral (qayta deploy bo'lganda o'chadi). Doimiy saqlov uchun PostgreSQL yoki Railway Volume ulang.
