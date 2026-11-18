"""Mix voiceover + sound design into the final soundtrack."""
import os, sys, json, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import sfx
from sfx import SR

ROOT = sfx.ROOT; AUD = os.path.join(ROOT, 'audio')
voice = sfx.load(os.path.join(AUD, 'voiceover_final.wav')) * 0.9
TOTAL = 118.4
N = int(TOTAL * SR) + SR
bus = np.zeros(N, np.float32)
vo = np.zeros(N, np.float32); vo[:len(voice)] = voice[:N]


def at(x, t, gain):
    i = int(t * SR); j = min(N, i + len(x))
    if i < N: bus[i:j] += x[:j - i] * gain


def bed(gen, t0, t1, gain, fade=0.6):
    d = t1 - t0; x = gen(d + 0.1)[:int(d * SR)]
    fn = int(min(fade, d / 3) * SR); e = np.ones(len(x), np.float32)
    e[:fn] = np.linspace(0, 1, fn); e[-fn:] = np.linspace(1, 0, fn)
    at(x * e, t0, gain)


db = lambda d: 10 ** (d / 20)

# ---- beds (low, under the voice) ----
for t0, t1 in ((0.0, 3.2), (25.3, 35.4), (85.1, 88.9)):
    bed(sfx.night, t0, t1, db(-25))
bed(lambda d: sfx.drone(d, 55), 0.0, 10.4, db(-26), 1.2)
bed(lambda d: sfx.drone(d, 49), 39.1, 56.0, db(-30), 1.5)
bed(lambda d: sfx.drone(d, 41.2), 72.0, 79.7, db(-21), 0.8)
for t0, t1 in ((15.0, 17.45), (23.2, 25.4), (61.7, 65.25), (68.5, 70.8)):
    bed(sfx.murmur, t0, t1, db(-24), 0.4)
bed(sfx.tick_tock, 55.7, 59.1, db(-20), 0.3)
bed(sfx.wind, 30.2, 31.95, db(-20), 0.4)
bed(lambda d: sfx.warm_pad(d, 110), 103.8, 118.4, db(-27), 1.5)

# ---- whoosh on every scene cut ----
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
cuts = [0.0, 1.54, 3.12, 5.56, 7.6, 10.38, 12.6, 15.0, 17.42, 19.76, 21.6, 23.26, 25.36, 28.08, 30.2, 31.92, 35.32, 39.14,
        42.6, 47.2, 51.4, 55.68, 59.1, 61.74, 63.8, 66.64, 68.52, 70.74, 72.06, 75.42, 79.68, 85.2, 88.84, 92.1, 95.42,
        101.04, 102.86, 103.84, 105.64, 108.3, 110.14]
for c in cuts[1:]:
    w = sfx.whoosh(0.45, True); at(w, max(0, c - 0.2), db(-23))

# ---- hits and spot effects ----
at(sfx.boom(2.4, 46), 0.0, db(-9))
at(sfx.footsteps(4, 0.38), 1.6, db(-17))
for t in (3.12, 3.9, 4.6):
    at(sfx.boom(0.8, 70), t, db(-19))
at(sfx.boom(2.0, 50), 5.65, db(-12))
at(sfx.heartbeat(3, 70), 7.65, db(-13))
at(sfx.boom(2.4, 44), 10.38, db(-10)); at(sfx.shimmer(1.8), 10.45, db(-20))
at(sfx.boom(1.0, 80), 22.3, db(-18))
at(sfx.footsteps(5, 0.42), 28.1, db(-17))
at(sfx.meow(), 32.2, db(-9)); at(sfx.boom(1.2, 60), 32.35, db(-14))
at(sfx.footsteps(2, 0.4), 34.6, db(-18))
at(sfx.scratch(0.45), 41.1, db(-14)); at(sfx.boom(1.8, 48), 41.24, db(-11))
at(sfx.shimmer(1.6), 42.7, db(-22)); at(sfx.shimmer(2.0), 45.42, db(-17))
at(sfx.boom(0.9, 75), 50.26, db(-19))
at(sfx.riser(1.0), 53.85, db(-22)); at(sfx.shimmer(2.0), 54.84, db(-16))
at(sfx.footsteps(4, 0.42), 63.85, db(-16))
at(sfx.boom(1.6, 52), 66.64, db(-13))
at(sfx.boom(1.2, 62), 69.48, db(-16))
at(sfx.boom(3.0, 38), 72.06, db(-8))
at(sfx.heartbeat(2, 50), 73.2, db(-15))
at(sfx.footsteps(5, 0.48), 75.5, db(-15))
at(sfx.boom(1.4, 56), 80.4, db(-14)); at(sfx.boom(1.0, 70), 82.6, db(-18))
at(sfx.footsteps(4, 0.42), 85.3, db(-18))
at(sfx.footsteps(6, 0.55), 88.9, db(-14))
at(sfx.boom(1.2, 60), 93.84, db(-17))
for t in (96.18, 96.9, 97.54):
    at(sfx.boom(0.9, 66), t, db(-15))
at(sfx.whoosh(0.9, True), 99.8, db(-17)); at(sfx.shimmer(1.4), 100.6, db(-20))
at(sfx.riser(1.7), 102.15, db(-17)); at(sfx.boom(2.0, 50), 103.84, db(-13)); at(sfx.shimmer(2.2), 103.9, db(-17))
at(sfx.boom(2.2, 46), 108.3, db(-11)); at(sfx.shimmer(1.8), 108.35, db(-18))

# ---- gentle ducking of the sound bus under the voice ----
env = np.abs(vo); k = int(0.12 * SR)
env = np.convolve(env, np.ones(k) / k, 'same')
duck = 1 - 0.45 * np.clip(env / (env.max() * 0.25), 0, 1)
mix = vo + bus * duck
mix = np.tanh(mix * 1.1) / 1.1
mix = mix[:int(TOTAL * SR)]
tmp = os.path.join(AUD, 'mix_raw.wav')
import wave
o = wave.open(tmp, 'wb'); o.setnchannels(1); o.setsampwidth(2); o.setframerate(SR)
o.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes()); o.close()
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-af', 'loudnorm=I=-14:TP=-1.2:LRA=10', '-ar', '48000', '-ac', '2',
                os.path.join(AUD, 'soundtrack.wav')], check=True)
print('soundtrack', TOTAL)
