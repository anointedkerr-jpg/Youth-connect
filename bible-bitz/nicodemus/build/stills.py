"""Four test stills to approve before the full render."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import *

OUT = os.path.join(ROOT, 'stills'); os.makedirs(OUT, exist_ok=True)
raw = lambda n: Image.open(A('raw', n + '.jpg')).convert('RGB')
cut = lambda n: clean_alpha(Image.open(A('cut', n + '.png')))


def fit(im, w=None, h=None):
    s = (w / im.width) if w else (h / im.height)
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)


def nicodemus(head_scale=1.75):
    """Big-head caricature from Tissot's portrait: head cut and enlarged over the body."""
    src = raw('tissot_nicodemus')
    body_pts = [(0, 1361), (0, 1090), (110, 900), (270, 745), (318, 560), (395, 380), (470, 235), (585, 152),
                (720, 150), (835, 205), (885, 310), (888, 560), (905, 700), (965, 820), (1100, 880), (1199, 930), (1199, 1361)]
    head_pts = [(300, 640), (318, 560), (395, 380), (470, 235), (585, 152), (720, 150), (835, 205), (885, 310),
                (890, 560), (880, 700), (800, 800), (700, 850), (560, 850), (430, 800), (330, 720)]
    body = poly_cut(src, body_pts); head = poly_cut(src, head_pts, feather=5)
    bs = 1 / head_scale                      # small body under a full-size head
    body = fit(body, w=int(body.width * bs))
    canvas = Image.new('RGBA', (head.width + 600, head.height + body.height + 200), (0, 0, 0, 0))
    nx, ny = 300 + head.width // 2, head.height + 20   # chin point
    canvas.alpha_composite(body, (int(nx - 595 * bs), int(ny - 800 * bs)))
    canvas.alpha_composite(head, (nx - head.width // 2 + 10, 20))
    return grade(canvas.crop(canvas.getbbox()), sat=0.95, warm=1.03)


def s1():
    c = paper(MUSTARD, seed=3)
    place(c, fit(grade(cut('kohler_plate185'), 0.8), h=820), 250, 1020, rot=8, shadow=(10, 12))
    place(c, fit(grade(cut('kohler_aloe'), 0.85), h=760), 860, 1010, rot=-9, shadow=(10, 12))
    place(c, sticker(fit(grade(cut('jar'), 0.9, 1.04), w=560), 20, RED, seed=1), 545, 1010, rot=-2)
    place(c, tag('MYRRH', 46), 190, 1330, rot=-6, shadow=(6, 7), blur=6)
    place(c, tag('ALOES', 46), 905, 1320, rot=5, shadow=(6, 7), blur=6)
    place(c, letters('A HUNDRED', 112, seed=4), W // 2, 380)
    place(c, letters('POUNDS', 170, seed=9, colors=(RED, CREAM, RED)), W // 2, 600)
    caption(c, 'OF SPICES.')
    place(c, verse_tag('John 19:39'), 830, 1500, rot=4, shadow=(6, 7), blur=6)
    finish(c, 1).save(f'{OUT}/s1_hook.jpg', quality=92)


def s2():
    c = paper(WALL, seed=5, strength=1.3)
    moon = raw('inness_moonrise').crop((150, 250, 1550, 1250))
    place(c, photo(fit(grade(moon, 0.9), w=600), seed=2), 350, 680, rot=-5)
    n = sticker(fit(nicodemus(), h=900), 22, RED, seed=3)
    place(c, n, 690, 1000, rot=2, shadow=(16, 18), blur=18)
    place(c, tag('NICODEMUS', 76, bg=MUSTARD), 270, 1080, rot=-7, shadow=(7, 8), blur=6)
    place(c, tag('PHARISEE', 44), 180, 1200, rot=4, shadow=(6, 7), blur=6)
    place(c, tag('RULER', 44), 205, 1290, rot=-3, shadow=(6, 7), blur=6)
    place(c, slam('HE VISITS JESUS', ANTON(120)), W // 2, 330)
    caption(c, 'AT NIGHT.')
    place(c, verse_tag('John 3:1-2'), 830, 1500, rot=4, shadow=(6, 7), blur=6)
    finish(c, 2).save(f'{OUT}/s2_night.jpg', quality=92)


def s3():
    c = paper(NIGHT, seed=8, strength=1.2)
    t = raw('tanner_night_visit').crop((60, 60, 1860, 1500))
    place(c, photo(fit(grade(t, 0.9), w=880), border=30, seed=4), W // 2, 1000, rot=3)
    place(c, tag('NICODEMUS', 44, bg=MUSTARD), 330, 760, rot=-5, shadow=(6, 7), blur=6)
    place(c, tag('JESUS', 44), 760, 800, rot=4, shadow=(6, 7), blur=6)
    it = slam('Born...', SERIF_I(170), fill=CREAM, stroke=NIGHT, sw=2)
    place(c, it, 400, 360, rot=-4, shadow=(6, 8), blur=6)
    place(c, letters('AGAIN?', 190, seed=12, colors=(RED, CREAM, MUSTARD)), 640, 560)
    caption(c, '"...WHEN HE IS OLD?"')
    place(c, verse_tag('John 3:3-4'), 830, 1500, rot=4, shadow=(6, 7), blur=6)
    finish(c, 3).save(f'{OUT}/s3_born_again.jpg', quality=92)


def s4():
    c = paper(CHAR, seed=11, strength=1.4)
    tomb = raw('tissot_carried_tomb').crop((30, 40, 560, 560))
    place(c, photo(fit(grade(tomb, 0.85), w=470), seed=6), 540, 700, rot=-4)
    jc = poly_cut(raw('tissot_joseph'), [(150,684),(40,420),(130,250),(250,110),(330,95),(400,200),(440,330),(500,470),(517,684)], 3)
    j = sticker(fit(grade(jc, 0.95, 1.03), h=640), 20, CREAM, seed=5)
    place(c, j, 300, 1090, rot=-3, shadow=(14, 16), blur=16)
    n = sticker(fit(nicodemus(), h=700), 22, RED, seed=3)
    place(c, n, 770, 1050, rot=3, shadow=(16, 18), blur=18)
    place(c, sticker(fit(grade(cut('jar'), 0.9, 1.04), w=250), 14, MUSTARD, seed=1), 540, 1270, rot=6)
    place(c, tag('JOSEPH', 50), 170, 800, rot=-5, shadow=(6, 7), blur=6)
    place(c, tag('NICODEMUS', 50, bg=MUSTARD), 880, 720, rot=4, shadow=(6, 7), blur=6)
    place(c, slam('TWO MEN', ANTON(170)), W // 2, 320)
    place(c, letters('SHOW UP', 120, seed=20, colors=(RED, CREAM)), W // 2, 470)
    caption(c, 'CARRYING SPICES.')
    place(c, verse_tag('John 19:38-39'), 800, 1500, rot=4, shadow=(6, 7), blur=6)
    finish(c, 4).save(f'{OUT}/s4_burial.jpg', quality=92)


if __name__ == '__main__':
    for f in (s1, s2, s3, s4): f()
    ims = [Image.open(f'{OUT}/{n}') for n in sorted(os.listdir(OUT)) if n.startswith('s')]
    sheet = Image.new('RGB', (W * 4 // 2 + 50, H // 2 + 20), (30, 30, 30))
    for i, im in enumerate(ims):
        sheet.paste(im.resize((W // 2, H // 2)), (10 + i * (W // 2 + 10), 10))
    sheet.save(f'{OUT}/contact_sheet.jpg', quality=88)
