#!/usr/bin/env python3
"""Render og.png (1200x630) for The Diffusion Index — darkroom / spectral card.
Charcoal + film grain, a prismatic spectral bar, a chromatic-aberration serif title.
Pillow only; graceful fallback if unavailable."""
from __future__ import annotations

import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))

# the spectrum stops (matches style.css)
SPECTRUM = [(255, 59, 107), (255, 138, 61), (255, 210, 61), (77, 255, 166),
            (77, 212, 255), (123, 123, 255), (199, 125, 255)]


def _font(paths, size):
    from PIL import ImageFont
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _spectral_bar(draw, x0, y0, w, h):
    segs = len(SPECTRUM) - 1
    for px in range(w):
        f = px / max(w - 1, 1) * segs
        i = min(int(f), segs - 1)
        draw.line([(x0 + px, y0), (x0 + px, y0 + h)], fill=_lerp(SPECTRUM[i], SPECTRUM[i + 1], f - i))


def main() -> int:
    try:
        from PIL import Image, ImageDraw
    except Exception:
        print("Pillow not available — skipping og.png")
        return 0
    try:
        data = json.load(open(os.path.join(HERE, "data.json"), encoding="utf-8"))
        count, cats = data.get("count", 0), len(data.get("categories", []))
    except Exception:
        count, cats = 0, 0

    W, H = 1200, 630
    bg, ink, muted = (9, 9, 11), (243, 241, 247), (162, 159, 175)
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)

    # chromatic dispersion glow (faint spectral wash, upper-left)
    glow = Image.new("RGB", (W, H), bg)
    gd = ImageDraw.Draw(glow)
    for px in range(0, W, 3):
        f = px / W
        i = min(int(f * (len(SPECTRUM) - 1)), len(SPECTRUM) - 2)
        gd.line([(px, 0), (px, 300)], fill=_lerp(SPECTRUM[i], SPECTRUM[i + 1], f * (len(SPECTRUM) - 1) - i))
    try:
        from PIL import ImageFilter
        glow = glow.filter(ImageFilter.GaussianBlur(110))
        img = Image.blend(img, glow, 0.10)
        d = ImageDraw.Draw(img)
    except Exception:
        pass

    # film grain
    rnd = random.Random(count or 7)
    for _ in range(9000):
        x, y = rnd.randint(0, W - 1), rnd.randint(0, H - 1)
        v = rnd.randint(0, 26)
        img.putpixel((x, y), (bg[0] + v, bg[1] + v, bg[2] + v))
    d = ImageDraw.Draw(img)

    # top spectral seam
    _spectral_bar(d, 0, 0, W, 4)

    serif = ["/System/Library/Fonts/Supplemental/Didot.ttc",
             "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
             "/System/Library/Fonts/Supplemental/Georgia.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"]
    mono = ["/System/Library/Fonts/Menlo.ttc", "/System/Library/Fonts/Monaco.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]
    f_kick = _font(mono, 23)
    f_h1 = _font(serif, 92)
    f_stat = _font(mono, 27)

    # wordmark — spectral node + label
    d.ellipse([70, 74, 96, 100], outline=(199, 125, 255), width=4)
    d.ellipse([80, 84, 86, 90], fill=(77, 212, 255))
    d.text((112, 76), "THE DIFFUSION INDEX", font=f_kick, fill=muted)

    # chromatic-aberration title: red channel left, cyan channel right, ink on top
    def ca_text(xy, text, font):
        x, y = xy
        d.text((x - 4, y), text, font=font, fill=(255, 59, 107))
        d.text((x + 4, y), text, font=font, fill=(77, 212, 255))
        d.text((x, y), text, font=font, fill=ink)

    ca_text((66, 188), "The generative", f_h1)
    ca_text((66, 300), "stack, developed.", f_h1)

    # baseline rule + stats
    _spectral_bar(d, 70, 470, W - 140, 3)
    d.text((70, 500), f"{count} tools  ·  {cats} categories  ·  ranked daily by GitHub momentum",
           font=f_stat, fill=muted)

    img.save(os.path.join(HERE, "og.png"))
    print(f"wrote og.png ({count} tools)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
