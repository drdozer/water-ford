#!/usr/bin/env python3
"""Build the water-ford footstep audio assets (deterministic, re-runnable).

Provenance: maintainer phone recordings (2026-10-18, Samsung voice recorder,
3 takes in assets-src/audio/source/), curated over six listening rounds with
agent-assisted DSP. This script embeds the distilled result — label times,
keeper grid, and every processing knob — and regenerates ALL shipped assets
from the sources alone. Re-running reproduces the shipped files exactly.

Outputs:
  assets-src/audio/masters/   curated WAV masters (tracked; never shipped)
  mod/sound/walking/          encoded Ogg Vorbis (shipped)

Chain per step (the round-by-round findings live in docs/journal.md):
  decode -> DC/rumble high-pass -> take-level peak normalise (-3 dBFS)
  -> per-take spectral denoise (Wiener-style, median-smoothed gains; the
     'tamed' parameters that killed the musical-noise pops)
  -> STFT with ONE-FRAME PADDING (an unpadded istft explodes signal edges:
     x/w -> inf where the single-frame Hann window -> 0 — the root cause of
     the 'terminal pops' in early rounds)
  -> tread peak picked strictly within label +/-0.25 s (a wider window let the
     picker wander into unlabeled house noise)
  -> two-sided window: dip-walk start (local env minimum before the tread —
     excludes pre-step clicks), end at last -48 dBFS crossing capped BEFORE the
     next footstep's onset (measured from the tread), head declick, cosine fades
  -> optional tail suppression (-12 dB above 3.5 kHz after +130 ms) for
     swish-flagged grid slots (clothing swish removal; never on squeaky rows)

Wet composites (ford deck): board + vanilla shallow-water splash, splash onset
leading the board thunk by ~120 ms (physically: foot breaks water, then loads
the deck), board 0.85 / splash 1.0, splash running its natural 0.44-0.66 s.
Licensing: derived from Factorio assets — permitted in mods per the Factorio
ToS ("adaptations or works derived from the Factorio assets are permitted to
be included and distributed as part of your mod"); Wube retains rights.

Usage:  tools/build-audio.py           (via `devctl python run` preferred;
ffmpeg must be on PATH)
"""
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent          # mod repo root
SRC = ROOT / 'assets-src' / 'audio' / 'source'
MASTERS = ROOT / 'assets-src' / 'audio' / 'masters'
SHIPPED = ROOT / 'mod' / 'sound' / 'walking'
SR = 44100

# ---------------------------------------------------------------- knobs ----
NORMALIZE_DBFS = -3.0
DENOISE = {'k': 1.8, 'floor_gain': 0.06}          # 'tamed' (round-4 lock)
HIGHPASS_HZ = 75
WINDOW = {'start_rel_db': -35, 'end_abs_db': -48, 'min_len_s': 0.05,
          'cap_s': 0.62, 'next_label_margin_s': 0.04, 'fade_in_s': 0.010,
          'fade_out_s': 0.030, 'hot_tail_fade_s': 0.060}
TAIL_SUPPRESS = {'after_s': 0.130, 'knee_hz': 3500, 'atten_db': -12}
WET = {'lead_s': 0.09, 'board_gain': 0.85, 'splash_gain': 1.0,
       'max_len_s': 0.75, 'fade_out_s': 0.060}
ENCODE = ['-ar', '44100', '-c:a', 'libvorbis', '-qscale:a', '5']

# label times (s) from the curation session (Audacity LabelSounds, -25 dB peak)
LABELS = {
    'take-20261018-220810': [0.92, 1.45, 2.05, 2.69, 3.35, 3.83, 4.68, 5.39,
                             6.01, 6.68, 7.3, 7.98, 8.61, 9.22, 9.89, 10.6,
                             11.19, 11.8],
    'take-20261018-220858': [0.94, 1.52, 2.02, 2.78, 3.43, 4.13, 4.84],
}
# grid: shipped slot -> (take, label index, treatment); treatment 'lp' = tail
# suppression (clothing swish), 'raw' = as-is
LAND_GRID = [
    ('flooring-01', 'take-20261018-220810', 2, 'lp'),   # D01
    ('flooring-02', 'take-20261018-220810', 4, 'raw'),  # D03
    ('flooring-03', 'take-20261018-220810', 5, 'raw'),  # D04
    ('flooring-04', 'take-20261018-220810', 6, 'lp'),   # D05
    ('flooring-05', 'take-20261018-220810', 7, 'lp'),   # D06
    ('flooring-06', 'take-20261018-220810', 12, 'raw'),  # D11 (squeak-mixed)
    ('flooring-07', 'take-20261018-220858', 3, 'raw'),  # C1 (combo)
    ('flooring-08', 'take-20261018-220858', 4, 'raw'),  # C2 (combo)
    ('flooring-09', 'take-20261018-220810', 15, 'raw'),  # D14
    ('flooring-10', 'take-20261018-220810', 16, 'raw'),  # D15
    ('flooring-11', 'take-20261018-220810', 1, 'raw'),  # X02 (rescue)
    ('flooring-12', 'take-20261018-220858', 2, 'lp'),   # X05 (rescue)
    ('flooring-13', 'take-20261018-220858', 6, 'raw'),  # P1 (squeak, vol 0.3)
]
LAND_SPARES = [  # curated alternates; masters built, not shipped
    ('spare-C3', 'take-20261018-220858', 5, 'raw'),
    ('spare-D13', 'take-20261018-220810', 14, 'lp'),
    ('spare-X01', 'take-20261018-220810', 0, 'lp'),
    ('spare-X03', 'take-20261018-220858', 0, 'lp'),
]
# wet composites: slot -> (board take/idx, vanilla splash 1..7)
FORD_GRID = [
    ('ford-deck-01', 'take-20261018-220810', 2, 1),    # W1
    ('ford-deck-02', 'take-20261018-220810', 8, 2),    # W2a
    ('ford-deck-03', 'take-20261018-220810', 12, 2),   # W2b
    ('ford-deck-04', 'take-20261018-220810', 4, 3),    # W3
    ('ford-deck-05', 'take-20261018-220810', 11, 4),   # W4a
    ('ford-deck-06', 'take-20261018-220810', 14, 4),   # W4b
    ('ford-deck-07', 'take-20261018-220810', 17, 5),   # W5b
    ('ford-deck-08', 'take-20261018-220810', 7, 6),    # W6
    ('ford-deck-09', 'take-20261018-220810', 6, 7),    # W7
    ('ford-deck-10', 'take-20261018-220858', 6, 1),    # W8 (wet creak)
]

# ------------------------------------------------------------------ io -----
def decode(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 'f32le',
                          '-ac', '1', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()

def write_wav(path, x):
    x = np.clip(x, -1.0, 1.0)
    pcm = (x * 32767).astype('<i2').tobytes()
    tmp = path.with_suffix('.tmp')
    with wave.open(str(tmp), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm)
    if path.exists() and path.read_bytes() == tmp.read_bytes():
        tmp.unlink()                                  # idempotent: no touch
    else:
        tmp.replace(path)

def encode_ogg(wav_path, ogg_path):
    """Encode + write only on audio change (ogg container serials differ per
    encode; compare decoded PCM so rebuilds don't churn tracked files)."""
    ogg_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = ogg_path.with_suffix('.tmp.ogg')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(wav_path), *ENCODE,
                    '-map_metadata', '-1', str(tmp)], check=True)
    if ogg_path.exists():
        def pcm(p):
            return subprocess.run(['ffmpeg', '-v', 'error', '-i', str(p), '-f', 'f32le', '-'],
                                  capture_output=True, check=True).stdout
        if pcm(ogg_path) == pcm(tmp):
            tmp.unlink()
            return
    tmp.replace(ogg_path)

# ----------------------------------------------------------------- dsp -----
def env_of(x, ms=5):
    w = int(ms * SR / 1000)
    return np.sqrt(np.convolve(x ** 2, np.ones(w) / w, 'same'))

def stft(x, n=1024, hop=256):
    w = np.hanning(n)
    return np.array([np.fft.rfft(np.pad(x[i:i+n], (0, max(0, n - (len(x) - i)))))
                     for i in range(0, len(x), hop)]), w

def istft(S, w, length):
    out = np.zeros(length + 4096); norm = np.zeros(length + 4096)
    for i, s in enumerate(S):
        out[i*256:i*256+len(w)] += np.fft.irfft(s, len(w)) * w
        norm[i*256:i*256+len(w)] += w ** 2
    return (out / np.maximum(norm, 1e-9))[:length]

def median_filter(x, size=9, axis=0):
    """Sliding-window median along one axis (numpy-only; odd size)."""
    pad = [(size // 2, size // 2)] + [(0, 0)] * (x.ndim - 1) if axis == 0 else None
    if axis == 0:
        xp = np.pad(x, pad, mode='edge')
        win = np.lib.stride_tricks.sliding_window_view(xp, size, axis=0)
        return np.median(win, axis=-1)
    xp = np.pad(x, ((0, 0), (size // 2, size // 2)), mode='edge')
    win = np.lib.stride_tricks.sliding_window_view(xp, size, axis=1)
    return np.median(win, axis=-1)

def denoise(x, noise_spec):
    n = 1024
    xp = np.pad(x, (n, n))            # THE pad fix: edges must sit in full overlap
    S, w = stft(xp)
    mag = np.abs(S); phase = S / np.maximum(mag, 1e-12)
    gain = np.maximum(0.0, (mag - DENOISE['k'] * noise_spec[None, :]) / np.maximum(mag, 1e-12))
    gain = np.maximum(gain, DENOISE['floor_gain'])
    gain = median_filter(gain, 5)     # musical-noise taming (over time)
    gain = np.apply_along_axis(lambda g: np.convolve(g, np.ones(3) / 3, 'same'), 1, gain)
    y = istft((mag * gain) * phase, w, len(xp))
    return y[n:n + len(x)].astype(np.float32)

def noise_profile(x):
    n = int(0.4 * SR); best, br = None, 1e9
    for i in range(0, max(1, len(x) - n), int(0.05 * SR)):
        r = float(np.sqrt(np.mean(x[i:i+n] ** 2)))
        if r < br:
            best, br = x[i:i+n], r
    S, _ = stft(best)
    return np.mean(np.abs(S), axis=0)

def highpass(x, fc=HIGHPASS_HZ):
    sp = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(sp * (1 / (1 + (fc / np.maximum(f, 1)) ** 4)), len(x)).astype(np.float32)

def tail_suppress(x):
    S, w = stft(x)
    f = np.fft.rfftfreq(1024, 1 / SR)
    gain = np.ones_like(S)
    start = int(TAIL_SUPPRESS['after_s'] * SR / 256)
    if start >= S.shape[0]:
        return x
    r1 = min(S.shape[0], start + int(0.060 * SR / 256))
    att = 10 ** (TAIL_SUPPRESS['atten_db'] / 20)
    ramp = np.ones(S.shape[0]); ramp[start:r1] = np.linspace(1, att, r1 - start); ramp[r1:] = att
    gain[:, f >= TAIL_SUPPRESS['knee_hz']] = ramp[:, None]
    return istft(S * gain, w, len(x)).astype(np.float32)

def window_hit(x, peak_idx, next_gap_from_peak_s):
    """Two-sided window (round-5/6 rules). Returns the cut hit."""
    env = env_of(x)
    peak_env = float(env[max(0, peak_idx - 50):peak_idx + 50].max())
    start_thr = peak_env * 10 ** (WINDOW['start_rel_db'] / 20)
    # dip-walk: back from the tread while env rises; stop at the local minimum
    i = peak_idx
    while i > 0 and env[i - 1] <= env[i] and peak_idx - i < int(0.08 * SR):
        i -= 1
    start = i
    if peak_env > 0 and env[start] > start_thr * 3:
        start = max(0, peak_idx - int(0.012 * SR))    # no usable dip -> tight
    # end: last -48 dBFS crossing, capped before the next footstep's onset
    cap = peak_idx + int(WINDOW['cap_s'] * SR)
    if next_gap_from_peak_s is not None:
        cap = min(cap, peak_idx + int(max(0.15, next_gap_from_peak_s
                                          - WINDOW['next_label_margin_s']) * SR))
    above = np.where(env[peak_idx:min(len(env), cap)] > 10 ** (WINDOW['end_abs_db'] / 20))[0]
    end = cap
    if len(above):
        end = min(cap, peak_idx + above[-1] + int(0.015 * SR))
    end = max(end, peak_idx + int(WINDOW['min_len_s'] * SR))
    y = x[start:end].copy()
    # head declick: isolated spikes (slipper slap / pre-echo) vs local median
    nh = min(len(y), int(0.025 * SR))
    head = y[:nh].copy(); sm = median_filter(head, 9)
    spike = np.abs(head) > 4 * np.abs(sm) + 1e-4
    if spike.any():
        head[spike] = sm[spike]
    y[:nh] = head
    # fades (gentler when the tail is still hot — mid-squeak cutoffs)
    ni = int(WINDOW['fade_in_s'] * SR)
    no = min(int(WINDOW['fade_out_s'] * SR), len(y) // 3)
    if len(y) > int(0.05 * SR) and np.max(np.abs(y[-int(0.05 * SR):])) > 10 ** (-40 / 20):
        no = min(int(WINDOW['hot_tail_fade_s'] * SR), len(y) // 3)
    y[:ni] *= np.linspace(0, 1, ni)
    y[-no:] *= 0.5 * (1 + np.cos(np.pi * np.linspace(0, 1, no)))
    return y

def build_hit(takes, take, li):
    x_all = takes[take]['audio']
    t = LABELS[take][li]
    labels = LABELS[take]
    next_gap = (labels[li + 1] - t) if li + 1 < len(labels) else None
    lo, hi = max(0, int((t - 0.25) * SR)), min(len(x_all), int((t + 0.85) * SR))
    region = denoise(x_all[lo:hi].copy(), takes[take]['profile'])
    energies = np.convolve(region ** 2, np.ones(int(0.005 * SR)) / int(0.005 * SR), 'valid')
    pick_end = min(len(energies), int(0.5 * SR))      # pick strictly label±0.25 s
    peak = int(np.argmax(energies[:pick_end]))
    if next_gap is not None:
        next_gap = next_gap - (peak / SR - 0.25)      # peak-anchored distance
    return window_hit(region, peak, next_gap)

def build_wet(board, splash_seg):
    off_b = int(WET['lead_s'] * SR)
    comp_len = max(off_b + len(board), min(len(splash_seg), int(WET['max_len_s'] * SR)))
    comp = np.zeros(comp_len, dtype=np.float32)
    seg = splash_seg[:comp_len]
    comp[:len(seg)] += WET['splash_gain'] * seg
    comp[off_b:off_b + len(board)] += WET['board_gain'] * board
    n = min(int(WET['fade_out_s'] * SR), comp_len // 3)
    comp[-n:] *= 0.5 * (1 + np.cos(np.pi * np.linspace(0, 1, n)))
    return comp / max(1e-9, np.max(np.abs(comp)) / 0.707)

# ---------------------------------------------------------------- main -----
def main():
    MASTERS.mkdir(parents=True, exist_ok=True)
    SHIPPED.mkdir(parents=True, exist_ok=True)

    takes = {}
    for name in LABELS:
        x = decode(SRC / f'{name}.mp3')
        x = highpass(x - x.mean())
        x = x / max(1e-9, np.max(np.abs(x))) * (10 ** (NORMALIZE_DBFS / 20))
        takes[name] = {'audio': x, 'profile': noise_profile(x)}

    manifest = {'land': [], 'land_spares': [], 'ford': []}

    def cut(slot, take, li, treat):
        y = build_hit(takes, take, li)
        if treat == 'lp':
            y = tail_suppress(y.copy())
        write_wav(MASTERS / f'{slot}.wav', y)
        return y

    print('land bank:')
    for slot, take, li, treat in LAND_GRID + LAND_SPARES:
        y = cut(slot, take, li, treat)
        key = 'land' if slot.startswith('flooring') else 'land_spares'
        manifest[key].append({'slot': slot, 'take': take, 'label': LABELS[take][li],
                              'treatment': treat, 'len_ms': int(len(y) / SR * 1000)})
        print(f"  {slot}: {len(y)/SR*1000:.0f} ms ({treat})")

    print('ford composites:')
    splash_raw = [decode(p) for p in sorted(SRC.parent.glob('vanilla-splash/shallow-water-*.ogg'))] \
        if (SRC.parent / 'vanilla-splash').exists() else \
        [decode(p) for p in sorted(Path.home().joinpath(
            '.local/share/factorio_2_dlc/data/base/sound/walking').glob('shallow-water-*.ogg'))]
    for s in splash_raw:                              # head declick + 20 ms fade-in
        nh = min(len(s), int(0.025 * SR))
        head = s[:nh].copy(); sm = median_filter(head, 9)
        spike = np.abs(head) > 4 * np.abs(sm) + 1e-4
        if spike.any():
            head[spike] = sm[spike]
        s[:nh] = head
        n = int(0.020 * SR); s[:n] *= np.linspace(0, 1, n)
    for slot, take, li, spi in FORD_GRID:
        board = build_hit(takes, take, li)            # wets use untreated boards
        y = build_wet(board, splash_raw[spi - 1])
        write_wav(MASTERS / f'{slot}.wav', y)
        manifest['ford'].append({'slot': slot, 'board': f'{take}#{li}',
                                 'splash': f'shallow-water-{spi}',
                                 'len_ms': int(len(y) / SR * 1000)})
        print(f"  {slot}: {len(y)/SR*1000:.0f} ms")

    print('encode:')
    for wav in sorted(MASTERS.glob('*.wav')):
        slot = wav.stem
        if slot.startswith('flooring'):
            encode_ogg(wav, SHIPPED / f'{slot}.ogg')
            print(f'  {slot}.ogg')
    for slot, *_ in FORD_GRID:
        encode_ogg(MASTERS / f'{slot}.wav', SHIPPED / f'{slot}.ogg')
        print(f'  {slot}.ogg')

    (MASTERS / 'build-manifest.json').write_text(json.dumps(manifest, indent=1))
    print(f"done: {len(manifest['land'])} land + {len(manifest['ford'])} ford assets")

if __name__ == '__main__':
    sys.exit(main())
