# 🤖 ربات کاریابی تلگرام — سیستم کامل

سیستم دو ربات تلگرام برای مدیریت کانال کاریابی و فریلنسری

---

## 📋 ربات‌ها

### ربات ۱ — کپی‌پست خودکار
- مانیتور کانال‌های کاریابی دیگه به صورت ۲۴/۷
- فیلتر هوشمند پست‌های مرتبط
- اضافه کردن برندینگ کانال شما
- جلوگیری از ارسال تکراری

### ربات ۲ — ثبت سفارش
- فرم ثبت آگهی استخدام یا پروژه فریلنسری
- پرداخت آنلاین یکپارچه
- پنل ادمین برای تایید/رد آگهی‌ها
- انتشار خودکار بعد از تایید

---

## 🚀 راه‌اندازی

### مرحله ۱ — ساخت ربات‌ها
1. به [@BotFather](https://t.me/BotFather) برو
2. `/newbot` بزن و دو ربات بساز
3. توکن هر ربات رو کپی کن

### مرحله ۲ — گرفتن آی‌دی عددی خودت
1. به [my.telegram.org](https://my.telegram.org) برو
2. وارد شو و **API Development Tools** رو بزن
3. یه اپ بساز و `api_id` و `api_hash` رو بگیر

### مرحله ۳ — تنظیم GitHub Secrets
در ریپوی GitHub خودت، برو به:
`Settings` → `Secrets and variables` → `Actions` → `New repository secret`

و این‌ها رو اضافه کن:

| نام Secret | توضیح |
|-----------|-------|
| `BOT1_TOKEN` | توکن ربات اول (کپی‌پست) |
| `BOT2_TOKEN` | توکن ربات دوم (ثبت سفارش) |
| `TARGET_CHANNEL` | یوزرنیم کانال شما (مثلاً `@mychannel`) |
| `ADMIN_CHAT_ID` | آی‌دی عددی ادمین — از [@userinfobot](https://t.me/userinfobot) بگیر |
| `SOURCE_CHANNELS` | کانال‌های منبع جدا با کاما: `@ch1,@ch2,@ch3` |


| `PAYMENT_PROVIDER_TOKEN` | از [@BotFather](https://t.me/BotFather) → Payments (اختیاری) |
| `PRICE_JOB_AD` | قیمت آگهی استخدام به تومان (مثلاً `150000`) |
| `PRICE_FREELANCE_PROJECT` | قیمت پروژه فریلنسری (مثلاً `100000`) |
| `CHANNEL_DISPLAY_NAME` | نام نمایشی کانال شما |

### مرحله ۴ — اجرا
بعد از تنظیم Secrets:
1. کد رو Push کن به GitHub
2. برو به `Actions` در ریپوی GitHub
3. Workflow رو فعال کن

✅ ربات‌ها خودکار اجرا میشن!

---

## 💳 تنظیم پرداخت آنلاین

### گزینه A — زرین‌پال (برای ایران)
1. در [zarinpal.com](https://zarinpal.com) ثبت نام کن
2. از [@BotFather](https://t.me/BotFather) → Payments → Zarrinpal توکن بگیر
3. توکن رو در `PAYMENT_PROVIDER_TOKEN` بذار

### گزینه B — بدون درگاه (حالت تست)
اگه `PAYMENT_PROVIDER_TOKEN` رو خالی بذاری، ربات بدون پرداخت کار می‌کنه و مستقیم به ادمین اطلاع میده.

---

## 🔧 ساختار فایل‌ها

```
telegram-jobboard/
├── bot1_scraper/
│   └── bot1.py          # ربات کپی‌پست
├── bot2_order/
│   └── bot2.py          # ربات ثبت سفارش
├── shared/
│   └── database.py      # دیتابیس مشترک
├── data/                # دیتابیس SQLite (خودکار ساخته میشه)
├── .github/workflows/
│   └── run_bots.yml     # GitHub Actions
├── .env.example         # نمونه فایل تنظیمات
├── requirements.txt
└── README.md
```

---

## ⚙️ شخصی‌سازی

### تغییر فیلتر کلمات (ربات ۱)
در `bot1_scraper/bot1.py` بخش `keywords` رو ویرایش کن:
```python
keywords = [
    'استخدام', 'کارجو', 'فریلنس', ...
    # کلمات دلخواه خودت رو اضافه کن
]
```

### تغییر قالب پست
در `bot1_scraper/bot1.py` تابع `format_post` رو ویرایش کن.

### تغییر قیمت‌ها
از طریق GitHub Secrets یا فایل `.env` تنظیم کن.

---

## 🆓 رایگان ۲۴/۷

این پروژه از **GitHub Actions** استفاده می‌کنه که:
- ✅ کاملاً رایگان (تا ۲۰۰۰ دقیقه در ماه برای ریپوی عمومی: نامحدود)
- ✅ هر ۵ دقیقه خودکار ریستارت میشه
- ✅ نیازی به سرور نیست

> **نکته:** برای پایداری بیشتر می‌تونی از [Railway](https://railway.app) یا [Render](https://render.com) هم استفاده کنی — هر دو پلن رایگان دارن.

---

## 📞 مشکل داشتی؟

1. لاگ‌ها رو در GitHub Actions → Workflow runs چک کن
2. مطمئن شو ربات ادمین کانال شما هست
3. مطمئن شو `SOURCE_CHANNELS` بدون فاصله و با کاما جداست
