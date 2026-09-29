"""Generate assets/img/torn-mask.svg: an irregular, ripped-through opening with ink-splatter
edges, used as a CSS mask on photos (.torn-photo). Run from the project root:
    python _source/build_torn_mask.py            (standard library only)
Change SEED for a different tear."""
import math, random

SEED = 1923
W, H = 1000, 833                     # matches the 6:5 photo box; the mask is stretched to fit
OUT = "assets/img/torn-mask.svg"
random.seed(SEED)


def periodic_noise(n, octaves):
    """1-D noise around a closed loop: sum of integer-frequency sines with random phases."""
    comps = [(random.randint(lo, hi), random.uniform(0, 2 * math.pi), amp) for lo, hi, amp in octaves for _ in range(3)]
    return [sum(a * math.sin(2 * math.pi * f * i / n + p) for f, p, a in comps) for i in range(n)]


# 1. Walk the perimeter of an inset rectangle and push each point in or out.
#    Per-side insets let the tear frame the photo: for the current poster the top edge stays
#    above the "Is seeing really believing?" line and the bottom tear runs above the credit line.
TOP, RIGHT, BOTTOM, LEFT = 14, 60, 150, 60
TOP_CALM = 0.45                      # softer lobes and no inward shards along the top edge
rect = [(LEFT, TOP), (W - RIGHT, TOP), (W - RIGHT, H - BOTTOM), (LEFT, H - BOTTOM)]
perim = []
for (x1, y1), (x2, y2) in zip(rect, rect[1:] + rect[:1]):
    steps = int(math.hypot(x2 - x1, y2 - y1) / 5)
    for k in range(steps):
        t = k / steps
        perim.append((x1 + (x2 - x1) * t, y1 + (y2 - y1) * t))
n = len(perim)
cx, cy = W / 2, H / 2
lobes = periodic_noise(n, [(2, 4, 18), (5, 9, 9)])          # big bites and bulges
grain = periodic_noise(n, [(30, 60, 2.2)])                   # small wobble
pts = []
spike_left = 0
for i, (x, y) in enumerate(perim):
    # outward normal of the rectangle side this point sits on
    nx = -1 if x <= LEFT + 0.1 else 1 if x >= W - RIGHT - 0.1 else 0
    ny = -1 if y <= TOP + 0.1 else 1 if y >= H - BOTTOM - 0.1 else 0
    top_edge = ny == -1 and not nx
    if nx and ny:
        nx, ny = nx * 0.7071, ny * 0.7071
    off = (lobes[i] * (TOP_CALM if top_edge else 1)) + grain[i] + random.uniform(-4, 4)   # ragged fibre edge
    if top_edge:
        off = max(off, -6)                                   # never bite down into the top line of the photo
    if spike_left:
        spike_left -= 1
    elif random.random() < 0.035:                            # occasional torn shard or deep notch
        spike_left = random.randint(2, 4)
        off += (1 if top_edge else random.choice([1, 1, -1])) * random.uniform(18, 46)
    pts.append((x + nx * off, y + ny * off))
outline = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + " Z"


def blob(x, y, r):
    """Small irregular splatter droplet as a closed path."""
    k = random.randint(6, 9)
    ang0 = random.uniform(0, math.tau)
    p = []
    for j in range(k):
        a = ang0 + j * math.tau / k
        rr = r * random.uniform(0.65, 1.25)
        p.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    return "M" + " L".join(f"{a:.1f} {b:.1f}" for a, b in p) + " Z"


# 2. Splatter: fragments outside the tear (image shows) and specks inside (image punched out).
#    Everything lives in one even-odd path, so inside specks become holes automatically.
subpaths = []
for _ in range(90):
    i = random.randrange(n)
    x, y = pts[i]
    px, py = perim[i]
    dx, dy = x - cx, y - cy
    d = math.hypot(dx, dy) or 1
    outward = random.random() < 0.55
    dist = random.uniform(8, 60) if outward else -random.uniform(10, 90)
    r = random.uniform(1.5, 7) if abs(dist) > 25 else random.uniform(1.2, 4)
    bx, by = x + dx / d * dist, y + dy / d * dist
    if 4 < bx < W - 4 and 4 < by < H - 4:
        subpaths.append(blob(bx, by, r))

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="none">'
       f'<path fill="#000" fill-rule="evenodd" d="{outline} {" ".join(subpaths)}"/></svg>')
open(OUT, "w", encoding="utf-8").write(svg)
print(OUT, len(svg) // 1024, "KB,", n, "edge points,", len(subpaths), "splatter drops")
