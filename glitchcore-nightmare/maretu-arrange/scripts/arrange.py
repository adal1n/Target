# Maretu-style arrangement: builds note events per instrument on a 16th grid
import json, sys
import numpy as np

bars_in = json.load(open(sys.argv[1])); notes = json.load(open(sys.argv[2])); out = sys.argv[3]
bt = np.array(notes['beats'])
BPM = round(2 * 60 * (len(bt) - 1) / (bt[-1] - bt[0]), 2)  # double-time of original pulse
NB = 2 * len(bars_in)
rng = np.random.default_rng(7)

PC = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}
QUAL = {2: 'm', 7: 'm', 9: '', 10: '', 0: '', 5: '', 1: 'dim', 11: 'dim', 6: 'dim', 4: 'dim', 3: '', 8: 'dim'}
IV = {'': [0, 4, 7], 'm': [0, 3, 7], 'dim': [0, 3, 6]}
NAMES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'G#', 'A', 'Bb', 'B']

# chord per new bar (orig half-bar -> new bar)
chords = []
for b in bars_in:
    for r in b['roots']:
        chords.append((r, QUAL[r]))
chords = chords[:NB]
# final pedal: lament bass over D
LAMENT = [(2, 'm'), (2, 'm'), (1, 'dim'), (1, 'dim'), (0, ''), (0, ''), (11, 'dim'), (11, 'dim'), (10, ''), (10, ''), (9, ''), (9, '')]
for i, c in enumerate(LAMENT): chords[138 + i] = c
chords[150] = chords[151] = (2, 'm')

SEC = [('intro', 0, 8), ('verse', 8, 32), ('pre', 32, 48), ('chorus', 48, 64), ('inter', 64, 72),
       ('verse2', 72, 96), ('pre2', 96, 112), ('chorus2', 112, 128), ('bridge', 128, 138), ('final', 138, 150), ('end', 150, NB)]
def sec_of(bar):
    for n, a, e in SEC:
        if a <= bar < e: return n, bar - a, e - a

ev = {k: [] for k in ['piano', 'musicbox', 'bells', 'guitar', 'bass', 'arp', 'strings', 'choir', 'orch', 'lead', 'drums', 'fx']}
def add(inst, bar, step, dur, pitch, vel=0.8, **kw):
    ev[inst].append(dict(t=bar * 16 + step, d=dur, p=pitch, v=vel, **kw))

def tones(bar, octv=4):
    r, q = chords[bar]
    base = 12 * (octv + 1) + r
    return [base + i for i in IV[q]]

# hook melody (intro/outro), 8 bars, (step,dur,note)
HOOK = [
    [(0, 2, 'D5'), (2, 2, 'F5'), (4, 2, 'A5'), (6, 1, 'G#5'), (7, 1, 'A5'), (8, 4, 'D6'), (12, 2, 'C#6'), (14, 2, 'A5')],
    [(0, 2, 'Bb5'), (2, 2, 'A5'), (4, 2, 'F5'), (6, 2, 'E5'), (8, 2, 'F5'), (10, 2, 'D5'), (12, 4, 'C#5')],
    [(0, 2, 'E5'), (2, 2, 'G5'), (4, 2, 'Bb5'), (6, 2, 'A5'), (8, 2, 'G5'), (10, 2, 'E5'), (12, 2, 'C#5'), (14, 2, 'E5')],
    [(0, 4, 'A5'), (4, 2, 'G#5'), (6, 2, 'A5'), (8, 4, 'C#6'), (12, 4, 'E6')],
    [(0, 2, 'D6'), (2, 2, 'Bb5'), (4, 2, 'F5'), (6, 2, 'D6'), (8, 2, 'C6'), (10, 2, 'A5'), (12, 2, 'F5'), (14, 2, 'A5')],
    [(0, 2, 'Bb5'), (2, 2, 'A5'), (4, 2, 'G5'), (6, 2, 'F5'), (8, 2, 'E5'), (10, 2, 'F5'), (12, 2, 'G5'), (14, 2, 'A5')],
    [(0, 2, 'G5'), (2, 2, 'Bb5'), (4, 2, 'D6'), (6, 2, 'C#6'), (8, 4, 'D6'), (12, 2, 'Bb5'), (14, 2, 'G5')],
    [(0, 2, 'A5'), (2, 2, 'C#6'), (4, 2, 'E6'), (6, 2, 'G6'), (8, 1, 'F6'), (9, 1, 'E6'), (10, 1, 'D6'), (11, 1, 'C#6'), (12, 1, 'Bb5'), (13, 1, 'A5'), (14, 1, 'G5'), (15, 1, 'E5')],
]
def nm(s):
    n = s[:-1].replace('Bb', 'A#').replace('Eb', 'D#'); return PC[n] + 12 * (int(s[-1]) + 1)

# chord-relative figure for interludes (creepy chromatic lower neighbours)
FIG = [[(0, 2, 3, 0), (2, 1, 2, 0), (3, 1, 3, -1), (4, 2, 3, 0), (6, 2, 4, 0), (8, 3, 5, 0), (11, 1, 4, 0), (12, 1, 3, -1), (13, 1, 3, 0), (14, 2, 1, 0)],
       [(0, 2, 4, 0), (2, 2, 3, 0), (4, 1, 2, -1), (5, 1, 2, 0), (6, 2, 1, 0), (8, 2, 2, 0), (10, 2, 3, 0), (12, 1, 5, 0), (13, 1, 4, 0), (14, 1, 3, 0), (15, 1, 3, -1)]]
def fig(bar, inst, octv=5, vel=0.85):
    ct = tones(bar, octv - 1); ct = ct + [c + 12 for c in ct]
    for s, d, i, nb in FIG[bar % 2]: add(inst, bar, s, d, ct[i] + nb, vel)

def hook(bar0, inst, vel=0.8, transp=0):
    for i in range(8):
        for s, d, n in HOOK[i]: add(inst, bar0 + i, s, d, nm(n) + transp, vel)

# ---------- per-bar writing ----------
for bar in range(NB):
    sec, k, L = sec_of(bar)
    r, q = chords[bar]
    ct4 = tones(bar, 4); ct3 = tones(bar, 3)
    root2 = 12 * 3 + r  # bass octave (C2..)
    if root2 > 45: root2 -= 12
    last = (k == L - 1)

    # ===== intro =====
    if sec == 'intro':
        if k == 0: hook(bar, 'musicbox', 0.7)
        for s in (0, 8): add('piano', bar, s, 8, ct3[0] - 12, 0.35, radio=bar < 4)
        add('piano', bar, 0, 16, ct4[0], 0.3, radio=bar < 4); add('piano', bar, 0, 16, ct4[1], 0.3, radio=bar < 4)
        if bar == 0: add('fx', bar, 0, 16 * 8, 0, 0.5, kind='vinyl')
        if bar >= 4:
            add('drums', bar, 0, 1, 'kick', 0.9)
            for s in range(0, 16, 2): add('drums', bar, s, 1, 'hat', 0.35 + 0.2 * (s % 4 == 0))
            add('bass', bar, 0, 8, root2, 0.7); add('bass', bar, 8, 6, root2 + 12, 0.6)
        if bar == 4: add('fx', bar, 0, 64, 0, 0.6, kind='riser')
        if bar == 6:
            for s in range(0, 16, 2): add('drums', bar, s, 1, 'snare', 0.3 + s / 40)
        if bar == 7:
            for s in range(0, 8): add('drums', bar, s, 1, 'snare', 0.55 + s / 20)
            add('fx', bar, 8, 8, 0, 0.7, kind='revcym'); add('fx', bar, 0, 8, 0, 1, kind='stutter', rate=2)

    # ===== verses: half-time, sparse, room for vocals =====
    elif sec in ('verse', 'verse2'):
        dense = k >= 8
        add('drums', bar, 0, 1, 'kick', 1.0); add('drums', bar, 8, 1, 'snare', 0.95)
        if k % 2 == 1: add('drums', bar, 10, 1, 'kick', 0.85)
        add('drums', bar, 6 if k % 4 != 3 else 7, 1, 'kick', 0.7)
        for s in range(0, 16, 2): add('drums', bar, s, 1, 'hat', 0.45 if s % 4 == 0 else 0.3)
        if dense:
            for s in (3, 13): add('drums', bar, s, 1, 'snare', 0.18)  # ghosts
            add('drums', bar, 14, 1, 'ohat', 0.4)
        if k % 8 == 7:
            for s in (12, 13, 14, 15): add('drums', bar, s, 1, ['tomh', 'tomh', 'toml', 'toml'][s - 12], 0.7)
        # piano offbeat stabs
        for s in (2, 6, 10, 14):
            for p in ct4: add('piano', bar, s, 1, p, 0.45 + 0.1 * dense, stac=True)
        add('piano', bar, 0, 4, ct3[0] - 12, 0.6); add('piano', bar, 0, 4, ct3[0], 0.5)
        # bass: root w/ octave hops
        for s in (0, 3, 6, 8, 11, 14): add('bass', bar, s, 2, root2 + (12 if s in (6, 14) else 0), 0.75, slide=(s == 8 and k % 2))
        if dense:
            for s in range(0, 16, 2): add('guitar', bar, s, 2, root2 + 12, 0.55, pm=True)
        if k % 4 == 3 and k > 0: fig(bar, 'bells', 6, 0.35)
        if sec == 'verse2':
            add('strings', bar, 0, 16, ct4[0], 0.25); add('strings', bar, 0, 16, ct4[2], 0.25)
            if k % 2 == 0: add('arp', bar, 0, 16, 0, 0.0)  # placeholder (no-op)
        if k == 0: add('fx', bar, 0, 1, 0, 0.8, kind='impact')

    # ===== pre-chorus: build =====
    elif sec in ('pre', 'pre2'):
        for s in (0, 4, 8, 12): add('drums', bar, s, 1, 'kick', 0.95)
        for s in (4, 12): add('drums', bar, s, 1, 'snare', 0.85)
        for s in range(2, 16, 4): add('drums', bar, s, 1, 'ohat', 0.35)
        if k >= L - 4:
            n = [4, 8, 16, 32][k - (L - 4)]
            for i in range(n):
                if k == L - 1 and i * 16 / n >= 12: break
                add('drums', bar, i * 16 / n, 16 / n, 'snare', 0.35 + 0.6 * (k - (L - 4) + i / n) / 4)
        if k == L - 4: add('fx', bar, 0, 64, 0, 0.8, kind='riser')
        # piano 16th broken chords, rising
        pat = [ct3[0], ct3[2], ct4[0], ct4[1], ct4[2], ct4[1], ct4[0], ct3[2]]
        for s in range(16): add('piano', bar, s, 1, pat[s % 8] + (12 if k >= L / 2 else 0), 0.45 + 0.4 * k / L)
        add('piano', bar, 0, 8, ct3[0] - 12, 0.7); add('piano', bar, 8, 8, ct3[0] - 12, 0.6)
        # string staccato 8ths
        for s in range(0, 16, 2):
            for p in ct4: add('strings', bar, s, 1, p, 0.4, stac=True)
        for s in range(0, 16, 2): add('bass', bar, s, 2, root2 + (12 if s % 4 == 2 else 0), 0.75)
        for s in range(0, 16, 2): add('guitar', bar, s, 2, root2 + 12, 0.6, pm=True)
        if k % 2 == 1:
            for p in ct4 + [ct4[0] + 12]: add('orch', bar, 14, 2, p, 0.6)
        if last:  # break: full stop beat 3-4 (Maretu silence)
            ev_cut = bar * 16 + 8
            for kk in ev:
                ev[kk] = [e for e in ev[kk] if not (ev_cut <= e['t'] < ev_cut + 8) or e.get('kind') == 'riser']
            for p in ct4 + [ct4[0] - 12, ct4[0] + 12]: add('orch', bar, 6, 2, p, 0.9)
            add('fx', bar, 8, 8, 0, 0.8, kind='revcym')

    # ===== choruses =====
    elif sec in ('chorus', 'chorus2', 'final'):
        hi = sec == 'final'
        # drums: full-tempo backbeat, syncopated kick
        for s in (0, 3, 6, 10) if k % 2 == 0 else (0, 3, 8, 11, 14): add('drums', bar, s, 1, 'kick', 1.0)
        for s in (4, 12): add('drums', bar, s, 1, 'snare', 1.0); add('drums', bar, s, 1, 'clap', 0.6)
        for s in range(0, 16, 2): add('drums', bar, s, 1, 'ride', 0.45)
        if k % 4 == 0: add('drums', bar, 0, 1, 'crash', 0.9)
        if k % 8 == 7 or (hi and k % 4 == 3):
            for s in range(8, 16): add('drums', bar, s, 1, 'kick', 0.8)  # double-kick burst
            for s in range(8, 16, 1): add('drums', bar, s, 1, ['snare', 'tomh', 'tomm', 'toml'][(s // 2) % 4], 0.7)
        if hi and k < 4:
            for s in range(16): add('drums', bar, s, 1, 'kick', 0.85)  # blast
            for s in range(0, 16, 2): add('drums', bar, s, 1, 'snare', 0.7)
        # piano: 16th arpeggio runs over 2 octaves
        up = [ct3[0], ct3[1], ct3[2], ct4[0], ct4[1], ct4[2], ct4[0] + 12, ct4[1] + 12]
        run = up + up[::-1] if k % 2 == 0 else up[::-1] + up
        for s in range(16): add('piano', bar, s, 1, run[s] + (12 if hi else 0), 0.55 + 0.1 * (s % 4 == 0))
        for s in range(0, 16, 2): add('piano', bar, s, 2, ct3[0] - 12, 0.6); add('piano', bar, s, 2, ct3[0] - 24, 0.4)
        # guitar power chords: sustained + chugs
        if k % 2 == 0: add('guitar', bar, 0, 6, root2 + 12, 0.85)
        for s in (6, 8, 10, 11, 12, 14): add('guitar', bar, s, 1 if s in (10, 11) else 2, root2 + 12, 0.7, pm=s in (10, 11))
        # bass driving 8ths with slides
        for s in range(0, 16, 2): add('bass', bar, s, 2, root2 + (12 if s in (6, 14) else 0), 0.85, slide=(s == 0 and k % 4 == 0))
        # gated square arp
        a = [ct4[0] + 12, ct4[2] + 12, ct4[1] + 12, ct4[2] + 12]
        for s in range(16): add('arp', bar, s, 1, a[s % 4] + (12 if s % 8 >= 6 else 0), 0.5)
        # pads
        for p in ct4 + [ct4[0] + 12]: add('strings', bar, 0, 16, p, 0.4 + 0.1 * hi)
        if hi or sec == 'chorus2':
            for p in ct4: add('choir', bar, 0, 16, p, 0.4)
        if k % 2 == 0:
            for p in ct3 + ct4: add('orch', bar, 0, 2, p, 0.75)
        if k % 8 == 6: fig(bar, 'bells', 6, 0.4); fig(bar + 1, 'bells', 6, 0.4)
        if k == 0: add('fx', bar, 0, 1, 0, 1.0, kind='impact')
        if hi and k in (4, 8): hook(bar, 'lead', 0.0)  # placeholder (no-op)
        if hi and k == L - 1: add('fx', bar, 8, 8, 0, 1, kind='stutter', rate=4)
        if sec == 'chorus' and k == L - 1: add('fx', bar, 12, 4, 0, 1, kind='stutter', rate=8)

    # ===== interlude: glitch hook =====
    elif sec == 'inter':
        fig(bar, 'piano', 5, 0.9); fig(bar, 'piano', 4, 0.6)
        fig(bar, 'bells', 6, 0.5)
        if k < 4: fig(bar, 'lead', 5, 0.7)
        for s in (0, 6, 10): add('drums', bar, s, 1, 'kick', 1)
        add('drums', bar, 8, 1, 'snare', 1)
        for s in range(16): add('drums', bar, s, 1, 'hat', 0.25 + 0.2 * (s % 2 == 0))
        for s in range(0, 16, 4): add('bass', bar, s, 3, root2, 0.85, slide=True)
        add('guitar', bar, 0, 8, root2 + 12, 0.8); add('guitar', bar, 8, 8, root2 + 13 if k % 2 else root2 + 12, 0.8)
        add('fx', bar, 0, 16, 0, 1, kind='crush', amt=0.3 + 0.08 * k)
        if k % 2 == 1: add('fx', bar, 12, 4, 0, 1, kind='stutter', rate=8)
        if last:
            add('fx', bar, 8, 8, 0, 1, kind='tapestop')
            # chromatic falling run
            for i, s in enumerate(range(0, 8)): add('piano', bar, s, 1, 86 - i, 0.8)

    # ===== bridge: piano solo + choir, then build =====
    elif sec == 'bridge':
        if k < 6:
            for s in range(0, 16, 2): add('piano', bar, s, 2, [ct3[0], ct3[2], ct4[1], ct4[2], ct4[0] + 12, ct4[2], ct4[1], ct3[2]][s // 2], 0.5)
            add('piano', bar, 0, 16, ct3[0] - 12, 0.5)
            for p in ct4: add('choir', bar, 0, 16, p, 0.45)
            fig(bar, 'musicbox', 6, 0.5)
            add('bass', bar, 0, 16, root2, 0.4)
            if k == 0: add('fx', bar, 0, 1, 0, 0.8, kind='impact'); add('fx', bar, 0, 16 * 6, 0, 0.35, kind='vinyl')
        else:
            n = [4, 8, 8, 16][k - 6]
            for s in np.arange(0, 16, 16 / n): add('drums', bar, s, 1, 'tomm' if k < 8 else 'snare', 0.5 + 0.12 * (k - 6))
            for s in (0, 4, 8, 12): add('drums', bar, s, 1, 'kick', 0.9)
            for s in range(16): add('piano', bar, s, 1, ct4[s % 3] + 12 * (s // 6 % 2), 0.55 + 0.08 * (k - 6))
            for p in ct4: add('strings', bar, 0, 16, p, 0.45); add('choir', bar, 0, 16, p, 0.4)
            for s in range(0, 16, 2): add('bass', bar, s, 2, root2, 0.8)
            for s in range(0, 16, 2): add('guitar', bar, s, 2, root2 + 12, 0.6, pm=True)
            if k == 6: add('fx', bar, 0, 64, 0, 0.9, kind='riser')
            if last:
                ev_cut = bar * 16 + 12
                for kk in ev: ev[kk] = [e for e in ev[kk] if not (ev_cut <= e['t'] < ev_cut + 4) or e.get('kind') == 'riser']
                add('fx', bar, 12, 4, 0, 0.9, kind='revcym')

    # ===== end =====
    elif sec == 'end':
        if k == 0:
            for p in ct3 + ct4 + [ct4[0] + 12]: add('orch', bar, 0, 4, p, 1.0)
            add('drums', bar, 0, 1, 'crash', 1); add('drums', bar, 0, 1, 'kick', 1)
            add('fx', bar, 0, 1, 0, 1, kind='impact')
            add('piano', bar, 0, 16, ct3[0] - 24, 0.8); add('piano', bar, 0, 16, ct3[0] - 12, 0.8)
            add('fx', bar, 4, 12, 0, 1, kind='tapestop')
        for s, d, n in HOOK[0][:5] if k == 1 else []: add('musicbox', bar, s, d, nm(n), 0.6)

# drop placeholders
for kk in ev: ev[kk] = [e for e in ev[kk] if e['v'] > 0]
# final-chorus hook on lead for vocal-free stretch at end
hook(142, 'lead', 0.0)
for kk in ev: ev[kk] = [e for e in ev[kk] if e['v'] > 0]
json.dump({'bpm': BPM, 'bars': NB, 'chords': [NAMES[r] + q for r, q in chords], 'sections': SEC, 'events': ev}, open(out, 'w'))
print('bpm', BPM, {k: len(v) for k, v in ev.items()})
