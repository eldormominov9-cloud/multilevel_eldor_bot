"""
4-AGENT — Sifat nazorati.

Postni chiqarishdan oldin tekshiradi. Ball QA_MIN_SCORE dan past bo'lsa,
kamchiliklar ro'yxati bilan writer agentiga qaytaradi.
"""
import re

from src import config
from src.utils import gemini

ALLOWED_TAGS = {"b", "i", "u", "s", "code", "pre", "a", "tg-spoiler", "blockquote"}

PROMPT = """Sen ingliz tili o'rgatuvchi o'zbek Telegram kanalining qat'iy sifat nazoratchisisan.
Vazifang — sifatsiz postni kanalga chiqib ketishiga yo'l qo'ymaslik.

=== KANAL USLUBI ===
{style_guide}

=== TEKSHIRILAYOTGAN POST ===
{post}
=== POST TUGADI ===

Mavzu: {topic}

DIQQAT: postning eng oxiridagi reklama qatori ({promo}) va kanal manzili
tizim tomonidan avtomatik qo'shilgan. Ularni kamchilik yoki reklama deb hisoblama,
uslubga mos emas dema — ular shunday bo'lishi kerak.

Quyidagi mezonlar bo'yicha tekshir:
1. GRAMMATIKA — inglizcha jumlalarda birorta ham xato bormi? (eng muhim mezon)
2. TARJIMA — o'zbekcha tarjimalar to'g'ri va tabiiymi? So'zma-so'z g'aliz emasmi?
3. FAKT — berilgan ta'rif, ma'no va qoidalar haqiqatga mos keladimi?
4. USLUB — yuqoridagi tuzilishga (sarlavha, misollar, maslahat, hashtag) mos keladimi?
5. FORMAT — faqat <b>, <i>, <u>, <code> teglari ishlatilganmi? Markdown yo'qmi?
6. UZUNLIK — 450-900 belgi orasidami?
7. TIL — o'zbek tili toza, ruscha so'zlarsizmi?
8. QIYMAT — o'quvchi bu postdan aniq bir yangi narsa o'rganadimi?

Baholashda qattiqqo'l bo'l. Bitta inglizcha grammatik xato bo'lsa — ball 5 dan oshmasin.

JAVOB FORMATI — faqat quyidagi JSON obyektni qaytar:

{{
  "score": 8,
  "passed": true,
  "issues": ["Topilgan aniq kamchilik 1", "Kamchilik 2"],
  "critical": ["Faktik yoki grammatik xato bo'lsa shu yerga"]
}}

Agar hech qanday kamchilik bo'lmasa, issues va critical bo'sh ro'yxat bo'lsin."""


def _check_html(post: str) -> list:
    """Telegram qabul qilmaydigan teglarni topadi — bu API xatosiga olib keladi."""
    problems = []
    tags = re.findall(r"</?([a-zA-Z0-9-]+)[^>]*>", post)
    bad = {t.lower() for t in tags} - ALLOWED_TAGS
    if bad:
        problems.append(
            f"Telegram qo'llab-quvvatlamaydigan HTML teg(lar): {', '.join(sorted(bad))}"
        )

    for tag in ALLOWED_TAGS:
        opens = len(re.findall(rf"<{tag}(?:\s[^>]*)?>", post, re.I))
        closes = len(re.findall(rf"</{tag}>", post, re.I))
        if opens != closes:
            problems.append(f"<{tag}> tegi yopilmagan ({opens} ochilgan, {closes} yopilgan)")

    if re.search(r"\*\*|__", post):
        problems.append("Markdown belgilari (** yoki __) ishlatilgan — Telegram HTML rejimida ishlamaydi")

    return problems


def run(post_text: str, topic: str) -> dict:
    # Avval mexanik tekshiruv — bu ishonchli va bepul
    mechanical = _check_html(post_text)

    length = len(post_text)
    if length > config.MAX_CAPTION_CHARS:
        mechanical.append(
            f"Post juda uzun ({length} belgi). {config.MAX_CAPTION_CHARS} belgidan qisqartir."
        )
    elif length < 300:
        mechanical.append(f"Post juda qisqa ({length} belgi). Kamida 450 belgi bo'lsin.")

    # Keyin AI tekshiruvi
    prompt = PROMPT.format(
        style_guide=config.STYLE_GUIDE,
        post=post_text,
        topic=topic,
        promo=config.PROMO_BOT,
    )

    try:
        raw = gemini.generate_text(prompt, json_output=True, temperature=0.2)
        data = gemini.parse_json(raw)
    except Exception as exc:  # noqa: BLE001
        print(f"[qa] AI tekshiruvi ishlamadi ({exc}), faqat mexanik tekshiruv qo'llanildi.")
        data = {"score": 7, "issues": [], "critical": []}

    try:
        score = int(data.get("score", 0))
    except (TypeError, ValueError):
        score = 0

    issues = list(data.get("issues") or [])
    critical = list(data.get("critical") or [])
    issues = mechanical + issues

    passed = (
        score >= config.QA_MIN_SCORE
        and not critical
        and not mechanical
    )

    print(f"[qa] Ball: {score}/10 — {'O`TDI' if passed else 'RAD ETILDI'}")
    for issue in (critical + issues)[:6]:
        print(f"[qa]   • {issue}")

    return {
        "score": score,
        "passed": passed,
        "issues": issues,
        "critical": critical,
        "feedback": "\n".join(f"- {i}" for i in (critical + issues)),
    }
