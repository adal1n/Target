import sys, numpy as np, librosa, soundfile as sf
src, out = sys.argv[1], sys.argv[2]
y, sr = librosa.load(src, sr=44100, mono=False)
N, H = 4096, 1024
S = np.stack([librosa.stft(c, n_fft=N, hop_length=H) for c in y])  # (2,F,T)
mag = np.abs(S).mean(0)
freqs = librosa.fft_frequencies(sr=sr, n_fft=N)

# drums vs harmonic (HPSS soft masks)
Hm, Pm = librosa.decompose.hpss(mag, kernel_size=(31, 31), power=2.0, mask=True, margin=(1.0, 2.0))
Pm = Pm ** 1.0
harm = mag * (1 - Pm)

# vocals: REPET-SIM on harmonic part + center-channel weighting
filt = librosa.decompose.nn_filter(harm, aggregate=np.median, metric='cosine',
                                   width=int(librosa.time_to_frames(2, sr=sr, hop_length=H)))
filt = np.minimum(harm, filt)
mv = librosa.util.softmask(harm - filt, 10 * filt, power=2)
L, R = np.abs(S[0]), np.abs(S[1])
center = 1 - np.abs(L - R) / (L + R + 1e-9)
band = ((freqs > 150) & (freqs < 8000)).astype(float)[:, None]
mv = mv * center ** 2 * band
# rest of harmonic
mrest = (1 - Pm) * (1 - mv)
lowcut = 1 / (1 + (freqs / 220.0) ** 8)  # bass lowpass
mb = mrest * lowcut[:, None]
mo = mrest * (1 - lowcut[:, None])
md = Pm * (1 - mv)
masks = {'vocals': mv, 'drums': md, 'bass': mb, 'other': mo}
for k, m in masks.items():
    st = np.stack([librosa.istft(S[c] * m, hop_length=H, length=y.shape[1]) for c in range(2)])
    sf.write(f'{out}/{k}.wav', st.T, sr)
    print(k, float(np.sqrt((st ** 2).mean())))
