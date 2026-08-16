"""
1-AGENT — Mavzu qidiruvchi.

Rubrika ichidan yangi, foydali va hali chiqarilmagan mavzu topadi.
Google Search grounding orqali internetdan real ma'lumot yig'adi.
"""
from src import config
from src.utils import gemini

PROMPT = """Sen o'zbek tilida ingliz tili o'rgatuvchi Telegram kanali uchun kontent tadqiqotchisisan.

KANAL RUBRIKASI: {rubric}
BUGUNGI KATEGORIYA: {category_name}
KATEGORIYA DOIRASI: {category_brief}

VAZIFA:
Shu kategoriya ichidan BITTA aniq, tor va amaliy mavzu tanla.
Qidiruv vositasi mavjud bo'lsa, undan foydalanib faktlarni tekshir.

TALABLAR:
- Mavzu tor va aniq bo'lsin. "Ingliz tili grammatikasi" — juda keng, YAROQSIZ.
  "Present Perfect va Past Simple orasidagi farq" — to'g'ri.
- O'zbek tilida so'zlashuvchi o'rganuvchilar uchun amaliy foyda keltirsin.
- Ularga xos tipik xatolarni hisobga ol (o'zbek tilida artikl yo'q, zamonlar tizimi boshqacha,
  "make/do", "say/tell" farqi qiyin, predloglar chalkashadi va hokazo).
- Ishonchli manbalarga tayan: Cambridge Dictionary, British Council, Merriam-Webster,
  IELTS.org, Oxford Learner's Dictionaries.
- Ma'nolar, misollar va talaffuz to'g'ri ekanligini qidiruv orqali tekshir.

QUYIDAGI MAVZULAR YAQINDA CHIQARILGAN — ULARNI VA ULARGA JUDA YAQIN MAVZULARNI TANLAMA:
{recent}

JAVOB FORMATI — faqat quyidagi JSON obyektni qaytar, boshqa hech narsa yozma:

{{
  "topic": "Mavzu nomi o'zbek tilida, qisqa (60 belgidan kam)",
  "target_expression": "Asosiy inglizcha ibora, so'z yoki qoida nomi",
  "why_useful": "Nega bu o'zbek o'rganuvchiga foydali — 1 jumla",
  "common_mistake": "O'zbeklar shu mavzuda qiladigan eng tipik xato — 1 jumla",
  "facts": [
    "Qidiruvdan olingan aniq fakt yoki ta'rif 1",
    "Aniq fakt 2",
    "Aniq fakt 3"
  ],
  "examples": [
    "To'g'ri inglizcha misol jumla 1",
    "To'g'ri inglizcha misol jumla 2",
    "To'g'ri inglizcha misol jumla 3"
  ],
  "sources": ["manba sayt nomi 1", "manba sayt nomi 2"]
}}"""


def run(category_key: str, recent_topics: list) -> dict:
    cat = config.CATEGORIES[category_key]
    recent = "\n".join(f"- {t}" for t in recent_topics[-60:]) or "- (hali yo'q)"

    prompt = PROMPT.format(
        rubric=config.RUBRIC,
        category_name=cat["name"],
        category_brief=cat["brief"],
        recent=recent,
    )

    raw = gemini.generate_text(
        prompt,
        use_search=config.USE_SEARCH_GROUNDING,
        json_output=not config.USE_SEARCH_GROUNDING,
        temperature=1.1,
    )
    data = gemini.parse_json(raw)

    if not data.get("topic"):
        raise ValueError("Researcher mavzu qaytarmadi")

    data["category"] = category_key
    print(f"[researcher] Mavzu: {data['topic']}")
    return data
