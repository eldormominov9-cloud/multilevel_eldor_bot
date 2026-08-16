"""
Markaziy konfiguratsiya.

Bu yerdagi qiymatlarni o'zgartirib, tizim xatti-harakatini boshqarasiz.
Kod fayllariga tegish shart emas.
"""
import os

# ---------------------------------------------------------------------------
# MAXFIY KALITLAR (GitHub Secrets'dan keladi — bu yerga yozmang!)
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "@Multilevel_Eldor")

# Xatolik haqida xabar keladigan shaxsiy chat (ixtiyoriy).
# Botga /start yozing, keyin o'z ID'ingizni @userinfobot dan oling.
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "")

# ---------------------------------------------------------------------------
# MODELLAR
# ---------------------------------------------------------------------------
# 2026-08-16 da sinovdan o'tkazildi: gemini-2.5-flash yangi kalitlarga berilmaydi.
TEXT_MODEL = "gemini-3.7-flash"
TEXT_MODEL_FALLBACK = "gemini-3.6-flash"   # asosiy model band bo'lsa
IMAGE_MODEL = "gemini-3.1-flash-image"     # yangi "nano-banana"

# Google Search grounding: billing yoqilgan bo'lsa ishlaydi (oyiga 5000 so'rov bepul).
# Bepul rejimda 429 xatosi beradi — kod avtomatik qidiruvsiz davom etadi.
USE_SEARCH_GROUNDING = True

# Rasm manbasi:
#   "ai"   — Gemini generatsiya qiladi (billing kerak), xato bo'lsa kartochkaga o'tadi
#   "card" — kod bilan chiziladi (bepul, yozuv har doim to'g'ri)
IMAGE_SOURCE = "ai"

# ---------------------------------------------------------------------------
# TASDIQLASH (moderatsiya)
# ---------------------------------------------------------------------------
# True bo'lsa: post avval ADMIN_CHAT_ID ga yuboriladi, tugma bosilishi kutiladi.
APPROVAL_REQUIRED = True

# Necha daqiqa javob kutilsin
APPROVAL_WAIT_MINUTES = 30

# Javob bo'lmasa: True — o'zi chiqaradi, False — chiqarmaydi
AUTO_PUBLISH_ON_TIMEOUT = True

# "🔄 Qayta yozish" tugmasi necha marta bosilishi mumkin
MAX_REGENERATIONS = 2

# ---------------------------------------------------------------------------
# KANAL
# ---------------------------------------------------------------------------
CHANNEL_HANDLE = "@Multilevel_Eldor"
RUBRIC = "Ingliz tilini tez o'rganish"

# ---------------------------------------------------------------------------
# REKLAMA QATORI (har post oxiriga avtomatik qo'shiladi)
#
# Modelga tashlab qo'yilmaydi — kod qo'shadi, shuning uchun hech qachon
# tushib qolmaydi. Har post navbatdagi variantni oladi, matn takrorlanmaydi.
# ---------------------------------------------------------------------------
PROMO_BOT = "@uchqizilbot"

PROMO_LINES = [
    f"📝 O'qib chiqdingizmi? Endi sinab ko'ring — <b>{PROMO_BOT}</b> da ingliz tilidan testlar ishlang.",
    f"🎯 Bilim amaliyotda mustahkamlanadi. <b>{PROMO_BOT}</b> da test ishlab, o'zingizni tekshiring.",
    f"🧠 Darajangiz qanday? <b>{PROMO_BOT}</b> da ingliz tilidan testlar sizni kutmoqda.",
    f"✍️ Bugun o'rganganingizni unutmang — <b>{PROMO_BOT}</b> da mashq qiling.",
    f"⚡️ 5 daqiqalik test — katta farq. <b>{PROMO_BOT}</b> da ingliz tilini sinang.",
]


def build_footer(variant: int = 0) -> str:
    """Post oxiriga qo'shiladigan reklama + kanal qatori."""
    line = PROMO_LINES[variant % len(PROMO_LINES)]
    return f"\n\n{line}\n👉 {CHANNEL_HANDLE}"

# Telegram rasm ostidagi matn chegarasi = 1024 belgi.
# Xavfsiz chegara qo'yamiz, chunki HTML teglar ham hisobga olinadi.
MAX_CAPTION_CHARS = 950

# ---------------------------------------------------------------------------
# MAVZU KATEGORIYALARI VA ROTATSIYA
# ---------------------------------------------------------------------------
CATEGORIES = {
    "vocabulary": {
        "name": "So'z boyligi va idiomalar",
        "brief": (
            "Kundalik inglizcha so'zlar, idiomalar, phrasal verbs, "
            "collocations, slang — ma'nosi, misollar va eslab qolish usuli bilan."
        ),
        "image_style": "illustration",
    },
    "grammar": {
        "name": "Grammatika qoidalari",
        "brief": (
            "Zamonlar, artikllar, predloglar, shart gaplar, modal fe'llar — "
            "o'zbek tilida sodda tushuntirish va tipik xatolar."
        ),
        "image_style": "minimal",
    },
    "exam": {
        "name": "Multilevel / IELTS maslahatlari",
        "brief": (
            "Multilevel (CEFR) va IELTS imtihonlariga tayyorgarlik: "
            "Speaking/Writing/Listening/Reading strategiyalari, ball oshirish yo'llari, "
            "tipik xatolar, vaqtni boshqarish."
        ),
        "image_style": "minimal",
    },
    "method": {
        "name": "O'rganish metodikasi",
        "brief": (
            "Xotira texnikalari, spaced repetition, kunlik odat qurish, "
            "foydali ilovalar va resurslar, motivatsiya va tilni tez o'zlashtirish usullari."
        ),
        "image_style": "minimal",
    },
}

# Har ishga tushishda navbatdagi kategoriya olinadi.
# So'z boyligi eng ko'p ulashiladigan kontent — shuning uchun ko'proq uchraydi.
CATEGORY_ROTATION = [
    "vocabulary",
    "grammar",
    "vocabulary",
    "exam",
    "vocabulary",
    "method",
    "grammar",
    "exam",
]

# ---------------------------------------------------------------------------
# POST USLUBI (STYLE GUIDE)
#
# ⚠️ MUHIM: bu bo'lim kanalingizdan olingan 3 ta namuna post asosida
# yangilanishi kerak. Hozirgi versiya — boshlang'ich shablon.
# ---------------------------------------------------------------------------
STYLE_GUIDE = """
TIL:
- Asosiy til: o'zbek tili (lotin alifbosi). Inglizcha so'z/jumlalar asl holida.
- Har inglizcha misoldan keyin o'zbekcha tarjima majburiy.
- Rus tilidan olingan so'zlarni ishlatma ("primer", "praktika" emas — "misol", "amaliyot").

OHANG:
- Do'stona, ustoz kabi, lekin ortiqcha rasmiyatchiliksiz.
- "Siz" shaklida murojaat.
- Hech qachon "Assalomu alaykum", "Bugun biz ko'rib chiqamiz" kabi cho'zilgan kirish yozma.
  Birinchi qatordan darhol mavzuga kir.
- Ortiqcha maqtov, "ajoyib", "hayratlanarli" kabi bo'sh sifatlardan qoch.

TUZILISH (aynan shu tartibda, hashtaglar bilan TUGAYDI):
1. Sarlavha: emoji + qalin qilingan asosiy ibora/qoida + qisqa savol yoki izoh
2. Bo'sh qator
3. 1-2 jumlada tushuntirish — nima ekanligi va nega kerakligi
4. Bo'sh qator
5. "📌 Misollar:" — 2 yoki 3 ta misol.
   Har biri: "• " + inglizcha jumla, keyingi qatorda "   — " + o'zbekcha tarjima
6. Bo'sh qator
7. "💡 " bilan boshlanuvchi bitta amaliy maslahat yoki eslab qolish usuli
8. Bo'sh qator
9. Hashtaglar qatori — SHU YERDA TUGATASAN

MUHIM: post oxiridagi reklama qatori va kanal manzilini O'ZING YOZMA.
Ularni tizim avtomatik qo'shadi. Sen faqat hashtaglargacha yozasan.

FORMAT:
- Telegram HTML: faqat <b>, <i>, <u>, <code> teglaridan foydalan.
- Markdown ishlatma (** yoki __ yo'q).
- Uzunlik: 400–780 belgi (hashtaglargacha). 780 dan oshmasin —
  oxiriga tizim yana ~110 belgi qo'shadi va Telegram chegarasi 1024 ta.
- Emoji: jami 3-5 ta, faqat tuzilish belgisi sifatida. Jumla ichida emoji ishlatma.

HASHTAGLAR:
- Har doim #ingliztili va #multilevel bo'lsin.
- Ularga qo'shimcha 1 ta mavzuga oid teg: #idiom #grammatika #ielts #sozboyligi #metodika
"""

# Namuna post — model shu ko'rinishga taqlid qiladi.
# Kanalingizdan namuna kelgach, shu yerni almashtiramiz.
EXAMPLE_POST = """🎯 <b>"Piece of cake"</b> — bu nima degani?

So'zma-so'z tarjimasi "bir bo'lak tort", lekin haqiqiy ma'nosi — <b>juda oson ish</b>. Ingliz tilida biror narsa qiyin emasligini aytmoqchi bo'lsangiz, shu iborani ishlatasiz.

📌 Misollar:
• The test was a piece of cake.
   — Imtihon juda oson edi.
• Don't worry, it's a piece of cake!
   — Xavotir olmang, bu oson!

💡 Eslab qolish uchun: tort yeyish oson-ku? Ibora ham shundan kelib chiqqan.

#ingliztili #idiom #multilevel

📝 O'qib chiqdingizmi? Endi sinab ko'ring — <b>@uchqizilbot</b> da ingliz tilidan testlar ishlang.
👉 @Multilevel_Eldor"""

# ---------------------------------------------------------------------------
# RASM USLUBLARI
#
# {scene} — writer agenti taklif qilgan sahna tavsifi
# {headline} — rasmda ko'rinishi kerak bo'lgan qisqa matn
# ---------------------------------------------------------------------------
IMAGE_STYLES = {
    "minimal": (
        "FULL-BLEED FLAT GRAPHIC DESIGN, square 1:1. The artwork itself fills the ENTIRE "
        "canvas edge to edge. This is NOT a photograph of a printed poster: no paper, "
        "no frame, no border, no drop shadow, no surrounding surface or background wall. "
        "Warm cream (#F2EEE6) fills the whole square. A thin bright orange bar sits flush "
        "against the very top edge, spanning the full width. "
        "Large bold black sans-serif lettering, left-aligned in the upper-middle area, "
        "reads exactly: \"{headline}\". Spell it perfectly — correct English, no extra, "
        "missing or garbled letters. "
        "Directly under it, one short thick orange rule. "
        "Bottom-left corner: small muted grey text reading exactly \"{channel}\". "
        "Bottom-right corner: one simple flat orange icon suggesting {scene}. "
        "Swiss editorial style, high contrast, balanced composition with no large empty "
        "dead zone in the middle. Flat vector only — no gradients, no shadows, no texture, "
        "no watermark, and no words beyond the two specified."
    ),
    "illustration": (
        "FULL-BLEED FLAT VECTOR ILLUSTRATION, square 1:1. The illustration fills the ENTIRE "
        "canvas edge to edge. This is NOT a photograph of a card or poster: no frame, "
        "no border, no drop shadow, no surrounding surface. "
        "Soft mint-green background covering the whole square, with simple geometric "
        "accent shapes bleeding off the edges. "
        "Scene: {scene}. "
        "Characters in a clean flat cartoon style with warm skin tones, simple facial "
        "features and rounded shapes. Limited harmonious palette: mint green, warm orange, "
        "soft blue, cream. The main subject is large and centred, filling most of the frame. "
        "Bold flat colors — no gradients, no textures, no photorealism, no 3D. "
        "Do not include any text, letters, words or numbers anywhere in the image."
    ),
    "3d": (
        "A soft 3D render, square 1:1 format, modern app-illustration style. "
        "Deep purple-to-indigo gradient background with soft studio lighting from the upper left. "
        "Scene: {scene}. "
        "Objects rendered as smooth, rounded, glossy 3D shapes with soft shadows "
        "and subtle highlights, in a palette of mint, coral, gold and lavender. "
        "Clean composition, shallow depth of field, no text, no letters, no words."
    ),
}

# ---------------------------------------------------------------------------
# SIFAT NAZORATI
# ---------------------------------------------------------------------------
QA_MIN_SCORE = 7          # 10 balldan shu balldan past bo'lsa qayta yoziladi
QA_MAX_RETRIES = 2        # qayta yozish urinishlari soni

# Oxirgi nechta mavzu takrorlanmasligi tekshiriladi
HISTORY_LOOKBACK = 120
HISTORY_MAX = 400
