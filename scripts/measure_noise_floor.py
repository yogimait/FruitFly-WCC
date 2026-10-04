"""Choose and verify the camera drive threshold from measured luminance, not from guesswork.

The drive threshold in dashboard/src/components/live-spikes.tsx is an absolute bar in 0-255
luminance units. What it must satisfy:

  noise / still  drive nothing — otherwise the fly twitches at sensor jitter
  face / bar     drive cells  — otherwise the encoder never sees a real subject

Those two pull in opposite directions, and an earlier threshold could not satisfy both because
it was a ratio of each frame's own peak, which made the effective bar depend on scene
brightness. Sampling resolution matters as much as the bar: at 8x8 point-sampled, real motion
measured under 1 luminance level; at 40x40 point-sampled, sensor noise measured 17. This
script measures the 16x16 box-averaged grid the app actually uses, then sweeps candidate bars
and reports which ones are admissible.

Run:  python scripts/measure_noise_floor.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

from fake_video import write_y4m

URL = 'http://localhost:5173/'
BARS = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
SHOTS = Path(r'C:\Users\Hp\AppData\Local\Temp\opencode')


def sample(kind: str) -> list[float]:
    """Read the live 8x8/16x16 grid of absolute luminance deltas from the running app."""
    clip = write_y4m(Path(tempfile.gettempdir()) / f'floor-{kind}.y4m', kind)
    with sync_playwright() as p:
        browser = p.chromium.launch(args=[
            '--use-fake-ui-for-media-stream',
            '--use-fake-device-for-media-stream',
            f'--use-file-for-fake-video-capture={clip}',
        ])
        ctx = browser.new_context(viewport={'width': 1400, 'height': 1100}, permissions=['camera'])
        page = ctx.new_page()
        page.goto(URL, wait_until='networkidle')
        page.wait_for_timeout(2500)
        page.get_by_role('button', name='use camera', exact=True).click()
        page.wait_for_timeout(5000)
        grid = page.evaluate('() => window.__gridProbe ? window.__gridProbe() : null')
        page.screenshot(path=str(SHOTS / f'floor-{kind}.png'), full_page=True)
        browser.close()
        return grid or []


def main() -> None:
    results: dict[str, list[float]] = {}
    for kind in ('still', 'noise', 'face', 'bar'):
        grid = sample(kind)
        if not grid:
            print(f'{kind}: no probe exposed — cannot measure')
            sys.exit(2)
        results[kind] = grid
        peak = max(grid)
        print(f'\n{kind:>5}: peak={peak:5.1f}  mean={sum(grid)/len(grid):5.2f}  n={len(grid)}')
        for bar in BARS:
            n = sum(1 for v in grid if v >= bar)
            print(f'      bar>={bar:>2}: {n:>3}/{len(grid)} cells driven')

    noise_peak = max(results['noise'])
    print('\n' + '=' * 62)
    print(f'noise peak = {noise_peak:.1f}')
    print('admissible bars (noise silent, face and bar both driven):')

    admissible = []
    for bar in BARS:
        noise_n = sum(1 for v in results['noise'] if v >= bar)
        face_n = sum(1 for v in results['face'] if v >= bar)
        bar_n = sum(1 for v in results['bar'] if v >= bar)
        ok = noise_n == 0 and face_n > 0 and bar_n > 0
        if ok:
            admissible.append((bar, face_n, bar_n))
        print(f'  bar={bar:>2}: noise={noise_n:>3} face={face_n:>3} bar={bar_n:>3}'
              f'  {"OK" if ok else "reject"}')

    if not admissible:
        print('\nFAIL: no single bar separates noise from motion at this sampling resolution')
        sys.exit(1)

    # Prefer the highest admissible bar: it rejects the most marginal signal while still
    # accepting every realistic case.
    chosen, face_n, bar_n = max(admissible)
    print(f'\nhighest admissible bar = {chosen} (face drives {face_n}, bar drives {bar_n})')
    print(f'noise peak {noise_peak:.1f} leaves {chosen - noise_peak:.1f} levels of margin')


if __name__ == '__main__':
    main()