# Multilevel_Eldor — avtomatik post tizimi

Telegram kanaliga kuniga 2 marta AI orqali post tayyorlaydi, **sizdan ruxsat so'raydi**,
tasdiqlaganingizdan keyin chiqaradi. GitHub Actions'da ishlaydi — kompyuter yoqiq bo'lishi shart emas.

## Kun tartibi

```
08:30  Bot postni tayyorlaydi va sizga shaxsiy chatga yuboradi
       (rasm + matn + 3 ta tugma)
         ✅ Chiqarish      -> darhol kanalga chiqadi
         🔄 Qayta yozish   -> boshqacha yozadi va yana so'raydi
         ❌ Bekor qilish   -> chiqmaydi
09:00  Javob bermasangiz -> post avtomatik chiqadi

18:30 / 19:00 — kechqurun ham xuddi shunday
```

## Ichki oqim

```
1. Researcher  -> Google qidiruvi bilan yangi mavzu topadi (takrorlanmaydi)
2. Writer      -> kanal uslubida post matnini yozadi
3. QA          -> grammatika, fakt, format, uzunlikni tekshiradi (10 ballik)
4. Imager      -> Gemini rasm chizadi; ishlamasa kod bilan kartochka chiziladi
5. Approver    -> sizga yuboradi va javobingizni kutadi
6. Publisher   -> kanalga chiqaradi
```

Sifat nazoratidan o'tmasa post 2 marta qayta yoziladi. Baribir o'tmasa —
chiqarilmaydi va sizga sabab bilan xabar keladi.

---

## ⚠️ Reponi PUBLIC qiling

Tasdiq kutish workflow'ni 30 daqiqa ushlab turadi. Hisob:

| Repo turi | Bepul Actions daqiqasi | Bizning sarf |
|---|---|---|
| **Private** | oyiga 2000 | ~1980 — chegaraga tegib turadi ❗ |
| **Public** | **cheksiz** | muammo yo'q ✅ |

Kodda hech qanday maxfiy ma'lumot yo'q — kalitlar GitHub Secrets'da saqlanadi va
public repoda ham ko'rinmaydi. Shuning uchun **Public** tavsiya qilinadi.

Private qoldirmoqchi bo'lsangiz: `src/config.py` da `APPROVAL_WAIT_MINUTES = 10` qiling
(oyiga ~780 daqiqa sarflanadi).

Repo turini o'zgartirish: **Settings → General → eng pastda Danger Zone → Change visibility**

---

## O'rnatish

### 1. Fayllarni yuklash
Repo → **Add file → Upload files** → hamma faylni tashlang → **Commit changes**.
`.github` papkasi ham yuklanganiga ishonch hosil qiling.

### 2. Botga /start yozing (majburiy)
Telegramda **@multilvel_bot** ni oching va `/start` yozing.
Busiz bot sizga tasdiq so'rovi yubora olmaydi.

### 3. Secrets qo'shish
**Settings → Secrets and variables → Actions → New repository secret**

| Nomi | Qiymati |
|---|---|
| `GEMINI_API_KEY` | aistudio.google.com dan olingan kalit |
| `TELEGRAM_BOT_TOKEN` | @BotFather bergan token |
| `TELEGRAM_CHANNEL_ID` | `@Multilevel_Eldor` |
| `ADMIN_CHAT_ID` | **majburiy** — sizning Telegram ID'ingiz (@userinfobot dan) |

### 4. Huquqlarni yoqish
**Settings → Actions → General → Workflow permissions → "Read and write permissions" → Save**

### 5. Google billing yoqish (AI rasmlar uchun)
`console.cloud.google.com` → loyihangiz → **Billing** → kartani bog'lang.
Yoqmasangiz ham tizim ishlaydi — rasm kod bilan chiziladi.

---

## Sinash

**Actions → "Avtomatik post" → Run workflow**

| Rejim | Nima qiladi |
|---|---|
| `dry-run` | Hech qayerga yubormaydi. Natija Artifacts'da. **Birinchi sinov shu bo'lsin** |
| `test-to-admin` | Faqat sizga yuboradi, tasdiqsiz |
| `approve` | Tasdiq so'raydi, keyin kanalga chiqaradi (haqiqiy rejim) |
| `publish-now` | Tasdiqsiz darhol kanalga chiqaradi |

`wait` maydoniga son yozib, tasdiq kutish vaqtini bir martalik o'zgartirasiz
(sinovda `2` qo'ying — 30 daqiqa kutib o'tirmaysiz).

---

## Sozlamalar — `src/config.py`

| Nima | O'zgaruvchi | Hozir |
|---|---|---|
| Tasdiq so'ralsinmi | `APPROVAL_REQUIRED` | `True` |
| Necha daqiqa kutsin | `APPROVAL_WAIT_MINUTES` | `30` |
| Javob bo'lmasa chiqsinmi | `AUTO_PUBLISH_ON_TIMEOUT` | `True` |
| Rasm manbasi | `IMAGE_SOURCE` | `"ai"` (`"card"` — bepul) |
| Google qidiruvi | `USE_SEARCH_GROUNDING` | `True` |
| Sifat chegarasi | `QA_MIN_SCORE` | `7` |
| Post uslubi | `STYLE_GUIDE`, `EXAMPLE_POST` | — |
| Kartochka ranglari | `src/utils/card.py` → `PALETTES` | — |

**Vaqtni o'zgartirish:** `.github/workflows/post.yml` dagi `cron`.
UTC yoziladi — Toshkent vaqtidan 5 soat ayiring. Post cron'dan 30 daqiqa keyin chiqadi.

---

## Sinov (tarmoqsiz)

```bash
python tests/mock_run.py
```

Soxta javoblar bilan butun oqimni tekshiradi: QA sikli, tasdiq tugmalari,
bekor qilish, vaqt tugashi, qayta yozish.

---

## Tez-tez uchraydigan xatolar

| Xato | Sabab va yechim |
|---|---|
| Tasdiq so'rovi kelmadi | Botga `/start` yozmagansiz yoki `ADMIN_CHAT_ID` xato |
| `Forbidden: bot is not a member` | Bot kanalga admin qilinmagan |
| `chat not found` | `TELEGRAM_CHANNEL_ID` xato. Yopiq kanalga `-100...` ID kerak |
| `can't parse entities` | Matnda noto'g'ri HTML teg. QA odatda ushlaydi |
| `RESOURCE_EXHAUSTED` (rasm) | Billing yoqilmagan. Rasm kartochka bilan chiziladi |
| Rasmda yozuv buzuq | AI kamchiligi. `IMAGE_SOURCE = "card"` qiling — yozuv har doim to'g'ri |
| Cron kechikdi | GitHub'da 5–15 daqiqa kechikish normal |
| Cron butunlay to'xtadi | Repo 60 kun harakatsiz qolgan. Biror commit qiling |

---

## Xarajat

| Xizmat | Oyiga |
|---|---|
| GitHub Actions (public repo) | Bepul |
| Gemini matn | ~$0.10 |
| Gemini rasm (60 ta, 1024px) | ~$4.00 |
| Google qidiruvi (60 so'rov) | Bepul (5000 gacha) |
| **Jami** | **~$4** |

`IMAGE_SOURCE = "card"` qilsangiz rasm bepul bo'ladi va jami ~$0.10 ga tushadi.
