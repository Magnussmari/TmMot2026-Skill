# @orchestrator: Magnús Smárason | smarason.is  @created: 2026-06-12
# „Hversu spenntur er Magnús?" — púls af Garmin (InfluxDB á docker-services)
# fyrir gluggann 10 mín fyrir leik → 10 mín eftir leik (kickoff+50 mín alls).
# Keyrir á Mac (þarf tailnet á your-influx-host). Flæði:
#   1) sækja data.json af VM (sannleikurinn — VM-cron skrifar úrslitin þangað)
#   2) spyrja Influx um HR í glugga hvers leiks, vista í data["pulse"]
#   3) exit 3 = breytt (kallari deployar); áminningarpóstur ef sync vantar
import json, subprocess, sys, datetime, pathlib

DIR = pathlib.Path(__file__).parent
VM = "user@your-server.example"
BEFORE_MIN, SPAN_MIN = 10, 50          # gluggi: kickoff-10 → kickoff+50
REMIND_AFTER_MIN = 45                  # áminning ef ekkert sync 45 mín eftir glugga
now = datetime.datetime.now(datetime.timezone.utc)

def sh(*cmd, timeout=30):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

# 1) VM data.json er sannleikurinn
r = sh("ssh", "-o", "ConnectTimeout=10", VM, "cat ~/ka2-eyjamot/data.json", timeout=20)
if r.returncode != 0:
    print("Næ ekki í VM data.json:", r.stderr[:200]); sys.exit(1)
data = json.loads(r.stdout)
before = json.dumps(data.get("pulse", {}), sort_keys=True)
pulse = data.setdefault("pulse", {})

def influx(start, end):
    q = (f"SELECT mean(HeartRate) FROM HeartRateIntraday WHERE "
         f"time >= '{start.strftime('%Y-%m-%dT%H:%M:%SZ')}' AND time <= '{end.strftime('%Y-%m-%dT%H:%M:%SZ')}' "
         f"GROUP BY time(1m) fill(none)")
    r = sh("ssh", "-o", "ConnectTimeout=10", "your-influx-host",
           f'docker exec your-influxdb-container influx -database garmin -execute "{q}" -format csv', timeout=30)
    out = []
    for line in r.stdout.splitlines()[1:]:
        p = line.split(",")
        if len(p) == 3 and p[2]:
            t = datetime.datetime.fromtimestamp(int(p[1]) / 1e9, datetime.timezone.utc)
            out.append((t, round(float(p[2]))))
    return out

# ALLIR 10 leikir KA-2 (úr ka_family + ÍR-uppgjör) — fastir lyklar svo engin
# tvítekning við gömlu færslurnar (selfoss/hamar/hk/fylkir/fh/kr). Ísland=UTC.
DAYDATE = {"Fim": "2026-06-11", "Fös": "2026-06-12", "Lau": "2026-06-13"}
KEYMAP = {"Víkingur-3": "vikingur3", "Haukar-2": "haukar2", "KFA-1": "kfa1",
          "Selfoss-1": "selfoss", "Hamar/Ægir-1": "hamar", "HK-Ísabel Rós": "hk",
          "Fylkir-Signý Lára": "fylkir", "FH-2": "fh", "KR-2": "kr", "ÍR-1": "ir-uppgjor"}
_ka2 = next(t for t in data["analysis"]["ka_family"] if t["name"] == "KA-2")
games_iter = []
for gm in _ka2["matches"]:
    _d = DAYDATE.get(gm["day"])
    if not _d:
        continue
    _ko = datetime.datetime.fromisoformat(f"{_d}T{gm['time']}:00+00:00")
    games_iter.append((KEYMAP.get(gm["opp"], gm["opp"].lower().replace(" ", "")), _ko, gm["opp"]))
for mm in data.get("matches", []):  # ÍR-uppgjör (ekki í ka_family)
    if mm.get("tbd_time"):
        _opp = mm["away"] if mm["home"] == "KA-2" else mm["home"]
        games_iter.append((mm["id"], datetime.datetime.fromisoformat("2026-06-13T15:00:00+00:00"), _opp))

for mid, ko, opp in games_iter:
    if pulse.get(mid, {}).get("complete"):
        continue  # frosið — fullt sett komið
    start, end = ko - datetime.timedelta(minutes=BEFORE_MIN), ko + datetime.timedelta(minutes=SPAN_MIN)
    if now < start:
        continue
    samples = influx(start, end)
    if samples:
        series = [[round((t - start).total_seconds() / 60), hr] for t, hr in samples]
        hrs = [hr for _, hr in samples]
        complete = now > end and (end - samples[-1][0]).total_seconds() < 300
        entry = {"series": series, "max": max(hrs), "avg": round(sum(hrs) / len(hrs)),
                 "label": opp, "complete": complete}
        old = pulse.get(mid, {})
        # asof sveiflukennt — haltu gamla stimplinum ef efnið er ÓBREYTT
        same = old.get("asof") and all(old.get(k) == entry[k] for k in ("series", "max", "avg", "complete"))
        entry["asof"] = old["asof"] if same else now.strftime("%Y-%m-%dT%H:%M:00Z")
        pulse[mid] = entry

if json.dumps(data.get("pulse", {}), sort_keys=True) != before:
    data["updated"] = now.strftime("%Y-%m-%dT%H:%M:00Z")
    (DIR / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print("BREYTT:", {k: (v.get("max"), v.get("complete")) for k, v in pulse.items()})
    sys.exit(3)
# haltu lókal eintaki í takt við VM-sannleikann þótt púls sé óbreyttur
(DIR / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
print("Óbreytt (púls)"); sys.exit(0)
