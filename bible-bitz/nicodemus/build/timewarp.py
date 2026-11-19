"""Map times on the first (fast) voiceover timeline to the current voiceover, word by word."""
import os, json, bisect
_A = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'audio')
_o = json.load(open(os.path.join(_A, 'words_v1.json'))); _n = json.load(open(os.path.join(_A, 'words.json')))
_xs, _ys = [0.0], [0.0]
for a, b in zip(_o, _n):
    for x, y in ((a['s'], b['s']), (a['e'], b['e'])):
        if x > _xs[-1] and y >= _ys[-1]: _xs.append(x); _ys.append(y)
END_OLD, END_NEW = 118.4, _n[-1]['e'] + 0.85


def T(t):
    if t >= _xs[-1]:
        return _ys[-1] + (t - _xs[-1]) * (END_NEW - _ys[-1]) / max(1e-6, END_OLD - _xs[-1])
    i = bisect.bisect_right(_xs, t) - 1
    x0, x1, y0, y1 = _xs[i], _xs[i + 1], _ys[i], _ys[i + 1]
    return y0 + (t - x0) * (y1 - y0) / (x1 - x0)
