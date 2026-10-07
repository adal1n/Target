import json, sys, numpy as np, pretty_midi
from music21 import stream, note, chord, meter, key, instrument, clef, metadata, expressions, harmony, percussion, tempo
A = json.load(open(sys.argv[1])); out = sys.argv[2]
BPM = A['bpm']; ST = 60 / BPM / 4; E = A['events']

# ---- MIDI ----
pm = pretty_midi.PrettyMIDI(initial_tempo=BPM)
PROG = {'piano': 0, 'musicbox': 10, 'bells': 9, 'guitar': 30, 'bass': 38, 'arp': 80, 'strings': 48, 'choir': 52, 'orch': 55, 'lead': 81}
GM = {'kick': 36, 'snare': 38, 'clap': 39, 'hat': 42, 'ohat': 46, 'ride': 51, 'crash': 49, 'tomh': 50, 'tomm': 47, 'toml': 43}
for k, prog in PROG.items():
    ins = pretty_midi.Instrument(program=prog, name=k)
    for e in E[k]:
        ps = [e['p'], e['p'] + 7, e['p'] + 12] if k == 'guitar' else [e['p']]
        d = (0.12 / ST if e.get('stac') else e['d'])
        for p in ps: ins.notes.append(pretty_midi.Note(int(np.clip(e['v'] * 127, 1, 127)), int(p), e['t'] * ST, (e['t'] + d) * ST))
    pm.instruments.append(ins)
dr = pretty_midi.Instrument(0, is_drum=True, name='drums')
for e in E['drums']: dr.notes.append(pretty_midi.Note(int(np.clip(e['v'] * 127, 1, 127)), GM[e['p']], e['t'] * ST, e['t'] * ST + 0.08))
pm.instruments.append(dr)
# section markers
for n, a, b in A['sections']: pm.lyrics.append(pretty_midi.Lyric(n, a * 16 * ST))
pm.write(f'{out}/arrangement.mid')

# ---- score ----
Q = 0.25
k = key.Key('d')
def mk(name, abbr, inst, clf, evs, poly=True, xform=None):
    p = stream.Part(id=name); p.partName = name; p.partAbbreviation = abbr
    p.insert(0, inst); p.insert(0, clf); p.insert(0, k); p.insert(0, meter.TimeSignature('4/4'))
    g = {}
    for e in evs:
        for pi in (xform(e) if xform else [e['p']]): g.setdefault(e['t'], []).append((e['d'] if not e.get('stac') else 1, pi))
    ts = sorted(g)
    for i, t in enumerate(ts):
        d = min(dd for dd, _ in g[t])
        if i + 1 < len(ts): d = min(d, ts[i + 1] - t)
        d = max(d, 0.5); ps = sorted({pi for _, pi in g[t]})
        el = note.Note(ps[0]) if len(ps) == 1 else chord.Chord(ps)
        el.quarterLength = d * Q; p.insert(t * Q, el)
    p.makeRests(fillGaps=True, inPlace=True)
    return p
top = [e for kk in ('musicbox', 'bells', 'lead') for e in E[kk]]
parts = [
    mk('Hook (Music box / Bells / Lead)', 'Hk', instrument.Glockenspiel(), clef.Treble8vaClef(), top),
    mk('Piano RH', 'Pf', instrument.Piano(), clef.TrebleClef(), [e for e in E['piano'] if e['p'] >= 60]),
    mk('Piano LH', 'Pf', instrument.Piano(), clef.BassClef(), [e for e in E['piano'] if e['p'] < 60]),
    mk('Dist. Guitar', 'Gt', instrument.ElectricGuitar(), clef.Treble8vbClef(), E['guitar'], xform=lambda e: [e['p'] + 12, e['p'] + 19, e['p'] + 24]),
    mk('Strings', 'Str', instrument.StringInstrument(), clef.TrebleClef(), E['strings']),
    mk('Bass', 'Bs', instrument.ElectricBass(), clef.BassClef(), E['bass'], xform=lambda e: [e['p'] + 12]),
]
dp = stream.Part(id='drums'); dp.partName = 'Drums'; dp.partAbbreviation = 'Dr'
dp.insert(0, instrument.UnpitchedPercussion()); dp.insert(0, clef.PercussionClef()); dp.insert(0, meter.TimeSignature('4/4'))
DISP = {'kick': 'F4', 'snare': 'C5', 'clap': 'C5', 'hat': 'G5', 'ohat': 'G5', 'ride': 'F5', 'crash': 'A5', 'tomh': 'E5', 'tomm': 'D5', 'toml': 'A4'}
g = {}
for e in E['drums']: g.setdefault(e['t'], set()).add(e['p'])
ts = sorted(g)
for i, t in enumerate(ts):
    d = min(4, ts[i + 1] - t) if i + 1 < len(ts) else 1
    us = []
    for nmn in sorted(g[t] - ({'clap'} if 'snare' in g[t] else set())):
        u = note.Unpitched(displayName=DISP[nmn])
        if nmn in ('hat', 'ohat', 'ride', 'crash'): u.notehead = 'x'
        us.append(u)
    el = us[0] if len(us) == 1 else percussion.PercussionChord(us)
    el.quarterLength = d * Q; dp.insert(t * Q, el)
dp.makeRests(fillGaps=True, inPlace=True)
parts.append(dp)
LBL = {'intro': 'Intro', 'verse': 'A (Verse 1)', 'pre': 'B (Pre)', 'chorus': 'Chorus 1', 'inter': 'Interlude', 'verse2': 'A2 (Verse 2)',
       'pre2': 'B2 (Pre)', 'chorus2': 'Chorus 2', 'bridge': 'C (Bridge)', 'final': 'Last Chorus', 'end': 'End'}
for n, a, b in A['sections']: parts[0].insert(a * 4, expressions.RehearsalMark(LBL[n]))
prev = None
for i, c in enumerate(A['chords']):
    if c != prev: parts[0].insert(i * 4, expressions.TextExpression(c))
    prev = c
parts[0].insert(0, expressions.TextExpression(f'♩ = {BPM}  (Maretu-style arr.)'))
sc = stream.Score()
sc.insert(0, metadata.Metadata(title='Glitchcore Nightmare (Maretu-style Arrangement)', composer='Arr. Claude'))
for p in parts: sc.insert(0, p)
sc.makeNotation(inPlace=True)
sc.write('musicxml', fp=f'{out}/arrangement.musicxml')
print('ok')
