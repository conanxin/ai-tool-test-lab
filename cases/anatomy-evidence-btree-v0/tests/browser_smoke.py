"""Optional real-browser smoke gate (requires Python playwright and installed Chromium)."""
from pathlib import Path
import re
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
# Inline harness because this execution environment blocks localhost browser navigation.
# The same app/model sources are used; remove ESM syntax only for the no-network fixture.
html = (root / 'index.html').read_text(encoding='utf-8')
css = (root / 'src/styles.css').read_text(encoding='utf-8')
btree = re.sub(r'^export ', '', (root / 'src/btree.mjs').read_text(encoding='utf-8'), flags=re.M)
app = re.sub(r'^import .*?;\s*', '', (root / 'src/app.mjs').read_text(encoding='utf-8'), count=1, flags=re.M)
html = html.replace('<link rel="stylesheet" href="./src/styles.css" />', '<style>' + css + '</style>')
html = html.replace('<script type="module" src="./src/app.mjs"></script>', '<script>' + btree + '\n' + app + '</script>')
out = root / 'assets'
out.mkdir(exist_ok=True)

try:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        page = browser.new_page(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.set_content(html, wait_until='load')
        assert page.locator('#node-count').inner_text() == '9'
        assert page.locator('#key-count').inner_text() == '18'
        assert page.locator('#btree-svg g[aria-label^="节点"]').count() == 9
        page.locator('#query-key').fill('55')
        page.locator('#search-btn').click()
        assert '步骤 1 /' in page.locator('#trace-count').inner_text()
        for _ in range(20):
            if page.locator('#next-btn').is_disabled(): break
            page.locator('#next-btn').click()
        assert '命中' in page.locator('#trace-text').inner_text()
        page.locator('#query-key').fill('57')
        page.locator('#search-btn').click()
        for _ in range(20):
            if page.locator('#next-btn').is_disabled(): break
            page.locator('#next-btn').click()
        assert '未命中' in page.locator('#trace-text').inner_text()
        page.locator('#insert-btn').click()
        assert page.locator('#key-count').inner_text() == '19'
        page.locator('#search-btn').click()
        for _ in range(20):
            if page.locator('#next-btn').is_disabled(): break
            page.locator('#next-btn').click()
        assert '命中' in page.locator('#trace-text').inner_text()
        page.locator('#reset-btn').click()
        assert page.locator('#key-count').inner_text() == '18'
        page.locator('[data-example="45"]').click()
        assert page.locator('#trace-count').inner_text().startswith('步骤 1 /')
        page.locator('.diagram').focus()
        page.keyboard.press('ArrowRight')
        assert page.locator('#trace-count').inner_text().startswith('步骤 2 /')
        page.locator('#query-key').fill('1.5')
        page.locator('#search-btn').click()
        assert '请输入' in page.locator('#trace-text').inner_text() or page.locator('#query-key').evaluate('(e) => !e.validity.valid')
        page.locator('#reset-btn').click()
        page.screenshot(path=str(out / 'desktop.png'), full_page=True)
        assert not errors, errors
        print('PASS desktop: render/search(hit/miss)/insert/reset/keyboard/no page errors')

        mobile = browser.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=1)
        mobile.set_content(html, wait_until='load')
        overflow = mobile.evaluate('document.documentElement.scrollWidth > window.innerWidth')
        assert not overflow, 'body must fit viewport; SVG may scroll inside diagram'
        assert mobile.locator('.diagram').evaluate('(e)=>e.scrollWidth > e.clientWidth')
        mobile.locator('[data-example="57"]').click()
        assert mobile.locator('#trace-count').inner_text().startswith('步骤 1 /')
        mobile.screenshot(path=str(out / 'mobile.png'), full_page=True)
        print('PASS mobile: 390px viewport, locally scrollable SVG, search')
        browser.close()
finally:
    pass
