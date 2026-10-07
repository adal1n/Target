# synth + mix engine for the Maretu-style arrangement
import json, sys, numpy as np, soundfile as sf
from scipy import signal
A = json.load(open(sys.argv[1])); out = sys.argv[2]
SR = 44100; BPM = A['bpm']; ST = 60 / BPM / 4
L = int((A['bars'] * 16 * ST + 4) * SR)
rng = np.random.default_rng(1)
hz = lambda m: 440 * 2 ** ((m - 69) / 12)
T = lambda n: np.arange(n) / SR

def bq(x, kind, f, q=0.707, gain=0):
    # RBJ biquad
    w = 2 * np.pi * min(f, SR * 0.45) / SR; al = np.sin(w) / (2 * q); c = np.cos(w); Ag = 10 ** (gain / 40)
    if kind == 'lp': b = [(1 - c) / 2, 1 - c, (1 - c) / 2]; a = [1 + al, -2 * c, 1 - al]
    elif kind == 'hp': b = [(1 + c) / 2, -(1 + c), (1 + c) / 2]; a = [1 + al, -2 * c, 1 - al]
    elif kind == 'bp': b = [al, 0, -al]; a = [1 + al, -2 * c, 1 - al]
    elif kind == 'peak': b = [1 + al * Ag, -2 * c, 1 - al * Ag]; a = [1 + al / Ag, -2 * c, 1 - al / Ag]
    return signal.lfilter(b, a, x, axis=0)

def adsr(n, a, d, s, r):
    a, d, r = max(1, int(a * SR)), max(1, int(d * SR)), max(1, int(r * SR))
    e = np.full(n + r, float(s))
    e[:min(a, n)] = np.linspace(0, 1, a)[:min(a, n)]
    if a < n: e[a:min(a + d, n)] = np.linspace(1, s, d)[:min(a + d, n) - a]
    e[n:] = e[n - 1] * np.linspace(1, 0, r)
    return e

def saw(f, n, ph=None):
    p = (T(n) * f + (rng.random() if ph is None else ph)) % 1
    return 2 * p - 1

def put(buf, x, t, pan=0.0):
    i = int(t * SR)
    if i >= L: return
    j = min(L, i + len(x)); x = x[:j - i]
    if x.ndim == 1:
        buf[i:j, 0] += x * np.sqrt(0.5 - pan / 2); buf[i:j, 1] += x * np.sqrt(0.5 + pan / 2)
    else: buf[i:j] += x

# ---------------- instruments ----------------
def piano(p, dur, v, stac=False):
    f = hz(p); rel = 0.08 if stac else 0.25
    n = int(min(dur, 0.12) * SR) if stac else int(dur * SR)
    m = n + int(rel * SR); t = T(m)
    B = 0.00035 * (1 + max(0, p - 60) / 24)
    x = np.zeros(m)
    for k in range(1, 14):
        fk = k * f * np.sqrt(1 + B * k * k)
        if fk > 16000: break
        amp = (1 / k ** (1.4 - 0.6 * v)) * (1 if k == 1 else 0.8)
        dec = (0.6 + 0.25 * k) * (1 + (p - 48) / 30)
        for det in (-0.0007, 0.0007):
            x += 0.5 * amp * np.sin(2 * np.pi * fk * (1 + det) * t + rng.random() * 6.28) * np.exp(-dec * t)
    x *= np.minimum(1, t / 0.002)
    off = np.ones(m); off[n:] = np.exp(-(t[n:] - t[n]) / (rel / 4))
    x *= off
    ham = bq(rng.standard_normal(int(0.006 * SR)), 'bp', min(4 * f, 6000), 1.0) * np.linspace(1, 0, int(0.006 * SR))
    x[:len(ham)] += 0.15 * v * ham
    return 0.25 * v * x

def musicbox(p, dur, v):
    f = hz(p); m = int(1.6 * SR); t = T(m)
    wow = 1 + 0.003 * np.sin(2 * np.pi * 0.7 * t) + 0.001 * np.sin(2 * np.pi * 6 * t)
    x = sum(a * np.sin(2 * np.pi * f * r * np.cumsum(wow) / SR) * np.exp(-t * d)
            for r, a, d in ((1, 1, 2.5), (3.01, 0.35, 6), (5.4, 0.18, 10), (8.9, 0.08, 18)))
    x[:200] *= np.linspace(0, 1, 200)
    return 0.22 * v * x

def bell(p, dur, v):
    f = hz(p); m = int(1.2 * SR); t = T(m)
    idx = 3 * np.exp(-t * 6)
    x = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * 3.5 * t)) * np.exp(-t * 3.5)
    x += 0.3 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 8)
    return 0.18 * v * x

KS_CACHE = {}
def ks(f, n, bright=0.5):
    N = max(2, int(SR / f)); g = 0.996
    exc = bq(rng.uniform(-1, 1, N), 'lp', 2000 + 6000 * bright)
    x = np.zeros(n); x[:N] = exc
    a = np.zeros(N + 2); a[0] = 1; a[N] = -g * 0.5; a[N + 1] = -g * 0.5
    return signal.lfilter([1], a, x)

def guitar_note(p, dur, v, pm=False):
    n = int(dur * SR); m = n + int(0.06 * SR)
    sig = np.zeros(m)
    for iv in (0, 7, 12):  # power chord
        sig += ks(hz(p + iv), m, 0.3 if pm else 0.7)
    e = np.ones(m)
    if pm: e = np.exp(-T(m) * 14)
    e[n:] *= np.linspace(1, 0, m - n)
    x = sig * e
    x = np.tanh(9 * x) + 0.3 * np.tanh(30 * x)  # distortion
    x = bq(bq(bq(x, 'hp', 90), 'lp', 4800, 0.9), 'peak', 2200, 1.0, -4)  # cab + vocal pocket
    return 0.12 * v * x

def bass_note(p, dur, v, slide_from=None):
    n = int(dur * SR); m = n + int(0.03 * SR); t = T(m)
    f = np.full(m, hz(p))
    if slide_from is not None:
        k = min(m, int(0.06 * SR)); f[:k] = np.linspace(hz(slide_from), hz(p), k)
    ph = np.cumsum(f) / SR
    x = 0.5 * (2 * ((ph * 1.004) % 1) - 1) + 0.5 * (2 * ((ph * 0.996 + 0.3) % 1) - 1)
    x = bq(x, 'lp', 700, 1.2)
    x = np.tanh(2.5 * x) + 0.9 * np.sin(2 * np.pi * ph)
    x *= adsr(n, 0.003, 0.1, 0.85, 0.03)[:m]
    return 0.3 * v * x

def arp_note(p, dur, v):
    n = int(dur * SR * 0.7); m = n + int(0.02 * SR); t = T(m)
    ph = (t * hz(p)) % 1
    x = np.where(ph < 0.3 + 0.15 * np.sin(2 * np.pi * 2 * t), 1.0, -1.0)
    env = adsr(n, 0.002, 0.08, 0.4, 0.02)[:m]
    x = bq(x * env, 'lp', 2500 + 4000 * v)
    return 0.08 * v * x

def strings_note(p, dur, v, stac=False):
    n = int((0.12 if stac else dur) * SR); rel = 0.08 if stac else 0.35; m = n + int(rel * SR); t = T(m)
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * t + rng.random() * 6) * np.clip(t / 0.4, 0, 1)
    x = sum(2 * ((np.cumsum(hz(p) * (1 + d) * vib) / SR + rng.random()) % 1) - 1 for d in (-0.008, -0.004, 0, 0.003, 0.007))
    x = bq(bq(x, 'lp', 3500 if not stac else 5000), 'peak', 2200, 1.0, -3)
    x *= adsr(n, 0.005 if stac else 0.25, 0.1, 0.8, rel)[:m]
    return 0.05 * v * x

def choir_note(p, dur, v):
    n = int(dur * SR); m = n + int(0.5 * SR); t = T(m)
    x = np.zeros(m)
    for d in (-0.006, 0, 0.005, 0.011):
        vib = 1 + 0.006 * np.sin(2 * np.pi * (5 + d * 100) * t)
        x += 2 * ((np.cumsum(hz(p) * (1 + d) * vib) / SR + rng.random()) % 1) - 1
    x = 1.0 * bq(x, 'bp', 800, 4) + 0.6 * bq(x, 'bp', 1150, 5) + 0.25 * bq(x, 'bp', 2900, 6)
    x *= adsr(n, 0.35, 0.2, 0.9, 0.5)[:m]
    return 0.07 * v * x

def orch_note(p, dur, v):
    m = int(0.6 * SR); t = T(m)
    x = sum(2 * ((t * hz(p) * (1 + d) + rng.random()) % 1) - 1 for d in (-0.006, 0, 0.006))
    cut = 600 + 6000 * np.exp(-t * 8)
    x = bq(x, 'lp', 3000) * np.exp(-t * 6)
    x[:int(0.03 * SR)] += 0.6 * rng.standard_normal(int(0.03 * SR)) * np.linspace(1, 0, int(0.03 * SR))
    return 0.06 * v * x

def lead_note(p, dur, v):
    n = int(dur * SR); m = n + int(0.05 * SR); t = T(m)
    x = sum(2 * ((t * hz(p) * (1 + d) + rng.random()) % 1) - 1 for d in (-0.01, -0.004, 0, 0.004, 0.01))
    x = bq(x, 'lp', 5000) * adsr(n, 0.004, 0.1, 0.7, 0.05)[:m]
    x = np.round(x * 12) / 12  # bitcrush flavour
    return 0.06 * v * x

# drums
def kick(v):
    t = T(int(0.4 * SR)); f = 48 + 140 * np.exp(-t * 35)
    x = np.tanh(3 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 10))
    x[:300] += 0.5 * rng.standard_normal(300) * np.linspace(1, 0, 300)
    return 0.9 * v * x
def snare(v):
    t = T(int(0.3 * SR))
    x = 0.6 * np.sin(2 * np.pi * (190 + 40 * np.exp(-t * 60)) * t) * np.exp(-t * 22)
    x += 0.8 * bq(rng.standard_normal(len(t)), 'bp', 4000, 0.5) * np.exp(-t * 14)
    return 0.6 * v * np.tanh(1.5 * x)
def clap(v):
    t = T(int(0.25 * SR)); e = np.zeros(len(t))
    for o in (0, 0.01, 0.02): i = int(o * SR); e[i:] += np.exp(-(t[: len(t) - i]) * 60)
    e += 0.5 * np.exp(-t * 12)
    return 0.5 * v * bq(rng.standard_normal(len(t)), 'bp', 1500, 0.8) * e
def metal(n, decay, hp_f=7000):
    t = T(n); fs = [205.3, 304.4, 369.6, 522.7, 540, 800]
    x = sum(np.sign(np.sin(2 * np.pi * f * 1.7 * t)) for f in fs)
    return bq(bq(x, 'hp', hp_f), 'hp', hp_f) * np.exp(-t * decay)
def hat(v): return 0.12 * v * metal(int(0.06 * SR), 70)
def ohat(v): return 0.12 * v * metal(int(0.35 * SR), 9)
def ride(v):
    x = metal(int(0.6 * SR), 5, 5000) + 0.5 * bq(rng.standard_normal(int(0.6 * SR)), 'hp', 8000) * np.exp(-T(int(0.6 * SR)) * 8)
    return 0.07 * v * x
def crash(v):
    n = int(2.2 * SR); t = T(n)
    x = 0.6 * metal(n, 1.8, 4000) + bq(rng.standard_normal(n), 'hp', 5000) * np.exp(-t * 1.6)
    return 0.15 * v * x
def tom(f0):
    def g(v):
        t = T(int(0.4 * SR)); return 0.6 * v * np.sin(2 * np.pi * np.cumsum(f0 * (1 + 0.6 * np.exp(-t * 20))) / SR) * np.exp(-t * 9)
    return g
DR = {'kick': (kick, 0), 'snare': (snare, 0.05), 'clap': (clap, -0.1), 'hat': (hat, 0.3), 'ohat': (ohat, 0.3), 'ride': (ride, -0.35),
      'crash': (crash, -0.25), 'tomh': (tom(220), 0.3), 'tomm': (tom(160), 0), 'toml': (tom(110), -0.3)}

# ---------------- render stems ----------------
st = {k: np.zeros((L, 2)) for k in ['piano', 'musicbox', 'bells', 'guitar', 'bass', 'arp', 'strings', 'choir', 'orch', 'lead', 'drums', 'fx']}
E = A['events']
sec = lambda e: e['t'] * ST
for e in E['piano']:
    x = piano(e['p'], e['d'] * ST, e['v'], e.get('stac', False))
    if e.get('radio'): x = np.tanh(3 * bq(bq(x, 'hp', 500), 'lp', 2500)) * 0.5
    put(st['piano'], x, sec(e), np.clip((e['p'] - 64) / 40, -0.5, 0.5))
for e in E['musicbox']: put(st['musicbox'], musicbox(e['p'], e['d'] * ST, e['v']), sec(e), 0.3)
for e in E['bells']: put(st['bells'], bell(e['p'], e['d'] * ST, e['v']), sec(e), -0.3)
for e in E['guitar']:
    x = guitar_note(e['p'], e['d'] * ST, e['v'], e.get('pm', False))
    put(st['guitar'], x, sec(e), -0.8)  # double-tracked
    put(st['guitar'], guitar_note(e['p'], e['d'] * ST, e['v'] * 0.95, e.get('pm', False)), sec(e) + 0.012, 0.8)
prev = None
for e in sorted(E['bass'], key=lambda e: e['t']):
    put(st['bass'], bass_note(e['p'], e['d'] * ST, e['v'], prev if (e.get('slide') and prev is not None and prev != e['p']) else None), sec(e))
    prev = e['p']
for i, e in enumerate(E['arp']): put(st['arp'], arp_note(e['p'], e['d'] * ST, e['v']), sec(e), 0.6 * np.sin(i * 0.7))
for e in E['strings']: put(st['strings'], strings_note(e['p'], e['d'] * ST, e['v'], e.get('stac', False)), sec(e), 0.4 * ((e['p'] % 3) - 1))
for e in E['choir']: put(st['choir'], choir_note(e['p'], e['d'] * ST, e['v']), sec(e), 0.3 * ((e['p'] % 3) - 1))
for e in E['orch']: put(st['orch'], orch_note(e['p'], e['d'] * ST, e['v']), sec(e), 0.2 * ((e['p'] % 3) - 1))
for e in E['lead']: put(st['lead'], lead_note(e['p'], e['d'] * ST, e['v']), sec(e), 0.15)
for e in E['drums']:
    fn, pan = DR[e['p']]; put(st['drums'], fn(e['v']), sec(e) + rng.normal(0, 0.002) * (e['p'] in ('hat', 'ride')), pan)
print('instruments rendered')

# fx one-shots
for e in E['fx']:
    k = e['kind']; n = int(e['d'] * ST * SR); t0 = sec(e)
    if k == 'vinyl':
        x = 0.01 * bq(rng.standard_normal(n), 'lp', 3000)
        pops = rng.random(n) < 8 / SR; x += 0.25 * bq(pops * rng.standard_normal(n), 'hp', 1500)
        put(st['fx'], x * e['v'], t0)
    elif k == 'riser':
        t = T(n); fc = 300 * (40 ** (t / t[-1]))
        nz = rng.standard_normal(n); x = np.zeros(n)
        for i in range(0, n, 1024):  # time-varying bandpass
            x[i:i + 1024] = bq(nz[i:i + 1024], 'bp', fc[i], 2)
        sw = np.sin(2 * np.pi * np.cumsum(200 * (8 ** (t / t[-1]))) / SR)
        put(st['fx'], 0.25 * e['v'] * (x + 0.15 * sw) * (t / t[-1]) ** 2, t0)
    elif k == 'revcym':
        c = crash(1.0)[: max(n, 1)][::-1]; put(st['fx'], 1.2 * e['v'] * c, t0 + (n - len(c)) / SR)
    elif k == 'impact':
        t = T(int(2 * SR))
        x = np.sin(2 * np.pi * np.cumsum(35 + 80 * np.exp(-t * 10)) / SR) * np.exp(-t * 2.5)
        x += 0.4 * bq(rng.standard_normal(len(t)), 'lp', 2000) * np.exp(-t * 4)
        put(st['fx'], 0.5 * e['v'] * x, t0)
print('fx rendered')

# ---------------- mix ----------------
# sidechain envelope from kicks
sc = np.ones(L)
for e in E['drums']:
    if e['p'] == 'kick':
        i = int(sec(e) * SR); m = min(L - i, int(0.25 * SR))
        if m > 0: sc[i:i + m] = np.minimum(sc[i:i + m], 1 - 0.55 * np.exp(-T(m) / 0.06))
for k, amt in (('bass', 1), ('strings', 0.8), ('choir', 0.6), ('arp', 0.8), ('guitar', 0.35), ('orch', 0.3)):
    st[k] *= (1 - amt * (1 - sc))[:, None]

def reverb_ir(sec_len=2.4, damp=5000):
    n = int(sec_len * SR); t = T(n)
    ir = rng.standard_normal((n, 2)) * np.exp(-t * 6.9 / sec_len)[:, None]
    ir = bq(ir, 'lp', damp); ir[:int(0.012 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum(0))
IR = reverb_ir()
def reverb(x, wet):
    y = np.stack([signal.fftconvolve(x[:, c], IR[:, c])[:L] for c in range(2)], 1)
    return bq(y, 'hp', 250) * wet
def delay(x, beats=0.75, fb=0.35, wet=0.3):
    d = int(beats * 4 * ST * SR); y = np.zeros_like(x); buf = x.copy()
    for i in range(1, 5):
        sh = np.zeros_like(x); sh[d * i:] = buf[:L - d * i] * fb ** (i - 1)
        if i % 2: sh = sh[:, ::-1]  # ping-pong
        y += sh
    return bq(y, 'lp', 4000) * wet

GAIN = {'piano': 1.1, 'musicbox': 0.9, 'bells': 1.6, 'guitar': 1.5, 'bass': 0.85, 'arp': 2.2, 'strings': 2.2,
        'choir': 2.0, 'orch': 2.2, 'lead': 1.5, 'drums': 0.42, 'fx': 0.9}
RV = {'piano': 0.25, 'musicbox': 0.5, 'bells': 0.4, 'strings': 0.35, 'choir': 0.5, 'orch': 0.3, 'lead': 0.2, 'drums': 0.08, 'arp': 0.15}
DL = {'arp': 0.35, 'bells': 0.3, 'musicbox': 0.25, 'lead': 0.25}
proc = {}
for k, x in st.items():
    y = x * GAIN[k]
    if k in RV: y = y + reverb(y, RV[k])
    if k in DL: y = y + delay(y, wet=DL[k])
    if k == 'drums': y = np.tanh(1.3 * y) / 1.1  # drum bus saturation
    proc[k] = y
mix = sum(proc.values())

# bus glitch fx: stutter / tapestop / crush (applied to full mix + stems consistently)
def apply_bus(fn, i, j):
    global mix
    mix[i:j] = fn(mix[i:j].copy())
    for k in proc: proc[k][i:j] = fn(proc[k][i:j].copy())
for e in E['fx']:
    k = e['kind']; i = int(sec(e) * SR); j = min(L, i + int(e['d'] * ST * SR))
    if k == 'stutter':
        seg = int(4 * ST * SR / e['rate'])  # slice length
        def f(x, seg=seg):
            s = x[:seg].copy(); w = np.minimum(1, np.linspace(0, 40, seg))[:, None] * np.minimum(1, np.linspace(40, 0, seg))[:, None]
            reps = int(np.ceil(len(x) / seg)); y = np.concatenate([s * w] * reps)[:len(x)]
            return y
        apply_bus(f, i, j)
    elif k == 'tapestop':
        def f(x):
            n = len(x); spd = np.linspace(1, 0, n) ** 1.5; pos = np.cumsum(spd)
            pos = np.clip(pos, 0, n - 1)
            return np.stack([np.interp(pos, np.arange(n), x[:, c]) for c in range(2)], 1) * np.linspace(1, 0.2, n)[:, None]
        apply_bus(f, i, j)
    elif k == 'crush':
        def f(x, a=e['amt']):
            hold = int(1 + a * 12); y = np.repeat(x[::hold], hold, axis=0)[:len(x)]
            q = 2 ** (12 - 7 * a); y = np.round(y * q) / q
            return 0.5 * x + 0.5 * y
        apply_bus(f, i, j)

# master: glue comp + limiter
def comp(x, thr=-12, ratio=3, att=0.005, rel=0.12):
    lvl = np.abs(x).max(1); env = signal.lfilter([1 - np.exp(-1 / (rel * SR))], [1, -np.exp(-1 / (rel * SR))], lvl)
    db = 20 * np.log10(env + 1e-9); gr = np.minimum(0, (thr - db) * (1 - 1 / ratio))
    return x * (10 ** (gr / 20))[:, None]
pk = np.abs(mix).max(); mix /= pk
for k in proc: proc[k] /= pk
mix = comp(bq(mix, 'hp', 30), thr=-14, ratio=2.5)
mix = mix / np.abs(mix).max() * 1.6
mix = np.tanh(mix) / np.tanh(1.6) * 0.93  # soft-clip limiter
end = int((A['bars'] * 16 * ST + 3.5) * SR)
mix = mix[:end]; mix[-int(0.05 * SR):] *= np.linspace(1, 0, int(0.05 * SR))[:, None]
sf.write(f'{out}/mix.wav', mix, SR, subtype='PCM_24')
for k, y in proc.items():
    sf.write(f'{out}/stem_{k}.wav', np.clip(y[:end] * 0.9, -1, 1), SR, subtype='PCM_16')
print('done', end / SR)
