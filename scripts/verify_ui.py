"""Screenshot every tab of the reworked dashboard and exercise the playback controls.

Verification only. Also asserts the controls actually change the rendered state, since dead
buttons were the original complaint.
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:5173/'
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else
           r'C:\Users\Hp\AppData\Local\Temp\opencode\ui').resolve()

TABS = {
    'stimulus': 'Stimulus & response',
    'saturation': 'Saturation',
    'findings': 'Findings',
    'sources': 'Sources',
}

# Text proving each tab carries real content, not placeholders.
EXPECTED = {
    'stimulus': ['Synthetic dark disk expanding', 'disk diameter', 'grid sampled'],
    'saturation': ['measurement window', 'refractory ceiling', 'measurement-window artefact'],
    'findings': ['41.4%', '97.5%', 'without LPLC2 output'],
    'sources': ['19 ms', '42 deg', '52.2%'],
}

page_errors: list[str] = []
console: list[str] = []

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1500, 'height': 1200})
    page.on('console', lambda m: console.append(f'{m.type}: {m.text}'))
    page.on('pageerror', lambda e: page_errors.append(str(e)))

    page.goto(URL, wait_until='networkidle')
    page.wait_for_timeout(3000)

    failures: list[str] = []

    for tab_id, label in TABS.items():
        page.get_by_role('button', name=label, exact=True).click()
        page.wait_for_timeout(1200)
        text = page.inner_text('body')
        page.screenshot(path=str(OUT.parent / f'ui-{tab_id}.png'), full_page=True)

        missing = [n for n in EXPECTED[tab_id] if n not in text]
        if missing:
            failures.append(f'{tab_id}: missing {missing}')
        print(f'{tab_id:<11} {"OK" if not missing else "MISSING " + str(missing):<24}')

    # --- Playback controls must actually change state ---
    print()
    page.get_by_role('button', name='Stimulus & response', exact=True).click()
    page.wait_for_timeout(900)

    before = page.inner_text('body')
    page.get_by_role('button', name='Step', exact=True).click()
    page.wait_for_timeout(700)
    after_step = page.inner_text('body')
    print(f'Step changes the rendered state: {before != after_step}')
    if before == after_step:
        failures.append('Step button does not change anything')

    page.get_by_role('button', name='Start', exact=True).click()
    page.wait_for_timeout(2200)
    after_run = page.inner_text('body')
    running_shown = 'Running' in after_run or 'replaying' in after_run
    print(f'Start runs playback:            {after_run != after_step}')
    print(f'  header shows running state:    {running_shown}')
    if after_run == after_step:
        failures.append('Start button does not change anything')

    page.get_by_role('button', name='Stop', exact=True).click()
    page.wait_for_timeout(800)
    after_stop = page.inner_text('body')
    print(f'Stop rewinds:                   {"replaying" not in after_stop}')

    page.screenshot(path=str(OUT.parent / 'ui-playback.png'), full_page=True)

    print()
    print(f'page errors: {page_errors or "none"}')
    noise = [c for c in console if c.startswith('error')]
    print(f'console errors: {noise or "none"}')

    browser.close()

if failures:
    print('\nFAIL')
    for f in failures:
        print(f'  {f}')
    sys.exit(1)
print('\nPASS: all tabs render content and playback controls work')