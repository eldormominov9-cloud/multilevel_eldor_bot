"""Gemini API bilan ishlash uchun yordamchi funksiyalar."""
import json
import re
import time

from google import genai
from google.genai import types

from src import config

_client = None


def client() -> "genai.Client":
    global _client
    if _client is None:
        if not config.GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY topilmadi. GitHub Secrets'ga qo'shganingizni tekshiring."
            )
        _client = genai.Client(api_key=config.GEMINI_API_KEY)
    return _client


def _retry(fn, attempts: int = 3, base_delay: float = 4.0):
    """Vaqtinchalik tarmoq/limit xatolarida qayta urinadi."""
    last = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - SDK turli xato turlarini qaytaradi
            last = exc
            msg = str(exc).lower()
            fatal = any(k in msg for k in ("api key", "permission", "unauthenticated", "invalid argument"))
            if fatal or i == attempts - 1:
                raise
            time.sleep(base_delay * (2 ** i))
    raise last  # pragma: no cover


def generate_text(prompt: str, *, use_search: bool = False,
                  json_output: bool = False, temperature: float = 1.0) -> str:
    """Matn generatsiya qiladi. use_search=True bo'lsa Google Search'ga ulanadi."""
    cfg_kwargs = {"temperature": temperature}

    if use_search:
        # Qidiruv vositasi bilan JSON rejimini birga ishlatib bo'lmaydi —
        # shuning uchun JSON'ni matndan ajratib olamiz.
        cfg_kwargs["tools"] = [types.Tool(google_search=types.GoogleSearch())]
    elif json_output:
        cfg_kwargs["response_mime_type"] = "application/json"

    def _make(model, kwargs):
        return lambda: client().models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(**kwargs),
        )

    try:
        resp = _retry(_make(config.TEXT_MODEL, cfg_kwargs))
    except Exception as exc:  # noqa: BLE001
        msg = str(exc).lower()

        # Grounding kvotasi tugagan bo'lsa — qidiruvsiz qayta urinamiz
        if use_search and ("resource_exhausted" in msg or "429" in msg or "quota" in msg):
            print("[gemini] Qidiruv kvotasi tugagan — model bilimiga tayanib davom etamiz.")
            cfg_kwargs.pop("tools", None)
            if json_output:
                cfg_kwargs["response_mime_type"] = "application/json"
            resp = _retry(_make(config.TEXT_MODEL, cfg_kwargs))

        # Asosiy model band bo'lsa — zaxira modelga o'tamiz
        elif "unavailable" in msg or "503" in msg or "overloaded" in msg:
            print(f"[gemini] {config.TEXT_MODEL} band — {config.TEXT_MODEL_FALLBACK} ishlatiladi.")
            resp = _retry(_make(config.TEXT_MODEL_FALLBACK, cfg_kwargs))
        else:
            raise

    return (resp.text or "").strip()


def parse_json(raw: str) -> dict:
    """Model javobidan JSON obyektni ajratib oladi (```json bloklarini ham qo'llab-quvvatlaydi)."""
    if not raw:
        raise ValueError("Model bo'sh javob qaytardi")

    text = raw.strip()

    fence = re.search(r"```(?:json)?\s*(.+?)\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Eng tashqi { ... } bo'lagini topamiz
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"JSON ajratib bo'lmadi. Model javobi:\n{raw[:600]}")


def generate_image(prompt: str) -> bytes | None:
    """Rasm generatsiya qiladi. Muvaffaqiyatsiz bo'lsa None qaytaradi (post rasmsiz chiqadi)."""
    def _call():
        return client().models.generate_content(
            model=config.IMAGE_MODEL,
            contents=prompt,
        )

    try:
        resp = _retry(_call, attempts=2, base_delay=6.0)
    except Exception as exc:  # noqa: BLE001
        print(f"[imager] Rasm generatsiya qilinmadi: {exc}")
        return None

    for candidate in (resp.candidates or []):
        content = getattr(candidate, "content", None)
        for part in (getattr(content, "parts", None) or []):
            inline = getattr(part, "inline_data", None)
            if inline is not None and getattr(inline, "data", None):
                return inline.data

    print("[imager] Javobda rasm topilmadi.")
    return None
