"""Camera encoder response: noise must stay silent, real motion must drive spikes.

This covers what the earlier camera tests missed. They used only a high-contrast synthetic bar,
which made the peak-relative threshold look correct — a real subject under room light is far
dimmer, and produced zero spikes while reporting non-zero motion.

Four clips, all from fake_video.py:
  still / noise  must drive no cells
  face / bar     must drive cells and produce spikes in all three populations
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

from fake_video import write_y4m

URL = 'http://localhost:5173/'
SHOTS = Path(r'C:\Users\Hp\AppData\Local\Temp\opencode')

LABELS = ('T4/T5 (13,595)', 'LPLC2 (185)', 'DNp01 (2)')


def sample(kind: str) -> dict[str, float | int | None]:
    clip = write_y4m(Path(tempfile.gettempdir()) / f'cam-{kind}.y4m', kind)
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

        body = page.inner_text('body')
        raw = re.search(r'live motion energy from your camera\s*\n\s*([0-9.]+)', body)

        def count(label: str) -> int:
            m = re.search(re.escape(label) + r'\s+(\d+)', body)
            return int(m.group(1)) if m else 0

        counts = {label: count(label) for label in LABELS}
        grid = page.evaluate('() => window.__gridProbe ? window.__gridProbe() : null')
        page.screenshot(path=str(SHOTS / f'tune-{kind}.png'), full_page=True)
        browser.close()

        return {
            'raw': float(raw.group(1)) if raw else None,
            'peak': max(grid) if grid else None,
            'total': sum(counts.values()),
            **counts,
        }


def main() -> None:
    results = {k: sample(k) for k in ('still', 'noise', 'face', 'bar')}

    print(f"{'clip':>6} {'raw':>8} {'peak':>7} {'T4/T5':>7} {'LPLC2':>6} {'DNp01':>6} {'total':>6}")
    for kind, r in results.items():
        raw = f"{r['raw']:.4f}" if r['raw'] is not None else 'none'
        peak = f"{r['peak']:.1f}" if r['peak'] is not None else 'none'
        print(f"{kind:>6} {raw:>8} {peak:>7} {r[LABELS[0]]:>7} {r[LABELS[1]]:>6} "
              f"{r[LABELS[2]]:>6} {r['total']:>6}")

    failures: list[str] = []

    # 1. A stationary scene must be completely silent.
    for kind in ('still', 'noise'):
        if results[kind]['total'] != 0:
            failures.append(
                f'{kind} clip produced {results[kind]["total"]} spikes; must be 0'
            )

    # 2. A real subject — the case that was silently broken — must drive the encoder.
    face = results['face']
    if face[LABELS[0]] <= 0:
        failures.append(
            f'a moving face drives no T4/T5 cells (peak {face["peak"]}); the encoder '
            f'stays silent on real subjects'
        )
    if face['total'] < 5:
        failures.append(f'a moving face yields only {face["total"]} spikes; want >= 5')

    # 3. All three populations must respond, so the full pathway is exercised.
    for label in LABELS:
        if face[label] <= 0:
            failures.append(f'face clip: {label} produced no spikes')

    # 4. The easy synthetic case must also work, or the encoder is broken outright.
    if results['bar'][LABELS[0]] <= 0:
        failures.append('sweeping bar drives no T4/T5 cells')

    # 5. Motion must separate from noise on the raw measurement.
    if None in (results['bar']['raw'], results['noise']['raw']):
        failures.append('raw motion not rendered')
    elif results['bar']['raw'] <= results['noise']['raw']:
        failures.append(
            f'bar motion does not exceed noise '
            f'({results["bar"]["raw"]} vs {results["noise"]["raw"]})'
        )

    print()
    if failures:
        print('FAIL')
        for f in failures:
            print(f'  {f}')
        sys.exit(1)
    print('PASS: noise silent, real subjects and synthetic motion both drive the encoder')


if __name__ == '__main__':
    main()