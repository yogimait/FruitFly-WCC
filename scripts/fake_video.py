"""Fake webcam clips for browser tests, in Y4M so Chromium can consume them directly.

Shared by verify_camera_tuning.py and measure_noise_floor.py so the two cannot drift apart —
the noise floor and the response test must exercise identical stimuli.

Each generator aims at a property a real webcam has:

  still  - a frozen frame. Any nonzero motion reading is a bug.
  noise  - a stationary subject with sensor jitter. Must never drive the encoder.
  face   - a mid-contrast head-and-shoulders blob sweeping across frame. The realistic case:
           a person leaning past the camera. Must drive the encoder.
  bar    - a high-contrast sweeping bar. The easy, unambiguous case.

The 8x8 / 16x16 sampling grid means each block spans tens of pixels, so `face` deliberately
travels a long way (180 px across the clip) to be sure motion crosses block boundaries.
"""

from __future__ import annotations

from pathlib import Path

WIDTH = 320
HEIGHT = 240
FRAMES = 60


def _luma(kind: str, frame: int, col: int, row: int, frames: int) -> int:
    if kind == 'bar':
        bar = int((frame / frames) * WIDTH)
        return 215 if abs(col - bar) < 26 else 24

    if kind == 'face':
        cx = WIDTH / 2 + (frame / frames - 0.5) * 180
        cy = HEIGHT / 2 + 12
        d2 = ((col - cx) ** 2 + (row - cy) ** 2) / (80.0 ** 2)
        return int(165 - 85 * max(0.0, 1.0 - d2))

    # still / noise share a stationary subject; noise adds low-amplitude jitter.
    n = ((frame * 37 + col * 61 + row * 17) % 7) - 3 if kind == 'noise' else 0
    return 120 + n + ((col // 40) % 2) * 40


def write_y4m(path: Path, kind: str, frames: int = FRAMES) -> Path:
    """Write a Y4M clip of `kind` and return the path."""
    if kind not in {'still', 'noise', 'face', 'bar'}:
        raise ValueError(f'unknown clip kind: {kind}')

    chroma = WIDTH * HEIGHT // 4
    with path.open('wb') as f:
        f.write(
            f'YUV4MPEG2 W{WIDTH} H{HEIGHT} F30:1 Ip A1:1 C420mpeg2\n'.encode()
        )
        for frame in range(frames):
            y = bytearray(WIDTH * HEIGHT)
            for row in range(HEIGHT):
                base = row * WIDTH
                for col in range(WIDTH):
                    y[base + col] = max(0, min(255, _luma(kind, frame, col, row, frames)))
            f.write(b'FRAME\n')
            f.write(bytes(y))
            f.write(bytes([128]) * chroma)
            f.write(bytes([128]) * chroma)
    return path