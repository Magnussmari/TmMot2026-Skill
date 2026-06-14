#!/usr/bin/env python3
# @orchestrator: Magnús Smárason | smarason.is  @created: 2026-06-14
# Beitir selection.json (frá editor.py): vinnur forsíðu + gallerí, byggir PDF,
# uppfærir síðu-gallerí (data.json) og deployar á VM. Kallað af editor.py.
import json, pathlib, subprocess, os
from PIL import Image, ImageOps

DIR = pathlib.Path(__file__).parent
APP = DIR.parent
RAW = pathlib.Path.home()/"Pictures"/"Eyjamot-2026-final"/"raw"
MEDIA = APP/"public"/"media"; MEDIA.mkdir(parents=True, exist_ok=True)
IMG = DIR/"img"; IMG.mkdir(exist_ok=True)
VM = "user@your-server.example"

sel = json.loads((DIR/"selection.json").read_text())
raw_by_stem = {p.stem: p for p in RAW.glob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png")}

def proc(stem, dest, maxpx, q=88):
    src = raw_by_stem.get(stem)
    if not src or not src.exists():
        return False
    im = Image.open(src); im = ImageOps.exif_transpose(im)
    if im.mode != "RGB": im = im.convert("RGB")
    im.thumbnail((maxpx, maxpx))
    im.save(dest, "JPEG", quality=q, optimize=True)
    return True

# 1) forsíða → album/img/forsida.jpg
if sel.get("cover"):
    proc(sel["cover"], IMG/"forsida.jpg", 2400, 92)

# 2) gallerí → public/media/g01..gNN.jpg + data.json
old = list(MEDIA.glob("g*.jpg"))
for f in old: f.unlink()
gallery = []
for i, stem in enumerate(sel.get("gallery", []), 1):
    if proc(stem, MEDIA/f"g{i:02d}.jpg", 1280, 84):
        gallery.append({"src": f"/media/g{i:02d}.jpg", "cap": ""})
data = json.loads((APP/"data.json").read_text())
data["gallery"] = gallery
(APP/"data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

# 3) byggja PDF
env = dict(os.environ, PATH="/Library/TeX/texbin:" + os.environ.get("PATH", ""))
subprocess.run(["python3", str(DIR/"build-album.py")], check=True, cwd=DIR)
subprocess.run(["quarto", "render", "index.qmd", "--to", "pdf"], check=True, cwd=DIR, env=env)
pdf = DIR/"_book"/"Saga-KA2-TM-motid-2026.pdf"
if pdf.exists():
    (MEDIA/"saga-ka2.pdf").write_bytes(pdf.read_bytes())

# 4) deploy á VM (best-effort)
try:
    subprocess.run(["scp", "-q", str(APP/"data.json"), f"{VM}:~/ka2-eyjamot/data.json"], check=True, timeout=60)
    for f in MEDIA.glob("g*.jpg"):
        subprocess.run(["scp", "-q", str(f), f"{VM}:~/ka2-eyjamot/public/media/{f.name}"], check=True, timeout=60)
    subprocess.run(["scp", "-q", str(MEDIA/"saga-ka2.pdf"), f"{VM}:~/ka2-eyjamot/public/media/saga-ka2.pdf"], check=True, timeout=120)
    subprocess.run(["ssh", VM, "cd ~/ka2-eyjamot && docker compose up -d --build"], check=True, timeout=180)
    print(f"BÚIÐ — forsíða + {len(gallery)} gallerí-myndir, PDF byggt og deployað á ka2.sumarhus.com")
except Exception as e:
    print(f"Staðbundið búið ({len(gallery)} myndir, PDF), EN deploy mistókst: {e}")
