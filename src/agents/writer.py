"""
2-AGENT — Post yozuvchi.

Researcher topgan mavzudan kanal uslubiga mos post matnini yozadi.
Shu bilan birga rasm uchun sahna tavsifini (image_brief) ham beradi.
"""
from src import config
from src.utils import gemini

PROMPT = """Sen "{channel}" Telegram kanali uchun kontent yozuvchisisan.
Kanal o'zbek tilida so'zlashuvchilarga ingliz tilini o'rgatadi.

=== KANAL USLUBI (qat'iy amal qil) ===
{style_guide}

=== NAMUNA POST (aynan shu ko'rinishga taqlid qil) ===
{example}
=== NAMUNA TUGADI ===

=== BUGUNGI MAVZU ===
Kategoriya: {category_name}
Mavzu: {topic}
Asosiy ibora/qoida: {target}
Nega foydali: {why}
Tipik xato: {mistake}

Tekshirilgan faktlar:
{facts}

Tayyor misollar (ishlatishing yoki yaxshiroqlarini yozishing mumkin):
{examples}
=== MAVZU TUGADI ===

VAZIFA:
1. Yuqoridagi uslub va namunaga to'liq mos post yoz.
2. Faktlarga sodiq qol — o'zingdan ma'lumot to'qima.
3. Inglizcha jumlalar grammatik jihatdan mukammal bo'lsin.
4. O'zbekcha tarjimalar tabiiy bo'lsin — so'zma-so'z emas, ma'noni bersin.
5. Post uzunligi 450-900 belgi orasida bo'lsin (bu qat'iy chegara).
6. Telegram HTML: faqat <b>, <i>, <u>, <code>. Markdown ISHLATMA.

Shuningdek, post uchun rasm sahnasini o'ylab top:
- "image_headline": rasmda ko'rinadigan JUDA qisqa inglizcha matn (2-4 so'z, 22 belgidan kam).
  Bu asosiy ibora yoki qoida bo'lsin. Faqat lotin harflari va bo'shliq.
- "image_subtext": shu iboraning o'zbekcha ma'nosi — juda qisqa (40 belgidan kam).
  Masalan: "juda oson ish" yoki "o'tmishdagi odat haqida".
- "image_scene": rasm sahnasining inglizcha tavsifi (1-2 jumla).
  Mavzuni vizual metafora orqali ko'rsatsin. Sahnada YOZUV bo'lmasin —
  faqat obyektlar, odamlar, harakat. Sodda va aniq tasvirla.

JAVOB FORMATI — faqat quyidagi JSON obyektni qaytar:

{{
  "post_text": "To'liq post matni HTML formatida, qatorlar \\n bilan ajratilgan",
  "image_headline": "Short English Phrase",
  "image_subtext": "o'zbekcha qisqa ma'no",
  "image_scene": "English description of the visual scene without any text",
  "hashtags": ["#ingliztili", "#multilevel", "#mavzuteg"]
}}"""


def run(topic_data: dict, feedback: str | None = None, variant: int = 0) -> dict:
    cat = config.CATEGORIES[topic_data["category"]]

    facts = "\n".join(f"- {f}" for f in topic_data.get("facts", [])) or "- (yo'q)"
    examples = "\n".join(f"- {e}" for e in topic_data.get("examples", [])) or "- (yo'q)"

    prompt = PROMPT.format(
        channel=config.CHANNEL_HANDLE,
        style_guide=config.STYLE_GUIDE,
        example=config.EXAMPLE_POST,
        category_name=cat["name"],
        topic=topic_data.get("topic", ""),
        target=topic_data.get("target_expression", ""),
        why=topic_data.get("why_useful", ""),
        mistake=topic_data.get("common_mistake", ""),
        facts=facts,
        examples=examples,
    )

    if feedback:
        prompt += (
            "\n\n=== AVVALGI URINISH RAD ETILDI ===\n"
            "Sifat nazoratchisi quyidagi kamchiliklarni topdi. "
            "Yangi versiyada ularning HAMMASINI tuzat:\n"
            f"{feedback}\n"
        )

    raw = gemini.generate_text(prompt, json_output=True, temperature=1.0)
    data = gemini.parse_json(raw)

    post = (data.get("post_text") or "").strip()
    if not post:
        raise ValueError("Writer bo'sh post qaytardi")

    # Model baribir reklama/kanal qatorini yozib yuborgan bo'lsa — olib tashlaymiz,
    # keyin tizim o'zinikini qo'shadi. Shunda ikki marta takrorlanmaydi.
    kept = [
        ln for ln in post.split("\n")
        if config.CHANNEL_HANDLE not in ln and config.PROMO_BOT not in ln
    ]
    post = "\n".join(kept).rstrip()

    data["body_length"] = len(post)
    post += config.build_footer(variant)

    data["post_text"] = post
    data["image_headline"] = (data.get("image_headline") or "").strip()[:22]
    data["image_subtext"] = (data.get("image_subtext") or "").strip()[:44]
    data["image_scene"] = (data.get("image_scene") or "").strip()

    print(f"[writer] Post tayyor ({len(post)} belgi)")
    return data
