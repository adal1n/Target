import json, numpy as np, librosa
sr = 22050
d = json.load(open('notes.json')); bt = np.array(d['beats'])
y, _ = librosa.load('in/song.wav', sr=sr)
yb, _ = librosa.load('sep/bass.wav', sr=sr)
H = 512
ch = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=H, bins_per_octave=36)
cb = librosa.feature.chroma_cqt(y=yb, sr=sr, hop_length=H, fmin=librosa.note_to_hz('C1'), n_octaves=4)
rms = librosa.feature.rms(y=y, hop_length=H)[0]
fr = librosa.time_to_frames(bt, sr=sr, hop_length=H)
print('global chroma', np.round(ch.mean(1) / ch.mean(1).max(), 2))
print('bass chroma  ', np.round(cb.mean(1) / cb.mean(1).max(), 2))
# key via Krumhansl
maj = np.array([6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88]); mn = np.array([6.33,2.68,3.52,5.38,2.6,3.53,2.54,4.75,3.98,2.69,3.34,3.17])
g = ch.mean(1) + cb.mean(1)
sc = [(np.corrcoef(np.roll(t, k), g)[0, 1], k, q) for t, q in ((maj, 'maj'), (mn, 'min')) for k in range(12)]
print('key', sorted(sc)[-3:])
nb = (len(bt) - 1) // 4
names = 'C C# D D# E F F# G G# A A# B'.split()
tm = {'': [0, 4, 7], 'm': [0, 3, 7], 'dim': [0, 3, 6], 'aug': [0, 4, 8], 'sus4': [0, 5, 7], '5': [0, 7]}
bars = []
for b in range(nb):
    out = []
    for half in range(2):
        a, e = fr[4 * b + 2 * half], fr[4 * b + 2 * half + 2]
        c = ch[:, a:e].mean(1); cbb = cb[:, a:e].mean(1)
        best = None
        for r in range(12):
            for q, iv in tm.items():
                tmpl = np.zeros(12); tmpl[[(r + i) % 12 for i in iv]] = 1
                s = (c / c.max()) @ tmpl / len(iv) + 0.6 * cbb[r] / cbb.max() - (0.08 if q in ('aug', 'sus4', '5') else 0)
                if best is None or s > best[0]: best = (s, names[r] + q, r, q)
        out.append(best[1:])
    bars.append({'bar': b, 't': float(bt[4 * b]), 'rms': float(rms[fr[4 * b]:fr[4 * b + 4]].mean()),
                 'chords': [o[0] for o in out], 'roots': [o[1] for o in out], 'qual': [o[2] for o in out],
                 'bassroot': names[int(np.argmax(cb[:, fr[4*b]:fr[4*b+4]].mean(1)))]})
json.dump(bars, open('bars.json', 'w'))
for b in bars: print(b['bar'], round(b['t'], 1), round(b['rms'], 3), b['bassroot'], b['chords'])
