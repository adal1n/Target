import json, sys, numpy as np, soundfile as sf
from scipy import signal
d = json.load(open(sys.argv[1])); info = json.load(open(sys.argv[2])); out = sys.argv[3]
SR = 44100; bpm = info['bpm']; sec = 60 / bpm / 4
P = d['parts']
end = max(n[1] for k in P for n in P[k]) * sec + 2
L = int(end * SR)
rng = np.random.default_rng(0)
hz = lambda m: 440 * 2 ** ((m - 69) / 12)

def env(n, a, dcy, s, r):
    a, dcy, r = int(a * SR), int(dcy * SR), int(r * SR)
    e = np.full(n + r, s, float)
    e[:a] = np.linspace(0, 1, a, endpoint=False)
    e[a:a + dcy] = np.linspace(1, s, len(e[a:a + dcy]))
    e[n:] = np.linspace(e[n - 1] if n else s, 0, r)
    return e

def saw(f, n, ph=0):
    t = np.arange(n) / SR
    x = (t * f + ph) % 1
    return 2 * x - 1

def lp(x, fc, order=2):
    b, a = signal.butter(order, min(fc / (SR / 2), 0.99))
    return signal.lfilter(b, a, x)

def hp(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), 'high')
    return signal.lfilter(b, a, x)

def bp(x, lo, hi):
    b, a = signal.butter(2, [lo / (SR / 2), hi / (SR / 2)], 'band')
    return signal.lfilter(b, a, x)

def place(buf, x, t):
    i = int(t * SR); j = min(L, i + len(x))
    if i < L: buf[i:j] += x[:j - i]

# bass: saw + sub, saturated
bass = np.zeros(L)
for s, e, p, a in P['bass']:
    n = int((e - s) * sec * SR); f = hz(p)
    x = 0.6 * saw(f, n + 2205) + 0.8 * np.sin(2 * np.pi * f * np.arange(n + 2205) / SR)
    x = np.tanh(3 * lp(x, 900)) * env(n, .003, .08, .8, .05)
    place(bass, 0.28 * x, s * sec)

# synth: detuned supersaw, bitcrushed
syn = np.zeros(L)
for s, e, p, a in P['other']:
    n = int((e - s) * sec * SR); f = hz(p); m = n + 4410
    x = sum(saw(f * (1 + dt), m, rng.random()) for dt in (-0.012, -0.005, 0, 0.006, 0.013)) / 5
    x = lp(x, 5000) * env(n, .005, .15, .6, .1)
    x = np.round(x * 24) / 24  # glitchy crush
    place(syn, 0.25 * (0.5 + a) * x, s * sec)

# vocal lead: formant-filtered saw with vibrato
voc = np.zeros(L)
for s, e, p, a in P['vocals']:
    n = int((e - s) * sec * SR); m = n + 4410; f = hz(p)
    t = np.arange(m) / SR
    fi = f * (1 + 0.012 * np.sin(2 * np.pi * 5.5 * t) * np.clip(t / 0.25, 0, 1))
    ph = np.cumsum(fi) / SR
    x = 2 * (ph % 1) - 1
    x = 0.6 * bp(x, 600, 1100) + 0.4 * bp(x, 1000, 1500) + 0.25 * bp(x, 2300, 3000)
    x *= env(n, .02, .1, .85, .1)
    place(voc, 1.6 * x, s * sec)

# drums
def kick():
    t = np.arange(int(.35 * SR)) / SR
    f = 45 + 110 * np.exp(-t * 30)
    return np.tanh(2.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)) + 0.3 * rng.standard_normal(len(t)) * np.exp(-t * 300)
def snare():
    t = np.arange(int(.25 * SR)) / SR
    return 0.5 * np.sin(2 * np.pi * 185 * t) * np.exp(-t * 25) + 0.7 * bp(rng.standard_normal(len(t)), 1500, 8000) * np.exp(-t * 18)
def hat():
    t = np.arange(int(.06 * SR)) / SR
    return 0.35 * hp(rng.standard_normal(len(t)), 7000) * np.exp(-t * 70)
dk = {'kick': (kick, 0.8), 'snare': (snare, 0.55), 'hihat': (hat, 0.5)}
drm = np.zeros(L)
for s, e, nm, a in P['drums']:
    fn, g = dk[nm]; place(drm, g * fn(), s * sec)

stems = {'vocals': voc, 'other': syn, 'bass': bass, 'drums': drm}
pan = {'vocals': 0, 'other': 0.25, 'bass': 0, 'drums': -0.1}
mix = np.zeros((L, 2))
for k, x in stems.items():
    st = np.stack([x * np.sqrt(0.5 - pan[k] / 2), x * np.sqrt(0.5 + pan[k] / 2)], 1)
    sf.write(f'{out}/rerecord_{k}.wav', 0.9 * st / (np.abs(st).max() + 1e-9), SR)
    mix += st
# simple glue: soft clip + normalize
mix = np.tanh(1.2 * mix / np.abs(mix).max()) 
mix = 0.95 * mix / np.abs(mix).max()
sf.write(f'{out}/rerecord_mix.wav', mix, SR)
print('done', end)
