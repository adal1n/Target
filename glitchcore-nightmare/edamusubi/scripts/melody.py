# melody + UST/MIDI for えだむすび
import json, sys, numpy as np, pretty_midi
sys.path.insert(0, sys.argv[1]); from lyrics import P, morae
A = json.load(open(sys.argv[2])); out = sys.argv[3]
BPM = A['bpm']; CH = A['chords']
PC = {'C': 0, 'C#': 1, 'D': 2, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'Bb': 10, 'B': 11}
IV = {'': [0, 4, 7], 'm': [0, 3, 7], 'dim': [0, 3, 6]}
def chord(bar):
    c = CH[min(bar, len(CH) - 1)]
    for q in ('dim', 'm', ''):
        if c.endswith(q) and c[:len(c) - len(q)] in PC: return PC[c[:len(c) - len(q)]], q
def ctones(bar):
    r, q = chord(bar); return {(r + i) % 12 for i in IV[q]}
def scale(bar):
    s = {2, 4, 5, 7, 9, 10, 0}
    ct = ctones(bar)
    if 1 in ct: s = (s - {0}) | {1}
    if 11 in ct: s = (s - {10}) | {11}
    if 6 in ct: s = (s - {5}) | {6}
    return s

def rhythm(ms, kind, nb):
    N = len(ms); Av = nb * 16 - (2 if kind == 'shout' else 3)
    unit = 4 if N * 4 <= Av and kind == 'sing' else 2
    d = [unit] * N
    if kind == 'shout': d = [2 if not we else 4 for _, we in ms]
    while sum(d) > Av:  # compress to 16ths
        for i in range(N - 1):
            if d[i] == 2 and not ms[i][1] and sum(d) > Av: d[i] = 1
        if all(x == 1 or ms[i][1] for i, x in enumerate(d[:-1])):
            for i in range(N - 1):
                if d[i] > 1 and sum(d) > Av: d[i] = 1
            break
    extra = Av - sum(d)
    add = min(extra, 8 if kind != 'shout' else 4); d[-1] += add; extra -= add
    idx = [i for i, (_, we) in enumerate(ms[:-1]) if we]
    k = 0
    while extra >= 2 and idx:
        d[idx[k % len(idx)]] += 2; extra -= 2; k += 1
        if k > 50: break
    return d

HOOK1, HOOK2 = [74, 74, 77, 76, 74], [72, 74, 77, 79, 81]
HR = [2, 2, 2, 2, 6]
def rng_for(bar, kind):
    if kind == 'whisper': return 64, 62, 69, 4
    if kind == 'shout': return 72, 67, 77, 3
    if bar >= 138: return 75, 69, 79, 5
    if 48 <= bar < 64 or 112 <= bar < 128: return 73, 67, 77, 5
    if 32 <= bar < 48 or 96 <= bar < 112:
        i = ((bar - 32) % 64) // 4; return 64 + 2 * i, 60, 75, 4
    return 67, 62, 74, 4

notes = []  # abs_step, dur, midi, mora, kind
for pi, (kind, b0, nb, kana, kanji, ko) in enumerate(P):
    ms = morae(kana)
    s0 = b0 * 16
    pre = []
    if kind == 'hook':
        nh = 2 if kana.startswith('えだむすび えだむすび') else 1
        for h in range(nh):
            for j in range(5): pre.append((s0 + 16 * h + sum(HR[:j]), HR[j], (HOOK1, HOOK2)[h][j], ms[5 * h + j][0]))
        ms = ms[5 * nh:]; s0 += 16 * nh; nb -= nh; kind = 'sing'
    d = rhythm(ms, kind, nb)
    c, lo, hi, span = rng_for(b0, P[pi][0])
    prev = pre[-1][2] if pre else c - 2
    t = s0; rs = np.random.default_rng(1000 + (pi // 2) * 7 + (b0 >= 72) * 0)
    out_notes = list(pre)
    SH = [[0, 1, 2, 3, 4, 5, 6, 7], [0, -1, -2, -3, -4, -5, -6, -7], [0, 1, 2, 1, 0, -1, 0, 1], [0, 2, 1, 3, 2, 4, 3, 5],
          [0, 3, 2, 1, 0, -1, -2, -3], [0, 0, 1, 0, -1, 0, 1, 2], [0, -2, -1, 0, 2, 1, 0, -1], [0, 4, 3, 2, 1, 2, 3, 4]]
    words = []; cur = []
    for i, (m, we) in enumerate(ms):
        cur.append(i)
        if we: words.append(cur); cur = []
    if cur: words.append(cur)
    i = 0
    for wi, w in enumerate(words):
        pos = (w[0] + len(w) / 2) / max(1, len(ms))
        tgt = c + span * (np.sin(np.pi * min(1, pos * 1.2)) - 0.4) * (1 if pi % 2 == 0 else 0.7)
        if pi % 2 and pos > 0.7: tgt -= 3
        shape = SH[int(rs.integers(len(SH)))]
        if tgt > c + 2 and shape[min(3, len(shape) - 1)] > 0 and rs.random() < 0.5: shape = [-x for x in shape]
        bar = t // 16
        ct = ctones(bar)
        anc = min([p for p in range(lo, hi + 1) if p % 12 in ct], key=lambda p: abs(p - tgt) + 0.3 * abs(p - prev))
        for j, k in enumerate(w):
            m, we = ms[k]; du = d[k]; bar = t // 16
            sc_ = sorted(p for p in range(lo, hi + 1) if p % 12 in scale(bar))
            ia = min(range(len(sc_)), key=lambda q: abs(sc_[q] - anc))
            q = ia + shape[j % len(shape)]; n_ = len(sc_) - 1
            q = -q if q < 0 else (2 * n_ - q if q > n_ else q)  # reflect at range edge
            p = sc_[int(np.clip(q, 0, n_))]
            if (t % 8 == 0) or du >= 4:  # strong: snap to chord tone
                ctp = [x for x in range(lo, hi + 1) if x % 12 in ctones(bar)]
                p = min(ctp, key=lambda x: abs(x - p))
            if P[pi][0] == 'shout': p = min([x for x in range(lo, hi + 1) if x % 12 in ctones(bar)], key=lambda x: abs(x - (c + (3 if we else 0))))
            out_notes.append((t, du, p, m)); prev = p; t += du
    # last note of song lands on tonic
    if pi == len(P) - 2: out_notes[-1] = out_notes[-1][:2] + (74,) + out_notes[-1][3:]
    notes += [(a, b, cc, dd, P[pi][0]) for a, b, cc, dd in out_notes]
notes.sort()
json.dump({'bpm': BPM, 'notes': notes}, open(f'{out}/vocal.json', 'w'), ensure_ascii=False)
print('notes', len(notes), 'range', min(n[2] for n in notes), max(n[2] for n in notes))

# ---- UST (Shift_JIS, OpenUtau/UTAU) ----
TK = 120  # ticks per 16th
lines = ['[#VERSION]', 'UST Version1.2', '[#SETTING]', f'Tempo={BPM}', 'Tracks=1', 'ProjectName=えだむすび',
         'VoiceDir=%VOICE%重音テト', 'OutFile=', 'CacheDir=', 'Tool1=wavtool.exe', 'Tool2=resampler.exe', 'Mode2=True']
idx = 0; cur = 0
def blk(length, lyric, nn, flags='', inten=100):
    global idx
    lines.extend([f'[#{idx:04d}]', f'Length={length}', f'Lyric={lyric}', f'NoteNum={nn}', 'PreUtterance=', f'Intensity={inten}', 'Modulation=0', f'Flags={flags}'])
    idx += 1
for st, du, p, m, kind in notes:
    if st > cur: blk((st - cur) * TK, 'R', 60)
    if m == 'っ': blk(du * TK, 'R', 60)
    else:
        fl = {'shout': 'g-4B80Y100', 'whisper': 'B100', 'sing': '', 'hook': ''}[kind]
        blk(du * TK, m, p, fl, 140 if kind == 'shout' else (70 if kind == 'whisper' else 100))
    cur = st + du
lines.append('[#TRACKEND]')
open(f'{out}/edamusubi_teto.ust', 'w', encoding='cp932', newline='\r\n').write('\n'.join(lines) + '\n')

# ---- MIDI with lyrics (UTF-8) ----
sec = 60 / BPM / 4
pm = pretty_midi.PrettyMIDI(initial_tempo=BPM)
ins = pretty_midi.Instrument(program=54, name='Teto (vocal)')
for st, du, p, m, kind in notes:
    if m == 'っ': continue
    ins.notes.append(pretty_midi.Note(127 if kind == 'shout' else 90, int(p), st * sec, (st + du) * sec))
    pm.lyrics.append(pretty_midi.Lyric(m.encode('utf-8').decode('latin1'), st * sec))
pm.instruments.append(ins); pm.write(f'{out}/edamusubi_vocal.mid')
