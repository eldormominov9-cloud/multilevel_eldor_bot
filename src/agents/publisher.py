"""
Telegram Bot API bilan ishlash.

Ikki vazifa:
  1. Kanalga post chiqarish
  2. Adminga tasdiq so'rovi yuborish va javobini kutish (approver.py ishlatadi)
"""
import json

import requests

from src import config

API = "https://api.telegram.org/bot{token}/{method}"
TIMEOUT = 90


def call(method: str, *, files=None, **data) -> dict:
    if not config.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN topilmadi. GitHub Secrets'ni tekshiring.")

    url = API.format(token=config.TELEGRAM_BOT_TOKEN, method=method)
    payload = {k: v for k, v in data.items() if v is not None}

    resp = requests.post(url, data=payload, files=files, timeout=TIMEOUT)
    try:
        body = resp.json()
    except ValueError:
        raise RuntimeError(f"Telegram javobi tushunarsiz (HTTP {resp.status_code}): {resp.text[:300]}")

    if not body.get("ok"):
        raise RuntimeError(
            f"Telegram xatosi ({method}): {body.get('error_code')} — {body.get('description')}"
        )
    return body["result"]


def keyboard(token: str) -> str:
    """Tasdiqlash tugmalari."""
    return json.dumps({
        "inline_keyboard": [[
            {"text": "✅ Chiqarish", "callback_data": f"pub:{token}"},
            {"text": "🔄 Qayta yozish", "callback_data": f"regen:{token}"},
            {"text": "❌ Bekor qilish", "callback_data": f"cancel:{token}"},
        ]]
    })


# ---------------------------------------------------------------------------
# Yuborish
# ---------------------------------------------------------------------------
def send_photo(chat_id: str, image_path: str, caption: str | None = None,
               reply_markup: str | None = None) -> dict:
    with open(image_path, "rb") as fh:
        return call(
            "sendPhoto",
            chat_id=chat_id,
            caption=caption,
            parse_mode="HTML" if caption else None,
            reply_markup=reply_markup,
            files={"photo": ("post.png", fh, "image/png")},
        )


def send_message(chat_id: str, text: str, reply_markup: str | None = None) -> dict:
    return call(
        "sendMessage",
        chat_id=chat_id,
        text=text,
        parse_mode="HTML",
        disable_web_page_preview="true",
        reply_markup=reply_markup,
    )


def send_post(post_text: str, image_path: str | None, chat_id: str | None = None) -> dict:
    """Tayyor postni kanalga (yoki berilgan chatga) chiqaradi."""
    target = chat_id or config.TELEGRAM_CHANNEL_ID
    if not target:
        raise RuntimeError("TELEGRAM_CHANNEL_ID topilmadi.")

    fits = len(post_text) <= config.MAX_CAPTION_CHARS

    if image_path and fits:
        result = send_photo(target, image_path, caption=post_text)
        print(f"[publisher] Rasm + matn yuborildi (message_id={result.get('message_id')})")
        return result

    if image_path:
        send_photo(target, image_path)

    result = send_message(target, post_text)
    print(f"[publisher] Matn yuborildi (message_id={result.get('message_id')})")
    return result


# ---------------------------------------------------------------------------
# Tahrirlash va javob berish
# ---------------------------------------------------------------------------
def clear_buttons(chat_id: str, message_id: int) -> None:
    for method in ("editMessageReplyMarkup",):
        try:
            call(method, chat_id=chat_id, message_id=message_id,
                 reply_markup=json.dumps({"inline_keyboard": []}))
        except Exception as exc:  # noqa: BLE001
            print(f"[publisher] Tugmalarni olib tashlab bo'lmadi: {exc}")


def answer_callback(callback_id: str, text: str) -> None:
    try:
        call("answerCallbackQuery", callback_query_id=callback_id, text=text)
    except Exception as exc:  # noqa: BLE001
        print(f"[publisher] answerCallbackQuery: {exc}")


# ---------------------------------------------------------------------------
# Yangiliklarni o'qish (tugma bosilishini kutish uchun)
# ---------------------------------------------------------------------------
def latest_offset() -> int:
    """Eski xabarlarni o'tkazib yuborish uchun boshlang'ich offset."""
    try:
        updates = call("getUpdates", offset=-1, limit=1, timeout=0)
    except Exception as exc:  # noqa: BLE001
        print(f"[publisher] getUpdates boshlang'ich: {exc}")
        return 0
    return (updates[-1]["update_id"] + 1) if updates else 0


def get_updates(offset: int, long_poll: int = 25) -> list:
    return call(
        "getUpdates",
        offset=offset,
        timeout=long_poll,
        allowed_updates=json.dumps(["callback_query", "message"]),
    )


def notify_admin(text: str) -> None:
    """Xatolik/holat haqida adminga xabar. ADMIN_CHAT_ID bo'lmasa jim o'tadi."""
    if not config.ADMIN_CHAT_ID or not config.TELEGRAM_BOT_TOKEN:
        return
    try:
        call("sendMessage", chat_id=config.ADMIN_CHAT_ID, text=text[:4000])
    except Exception as exc:  # noqa: BLE001
        print(f"[publisher] Adminga xabar yuborilmadi: {exc}")
