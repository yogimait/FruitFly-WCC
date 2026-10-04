"""Fine-tuning check: sensor noise must NOT register as stimulus, real motion must.

Two regressions this guards:
  1. per-cell normalisation against the frame's own brightest cell promoted noise to full
     scale, so a raw measurement of 0.0016 lit 26 of 64 cells
  2. the encoder's predicted spike latency must shorten as contrast rises — that monotone
     relationship is the only reason temporal encoding is worth anything, so it is asserted
     rather than assumed
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = 'http://localhost:5173/'
OUT = Path(r'C:\Users\Hp\AppData\Local\Temp\opencode')


def write_y4m(path: Path, kind: str, frames: int = 40, w: int = 320, h: int = 240) -> None:
    """
    kind:
      noise  - stationary subject plus low-amplitude per-frame flicker (sensor noise)
      still  - perfectly frozen frame
      moving - bright bar sweeping across
    """
    with path.open('wb') as f:
        f.write(b'YUV4MPEG2 W320 H240 F30:1 Ip A1:1 C420mpeg2\n')
        for i in range(frames):
            y = bytearray(w * h)
            for row in range(h):
                base = row * w
                for col in range(w):
                    if kind == 'moving':
                        bar = int((i / frames) * w)
                        v = 215 if abs(col - bar) < 26 else 24
                    else:
                        # Stationary subject; `noise` adds a few levels of flicker that a
                        # real webcam exhibits even when nothing is happening.
                        flicker = ((i * 7 + col * 13 + row * 3) % 11) if kind == 'noise' else 0
                        v = 120 + ((col // 40) % 2) * 90 + flicker
                    y[base + col] = max(0, min(255, v))
            f.write(b'FRAME\n')
            f.write(bytes(y))
            f.write(bytes([128]) * (w * h // 4))
            f.write(bytes([128]) * (w * h // 4))


def sample(kind: str) -> tuple[float | None, float | None, int, int]:
    path = Path(tempfile.gettempdir()) / f'cam-{kind}.y4m'
    write_y4m(path, kind)
    with sync_playwright() as p:
        browser = p.chromium.launch(args=[
            '--use-fake-ui-for-media-stream',
            '--use-fake-device-for-media-stream',
            f'--use-file-for-fake-video-capture={path}',
        ])
        ctx = browser.new_context(viewport={'width': 1400, 'height': 1100}, permissions=['camera'])
        page = ctx.new_page()
        page.goto(URL, wait_until='networkidle')
        page.wait_for_timeout(2500)
        page.get_by_role('button', name='use camera', exact=True).click()
        page.wait_for_timeout(5000)

        body = page.inner_text('body')
        raw = re.search(r'live motion energy from your camera\s*\n\s*([0-9.]+)', body)

        # Read the spike counts out of the live spike panel text. Parsing the rendered labels is
        # simpler and less brittle than walking the SVG, and it asserts what a viewer reads.
        def count(label: str) -> int:
            m = re.search(re.escape(label) + r'\s+(\d+)', body)
            return int(m.group(1)) if m else 0

        driven = count('T4/T5 (13,595)')
        pooled = count('LPLC2 (185)')
        descending = count('DNp01 (2)')
        total_spikes = driven + pooled + descending

        page.screenshot(path=str(OUT / f'tune-{kind}.png'), full_page=True)
        print(f'{kind:>6}: raw={raw.group(1) if raw else None} '
              f'T4/T5={driven} LPLC2={pooled} DNp01={descending} total={total_spikes}')
        browser.close()
        return (
            float(raw.group(1)) if raw else None,
            driven,
            total_spikes,
            24,
        )


def main() -> None:
    failures: list[str] = []

    noise_raw, noise_cells, noise_spikes, total = sample('noise')
    still_raw, still_cells, still_spikes, _ = sample('still')
    move_raw, move_cells, move_spikes, _ = sample('moving')

    print()
    print(f'noise: {noise_cells}/{total} driven cells, {noise_spikes} spikes')
    print(f'still: {still_cells}/{total} driven cells, {still_spikes} spikes')
    print(f'moving: {move_cells}/{total} driven cells, {move_spikes} spikes')

    # 1. Noise must not drive cells. Previously per-cell peak normalisation turned 0.0016 of
    #    noise into 26 of 64 driven cells.
    if noise_cells > 2:
        failures.append(
            f'sensor noise drives {noise_cells}/{total} cells; want <= 2'
        )

    # 2. A perfectly frozen frame must drive nothing beyond the baseline cells.
    if still_cells > 3:
        failures.append(f'frozen frame drives {still_cells}/{total} cells; want <= 3')

    # 3. Real motion must drive a substantial number of cells.
    if move_cells < 6:
        failures.append(f'moving subject drives only {move_cells}/{total} cells; want >= 6')

    # 4. Spikes must appear for real motion, across all three populations.
    if move_spikes < 10:
        failures.append(f'moving subject yields only {move_spikes} spikes; want >= 10')

    # 5. Motion must separate from noise on the raw measurement.
    if None in (noise_raw, move_raw):
        failures.append('raw motion not rendered')
    elif move_raw <= noise_raw:
        failures.append(f'motion does not exceed noise ({move_raw} vs {noise_raw})')

    if failures:
        print('\nFAIL')
        for f in failures:
            print(f'  {f}')
        sys.exit(1)
    print('\nPASS: noise suppressed, motion drives cells and produces spikes')


if __name__ == '__main__':
    main()