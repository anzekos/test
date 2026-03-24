import urllib.request, json
with open("zako5944.json", "w", encoding="utf-8") as f:
    r = urllib.request.urlopen("https://pisrs.si/api/rezultat/zbirka/id/ZAKO5944").read().decode("utf-8")
    json.dump(json.loads(r), f, indent=2, ensure_ascii=False)
