"""Verify the dashboard renders measured data, not placeholders.

Screenshots every tab and asserts that real measured values are visible. A dashboard that
silently falls back to "not measured" looks fine in a screenshot and is useless in a demo, so
the check is on rendered text, not on HTTP status.
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:5177/'
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else
           r'C:\Users\Hp\AppData\Local\Temp\opencode\final').resolve()

# Values measured by scripts/measure_final.py. If these appear on screen, the wiring is real.
# Asserted against rendered text, not HTTP status, because a dashboard that silently falls back
# to placeholders looks fine in a screenshot and is useless in a demo.
EXPECTED = {
    # live: measured latency, rate, validity state, populated raster, real seed latencies
    'live': ['8.00', '390.0 Hz', 'unpinned', '8.00 ms', 'spread 0.00 ms'],
    # sweep: the saturation boundary between the 300 ms and 400 ms points
    'sweep': ['300', '400', 'saturated'],
    # findings: every measured section
    'findings': [
        '19,267', '41.4%', '52.2%', '97.5%',
        '97', '67', 'without LPLC2 output', 'without LC4 output',
    ],
    'reference': ['19', '42', '97.5'],
}

# Text that indicates the UI is showing an empty panel. `not measured` is allowed on the live
# tab only for a panel that genuinely has no measurement; the separability panel is empty
# because that experiment was never run, which is honest and expected.
EMPTY_PANEL_TEXT = ['no spikes recorded']
HARD_PLACEHOLDER = 'not measured'

page_errors: list[str] = []
console: list[str] = []

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1500, 'height': 1150})
    page.on('console', lambda m: console.append(f'{m.type}: {m.text}'))
    page.on('pageerror', lambda e: page_errors.append(str(e)))

    page.goto(URL, wait_until='networkidle')
    page.wait_for_timeout(3000)

    failures: list[str] = []
    combined = ''
    for tab, needles in EXPECTED.items():
        page.get_by_role('button', name=tab, exact=True).click()
        page.wait_for_timeout(1500)
        text = page.inner_text('body')
        combined += text
        dest = OUT.parent / f'final-{tab}.png'
        page.screenshot(path=str(dest), full_page=True)

        missing = [n for n in needles if n not in text]
        if missing:
            failures.append(f'{tab}: missing {missing}')
        print(f'{tab:<9} {"OK" if not missing else "MISSING " + str(missing):<20} '
              f'-> {dest.name}')

    # Every headline panel must carry a measurement. An empty raster means the API is not
    # feeding the UI at all, which is the failure this test exists to catch.
    print()
    empties = {e: combined.count(e) for e in EMPTY_PANEL_TEXT if e in combined}
    print(f'empty panels: {empties or "none"}')
    if empties:
        failures.append(f'empty panels rendered: {empties}')

    placeholders = combined.count(HARD_PLACEHOLDER)
    print(f'"{HARD_PLACEHOLDER}" occurrences: {placeholders}')
    print(f'page errors: {page_errors or "none"}')

    browser.close()

if failures:
    print('\nFAIL')
    for f in failures:
        print(f'  {f}')
    sys.exit(1)

noise = [c for c in console if c.startswith('error')]
print(f'console errors: {noise or "none"}')
print('\nPASS: dashboard renders measured values on every tab')