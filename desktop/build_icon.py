from PIL import Image, ImageDraw

size = 256
img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

gap = size // 14
half = size // 2
radius = size // 9
colors = ["#F87171", "#60A5FA", "#FB923C", "#A78BFA"]
coords = [(0, 0), (1, 0), (0, 1), (1, 1)]

for color, (col, row) in zip(colors, coords):
    x = col * half + gap
    y = row * half + gap
    w = half - gap * 2
    h = half - gap * 2
    draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=color)

img.save("icon.ico", format="ICO", sizes=[(256, 256), (64, 64), (32, 32), (16, 16)])
print("icon.ico created.")
