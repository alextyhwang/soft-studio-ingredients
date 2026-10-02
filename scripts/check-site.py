"""Check the published static galleries with Playwright and Python's standard library."""
import hashlib
import json
import sys
from pathlib import Path
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
base = (sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8094').rstrip('/')
evidence = ROOT / '.checks'
evidence.mkdir(exist_ok=True)
def fetch(path):
    with urlopen(base + '/' + path, timeout=45) as response:
        return response.read()
art = json.loads(fetch('ingredients.json'))
catalog = json.loads(fetch('metadata/ingredients.json'))
recipes = json.loads(fetch('metadata/recipes.json'))
assert len(art) == catalog['count'] == 812
assert recipes['count'] == len(recipes['items']) == 809
hashes = {item['id']: item['webp']['sha256'] for item in catalog['items']}
def verify_image(item):
    assert hashlib.sha256(fetch(item['image'])).hexdigest() == hashes[item['id']], item['id']
with ThreadPoolExecutor(max_workers=12) as workers:
    list(workers.map(verify_image, art))
checks = []
with sync_playwright() as runtime:
    for name in ['chromium', 'webkit']:
        browser = getattr(runtime, name).launch()
        for width in [320, 390, 768, 1440]:
            context = browser.new_context(viewport={'width': width, 'height': 844}, is_mobile=width <= 390, has_touch=width <= 390, reduced_motion='reduce')
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(base, wait_until='networkidle')
            page.wait_for_function('document.querySelectorAll("#gallery .card").length === 812')
            assert page.locator('#result-count').inner_text() == '812 of 812 ingredients'
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (name, width, 'landing overflow')
            if width in [390, 1440]:
                page.screenshot(path=str(evidence / f'{name}-{width}-landing.png'))
            page.locator('#search').fill('morning glory')
            assert page.locator('#gallery .card').count() == 1
            page.locator('#gallery .card').click()
            assert page.locator('#detail').evaluate('(node) => node.open')
            assert page.locator('#detail-image').evaluate('(img) => img.complete && img.naturalWidth === 320')
            page.keyboard.press('Escape')
            page.locator('#search').fill('')
            page.locator('a[href="#recipes"]').first.click()
            page.wait_for_function('document.querySelectorAll(".recipe-card").length === 48')
            assert page.locator('#recipe-count').inner_text() == '809 of 809 recipes'
            if width in [390, 1440]:
                page.screenshot(path=str(evidence / f'{name}-{width}-recipes.png'))
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (name, width, 'recipes overflow')
            page.locator('#recipe-more').click()
            assert page.locator('.recipe-card').count() == 96
            page.locator('#recipe-search').fill('Vietnamese veg parcels')
            assert page.locator('.recipe-card').count() == 1
            page.locator('.recipe-card').click()
            assert page.locator('#recipe-detail').evaluate('(node) => node.open')
            assert page.locator('#recipe-detail-title').inner_text() == 'Vietnamese veg parcels'
            assert page.locator('#recipe-ingredients img').count() > 0
            assert page.locator('#recipe-steps li').count() > 0
            assert page.locator('#recipe-source').get_attribute('href').startswith('http')
            for image in page.locator('#recipe-ingredients img').all():
                image.scroll_into_view_if_needed()
                image.evaluate('(img) => img.decode()')
                assert image.evaluate('(img) => img.naturalWidth === 320')
            if width in [390, 1440]:
                page.locator('#recipe-detail').evaluate('(node) => { node.scrollTop = 0; }')
                page.screenshot(path=str(evidence / f'{name}-{width}-recipe.png'))
            page.locator('#recipe-close').click()
            page.locator('#recipe-search').fill('zz-no-such-recipe-zz')
            assert page.locator('#recipe-empty').is_visible()
            page.locator('#recipe-reset').click()
            assert page.locator('.recipe-card').count() == 48
            page.locator('#recipe-tag').select_option(label='Chinese')
            assert 0 < page.locator('.recipe-card').count() <= 48
            page.locator('#recipe-tag').select_option('')
            if width <= 390:
                assert float(page.locator('#recipe-search').evaluate('(node) => parseFloat(getComputedStyle(node).fontSize)')) >= 16
            page.goto(base + '/#recipe=mealdb-52937', wait_until='networkidle')
            page.wait_for_function('document.querySelector("#recipe-detail").open')
            assert page.locator('#recipe-detail-title').inner_text() == 'Jerk chicken with rice & peas'
            page.keyboard.press('Escape')
            assert not page.locator('#recipe-detail').evaluate('(node) => node.open')
            assert not errors, (name, width, errors)
            checks.append({'browser': name, 'width': width, 'status': 'passed'})
            context.close()
        browser.close()
(evidence / 'results.json').write_text(json.dumps({'base': base, 'verifiedImages': 812, 'recipes': 809, 'checks': checks}, indent=2), encoding='utf-8')
print(json.dumps({'base': base, 'verifiedImages': 812, 'recipes': 809, 'browserChecks': len(checks), 'status': 'passed'}))
