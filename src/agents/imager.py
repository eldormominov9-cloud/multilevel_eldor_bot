"""
3-AGENT — Rasm.

Ikki manba:
  - "ai"   : Gemini (nano-banana) generatsiya qiladi
  - "card" : kod bilan chiziladi (Pillow)

AI ishlamasa (kvota, xato, billing yoq) — avtomatik kartochkaga o'tadi.
Ya'ni post hech qachon rasmsiz qolmaydi.
"""
import os
import re

from src import config
from src.utils import gemini, card

OUT_DIR = "out"
OUT_PATH = os.path.join(OUT_DIR, "post.png")


def _safe_headline(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9 '\-!?]", "", text or "").strip()
    return cleaned[:22] or "English Tip"


def build_prompt(category_key: str, headline: str, scene: str) -> str:
    style_key = config.CATEGORIES[category_key]["image_style"]
    template = config.IMAGE_STYLES[style_key]
    return template.format(
        headline=_safe_headline(headline),
        scene=(scene or "learning English").strip(),
        channel=config.CHANNEL_HANDLE,
    )


def _from_ai(category_key: str, headline: str, scene: str) -> str | None:
    prompt = build_prompt(category_key, headline, scene)
    style_key = config.CATEGORIES[category_key]["image_style"]
    print(f"[imager] AI rasm, uslub: {style_key}")

    data = gemini.generate_image(prompt)
    if not data:
        return None

    if len(data) > 9_500_000:
        print("[imager] Rasm 10 MB dan katta — Telegram qabul qilmaydi.")
        return None

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_PATH, "wb") as f:
        f.write(data)
    print(f"[imager] AI rasm saqlandi ({len(data) // 1024} KB)")
    return OUT_PATH


def _from_card(category_key: str, headline: str, subtext: str) -> str | None:
    try:
        path = card.render(
            headline=_safe_headline(headline),
            subtext=subtext or "",
            category=category_key,
            out_path=OUT_PATH,
            channel=config.CHANNEL_HANDLE,
        )
        print(f"[imager] Kartochka chizildi ({os.path.getsize(path) // 1024} KB)")
        return path
    except Exception as exc:  # noqa: BLE001
        print(f"[imager] Kartochka chizilmadi: {exc}")
        return None


def run(category_key: str, headline: str, scene: str, subtext: str = "") -> str | None:
    source = config.IMAGE_SOURCE

    if source == "card":
        return _from_card(category_key, headline, subtext)

    path = _from_ai(category_key, headline, scene)
    if path:
        return path

    print("[imager] AI ishlamadi — zaxira kartochkaga o'tilmoqda.")
    return _from_card(category_key, headline, subtext)
