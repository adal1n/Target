# えだむすび: SFX + guide vocal + MR remix
import json, sys, glob, os, numpy as np, soundfile as sf
from scipy import signal
V = json.load(open(sys.argv[1])); stem_dir = sys.argv[2]; out = sys.argv[3]
SR = 44100; BPM = V['bpm']; ST = 60 / BPM / 4
rng = np.random.default_rng(3)
T = lambda n: np.arange(n) / SR
at = lambda bar, step=0: (bar * 16 + step) * ST

def bq(x, kind, f, q=0.707):
    w = 2 * np.pi * min(f, SR * 0.45) / SR; al = np.sin(w) / (2 * q); c = np.cos(w)
    if kind == 'lp': b = [(1 - c) / 2, 1 - c, (1 - c) / 2]; a = [1 + al, -2 * c, 1 - al]
    elif kind == 'hp': b = [(1 + c) / 2, -(1 + c), (1 + c) / 2]; a = [1 + al, -2 * c, 1 - al]
    else: b = [al, 0, -al]; a = [1 + al, -2 * c, 1 - al]
    return signal.lfilter(b, a, x, axis=0)

stems = {os.path.basename(f)[5:-4]: sf.read(f)[0] for f in glob.glob(f'{stem_dir}/stem_*.wav')}
L = len(next(iter(stems.values())))
def put(buf, x, t, pan=0.0):
    i = int(t * SR)
    if i >= L or i + len(x) <= 0: return
    if i < 0: x = x[-i:]; i = 0
    j = min(L, i + len(x)); x = x[:j - i]
    if x.ndim == 1: buf[i:j, 0] += x * np.sqrt(0.5 - pan / 2); buf[i:j, 1] += x * np.sqrt(0.5 + pan / 2)
    else: buf[i:j] += x

# ================= SFX =================
def creak(dur=1.6, base=35, swell=2.2, bright=1.0):
    n = int(dur * SR); t = T(n); u = t / dur
    env = np.sin(np.pi * u) ** 0.6
    walk = np.cumsum(rng.normal(0, 1, n)) / np.sqrt(n) * 0.6
    rate = base * (1 + swell * np.sin(np.pi * u) ** 2 + walk) .clip(0.3)
    ph = np.cumsum(rate) / SR; k = np.floor(ph); imp = np.zeros(n)
    idx = np.nonzero(np.diff(k, prepend=0))[0]; imp[idx] = rng.uniform(0.5, 1, len(idx))
    imp += 0.05 * rng.standard_normal(n) * (rate / rate.max())  # friction
    modes = [(300, 18, 1), (690, 22, .8), (1250, 25, .6), (2050, 30, .4 * bright), (3300, 30, .25 * bright)]
    x = sum(g * bq(imp, 'bp', f * rng.uniform(.92, 1.08), q) for f, q, g in modes)
    return 1.8 * x * env

def twig(scale=0.4):
    n = int(0.25 * SR); x = np.zeros(n)
    for _ in range(rng.integers(2, 5)):
        i = rng.integers(0, int(0.08 * SR)); m = int(0.004 * SR)
        x[i:i + m] += rng.standard_normal(m) * np.exp(-T(m) * 900) * rng.uniform(.4, 1)
    return scale * (bq(x, 'hp', 1500) + 0.6 * bq(x, 'bp', 1100, 6))

def snap():
    n = int(2.6 * SR); x = np.zeros(n); t = T(n)
    # strain creak, micro cracks, main crack, splinters, falling rustle
    c = creak(0.45, 60, 3, 1.4); x[:len(c)] += 0.6 * c
    for k in range(7):
        i = int((0.25 + 0.03 * k + rng.uniform(0, .01)) * SR); m = int(0.003 * SR)
        x[i:i + m] += rng.uniform(.3, .7) * rng.standard_normal(m)
    i = int(0.47 * SR); m = int(0.025 * SR)
    burst = rng.standard_normal(m) * np.exp(-T(m) * 160)
    x[i:i + m] += 3.0 * burst
    ring = np.zeros(int(0.15 * SR)); ring[0] = 1
    x[i:i + len(ring)] += 1.5 * (bq(ring, 'bp', 900, 8) + bq(ring, 'bp', 1700, 10)) * 40
    th = np.sin(2 * np.pi * np.cumsum(60 + 90 * np.exp(-T(int(.3 * SR)) * 25)) / SR) * np.exp(-T(int(.3 * SR)) * 12)
    x[i:i + len(th)] += 1.2 * th
    for _ in range(40):
        j = i + int(rng.exponential(0.12) * SR); m = int(0.002 * SR)
        if j + m < n: x[j:j + m] += rng.uniform(.05, .35) * rng.standard_normal(m)
    rs = bq(rng.standard_normal(n), 'hp', 3000) * np.exp(-np.maximum(0, t - 0.55) * 2.2) * (t > 0.55) * 0.18
    x += rs * (1 + np.sin(2 * np.pi * 7 * t)) / 2
    return np.tanh(1.2 * x) * 0.9

def thud(g=1.0):
    n = int(0.9 * SR); t = T(n)
    x = np.sin(2 * np.pi * np.cumsum(45 + 70 * np.exp(-t * 18)) / SR) * np.exp(-t * 7)
    x += 0.5 * bq(rng.standard_normal(n), 'lp', 500) * np.exp(-t * 14)
    x += 0.12 * bq(rng.standard_normal(n), 'hp', 2500) * np.exp(-t * 5)  # leaves/dirt
    return g * x

def crow():
    n = int(rng.uniform(.28, .4) * SR); t = T(n); u = t / t[-1]
    f0 = rng.uniform(480, 620) * (1.15 - 0.35 * u) * (1 + 0.04 * rng.standard_normal(n).cumsum() / np.sqrt(n))
    src = 2 * ((np.cumsum(f0) / SR) % 1) - 1
    src = np.sign(src) * np.abs(src) ** 0.5 + 0.4 * rng.standard_normal(n)  # rough
    x = bq(src, 'bp', 1300, 4) + 0.8 * bq(src, 'bp', 2400, 5) + 0.3 * bq(src, 'bp', 3600, 6)
    return 0.6 * x * np.sin(np.pi * u) ** 0.3 * np.exp(-u * 1.5)

def crows(k=3):
    outb = np.zeros(int(2.5 * SR)); p = 0
    for _ in range(k):
        c = crow(); i = int(p * SR); outb[i:i + len(c)] += c[:len(outb) - i]; p += rng.uniform(.38, .55)
    return outb

def wind(dur):
    n = int(dur * SR); t = T(n); x = np.zeros((n, 2))
    for ch in range(2):
        nz = rng.standard_normal(n); y = np.zeros(n)
        fc = 450 + 300 * np.sin(2 * np.pi * (0.07 + .02 * ch) * t + ch)
        for i in range(0, n, 2048): y[i:i + 2048] = bq(nz[i:i + 2048], 'bp', fc[i], 1.5)
        x[:, ch] = y * (0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * t + ch * 2)) 
    fade = np.minimum(1, np.minimum(t / 1.5, (t[-1] - t) / 1.5))
    return 0.25 * x * fade[:, None]

def heartbeat(start_bpm, end_bpm, dur):
    n = int(dur * SR); x = np.zeros(n); tt = 0
    while tt < dur - 0.5:
        b = start_bpm + (end_bpm - start_bpm) * tt / dur
        for off, g in ((0, 1), (0.22, .7)):
            m = int(.12 * SR); i = int((tt + off) * SR)
            if i + m < n: x[i:i + m] += g * np.sin(2 * np.pi * 55 * T(m)) * np.exp(-T(m) * 30)
        tt += 60 / b
    return bq(x, 'lp', 150) * 1.4

sfx = np.zeros((L, 2))
E = []  # (time, sound, gain, pan)
E.append((at(0), wind(at(9)), 1, 0))
for i in range(5): E.append((at(0, 2) + i * 1.85, creak(1.3, 30 + 5 * i, 2.0), 0.55, -0.3 + 0.15 * i))  # swaying rope
E.append((at(2, 6), twig(), 1, 0.4)); E.append((at(5, 0), crows(3), 0.5, 0.6))
E.append((at(8), creak(1.0, 40), 0.5, -0.4))
E.append((at(47, 8), creak(0.9, 55, 3), 0.9, 0.2))  # pre break
E.append((at(48), twig(0.8), 1, -0.3))
for b in (64, 66, 68, 70): E.append((at(b), creak(0.8, 45 + b % 4 * 8, 2.5, 1.3), 0.7, (-1) ** b * 0.4))
E.append((at(69, 8), twig(0.7), 1, 0.3))
E.append((at(72), crows(2), 0.45, -0.6))
E.append((at(111, 8), creak(0.9, 55, 3), 0.9, -0.2))  # pre2 break
E.append((at(117, 4), crows(4), 0.55, 0.5)); E.append((at(118, 8), crows(3), 0.45, -0.5))  # カラスが群がって
E.append((at(128), wind(at(10)), 0.45, 0))
E.append((at(128), heartbeat(70, 150, at(9.5)), 0.4, 0))
for i in range(6): E.append((at(128, 4) + i * 1.75, creak(1.4, 28, 2.4), 0.6, 0.35 * np.sin(i)))
for b in range(134, 137): E.append((at(b, 8), creak(0.7, 60, 3), 0.7, 0))
E.append((at(137, 12) - 0.47, snap(), 1.4, 0))  # crack lands on the silence
E.append((at(138, 1), thud(1.0), 1.0, 0)); E.append((at(139, 9), thud(0.7), 1, 0.1))
E.append((at(150, 8), wind(5), 1.0, 0))
E.append((at(151, 10), creak(1.8, 26, 2.0), 0.8, 0.5))  # someone else's rope
for t0, x, g, pan in E: put(sfx, g * x, t0, pan)

# ================= guide vocal (formant synth) =================
ROW = {'': 'あいうえお', 'k': 'かきくけこ', 'g': 'がぎぐげご', 's': 'さしすせそ', 'z': 'ざじずぜぞ', 't': 'たちつてと', 'd': 'だぢづでど',
       'n': 'なにぬねの', 'h': 'はひふへほ', 'b': 'ばびぶべぼ', 'p': 'ぱぴぷぺぽ', 'm': 'まみむめも', 'r': 'らりるれろ'}
KV = {}
for c, row in ROW.items():
    for ch, v in zip(row, 'aiueo'): KV[ch] = (c, v)
KV.update({'し': ('sh', 'i'), 'じ': ('j', 'i'), 'ち': ('ch', 'i'), 'つ': ('ts', 'u'), 'ふ': ('h', 'u'), 'や': ('y', 'a'), 'ゆ': ('y', 'u'),
           'よ': ('y', 'o'), 'わ': ('w', 'a'), 'を': ('', 'o'), 'ん': ('N', 'N')})
SMV = {'ゃ': 'a', 'ゅ': 'u', 'ょ': 'o', 'ぁ': 'a', 'ぃ': 'i', 'ぅ': 'u', 'ぇ': 'e', 'ぉ': 'o'}
def parse(m):
    c, v = KV.get(m[0], ('', 'a'))
    if len(m) > 1 and m[1] in SMV:
        v = SMV[m[1]]
        if c not in ('sh', 'j', 'ch'): c = c + 'y'
    return c, v
FMT = {'a': [(900, 1.0), (1400, .6), (2900, .3)], 'i': [(330, 1.0), (2700, .45), (3300, .3)], 'u': [(380, 1.0), (1600, .4), (2700, .2)],
       'e': [(550, 1.0), (2300, .5), (3000, .3)], 'o': [(550, 1.0), (950, .7), (2900, .2)], 'N': [(280, 1.0), (1600, .12), (2600, .06)]}
def formant(src, v, shift=1.0):
    y = sum(g * bq(src, 'bp', f * shift, max(2.0, f / 90)) for f, g in FMT[v])
    return y + 0.12 * bq(src, 'bp', 4200, 3)

vox = np.zeros((L, 2))
notes = V['notes']; prevf = None
cut = at(137, 12)
for i, (st, du, p, m, kind) in enumerate(notes):
    if m == 'っ': continue
    t0 = st * ST; dur = du * ST
    if t0 + dur > cut and t0 < at(138): dur = max(0.05, cut - t0)
    n = int((dur + 0.03) * SR); t = T(n)
    f = 440 * 2 ** ((p - 69) / 12)
    f0 = np.full(n, f)
    if prevf and (i and notes[i - 1][0] + notes[i - 1][1] >= st - 1):
        k = min(n, int(0.045 * SR)); f0[:k] = f * (prevf / f) ** (1 - np.linspace(0, 1, k))
    if dur > 0.3: f0 *= 1 + 0.018 * np.sin(2 * np.pi * 5.8 * t) * np.clip((t - 0.18) / 0.15, 0, 1)
    c, v = parse(m)
    if kind == 'shout':
        f0 *= 1 + 0.02 * rng.standard_normal(n).cumsum() / np.sqrt(n) * 3
    ph = np.cumsum(f0) / SR
    glot = 2 * (ph % 1) - 1
    glot = signal.lfilter([0.3], [1, -0.7], glot)  # spectral tilt
    asp = 0.08 * rng.standard_normal(n)
    if kind == 'whisper': src = rng.standard_normal(n) * 0.9
    elif kind == 'shout': src = glot * 1.4 + 0.5 * np.sin(np.pi * ph) + 0.35 * rng.standard_normal(n)  # subharmonic growl
    else: src = glot + asp
    y = formant(src, v, 1.12 if kind == 'shout' else 1.0)
    if kind == 'shout': y = np.tanh(4 * y) * 0.5
    # consonant
    cl = {'s': .07, 'sh': .07, 'z': .05, 'j': .05, 'ts': .05, 'ch': .05, 'h': .05, 'k': .03, 'g': .025, 't': .02, 'd': .02,
          'p': .02, 'b': .02, 'n': .045, 'm': .05, 'N': 0, 'r': .02, 'y': .04, 'w': .04, 'ky': .03, 'gy': .03, 'ny': .045,
          'hy': .05, 'by': .02, 'py': .02, 'my': .05, 'ry': .02}.get(c, 0)
    k = min(n - 1, int(cl * SR))
    if k > 0:
        nz = rng.standard_normal(k); cs = np.zeros(k)
        b0 = c[0] if c else ''
        if c in ('s', 'z', 'ts'): cs = bq(bq(nz, 'hp', 5000), 'hp', 5000) * 1.2
        elif c in ('sh', 'j', 'ch'): cs = bq(nz, 'bp', 3000, 1.2) * 1.2
        elif b0 in 'kg': cs = bq(nz, 'bp', 2500, 2) * np.exp(-T(k) * 120)
        elif b0 in 'tdpb': cs = bq(nz, 'bp', 4000 if b0 in 'td' else 1200, 2) * np.exp(-T(k) * 200)
        elif b0 == 'h': cs = formant(nz, v) * 0.8
        elif b0 in 'nm': cs = bq(glot[:k], 'lp', 400) * 0.6
        elif b0 in 'yw': cs = formant(glot[:k], 'i' if b0 == 'y' else 'u') * 0.7
        elif b0 == 'r': cs = y[:k] * np.linspace(0.3, 1, k)
        if c in ('z', 'j', 'g', 'd', 'b'): cs = cs + 0.4 * bq(glot[:k], 'lp', 500)
        y[:k] = cs * (0.6 if kind != 'shout' else 1.0) + (y[:k] * np.linspace(0, 1, k) if b0 in 'nmywr' else 0)
    env = np.ones(n); a = int(0.008 * SR); r = int(0.03 * SR)
    env[:a] = np.linspace(0, 1, a); env[-r:] = np.linspace(1, 0, r)
    g = {'sing': 0.55, 'shout': 0.9, 'whisper': 0.35}.get(kind, 0.55)
    put(vox, g * y * env, t0, 0.0)
    prevf = f
vox = bq(bq(vox, 'hp', 140), 'lp', 9000)

def reverb(x, sec=2.0, wet=0.2):
    n = int(sec * SR); ir = rng.standard_normal((n, 2)) * np.exp(-T(n) * 6.9 / sec)[:, None]
    ir = bq(ir, 'lp', 5000); ir /= np.sqrt((ir ** 2).sum(0))
    y = np.stack([signal.fftconvolve(x[:, c], ir[:, c])[:L] for c in range(2)], 1)
    return x + wet * bq(y, 'hp', 300)
vox = reverb(vox, 1.8, 0.22); sfx = reverb(sfx, 2.6, 0.35)

# ================= MR from stems =================
G = {'bells': 0.6, 'musicbox': 0.8, 'lead': 0.7}  # make room for vocal
mr = sum(x * G.get(k, 1.0) for k, x in stems.items())
i0, i1 = int(cut * SR), int(at(138) * SR)
mr[i0:i1] *= np.linspace(1, 0, 1, endpoint=True)[0] * 0  # dead silence for the snap
def master(x):
    lvl = np.abs(x).max(1); rel = np.exp(-1 / (0.12 * SR))
    env = signal.lfilter([1 - rel], [1, -rel], lvl); db = 20 * np.log10(env + 1e-9)
    x = x * (10 ** (np.minimum(0, (-14 - db) * (1 - 1 / 2.5)) / 20))[:, None]
    x = x / np.abs(x).max() * 1.6
    return np.tanh(x) / np.tanh(1.6) * 0.93
def norm_ref(x, ref): return x / (np.abs(ref).max() + 1e-9)
# vocal level automation (dB) per bar range
for a, b, db in [(8, 32, -2.5), (32, 48, 0.5), (48, 64, 3), (64, 72, 0), (72, 96, -2.5), (96, 112, 0.5), (112, 128, 3), (128, 134, 5), (134, 138, 2), (138, 150, 4), (150, 152, 6)]:
    vox[int(at(a) * SR):int(at(b) * SR)] *= 10 ** (db / 20)
pk = np.abs(mr).max()
mr_n, sfx_n, vox_n = mr / pk, sfx / pk * 0.9, vox / pk * 1.0
sf.write(f'{out}/MR_inst_sfx.wav', master(mr_n * 0.85 + sfx_n), SR, subtype='PCM_16')
sf.write(f'{out}/guide_full.wav', master(mr_n * 0.75 + sfx_n + vox_n), SR, subtype='PCM_16')
sf.write(f'{out}/stem_sfx.wav', np.clip(sfx_n, -1, 1), SR, subtype='PCM_16')
sf.write(f'{out}/stem_guide_vocal.wav', np.clip(vox_n / max(1, np.abs(vox_n).max()), -1, 1), SR, subtype='PCM_16')
def r(x, a, b): seg = x[int(at(a) * SR):int(at(b) * SR)]; return 20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-9)
for nm_, a, b in [('verse', 8, 32), ('pre', 32, 46), ('chorus', 48, 64), ('bridgeQ', 128, 134), ('final', 138, 150)]:
    print(nm_.ljust(8), 'mr', round(r(mr_n * 0.75, a, b), 1), 'vox', round(r(vox_n, a, b), 1), 'sfx', round(r(sfx_n, a, b), 1))
