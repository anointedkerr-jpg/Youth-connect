"""Sound effects: a few real public-domain/CC0 recordings plus synthesized ones.
Everything is returned as mono float32 numpy arrays at SR."""
import os, subprocess
import numpy as np

SR = 48000
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'audio', 'sfx_src')
rng = np.random.default_rng(7)


def load(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).copy()
    return x / (np.abs(x).max() + 1e-9)


def env(n, a=0.005, r=0.3, curve=2.0):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.clip(1 - (t - a) / r, 0, 1) ** curve
    return e.astype(np.float32)


def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x); s = 0.0
    for i in range(len(x)):
        s = (1 - a) * x[i] + a * s; y[i] = s
    return y


def fft_band(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(x)).astype(np.float32)


def norm(x, peak=0.9):
    return (x / (np.abs(x).max() + 1e-9) * peak).astype(np.float32)


# ---------- synthesized ----------
def boom(dur=2.2, f0=52):
    """Deep cinematic hit: falling sine + sub thump + noise crack."""
    n = int(dur * SR); t = np.arange(n) / SR
    f = f0 * (1 + 1.6 * np.exp(-t * 9))
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * env(n, 0.003, dur, 2.5)
    crack = fft_band(rng.standard_normal(n).astype(np.float32), 80, 2500) * env(n, 0.001, 0.25, 3) * 0.5
    return norm(np.tanh((body + crack) * 2.2))


def whoosh(dur=0.7, up=True):
    n = int(dur * SR)
    x = rng.standard_normal(n).astype(np.float32)
    # sweep a band through the noise
    out = np.zeros(n, np.float32); hop = 2048
    for i in range(0, n, hop):
        k = i / n
        c = 300 + (k if up else 1 - k) * 4200
        seg = x[i:i + hop]
        out[i:i + hop] = fft_band(seg, c * 0.6, c * 1.6)[:len(seg)]
    e = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.6
    return norm(out * e)


def riser(dur=1.8):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 120 * (2 ** (t / dur * 2.5))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.35
    noise = whoosh(dur, True) * 0.7
    e = (t / dur) ** 2
    return norm((tone + noise) * e)


def heartbeat(beats=3, bpm=62):
    one = int(60 / bpm * SR); out = np.zeros(one * beats, np.float32)
    def thump(d=0.16, f=48):
        n = int(d * SR); t = np.arange(n) / SR
        return np.sin(2 * np.pi * f * t * (1 + 0.6 * np.exp(-t * 30))) * env(n, 0.004, d, 3)
    for b in range(beats):
        s = b * one
        a = thump(); out[s:s + len(a)] += a
        c = thump(0.13, 42) * 0.7; s2 = s + int(0.24 * SR); out[s2:s2 + len(c)] += c
    return norm(np.tanh(out * 2))


def tick_tock(secs=4.0):
    n = int(secs * SR); out = np.zeros(n, np.float32)
    for i, s in enumerate(range(0, n, int(0.5 * SR))):
        d = int(0.03 * SR)
        click = fft_band(rng.standard_normal(d).astype(np.float32), 2000 if i % 2 == 0 else 1300, 7000) * env(d, 0.0005, 0.03, 2)
        out[s:s + d] += click[:n - s]
    return norm(out, 0.6)


def shimmer(dur=1.6):
    n = int(dur * SR); t = np.arange(n) / SR; out = np.zeros(n, np.float32)
    for f in (1318.5, 1760, 2093, 2637, 3136):
        out += np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * np.exp(-t * rng.uniform(2, 4))
    trem = 0.6 + 0.4 * np.sin(2 * np.pi * 9 * t)
    return norm(out * trem * env(n, 0.02, dur, 1.2))


def scratch(dur=0.45):
    """Record-scratch-like squeal: fast pitch wobble on filtered noise and a saw."""
    n = int(dur * SR); t = np.arange(n) / SR
    f = 900 + 700 * np.sin(2 * np.pi * 7 * t)
    saw = ((np.cumsum(f) / SR) % 1.0) * 2 - 1
    return norm(fft_band((saw + 0.6 * rng.standard_normal(n)).astype(np.float32), 500, 5000) * env(n, 0.005, dur, 1.5))


def night(secs):
    """Night ambience: crickets (pulsed high tones) over soft wind."""
    n = int(secs * SR); t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for f, rate, ph in ((4400, 2.6, 0), (4950, 3.1, 1.3), (5300, 2.2, 2.1)):
        chirp = (np.sin(2 * np.pi * rate * t + ph) > 0.55).astype(np.float32)
        chirp = np.convolve(chirp, np.ones(200) / 200, 'same')
        out += np.sin(2 * np.pi * f * t) * chirp * (0.6 + 0.4 * np.sin(2 * np.pi * 0.13 * t + ph))
    return norm(out * 0.5 + wind(secs) * 0.6, 0.8)


def wind(secs):
    n = int(secs * SR)
    x = fft_band(rng.standard_normal(n).astype(np.float32), 120, 900)
    t = np.arange(n) / SR
    mod = 0.55 + 0.45 * np.sin(2 * np.pi * 0.11 * t) * np.sin(2 * np.pi * 0.047 * t + 1)
    return norm(x * mod, 0.8)


def murmur(secs):
    """Crowd murmur: many band-limited voices with syllable-rate amplitude."""
    n = int(secs * SR); t = np.arange(n) / SR; out = np.zeros(n, np.float32)
    base = rng.standard_normal(n).astype(np.float32)
    for v in range(10):
        lo = rng.uniform(250, 500); hi = lo * rng.uniform(2.5, 4)
        voice = fft_band(np.roll(base, rng.integers(0, n)), lo, hi)
        syl = np.clip(np.sin(2 * np.pi * rng.uniform(3, 5.5) * t + rng.uniform(0, 6)), 0, 1) ** 2
        phrase = np.clip(np.sin(2 * np.pi * rng.uniform(0.15, 0.4) * t + rng.uniform(0, 6)) + 0.3, 0, 1)
        out += voice * syl * phrase
    return norm(fft_band(out, 150, 3000), 0.8)


def drone(secs, root=55.0):
    """Low dark pad: detuned sines with slow swells."""
    n = int(secs * SR); t = np.arange(n) / SR; out = np.zeros(n, np.float32)
    for mult, amp in ((1, 1), (1.5, 0.5), (2, 0.35), (3, 0.15)):
        for det in (-0.6, 0.6):
            out += amp * np.sin(2 * np.pi * (root * mult + det) * t + rng.uniform(0, 6))
    swell = 0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * t)
    return norm(out * swell, 0.8)


def warm_pad(secs, root=110.0):
    """Hopeful major pad for the ending."""
    n = int(secs * SR); t = np.arange(n) / SR; out = np.zeros(n, np.float32)
    for mult, amp in ((1, 1), (1.25, 0.6), (1.5, 0.6), (2, 0.4)):
        for det in (-0.4, 0.4):
            out += amp * np.sin(2 * np.pi * (root * mult + det) * t + rng.uniform(0, 6))
    return norm(out * (0.7 + 0.3 * np.sin(2 * np.pi * 0.09 * t)), 0.8)


# ---------- real recordings ----------
def meow():
    x = load(os.path.join(SRC, 'cat_meow.oga'))
    # pick the loudest ~1.3 s
    w = int(1.3 * SR); e = np.convolve(np.abs(x), np.ones(w), 'valid')
    i = int(e.argmax()); return norm(x[i:i + w])


def footsteps(n_steps=4, gap=0.42):
    x = load(os.path.join(SRC, 'footsteps_cc0.wav'))
    # split the recording into individual steps by energy peaks
    e = np.convolve(np.abs(x), np.ones(400) / 400, 'same')
    peaks = [i for i in range(1, len(e) - 1) if e[i] > 0.35 * e.max() and e[i] >= e[i - 1] and e[i] > e[i + 1]]
    starts = []
    for p in peaks:
        if not starts or p - starts[-1] > int(0.15 * SR): starts.append(p)
    steps = [x[max(0, s - 800):s + int(0.22 * SR)] for s in starts] or [x[:int(0.25 * SR)]]
    out = np.zeros(int((n_steps * gap + 0.4) * SR), np.float32)
    for k in range(n_steps):
        s = steps[k % len(steps)] * (0.85 + 0.15 * rng.random())
        p = int(k * gap * SR); out[p:p + len(s)] += s[:len(out) - p]
    # a little stone-hall reverb
    rev = np.zeros_like(out)
    for d, a in ((0.045, 0.35), (0.09, 0.22), (0.15, 0.12)):
        k = int(d * SR); rev[k:] += out[:-k] * a
    return norm(lowpass(out + rev, 5000))


def reveal():
    """Logo reveal: short rising whoosh into a punchy hit, bright chime and sparkle tail.
    The hit lands 0.35 s into the sound."""
    pre = 0.35
    n = int((pre + 2.4) * SR); out = np.zeros(n, np.float32)
    w = whoosh(pre + 0.05, True); out[:len(w)] += w * 0.7
    h = int(pre * SR)
    b = boom(1.6, 58); out[h:h + len(b)] += b[:n - h] * 0.9
    t = np.arange(int(1.8 * SR)) / SR
    chime = sum(np.sin(2 * np.pi * f * t) * a for f, a in ((1046.5, 1), (1568, 0.6), (2093, 0.45), (3136, 0.25))) * np.exp(-t * 3.2)
    out[h:h + len(chime)] += chime[:n - h] * 0.35
    sh = shimmer(1.8); out[h:h + len(sh)] += sh[:n - h] * 0.4
    return norm(np.tanh(out * 1.4))
