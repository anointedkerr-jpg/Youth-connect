"""Stills v2: painterly gallery look (reference style 7). Full-bleed real textures,
gilt frames, depth of field, glow type, no sticker borders."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cv2
from engine import *
from stills import raw, cut, fit, nicodemus

OUT = os.path.join(ROOT, 'stills_v2'); os.makedirs(OUT, exist_ok=True)
GOLD = (236, 178, 56)
WHITE = (246, 240, 228)
BOWL = lambda s: font('BowlbyOne.ttf', s)
CINZEL = lambda s: font('Cinzel.ttf', s, 600)


def cover(im, w=W, h=H):
    s = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def vignette(im, amt=0.75):
    a = np.asarray(im.convert('RGB'), dtype=np.float32)
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    a *= (1 - amt * np.clip(d - 0.35, 0, 1) ** 1.5)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert('RGBA')


def wood_wall(dark=0.42):
    p = raw('paneling').crop((60, 150, 3340, 1010))          # real carved panelling
    tile = fit(p, w=1500)
    wall = Image.new('RGB', (W, H))
    for i, y in enumerate(range(0, H, tile.height)):
        t = tile if i % 2 == 0 else tile.transpose(Image.FLIP_LEFT_RIGHT)
        wall.paste(t, (-200 - (i % 2) * 120, y))
    wall = ImageEnhance.Brightness(grade(wall, 0.8, 1.02)).enhance(dark)
    return vignette(wall, 0.8)


def velvet_wall(dark=0.5):
    v = raw('velvet_b').crop((120, 120, 1560, 1640))
    v = cover(v.resize((v.width * 2, v.height * 2), Image.LANCZOS).filter(ImageFilter.GaussianBlur(3)))
    v = ImageEnhance.Brightness(grade(v, 0.9, 1.0)).enhance(dark)
    return vignette(v, 0.85)


def gilt(name):
    """Key the grey studio backdrop out of a museum frame photo; return frame + its opening mask."""
    im = raw(name)
    hsv = cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2HSV)
    m = ((hsv[..., 1] > 70) & (hsv[..., 2] > 40)).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    m = np.where(lab == 1 + st[1:, cv2.CC_STAT_AREA].argmax(), 255, 0).astype(np.uint8)
    inv = (m == 0).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(inv, 4)
    outside = lab[0, 0]
    areas = [(st[i, cv2.CC_STAT_AREA], i) for i in range(1, n) if i != outside]
    hole = np.where(lab == max(areas)[1], 255, 0).astype(np.uint8)
    hole = cv2.dilate(hole, np.ones((9, 9), np.uint8))
    fr = im.convert('RGBA'); fr.putalpha(Image.fromarray(m).filter(ImageFilter.GaussianBlur(1)))
    box = fr.getbbox()
    return grade(fr.crop(box), 0.95, 1.03), Image.fromarray(hole).crop(box)


def framed(name, picture, w):
    """Put a painting behind a gilt frame's opening."""
    fr, hole = gilt(name)
    s = w / fr.width
    fr = fr.resize((w, int(fr.height * s)), Image.LANCZOS); hole = hole.resize(fr.size, Image.LANCZOS)
    hb = hole.getbbox()
    pic = cover(picture.convert('RGB'), hb[2] - hb[0], hb[3] - hb[1])
    out = Image.new('RGBA', fr.size, (0, 0, 0, 0))
    layer = Image.new('RGBA', fr.size, (0, 0, 0, 0)); layer.paste(pic, hb[:2]); layer.putalpha(hole)
    out.alpha_composite(layer); out.alpha_composite(fr)
    return out


def glow_text(txt, fnt, fill=WHITE, glow=18, shadow=True):
    l, t, r, b = fnt.getbbox(txt)
    pad = glow * 3
    im = Image.new('RGBA', (r - l + 2 * pad, b - t + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if shadow:
        d.text((pad - l + 5, pad - t + 7), txt, font=fnt, fill=(0, 0, 0, 170))
        im = im.filter(ImageFilter.GaussianBlur(5))
    g = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).text((pad - l, pad - t), txt, font=fnt, fill=fill + (130,))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(glow)))
    ImageDraw.Draw(im).text((pad - l, pad - t), txt, font=fnt, fill=fill)
    return im


def soft(layer, r):  # depth of field
    return layer.filter(ImageFilter.GaussianBlur(r))


def put(c, layer, cx, cy, rot=0, sh=(18, 22), blur=22, op=0.55):
    return place(c, layer, cx, cy, rot=rot, shadow=sh, blur=blur, opacity=op)


def verse(c, txt, y=1455):
    put(c, glow_text(txt, CINZEL(40), GOLD, glow=8), W // 2, y, sh=None)


def done(c, name, seed):
    c = vignette(c, 0.45)
    grain(c, 9, seed).convert('RGB').save(f'{OUT}/{name}.jpg', quality=92)


def joseph():
    jc = poly_cut(raw('tissot_joseph'), [(150, 684), (40, 420), (130, 250), (250, 110), (330, 95), (400, 200), (440, 330), (500, 470), (517, 684)], 4)
    return grade(jc, 0.95, 1.03)


def nic():
    """Tissot's Nicodemus, cut whole so he can run off the bottom of the frame."""
    src = raw('tissot_nicodemus')
    pts = [(0, 1361), (0, 1090), (110, 900), (270, 745), (318, 560), (395, 380), (470, 235), (585, 152),
           (720, 150), (835, 205), (885, 310), (888, 560), (905, 700), (965, 820), (1100, 880), (1199, 930), (1199, 1361)]
    return grade(poly_cut(src, pts, 3), 0.95, 1.03)


def bottom(c, layer, cx, base=H + 40, **k):
    """Stand a figure on the bottom edge so it bleeds off the frame."""
    return put(c, layer, cx, base - layer.height // 2, **k)


def s1():
    c = velvet_wall(0.6)
    fa, _ = gilt('frame_gloria_a'); fb, _ = gilt('frame_gloria_b')
    put(c, soft(fit(fb, w=520), 9), 40, 200, rot=24, sh=None)        # out-of-focus foreground gold
    put(c, soft(fit(fa, w=640), 11), 1060, 1700, rot=-18, sh=None)
    put(c, glow_text('A HUNDRED', BOWL(118)), W // 2, 340, sh=None)
    put(c, glow_text('POUNDS', BOWL(176), GOLD), W // 2, 510, sh=None)
    # spices burst out of the jar
    put(c, fit(grade(cut('kohler_plate185'), 0.85), h=640), 330, 960, rot=24)
    put(c, fit(grade(cut('kohler_aloe'), 0.9), h=560), 770, 930, rot=-18)
    put(c, fit(grade(cut('kohler_aloe'), 0.9), h=460), 560, 860, rot=4)
    put(c, fit(grade(cut('jar'), 0.92, 1.05), w=620), W // 2, 1220, sh=(22, 30), blur=30, op=0.7)
    put(c, glow_text('OF SPICES', BOWL(76)), W // 2, 1440, sh=None)
    verse(c, 'JOHN 19:39', 1505)
    done(c, 's1_hook', 1)


def s2():
    c = wood_wall(0.55)
    t = raw('tanner_night_visit').crop((60, 60, 1860, 1500))
    put(c, soft(framed('frame_gloria_a', t, 540), 2), 200, 330, rot=-4)
    put(c, soft(framed('frame_gloria_b', raw('inness_moonrise').crop((300, 500, 1400, 1300)), 380), 2), 900, 330, rot=5)
    put(c, soft(framed('frame_gloria_b', raw('sanhedrin').crop((600, 100, 1700, 1250)), 330), 4), 120, 1120, rot=-7)
    put(c, soft(framed('frame_gloria_a', raw('tissot_council').crop((60, 150, 700, 500)), 420), 4), 980, 1180, rot=6)
    put(c, glow_text('NICODEMUS', CINZEL(132), WHITE, glow=14), W // 2, 640, sh=None)
    bottom(c, fit(nic(), w=980), W // 2 + 10, sh=(24, 30), blur=36, op=0.8)      # overlaps his own name
    put(c, glow_text('PHARISEE.', BOWL(78)), 320, 1400, sh=None)
    put(c, glow_text('RULER.', BOWL(78), GOLD), 790, 1400, sh=None)
    verse(c, 'JOHN 3:1', 1480)
    done(c, 's2_nicodemus', 2)


def s3():
    sky = raw('inness_moonrise')
    c = cover(sky.crop((100, 0, 1250, 2021)))
    c = vignette(ImageEnhance.Brightness(grade(c, 0.9, 0.96)).enhance(0.7), 0.7)
    t = raw('tanner_night_visit').crop((60, 60, 1860, 1500))
    put(c, glow_text('AT NIGHT', BOWL(176)), W // 2, 380, sh=None)
    put(c, framed('frame_gloria_a', t, 900), W // 2, 860, rot=-2, sh=(24, 30), blur=30, op=0.7)
    bottom(c, fit(nic(), w=760), 330, base=H + 120, sh=(22, 28), blur=30, op=0.8)
    put(c, glow_text('HE VISITS', BOWL(70), GOLD), 760, 1350, sh=None)
    put(c, glow_text('JESUS', BOWL(70), GOLD), 760, 1430, sh=None)
    verse(c, 'JOHN 3:2', 1500)
    done(c, 's3_night', 3)


def s4():
    tomb = raw('tissot_carried_tomb').crop((30, 40, 560, 730))
    c = cover(tomb).filter(ImageFilter.GaussianBlur(6))
    c = vignette(ImageEnhance.Brightness(grade(c, 0.8, 1.0)).enhance(0.62), 0.8)
    put(c, glow_text('TWO MEN', BOWL(176)), W // 2, 360, sh=None)
    put(c, glow_text('SHOW UP', BOWL(124), GOLD), W // 2, 525, sh=None)
    put(c, fit(grade(cut('kohler_plate185'), 0.85), h=700), 150, 980, rot=-14)
    put(c, fit(grade(cut('kohler_aloe'), 0.9), h=640), 960, 900, rot=14)
    bottom(c, fit(joseph(), h=1000), 290, base=H + 60, rot=-2, sh=(22, 28), blur=30, op=0.75)
    bottom(c, fit(nic(), w=760), 780, base=H + 60, sh=(22, 28), blur=30, op=0.75)
    put(c, fit(grade(cut('jar'), 0.92, 1.05), w=300), 530, 1300, sh=(16, 22), blur=22, op=0.7)
    put(c, glow_text('JOSEPH', CINZEL(48), WHITE, glow=8), 250, 800, sh=None)
    put(c, glow_text('NICODEMUS', CINZEL(48), WHITE, glow=8), 800, 760, sh=None)
    put(c, glow_text('CARRYING SPICES', BOWL(70)), W // 2, 1440, sh=None)
    verse(c, 'JOHN 19:38-39', 1505)
    done(c, 's4_burial', 4)


if __name__ == '__main__':
    for f in (s1, s2, s3, s4): f()
    ims = [Image.open(f'{OUT}/{n}') for n in sorted(os.listdir(OUT)) if n.startswith('s')]
    sheet = Image.new('RGB', (W * 2 + 50, H // 2 + 20), (20, 20, 20))
    for i, im in enumerate(ims):
        sheet.paste(im.resize((W // 2, H // 2)), (10 + i * (W // 2 + 10), 10))
    sheet.save(f'{OUT}/contact_sheet.jpg', quality=88)
