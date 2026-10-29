"""Build an SFX bed under the finished narration and mix it (voice untouched).

Timing = word cues (the scenes are keyed to them) snapped to measured on-screen
motion from the rendered video. Output: mix.wav (48 kHz stereo float) + cue_sheet.csv
"""
import csv, json, re, glob, os
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

R = 48000
FPS = 30
rng = np.random.default_rng(7)

# ---------------------------------------------------------------- inputs
voice = np.fromfile('voice.f32', np.float32).astype(np.float64)   # mono, the video's audio
voice = np.pad(voice, (0, int(468.933 * 48000) - len(voice)))       # to full video length (end-screen hold)
N = len(voice)
mot = np.load('motion.npy')[0]                                     # per-frame motion energy
cues = json.load(open('cues.json'))                                # [start, end, text] per word

def cue_t(n):  # 1-based like cues.py
    return cues[n - 1][0]

T = {}
for f in sorted(glob.glob('proj/scenes/ch*_*.py')):
    ch = int(re.search(r'ch(\d)', f).group(1))
    for name, n in re.findall(r'"(\w+)":\s*cue\((\d+)\)', open(f).read()):
        T[(ch, name)] = cue_t(int(n))

def word(text, after):
    t = re.sub(r'[^a-z0-9]', '', text.lower())
    for s, e, w in cues:
        if s >= after - 1e-6 and re.sub(r'[^a-z0-9]', '', w.lower()) == t:
            return s
    raise KeyError(text)

# ---------------------------------------------------------------- sound library
def load_f32(name):
    return np.fromfile(f'wav/{name}.f32', np.float32).astype(np.float64)

MIX = {os.path.basename(p).split('_')[2]: os.path.basename(p)[:-4]
       for p in glob.glob('wav/mixkit_*.f32')}

def trim(x, db=-50):
    env = np.abs(x)
    thr = env.max() * 10 ** (db / 20)
    idx = np.where(env > thr)[0]
    x = x[max(0, idx[0] - 48): idx[-1] + 1]
    fade = min(len(x) // 4, int(0.03 * R))
    x[-fade:] *= np.linspace(1, 0, fade)
    return x / (np.abs(x).max() + 1e-12)

def mk(i, maxlen=None):
    x = trim(load_f32(MIX[str(i)]))
    if maxlen:
        n = int(maxlen * R)
        if len(x) > n:
            f = int(0.25 * R)
            x = x[:n].copy(); x[-f:] *= np.linspace(1, 0, f) ** 2
    return x

def kn(pack, name):
    return trim(load_f32(f'k_{pack}_{name}'))

def peak_time(x):
    hop = 240
    e = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, 'same'))
    return int(np.argmax(e))

def resample(x, rate):  # pitch shift by playback rate
    n = int(len(x) / rate)
    return np.interp(np.arange(n) * rate, np.arange(len(x)), x)

# ---- synthesized clap + cathedral impulse response (convolution, on theme)
def cathedral_clap(rt60=3.6):
    n = int(0.05 * R)
    clap = np.zeros(n)
    for k, (dt, a) in enumerate([(0, 1.0), (0.006, 0.7), (0.012, 0.85), (0.019, 0.6)]):
        s = int(dt * R); L = int(0.012 * R)
        clap[s:s + L] += a * rng.standard_normal(L) * np.exp(-np.arange(L) / (0.0025 * R))
    clap = sosfilt(butter(2, [700, 4500], 'band', fs=R, output='sos'), clap)
    L = int(rt60 * 1.3 * R)
    t = np.arange(L) / R
    ir = rng.standard_normal(L) * np.exp(-6.91 * t / rt60)
    ir = sosfilt(butter(1, 3500, 'low', fs=R, output='sos'), ir)          # stone absorbs highs
    ir[:int(0.045 * R)] = 0                                               # pre-delay
    for d, g in [(0.023, 0.5), (0.037, 0.35), (0.061, 0.3), (0.089, 0.22), (0.13, 0.15)]:
        ir[int(d * R)] += g * 40                                          # early reflections
    wet = fftconvolve(clap, ir)
    wet /= np.abs(wet).max()
    out = np.zeros(len(wet)); out[:n] += clap / np.abs(clap).max()
    out += 0.55 * wet
    return out / np.abs(out).max()

LIB = {
    'clap':      cathedral_clap(),
    'boom':      mk(1143),                        # Cinematic whoosh deep impact
    'hit':       mk(2903, 2.2),                   # Movie whoosh impact presentation
    'riser':     mk(790),                         # Cinematic trailer riser
    'trans':     mk(1489),                        # Air woosh
    'whoosh':    mk(168),                         # Fast air sweep transition
    'swish':     mk(1464),                        # Quick swoosh accent (slide steps)
    'swish2':    mk(175),                         # Short transition sweep
    'slide':     mk(2632),                        # Whoosh wind sweep (long slide)
    'flip':      mk(3115),                        # Fast transitions swoosh
    'pop':       mk(2356),                        # Dry pop up notification
    'pop2':      mk(3005),                        # Explainer video light pop
    'click':     kn('interface-sounds', 'select_006'),
    'tick':      kn('interface-sounds', 'pluck_002'),
    'drop':      kn('interface-sounds', 'drop_002'),
    'chime':     kn('interface-sounds', 'confirmation_002'),
    'glass':     kn('interface-sounds', 'glass_001'),
    'sparkle':   mk(3083),                        # Magic sparkle touch
    'shine':     mk(2633, 1.5),                   # Sweeping sparkle presentation intro
    'down':      kn('digital-audio', 'phaserDown1'),
    'bell':      mk(619, 3.5),                    # Cinematic church bell hit
}
# per-type: (gain dB, align: 'onset'|'peak', snap window)
TYPE = {
    'clap': (-6, 'onset'), 'boom': (-17, 'onset'), 'hit': (-21, 'peak'), 'riser': (-24, 'end'),
    'trans': (-22, 'peak'), 'whoosh': (-23, 'peak'), 'swish': (-22, 'peak'), 'swish2': (-27, 'peak'),
    'slide': (-25, 'peak'), 'flip': (-25, 'peak'), 'pop': (-24, 'onset'), 'pop2': (-24, 'onset'),
    'click': (-25, 'onset'), 'tick': (-25, 'onset'), 'drop': (-22, 'onset'), 'chime': (-26, 'onset'),
    'glass': (-25, 'onset'), 'sparkle': (-27, 'onset'), 'shine': (-26, 'peak'), 'down': (-30, 'onset'),
    'bell': (-30, 'onset'),
}

# ---------------------------------------------------------------- motion snapping
def snap(t, before=0.15, after=0.6):
    """Earliest motion onset near t (seconds), else t."""
    a, b = int((t - before) * FPS), int((t + after) * FPS)
    a = max(a, 8); b = min(b, len(mot) - 1)
    for i in range(a, b):
        base = np.median(mot[i - 8:i - 1])
        if mot[i] > 0.12 and mot[i] > 2.2 * base + 0.06:
            return i / FPS
    return t

def snap_peak(t, before=0.1, after=0.9):
    a, b = int((t - before) * FPS), int((t + after) * FPS)
    w = mot[a:b]
    if len(w) and w.max() > 0.25:
        return (a + int(np.argmax(w))) / FPS
    return t + 0.25

# ---------------------------------------------------------------- the cue sheet
E = []  # (time, type, extra dict, note)
def ev(t, typ, note='', snapmode='auto', **kw):
    E.append(dict(t=t, typ=typ, note=note, snap=snapmode, **kw))

C = lambda ch, n: T[(ch, n)]

# ===== Chapter 0 - cold open
ev(0.53, 'clap', 'clap in the cathedral', snapmode='onset_fixed')
ev(0.53, 'boom', 'flash / camera kick', snapmode='onset_fixed', gain=-3)
ev(C(0, 'play'), 'trans', 'song streams in', gain=-4)
ev(C(0, 'conv') - 0.02, 'riser', 'build to the name', snapmode='none')
ev(C(0, 'conv'), 'hit', 'CONVOLUTION title')
for k in ('blurs', 'neural', 'dice', 'long'):
    ev(C(0, k), 'whoosh', f'panel flips in: {k}')
    ev(C(0, k) + 0.25, 'pop2', f'panel lands: {k}', gain=-4, snapmode='none')
for i, k in enumerate(('flip', 'slide', 'multiply', 'add')):
    ev(C(0, k), 'pop', f'recipe pill {k.upper()}', rate=1 + 0.06 * i)
ev(40.03, 'slide', 'box slides over box')
ev(C(0, 'fourier'), 'shine', 'Fourier teaser')
ev(word('multiplication', 48), 'chime', 'single multiplication')
# ===== Chapter 1 - sliding by hand
ev(C(1, 'hand'), 'trans', 'chapter 1 in')
for i, k in enumerate(('v0', 'v1', 'v2', 'v3')):
    ev(C(1, k), 'tick', f'temperature {i + 1}', rate=1 + 0.05 * i)
ev(C(1, 'three'), 'pop', 'window appears')
ev(C(1, 'add'), 'click', 'window sum')
for t in (67.47, 68.57, 69.17, 69.57):
    ev(t, 'swish', 'window slides a day', snapmode='peak')
ev(C(1, 'kernel'), 'glass', 'KERNEL label')
for i, k in enumerate(('s1', 's2', 's3')):
    ev(C(1, k), 'pop', f'signal tile {i + 1}', rate=1 + 0.06 * i)
for i, k in enumerate(('k1', 'k2')):
    ev(C(1, k), 'pop', f'kernel tile {i + 1}', rate=0.9 + 0.06 * i)
ev(C(1, 'flip'), 'flip', 'kernel flips')
ev(C(1, 'slide_in'), 'slide', 'kernel slides in')
for k, g in (('first', 'p0g'), ('slide2', 'p1g'), ('slide3', 'p2g'), ('last', 'p3g')):
    if k != 'first':
        ev(C(1, k), 'swish', f'slide step ({k})')
    ev(C(1, g), 'drop', f'output tile ({g})')
for i, k in enumerate(('a0', 'a1', 'a2', 'a3')):
    ev(C(1, k), 'tick', f'answer digit {i + 1}', rate=1 + 0.06 * i)
ev(C(1, 'mult'), 'whoosh', '123 x 11 appears')
for i, k in enumerate(('d0', 'd1', 'd2', 'd3')):
    ev(C(1, k), 'tick', f'product digit {i + 1}', rate=1 + 0.06 * i)
ev(C(1, 'same'), 'sparkle', 'the same digits!')
ev(C(1, 'why'), 'trans', 'why flip? scene')
ev(C(1, 'instant'), 'glass', 'echo now', gain=0)
ev(C(1, 'quieter'), 'glass', 'quieter copy', gain=-5, rate=0.94)
ev(C(1, 'fainter'), 'glass', 'fainter copy', gain=-10, rate=0.88)
ev(C(1, 'flip2'), 'flip', 'the flip lines up past')
# ===== Chapter 2 - dice
ev(C(2, 'dice'), 'trans', 'chapter 2 in')
ev(C(2, 'six_bars'), 'pop', 'six equal bars')
ev(C(2, 'roll'), 'whoosh', 'two dice')
ev(C(2, 'seven'), 'glass', 'seven: six ways')
ev(C(2, 'flip'), 'flip', 'flip one row')
ev(C(2, 'slide'), 'slide', 'slide across')
ev(C(2, 'grows'), 'swish2', 'overlap grows')
ev(C(2, 'seven2'), 'chime', 'all six line up')
ev(C(2, 'shrinks'), 'swish2', 'overlap shrinks')
ev(C(2, 'triangle'), 'sparkle', 'flat -> triangle')
ev(C(2, 'convolve'), 'whoosh', 'third die')
ev(C(2, 'hill'), 'pop', 'hill')
ev(C(2, 'bell'), 'shine', 'bell curve')
# ===== Chapter 3 - smooth shapes
ev(C(3, 'smooth_w'), 'trans', 'chapter 3 in')
ev(207.60, 'whoosh', 'bars melt into curves', snapmode='peak')
for k, r in (('f1', 1.0), ('int', 1.05), ('dtau', 1.1)):
    ev(C(3, k), 'click', f'formula {k}', rate=r)
ev(C(3, 'flipped'), 'flip', 'g flipped')
ev(C(3, 'slid'), 'swish', 'slid to t')
ev(C(3, 'multiply'), 'pop', 'multiply point by point')
ev(C(3, 'area'), 'glass', 'area of overlap')
for i, k in enumerate(('flip', 'slide', 'measure')):
    ev(C(3, k), 'pop', f'summary {k}', rate=1 + 0.06 * i)
ev(C(3, 'boxes'), 'pop2', 'two boxes')
ev(C(3, 'slide3'), 'slide', 'box slides in')
ev(C(3, 'peaks'), 'chime', 'peaks at one')
ev(C(3, 'shrinks'), 'swish2', 'shrinks to zero')
ev(C(3, 'triangle'), 'sparkle', 'boxes -> triangle')
# ===== Chapter 4 - images
ev(267.87, 'trans', 'step into 2D', snapmode='peak', gain=2)
ev(C(4, 'small_grid'), 'whoosh', '3x3 kernel')
ev(C(4, 'place'), 'drop', 'kernel placed')
ev(C(4, 'nine'), 'click', 'add all nine')
ev(C(4, 'write'), 'pop', 'write into new image')
ev(C(4, 'slide'), 'swish', 'slide one pixel')
ev(C(4, 'ninth'), 'pop', '1/9 kernel')
ev(C(4, 'blurs'), 'shine', 'image blurs')
ev(293.23, 'whoosh', 'edge kernel scene', snapmode='peak')
for i, k in enumerate(('minus', 'zero', 'plus')):
    ev(C(4, k), 'tick', f'column {k}', rate=1 + 0.07 * i)
ev(C(4, 'lights'), 'glass', 'kernel lights up')
ev(C(4, 'detector'), 'chime', 'edge detector')
ev(C(4, 'cnn'), 'trans', 'CNN')
ev(C(4, 'learn'), 'whoosh', 'learned filters')
ev(C(4, 'edge2'), 'sparkle', 'they discover edges')
# ===== Chapter 5 - Fourier
ev(C(5, 'problem'), 'boom', 'one problem', gain=-4)
ev(C(5, 'trillion') - 0.02, 'riser', 'build to a trillion', snapmode='none', gain=-2)
ev(C(5, 'trillion'), 'hit', 'a trillion multiplications')
ev(C(5, 'rescue'), 'shine', 'Fourier to the rescue')
ev(C(5, 'cathedral'), 'bell', 'pure tone in the cathedral')
ev(C(5, 'split'), 'whoosh', 'split into frequencies')
ev(358.77, 'swish', 'put back together', snapmode='peak')
ev(C(5, 'theorem'), 'trans', 'convolution theorem')
for k, r in (('F1', 1.0), ('equals', 1.05), ('times', 1.1)):
    ev(C(5, k), 'click', f'theorem {k}', rate=r)
ev(368.33, 'pop', 'theorem complete', snapmode='peak')
ev(C(5, 'multiplication'), 'chime', 'time -> multiplication')
ev(C(5, 'with_fft'), 'whoosh', 'FFT')
ev(C(5, 'drops'), 'down', 'trillion drops')
ev(C(5, 'million3'), 'pop', 'a hundred million')
ev(C(5, 'clap') + 0.30, 'clap', 'recorded clap', gain=-12, snapmode='none')
ev(C(5, 'sounds'), 'trans', 'song inside cathedral', gain=-3)
ev(C(5, 'laplace'), 'pop', 'Laplace')
ev(C(5, 'z'), 'pop', 'Z transform', rate=1.06)
ev(C(5, 'transfer'), 'click', 'transfer function')
ev(C(5, 'theorem2'), 'chime', 'convolution theorem at work')
# ===== Chapter 6 - recap
ev(C(6, 'discovered'), 'trans', 'recap in')
for i, k in enumerate(('flip', 'slide', 'multiply', 'add')):
    ev(C(6, k), 'pop', f'recap pill {k}', rate=1 + 0.06 * i)
for k in ('numbers', 'dice', 'curves', 'images', 'fourier'):
    ev(C(6, k), 'swish', f'recap card {k}')
ev(C(6, 'collapses'), 'whoosh', 'collapses')
ev(C(6, 'single'), 'chime', 'single multiplication')
ev(C(6, 'echo'), 'glass', 'echo', gain=-2)
ev(C(6, 'blurry'), 'tick', 'blurry photo')
ev(C(6, 'dice2'), 'tick', 'dice', rate=1.06)
ev(C(6, 'subscribe'), 'pop2', 'subscribe')
ev(C(6, 'one'), 'shine', 'end card', gain=-2)

# ---------------------------------------------------------------- render the bed
voice_env = np.sqrt(np.convolve(voice ** 2, np.ones(2400) / 2400, 'same'))
speech = np.clip((20 * np.log10(voice_env + 1e-9) + 45) / 15, 0, 1)     # 0 silence .. 1 speech
duck = 10 ** (-4 * speech / 20)                                         # SFX dip up to 4 dB under words
duck = np.convolve(duck, np.ones(4800) / 4800, 'same')                  # smooth 100 ms

L = np.zeros(N); Rr = np.zeros(N)
rows = []
last = {}
for k, e in enumerate(sorted(E, key=lambda e: e['t'])):
    typ = e['typ']; x = LIB[typ]
    if e.get('rate'): x = resample(x, e['rate'])
    gain_db, align = TYPE[typ]
    gain_db += e.get('gain', 0)
    if typ not in ('clap', 'boom'): gain_db += 6
    if typ == 'clap' and e['t'] < 5: gain_db -= 3
    t = e['t']
    if e['snap'] == 'auto':
        t = snap_peak(t) if align == 'peak' else snap(t)
        if t - last.get(typ, -9) < 0.2:          # two cues snapped to one onset -> keep word time
            t = max(e['t'], last[typ] + 0.25)
    elif e['snap'] == 'peak':
        t = snap_peak(t, 0.2, 0.4)
    last[typ] = t
    start = int(t * R)
    if align == 'peak' and e['snap'] != 'none':
        start -= peak_time(x)
    elif align == 'end':
        start -= len(x)
    start -= int(0.008 * R) if align == 'onset' else 0
    if start < 0:
        x = x[-start:]; start = 0
    seg = x[: max(0, min(len(x), N - start))] * 10 ** (gain_db / 20)
    seg = seg * duck[start:start + len(seg)]
    pan = 0.0 if typ in ('clap', 'boom', 'hit', 'riser', 'bell', 'trans') else rng.uniform(-0.25, 0.25)
    gl, gr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    L[start:start + len(seg)] += seg * gl * np.sqrt(2)
    Rr[start:start + len(seg)] += seg * gr * np.sqrt(2)
    rows.append((f'{int(start / R // 60)}:{start / R % 60:06.3f}', typ, round(gain_db, 1), e['note']))

sfx = np.stack([L, Rr])
mix = sfx + voice[None, :]
pk = np.abs(mix).max()
print('events', len(rows), 'voice peak', round(20 * np.log10(np.abs(voice).max()), 2),
      'mix peak', round(20 * np.log10(pk), 2))
# safety: soft-limit only the SFX contribution where the sum would clip (voice untouched)
ceil = 10 ** (-1.0 / 20)
over = np.abs(mix).max(axis=0) > ceil
if over.any():
    print('limiting samples:', over.sum())
    room = np.maximum(ceil - np.abs(voice), 0)
    s = np.minimum(1, room / (np.abs(sfx).max(axis=0) + 1e-12))
    s = np.convolve(s, np.ones(480) / 480, 'same')
    mix = sfx * s + voice[None, :]
mix.T.astype(np.float32).tofile('mix.f32')
sfx.T.astype(np.float32).tofile('sfx_only.f32')
with open('cue_sheet.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['time', 'sound', 'gain_dB', 'what happens on screen']); w.writerows(rows)
