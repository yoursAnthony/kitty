"""Делает скриншоты ключевых страниц API через Playwright.

Перед запуском поднять стек: `docker compose up -d --build` (порт 8000 наружу).
Запуск:
    .venv/Scripts/python scripts/screenshots.py
Результаты — в каталог `docs/screenshots/`.
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get('SCREENSHOT_BASE_URL', 'http://127.0.0.1:8000')
OUT_DIR = Path(__file__).resolve().parent.parent / 'docs' / 'screenshots'
OUT_DIR.mkdir(parents=True, exist_ok=True)


def get_token() -> str:
    """Получает JWT-токен alice (предполагается, что seed уже отработал)."""
    body = json.dumps({
        'username': 'alice',
        'password': 'P@ssw0rd!2026Long',
    }).encode('utf-8')
    req = urllib.request.Request(
        f'{BASE_URL}/api/v1/auth/jwt/create/',
        data=body,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    return data['access']


def shot(page, name: str, full_page: bool = True) -> None:
    path = OUT_DIR / f'{name}.png'
    page.screenshot(path=str(path), full_page=full_page)
    print(f'  [ok] {path.relative_to(OUT_DIR.parent.parent)} ({path.stat().st_size} B)')


def main() -> int:
    token = get_token()
    print(f'JWT received (len={len(token)})')

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={'width': 1440, 'height': 900},
            locale='ru-RU',
        )
        page = context.new_page()

        # 1. Swagger UI — компактный кадр верхней части (без бесконечного списка схем)
        print('Swagger UI (top, viewport) ...')
        page.set_viewport_size({'width': 1440, 'height': 1100})
        page.goto(f'{BASE_URL}/api/schema/swagger-ui/', wait_until='networkidle')
        page.wait_for_selector('.swagger-ui', timeout=10000)
        page.wait_for_timeout(800)
        page.evaluate('window.scrollTo(0, 0)')
        page.wait_for_timeout(300)
        shot(page, '01_swagger_ui', full_page=False)

        # 2. Swagger UI — компактный кадр с открытым диалогом «Authorize» (демо JWT в схеме)
        print('Swagger Authorize dialog ...')
        page.set_viewport_size({'width': 1440, 'height': 1100})
        page.goto(f'{BASE_URL}/api/schema/swagger-ui/', wait_until='networkidle')
        page.wait_for_selector('.swagger-ui', timeout=10000)
        page.wait_for_timeout(800)
        try:
            page.click('button.btn.authorize', timeout=3000)
            page.wait_for_selector('.dialog-ux .modal-ux-content', timeout=3000)
            page.wait_for_timeout(400)
        except Exception as exc:
            print(f'  warn: failed to open Authorize dialog: {exc}')
        shot(page, '02_swagger_authorize', full_page=False)
        # Закроем диалог чтобы не мешал следующим скринам
        try:
            page.click('button.btn.modal-btn.auth.btn-done', timeout=1500)
        except Exception:
            pass
        page.set_viewport_size({'width': 1440, 'height': 900})

        # 3. ReDoc — три viewport-кадра, чтобы влезали в A4
        print('ReDoc (top / cats / models) ...')
        page.set_viewport_size({'width': 1440, 'height': 1800})
        page.goto(f'{BASE_URL}/api/schema/redoc/', wait_until='networkidle')
        page.wait_for_selector('redoc', timeout=10000)
        page.wait_for_timeout(2000)

        # Раскрываем навигацию (v1) в левом sidebar, чтобы было видно дерево эндпоинтов
        try:
            page.evaluate(
                "() => { const v1 = [...document.querySelectorAll('label')]"
                ".find(e => e.textContent.trim() === 'v1');"
                " if (v1 && !v1.classList.contains('active')) v1.click(); }"
            )
            page.wait_for_timeout(700)
        except Exception as exc:
            print(f'  warn: failed to expand v1 nav: {exc}')

        # 3a. Верх страницы — логотип + описание + раскрытое дерево навигации в sidebar
        page.evaluate('window.scrollTo(0, 0)')
        page.wait_for_timeout(400)
        shot(page, '03a_redoc_top', full_page=False)

        # 3b. Скроллим к первому эндпоинту /cats/ (главный модуль API)
        try:
            page.evaluate(
                "() => { const el = [...document.querySelectorAll('a')]"
                ".find(e => /v1_cats_list|cats_list/i.test(e.getAttribute('href') || ''));"
                " if (el) el.click(); }"
            )
            page.wait_for_timeout(800)
        except Exception:
            page.evaluate('window.scrollTo(0, 6500)')
        shot(page, '03b_redoc_cats', full_page=False)

        # 3c. Скроллим к блоку моделей данных (Cat / Achievement / Tag schema)
        try:
            page.evaluate(
                "() => { const headers = [...document.querySelectorAll('h2, h3, h5')];"
                " const target = headers.find(e => /\\bCat\\b/i.test(e.textContent.trim())"
                "                                  && !/cats_/i.test(e.textContent));"
                " if (target) target.scrollIntoView({block:'start'}); else"
                " window.scrollTo(0, document.body.scrollHeight - 1800); }"
            )
            page.wait_for_timeout(700)
        except Exception:
            page.evaluate('window.scrollTo(0, document.body.scrollHeight - 1800)')
        shot(page, '03c_redoc_schemas', full_page=False)

        # 4. JSON-список котов в браузере (BrowsableAPI у DRF не включён,
        # но можно показать сырое JSON-представление)
        print('Cats list (raw JSON) ...')
        page.goto(f'{BASE_URL}/api/v1/cats/?format=json', wait_until='networkidle')
        shot(page, '04_cats_list_json', full_page=False)

        # 5. Admin: список котов после логина (живые данные из postgres под docker)
        print('Admin: login + cats list ...')
        page.set_viewport_size({'width': 1440, 'height': 1100})
        page.goto(f'{BASE_URL}/admin/login/', wait_until='networkidle')
        try:
            page.fill('input[name="username"]', 'admin')
            page.fill('input[name="password"]', 'AdminP@ss!2026Long')
            page.click('input[type="submit"]')
            page.wait_for_load_state('networkidle', timeout=8000)
        except Exception as exc:
            print(f'  warn: admin login failed: {exc}')
        page.goto(f'{BASE_URL}/admin/cats/cat/', wait_until='networkidle')
        page.wait_for_timeout(800)
        shot(page, '05_admin_cats_list', full_page=False)

        # 6. Newman HTML report — компактный кадр со сводкой
        report = OUT_DIR.parent / 'newman_report.html'
        if report.exists():
            print('Newman HTML report (top, viewport) ...')
            page.set_viewport_size({'width': 1440, 'height': 1500})
            page.goto(f'file://{report.absolute()}', wait_until='networkidle')
            page.wait_for_timeout(1500)
            page.evaluate('window.scrollTo(0, 0)')
            page.wait_for_timeout(300)
            shot(page, '06_newman_report', full_page=False)
        else:
            print(f'(newman report not found at {report}; skip)')

        browser.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
