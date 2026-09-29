"""Generate assets/img/marquee-tape.webp: the aged gold tape behind the first marquee band.
Seamless left-to-right so it can scroll with the text. Run from the project root:
    python _source/build_tape.py      (needs Pillow only)"""
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageOps
import math, os, random

random.seed(1923)
W, H = 1600, 150                   # rendered at ~75px tall on desktop, so this is 2x
BASE = (201, 171, 129)             # #C9AB81
OUT = "assets/img/marquee-tape.webp"


def wrap_noise(w, h, cx, cy):
    """Value noise that tiles horizontally."""
    small = Image.new("L", (cx, cy))
    small.putdata([random.randrange(256) for _ in range(cx * cy)])
    tiled = Image.new("L", (cx * 3, cy))
    for i in range(3):
        tiled.paste(small, (i * cx, 0))
    return tiled.resize((w * 3, h), Image.BICUBIC).crop((w, 0, w * 2, h))


def mix(layers):
    acc = None
    for img, a in layers:
        layer = img.point(lambda v, a=a: v * a)
        acc = layer if acc is None else ImageChops.add(acc, layer)
    return ImageOps.autocontrast(acc)


def periodic_edge(n, amp, seed_parts=7):
    """Jagged edge offsets that wrap: sum of integer-frequency sines plus wrapped jitter."""
    phases = [(random.uniform(0, 6.283), random.randint(1, 40), random.uniform(0.2, 1)) for _ in range(seed_parts)]
    jitter = [random.uniform(-1, 1) for _ in range(n)]
    out = []
    for x in range(n):
        v = sum(a * math.sin(2 * math.pi * f * x / n + p) for p, f, a in phases) / seed_parts
        j = (jitter[x] + jitter[(x + 1) % n] + jitter[(x - 1) % n]) / 3
        out.append(amp * (0.5 + 0.35 * v + 0.35 * j))
    return out


def wrap_blur(img, radius):
    """Gaussian blur that stays seamless left-to-right: blur three copies side by side, keep the middle."""
    w, h = img.size
    strip = Image.new(img.mode, (w * 3, h))
    for i in range(3):
        strip.paste(img, (i * w, 0))
    return strip.filter(ImageFilter.GaussianBlur(radius)).crop((w, 0, w * 2, h))


# 1. Base with mottled ageing. The coarse layer needs enough rows and a soft blur,
#    otherwise the upscaled grid shows up as straight-edged rectangles on the tape.
tape = Image.new("RGB", (W, H), BASE)
mottle = mix([(wrap_noise(W, H, 12, 6), .45), (wrap_noise(W, H, 40, 12), .33), (wrap_noise(W, H, 160, 24), .22)])
mottle = wrap_blur(mottle, 9)
dark = Image.new("RGB", (W, H), (138, 104, 62))
tape = Image.composite(dark, tape, mottle.point(lambda v: int(max(0, v - 110) * 0.5)))

# 2. Water stains and burn marks (drawn three times across the seam so they wrap)
stains = Image.new("L", (W, H), 0)
d = ImageDraw.Draw(stains)
for _ in range(34):
    x, y = random.uniform(0, W), random.choice([random.uniform(-10, 28), random.uniform(H - 28, H + 10), random.uniform(0, H)])
    rx, ry = random.uniform(8, 60), random.uniform(4, 22)
    shade = random.randint(40, 120)
    for dx in (-W, 0, W):
        d.ellipse((x + dx - rx, y - ry, x + dx + rx, y + ry), fill=shade)
stains = wrap_blur(stains, 7)
burn = Image.new("RGB", (W, H), (92, 48, 22))
tape = Image.composite(burn, tape, stains)

# 3. Speckles and fine grain
spk = Image.new("L", (W, H), 0)
d = ImageDraw.Draw(spk)
for _ in range(900):
    x, y, r = random.uniform(0, W), random.uniform(0, H), random.uniform(0.4, 1.6)
    d.ellipse((x - r, y - r, x + r, y + r), fill=random.randint(60, 200))
tape = Image.composite(Image.new("RGB", (W, H), (70, 40, 20)), tape, spk.filter(ImageFilter.GaussianBlur(0.4)))
grain = wrap_noise(W, H, W // 2, H // 2).point(lambda v: int(v * 0.12))
tape = Image.composite(Image.new("RGB", (W, H), (60, 40, 20)), tape, grain)

# 4. Printed rules above and below the text
d = ImageDraw.Draw(tape)
for y in (int(H * 0.2), int(H * 0.8)):
    d.line((0, y, W, y), fill=(42, 30, 18), width=2)

# 5. Torn, burnt edges -> alpha, with a scorched rim just inside the tear
top = periodic_edge(W, 14)
bottom = periodic_edge(W, 14)
alpha = Image.new("L", (W, H), 0)
rim = Image.new("L", (W, H), 0)
da, dr = ImageDraw.Draw(alpha), ImageDraw.Draw(rim)
for x in range(W):
    t, b = top[x] + 2, H - bottom[x] - 2
    da.line((x, t, x, b), fill=255)
    dr.line((x, t, x, t + 5), fill=200)
    dr.line((x, b - 5, x, b), fill=200)
rim = wrap_blur(rim, 2.2)
tape = Image.composite(Image.new("RGB", (W, H), (58, 30, 14)), tape, rim)
alpha = wrap_blur(alpha, 0.6)

tape = tape.convert("RGBA")
tape.putalpha(alpha)
tape.save(OUT, "WEBP", quality=78, method=6)
print(OUT, tape.size, os.path.getsize(OUT) // 1024, "KB")
