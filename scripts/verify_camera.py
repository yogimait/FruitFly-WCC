"""Drive the camera path with a moving pattern and verify the fly reacts.

Headless Chromium ships no real webcam, so getUserMedia only works against a fake capture
device. Chromium's --use-file-for-fake-video-capture plays a Y4M file, which gives frames
that actually change over time — enough to prove the motion measure is live and that the fly
responds to it, rather than just that no error was thrown.

Two cases:
  1. no camera at all -> the page must fall back to the synthetic disk and say so
  2. fake moving camera -> motion energy must be non-zero and the fly must animate
"""

from __future__ import annotations

import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

PORT = 5173
URL = f'http://localhost:{PORT}/'
OUT = Path(r'C:\Users\Hp\AppData\Local\Temp\opencode')


def make_y4m(path: Path, frames: int = 30, w: int = 320, h: int = 240) -> None:
    """Write a Y4M with a bright bar sweeping across, so consecutive frames differ."""
    with path.open('wb') as f:
        f.write(b'YUV4MPEG2 W320 H240 F30:1 Ip A1:1 C420mpeg2\n')
        for i in range(frames):
            # C420mpeg2: one Y plane then U then V, half resolution.
            y_plane = bytearray(w * h)
            bar = int((i / frames) * w)
            for row in range(h):
                base = row * w
                for col in range(w):
                    # A moving vertical bar plus static stripes, so motion is unambiguous.
                    bright = abs(col - bar) < 24 or (col // 40) % 2 == 0
                    y_plane[base + col] = 220 if bright else 20
            f.write(b'FRAME\n')
            f.write(bytes(y_plane))
            f.write(bytes([128]) * (w * h // 4))
            f.write(bytes([128]) * (w * h // 4))


def main() -> None:
    y4m = Path(tempfile.gettempdir()) / 'fake-cam.y4m'
    make_y4m(y4m)
    print(f'fake camera file: {y4m} ({y4m.stat().st_size / 1024:.0f} KB)')

    failures: list[str] = []

    # --- Case 1: no camera available -------------------------------------------------
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1400, 'height': 900})
        errs: list[str] = []
        page.on('pageerror', lambda e: errs.append(str(e)))
        page.goto(URL, wait_until='networkidle')
        page.wait_for_timeout(2500)
        page.get_by_role('button', name='use camera', exact=True).click()
        page.wait_for_timeout(2500)
        body = page.inner_text('body')
        fallback = 'falling back' in body or 'no camera' in body
        print(f'no-camera: falls back honestly = {fallback}')
        print(f'no-camera: page errors         = {errs or "none"}')
        if not fallback:
            failures.append('no-camera path did not report a fallback')
        browser.close()

    # --- Case 2: fake camera with real motion ----------------------------------------
    with sync_playwright() as p:
        browser = p.chromium.launch(args=[
            '--use-fake-ui-for-media-stream',
            '--use-fake-device-for-media-stream',
            f'--use-file-for-fake-video-capture={y4m}',
        ])
        ctx = browser.new_context(
            viewport={'width': 1400, 'height': 900}, permissions=['camera']
        )
        page = ctx.new_page()
        errs = []
        page.on('pageerror', lambda e: errs.append(str(e)))
        page.goto(URL, wait_until='networkidle')
        page.wait_for_timeout(2500)
        page.get_by_role('button', name='use camera', exact=True).click()
        page.wait_for_timeout(4000)

        body = page.inner_text('body')
        video_visible = page.locator('video').is_visible()

        # Read the live motion value off the page.
        import re
        match = re.search(r'live motion energy from your camera\s*\n\s*([0-9.]+)', body)
        motion = float(match.group(1)) if match else None

        print(f'fake-camera: video visible     = {video_visible}')
        print(f'fake-camera: motion energy      = {motion}')
        print(f'fake-camera: page errors        = {errs or "none"}')

        # Sample the 3D canvas twice: differing frames prove the fly is animating.
        page.locator('canvas').first.screenshot(path=str(OUT / 'cam-a.png'))
        page.wait_for_timeout(700)
        page.locator('canvas').first.screenshot(path=str(OUT / 'cam-b.png'))
        a = (OUT / 'cam-a.png').read_bytes()
        b = (OUT / 'cam-b.png').read_bytes()
        animating = a != b
        print(f'fake-camera: 3D scene animating = {animating}')

        page.screenshot(path=str(OUT / 'cam-full.png'), full_page=True)

        if not video_visible:
            failures.append('camera preview is not visible')
        if motion is None:
            failures.append('live motion energy not rendered')
        elif motion <= 0.0:
            failures.append(f'live motion energy is zero ({motion}) — feed not measured')
        if not animating:
            failures.append('3D scene is static; fly is not reacting')

        browser.close()

    print()
    if failures:
        print('FAIL')
        for f in failures:
            print(f'  {f}')
        sys.exit(1)
    print('PASS: camera preview visible, motion measured, fly reacts')


if __name__ == '__main__':
    main()