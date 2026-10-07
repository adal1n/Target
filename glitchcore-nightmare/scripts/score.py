import json, sys, numpy as np, pretty_midi
from music21 import percussion, expressions, stream, note, chord, meter, tempo, key, instrument, clef, metadata, analysis, pitch as m21p
d = json.load(open(sys.argv[1])); out = sys.argv[2]
bt = np.array(d['beats']); bpm = round(60 * (len(bt) - 1) / (bt[-1] - bt[0]), 1)
P = d['parts']
STEP = 0.25  # 16th in quarterLength

# key from pitched parts
ks = stream.Stream()
for n in P['vocals'] + P['bass'] + P['other']:
    ks.append(note.Note(n[2], quarterLength=(n[1] - n[0]) * STEP))
k = ks.analyze('key')
print('key', k, 'bpm', bpm)

def pitched_part(name, inst, notes, clf):
    p = stream.Part(id=name); p.partName = name.capitalize()
    p.insert(0, inst); p.insert(0, clf); p.insert(0, k); p.insert(0, meter.TimeSignature('4/4'))
    groups = {}
    for s, e, pi, a in notes: groups.setdefault(s, []).append((e, pi))
    keys = sorted(groups)
    for i, s in enumerate(keys):
        g = groups[s]
        ql = min(e for e, _ in g) - s
        if i + 1 < len(keys): ql = min(ql, keys[i + 1] - s)  # no overlaps
        el = note.Note(g[0][1]) if len(g) == 1 else chord.Chord(sorted({pi for _, pi in g}))
        el.quarterLength = max(1, ql) * STEP
        p.insert(s * STEP, el)
    p.makeRests(fillGaps=True, inPlace=True)
    return p

def drum_part(hits):
    p = stream.Part(id='drums'); p.partName = 'Drums'
    p.insert(0, instrument.UnpitchedPercussion()); p.insert(0, clef.PercussionClef()); p.insert(0, meter.TimeSignature('4/4'))
    disp = {'kick': 'F4', 'snare': 'C5', 'hihat': 'G5'}
    by = {}
    for s, e, n, a in hits: by.setdefault(s, set()).add(n)
    for s in sorted(by):
        ns = []
        for n in sorted(by[s]):
            u = note.Unpitched(displayName=disp[n]);
            if n == 'hihat': u.notehead = 'x'
            ns.append(u)
        el = ns[0] if len(ns) == 1 else percussion.PercussionChord(ns)
        el.quarterLength = STEP
        p.insert(s * STEP, el)
    p.makeRests(fillGaps=True, inPlace=True)
    return p

sc = stream.Score()
sc.insert(0, metadata.Metadata(title='Glitchcore Nightmare', composer='Transcribed by Claude (auto)'))
parts = [
    pitched_part('vocals', instrument.Vocalist(), P['vocals'], clef.TrebleClef()),
    pitched_part('other', instrument.ElectricPiano(), P['other'], clef.TrebleClef()),
    pitched_part('bass', instrument.ElectricBass(), P['bass'], clef.BassClef()),
    drum_part(P['drums']),
]
parts[1].partName = 'Synth'; parts[1].partAbbreviation = 'Syn'; parts[0].partAbbreviation = 'Vo'; parts[2].partName = 'Bass'; parts[2].partAbbreviation = 'Bs'; parts[3].partAbbreviation = 'Dr'
parts[0].insert(0, expressions.TextExpression(f'Tempo ≈ {bpm:.0f} BPM'))
for p in parts: sc.insert(0, p)
sc = sc.makeNotation()
sc.write('musicxml', fp=f'{out}/score.musicxml')

# MIDI at constant tempo
pm = pretty_midi.PrettyMIDI(initial_tempo=bpm)
sec = 60 / bpm / 4
progs = {'vocals': 54, 'other': 81, 'bass': 38}
for name, prog in progs.items():
    ins = pretty_midi.Instrument(program=prog, name=name)
    for s, e, pi, a in P[name]:
        ins.notes.append(pretty_midi.Note(velocity=int(np.clip(40 + a * 100, 40, 120)), pitch=pi, start=s * sec, end=e * sec))
    pm.instruments.append(ins)
dr = pretty_midi.Instrument(program=0, is_drum=True, name='drums')
gm = {'kick': 36, 'snare': 38, 'hihat': 42}
for s, e, n, a in P['drums']:
    dr.notes.append(pretty_midi.Note(velocity=100, pitch=gm[n], start=s * sec, end=s * sec + 0.1))
pm.instruments.append(dr)
pm.write(f'{out}/score.mid')
json.dump({'bpm': bpm, 'key': str(k)}, open(f'{out}/info.json', 'w'))
