# deutsch-word-order-fa — ترتیب کلمات آلمانی (Satzbau) برای فارسی‌زبان‌ها

یک **Agent Skill** قطعی برای سومین چیزی که فارسی‌زبان‌ها موقع یادگیری
آلمانی هر روز با آن زمین می‌خورند: ترتیب کلمات. بعد از
[`deutsch-fa`](https://github.com/mohammad-abbasi-sh/deutsch-fa)
(آرتیکل + ۴ حالت) و
[`deutsch-verbs-fa`](https://github.com/mohammad-abbasi-sh/deutsch-verbs-fa)
(صرف فعل)، این دنباله‌ی آن‌هاست — *فعل کجای جمله می‌ایستد؟*

ترتیب کلمات فارسی SOV و انعطاف‌پذیر است؛ آلمانی این‌طور نیست. در جمله‌ی
خبری آلمانی فعل صرف‌شده **همیشه دوم** است. در جمله‌ی فرعی به **انتها**
می‌رود. قیدها به ترتیب **زمان ← حالت ← مکان** می‌آیند. بخش دوم فعل
(Partizip، مصدر، پیشوند فعل جداشدنی) **قاب جمله** را در انتها می‌بندد.
هیچ‌کدام از این‌ها در فارسی وجود ندارد؛ برای همین زبان‌آموزها همان ده
اشتباه را بارها تکرار می‌کنند — و ایجنت‌هایی که از حافظه جواب می‌دهند
هم همان اشتباه‌ها را «درست» اعلام می‌کنند. این اسکیل ترتیب کلمات را
**قطعی** می‌کند: یک موتور پایتون بدون وابستگی + ۴۸ جفت جمله‌ی
دست‌ساز A1–B1 (درست + نسخه‌ی غلط رایج، هرکدام با ترجمه‌ی فارسی)، با
توضیح همه‌ی قواعد به فارسی.

بدون فراخوانی مدل، بدون دانلود، بدون کلید API. فقط کتابخانه‌ی استاندارد
پایتون ۳٫۸ به بالا.

## مسئله

```
زبان‌آموز می‌نویسد:   Ich jeden Tag gehe zur Schule.
ایجنت (از حافظه):     درست است ✓     ← غلط است، و زبان‌آموز حالا
                                       اشتباه را حفظ می‌کند

با deutsch-word-order-fa:
$ python3 scripts/deutsch_word_order.py check "Ich jeden Tag gehe zur Schule"
✗ [DWO-01] Verb-second (V2) — فعل باید دومین جزء جمله باشد
  قبل از فعل «gehe» دو جزء آمده است: «Ich» و «jeden Tag».
  درست: Morgen fahre ich nach Berlin.
```

## ده قانون

| کد | قانون |
|---|---|
| DWO-01 | فعل دوم (V2): فقط یک جزء قبل از فعل |
| DWO-02 | در جمله‌ی فرعی فعل آخر است (weil/dass/wenn/…) |
| DWO-03 | TeKaMoLo: زمان ← حالت ← مکان |
| DWO-04 | قاب جمله: Partizip / مصدر / پیشوند جداشدنی آخر است |
| DWO-05 | سؤال بله/خیر با فعل شروع می‌شود |
| DWO-06 | کلمه‌ی پرسشی اول، فعل دوم |
| DWO-07 | جمله‌ی خبری با فعل شروع نمی‌شود (به‌جز امر) |
| DWO-08 | بعد از und/aber/oder/denn/sondern هم V2 برقرار است |
| DWO-09 | «nicht» هرگز بلافاصله قبل از فعل نمی‌آید |
| DWO-10 | ضمیر مفعولی قبل از اسم؛ ضمیر Akkusativ قبل از Dativ |

## نصب و استفاده

```bash
# Claude Code: کپی اسکیل
cp -r skills/deutsch-word-order-fa ~/.claude/skills/

# Claude.ai: فایل dist/deutsch-word-order-fa-skill.zip را آپلود کنید

# Cursor / Windsurf / Cline / Continue: راهنما در cursor/README.md

# بررسی، اصلاح، توضیح، آزمون، خروجی انکی
python3 skills/deutsch-word-order-fa/scripts/deutsch_word_order.py check "Ich jeden Tag gehe zur Schule"
python3 skills/deutsch-word-order-fa/scripts/deutsch_word_order.py fix "Ich jeden Tag gehe zur Schule"
python3 skills/deutsch-word-order-fa/scripts/deutsch_word_order.py explain DWO-03
python3 skills/deutsch-word-order-fa/scripts/deutsch_word_order.py quiz --n 5 --level A2 --seed 7
python3 skills/deutsch-word-order-fa/scripts/deutsch_word_order.py anki --out cards.tsv
```

کدهای خروج: `0` = درست / موفق · `1` = خطا یافت شد یا فعل ناشناخته ·
`2` = خطای استفاده.

## محدودیت‌ها (صادقانه)

- واژگان A1–B1 (۷۳ فعل، ۴۸ جفت جمله) — جایگزین دیکشنری نیست.
- فقط جمله‌های ساده‌ی اصلی/فرعی و سؤالی؛ جمله‌های موصولی،
  Ersatzinfinitiv و مفعولِ جلوانداخته‌شده با ضمیر بررسی نمی‌شوند.
- مرجع قطعی است، نه معلم: درباره‌ی سبک و طبیعی‌بودن قضاوت نمی‌کند.
  **«خطایی پیدا نشد» به معنی «جمله کاملاً درست است» نیست.**

## نقشه‌ی راه

- نسخه‌ی ۱٫۱: جمله‌های B2 (موصولی، مصدر دوتایی)، عبارت‌های قیدی بیشتر.
- نسخه‌ی ۱٫۲: اتصال به `deutsch-fa` برای بررسی هم‌زمان آرتیکل و حالت.
- نسخه‌ی ۱٫۳: حالت آزمون نوشتاری Goethe A1/A2 — بررسی متن کامل با نمره.

## مجوز

MIT — فایل [LICENSE](LICENSE).
