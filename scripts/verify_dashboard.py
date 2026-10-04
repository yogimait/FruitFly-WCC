"""Verify the dashboard renders measured data, not placeholders.

The dashboard is one continuous view rather than tabs, so this walks the real page: the default
view, then the collapsed data disclosure, then the camera mode.

Asserts on rendered TEXT, not HTTP status. A dashboard that silently falls back to "not
measured" looks fine in a screenshot and is useless in a demo, which is exactly the failure this
exists to catch. Also checks the accessibility affordances, since a canvas chart or an
unlabelled control is invisible to half the audience.

Usage:
    bun run preview --port 5177      # in dashboard/
    python scripts/verify_dashboard.py
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

from fake_video import write_y4m

URL = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:5177/'
SHOTS = Path(tempfile.gettempdir()) / 'opencode'


def main() -> int:
    failures: list[str] = []
    page_errors: list[str] = []
    console_errors: list[str] = []

    # Measured values from data/measurement.json. If these appear on screen, the wiring is real.
    headline = ['117', '8.00 ms', '19 ms']
    drive_range = re.compile(r'67[–-]6,719')
    sources = ['19,267', '41.4%', '52.2%', '97.5%']

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1500, 'height': 1150})
        page.on('pageerror', lambda e: page_errors.append(str(e)))
        page.on('console', lambda m: console_errors.append(m.text) if m.type == 'error' else None)

        page.goto(URL, wait_until='networkidle')
        page.wait_for_timeout(3000)

        # 1. Default view carries the headline measurement.
        text = page.inner_text('body')
        page.screenshot(path=str(SHOTS / 'verify-default.png'), full_page=True)
        missing = [n for n in headline if n not in text]
        if missing:
            failures.append(f'default view missing headline values: {missing}')
        if not drive_range.search(text):
            failures.append('drive range not rendered from the measured sweep')
        print(f'default    {"OK" if not missing else "MISSING " + str(missing)}')

        # 2. The loading state must resolve rather than stick.
        if 'loading measurement' in text:
            failures.append('still showing the loading state after 3 s')

        # 3. Data disclosure expands and carries the sources.
        toggle = page.get_by_role('button', name='show data & sources', exact=True)
        if toggle.count() == 0:
            failures.append('data disclosure toggle not found')
        else:
            if toggle.get_attribute('aria-expanded') != 'false':
                failures.append('disclosure does not report aria-expanded=false when collapsed')
            toggle.click()
            page.wait_for_timeout(800)
            expanded = page.inner_text('body')
            page.screenshot(path=str(SHOTS / 'verify-data.png'), full_page=True)
            gone = [n for n in sources if n not in expanded]
            if gone:
                failures.append(f'data view missing source values: {gone}')
            print(f'data       {"OK" if not gone else "MISSING " + str(gone)}')

            # Charts are canvas/SVG with no text, so each needs a table alternative.
            for caption in ('Response versus measurement window',
                            'DNp01 spike count versus number of lobula plate neurons driven'):
                if caption not in expanded:
                    failures.append(f'chart has no text alternative: {caption!r}')

        # 4. Accessibility affordances that are easy to regress.
        if page.get_by_role('img', name='Procedural fruitfly').count() == 0:
            failures.append('3D canvas has no accessible label')
        if page.get_by_role('group', name='synthetic stimulus playback').count() == 0:
            failures.append('playback controls have no accessible group label')

        # 5. Camera mode drives the live encoder.
        #
        # This needs its own browser: --use-file-for-fake-video-capture is a LAUNCH option, not a
        # context option. Creating a context with permissions=['camera'] on an ordinary browser
        # gets whatever the host has, which is usually nothing.
        clip = write_y4m(Path(tempfile.gettempdir()) / 'verify-face.y4m', 'face')
        cam_browser = p.chromium.launch(args=[
            '--use-fake-ui-for-media-stream',
            '--use-fake-device-for-media-stream',
            f'--use-file-for-fake-video-capture={clip}',
        ])
        cam_ctx = cam_browser.new_context(
            viewport={'width': 1500, 'height': 1150}, permissions=['camera'],
        )
        cam = cam_ctx.new_page()
        cam.on('pageerror', lambda e: page_errors.append(str(e)))
        cam.goto(URL, wait_until='networkidle')
        cam.wait_for_timeout(2500)
        cam.get_by_role('button', name='use camera', exact=True).click()
        cam.wait_for_timeout(5000)
        cam_text = cam.inner_text('body')
        cam.screenshot(path=str(SHOTS / 'verify-camera.png'), full_page=True)

        for label in ('T4/T5 (13,595)', 'LPLC2 (185)', 'DNp01 (2)'):
            if label not in cam_text:
                failures.append(f'camera mode missing raster row {label!r}')

        # A real subject must produce at least one input spike.
        m = re.search(r'T4/T5 \(13,595\)\s+(\d+)', cam_text)
        driven = int(m.group(1)) if m else 0
        print(f'camera     T4/T5 driven={driven}')
        if driven <= 0:
            failures.append('camera mode: a moving subject drives no T4/T5 cells')

        # The honest caveat must stay on screen while camera mode is active.
        if 'not measured neural output' not in cam_text:
            failures.append('camera mode dropped the "not measured neural output" caveat')

        cam_browser.close()
        browser.close()

    print()
    print(f'page errors:   {page_errors or "none"}')
    print(f'console errors: {console_errors or "none"}')
    if page_errors:
        failures.append(f'uncaught page errors: {page_errors}')

    if failures:
        print('\nFAIL')
        for f in failures:
            print(f'  {f}')
        return 1

    print('\nPASS: dashboard renders measured values, is accessible, and the camera path drives')
    return 0


if __name__ == '__main__':
    sys.exit(main())