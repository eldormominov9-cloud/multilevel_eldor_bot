"""
Oflayn sinov: Gemini va Telegram chaqiruvlari soxta javoblar bilan almashtiriladi.
Tarmoq va API kalit talab qilmaydi.

Ishlatish:  python tests/mock_run.py
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("GEMINI_API_KEY", "fake")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "fake")
os.environ.setdefault("TELEGRAM_CHANNEL_ID", "@Multilevel_Eldor")
os.environ.setdefault("ADMIN_CHAT_ID", "555000555")
os.environ.setdefault("GITHUB_RUN_ID", "123456789")

from src import config  # noqa: E402
from src.utils import gemini  # noqa: E402
from src.agents import qa, publisher  # noqa: E402

TOKEN = "123456789"
ADMIN = "555000555"

GOOD_POST = """🎯 <b>"Used to"</b> — o'tmishdagi odat haqida qanday gapiriladi?

Ilgari muntazam qilgan, hozir esa qilmaydigan ishlaringiz haqida gapirganda <b>used to</b> ishlatiladi. Bu tuzilmadan keyin fe'l har doim asl shaklda keladi.

📌 Misollar:
• I used to drink coffee every morning.
   — Ilgari har kuni ertalab qahva ichardim.
• She used to live in Tashkent.
   — U ilgari Toshkentda yashagan.

💡 Tipik xato: "I used to drinking" emas, "I used to drink". Keyin doim oddiy fe'l.

#ingliztili #grammatika #multilevel
👉 @Multilevel_Eldor"""

BAD_POST = """**Used to** — bu nima?

<span>Ilgari</span> qilgan ishlar.

#ingliztili"""

state = {"writer": 0, "sent_to_channel": None, "previews": 0, "admin_msgs": []}
fails = []


# --------------------------------------------------------------------------
# Soxta Gemini
# --------------------------------------------------------------------------
def fake_text(prompt, *, use_search=False, json_output=False, temperature=1.0):
    if "kontent tadqiqotchisisan" in prompt:
        return json.dumps({
            "topic": "Used to — o'tmishdagi odatlar",
            "target_expression": "used to",
            "why_useful": "O'zbeklar o'tmishdagi odatni ifodalashda qiynaladi.",
            "common_mistake": "'used to' dan keyin -ing qo'shib yuborish.",
            "facts": ["used to + infinitive", "faqat o'tmish uchun"],
            "examples": ["I used to play football."],
            "sources": ["Cambridge Dictionary"],
        }, ensure_ascii=False)

    if "kontent yozuvchisisan" in prompt:
        state["writer"] += 1
        post = BAD_POST if state["writer"] == 1 else GOOD_POST
        return json.dumps({
            "post_text": post,
            "image_headline": "Used To",
            "image_subtext": "o'tmishdagi odat haqida",
            "image_scene": "a person looking at an old photo album",
            "hashtags": ["#ingliztili", "#grammatika", "#multilevel"],
        }, ensure_ascii=False)

    if "sifat nazoratchisisan" in prompt:
        good = "Tipik xato" in prompt
        return json.dumps({
            "score": 9 if good else 4,
            "issues": [] if good else ["Misollar yo'q"],
            "critical": [] if good else ["Markdown ishlatilgan"],
        }, ensure_ascii=False)

    raise AssertionError("Kutilmagan prompt")


def fake_image(prompt):
    return None  # AI ishlamadi -> kartochkaga tushishi kerak


# --------------------------------------------------------------------------
# Soxta Telegram
# --------------------------------------------------------------------------
def install_telegram_mocks(updates_queue):
    def send_photo(chat_id, image_path, caption=None, reply_markup=None):
        if str(chat_id) == ADMIN and reply_markup:
            state["previews"] += 1
        else:
            state["sent_to_channel"] = {"text": caption, "image": image_path}
        return {"message_id": 1000 + state["previews"]}

    def send_message(chat_id, text, reply_markup=None):
        if str(chat_id) == ADMIN:
            state["admin_msgs"].append(text)
        else:
            state["sent_to_channel"] = {"text": text, "image": None}
        return {"message_id": 2000}

    def send_post(post_text, image_path, chat_id=None):
        state["sent_to_channel"] = {"text": post_text, "image": image_path}
        return {"message_id": 3000}

    publisher.send_photo = send_photo
    publisher.send_message = send_message
    publisher.send_post = send_post
    publisher.latest_offset = lambda: 0
    publisher.get_updates = lambda offset, long_poll=25: (
        [updates_queue.pop(0)] if updates_queue else []
    )
    publisher.clear_buttons = lambda *a, **k: None
    publisher.answer_callback = lambda *a, **k: None
    publisher.notify_admin = lambda t: state["admin_msgs"].append(t)


def cb(action):
    return {"update_id": 1, "callback_query": {
        "id": "cb1", "data": f"{action}:{TOKEN}", "from": {"id": int(ADMIN)}}}


# --------------------------------------------------------------------------
def section(title):
    print(f"\n=== {title} ===")


def main():
    section("1. HTML / format tekshiruvi")
    for text, want_problem in [("<b>ok</b>", False), ("<b>yopilmagan", True),
                               ("<span>yaroqsiz</span>", True), ("**markdown**", True)]:
        got = len(qa._check_html(text)) > 0
        ok = got == want_problem
        if not ok:
            fails.append(f"HTML: {text!r}")
        print(f"  {'OK ' if ok else 'XATO'} {text[:26]!r} -> muammo={got}")

    section("2. Sozlamalar")
    print(f"  Matn modeli:      {config.TEXT_MODEL}")
    print(f"  Rasm modeli:      {config.IMAGE_MODEL}")
    print(f"  Rasm manbasi:     {config.IMAGE_SOURCE}")
    print(f"  Tasdiq:           {config.APPROVAL_REQUIRED}, {config.APPROVAL_WAIT_MINUTES} daq")
    print(f"  Vaqt tugasa:      {'chiqadi' if config.AUTO_PUBLISH_ON_TIMEOUT else 'chiqmaydi'}")
    print(f"  Caption limiti:   {config.MAX_CAPTION_CHARS}")
    if config.MAX_CAPTION_CHARS > 1024:
        fails.append("MAX_CAPTION_CHARS > 1024")

    section("3. Kartochka generatori")
    from src.utils import card
    for cat in config.CATEGORIES:
        p = card.render("Piece of Cake", "juda oson ish", cat, f"/tmp/t_{cat}.png")
        print(f"  {cat:11s} -> {os.path.getsize(p)//1024} KB")

    section("4. To'liq oqim — ✅ tugmasi bosildi")
    gemini.generate_text = fake_text
    gemini.generate_image = fake_image
    install_telegram_mocks([cb("pub")])

    import src.main as m
    sys.argv = ["main", "--category", "grammar", "--wait", "1"]
    code = m.run()

    print(f"  Chiqish kodi:        {code}")
    print(f"  Writer chaqiruvlari: {state['writer']} (2 kutilgan — 1-si QA'dan o'tmagan)")
    print(f"  Tasdiq so'rovlari:   {state['previews']}")
    print(f"  Kanalga yuborildi:   {bool(state['sent_to_channel'])}")
    print(f"  Rasm (AI yiqildi ->) {state['sent_to_channel'] and state['sent_to_channel']['image']}")

    if code != 0:
        fails.append(f"oqim kod {code}")
    if state["writer"] != 2:
        fails.append("QA sikli ishlamadi")
    if state["previews"] != 1:
        fails.append("tasdiq so'ralmadi")
    if not state["sent_to_channel"]:
        fails.append("kanalga yuborilmadi")
    elif "**" in state["sent_to_channel"]["text"]:
        fails.append("sifatsiz post yuborildi")
    elif not state["sent_to_channel"]["image"]:
        fails.append("zaxira kartochka ishlamadi")

    section("5. ❌ tugmasi — post chiqmasligi kerak")
    state.update({"writer": 0, "sent_to_channel": None, "previews": 0})
    install_telegram_mocks([cb("cancel")])
    code = m.run()
    print(f"  Chiqish kodi: {code} | Kanalga yuborildi: {bool(state['sent_to_channel'])}")
    if state["sent_to_channel"]:
        fails.append("bekor qilinganda ham yuborildi!")

    section("6. Javob yo'q — 30 daqiqadan keyin avtomatik chiqishi")
    state.update({"writer": 0, "sent_to_channel": None, "previews": 0})
    install_telegram_mocks([])          # hech qanday tugma bosilmadi
    sys.argv = ["main", "--category", "exam", "--wait", "0"]
    code = m.run()
    print(f"  Chiqish kodi: {code} | Kanalga yuborildi: {bool(state['sent_to_channel'])}")
    if config.AUTO_PUBLISH_ON_TIMEOUT and not state["sent_to_channel"]:
        fails.append("timeout'da avtomatik chiqmadi")

    section("7. 🔄 Qayta yozish -> keyin ✅")
    state.update({"writer": 0, "sent_to_channel": None, "previews": 0})
    install_telegram_mocks([cb("regen"), cb("pub")])
    sys.argv = ["main", "--category", "vocabulary", "--wait", "1"]
    code = m.run()
    print(f"  Tasdiq so'rovlari: {state['previews']} (2 kutilgan)")
    print(f"  Kanalga yuborildi: {bool(state['sent_to_channel'])}")
    if state["previews"] < 2:
        fails.append("qayta yozishdan keyin qayta so'ralmadi")
    if not state["sent_to_channel"]:
        fails.append("qayta yozishdan keyin yuborilmadi")

    print("\n" + "=" * 52)
    if fails:
        print(f"❌ {len(fails)} ta muammo:")
        for f in fails:
            print("   -", f)
        return 1
    print("✅ Barcha sinovlar o'tdi")
    return 0


if __name__ == "__main__":
    sys.exit(main())
