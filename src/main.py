"""
Multilevel_Eldor — avtomatik post tizimi.

Oqim:
  mavzu -> matn -> sifat nazorati -> rasm -> TASDIQ SO'RASH -> kanalga chiqarish

Ishlatish:
    python -m src.main                     # to'liq oqim (tasdiq so'raladi)
    python -m src.main --dry-run           # hech qayerga yubormaydi, out/ ga saqlaydi
    python -m src.main --no-approval       # tasdiqsiz, to'g'ridan-to'g'ri chiqaradi
    python -m src.main --wait 5            # tasdiq kutish vaqtini o'zgartirish (daqiqa)
    python -m src.main --category grammar  # kategoriyani majburiy tanlash
"""
import argparse
import os
import sys
import traceback
from datetime import datetime, timezone, timedelta

from src import config
from src.agents import researcher, writer, imager, qa, publisher, approver
from src.utils import history as hist

TASHKENT = timezone(timedelta(hours=5))


def parse_args():
    p = argparse.ArgumentParser(description="Multilevel_Eldor avtomatik post tizimi")
    p.add_argument("--dry-run", action="store_true",
                   help="Telegramga yubormaydi, natijani out/ ga saqlaydi")
    p.add_argument("--to", metavar="CHAT_ID",
                   help="Kanal o'rniga shu chatga yuboradi (sinov)")
    p.add_argument("--category", choices=list(config.CATEGORIES.keys()))
    p.add_argument("--no-approval", action="store_true", help="Tasdiq so'ramasdan chiqarish")
    p.add_argument("--wait", type=int, metavar="DAQIQA", help="Tasdiq kutish vaqti")
    p.add_argument("--no-image", action="store_true", help="Rasmsiz post")
    return p.parse_args()


def save_preview(post_text: str, image_path: str | None) -> None:
    os.makedirs("out", exist_ok=True)
    with open(os.path.join("out", "post.txt"), "w", encoding="utf-8") as f:
        f.write(post_text)
    print("\n" + "=" * 60)
    print(post_text)
    print("=" * 60)
    print(f"Uzunlik: {len(post_text)} belgi | Rasm: {image_path or 'yo`q'}")


def build_post(topic_data: dict, feedback: str | None, variant: int = 0):
    """Yozish + sifat nazorati sikli. (draft, review) qaytaradi."""
    draft = review = None
    for attempt in range(1, config.QA_MAX_RETRIES + 2):
        print(f"[main] Yozish urinishi {attempt}")
        draft = writer.run(topic_data, feedback=feedback, variant=variant)
        review = qa.run(draft["post_text"], topic_data.get("topic", ""))
        if review["passed"]:
            return draft, review
        feedback = review["feedback"]
    return draft, review


def run() -> int:
    args = parse_args()

    history = hist.load()
    category = args.category or hist.next_category(history)
    cat_name = config.CATEGORIES[category]["name"]
    print(f"[main] Kategoriya: {cat_name}")

    # --- 1-agent: mavzu ----------------------------------------------------
    topic_data = researcher.run(category, hist.recent_topics(history))

    # --- 2 + 4-agent: matn va sifat nazorati -------------------------------
    variant = len(history)
    draft, review = build_post(topic_data, None, variant)

    if not review["passed"]:
        print("[main] Sifat nazoratidan o'tmadi — post CHIQARILMAYDI.")
        publisher.notify_admin(
            "⚠️ Multilevel_Eldor: post sifat nazoratidan o'tmadi.\n\n"
            f"Mavzu: {topic_data.get('topic')}\nBall: {review['score']}/10\n\n"
            f"Kamchiliklar:\n{review['feedback']}"
        )
        save_preview(draft["post_text"], None)
        return 2

    # --- 3-agent: rasm -----------------------------------------------------
    def make_image():
        if args.no_image:
            return None
        return imager.run(
            category,
            draft.get("image_headline", ""),
            draft.get("image_scene", ""),
            draft.get("image_subtext", ""),
        )

    image_path = make_image()

    # --- Dry run -----------------------------------------------------------
    if args.dry_run:
        print("[main] DRY RUN — hech qayerga yuborilmadi.")
        save_preview(draft["post_text"], image_path)
        return 0

    # --- 6-agent: tasdiq so'rash -------------------------------------------
    approval_on = (
        config.APPROVAL_REQUIRED
        and not args.no_approval
        and not args.to
        and bool(config.ADMIN_CHAT_ID)
    )

    if config.APPROVAL_REQUIRED and not config.ADMIN_CHAT_ID and not args.to:
        print("[main] ⚠️ ADMIN_CHAT_ID yo'q — tasdiq so'ralmaydi, post to'g'ridan-to'g'ri chiqadi.")

    if approval_on:
        token = str(os.environ.get("GITHUB_RUN_ID") or int(datetime.now().timestamp()))[-9:]
        wait = args.wait if args.wait is not None else config.APPROVAL_WAIT_MINUTES
        regens = 0

        while True:
            now = datetime.now(TASHKENT).strftime("%H:%M")
            meta = (
                f"📝 Yangi post tayyor — {now}\n"
                f"Kategoriya: {cat_name}\n"
                f"Mavzu: {topic_data.get('topic')}\n"
                f"Sifat balli: {review['score']}/10\n"
                f"Uzunlik: {len(draft['post_text'])} belgi\n\n"
                f"⏳ {wait} daqiqa ichida javob bermasangiz, "
                f"{'post avtomatik chiqadi.' if config.AUTO_PUBLISH_ON_TIMEOUT else 'post chiqarilmaydi.'}"
            )

            decision = approver.run(draft["post_text"], image_path, token, meta, wait)

            if decision == "publish":
                break

            if decision == "cancel":
                publisher.notify_admin("❌ Post bekor qilindi, kanalga chiqarilmadi.")
                save_preview(draft["post_text"], image_path)
                return 0

            if decision == "regenerate":
                regens += 1
                if regens > config.MAX_REGENERATIONS:
                    publisher.notify_admin(
                        f"🔄 Qayta yozish chegarasi ({config.MAX_REGENERATIONS}) tugadi. "
                        "Post chiqarilmadi."
                    )
                    return 0
                print(f"[main] Qayta yozish {regens}/{config.MAX_REGENERATIONS}")
                draft, review = build_post(
                    topic_data,
                    "Admin bu variantni rad etdi. Butunlay boshqacha yondashuv bilan, "
                    "boshqa misollar va boshqa tuzilish bilan qaytadan yoz.",
                    variant + regens,
                )
                image_path = make_image()
                continue

            # timeout
            if config.AUTO_PUBLISH_ON_TIMEOUT:
                print("[main] Javob kelmadi — avtomatik chiqarilmoqda.")
                break
            publisher.notify_admin("⏳ Vaqt tugadi, javob kelmadi. Post chiqarilmadi.")
            save_preview(draft["post_text"], image_path)
            return 0

    # --- 5-agent: kanalga chiqarish ----------------------------------------
    publisher.send_post(draft["post_text"], image_path, chat_id=args.to)

    if not args.to:
        hist.append(history, {
            "category": category,
            "topic": topic_data.get("topic"),
            "target_expression": topic_data.get("target_expression"),
            "qa_score": review["score"],
            "had_image": bool(image_path),
        })
        print("[main] Tarix yangilandi.")
        publisher.notify_admin(f"✅ Kanalga chiqarildi: {topic_data.get('topic')}")

    save_preview(draft["post_text"], image_path)
    print("[main] Tayyor ✅")
    return 0


def main() -> None:
    try:
        sys.exit(run())
    except Exception as exc:  # noqa: BLE001
        traceback.print_exc()
        publisher.notify_admin(
            f"❌ Multilevel_Eldor: xatolik yuz berdi\n\n{type(exc).__name__}: {exc}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
