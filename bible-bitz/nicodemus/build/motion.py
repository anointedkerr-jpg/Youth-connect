"""2.5D motion test: real photo backgrounds, cut-out characters as separate layers,
parallax camera, light flicker, drifting dust. Renders short MP4 clips."""
import os, sys, math, random, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw
from engine import ROOT, A, W, H, grain, font

FPS = 16
OUT = os.path.join(ROOT, 'motion_tests'); os.makedirs(OUT, exist_ok=True)
BOWL = lambda s: font('BowlbyOne.ttf', s)


def load(p):
    return Image.open(A(*p.split('/')))


def ease(t):
    return t * t * (3 - 2 * t)


# ---------- photo grading ----------
def night_grade(im, warm_spot=None, strength=1.0):
    """Day-for-night on an old B&W photo: deep blue shadows, optional warm lamp pool."""
    g = np.asarray(im.convert('L'), dtype=np.float32) / 255
    g = np.clip((g - 0.08) * 1.15, 0, 1) ** 1.35
    blue = np.stack([g * 70 + 6, g * 105 + 10, g * 165 + 22], -1)
    if warm_spot:
        h, w = g.shape
        yy, xx = np.mgrid[0:h, 0:w]
        cx, cy, r = warm_spot
        m = np.exp(-(((xx - cx * w) ** 2 + (yy - cy * h) ** 2) / (2 * (r * w) ** 2)))[..., None]
        warm = np.stack([g * 255, g * 175 + 10, g * 95 + 5], -1) * 1.15
        blue = blue * (1 - m * strength) + warm * m * strength
    return Image.fromarray(np.clip(blue, 0, 255).astype(np.uint8))


def warm_grade(im):
    """Warm sepia-colour grade for daylight scenes from B&W photos."""
    g = np.asarray(im.convert('L'), dtype=np.float32) / 255
    rgb = np.stack([g * 245 + 8, g * 205 + 6, g * 150 + 4], -1)
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))


def char_to_light(layer, tint=(1.0, 1.0, 1.0), bright=1.0):
    rgb = np.asarray(layer.convert('RGBA'), dtype=np.float32)
    rgb[..., :3] *= np.array(tint) * bright
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))


def relight(layer, light=(0.25, 0.35), ambient=(0.42, 0.5, 0.75), warm=(1.15, 0.9, 0.62), reach=0.9):
    """Night lighting on a cutout: blue ambient everywhere, warm light falling off from a point."""
    a = np.asarray(layer.convert('RGBA'), dtype=np.float32)
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt(((xx / w - light[0]) * w / h) ** 2 + (yy / h - light[1]) ** 2)
    m = np.clip(1 - d / reach, 0, 1)[..., None] ** 1.4
    mult = np.array(ambient) * (1 - m) + np.array(warm) * m
    a[..., :3] *= mult
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def rim_shadow(layer, blur=26, op=0.6):
    a = layer.getchannel('A').filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * op))
    s = Image.new('RGBA', layer.size, (0, 0, 0, 255)); s.putalpha(a)
    return s


# ---------- layer composition ----------
class Layer:
    """An image placed in a virtual 3D space. depth 0 = background, 1 = camera plane.
    Nearer layers move and scale more when the camera moves: that is the parallax."""

    def __init__(self, img, x, y, h=None, depth=0.5, anim=None, blur=0, shadow=False):
        self.img = img
        if h:
            s = h / img.height
            self.img = img.resize((int(img.width * s), int(h)), Image.LANCZOS)
        if blur:
            self.img = self.img.filter(ImageFilter.GaussianBlur(blur))
        self.x, self.y, self.depth, self.anim, self.shadow = x, y, depth, anim, shadow
        self.sh = rim_shadow(self.img) if shadow else None


def render_frame(layers, cam, t, seed):
    """cam: dict with zoom, panx, pany (in screen px at depth 1)."""
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    rnd = random.Random(seed)
    for L in layers:
        dx, dy, rot, sc, alpha = 0, 0, 0, 1, 1
        if L.anim:
            r = L.anim(t)
            dx, dy = r.get('dx', 0), r.get('dy', 0)
            rot, sc, alpha = r.get('rot', 0), r.get('scale', 1), r.get('alpha', 1)
        # parallax: layers nearer the camera get more zoom and more pan
        z = 1 + (cam['zoom'] - 1) * (0.35 + 0.65 * L.depth)
        px = cam['panx'] * (0.25 + 0.75 * L.depth)
        py = cam['pany'] * (0.25 + 0.75 * L.depth)
        # house jitter: tiny per-frame wobble for the handmade feel (not on the background)
        if L.depth > 0.05:
            dx += rnd.uniform(-1.5, 1.5); dy += rnd.uniform(-1.5, 1.5); rot += rnd.uniform(-0.25, 0.25)
        img = L.img
        s = z * sc
        if abs(s - 1) > 1e-3:
            img = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.BILINEAR)
        if rot:
            img = img.rotate(rot, resample=Image.BICUBIC, expand=True)
        if alpha < 1:
            a = img.getchannel('A').point(lambda v: int(v * alpha)); img = img.copy(); img.putalpha(a)
        cx = W / 2 + (L.x - W / 2) * z + px + dx
        cy = H / 2 + (L.y - H / 2) * z + py + dy
        if L.sh is not None:
            sh = L.sh.resize(img.size, Image.BILINEAR) if L.sh.size != img.size else L.sh
            _paste(canvas, sh, int(cx - img.width / 2 + 14 * z), int(cy - img.height / 2 + 18 * z))
        _paste(canvas, img, int(cx - img.width / 2), int(cy - img.height / 2))
    return canvas


def _paste(canvas, img, x, y):
    if x >= W or y >= H or x + img.width <= 0 or y + img.height <= 0:
        return
    canvas.alpha_composite(img.convert('RGBA'), (max(0, x), max(0, y)),
                           (max(0, -x), max(0, -y), min(img.width, W - x), min(img.height, H - y)))


def dust_layer(n=70, seed=3, warm=True):
    rng = np.random.default_rng(seed)
    pts = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(1.5, 4.5), rng.uniform(-14, 14), rng.uniform(-30, -6),
            rng.uniform(0, 6.28)) for _ in range(n)]

    def draw(t):
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        for x, y, r, vx, vy, ph in pts:
            xx = (x + vx * t + 10 * math.sin(t * 0.9 + ph)) % W
            yy = (y + vy * t) % H
            a = int(110 + 90 * math.sin(t * 2 + ph))
            col = (255, 214, 150, a) if warm else (200, 220, 255, a)
            d.ellipse((xx - r, yy - r, xx + r, yy + r), fill=col)
        return im.filter(ImageFilter.GaussianBlur(1.6))
    return draw


def light_pool(cx, cy, r, color=(255, 170, 80)):
    yy, xx = np.mgrid[0:H, 0:W]
    m = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r)))
    return m.astype(np.float32), np.array(color, np.float32)


def add_light(frame, pool, k):
    m, col = pool
    a = np.asarray(frame.convert('RGB'), dtype=np.float32)
    a = a + (m[..., None] * col[None, None, :] * k * 0.55) + a * m[..., None] * k * 0.35
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert('RGBA')


def vignette(frame, amt=0.65):
    a = np.asarray(frame.convert('RGB'), dtype=np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    a *= (1 - amt * np.clip(d - 0.4, 0, 1) ** 1.5)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert('RGBA')


def glow_word(txt, size, fill=(246, 240, 228)):
    f = BOWL(size); l, t, r, b = f.getbbox(txt); pad = 50
    im = Image.new('RGBA', (r - l + 2 * pad, b - t + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im); d.text((pad - l + 5, pad - t + 8), txt, font=f, fill=(0, 0, 0, 180))
    im = im.filter(ImageFilter.GaussianBlur(6))
    g = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(g).text((pad - l, pad - t), txt, font=f, fill=fill + (120,))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(16)))
    ImageDraw.Draw(im).text((pad - l, pad - t), txt, font=f, fill=fill)
    return im


def write_video(frames_fn, n, name):
    path = os.path.join(OUT, name)
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                          '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '23',
                          '-preset', 'medium', '-movflags', '+faststart', path], stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(np.asarray(frames_fn(i).convert('RGB')).tobytes())
    p.stdin.close(); p.wait()
    return path


# ---------- scene: cat scare in the arched street ----------
def scene_cat(secs=5.0):
    bg = load('bg/arched_street_b.jpg')
    bg = bg.crop((60, 40, bg.width - 60, bg.height - 120))
    bg = night_grade(bg, warm_spot=(0.62, 0.42, 0.22), strength=0.55)
    bg = ImageEnhance.Brightness(bg).enhance(0.8)
    s = (H * 1.12) / bg.height
    bg = bg.resize((int(bg.width * s), int(bg.height * s)), Image.LANCZOS).filter(ImageFilter.GaussianBlur(3.2))
    jump = load('kittl_cut2/s03_cat_scare.png')
    cat = load('kittl_cut2/cat.png')
    walk = load('kittl_cut2/s01_rooftop_lantern.png')
    walk = relight(walk, light=(0.72, 0.62))      # lantern in his right hand
    jump = relight(jump, light=(0.12, 0.42))      # lantern raised on the left
    cat = relight(cat, light=(0.0, 0.3), ambient=(0.55, 0.6, 0.8), warm=(1.1, 0.95, 0.8), reach=1.4)
    T = secs; SCARE = 2.2
    FLOOR = 1600

    def walk_anim(t):
        if t >= SCARE: return {'alpha': 0}
        k = ease(min(1, t / SCARE))
        return {'dx': -330 * (1 - k), 'dy': 8 * abs(math.sin(t * 6.5))}

    def jump_anim(t):
        if t < SCARE: return {'alpha': 0}
        u = t - SCARE
        up = -170 * math.sin(min(math.pi, u / 0.85 * math.pi))
        return {'dy': up, 'rot': 4 * math.sin(u * 20) * max(0, 1 - u / 1.0)}

    def cat_anim(t):
        if t < SCARE - 0.15: return {'alpha': 0, 'dx': 180}
        k = ease(min(1, (t - SCARE + 0.15) / 0.3))
        return {'dx': 180 * (1 - k), 'alpha': k}

    hw = 900
    layers = [
        Layer(bg.convert('RGBA'), W / 2, H / 2, depth=0.0),
        Layer(walk, 470, FLOOR - hw / 2, h=hw, depth=0.6, anim=walk_anim, shadow=True),
        Layer(jump, 450, FLOOR - 860 / 2, h=860, depth=0.6, anim=jump_anim, shadow=True),
        Layer(cat, 840, FLOOR - 120, h=250, depth=0.75, anim=cat_anim, shadow=True),
    ]
    dust = dust_layer(60, 5)
    word = glow_word('MEOW.', 150)

    def lantern_pos(t):
        if t < SCARE:
            k = ease(min(1, t / SCARE)); return (470 - 330 * (1 - k) + 140, FLOOR - 330)
        u = t - SCARE
        return (450 - 330, FLOOR - 620 - 170 * math.sin(min(math.pi, u / 0.85 * math.pi)))

    def frame(i):
        t = i / FPS
        k = ease(t / T)
        cam = {'zoom': 1.0 + 0.08 * k, 'panx': -30 * k, 'pany': -10 * k}
        if SCARE <= t < SCARE + 0.3:
            cam['panx'] += random.Random(i).uniform(-16, 16); cam['pany'] += random.Random(i + 9).uniform(-16, 16)
        f = render_frame(layers, cam, t, i)
        lx, ly = lantern_pos(t)
        f = add_light(f, light_pool(lx, ly, 280), 0.5 + 0.12 * math.sin(t * 13) + 0.06 * math.sin(t * 31))
        f.alpha_composite(dust(t))
        if t >= SCARE - 0.1:
            a = min(1, (t - SCARE + 0.1) / 0.12)
            w = word.copy(); w.putalpha(w.getchannel('A').point(lambda v: int(v * a)))
            sc = 1.3 - 0.3 * min(1, (t - SCARE + 0.1) / 0.2)
            w = w.resize((int(w.width * sc), int(w.height * sc)), Image.BILINEAR)
            f.alpha_composite(w, (int(W * 0.66 - w.width / 2), int(470 - w.height / 2)))
        f = vignette(f, 0.75)
        return grain(f, 8, i)
    return write_video(frame, int(T * FPS), 'test_cat_scare.mp4')


# ---------- scene: rooftops at night ----------
def city_strip():
    """Real view over Jerusalem from the Mount of Olives, graded to night, sky keyed out."""
    im = load('bg/jerusalem_from_olives.jpg').convert('L').crop((150, 440, 1790, 1340))
    g = np.asarray(im, dtype=np.float32)
    h, w = g.shape
    yy = np.mgrid[0:h, 0:w][0]
    sky = (g > 175) & (yy < 140)                           # bright sky above the skyline
    sky = cv2.morphologyEx(sky.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    m = (1 - sky).astype(np.float32)
    m = cv2.GaussianBlur(m, (0, 0), 3)
    out = np.asarray(night_grade(im), dtype=np.float32)
    fall = np.clip(1.0 - (yy - 200) / (h - 200), 0.28, 1.0) ** 1.2   # ground fades into darkness
    out = Image.fromarray(np.clip(out * 0.75 * fall[..., None], 0, 255).astype(np.uint8)).convert('RGBA')
    out.putalpha(Image.fromarray((m * 255).astype(np.uint8)))
    d = ImageDraw.Draw(out); rng = random.Random(4)
    for _ in range(140):                                    # lamp-lit windows in the city band
        x, y = rng.uniform(250, w - 60), rng.uniform(70, 210)
        r = rng.uniform(1.5, 3)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 196, 120, 210))
    return out


def roof_ledge():
    """Near rooftop parapet in silhouette: real stone, almost black, with a ragged top."""
    im = load('bg/arched_street_a.jpg').convert('L').crop((60, 900, 760, 1300))
    g = night_grade(im); g = ImageEnhance.Brightness(g).enhance(0.38)
    g = g.resize((W + 400, int((W + 400) * g.height / g.width)), Image.LANCZOS).convert('RGBA')
    w, h = g.size
    m = Image.new('L', (w, h), 0); d = ImageDraw.Draw(m); rng = random.Random(2)
    pts = [(0, h)]; x = 0
    while x < w:
        pts.append((x, rng.uniform(0, 26))); x += rng.uniform(60, 160)
    pts += [(w, 10), (w, h)]
    d.polygon(pts, fill=255)
    g.putalpha(m.filter(ImageFilter.GaussianBlur(2)))
    return g


def scene_rooftop(secs=5.0):
    sky = load('bg/stars.jpg'); sky = sky.crop((0, 0, sky.width, int(sky.height * 0.5)))
    s = (W * 1.3) / sky.width
    sky = sky.resize((int(sky.width * s), int(sky.height * s)), Image.LANCZOS)
    sky = ImageEnhance.Brightness(ImageEnhance.Color(sky).enhance(0.7)).enhance(0.85).convert('RGBA')
    city = city_strip(); s = (W * 1.45) / city.width
    city = city.resize((int(city.width * s), int(city.height * s)), Image.LANCZOS).filter(ImageFilter.GaussianBlur(2.0))
    ledge = roof_ledge().filter(ImageFilter.GaussianBlur(4))
    man = relight(load('kittl_cut2/s01_rooftop_lantern.png'), light=(0.72, 0.62))
    T = secs; FLOOR = 1640; hm = 1050

    def man_anim(t):
        k = ease(min(1, t / T))
        return {'dx': -240 + 260 * k, 'dy': 8 * abs(math.sin(t * 5.5))}

    layers = [Layer(sky, W / 2, 560, depth=0.0, anim=lambda t: {'dx': -10 * t}),
              Layer(city, W / 2, 820 + city.height / 2, depth=0.2),
              Layer(man, 560, FLOOR - hm / 2, h=hm, depth=0.6, anim=man_anim, shadow=True),
              Layer(ledge, W / 2, FLOOR - 40 + ledge.height / 2, depth=0.95)]
    dust = dust_layer(35, 8, warm=False)
    word = glow_word('AT NIGHT.', 130)

    def frame(i):
        t = i / FPS
        k = ease(t / T)
        f = render_frame(layers, {'zoom': 1.0 + 0.08 * k, 'panx': 40 * k, 'pany': -15 * k}, t, i)
        mx = 560 - 240 + 260 * k
        f = add_light(f, light_pool(mx + 150, FLOOR - 330, 260), 0.55 + 0.12 * math.sin(t * 11) + 0.05 * math.sin(t * 29))
        f.alpha_composite(dust(t))
        if t > 1.2:
            a = min(1, (t - 1.2) / 0.15); w = word.copy(); w.putalpha(w.getchannel('A').point(lambda v: int(v * a)))
            f.alpha_composite(w, (int(W / 2 - w.width / 2), 330))
        return grain(vignette(f, 0.7), 8, i)
    return write_video(frame, int(T * FPS), 'test_rooftop.mp4')


# ---------- scene: awake in bed ----------
def scene_bed(secs=5.0, bgname='caiaphas_niche'):
    bg = load(f'bg/{bgname}.jpg').convert('L') if bgname != 'caiaphas_niche' else None
    if bgname == 'veronica_interior':
        # left frame of the stereo pair, stone vault only (no chapel figures), floor extended in darkness
        vault = bg.crop((60, 70, 860, 630))
        bg = Image.new('L', (800, 1000), 18)
        bg.paste(vault, (0, 0))
        g = np.asarray(bg, dtype=np.float32); yy = np.arange(1000)[:, None]
        fade = np.clip((yy - 430) / 170, 0, 1)
        g = g * (1 - fade) + 22 * fade
        bg = Image.fromarray(g.astype(np.uint8))
    elif bgname == 'caiaphas_niche':
        bg = load('bg/caiaphas_court.jpg').convert('L').crop((70, 420, 560, 1250))   # arched alcove, stone floor
    else:
        bg = bg.crop((40, 40, bg.width - 40, bg.height - 40))
    bg = night_grade(bg, warm_spot=(0.25, 0.75, 0.35), strength=0.45)
    bg = ImageEnhance.Brightness(bg).enhance(0.95)
    s = max((H * 1.1) / bg.height, (W * 1.1) / bg.width)
    bg = bg.resize((int(bg.width * s), int(bg.height * s)), Image.LANCZOS).filter(ImageFilter.GaussianBlur(2.2))
    bed = relight(load('kittl_cut2/s02_awake_in_bed.png'), light=(0.08, 0.32), reach=1.1,
                  ambient=(0.5, 0.56, 0.78), warm=(1.12, 0.92, 0.68))
    T = secs; FLOOR = 1700; bw = 1100
    bh = bw * bed.height / bed.width
    lamp = (W / 2 - bw / 2 + bw * 0.06, FLOOR - bh + bh * 0.33)
    marks = [glow_word('?', 170 + 30 * i, (246, 222, 150)) for i in range(3)]

    def bed_anim(t):
        return {'dy': 2 * math.sin(t * 1.3)}          # slow breathing

    layers = [Layer(bg.convert('RGBA'), W / 2, H / 2, depth=0.0),
              Layer(bed, W / 2, FLOOR - bh / 2, h=bh, depth=0.55, anim=bed_anim, shadow=True)]
    dust = dust_layer(45, 11)
    head = (W / 2 - bw / 2 + bw * 0.38, FLOOR - bh + bh * 0.12)

    def frame(i):
        t = i / FPS
        k = ease(t / T)
        f = render_frame(layers, {'zoom': 1.0 + 0.1 * k, 'panx': 30 * k, 'pany': 25 * k}, t, i)
        # moonlight shaft from the upper right, and the oil-lamp flicker on the left
        f = add_light(f, light_pool(W * 0.85, H * 0.2, 420, (120, 150, 230)), 0.35)
        f = add_light(f, light_pool(lamp[0], lamp[1], 300), 0.5 + 0.14 * math.sin(t * 12) + 0.07 * math.sin(t * 27))
        for j, m in enumerate(marks):                   # question marks rise one after another
            u = t - 0.8 - j * 1.0
            if u <= 0: continue
            a = min(1, u / 0.3) * max(0, 1 - max(0, u - 2.2) / 0.6)
            if a <= 0: continue
            mm = m.copy(); mm.putalpha(mm.getchannel('A').point(lambda v: int(v * a)))
            mm = mm.rotate(8 * math.sin(u * 2 + j), resample=Image.BICUBIC, expand=True)
            x = head[0] + (j - 1) * 170 + 20 * math.sin(u * 1.7 + j)
            y = head[1] - 230 - u * 130
            f.alpha_composite(mm, (int(x - mm.width / 2), int(y - mm.height / 2)))
        f.alpha_composite(dust(t))
        return grain(vignette(f, 0.75), 8, i)
    return write_video(frame, int(T * FPS), 'test_awake_in_bed.mp4')


# ---------- scene: burial at the Garden Tomb ----------
def sunset_grade(im):
    a = np.asarray(im.convert('RGB'), dtype=np.float32)
    a = a * np.array([1.08, 0.9, 0.68]) * 0.78
    lum = a.mean(-1, keepdims=True)
    a = lum + (a - lum) * 0.7
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def scene_burial(secs=5.0):
    bg = load('bg/garden_tomb_color.jpg').crop((620, 0, 1920, 1100))   # rock face and tomb door, no railings
    bg = sunset_grade(bg)
    s = (H * 1.1) / bg.height
    bg = bg.resize((int(bg.width * s), int(bg.height * s)), Image.LANCZOS).filter(ImageFilter.GaussianBlur(3.5))
    men = relight(load('kittl_cut2/s06_burial_two_men.png'), light=(-0.2, 0.3), reach=1.6,
                  ambient=(0.7, 0.66, 0.66), warm=(1.12, 0.98, 0.82))
    jar = lambda n, h: relight(load(f'cut/{n}.png'), light=(-0.3, 0.2), reach=2.0, ambient=(0.55, 0.5, 0.46), warm=(0.95, 0.82, 0.66))
    T = secs; FLOOR = 1640; hm = 1080

    def men_anim(t):
        return {'dy': 2 * math.sin(t * 1.1)}

    layers = [Layer(bg.convert('RGBA'), W / 2 + 40, H / 2, depth=0.0),
              Layer(men, 650, FLOOR - hm / 2, h=hm, depth=0.55, anim=men_anim, shadow=True),
              Layer(jar('jar', 0), 150, FLOOR + 20, h=420, depth=0.85, shadow=True),
              Layer(jar('ointment_jar', 0), 360, FLOOR + 110, h=300, depth=0.9, shadow=True),
              Layer(jar('roman_glass_jar', 0), 960, FLOOR + 80, h=340, depth=0.9, shadow=True)]
    dust = dust_layer(55, 21)
    word = glow_word('TWO MEN', 150); word2 = glow_word('SHOW UP.', 110, (236, 178, 56))

    def frame(i):
        t = i / FPS
        k = ease(t / T)
        f = render_frame(layers, {'zoom': 1.0 + 0.08 * k, 'panx': -35 * k, 'pany': -10 * k}, t, i)
        f = add_light(f, light_pool(-80, 420, 650, (255, 175, 90)), 0.45)    # low sun from the left
        f.alpha_composite(dust(t))
        if t > 0.8:
            a = min(1, (t - 0.8) / 0.15); w = word.copy(); w.putalpha(w.getchannel('A').point(lambda v: int(v * a)))
            f.alpha_composite(w, (int(W / 2 - w.width / 2), 200))
        if t > 1.3:
            a = min(1, (t - 1.3) / 0.15); w = word2.copy(); w.putalpha(w.getchannel('A').point(lambda v: int(v * a)))
            f.alpha_composite(w, (int(W / 2 - w.width / 2), 370))
        return grain(vignette(f, 0.6), 7, i)
    return write_video(frame, int(T * FPS), 'test_burial.mp4')


if __name__ == '__main__':
    which = sys.argv[1:] or ['cat']
    for w in which:
        print({'cat': scene_cat, 'rooftop': scene_rooftop, 'bed': scene_bed, 'burial': scene_burial}[w]())
