"""Prove the camera response is visible: compare a STILL subject against a MOVING one.

The original bug was scale, not plumbing. Raw motion energy for a still person in a lit room
is ~0.002, and feeding that into an animation parameter linearly produced no visible change —
the fly looked inert. This test asserts the normalised response actually separates the two
cases, and that the live stimulus map lights up.
"""

from __future__ import annotations

import re
import struct
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = 'http://localhost:5173/'
OUT = Path(r'C:\Users\Hp\AppData\Local\Temp\opencode')


def write_y4m(path: Path, moving: bool, frames: int = 40, w: int = 320, h: int = 240) -> None:
    """Y4M with a sweeping bar (moving) or a frozen frame (still)."""
    with path.open('wb') as f:
        f.write(b'YUV4MPEG2 W320 H240 F30:1 Ip A1:1 C420mpeg2\n')
        for i in range(frames):
            bar = int((i / frames) * w) if moving else 120
            y = bytearray(w * h)
            for row in range(h):
                base = row * w
                for col in range(w):
                    bright = abs(col - bar) < 26
                    y[base + col] = 215 if bright else 24
            f.write(b'FRAME\n')
            f.write(bytes(y))
            f.write(bytes([128]) * (w * h // 4))
            f.write(bytes([128]) * (w * h // 4))


def read_state(page) -> tuple[float | None, float | None]:
    body = page.inner_text('body')
    raw = re.search(r'measured motion\s*\n\s*([0-9.]+)', body)
    lvl = re.search(r'response level\s*\n\s*([0-9.]+)%', body)
    return (
        float(raw.group(1)) if raw else None,
        float(lvl.group(1)) if lvl else None,
    )


def run_case(moving: bool) -> tuple[float | None, float | None, int]:
    path = Path(tempfile.gettempdir()) / ('cam-move.y4m' if moving else 'cam-still.y4m')
    write_y4m(path, moving)
    with sync_playwright() as p:
        browser = p.chromium.launch(args=[
            '--use-fake-ui-for-media-stream',
            '--use-fake-device-for-media-stream',
            f'--use-file-for-fake-video-capture={path}',
        ])
        ctx = browser.new_context(viewport={'width': 1400, 'height': 1000}, permissions=['camera'])
        page = ctx.new_page()
        page.goto(URL, wait_until='networkidle')
        page.wait_for_timeout(2500)
        page.get_by_role('button', name='use camera', exact=True).click()
        page.wait_for_timeout(5000)

        raw, level = read_state(page)

        # Count lit cells in the live stimulus map.
        lit = page.evaluate("""() => {
          const cells = [...document.querySelectorAll('[title^="cell "]')]
          return cells.filter(c => (parseFloat(c.getAttribute('title').split(': ')[1]) || 0) > 0.35)
                      .length;
        }""")

        tag = 'moving' if moving else 'still'
        page.screenshot(path=str(OUT / f'response-{tag}.png'), full_page=True)
        print(f'{tag:>7}: raw={raw} response={level}% lit-cells={lit}')
        browser.close()
        return raw, level, lit


def main() -> None:
    still_raw, still_lvl, still_lit = run_case(False)
    move_raw, move_lvl, move_lit = run_case(True)

    failures: list[str] = []

    if still_lvl is None or move_lvl is None:
        print('FAIL: response level not rendered')
        sys.exit(1)

    # A still subject must still clear a visible floor, or the fly reads as "off".
    if still_lvl < 15:
        failures.append(f'still subject response too low ({still_lvl}%) — fly looks inert')

    # A moving subject must read clearly higher than a still one.
    if move_lvl <= still_lvl + 15:
        failures.append(
            f'moving subject does not separate from still ({move_lvl}% vs {still_lvl}%)'
        )

    if move_lit == 0:
        failures.append('live stimulus map has no lit cells while moving')

    print()
    print(f'still  -> {still_lvl}% response, {still_lit} lit cells')
    print(f'moving -> {move_lvl}% response, {move_lit} lit cells')
    print(f'separation: {move_lvl - still_lvl:.0f} percentage points')

    if failures:
        print('\nFAIL')
        for f in failures:
            print(f'  {f}')
        sys.exit(1)
    print('\nPASS: still subject shows a baseline, moving subject reads clearly higher')


if __name__ == '__main__':
    main()