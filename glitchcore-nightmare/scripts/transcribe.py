import json, sys, numpy as np, librosa
from basic_pitch import ICASSP_2022_MODEL_PATH
from basic_pitch.inference import predict, Model

sep = sys.argv[1]; out = sys.argv[2]
sr = 22050

# beat-synchronous grid (handles glitch phase jumps)
y, _ = librosa.load(f'{sep}/drums.wav', sr=sr)
dur = len(y) / sr
oe = librosa.onset.onset_strength(y=y, sr=sr, hop_length=256)
_, bfr = librosa.beat.beat_track(onset_envelope=oe, sr=sr, hop_length=256, start_bpm=100, tightness=400)
bt = librosa.frames_to_time(bfr, sr=sr, hop_length=256)
per = np.median(np.diff(bt))
# extend grid to cover full song
pre = np.arange(bt[0] - per, -per, -per)[::-1]
post = np.arange(bt[-1] + per, dur + per, per)
bt = np.concatenate([pre, bt, post])
bpm = 60 / per
# downbeat phase: kick energy on beat k mod 4
kick = oe[np.clip((bt * sr / 256).astype(int), 0, len(oe) - 1)]
ph = int(np.argmax([kick[k::4].mean() for k in range(4)]))
bt = bt[ph:] if bt[0] >= 0 else bt[ph:]
off = bt[0]; st = per / 4
print('bpm', bpm, 'first downbeat', off, 'beats', len(bt))
q = lambda t: int(round(4 * np.interp(t, bt, np.arange(len(bt)), left=(t - bt[0]) / per, right=len(bt) - 1 + (t - bt[-1]) / per)))  # time -> 16th index

model = Model(ICASSP_2022_MODEL_PATH)
cfg = {
    'vocals': dict(onset_threshold=0.5, frame_threshold=0.35, minimum_note_length=90, minimum_frequency=110, maximum_frequency=1400, mono='high'),
    'bass':   dict(onset_threshold=0.5, frame_threshold=0.3, minimum_note_length=90, minimum_frequency=30, maximum_frequency=330, mono='low'),
    'other':  dict(onset_threshold=0.6, frame_threshold=0.4, minimum_note_length=100, minimum_frequency=150, maximum_frequency=3000, mono=None),
}
parts = {}
for name, c in cfg.items():
    mono = c.pop('mono')
    _, _, ev = predict(f'{sep}/{name}.wav', model, multiple_pitch_bends=False, melodia_trick=True, **c)
    notes = []
    for s, e, p, a, _ in ev:
        qs, qe = q(s), max(q(e), q(s) + 1)
        if qs < 0: continue
        notes.append([qs, qe, int(p), float(a)])
    notes.sort()
    if mono:
        # one note per 16th slot: pick highest/lowest pitch weighted by amplitude
        slots = {}
        for n in notes:
            k = n[0]
            if k not in slots: slots[k] = n
            else:
                o = slots[k]
                better = (n[3] > o[3] * 1.3) or (abs(n[3] - o[3]) < o[3] * 0.3 and ((n[2] > o[2]) if mono == 'high' else (n[2] < o[2])))
                if better: slots[k] = n
        notes = [slots[k] for k in sorted(slots)]
        for i in range(len(notes) - 1):
            notes[i][1] = min(notes[i][1], notes[i + 1][0])
        if mono == 'low':  # fold octave errors toward median
            med = np.median([n[2] for n in notes])
            for n in notes:
                while n[2] - med > 9: n[2] -= 12
                while med - n[2] > 9: n[2] += 12
    else:
        # cap polyphony at 4 loudest per onset, drop weak notes
        thr = np.percentile([n[3] for n in notes], 35)
        by = {}
        for n in notes:
            if n[3] >= thr: by.setdefault(n[0], []).append(n)
        notes = [n for k in sorted(by) for n in sorted(by[k], key=lambda x: -x[3])[:4]]
        dedup = {}
        for n in notes: dedup[(n[0], n[2])] = n
        notes = sorted(dedup.values())
    notes = [n for n in notes if n[1] > n[0]]
    parts[name] = notes
    print(name, len(notes))

# drums: band onset classification
yd, _ = librosa.load(f'{sep}/drums.wav', sr=sr)
Sd = np.abs(librosa.stft(yd, n_fft=1024, hop_length=256))
f = librosa.fft_frequencies(sr=sr, n_fft=1024)
bands = {'kick': (30, 120), 'snare': (180, 2500), 'hihat': (6000, 11000)}
drums = []
nslots = q(dur)
tt = librosa.frames_to_time(np.arange(Sd.shape[1]), sr=sr, hop_length=256)
for name, (lo, hi) in bands.items():
    e = Sd[(f >= lo) & (f < hi)].sum(0)
    flux = np.maximum(0, np.diff(np.log1p(e * 10), prepend=0))
    on = librosa.onset.onset_detect(onset_envelope=flux, sr=sr, hop_length=256, units='frames',
                                    pre_max=3, post_max=3, pre_avg=10, post_avg=10, delta={'kick': .12, 'snare': .1, 'hihat': .1}[name], wait=3)
    strength = flux[on]
    keep = strength > np.percentile(strength, {'kick': 55, 'snare': 40, 'hihat': 35}[name]) if len(on) else []
    seen = set()
    for fr, k in zip(on, keep):
        if not k: continue
        s = q(tt[fr])
        if s < 0 or s in seen: continue
        seen.add(s); drums.append([s, s + 1, name, float(flux[fr])])
    print(name, len(seen))
parts['drums'] = sorted(drums, key=lambda x: (x[0], x[2]))
json.dump({'bpm': bpm, 'offset': off, 'step': st, 'beats': bt.tolist(), 'parts': parts}, open(out, 'w'))
