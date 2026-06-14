#!/usr/bin/env python3
# @orchestrator: Magnús Smárason | smarason.is  @created: 2026-06-14
# MYNDAEDITOR fyrir KA-2 minningabók + síðu-gallerí.
# Staðbundið vef-tól: veldu FORSÍÐU + GALLERÍ úr öllum harvestuðu myndunum,
# smelltu "Vista & byggja" → skrifar selection.json, vinnur myndir, byggir PDF
# og uppfærir síðu-gallerí (data.json). Engin gögn fara út af vélinni.
#
# Keyrsla:  python3 editor.py     → opnaðu http://localhost:8765
import json, pathlib, subprocess, http.server, socketserver, urllib.parse, webbrowser, threading
from PIL import Image, ImageOps

DIR = pathlib.Path(__file__).parent
RAW = pathlib.Path.home()/"Pictures"/"Eyjamot-2026-final"/"raw"
THUMBS = DIR/"_thumbs"; THUMBS.mkdir(exist_ok=True)
SEL = DIR/"selection.json"
PORT = 8765

def gen_thumbs():
    photos = sorted(p for p in RAW.glob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    for p in photos:
        out = THUMBS/(p.stem + ".jpg")
        if not out.exists():
            try:
                im = Image.open(p); im = ImageOps.exif_transpose(im); im.thumbnail((480, 480))
                if im.mode != "RGB": im = im.convert("RGB")
                im.save(out, "JPEG", quality=80)
            except Exception as e:
                print("þumall mistókst", p.name, e)
    return [p.stem for p in photos]

NAMES = gen_thumbs()
print(f"{len(NAMES)} myndir tilbúnar í editorinn")
cur = json.loads(SEL.read_text()) if SEL.exists() else {"cover": None, "gallery": []}

PAGE = """<!doctype html><html lang=is><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>KA-2 myndaeditor</title><style>
*{box-sizing:border-box;margin:0;padding:0}body{background:#0e1836;color:#f4f1e8;font-family:-apple-system,Inter,sans-serif;padding:1rem 1rem 7rem}
h1{font-size:1.3rem;margin-bottom:.3rem}p.sub{color:#8d99b8;margin-bottom:1rem;font-size:.9rem}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:.6rem}
.ph{position:relative;border-radius:.6rem;overflow:hidden;aspect-ratio:1;cursor:pointer;border:3px solid transparent}
.ph img{width:100%;height:100%;object-fit:cover;display:block}
.ph.cover{border-color:#f2b705}.ph.gal{border-color:#43d17c}
.badge{position:absolute;top:.3rem;left:.3rem;background:#43d17c;color:#06210f;font-weight:800;border-radius:99px;min-width:1.5rem;height:1.5rem;display:grid;place-items:center;font-size:.85rem;padding:0 .3rem}
.cbadge{position:absolute;top:.3rem;right:.3rem;background:#f2b705;color:#1a1402;font-weight:800;border-radius:99px;padding:.15rem .5rem;font-size:.72rem}
.bar{position:fixed;left:0;right:0;bottom:0;background:#070d1c;border-top:1px solid #28324f;padding:.9rem 1rem calc(.9rem + env(safe-area-inset-bottom));display:flex;gap:.7rem;align-items:center;flex-wrap:wrap}
.bar b{color:#f2b705}button{font:inherit;font-weight:800;border:0;border-radius:.6rem;padding:.8rem 1.4rem;cursor:pointer}
#save{background:linear-gradient(180deg,#ffd95e,#f2b705);color:#1a1402}#save:disabled{opacity:.5}
.mode{display:flex;gap:.4rem;margin-bottom:1rem}.mode button{background:#1a2546;color:#f4f1e8;padding:.5rem 1rem}.mode button.on{background:#f2b705;color:#1a1402}
#msg{color:#8d99b8;font-size:.85rem}
</style></head><body>
<h1>🖼️ KA-2 myndaeditor</h1>
<p class=sub>Veldu <b style=color:#f2b705>forsíðu</b> (smelltu í forsíðu-ham) og <b style=color:#43d17c>gallerí-myndir</b> (smelltu í gallerí-ham, röðin ræður birtingu). Svo „Vista &amp; byggja".</p>
<div class=mode><button id=mCover class=on onclick="setMode('cover')">★ Forsíðu-hamur</button><button id=mGal onclick="setMode('gal')">✓ Gallerí-hamur</button></div>
<div class=grid id=grid></div>
<div class=bar><span id=count></span><button id=save onclick=save()>Vista &amp; byggja PDF + gallerí</button><span id=msg></span></div>
<script>
const NAMES=__NAMES__; let cover=__COVER__, gallery=__GALLERY__, mode='cover';
const grid=document.getElementById('grid');
function setMode(m){mode=m;document.getElementById('mCover').className=m=='cover'?'on':'';document.getElementById('mGal').className=m=='gal'?'on':'';}
function render(){grid.innerHTML='';NAMES.forEach(n=>{const d=document.createElement('div');d.className='ph'+(cover==n?' cover':'')+(gallery.includes(n)?' gal':'');
 d.innerHTML='<img loading=lazy src="/thumb/'+n+'.jpg">'+(gallery.includes(n)?'<span class=badge>'+(gallery.indexOf(n)+1)+'</span>':'')+(cover==n?'<span class=cbadge>FORSÍÐA</span>':'');
 d.onclick=()=>{if(mode=='cover'){cover=cover==n?null:n}else{const i=gallery.indexOf(n);if(i>=0)gallery.splice(i,1);else gallery.push(n)}render()};grid.appendChild(d)});
 document.getElementById('count').innerHTML='Forsíða: <b>'+(cover||'engin')+'</b> · Gallerí: <b>'+gallery.length+'</b>';}
async function save(){const b=document.getElementById('save');b.disabled=true;document.getElementById('msg').textContent='Bygging í gangi… (1–2 mín)';
 const r=await fetch('/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cover,gallery})});
 const j=await r.json();document.getElementById('msg').textContent=j.ok?'✓ '+j.msg:'✗ '+j.msg;b.disabled=false;}
render();
</script></body></html>"""

class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            html = (PAGE.replace("__NAMES__", json.dumps(NAMES))
                        .replace("__COVER__", json.dumps(cur.get("cover")))
                        .replace("__GALLERY__", json.dumps(cur.get("gallery", []))))
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers()
            self.wfile.write(html.encode("utf-8")); return
        if self.path.startswith("/thumb/"):
            f = THUMBS/urllib.parse.unquote(self.path[len("/thumb/"):])
            if f.exists():
                self.send_response(200); self.send_header("Content-Type", "image/jpeg"); self.end_headers()
                self.wfile.write(f.read_bytes()); return
        self.send_response(404); self.end_headers()
    def do_POST(self):
        if self.path == "/save":
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            SEL.write_text(json.dumps(body, ensure_ascii=False, indent=2))
            try:
                out = subprocess.run(["python3", str(DIR/"apply-selection.py")], capture_output=True, text=True, timeout=600)
                ok = out.returncode == 0
                msg = (out.stdout.strip().split("\n")[-1] if ok else out.stderr.strip().split("\n")[-1])[:200]
            except Exception as e:
                ok, msg = False, str(e)[:200]
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps({"ok": ok, "msg": msg}, ensure_ascii=False).encode("utf-8")); return
        self.send_response(404); self.end_headers()

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), H) as srv:
        url = f"http://localhost:{PORT}"
        print(f"\n  🖼️  Myndaeditor opinn:  {url}\n  (Ctrl+C til að loka)\n")
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
        srv.serve_forever()
