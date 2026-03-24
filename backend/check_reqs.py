from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://pisrs.si/pregledPredpisa?id=ZAKO5944")
    page.wait_for_timeout(5000)
    reqs = page.evaluate("() => window.performance.getEntriesByType('resource').map(r => r.name)")
    
    with open("requests.json", "w") as f:
        json.dump(reqs, f, indent=2)
    browser.close()
