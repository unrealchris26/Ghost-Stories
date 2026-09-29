"""Rebuild optimized images in assets/img from the source photos in _source/photos.
Run from the project root:  python _source/build_assets.py   (needs Pillow only)"""
from PIL import Image, ImageFilter, ImageOps, ImageChops
import os, random
SRC = "_source/photos"; OUT = "assets/img"; BG = (11, 19, 21)
os.makedirs(OUT, exist_ok=True)
random.seed(1923)

def load(name, flatten=False):
    im = Image.open(os.path.join(SRC, name)).convert("RGBA")
    if flatten:
        base = Image.new("RGBA", im.size, BG + (255,)); base.alpha_composite(im); im = base
    return im

def save(im, name, width=None, q=78, crop=None, keep_alpha=False):
    if crop: im = ImageOps.fit(im, crop, Image.LANCZOS, centering=(0.5, 0.4))
    if width and im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    if not keep_alpha: im = im.convert("RGB")
    im.save(os.path.join(OUT, name), "WEBP", quality=q, method=6)
    print(f"{name:52s} {im.size[0]}x{im.size[1]}  {os.path.getsize(os.path.join(OUT,name))//1024}KB")

# Hero background (full size + a 1280 version for small screens)
save(load("Ghost Stories Web Background 3.webp"), "hero-ghost-stories-bg.webp", 1920, 72)
save(load("Ghost Stories Web Background 3.webp"), "hero-ghost-stories-bg-1280.webp", 1280, 70)
# Trailer + video thumbnails
save(load("kent-landscape.jpg"), "trailer-poster-kent-speakeasy.webp", 1280, 74, crop=(1600, 900))
save(load("show-01-clean.jpg"), "video-thumb-the-seance.webp", 720, 74, crop=(1080, 720))
save(load("show-11-clean.jpg"), "video-thumb-guest-reactions.webp", 720, 74, crop=(1080, 720))
save(load("show-07-clean.jpg"), "video-thumb-behind-the-veil.webp", 720, 74, crop=(1080, 720))
# Encounters (zig-zag)
save(load("poster-square.jpg"), "encounter-nightly-show-poster.webp", 1000, 76, crop=(1200, 1000))
save(load("illuminati.jpg"), "encounter-private-seance-candles.webp", 1000, 76, crop=(1200, 1000))
save(load("kent-landscape.jpg"), "encounter-corporate-speakeasy-bar.webp", 1000, 76, crop=(1200, 1000))
save(load("red-curtain.png", flatten=True), "encounter-special-occasion-curtain.webp", 1000, 76, crop=(1200, 1000))
# Medium portrait (transparent cut-out)
save(load("kent-portrait.png"), "medium-kent-axell-portrait.webp", 820, 80, keep_alpha=True)
# Logos
save(load("1923-logo.png"), "logo-1923-prohibition-bar.webp", 520, 85, keep_alpha=True)
# About Ghost Stories stage: chair backdrop. (The velvet curtain panel, about-curtain-panel.webp,
# is a committed asset and is not rebuilt here.)
save(load("Seat Image.jpg"), "about-stage-chair.webp", 1600, 72)
# Contact section backdrop
save(load("candle-hand.jpg"), "gallery-candle-in-the-dark.webp", 900, 72)
# Gallery: square snapshots from _source/photos/gallery ("GS Snapshot N.jpg").
# Each gets a full-size file (lightbox) and a 640px preview (grid). Never cropped.
import glob
for f in glob.glob(os.path.join(SRC, "gallery", "GS Snapshot *.jpg")):
    n = int(os.path.splitext(f)[0].split()[-1])
    im = Image.open(f).convert("RGB")
    save(im, f"gallery-gs-{n:02d}.webp", 1080, 80)
    save(im, f"gallery-gs-{n:02d}-640.webp", 640, 74)
# Social share image
# Social share image: rendered from assets/og/og-template.html (see README, SEO section)

# ---- Generated textures (Pillow only) ----------------------------------
def octave(w, h, cx, cy):
    """Value noise that wraps horizontally: tile the tiny grid 3x, upscale, keep the middle third."""
    small = Image.new("L", (cx, cy)); small.putdata([random.randrange(256) for _ in range(cx * cy)])
    tiled = Image.new("L", (cx * 3, cy)); [tiled.paste(small, (i * cx, 0)) for i in range(3)]
    return tiled.resize((w * 3, h), Image.BICUBIC).crop((w, 0, w * 2, h))

def mix(layers):
    acc = layers[0][0].point(lambda v, a=layers[0][1]: v * a)
    for img, a in layers[1:]:
        acc = ImageChops.add(acc, img.point(lambda v, a=a: v * a))
    return ImageOps.autocontrast(acc)

W, H = 1200, 525
fog = mix([(octave(W, H, 5, 3), .55), (octave(W, H, 11, 6), .28), (octave(W, H, 23, 11), .17)])
fog = fog.point(lambda v: int(max(0, min(1, (v / 255 - .38) * 1.9)) ** 1.6 * 150))
band = Image.linear_gradient("L").resize((1, H))                     # soft top and bottom
band = band.point(lambda v: int(255 * (1 - abs(v / 127.5 - 1)) ** .8)).resize((W, H))
alpha = ImageChops.multiply(fog, band).filter(ImageFilter.GaussianBlur(6))
fog_rgba = Image.new("RGBA", (W, H), (214, 222, 218, 0)); fog_rgba.putalpha(alpha)
fog_rgba.save(os.path.join(OUT, "fog-layer.webp"), "WEBP", quality=45)
print("fog-layer.webp", os.path.getsize(os.path.join(OUT, "fog-layer.webp")) // 1024, "KB")

P = 480
paper = mix([(octave(P, P, 6, 6), .5), (octave(P, P, 24, 24), .3), (octave(P, P, 96, 96), .2)])
light = Image.new("RGB", (P, P), (236, 227, 206)); dark = Image.new("RGB", (P, P), (200, 181, 146))
tex = Image.composite(dark, light, paper.point(lambda v: int(v * .6)))
# mirror into a 2x2 tile so it repeats seamlessly in both directions
big = Image.new("RGB", (P * 2, P * 2))
big.paste(tex, (0, 0)); big.paste(ImageOps.mirror(tex), (P, 0))
big.paste(ImageOps.flip(tex), (0, P)); big.paste(ImageOps.flip(ImageOps.mirror(tex)), (P, P))
big.save(os.path.join(OUT, "parchment-texture.webp"), "WEBP", quality=70); print("parchment-texture.webp")
