"""Generate the hand-torn edges for the venue strip ("Held in secret at 1923 Prohibition Bar")
and write them inline into index.html as two SVG <clipPath>s (no external asset):
  #venue-tear        the paper itself
  #venue-tear-fiber  a slightly larger outline: the pale ripped-fibre rim behind the paper
Units are objectBoundingBox (0..1 of the section), so the tear scales with the section.
Run from the project root:  python _source/build_venue_tear.py    (standard library only)
Change SEED for a different tear."""
import math, random, re

SEED = 7
N = 260                                   # points per edge
random.seed(SEED)


def smooth_noise(n, waves):
    """Sum of random sine waves (freq range, amplitude) sampled at n points: no repetition."""
    comps = [(random.uniform(lo, hi), random.uniform(0, math.tau), amp) for lo, hi, amp in waves for _ in range(3)]
    return [sum(a * math.sin(f * math.tau * i / n + p) for f, p, a in comps) / 3 for i in range(n)]


def edge(start, end, depth):
    """y(x) for one edge: a diagonal, plus big tears, plus fibre roughness that comes and goes.
    `depth` is +1 for the top edge (tears go down into the paper) and -1 for the bottom."""
    lobes = smooth_noise(N, [(0.6, 1.6, 0.030), (2, 5, 0.014)])      # large natural sections
    mid = smooth_noise(N, [(8, 18, 0.006)])                           # smaller tears
    envelope = smooth_noise(N, [(1, 3, 1.0)])                         # where the edge is rough vs almost straight
    xs, ys = [], []
    for i in range(N):
        t = i / (N - 1)
        x = t if i in (0, N - 1) else t + random.uniform(-0.0012, 0.0012)
        rough = max(0.0, 0.35 + envelope[i])                          # 0 = nearly straight stretch
        fibre = random.uniform(-1, 1) * 0.0045 * rough
        if random.random() < 0.05 * rough:                            # occasional deeper nick
            fibre += depth * random.uniform(0.006, 0.02)
        y = start + (end - start) * t + lobes[i] + mid[i] * rough + fibre
        xs.append(x); ys.append(y)
    return xs, ys


# Paper tapers toward the right, like the reference: top drops, bottom rises
tx, ty = edge(0.012, 0.115, +1)
bx, by = edge(0.985, 0.895, -1)
ty = [max(0.0, y) for y in ty]
by = [min(1.0, y) for y in by]

# Fibre rim: pale paper core exposed along the rip. Irregular width, missing in places.
rim_env = smooth_noise(N, [(2, 6, 1.0)])
def rim(i):
    w = max(0.0015, 0.007 + 0.008 * rim_env[i]) + random.uniform(0, 0.005)
    if random.random() < 0.08:
        w += random.uniform(0.004, 0.012)                             # stray fibre sticking out
    return w


def fmt(v):
    return f"{v:.4f}".rstrip("0").rstrip(".") or "0"


def path(top, bottom):
    pts = [f"{fmt(x)} {fmt(y)}" for x, y in zip(tx, top)]
    pts += [f"{fmt(x)} {fmt(y)}" for x, y in reversed(list(zip(bx, bottom)))]
    return "M" + " L".join(pts) + " Z"


paper = path(ty, by)
fiber = path([max(0.0, y - rim(i)) for i, y in enumerate(ty)], [min(1.0, y + rim(i)) for i, y in enumerate(by)])

svg = ('<svg class="venue__clips" width="0" height="0" aria-hidden="true" focusable="false"><defs>'
       f'<clipPath id="venue-tear" clipPathUnits="objectBoundingBox"><path d="{paper}"/></clipPath>'
       f'<clipPath id="venue-tear-fiber" clipPathUnits="objectBoundingBox"><path d="{fiber}"/></clipPath>'
       '</defs></svg>')

p = "index.html"
h = open(p, encoding="utf-8").read()
h, n = re.subn(r'<svg class="venue__clips".*?</svg>', lambda m: svg, h, count=1, flags=re.S)
if not n:
    raise SystemExit("venue__clips placeholder not found in index.html")
open(p, "w", encoding="utf-8").write(h)
print("wrote torn edges into index.html:", len(svg) // 1024, "KB inline")
