"""
6-AGENT — Tasdiq so'rovchi.

Tayyor postni adminga yuboradi va tugma bosilishini kutadi.
Server kerak emas: getUpdates orqali javob so'raladi.

Qaytaradigan qarorlar: "publish" | "cancel" | "regenerate" | "timeout"
"""
import time

from src import config
from src.agents import publisher

YES_WORDS = {"ha", "+", "ok", "okay", "yes", "chiqar", "chiqarish", "tasdiq", "tasdiqlayman", "✅"}
NO_WORDS = {"yo'q", "yoq", "-", "no", "bekor", "kerakmas", "❌"}
AGAIN_WORDS = {"qayta", "qaytadan", "boshqa", "regen", "🔄"}


def _decide(text: str) -> str | None:
    t = (text or "").strip().lower()
    if t in YES_WORDS:
        return "publish"
    if t in NO_WORDS:
        return "cancel"
    if t in AGAIN_WORDS:
        return "regenerate"
    return None


def send_preview(post_text: str, image_path: str | None, token: str, meta: str) -> dict:
    """Postni adminga tugmalar bilan yuboradi."""
    chat = config.ADMIN_CHAT_ID
    kb = publisher.keyboard(token)

    publisher.send_message(chat, meta)

    if image_path and len(post_text) <= config.MAX_CAPTION_CHARS:
        return publisher.send_photo(chat, image_path, caption=post_text, reply_markup=kb)

    if image_path:
        publisher.send_photo(chat, image_path)
    return publisher.send_message(chat, post_text, reply_markup=kb)


def wait_for_decision(token: str, preview_message_id: int,
                      wait_minutes: int | None = None) -> str:
    """Tugma bosilishini yoki matnli javobni kutadi."""
    wait = (wait_minutes if wait_minutes is not None else config.APPROVAL_WAIT_MINUTES)
    deadline = time.monotonic() + wait * 60
    offset = publisher.latest_offset()
    chat = str(config.ADMIN_CHAT_ID)

    print(f"[approver] Javob kutilmoqda ({wait} daqiqa)...")

    while time.monotonic() < deadline:
        remaining = int(deadline - time.monotonic())
        try:
            updates = publisher.get_updates(offset, long_poll=min(25, max(1, remaining)))
        except Exception as exc:  # noqa: BLE001
            print(f"[approver] getUpdates xatosi: {exc}")
            time.sleep(10)
            continue

        for upd in updates:
            offset = upd["update_id"] + 1

            cq = upd.get("callback_query")
            if cq:
                data = cq.get("data", "")
                action, _, tok = data.partition(":")
                from_id = str((cq.get("from") or {}).get("id", ""))

                if from_id != chat:
                    publisher.answer_callback(cq["id"], "Bu tugma siz uchun emas.")
                    continue
                if tok != token:
                    publisher.answer_callback(cq["id"], "Bu eski post — tugma ishlamaydi.")
                    continue

                labels = {"pub": "✅ Chiqarilmoqda...",
                          "cancel": "❌ Bekor qilindi",
                          "regen": "🔄 Qaytadan yozilmoqda..."}
                publisher.answer_callback(cq["id"], labels.get(action, "?"))
                publisher.clear_buttons(chat, preview_message_id)

                decision = {"pub": "publish", "cancel": "cancel", "regen": "regenerate"}.get(action)
                if decision:
                    print(f"[approver] Qaror: {decision}")
                    return decision

            msg = upd.get("message")
            if msg and str((msg.get("from") or {}).get("id", "")) == chat:
                decision = _decide(msg.get("text", ""))
                if decision:
                    publisher.clear_buttons(chat, preview_message_id)
                    print(f"[approver] Qaror (matn orqali): {decision}")
                    return decision

    print("[approver] Vaqt tugadi — javob kelmadi.")
    publisher.clear_buttons(chat, preview_message_id)
    return "timeout"


def run(post_text: str, image_path: str | None, token: str, meta: str,
        wait_minutes: int | None = None) -> str:
    preview = send_preview(post_text, image_path, token, meta)
    return wait_for_decision(token, preview.get("message_id"), wait_minutes)
