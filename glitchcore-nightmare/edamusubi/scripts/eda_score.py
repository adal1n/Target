import json, sys
from music21 import stream, note, meter, key, instrument, clef, metadata, expressions
V = json.load(open(sys.argv[1])); A = json.load(open(sys.argv[2])); out = sys.argv[3]
Q = 0.25
p = stream.Part(id='teto'); p.partName = 'Kasane Teto'
p.insert(0, instrument.Vocalist()); p.insert(0, clef.TrebleClef()); p.insert(0, key.Key('d')); p.insert(0, meter.TimeSignature('4/4'))
ns = V['notes']
for i, (st, du, m, mo, kind) in enumerate(ns):
    if i + 1 < len(ns): du = min(du, ns[i + 1][0] - st)
    if mo == 'っ': continue
    n = note.Note(m, quarterLength=du * Q); n.lyric = mo
    if n.pitch.accidental is not None and n.pitch.accidental.name == 'natural': n.pitch.accidental = None
    if kind == 'shout': n.notehead = 'x'
    p.insert(st * Q, n)
LBL = {'intro': 'Intro', 'verse': 'A', 'pre': 'B', 'chorus': 'サビ', 'inter': 'Interlude', 'verse2': 'A2', 'pre2': 'B2',
       'chorus2': 'サビ2', 'bridge': 'C', 'final': 'ラスサビ', 'end': 'End'}
for nm, a, b in A['sections']: p.insert(a * 4, expressions.RehearsalMark(LBL[nm]))
prev = None
for i, c in enumerate(A['chords']):
    if c != prev: p.insert(i * 4, expressions.TextExpression(c))
    prev = c
for bar, txt in [(0, '[SE] 風・縄の軋み'), (46, 'SHOUT'), (64, 'SHOUT'), (110, 'SHOUT'), (128, 'whisper / 心音'), (134, 'SHOUT'), (137, '[SE] 枝が折れる'), (151, '[SE] 軋み')]:
    p.insert(bar * 4 + (3 if bar == 137 else 0), expressions.TextExpression(txt))
p.makeRests(fillGaps=True, inPlace=True)
sc = stream.Score(); sc.insert(0, metadata.Metadata(title='えだむすび', composer='feat. 重音テト'))
sc.insert(0, p); sc.makeNotation(inPlace=True)
sc.write('musicxml', fp=f'{out}/edamusubi_vocal.musicxml')
