"""
Dasturiy rasm generatori (Pillow).

AI'siz, bepul va aniq: yozuv har doim to'g'ri chiqadi va har post
bir xil brend uslubida bo'ladi. Kategoriyaga qarab rang sxemasi almashadi.
"""
import os
import textwrap

from PIL import Image, ImageDraw, ImageFont

SIZE = 1080
MARGIN = 88

# Kategoriya -> rang sxemasi
PALETTES = {
    "vocabulary": {"bg": "#FFF4E8", "accent": "#E8552F", "ink": "#1A1410", "muted": "#8A7566",
                   "label": "SO'Z BOYLIGI"},
    "grammar":    {"bg": "#EAF1FB", "accent": "#1F5FD0", "ink": "#0F1D33", "muted": "#6E829E",
                   "label": "GRAMMATIKA"},
    "exam":       {"bg": "#E9F6EF", "accent": "#0E8A5A", "ink": "#0C2A1E", "muted": "#6A8C7C",
                   "label": "MULTILEVEL / IELTS"},
    "method":     {"bg": "#F2ECFB", "accent": "#6A3FCC", "ink": "#211539", "muted": "#84759E",
                   "label": "METODIKA"},
}
DEFAULT = PALETTES["vocabulary"]

BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
]
REGULAR_CANDIDATES = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
]


def _font_path(candidates):
    for p in candidates:
        if os.path.exists(p):
            return p
    raise RuntimeError(
        "Shrift topilmadi. Workflow'ga qo'shing: sudo apt-get install -y fonts-liberation"
    )


def _font(bold: bool, size: int):
    return ImageFont.truetype(_font_path(BOLD_CANDIDATES if bold else REGULAR_CANDIDATES), size)


def _w(draw, text, font):
    return draw.textbbox((0, 0), text, font=font)[2]


def _tracked(draw, xy, text, font, fill, tracking):
    """Harflar orasiga bo'shliq qo'shib yozadi (letter-spacing)."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += _w(draw, ch, font) + tracking
    return x


def _fit_headline(draw, text, max_width, max_lines=3):
    """Sarlavhani maydonga sig'adigan eng katta o'lchamda joylashtiradi."""
    for size in range(132, 47, -4):
        font = _font(True, size)
        avg = max(_w(draw, "M", font) * 0.62, 1)
        wrap_at = max(int(max_width / avg), 6)
        lines = textwrap.wrap(text, width=wrap_at) or [text]
        if len(lines) <= max_lines and all(_w(draw, ln, font) <= max_width for ln in lines):
            return font, lines
    font = _font(True, 48)
    return font, textwrap.wrap(text, width=22)[:max_lines] or [text]


def render(headline: str, subtext: str, category: str = "vocabulary",
           out_path: str = "out/post.png", channel: str = "@Multilevel_Eldor") -> str:
    p = PALETTES.get(category, DEFAULT)

    img = Image.new("RGB", (SIZE, SIZE), p["bg"])
    draw = ImageDraw.Draw(img)

    # Fon bezagi — past shaffoflikdagi katta doira
    layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    accent_rgb = tuple(int(p["accent"][i:i + 2], 16) for i in (1, 3, 5))
    ld.ellipse([SIZE - 300, SIZE - 340, SIZE + 260, SIZE + 220], fill=accent_rgb + (26,))
    ld.ellipse([-190, -230, 190, 150], fill=accent_rgb + (18,))
    img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Yuqori aksent chizig'i
    draw.rectangle([0, 0, SIZE, 13], fill=p["accent"])

    # Kategoriya yorlig'i
    lf = _font(True, 25)
    label = p["label"]
    lw = sum(_w(draw, c, lf) + 5 for c in label) + 44
    draw.rounded_rectangle([MARGIN, 108, MARGIN + lw, 108 + 54], radius=27, fill=p["accent"])
    _tracked(draw, (MARGIN + 24, 108 + 13), label, lf, p["bg"], 5)

    # Sarlavha + izoh bloki — yorliq bilan pastki qator orasida vertikal markazlashtiriladi
    hf, lines = _fit_headline(draw, (headline or "").strip(), SIZE - MARGIN * 2)
    line_h = int(hf.size * 1.13)

    sf = _font(False, 40)
    sub_lines = textwrap.wrap((subtext or "").strip(), width=40)[:3]
    sub_h = 52 * len(sub_lines)

    RULE_GAP, RULE_H, AFTER_RULE = 26, 7, 44
    block_h = line_h * len(lines) + RULE_GAP + RULE_H + AFTER_RULE + sub_h

    top, bottom = 218, SIZE - MARGIN - 108
    y = top + max(0, (bottom - top - block_h) // 2)

    for ln in lines:
        draw.text((MARGIN, y), ln, font=hf, fill=p["ink"])
        y += line_h

    y += RULE_GAP
    draw.rectangle([MARGIN, y, MARGIN + 96, y + RULE_H], fill=p["accent"])
    y += RULE_H + AFTER_RULE

    for ln in sub_lines:
        draw.text((MARGIN, y), ln, font=sf, fill=p["muted"])
        y += 52

    # Pastki qator
    cf = _font(True, 27)
    draw.text((MARGIN, SIZE - MARGIN - 30), channel, font=cf, fill=p["muted"])
    for i in range(3):
        cx = SIZE - MARGIN - 12 - i * 34
        draw.ellipse([cx - 11, SIZE - MARGIN - 24, cx + 11, SIZE - MARGIN - 2],
                     fill=p["accent"] if i == 0 else None,
                     outline=p["accent"], width=4)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    img.save(out_path, "PNG", optimize=True)
    return out_path
