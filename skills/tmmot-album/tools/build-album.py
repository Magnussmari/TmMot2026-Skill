#!/usr/bin/env python3
# @orchestrator: Magnús Smárason | smarason.is  @created: 2026-06-13
# Byggir index.qmd (hrátt LaTeX, LIQUID-GLASS hönnunarmál) úr ../data.json + photos.json.
# - Velur myndir per leik, afritar með RÉTTRI snúningi (EXIF) + minnkun í img/
# - Gefur út einn {=latex} blokk með \glasscover/\dayhead/\gamehead/\glassphoto/\lead úr _brand.tex
# Render:  quarto render index.qmd
import json, pathlib
from collections import defaultdict
from PIL import Image, ImageOps

DIR = pathlib.Path(__file__).parent
DATA = json.loads((DIR.parent/"data.json").read_text())
PHOTOS = json.loads((DIR/"photos.json").read_text())
IMG = DIR/"img"; IMG.mkdir(exist_ok=True)
PER_GAME = 3
AROUND_MAX = 22
MAXPX = 2000

def tex(s):
    """escape LaTeX-sérstafir í kvikum texta."""
    if s is None: return ""
    for a, b in [("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"),
                 ("#", r"\#"), ("_", r"\_"), ("$", r"\$"),
                 ("{", r"\{"), ("}", r"\}"), ("~", r"\textasciitilde{}"),
                 ("^", r"\textasciicircum{}")]:
        s = s.replace(a, b)
    return s

by_game = defaultdict(list)
for p in PHOTOS:
    by_game[p["game_id"]].append(p)
for g in by_game.values():
    g.sort(key=lambda x: x["dt"] or "")

_done = {}
def place(photo, tag, idx):
    src = pathlib.Path(photo["path"])
    if not src.exists(): return None
    out = IMG/f"{tag}-{idx:02d}.jpg"
    try:
        if str(src) in _done:
            im = Image.open(IMG/_done[str(src)])
        else:
            im = Image.open(src); im = ImageOps.exif_transpose(im)
            im.thumbnail((MAXPX, MAXPX))
            if im.mode != "RGB": im = im.convert("RGB")
            _done[str(src)] = out.name
        im.save(out, "JPEG", quality=86, optimize=True)
    except Exception as e:
        print("WARN", src.name, e); return None
    return f"img/{out.name}"

def evenly(lst, n):
    if len(lst) <= n: return lst
    step = len(lst)/n
    return [lst[int(i*step)] for i in range(n)]

ka2 = next(t for t in DATA["analysis"]["ka_family"] if t["name"] == "KA-2")
id_by_opp = {}
for m in DATA["matches"]:
    opp = m["away"] if m["home"] == "KA-2" else m["home"]
    id_by_opp[opp] = m["id"]
RES = {"S": "sigur", "J": "jafntefli", "T": "tap"}
DAYNAME = {"Fim": "Fimmtudagur", "Fös": "Föstudagur", "Lau": "Laugardagur"}
DAYSUB = {"Fim": "Fyrsti dagur — þrír sigrar", "Fös": "Annar dagur — eldskírnin",
          "Lau": "Lokadagurinn"}

L = []
def w(s=""): L.append(s)

# ---- skjal ----
w("---\nformat: pdf\n---\n")
w("```{=latex}")

# KÁPA — forsíðumynd valin af Magnúsi (img/forsida.jpg), öll andlit sýnileg
cover = "img/forsida.jpg" if (DIR/"img"/"forsida.jpg").exists() else None
if cover:
    w(f"\\glasscover{{{cover}}}")

# FORMÁLI
story = DATA.get("story", {})
w(f"\\dayhead{{Minningabók}}{{{tex(story.get('eyebrow','Mótinu lokið'))}}}")
w("\\goldrule")
w(tex(story.get("text","")))
w("")
w(f"\\lead{{{tex(story.get('hype',''))}}}")
w("\\clearpage")

# DAGAR → LEIKIR
games_by_day = defaultdict(list)
for m in ka2["matches"]:
    games_by_day[m["day"]].append(m)
for m in DATA["matches"]:
    if m.get("tbd_time"):
        opp = m["away"] if m["home"]=="KA-2" else m["home"]
        games_by_day["Lau"].append({"day":"Lau","time":"—","opp":opp,
            "gf":m["result"]["home"],"ga":m["result"]["away"],
            "res":"S" if m["result"]["home"]>m["result"]["away"] else "T" if m["result"]["home"]<m["result"]["away"] else "J",
            "_uppgjor":True})

for day in ("Fim","Fös","Lau"):
    if day not in games_by_day: continue
    w(f"\\dayhead{{{DAYNAME[day]}}}{{{tex(DAYSUB[day])}}}")
    for m in games_by_day[day]:
        gid = id_by_opp.get(m["opp"]) or ("ir-uppgjor" if m.get("_uppgjor") else m["opp"].lower().replace(" ","-"))
        score = f"{m['gf']}\\,–\\,{m['ga']}"
        tag = "Uppgjörsleikur" if m.get("_uppgjor") else f"kl. {m['time']}"
        w(f"\\gamehead{{KA-2 \\textendash\\ {tex(m['opp'])}}}{{{score}}}")
        w(f"\\meta{{{tex(tag)} \\, · \\, {RES.get(m['res'],'')}}}")
        pics = evenly(by_game.get(gid, []), PER_GAME)
        for i,ph in enumerate(pics):
            rel = place(ph, gid.replace("/","-").replace("ð","d").replace("æ","ae"), i)
            if rel:
                w(f"\\glassphoto{{{rel}}}{{KA-2 gegn {tex(m['opp'])}}}")
        if not pics:
            w("\\par\\smallskip{\\sffamily\\small\\itshape\\color{mute}Engar tímastimplaðar myndir úr þessum leik.}\\par")
    w("\\clearpage")

# LOKASTAÐAN
a = DATA["analysis"]["ka2"]
w("\\dayhead{Lokastaðan}{Tíu leikir, þrír dagar}")
w("\\goldrule")
w(f"KA-2 lék \\textbf{{10 leiki á þremur dögum}}: \\textbf{{{a['w']} sigrar}}, {a['l']} töp, "
  f"markatala \\textbf{{{a['gf']}\\,–\\,{a['ga']}}} (að uppgjörsleik meðtöldum).")
w("\\par\\medskip")
for day in ("Fim","Fös","Lau"):
    w(f"\\par\\smallskip\\eyebrow{{{DAYNAME[day]}}}\\par\\vspace{{1mm}}")
    for m in games_by_day.get(day,[]):
        res = RES.get(m['res'],'')
        w(f"{{\\disp {tex(m['opp'])}}}\\,\\dotfill\\,{{\\color{{gold}}{m['gf']}\\,–\\,{m['ga']}}}\\;{{\\sffamily\\footnotesize\\color{{mute}}{res}}}\\par")
w("\\clearpage")

# KVEÐJUR
kv = DATA.get("kvedja",{})
if kv.get("team"):
    w("\\dayhead{Kveðja}{Til stelpnanna}")
    w("\\goldrule")
    w(f"\\lead{{{tex(kv['team'])}}}")
    w("\\par\\bigskip")
if kv.get("pabbi"):
    w(f"\\par\\eyebrow{{{tex(kv.get('pabbi_label',''))}}}\\par\\vspace{{2mm}}")
    w(tex(kv["pabbi"]))
    w("")
    w(f"\\sign{{{tex(kv.get('pabbi_sign',''))}}}")
w("\\clearpage")

# UMGJÖRÐ
around = evenly(by_game.get("around",[]), AROUND_MAX)
if around:
    w("\\dayhead{Umgjörðin}{Ferðin, hraunið og hópurinn}")
    w("\\goldrule")
    for i,ph in enumerate(around):
        rel = place(ph, "around", i)
        if rel:
            w(f"\\glassphoto{{{rel}}}{{}}")

w("```")
(DIR/"index.qmd").write_text("\n".join(L)+"\n")
print(f"index.qmd skrifað — {len(_done)} einstakar myndir í img/ | umgjörð: {len(around)}")
