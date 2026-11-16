"""2.5D paper cutout engine: real images in, code only for cutting, borders,
shadows, grain, text and motion."""
import os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops, ImageEnhance

W, H = 1080, 1920
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = lambda *p: os.path.join(ROOT, 'assets', *p)

RED = (196, 38, 34)
CREAM = (240, 228, 200)
MUSTARD = (214, 160, 38)
INK = (24, 20, 18)
NIGHT = (22, 32, 58)
WALL = (112, 22, 24)
CHAR = (38, 34, 34)


def font(name, size, wght=None):
    f = ImageFont.truetype(A('fonts', name), size)
    if wght:
        try:
            f.set_variation_by_axes([wght])
        except Exception:
            pass
    return f


ANTON = lambda s: font('Anton-Regular.ttf', s)
SERIF_I = lambda s: font('Playfair-Italic.ttf', s, 700)
SERIF = lambda s: font('Playfair.ttf', s, 800)
HAND = lambda s: font('Caveat.ttf', s, 700)


# ---------- textures ----------
def _noise(w, h, scale, rng):
    small = rng.random((max(2, h // scale), max(2, w // scale))).astype(np.float32)
    im = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(im, dtype=np.float32) / 255 - 0.5


def paper(color, w=W, h=H, seed=1, strength=1.0, vignette=0.55):
    rng = np.random.default_rng(seed)
    n = (_noise(w, h, 220, rng) * 0.16 + _noise(w, h, 40, rng) * 0.08 +
         _noise(w, h, 6, rng) * 0.07 + _noise(w, h, 1, rng) * 0.09)
    # paper fibres: stretched noise
    fib = np.asarray(Image.fromarray((rng.random((h // 2, w // 40)) * 255).astype(np.uint8))
                     .resize((w, h), Image.BICUBIC), dtype=np.float32) / 255 - 0.5
    n += fib * 0.05
    arr = np.array(color, dtype=np.float32)[None, None, :] * (1 + n[..., None] * strength)
    if vignette:
        yy, xx = np.mgrid[0:h, 0:w]
        d = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
        arr *= (1 - vignette * np.clip(d - 0.45, 0, 1) ** 1.6)[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert('RGBA')


def grain(im, amount=14, seed=0):
    rng = np.random.default_rng(seed)
    a = np.asarray(im.convert('RGBA'), dtype=np.float32)
    n = rng.normal(0, amount, a.shape[:2])[..., None]
    a[..., :3] = np.clip(a[..., :3] + n, 0, 255)
    return Image.fromarray(a.astype(np.uint8))


def grade(im, sat=0.85, warm=1.0, bright=1.0, contrast=1.05):
    """Pull every source into one world: lower saturation, shared warmth."""
    al = im.getchannel('A') if im.mode == 'RGBA' else None
    rgb = ImageEnhance.Color(im.convert('RGB')).enhance(sat)
    rgb = ImageEnhance.Contrast(rgb).enhance(contrast)
    rgb = ImageEnhance.Brightness(rgb).enhance(bright)
    r, g, b = rgb.split()
    r = r.point(lambda v: min(255, int(v * warm)))
    b = b.point(lambda v: int(v / warm))
    rgb = Image.merge('RGB', (r, g, b))
    if al is not None:
        rgb.putalpha(al)
    return rgb


# ---------- cutouts ----------
def clean_alpha(im, keep=0.03):
    """Drop stray specks: keep connected blobs bigger than `keep` of the largest."""
    import cv2
    a = np.asarray(im.getchannel('A'))
    n, lab, stats, _ = cv2.connectedComponentsWithStats((a > 40).astype(np.uint8), 8)
    if n <= 2:
        return im
    big = stats[1:, cv2.CC_STAT_AREA].max()
    ok = np.isin(lab, [i for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] >= keep * big])
    out = im.copy()
    out.putalpha(Image.fromarray((a * ok).astype(np.uint8)))
    return out.crop(out.getbbox())


def poly_cut(im, pts, feather=2):
    m = Image.new('L', im.size, 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(feather))
    out = im.convert('RGBA')
    out.putalpha(m)
    return out.crop(out.getbbox())


def sticker(cut, border=20, color=RED, grain_amt=12, seed=0):
    """Thick sticker border round the whole cutout, plus print grain."""
    pad = border + 6
    w, h = cut.size
    base = Image.new('RGBA', (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    a = Image.new('L', base.size, 0)
    a.paste(cut.getchannel('A'), (pad, pad))
    grown = a.filter(ImageFilter.GaussianBlur(border / 2.2)).point(lambda v: 255 if v > 26 else 0)
    grown = grown.filter(ImageFilter.GaussianBlur(1.2))
    edge = Image.new('RGBA', base.size, color + (255,))
    edge.putalpha(grown)
    base = Image.alpha_composite(base, edge)
    c = Image.new('RGBA', base.size, (0, 0, 0, 0))
    c.paste(cut, (pad, pad))
    base = Image.alpha_composite(base, c)
    g = grain(base, grain_amt, seed)
    g.putalpha(base.getchannel('A'))
    return g


def shadow_of(layer, blur=14, opacity=0.42):
    a = layer.getchannel('A').filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * opacity))
    s = Image.new('RGBA', layer.size, (0, 0, 0, 255))
    s.putalpha(a)
    return s


def place(canvas, layer, cx, cy, scale=1.0, rot=0.0, shadow=(12, 14), blur=14, opacity=0.42):
    """Paste a layer centred at (cx, cy) with a soft drop shadow down and right."""
    if scale != 1.0:
        layer = layer.resize((max(1, int(layer.width * scale)), max(1, int(layer.height * scale))), Image.LANCZOS)
    if rot:
        layer = layer.rotate(rot, resample=Image.BICUBIC, expand=True)
    x, y = int(cx - layer.width / 2), int(cy - layer.height / 2)
    if shadow:
        _paste(canvas, shadow_of(layer, blur, opacity), x + shadow[0], y + shadow[1])
    _paste(canvas, layer, x, y)
    return canvas


def _paste(canvas, layer, x, y):
    tmp = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    tmp.paste(layer, (x, y))
    canvas.alpha_composite(tmp)


# ---------- paper props ----------
def torn_card(w, h, color=CREAM, seed=0, rough=7):
    """A scrap of paper with a rough torn edge."""
    rng = random.Random(seed)
    pts = []
    step = 18
    for x in range(0, w + 1, step): pts.append((x, rng.uniform(0, rough)))
    for y in range(0, h + 1, step): pts.append((w - rng.uniform(0, rough), y))
    for x in range(w, -1, -step): pts.append((x, h - rng.uniform(0, rough)))
    for y in range(h, -1, -step): pts.append((rng.uniform(0, rough), y))
    m = Image.new('L', (w, h), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    card = paper(color, w, h, seed=seed + 7, strength=0.7, vignette=0)
    card.putalpha(m)
    return card


def text_card(txt, fnt, fg=INK, bg=CREAM, pad=(34, 14), seed=0, rough=7):
    l, t, r, b = fnt.getbbox(txt)
    card = torn_card(r - l + 2 * pad[0], b - t + 2 * pad[1], bg, seed, rough)
    ImageDraw.Draw(card).text((pad[0] - l, pad[1] - t), txt, font=fnt, fill=fg)
    return card


def slam(txt, fnt, fill=CREAM, stroke=INK, sw=6):
    """Heavy word with an outline, for slamming in."""
    l, t, r, b = fnt.getbbox(txt, stroke_width=sw)
    im = Image.new('RGBA', (r - l + 8, b - t + 8), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 - l, 4 - t), txt, font=fnt, fill=fill, stroke_width=sw, stroke_fill=stroke)
    return im


def letters(txt, size, colors=(CREAM, MUSTARD, RED), seed=0, gap=6):
    """Cut-out ransom letters: each letter on its own scrap of paper."""
    rng = random.Random(seed)
    f = ANTON(size)
    tiles = []
    for i, ch in enumerate(txt):
        if ch == ' ':
            tiles.append(None); continue
        bg = colors[rng.randrange(len(colors))]
        fg = CREAM if bg == RED else INK
        t = text_card(ch, f, fg, bg, pad=(int(size * .16), int(size * .12)), seed=seed * 31 + i, rough=5)
        tiles.append(t.rotate(rng.uniform(-5, 5), resample=Image.BICUBIC, expand=True))
    hh = max(t.height for t in tiles if t)
    ww = sum((t.width + gap) if t else int(size * .35) for t in tiles)
    out = Image.new('RGBA', (ww + 30, hh + 40), (0, 0, 0, 0))
    x = 10
    for t in tiles:
        if t is None:
            x += int(size * .35); continue
        y = 14 + (hh - t.height) // 2 + rng.randint(-6, 6)
        _paste(out, shadow_of(t, 5, 0.45), x + 5, y + 6)
        _paste(out, t, x, y)
        x += t.width + gap
    return out


def tag(txt, size=58, bg=CREAM, fg=INK, seed=0):
    """Sticker name tag."""
    f = ANTON(size)
    l, t, r, b = f.getbbox(txt)
    w, h = r - l + 64, b - t + 40
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 14, fill=bg + (255,), outline=INK, width=5)
    d.text((32 - l, 20 - t), txt, font=f, fill=fg)
    g = grain(im, 9, seed); g.putalpha(im.getchannel('A'))
    return g


def verse_tag(txt, size=44, seed=0):
    """Price-tag style scripture reference with a punched hole."""
    f = SERIF(size)
    l, t, r, b = f.getbbox(txt)
    w, h = r - l + 120, b - t + 44
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(0, h // 2), (46, 0), (w - 1, 0), (w - 1, h - 1), (46, h - 1)], fill=(232, 214, 170, 255), outline=INK)
    d.line([(0, h // 2), (46, 0), (w - 1, 0), (w - 1, h - 1), (46, h - 1), (0, h // 2)], fill=INK, width=4)
    d.ellipse((34, h // 2 - 11, 56, h // 2 + 11), fill=(0, 0, 0, 0), outline=INK, width=4)
    d.text((84 - l, 22 - t), txt, font=f, fill=INK)
    g = grain(im, 9, seed); g.putalpha(im.getchannel('A'))
    return g


def photo(im, border=26, bottom=None, color=(244, 238, 224), tape=True, seed=0):
    """A painting pasted on the page as a white-bordered print with tape."""
    bottom = border if bottom is None else bottom
    w, h = im.size
    card = paper(color, w + 2 * border, h + border + bottom, seed=seed, strength=0.5, vignette=0)
    card.paste(im.convert('RGBA'), (border, border))
    card = grain(card, 10, seed)
    if tape:
        tw, th = 190, 58
        tp = Image.new('RGBA', (tw, th), (226, 206, 150, 190))
        tp = grain(tp, 8, seed); tp.putalpha(Image.new('L', (tw, th), 185))
        full = Image.new('RGBA', (card.width, card.height + th // 2), (0, 0, 0, 0))
        full.paste(card, (0, th // 2))
        _paste(full, tp.rotate(-3, expand=True, resample=Image.BICUBIC), card.width // 2 - tw // 2, 0)
        card = full
    return card


def caption(canvas, txt, y=1400, size=74):
    """Caption box: same spot in every scene."""
    c = text_card(txt, ANTON(size), INK, CREAM, pad=(40, 20), seed=len(txt))
    return place(canvas, c, W // 2, y, rot=-1.2, shadow=(8, 10), blur=8)


def finish(canvas, seed=0):
    return grain(canvas, 7, seed).convert('RGB')
