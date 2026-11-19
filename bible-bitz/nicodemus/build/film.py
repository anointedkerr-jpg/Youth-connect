"""Full Bible Bitz: Nicodemus video. 2.5D: real photo/painting backgrounds, cut-out
characters on their own layers, parallax camera, captions timed to the voiceover,
sound effects mixed to the words. Usage: python3 build/film.py [scene numbers...]"""
import os, sys, json, math, random, subprocess
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont
import motion as M
from motion import Layer, render_frame, relight, night_grade, add_light, light_pool, dust_layer, ease, W, H, FPS
from engine import ROOT, A, grain, font
import stills2 as S2
from timewarp import T, END_NEW

OUTD = os.path.join(ROOT, 'render'); SC = os.path.join(OUTD, 'scenes'); os.makedirs(SC, exist_ok=True)
AUD = os.path.join(ROOT, 'audio')
WORDS = json.load(open(os.path.join(AUD, 'words.json')))
BOWL = lambda s: font('BowlbyOne.ttf', s)
CINZEL = lambda s: font('Cinzel.ttf', s, 700)
GOLD = (236, 178, 56); WHITE = (246, 240, 228)
load = M.load
cut = lambda n: load(f'kittl_cut2/{n}.png')
raw = lambda n: Image.open(A('raw', n + '.jpg')).convert('RGB')


# ---------------- text ----------------
FIX = {'BITS': 'BITZ', 'BITS.': 'BITZ.', 'ANOTHIN.': 'ANOTHEN.', 'ALLOS.': 'ALOES.', 'ARK.': 'ARC.'}
KEY = {'NICODEMUS', 'NIGHT', 'NIGHT?', 'AGAIN', 'ABOVE', 'GALILEE', 'CROSS', 'HUNDRED', '75', 'MYRRH', 'ALOES',
       'DAYLIGHT', 'JOHN', 'FAITH', 'COURAGE', 'FEAR', 'SPIRIT', 'JERUSALEM', 'BITZ', 'BIBLE', 'JESUS', 'BORN',
       'ANOTHEN', 'JOSEPH', 'DEAD', 'ARC', 'QUIET', 'GOD', 'ISRAEL', 'LAW', 'SCRIPTURES', 'PHARISEE', 'RESPECT'}


def caption_chunks():
    chunks, cur = [], []
    for w in WORDS:
        cur.append(w)
        end = w['w'][-1] in '.?!,'
        if end or len(cur) >= 3:
            chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    out = []
    for i, c in enumerate(chunks):
        s = c[0]['s']; e = chunks[i + 1][0]['s'] if i + 1 < len(chunks) else c[-1]['e'] + 0.6
        e = min(e, c[-1]['e'] + 0.5)
        words = [FIX.get(x['w'].upper(), x['w'].upper()) for x in c]
        out.append({'s': s, 'e': e, 'words': words})
    return out


CAPS = caption_chunks()
_cap_cache = {}


def caption_img(words):
    key = ' '.join(words)
    if key in _cap_cache: return _cap_cache[key]
    f = BOWL(70); sw = 7
    spans = []; x = 0
    for w in words:
        bare = w.strip('.,?!"')
        col = GOLD if bare in KEY else WHITE
        l, t, r, b = f.getbbox(w, stroke_width=sw); spans.append((w, col, x, l)); x += (r - l) + 22
    h = f.getbbox('AGjy', stroke_width=sw); hh = h[3] - h[1] + 30
    im = Image.new('RGBA', (x + 40, hh + 30), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for w, col, xx, l in spans:
        d.text((20 + xx - l + 4, 18 - h[1] + 7), w, font=f, fill=(0, 0, 0, 160), stroke_width=sw, stroke_fill=(0, 0, 0, 160))
    im = im.filter(ImageFilter.GaussianBlur(4)); d = ImageDraw.Draw(im)
    for w, col, xx, l in spans:
        d.text((20 + xx - l, 18 - h[1]), w, font=f, fill=col, stroke_width=sw, stroke_fill=(20, 16, 14))
    if im.width > W - 80:
        s = (W - 80) / im.width; im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    _cap_cache[key] = im
    return im


def draw_caption(f, t):
    for c in CAPS:
        if c['s'] - 0.03 <= t < c['e']:
            im = caption_img(c['words']); u = t - c['s']
            sc = 1.18 - 0.18 * min(1, u / 0.12)
            if sc != 1: im = im.resize((int(im.width * sc), int(im.height * sc)), Image.BILINEAR)
            f.alpha_composite(im, (int(W / 2 - im.width / 2), int(1395 - im.height / 2)))
            return


_vt = {}


def verse_tag(txt):
    if txt not in _vt:
        _vt[txt] = S2.glow_text(txt, CINZEL(40), GOLD, glow=8)
    return _vt[txt]


def word_in(f, im, t, t0, x, y, dur=None, slam=True):
    if t < t0 or (dur and t > t0 + dur): return
    u = t - t0; a = min(1, u / 0.1)
    sc = (1.35 - 0.35 * min(1, u / 0.14)) if slam else 1
    w = im if sc == 1 else im.resize((int(im.width * sc), int(im.height * sc)), Image.BILINEAR)
    if a < 1:
        w = w.copy(); w.putalpha(w.getchannel('A').point(lambda v: int(v * a)))
    f.alpha_composite(w, (int(x - w.width / 2), int(y - w.height / 2)))


def big(txt, size=150, col=WHITE):
    return M.glow_word(txt, size, col)


def serif(txt, size=110, col=WHITE):
    return S2.glow_text(txt, CINZEL(size), col, glow=14)


# ---------------- backgrounds ----------------
def fill(im, scale=1.12, blur=0):
    im = im.convert('RGB'); s = max(W * scale / im.width, H * scale / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    return im.convert('RGBA')


def bg_court(night=True):
    g = load('bg/caiaphas_court.jpg').convert('L').crop((60, 60, 1860, 1340))
    im = night_grade(g, warm_spot=(0.5, 0.55, 0.3), strength=0.6) if night else M.warm_grade(g)
    return fill(ImageEnhance.Brightness(im).enhance(0.85 if night else 0.8), blur=3)


def bg_street(which='b', night=True):
    g = load(f'bg/arched_street_{which}.jpg').convert('L')
    g = g.crop((60, 40, g.width - 60, g.height - 120))
    im = night_grade(g, warm_spot=(0.62, 0.42, 0.22), strength=0.5) if night else M.warm_grade(g)
    return fill(ImageEnhance.Brightness(im).enhance(0.8 if night else 0.85), scale=1.12, blur=3)


def bg_painting(name, crop=None, dark=0.85, blur=0):
    im = raw(name)
    if crop: im = im.crop(crop)
    im = S2.grade(im, 0.9, 1.02)
    return fill(ImageEnhance.Brightness(im).enhance(dark), blur=blur)


def gallery(paintings, wall='wood', ws=(560,), pos=((W / 2, 800),), rots=(0,)):
    c = S2.wood_wall(0.5) if wall == 'wood' else S2.velvet_wall(0.6)
    c = c.resize((int(W * 1.12), int(H * 1.12)))
    out = c.copy()
    for (frame, pic), w, (x, y), r in zip(paintings, ws, pos, rots):
        fr = S2.framed(frame, pic, w)
        if r: fr = fr.rotate(r, resample=Image.BICUBIC, expand=True)
        ox, oy = int(x * 1.12 - fr.width / 2), int(y * 1.12 - fr.height / 2)
        sh = M.rim_shadow(fr, 24, 0.7); out.alpha_composite(sh, (ox + 18, oy + 24)); out.alpha_composite(fr, (ox, oy))
    return out


_city = None


def night_sky_city():
    global _city
    if _city is None:
        sky = load('bg/stars.jpg'); sky = sky.crop((0, 0, sky.width, int(sky.height * 0.5)))
        sky = fill(ImageEnhance.Brightness(ImageEnhance.Color(sky).enhance(0.7)).enhance(0.85))
        city = M.city_strip(); s = (W * 1.45) / city.width
        city = city.resize((int(city.width * s), int(city.height * s)), Image.LANCZOS).filter(ImageFilter.GaussianBlur(2))
        _city = (sky, city)
    return _city


def tomb_bg(warm=True):
    bg = load('bg/garden_tomb_color.jpg').crop((620, 0, 1920, 1100))
    return fill(M.sunset_grade(bg), scale=1.1, blur=3.5)


def olives_day():
    g = load('bg/jerusalem_from_olives.jpg').convert('L').crop((150, 120, 1790, 1340))
    im = M.warm_grade(g)
    a = np.asarray(im, dtype=np.float32) * np.array([1.05, 0.95, 0.85]) * 0.9
    return fill(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), blur=2)


# ---------------- scene table ----------------
# each scene: start, end, builder -> dict(layers, cam, extra(f,t), lights, sfx tags)
def L(img, x, y, h=None, depth=0.5, anim=None, shadow=True, blur=0):
    return Layer(img, x, y, h=h, depth=depth, anim=anim, blur=blur, shadow=shadow)


def bgL(img, dx=0):
    return Layer(img, W / 2 + dx, H / 2, depth=0.0, shadow=False)


def push(z=0.08, px=0, py=0):
    return lambda k: {'zoom': 1 + z * k, 'panx': px * k, 'pany': py * k}


def walk_in(dx, bob=7, rate=6, dur=None):
    def a(t):
        k = ease(min(1, t / (dur or 2.0)))
        return {'dx': dx * (1 - k), 'dy': bob * abs(math.sin(t * rate))}
    return a


def fade_in(t0=0.0, d=0.5, dx=0, dy=0):
    def a(t):
        k = ease(min(1, max(0, (t - t0) / d)))
        return {'alpha': k, 'dx': dx * (1 - k), 'dy': dy * (1 - k)}
    return a


def breathe(t):
    return {'dy': 3 * math.sin(t * 1.4), 'scale': 1 + 0.004 * math.sin(t * 1.4)}


def lantern_flicker(x, y, r=260, base=0.5):
    return lambda f, t: add_light(f, light_pool(x, y, r), base + 0.12 * math.sin(t * 12) + 0.06 * math.sin(t * 29))


def build_scenes():
    sc = []
    add = lambda s, e, **kw: sc.append(dict(s=s, e=e, **kw))
    nic = lambda: relight(cut('nicodemus_fullbody_01'), light=(0.2, 0.3), reach=1.2, ambient=(0.55, 0.6, 0.8))
    nic_day = lambda: relight(cut('nicodemus_fullbody_01'), light=(-0.2, 0.2), reach=1.8, ambient=(0.75, 0.7, 0.68), warm=(1.1, 1.0, 0.86))
    lantern = lambda: relight(cut('s01_rooftop_lantern'), light=(0.72, 0.62))

    # 1  Jerusalem. Night.
    sky, city = night_sky_city()
    ledge = M.roof_ledge().filter(ImageFilter.GaussianBlur(4))
    add(0.0, 1.54, layers=lambda: [bgL(sky), L(city, W / 2, 820 + city.height / 2, depth=0.2, shadow=False), Layer(ledge, W / 2, 1600 + ledge.height / 2, depth=0.95)],
        cam=push(0.12, 0, -30), dust='cold', words=[(0.0, big('JERUSALEM.', 128), W / 2, 520), (1.1, big('NIGHT.', 170, GOLD), W / 2, 700)])
    # 2  A man steps out of the shadows.
    add(1.54, 3.12, layers=lambda: [bgL(bg_street('a')), L(lantern(), 560, 1600 - 520, h=1040, depth=0.6, anim=fade_in(0, 0.9, dy=60))],
        cam=push(0.1), lights=[lantern_flicker(700, 1270)], dust='warm')
    # 3  respected, educated, powerful
    add(3.12, 5.56, layers=lambda: [bgL(bg_court()), L(nic(), W / 2, 1640 - 600, h=1200, depth=0.6, anim=breathe)],
        cam=push(0.1, 0, -20), words=[(3.12, serif('RESPECTED', 86), W / 2, 330), (3.9, serif('EDUCATED', 86), W / 2, 450), (4.6, serif('POWERFUL', 86, GOLD), W / 2, 570)])
    # 4a name
    add(5.56, 7.6, layers=lambda: [bgL(S2.wood_wall(0.5).resize((int(W * 1.12), int(H * 1.12)))),
                                   L(nic(), W / 2, 1700 - 650, h=1300, depth=0.6, anim=breathe)],
        cam=push(0.08), words=[(5.7, serif('NICODEMUS', 128), W / 2, 420)], under_words=True)
    # 4b risk his reputation for one conversation (heartbeat)
    add(7.6, 10.38, layers=lambda: [bgL(bg_street('b')), L(nic(), W / 2, 2300 - 1050, h=2100, depth=0.7, anim=breathe)],
        cam=push(0.14, 0, 60), words=[(9.0, big('ONE CONVERSATION.', 92, GOLD), W / 2, 420)])
    # 5 title
    def title_extra(f, t):
        pass
    add(10.38, 12.6, layers=lambda: [bgL(bg_painting('tissot_nicodemus', None, 0.6, 2))],
        cam=push(0.06), words=[(10.45, big('BIBLE BITZ', 150, GOLD), W / 2, 380), (11.52, serif('things you may have missed', 52), W / 2, 1180)])
    # 6a Pharisee, ruler
    add(12.6, 15.0, layers=lambda: [bgL(bg_court()), L(nic(), 640, 1640 - 560, h=1120, depth=0.6, anim=walk_in(-200, dur=1.2))],
        cam=push(0.08, -20), verse='JOHN 3:1')
    # 6b seat among the leaders
    add(15.0, 17.42, layers=lambda: [bgL(bg_painting('sanhedrin', (300, 0, 1500, 1302), 0.8))], cam=push(0.12, 40), verse='JOHN 3:1', sfx_bed='murmur')
    # 7 teacher of Israel
    add(17.42, 19.76, layers=lambda: [bgL(bg_painting('tissot_interview', (20, 20, 570, 748), 0.9))],
        cam=push(0.1), verse='JOHN 3:10')
    # 8 knew the law, the scriptures
    add(19.76, 21.6, layers=lambda: [bgL(bg_painting('callot_pharisees', (40, 40, 1640, 1100), 0.85))], cam=push(0.14, -30))
    # 9 did not have every answer
    add(21.6, 23.26, layers=lambda: [bgL(bg_street('b')), L(nic(), W / 2, 1700 - 650, h=1300, depth=0.6, anim=breathe)],
        cam=push(0.08), words=[(22.3, big('?', 300, GOLD), 820, 520)])
    # 10 leaders had made up their minds
    add(23.26, 25.36, layers=lambda: [bgL(bg_painting('tissot_council', (40, 60, 720, 530), 0.85))], cam=push(0.12, 30), sfx_bed='murmur')
    # 11 watched the miracles, not so sure (bed)
    add(25.36, 28.08, kind='bed')
    # 12 came to Jesus at night (rooftop walk)
    add(28.08, 30.2, kind='rooftop', verse='JOHN 3:2')
    # 13 Why at night? The Bible does not say.
    add(30.2, 31.92, layers=lambda: [bgL(sky), L(city, W / 2, 820 + city.height / 2, depth=0.2, shadow=False), Layer(ledge, W / 2, 1600 + ledge.height / 2, depth=0.95)], cam=push(0.1, 0, -40),
        words=[(30.2, big('WHY AT NIGHT?', 120, GOLD), W / 2, 560)])
    # 14 fear... but he came (cat scare)
    add(31.92, 35.32, kind='cat')
    # 15 respect / Rabbi...
    add(35.32, 39.14, layers=lambda: [bgL(bg_painting('tanner_night_visit', (500, 60, 1500, 1640), 0.9))],
        cam=push(0.12), verse='JOHN 3:2')
    # 16 Jesus answers... born again
    add(39.14, 42.6, layers=lambda: [bgL(bg_painting('dejode_night_piece', (60, 40, 1640, 1180), 0.9))], cam=push(0.16, 0, -30),
        verse='JOHN 3:3', words=[(41.24, big('BORN AGAIN.', 140, GOLD), W / 2, 420)], shake=41.24)
    # 17 Greek word
    add(42.6, 47.2, kind='greek', verse='JOHN 3:3')
    # 18 womb question / fair question
    add(47.2, 51.4, layers=lambda: [bgL(bg_street('a')), L(lantern(), 560, 1620 - 520, h=1040, depth=0.6, anim=breathe)],
        cam=push(0.1), lights=[lantern_flicker(700, 1290)], verse='JOHN 3:4', words=[(47.6, big('?', 260, GOLD), 300, 520), (50.26, big('FAIR.', 150, GOLD), 820, 520)])
    # 19 Jesus explains... from the spirit
    add(51.4, 55.68, layers=lambda: [bgL(bg_painting('tissot_interview', (30, 200, 560, 700), 0.85))], cam=push(0.16, 0, -20),
        verse='JOHN 3:5-6', glow_at=54.84)
    # 20a story goes quiet
    add(55.68, 59.1, layers=lambda: [bgL(bg_street('a', night=False))], cam=push(0.06, 30), words=[(55.9, serif('quiet.', 120), W / 2, 520)], sfx_bed='tick')
    # 20b nothing more of Nicodemus (empty frame)
    add(59.1, 61.74, kind='fade_out')
    # 21a leaders want him arrested
    add(61.74, 63.8, layers=lambda: [bgL(bg_painting('sanhedrin', (100, 0, 1300, 1302), 0.75))], cam=push(0.14, -40), sfx_bed='murmur')
    # 21b one voice speaks up
    add(63.8, 66.64, layers=lambda: [bgL(bg_court()), L(nic(), 760, 1640 - 560, h=1120, depth=0.6, anim=walk_in(260, dur=1.4))],
        cam=push(0.1), sfx_bed='murmur_stop', words=[(65.2, big('ONE VOICE.', 140, GOLD), W / 2, 420)])
    # 22 Does our law judge...
    add(66.64, 68.52, layers=lambda: [bgL(bg_court()), L(nic(), W / 2, 2250 - 1000, h=2000, depth=0.7, anim=breathe)], cam=push(0.1, 0, 40), verse='JOHN 7:51')
    # 23 They turn on him / Galilee
    add(68.52, 70.74, layers=lambda: [bgL(bg_court()), L(relight(cut('s04_council_facepalm'), light=(0.3, 0.2), reach=1.3, ambient=(0.6, 0.62, 0.8)),
                                                           W / 2, 1920 - 560 + 40, h=1120 * 1.6, depth=0.6, anim=fade_in(0, 0.2, dy=40))],
        cam=push(0.08), verse='JOHN 7:52', words=[(69.48, big('GALILEE?!', 140, GOLD), W / 2, 380)], sfx_bed='murmur')
    # 24 says no more
    add(70.74, 72.06, layers=lambda: [bgL(bg_court()), L(nic(), W / 2, 1640 - 450, h=900, depth=0.6)], cam=push(0.05), darken=True)
    # 25 the cross
    add(72.06, 75.42, layers=lambda: [bgL(fill(ImageEnhance.Brightness(raw('zurbaran_crucifixion').crop((0, 0, 1686, 2974))).enhance(0.9), scale=1.1))],
        cam=push(0.1, 0, 60))
    # 26 two men step forward
    add(75.42, 79.68, kind='burial', verse='JOHN 19:38-39')
    # 27 a hundred pounds of myrrh and aloes
    add(79.68, 85.2, kind='spices', verse='JOHN 19:39')
    # 28 came to Jesus by night (callback)
    add(85.2, 88.84, kind='rooftop', verse='JOHN 19:39', words=[(87.2, big('BY NIGHT.', 140), W / 2, 420)])
    # 29 now in daylight
    add(88.84, 92.1, kind='sack_day', words=[(89.2, big('DAYLIGHT.', 140, GOLD), W / 2, 380)])
    # 30 last the Bible tells us / only John
    add(92.1, 95.42, layers=lambda: [bgL(bg_painting('tissot_nicodemus', None, 0.8))], cam=push(0.12),
        words=[(93.84, serif('ONLY JOHN', 110, GOLD), W / 2, 330)])
    # 31-32 three scenes + arc
    add(95.42, 101.04, kind='three')
    # 33 full of questions (bed)
    add(101.04, 102.86, kind='bed2')
    # 34 quiet for a time
    add(102.86, 103.84, layers=lambda: [bgL(bg_street('a', night=False))], cam=push(0.06, -30))
    # 35 standing in the open
    add(103.84, 105.64, layers=lambda: [bgL(tomb_bg()), L(nic_day(), W / 2, 1660 - 600, h=1200, depth=0.6, anim=fade_in(0, 0.4, dy=30))],
        cam=push(0.1), glow_at=103.9, sfx_hit='riser_end')
    # 36 faith / courage
    add(105.64, 108.3, layers=lambda: [bgL(olives_day()), L(nic_day(), 360, 1700 - 500, h=1000, depth=0.6, anim=breathe)], cam=push(0.08, 40),
        words=[(105.64, big('FAITH', 140, GOLD), 700, 460), (107.1, big('COURAGE', 130, GOLD), 680, 620)])
    # 37 Bible Bitz end title
    add(108.3, 110.14, layers=lambda: [bgL(bg_painting('tissot_nicodemus', None, 0.6, 2))],
        cam=push(0.05), words=[(108.3, big('BIBLE BITZ', 150, GOLD), W / 2, 380), (109.14, serif('things you may have missed', 52), W / 2, 1180)])
    # 38 like & subscribe / more people
    add(110.14, 118.4, kind='outro')
    return sc


# ---------------- special scenes ----------------
def special(s):
    k = s['kind']
    if k in ('bed', 'bed2'):
        bg = load('bg/caiaphas_court.jpg').convert('L').crop((70, 420, 560, 1250))
        bg = fill(ImageEnhance.Brightness(night_grade(bg, warm_spot=(0.25, 0.75, 0.35), strength=0.45)).enhance(0.95), blur=2.2)
        bed = relight(cut('s02_awake_in_bed'), light=(0.08, 0.32), reach=1.1, ambient=(0.5, 0.56, 0.78), warm=(1.12, 0.92, 0.68))
        bw = 1100; bh = bw * bed.height / bed.width; FL = 1700
        lamp = (W / 2 - bw / 2 + bw * 0.06, FL - bh + bh * 0.33); head = (W / 2 - bw / 2 + bw * 0.38, FL - bh + bh * 0.12)
        marks = [M.glow_word('?', 170 + 30 * i, (246, 222, 150)) for i in range(3)]
        def ex(f, t):
            f2 = add_light(f, light_pool(W * 0.85, H * 0.2, 420, (120, 150, 230)), 0.35)
            f2 = add_light(f2, light_pool(*lamp, 300), 0.5 + 0.14 * math.sin(t * 12) + 0.07 * math.sin(t * 27))
            u0 = t - s['s']
            for j, m in enumerate(marks):
                u = u0 - 0.3 - j * 0.55
                if u <= 0: continue
                a = min(1, u / 0.25)
                mm = m.copy(); mm.putalpha(mm.getchannel('A').point(lambda v: int(v * a)))
                mm = mm.rotate(8 * math.sin(u * 2 + j), resample=Image.BICUBIC, expand=True)
                f2.alpha_composite(mm, (int(head[0] + (j - 1) * 170 - mm.width / 2), int(head[1] - 230 - u * 120 - mm.height / 2)))
            return f2
        return dict(layers=[bgL(bg), L(bed, W / 2, FL - bh / 2, h=bh, depth=0.55, anim=lambda t: {'dy': 2 * math.sin(t * 1.3)})],
                    cam=push(0.1, 30, 25), post=ex, dust='warm')
    if k == 'rooftop':
        sky, city = night_sky_city()
        ledge = M.roof_ledge().filter(ImageFilter.GaussianBlur(4)); FL = 1640; hm = 1050
        man = relight(cut('s01_rooftop_lantern'), light=(0.72, 0.62))
        d = s['e'] - s['s']
        anim = lambda t: {'dx': -240 + 260 * ease(min(1, t / d)), 'dy': 8 * abs(math.sin(t * 5.5))}
        def ex(f, t):
            u = t - s['s']; mx = 560 - 240 + 260 * ease(min(1, u / d))
            return add_light(f, light_pool(mx + 150, FL - 330, 260), 0.55 + 0.12 * math.sin(t * 11))
        return dict(layers=[Layer(sky, W / 2, 560, depth=0.0, anim=lambda t: {'dx': -10 * t}),
                            L(city, W / 2, 820 + city.height / 2, depth=0.2, shadow=False),
                            L(man, 560, FL - hm / 2, h=hm, depth=0.6, anim=anim),
                            Layer(ledge, W / 2, FL - 40 + ledge.height / 2, depth=0.95)],
                    cam=push(0.08, 40, -15), post=ex, dust='cold')
    if k == 'cat':
        bg = bg_street('b'); FL = 1600; SCARE = T(32.35) - s['s']
        walk = relight(cut('s01_rooftop_lantern'), light=(0.72, 0.62))
        jump = relight(cut('s03_cat_scare'), light=(0.12, 0.42))
        cat = relight(load('kittl_cut2/cat.png'), light=(0.0, 0.3), ambient=(0.55, 0.6, 0.8), warm=(1.1, 0.95, 0.8), reach=1.4)
        def wa(t): return {'alpha': 0} if t >= SCARE else {'dx': -330 * (1 - ease(min(1, t / SCARE))), 'dy': 8 * abs(math.sin(t * 6.5))}
        def ja(t):
            if t < SCARE: return {'alpha': 0}
            u = t - SCARE; return {'dy': -170 * math.sin(min(math.pi, u / 0.85 * math.pi)), 'rot': 4 * math.sin(u * 20) * max(0, 1 - u)}
        def ca(t):
            if t < SCARE - 0.15: return {'alpha': 0, 'dx': 180}
            q = ease(min(1, (t - SCARE + 0.15) / 0.3)); return {'dx': 180 * (1 - q), 'alpha': q}
        meow = big('MEOW.', 150)
        def ex(f, t):
            u = t - s['s']
            if u < SCARE: lx, ly = 470 - 330 * (1 - ease(min(1, u / SCARE))) + 140, FL - 330
            else: lx, ly = 120, FL - 620 - 170 * math.sin(min(math.pi, (u - SCARE) / 0.85 * math.pi))
            f = add_light(f, light_pool(lx, ly, 280), 0.5 + 0.12 * math.sin(t * 13))
            word_in(f, meow, u, SCARE - 0.05, W * 0.62, 1170)
            return f
        return dict(layers=[bgL(bg), L(walk, 470, FL - 450, h=900, depth=0.6, anim=wa), L(jump, 450, FL - 430, h=860, depth=0.6, anim=ja),
                            L(cat, 840, FL - 120, h=250, depth=0.75, anim=ca)],
                    cam=push(0.08, -30, -10), post=ex, dust='warm', shake=32.35, words=[(31.95, big('FEAR?', 150, GOLD), W / 2, 330)])
    if k == 'greek':
        bgc = S2.velvet_wall(0.55).resize((int(W * 1.12), int(H * 1.12)))
        g = S2.glow_text('ἄνωθεν', ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', 170), GOLD, glow=18)
        again = big('AGAIN', 130); above = big('FROM ABOVE', 120, GOLD)
        def ex(f, t):
            u = t - s['s']
            word_in(f, g, u, 0.0, W / 2, 620 - 60 * ease(min(1, max(0, u - 1.5) / 0.5)))
            word_in(f, again, u, T(44.28) - s['s'], W / 2 - 0, 860)
            if u > T(45.42) - s['s']:
                word_in(f, above, u, T(45.42) - s['s'], W / 2, 1040)
            return f
        return dict(layers=[bgL(bgc)], cam=push(0.08), post=ex, dust='warm')
    if k == 'fade_out':
        lay = [bgL(bg_street('a')), L(relight(cut('nicodemus_fullbody_01'), light=(0.2, 0.3), reach=1.2, ambient=(0.55, 0.6, 0.8)),
                                       W / 2, 1640 - 520, h=1040, depth=0.6,
                                       anim=lambda t: {'alpha': max(0, 1 - t / 2.2), 'dx': -40 * t})]
        return dict(layers=lay, cam=push(0.08), dust='warm')
    if k == 'burial':
        bg = tomb_bg()
        men = relight(cut('s06_burial_two_men'), light=(-0.2, 0.3), reach=1.6, ambient=(0.7, 0.66, 0.66), warm=(1.12, 0.98, 0.82))
        jar = lambda n: relight(load(f'cut/{n}.png'), light=(-0.3, 0.2), reach=2.0, ambient=(0.55, 0.5, 0.46), warm=(0.95, 0.82, 0.66))
        FL = 1640
        return dict(layers=[bgL(bg, 40), L(men, 650, FL - 540, h=1080, depth=0.55, anim=walk_in(260, 4, 4, 1.8)),
                            L(jar('jar'), 150, FL + 20, h=420, depth=0.85), L(jar('ointment_jar'), 360, FL + 110, h=300, depth=0.9),
                            L(jar('roman_glass_jar'), 960, FL + 80, h=340, depth=0.9)],
                    cam=push(0.08, -35, -10), post=lambda f, t: add_light(f, light_pool(-80, 420, 650, (255, 175, 90)), 0.45), dust='warm',
                    words=[(75.6, big('TWO MEN', 150), W / 2, 300), (77.4, serif('JOSEPH', 66, GOLD), 830, 470), (78.4, serif('NICODEMUS', 66, GOLD), 420, 470)])
    if k in ('spices', 'sack_day'):
        g = load('bg/garden_tomb_old.jpg').convert('L').crop((60, 40, 1860, 1400)) if k == 'spices' else None
        bg = fill(M.warm_grade(g), blur=3) if k == 'spices' else tomb_bg()
        sack = relight(cut('s05_spice_sack'), light=(-0.2, 0.2), reach=1.8, ambient=(0.75, 0.7, 0.68), warm=(1.1, 1.0, 0.86))
        lay = [bgL(bg), L(sack, 560, 1660 - 560, h=1120, depth=0.6, anim=lambda t: {'dx': -120 + 50 * t, 'dy': 6 * abs(math.sin(t * 3.2)), 'rot': 1.2 * math.sin(t * 3.2)})]
        words = []
        if k == 'spices':
            myrrh = relight(load('cut/kohler_plate185.png'), light=(0, 0), reach=3, ambient=(0.85, 0.8, 0.75), warm=(1, 1, 1))
            aloe = relight(load('cut/kohler_aloe.png'), light=(0, 0), reach=3, ambient=(0.85, 0.8, 0.75), warm=(1, 1, 1))
            lay += [L(myrrh, 140, 820, h=640, depth=0.8, anim=fade_in(T(81.2) - s['s'], 0.3, dx=-200)),
                    L(aloe, 940, 820, h=600, depth=0.8, anim=fade_in(T(81.6) - s['s'], 0.3, dx=200))]
            words = [(80.4, big('100 POUNDS', 140, GOLD), W / 2, 380), (82.6, big('≈ 75 LB TODAY', 96), W / 2, 540)]
        return dict(layers=lay, cam=push(0.08, 30), dust='warm', words=words,
                    post=lambda f, t: add_light(f, light_pool(-80, 420, 650, (255, 175, 90)), 0.4))
    if k == 'three':
        # three stacked panels, one per word, no frames
        pics = [raw('tanner_night_visit').crop((300, 200, 1700, 1100)), raw('sanhedrin').crop((300, 200, 1500, 1000)),
                raw('tissot_carried_tomb').crop((20, 160, 570, 520))]
        ph = 560; gap = 22; top = (H - 3 * ph - 2 * gap) // 2
        panels = []
        for p in pics:
            q = S2.cover(S2.grade(p, 0.9, 1.02), W - 60, ph).convert('RGBA'); panels.append(q)
        times = [T(96.18), T(96.9), T(97.54)]
        bg = Image.new('RGBA', (int(W * 1.12), int(H * 1.12)), (14, 12, 12, 255))
        ys = [top + ph / 2 + i * (ph + gap) for i in range(3)]
        lay = [bgL(bg)] + [L(pn, W / 2, y, depth=0.4, anim=fade_in(tt - s['s'], 0.18, dx=(-1) ** i * 300)) for i, (pn, y, tt) in enumerate(zip(panels, ys, times))]
        labels = [big('NIGHT', 96, GOLD), big('DEFENSE', 96, GOLD), big('BURIAL', 96, GOLD)]
        def ex(f, t):
            u = t - s['s']
            for lab, y, tt in zip(labels, ys, times):
                word_in(f, lab, u, tt - s['s'] + 0.1, W / 2, y + ph / 2 - 70)
            a0 = T(99.84) - s['s']
            if u > a0:   # golden arc drawn down through the three panels
                q = min(1, (u - a0) / 0.9); d = ImageDraw.Draw(f); pts = []
                for i in range(int(60 * q) + 1):
                    v = i / 60; pts.append((140 + v * 800 + 260 * math.sin(v * math.pi), ys[0] - 120 + v * (ys[2] - ys[0] + 240)))
                if len(pts) > 1: d.line(pts, fill=GOLD + (255,), width=14, joint='curve')
            return f
        return dict(layers=lay, cam=push(0.05), post=ex, dust='warm')
    if k == 'outro':
        nic = relight(cut('nicodemus_fullbody_01'), light=(-0.2, 0.2), reach=1.8, ambient=(0.75, 0.7, 0.68), warm=(1.1, 1.0, 0.86))
        jos = relight(cut('joseph_fullbody_01'), light=(-0.2, 0.2), reach=1.8, ambient=(0.75, 0.7, 0.68), warm=(1.1, 1.0, 0.86))
        return dict(layers=[bgL(olives_day()), L(jos, 760, 1700 - 520, h=1040, depth=0.55, anim=breathe), L(nic, 330, 1720 - 560, h=1120, depth=0.6, anim=breathe)],
                    cam=push(0.1, -30), dust='warm', words_old=False,
                    words=[(T(110.4), big('LIKE + SUBSCRIBE', 92, GOLD), W / 2, 330), (T(112.3), serif('more people nobody talks about', 46), W / 2, 470)])
    raise ValueError(k)


# ---------------- frame renderer ----------------
def whip(img, k, direction=1):
    a = np.asarray(img.convert('RGB'))
    n = int(15 + 70 * k); kern = np.zeros((1, n), np.float32); kern[0, :] = 1 / n
    b = cv2.filter2D(a, -1, kern)
    b = np.roll(b, int(direction * 140 * k), axis=1)
    return Image.fromarray(b).convert('RGBA')


def render_scene(i):
    scenes = build_scenes(); s = dict(scenes[i]); s0 = s['s']
    s['s'], s['e'] = T(s['s']), (T(s['e']) if i < len(scenes) - 1 else END_NEW)
    for key in ('shake', 'glow_at'):
        if s.get(key): s[key] = T(s[key])
    s['words'] = [(T(tt), im, x, y) for tt, im, x, y in s.get('words', [])]
    spec = special(s) if s.get('kind') else {}
    layers = spec.get('layers') or s['layers']()
    cam = spec.get('cam') or s.get('cam') or push()
    words = list(s.get('words', [])) + [(T(tt) if spec.get('words_old', True) else tt, im, x, y) for tt, im, x, y in spec.get('words', [])]
    post = spec.get('post'); lights = s.get('lights', [])
    dust = spec.get('dust') or s.get('dust')
    dfn = dust_layer(45, i + 3, warm=(dust != 'cold')) if dust else None
    f0 = round(s['s'] * FPS); f1 = round(s['e'] * FPS); n = f1 - f0
    shake = (T(spec['shake']) if spec.get('shake') else None) or s.get('shake'); glow_at = s.get('glow_at')
    def frame(j):
        t = (f0 + j) / FPS; u = t - s['s']; k = ease(min(1, u / max(0.1, s['e'] - s['s'])))
        c = cam(k)
        if shake and shake <= t < shake + 0.3:
            c = dict(c); c['panx'] += random.Random(j).uniform(-18, 18); c['pany'] += random.Random(j + 7).uniform(-18, 18)
        f = render_frame(layers, c, u, f0 + j)
        for lf in lights: f = lf(f, u)
        if post: f = post(f, t)
        if glow_at and t >= glow_at:
            g = min(1, (t - glow_at) / 0.6); f = add_light(f, light_pool(W / 2, 300, 700, (255, 230, 170)), 0.55 * g)
        if s.get('darken'):
            f = Image.fromarray((np.asarray(f.convert('RGB'), dtype=np.float32) * (1 - 0.5 * k)).astype(np.uint8)).convert('RGBA')
        if dfn: f.alpha_composite(dfn(u))
        for (tt, im, x, y) in words: word_in(f, im, t, tt, x, y)
        if s.get('verse'): f.alpha_composite(verse_tag(s['verse']), (int(W / 2 - verse_tag(s['verse']).width / 2), 1478))
        if s0 not in (0.0, 10.38, 30.2, 108.3): draw_caption(f, t)
        f = M.vignette(f, 0.62)
        # whip-pan out on the last 2 frames, whip in on the first frame
        if j >= n - 2 and i < len(scenes) - 1: f = whip(f, (j - (n - 3)) / 2, 1)
        if j == 0 and i > 0: f = whip(f, 0.5, -1)
        return grain(f, 7, f0 + j)
    path = os.path.join(SC, f'{i:02d}.mp4')
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-preset', 'medium', path], stdin=subprocess.PIPE)
    for j in range(n): p.stdin.write(np.asarray(frame(j).convert('RGB')).tobytes())
    p.stdin.close(); p.wait()
    return i, n


if __name__ == '__main__':
    n = len(build_scenes())
    which = [int(a) for a in sys.argv[1:]] or list(range(n))
    with Pool(4) as pool:
        for i, frames in pool.imap_unordered(render_scene, which):
            print('scene', i, frames, flush=True)
