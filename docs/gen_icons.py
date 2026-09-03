"""Generates the PWA PNG icons (192, 512, and a maskable 512) using the same
four-square design as the desktop app's icon.ico (see ../build_icon.py).
Run once with: python gen_icons.py
"""
from PIL import Image, ImageDraw

COLORS = ["#F87171", "#60A5FA", "#FB923C", "#A78BFA"]
COORDS = [(0, 0), (1, 0), (0, 1), (1, 1)]


def draw_squares(size: int, gap_ratio: float, radius_ratio: float) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    gap = int(size * gap_ratio)
    half = size // 2
    radius = int(size * radius_ratio)
    for color, (col, row) in zip(COLORS, COORDS):
        x = col * half + gap
        y = row * half + gap
        w = half - gap * 2
        h = half - gap * 2
        draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=color)
    return img


# Standard icons (content fills most of the canvas)
draw_squares(192, 1 / 14, 1 / 9).save("icons/icon-192.png")
draw_squares(512, 1 / 14, 1 / 9).save("icons/icon-512.png")

# Maskable icon: Android may crop to a circle/rounded-square, so keep all
# content inside the safe zone (center ~80% of the canvas).
maskable = Image.new("RGBA", (512, 512), (0, 0, 0, 255))
inner = draw_squares(410, 1 / 12, 1 / 8)
maskable.alpha_composite(inner, (51, 51))
maskable.save("icons/icon-maskable-512.png")

print("Icons written to icons/")
