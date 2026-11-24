# AZ / TR / RU IPTV siyahısını qurur: yalnız son yoxlamada işlək olan linklər
import json, re, collections, urllib.request

RAW = "https://raw.githubusercontent.com/"
SOURCES = {
    "Azərbaycan": RAW + "iptv-org/iptv/master/streams/az.m3u",
    "Türkiyə":    RAW + "iptv-org/iptv/master/streams/tr.m3u",
    "Rusiya":     RAW + "iptv-org/iptv/master/streams/ru.m3u",
}
FREETV = RAW + "Free-TV/IPTV/master/playlist.m3u8"
FREETV_GROUPS = {"Azerbaijan": "Azərbaycan", "Turkey": "Türkiyə", "Russia": "Rusiya"}
HEALTH = RAW + "dearbulut/iptv/state/health.json"
MIN_SCORE = 60

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "iptv-builder"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read().decode("utf-8", "ignore")

def parse(text):
    out, lines, i = [], text.splitlines(), 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#EXTINF"):
            extra, j = [], i + 1
            while j < len(lines) and lines[j].startswith("#"):
                extra.append(lines[j]); j += 1
            if j < len(lines) and lines[j].strip():
                g = re.search(r'group-title="([^"]*)"', line)
                t = re.search(r'tvg-id="([^"]*)"', line)
                out.append({"extinf": line, "extra": extra, "url": lines[j].strip(),
                            "name": line.split(",", 1)[-1].strip(),
                            "group": g.group(1) if g else "", "tid": t.group(1) if t else ""})
            i = j + 1
        else:
            i += 1
    return out

def key(s):
    if s["tid"]:
        return s["tid"].split("@")[0].lower()
    n = re.sub(r"\[.*?\]|\(.*?\)", "", s["name"]).lower()
    n = re.sub(r"\b(hd|sd|fhd|4k)\b", "", n)
    return re.sub(r"[^a-z0-9а-яçəğıöşü]", "", n)

def clean(n):
    return re.sub(r"\s*\[(Geo-blocked|Not 24/7)\]", "", n).strip()

health = {h["url"]: h for h in json.loads(get(HEALTH))}
cands = collections.defaultdict(list)
for label, url in SOURCES.items():
    cands[label] += parse(get(url))
for s in parse(get(FREETV)):
    if s["group"] in FREETV_GROUPS:
        cands[FREETV_GROUPS[s["group"]]].append(s)

lines = ["#EXTM3U"]
for label in ["Azərbaycan", "Türkiyə", "Rusiya"]:
    groups = collections.defaultdict(list)
    for s in cands[label]:
        groups[key(s)].append(s)
    chosen = []
    for ss in groups.values():
        ok = [(s, health[s["url"]]) for s in ss
              if s["url"] in health and health[s["url"]]["status"] == "online"
              and health[s["url"]]["score"] >= MIN_SCORE]
        if ok:
            chosen.append(max(ok, key=lambda x: x[1]["score"])[0])
    chosen.sort(key=lambda s: clean(s["name"]).lower())
    for s in chosen:
        head = re.sub(r'\s*group-title="[^"]*"', "", s["extinf"]).rsplit(",", 1)[0].rstrip()
        lines.append(f'{head} group-title="{label}",{clean(s["name"])}')
        lines += s["extra"]
        lines.append(s["url"])
    print(label, len(chosen))

if len(lines) < 50:
    raise SystemExit("Too few channels, keeping the old list")
open("azrutr.m3u", "w", encoding="utf-8").write("\n".join(lines) + "\n")
