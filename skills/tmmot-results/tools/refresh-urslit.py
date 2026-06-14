# @orchestrator: Magnús Smárason | smarason.is  @created: 2026-06-12
# Sækir opinber úrslit TM-mótsins (urslit.tmmotid.is), skrifar CSV + reiknar
# gagnagreiningu inn í data.json. Idempotent: exit 0 = óbreytt, exit 3 = breytt.
# Heiðarleikaregla: AÐEINS spilaðir leikir telja; engin ágiskun.
import json, re, csv, sys, urllib.request, datetime, pathlib

DIR = pathlib.Path(__file__).parent
UA = {"User-Agent": "Mozilla/5.0 (ka2.sumarhus.com foreldrasvaedi)"}
DAYS = [("fimmtudagur", "A"), ("föstudagur", "B"), ("laugardagur", "C")]
ROW = re.compile(
    r'<tr>\s*<td class="searchable">([^<]*)</td>\s*<td class="searchable">([^<]*)</td>'
    r'\s*<td class="searchable">([^<]*)</td>\s*<td class="searchable">([^<]*)</td>'
    r'\s*<td class="searchable">([^<]*)</td>\s*<td>([^<]*)</td>\s*<td>([^<]*)</td>')

rows = []
for day, code in DAYS:
    html = urllib.request.urlopen(urllib.request.Request(
        f"https://urslit.tmmotid.is/index?day={code}", headers=UA), timeout=20).read().decode("utf-8", "replace")
    for m in ROW.finditer(html):
        g, t, v, home, away, hs, as_ = [x.strip() for x in m.groups()]
        if not g or not home:
            continue
        rows.append(dict(day=day, group=g, time=t, venue=v, home=home, away=away,
                         hs=int(hs) if hs.isdigit() else None,
                         as_=int(as_) if as_.isdigit() else None))
if len(rows) < 100:
    print(f"VARÚÐ: aðeins {len(rows)} raðir — vefur breyttur? Hætti án breytinga.")
    sys.exit(1)

# ---- ÚRSLITAKEPPNIN (jafningjaleikir / TM Mótsbikarinn) — aðskilin tafla, annað snið ----
# Dálkar: Völlur · kl. · Riðill · Lið · Riðill · Lið · Úrslit("h:a"). Þetta er ENDIR margra liða.
PLAY = re.compile(
    r'<tr[^>]*>\s*<td[^>]*>([^<]*)</td>\s*<td[^>]*>([^<]*)</td>\s*<td[^>]*>([^<]*)</td>'
    r'\s*<td[^>]*>([^<]*)</td>\s*<td[^>]*>([^<]*)</td>\s*<td[^>]*>([^<]*)</td>\s*<td[^>]*>([^<:]*):([^<]*)</td>')
try:
    ph = urllib.request.urlopen(urllib.request.Request(
        "https://urslit.tmmotid.is/index/jafningjaleikir", headers=UA), timeout=20).read().decode("utf-8", "replace")
    for m in PLAY.finditer(ph):
        v, t, _gh, home, _ga, away, hs, as_ = [x.strip() for x in m.groups()]
        if not home or not away:
            continue
        rows.append(dict(day="laugardagur", group="Mótsbikarinn", time=t, venue=v + " · TM Mótsbikarinn",
                         home=home, away=away,
                         hs=int(hs) if hs.isdigit() else None, as_=int(as_) if as_.isdigit() else None))
except Exception as e:
    print(f"VARÚÐ: náði ekki í jafningjaleiki ({e}) — held áfram með riðlana.")

played = [r for r in rows if r["hs"] is not None and r["as_"] is not None]

# ---- CSV (gated download á síðunni) ----
with open(DIR / "public" / "urslit.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["dagur", "riðill", "tími", "völlur", "heimalið", "útilið", "mörk_heima", "mörk_úti"])
    for r in rows:
        w.writerow([r["day"], r["group"], r["time"], r["venue"], r["home"], r["away"],
                    "" if r["hs"] is None else r["hs"], "" if r["as_"] is None else r["as_"]])

# ---- liðatöflur úr spiluðum leikjum ----
teams = {}
def T(n):
    return teams.setdefault(n, dict(p=0, w=0, d=0, l=0, gf=0, ga=0))
for r in played:
    h, a = T(r["home"]), T(r["away"])
    h["p"] += 1; a["p"] += 1
    h["gf"] += r["hs"]; h["ga"] += r["as_"]; a["gf"] += r["as_"]; a["ga"] += r["hs"]
    if r["hs"] > r["as_"]: h["w"] += 1; a["l"] += 1
    elif r["hs"] < r["as_"]: a["w"] += 1; h["l"] += 1
    else: h["d"] += 1; a["d"] += 1

full = {n: s for n, s in teams.items() if s["p"] >= 3}  # heill dagur spilaður
ka = teams.get("KA-2")
goals = sum(r["hs"] + r["as_"] for r in played)
perfect = [n for n, s in full.items() if s["w"] == s["p"]]
ga_better = sum(1 for s in full.values() if s["ga"] < ka["ga"])  # færri mörk fengin en KA-2
gf_avg = round(sum(s["gf"] for s in full.values()) / max(1, len(full)), 1)
top = max(played, key=lambda r: r["hs"] + r["as_"])

analysis = {
    "asof": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:00Z"),
    "played": len(played), "goals": goals,
    "avg": round(goals / max(1, len(played)), 1),
    "teams": len(teams),
    "perfect_count": len(perfect), "full_teams": len(full),
    "ka2": None if not ka else {
        "gf": ka["gf"], "ga": ka["ga"], "w": ka["w"], "d": ka["d"], "l": ka["l"], "p": ka["p"],
        "perfect": ka["w"] == ka["p"] and ka["p"] >= 3,
        "def_beaten_by": ga_better, "gf_avg_all": gf_avg,
        "def_pct": round(100 * (1 - ga_better / max(1, len(full)))),
    },
    "fun": [
        {"label": "Markahæsti leikur mótsins", "value": f"{top['home']} – {top['away']} {top['hs']}–{top['as_']} ({top['hs']+top['as_']} mörk, riðill {top['group']})"},
        {"label": "Vellirnir í Eyjum", "value": f"{len(set(r['venue'] for r in rows))} vellir í notkun samtímis"},
    ],
}

# ---- hin KA-liðin (KA-1/3/4) — allir leikir beggja daga ----
ka_family = []
for name in sorted(n for n in teams if re.fullmatch(r"KA-\d", n)):
    ms = []
    for r in rows:
        if name not in (r["home"], r["away"]):
            continue
        mine_home = r["home"] == name
        gf_ = r["hs"] if mine_home else r["as_"]
        ga_ = r["as_"] if mine_home else r["hs"]
        res = None if gf_ is None else ("S" if gf_ > ga_ else "T" if gf_ < ga_ else "J")
        ms.append({"day": {"fimmtudagur": "Fim", "föstudagur": "Fös", "laugardagur": "Lau"}[r["day"]], "time": r["time"],
                   "opp": r["away"] if mine_home else r["home"], "gf": gf_, "ga": ga_, "res": res})
    s = teams[name]
    ka_family.append({"name": name, "rec": {"w": s["w"], "d": s["d"], "l": s["l"], "gf": s["gf"], "ga": s["ga"]}, "matches": ms})
analysis["ka_family"] = ka_family

# ---- data.json: greining + KA-2 úrslit + B08 riðilsúrslit ----
data = json.loads((DIR / "data.json").read_text())
before = json.dumps(data, sort_keys=True, ensure_ascii=False)
# asof er sveiflukennt — haltu gamla stimplinum í samanburðinum svo diff sé efnislegt
old_asof = (data.get("analysis") or {}).get("asof")
if old_asof:
    analysis["asof"] = old_asof
data["analysis"] = analysis

by_key = {(r["home"], r["away"]): r for r in played}
for m in data["matches"]:
    r = by_key.get((m["home"], m["away"]))
    if r and not m.get("result"):
        m["result"] = {"home": r["hs"], "away": r["as_"]}

grp = [r for r in played if r["group"] == data.get("group")]
have = {(g["home"], g["away"]) for g in data["groupResults"]}
for r in grp:
    if (r["home"], r["away"]) not in have:
        data["groupResults"].append({"home": r["home"], "away": r["away"], "hs": r["hs"], "as": r["as_"]})

after = json.dumps(data, sort_keys=True, ensure_ascii=False)
if after != before:
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:00Z")
    data["analysis"]["asof"] = now
    data["updated"] = now
    (DIR / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(f"BREYTT: {len(played)} spilaðir, {data.get('group')}={len(grp)}, KA-2 úrslit={sum(1 for m in data['matches'] if m.get('result'))}")
    sys.exit(3)
print(f"Óbreytt: {len(played)} spilaðir, {data.get('group')}={len(grp)}")
sys.exit(0)
