#!/usr/bin/env python3
"""Utility: Convert a WAV file to 16 kHz mono.

Usage:
  python -m triage_stream.utils.convert_wav_to_16k [INPUT_WAV] [OUTPUT_WAV]

Defaults to `data/sample/call_10.wav` -> `data/sample/call_10_16k.wav` when run
from the project root.
"""
from __future__ import annotations

import argparse
import math
import sys

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly


def resample_audio(data: np.ndarray, orig_sr: int, target_sr: int = 16000) -> np.ndarray:
    if orig_sr == target_sr:
        return data
    g = math.gcd(orig_sr, target_sr)
    up = target_sr // g
    down = orig_sr // g

    if data.ndim == 1:
        return resample_poly(data, up, down)

    out_channels = []
    for ch in range(data.shape[1]):
        out_channels.append(resample_poly(data[:, ch], up, down))
    min_len = min(c.shape[0] for c in out_channels)
    stacked = np.stack([c[:min_len] for c in out_channels], axis=1)
    return stacked


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    p = argparse.ArgumentParser(description="Convert WAV to 16 kHz mono")
    p.add_argument("infile", nargs="?", default="data/sample/call_10.wav")
    p.add_argument("outfile", nargs="?", default="data/sample/call_10_16k.wav")
    args = p.parse_args(argv)

    data, sr = sf.read(args.infile)

    # Downmix to mono if input is multi-channel
    if getattr(data, "ndim", 1) > 1 and data.shape[1] > 1:
        orig_ch = data.shape[1]
        data = np.mean(data, axis=1)
        print(f"Downmixed {args.infile} from {orig_ch} channels to mono")

    resampled = resample_audio(data, sr, 16000)

    # write as 16-bit PCM WAV
    sf.write(args.outfile, resampled, 16000, subtype="PCM_16")
    print(f"Wrote {args.outfile} (16000 Hz, mono)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
