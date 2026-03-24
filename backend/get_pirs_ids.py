from playwright.sync_api import sync_playwright

LAWS = {
    "ZDR-1":   "ZAKO5944",
    "ZPP":     "ZAKO3210",
    "ZGD-1":   "ZAKO4291",
    "ZIZ":     "ZAKO3351",
    "SPZ":     "ZAKO3242",
    "KZ-1":    "ZAKO5019",
    "ZKP":     "ZAKO1588",
    "ZN":      "ZAKO1198",
    "ZVPot-1": "ZAKO7840",
    "ZLS":     "ZAKO408",
    "ZUstS":   "ZAKO1260",
}

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    ids = {}
    for kratice, zako_id in LAWS.items():
        page.goto(f"https://pisrs.si/pregledPredpisa?id={zako_id}")
        page.wait_for_load_state("networkidle")
        # Ujame vse klice na integracije
        requests = page.evaluate("""() => {
            return window.performance.getEntriesByType('resource')
                .filter(r => r.name.includes('/api/datoteke/integracije/'))
                .map(r => r.name);
        }""")
        for url in requests:
            num_id = url.split('/')[-1]
            if num_id.isdigit():
                ids[kratice] = num_id
                break
        print(f"{kratice}: {ids.get(kratice, 'NOT FOUND')}")
    browser.close()
