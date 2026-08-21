"""One-off script that renders assets/icon.ico for CameraX (app icon + tray icon).
Run manually with: .venv\\Scripts\\python.exe scripts\\make_icon.py
Requires Pillow (dev-only dependency, not needed at app runtime).
"""

from pathlib import Path

from PIL import Image, ImageDraw

OUT_DIR = Path(__file__).resolve().parent.parent / "assets"
OUT_DIR.mkdir(exist_ok=True)

BG = (23, 42, 74, 255)          # dark navy background
BODY = (235, 240, 245, 255)     # camera body
ACCENT = (64, 156, 255, 255)    # lens ring accent
LENS = (18, 24, 33, 255)        # lens glass


def render(size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    pad = size * 0.06
    d.rounded_rectangle([pad, pad, size - pad, size - pad], radius=size * 0.22, fill=BG)

    body_w = size * 0.62
    body_h = size * 0.40
    body_x0 = (size - body_w) / 2
    body_y0 = size * 0.34
    d.rounded_rectangle(
        [body_x0, body_y0, body_x0 + body_w, body_y0 + body_h],
        radius=size * 0.06,
        fill=BODY,
    )

    bump_w = size * 0.18
    bump_h = size * 0.09
    bump_x0 = body_x0 + body_w * 0.14
    bump_y0 = body_y0 - bump_h * 0.8
    d.rounded_rectangle(
        [bump_x0, bump_y0, bump_x0 + bump_w, bump_y0 + bump_h],
        radius=size * 0.02,
        fill=BODY,
    )

    cx = size / 2
    cy = body_y0 + body_h / 2
    r_outer = body_h * 0.42
    d.ellipse([cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer], fill=ACCENT)
    r_inner = r_outer * 0.62
    d.ellipse([cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner], fill=LENS)
    r_glint = r_inner * 0.35
    gx, gy = cx - r_inner * 0.35, cy - r_inner * 0.35
    d.ellipse([gx - r_glint, gy - r_glint, gx + r_glint, gy + r_glint], fill=(255, 255, 255, 140))

    return img


sizes = [16, 24, 32, 48, 64, 128, 256]
images = [render(s) for s in sizes]
images[-1].save(OUT_DIR / "icon.ico", sizes=[(s, s) for s in sizes])
images[-1].save(OUT_DIR / "icon.png")
print("wrote", OUT_DIR / "icon.ico", "and", OUT_DIR / "icon.png")
