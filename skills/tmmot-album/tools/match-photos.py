#!/usr/bin/env python3
# @orchestrator: Magnús Smárason | smarason.is  @created: 2026-06-13
# Vörpun mynd→leikur fyrir KA-2 albúmið. Les EXIF-tíma hverrar myndar og finnur
# í hvaða leikglugga hún fellur (kickoff-10mín → kickoff+55mín). Gagnadrifið:
# leikir + tímar koma úr ../data.json (analysis.ka_family["KA-2"] + matches[]).
# Ísland = UTC allt árið. Myndir utan glugga → "around" (umgjörð/ferðin).
#
# Notkun:  python3 match-photos.py [RAW_DIR]
# Útkoma:  photos.json  [{file, dt, game_id, opp, day}]
import json, subprocess, sys, datetime, pathlib, shutil

DIR = pathlib.Path(__file__).parent
RAW = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path.home()/"Pictures"/"Eyjamot-2026-final"/"raw"
DATA = json.loads((DIR.parent/"data.json").read_text())

# Dagur-kóði → dagsetning (Ísland=UTC)
DAYDATE = {"Fim": "2026-06-11", "Fös": "2026-06-12", "Lau": "2026-06-13"}
WIN_BEFORE, WIN_AFTER = 10, 55  # mínútur fyrir/eftir kickoff

# Byggja leikglugga KA-2 úr gögnunum (sami sannleikur og vefurinn)
ka2 = next(t for t in DATA["analysis"]["ka_family"] if t["name"] == "KA-2")
# id úr matches[] (day-C) svo albúm/vefur deili sömu auðkennum
id_by_opp = {}
for m in DATA["matches"]:
    opp = m["away"] if m["home"] == "KA-2" else m["home"]
    id_by_opp[opp] = m["id"]

games = []
for m in ka2["matches"]:
    d = DAYDATE.get(m["day"])
    if not d:
        continue
    hh, mm = m["time"].split(":")
    k = datetime.datetime.fromisoformat(f"{d}T{hh}:{mm}:00+00:00")
    games.append({
        "id": id_by_opp.get(m["opp"], m["opp"].lower().replace(" ", "-")),
        "opp": m["opp"], "day": m["day"],
        "start": k - datetime.timedelta(minutes=WIN_BEFORE),
        "end": k + datetime.timedelta(minutes=WIN_AFTER),
    })
# uppgjörsleikur (tbd_time) — gluggi víður því tími óþekktur (eftir KR til kvölds)
for m in DATA["matches"]:
    if m.get("tbd_time"):
        opp = m["away"] if m["home"] == "KA-2" else m["home"]
        games.append({"id": m["id"], "opp": opp, "day": "Lau",
                       "start": datetime.datetime.fromisoformat("2026-06-13T14:25:00+00:00"),
                       "end": datetime.datetime.fromisoformat("2026-06-13T20:00:00+00:00")})

def exif_dt(path):
    # 1) exiftool (best fyrir HEIC)
    if shutil.which("exiftool"):
        r = subprocess.run(["exiftool", "-s3", "-DateTimeOriginal", "-CreateDate", str(path)],
                           capture_output=True, text=True)
        for line in r.stdout.splitlines():
            line = line.strip()
            if line and line[:4].isdigit():
                try:
                    return datetime.datetime.strptime(line[:19], "%Y:%m:%d %H:%M:%S").replace(tzinfo=datetime.timezone.utc)
                except ValueError:
                    pass
    # 2) Pillow fallback
    try:
        from PIL import Image
        img = Image.open(path); ex = getattr(img, "_getexif", lambda: None)()
        if ex:
            for tag in (36867, 36868, 306):  # DateTimeOriginal, DateTimeDigitized, DateTime
                if tag in ex:
                    return datetime.datetime.strptime(ex[tag][:19], "%Y:%m:%d %H:%M:%S").replace(tzinfo=datetime.timezone.utc)
    except Exception:
        pass
    return None

out = []
files = sorted(p for p in RAW.glob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".heic", ".mp4"))
for f in files:
    dt = exif_dt(f)
    gid, opp, day = "around", None, None
    if dt:
        for g in games:
            if g["start"] <= dt <= g["end"]:
                gid, opp, day = g["id"], g["opp"], g["day"]; break
    out.append({"file": f.name, "path": str(f), "dt": dt.isoformat() if dt else None,
                "game_id": gid, "opp": opp, "day": day})

(DIR/"photos.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
# samantekt
from collections import Counter
c = Counter(o["game_id"] for o in out)
nodt = sum(1 for o in out if not o["dt"])
print(f"{len(out)} myndir → photos.json  | án EXIF-tíma: {nodt}")
for gid, n in c.most_common():
    g = next((x for x in games if x["id"] == gid), None)
    print(f"  {gid:14} {n:3}  {g['opp'] if g else 'umgjörð/ferðin'}")
