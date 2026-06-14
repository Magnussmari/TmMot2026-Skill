#!/usr/bin/env python3
# Byggir demo-minningabók (ljós, prentvæn) með PLACEHOLDER-myndum — engin raunveruleg
# börn → óhætt opinbert. Sýnir útlit keepsake-bókarinnar. Keyrsla: python3 build-demo.py
import pathlib, shutil, subprocess, os
from PIL import Image, ImageDraw, ImageFont

DEMO = pathlib.Path(__file__).parent
TOOLS = DEMO.parent/"skills"/"tmmot-album"/"tools"
W = DEMO/"_work"; IMG = W/"img"
if W.exists(): shutil.rmtree(W)
IMG.mkdir(parents=True)

# brand-skrár + fontar
shutil.copy(TOOLS/"_brand.tex", W/"_brand.tex")
shutil.copy(TOOLS/"_quarto.yml", W/"_quarto.yml")
shutil.copytree(TOOLS/"fonts", W/"fonts")

def font(sz):
    for p in ["fonts/BigShoulders-Black.ttf"]:
        try: return ImageFont.truetype(str(W/p), sz)
        except Exception: pass
    return ImageFont.load_default()

def placeholder(path, w, h, label, sub=""):
    im = Image.new("RGB", (w, h)); dr = ImageDraw.Draw(im)
    for y in range(h):  # ljós himinn → rjómi
        t = y/h; r=int(150+90*t); g=int(180+60*t); b=int(210+20*t)
        dr.line([(0,y),(w,y)], fill=(min(r,250),min(g,245),min(b,235)))
    dr.polygon([(0,h),(0,int(h*.68)),(int(w*.35),int(h*.5)),(int(w*.6),int(h*.62)),
                (w,int(h*.52)),(w,h)], fill=(74,92,60))   # græn/dökk hlíð
    cx,cy=w//2,int(h*.42); R=int(min(w,h)*.13)
    dr.ellipse([cx-R,cy-R,cx+R,cy+R], fill=(242,183,5))
    f=font(int(R*1.0)); txt="KA"; tb=dr.textbbox((0,0),txt,font=f)
    dr.text((cx-(tb[2]-tb[0])/2,cy-(tb[3]-tb[1])/2-tb[1]),txt,font=f,fill=(17,32,63))
    fl=font(int(h*.06)); lb=dr.textbbox((0,0),label,font=fl)
    dr.text((cx-(lb[2]-lb[0])/2,int(h*.80)),label,font=fl,fill=(255,255,255))
    dr.text((12,12),"DEMO",font=font(int(h*.05)),fill=(242,183,5))
    im.save(path,"JPEG",quality=88)

placeholder(IMG/"forsida.jpg", 1600, 1100, "LIÐ-X")
for i,(lab) in enumerate(["Fimmtudagur","Föstudagur","Laugardagur","Umgjörðin"],1):
    placeholder(IMG/f"d{i}.jpg", 1200, 900, lab)

# index.qmd — ljósu makróin úr _brand.tex
L = ["---","format: pdf","---","","```{=latex}",
 "\\glasscover{img/forsida.jpg}",
 "\\dayhead{Minningabók · DEMO}{Mótinu lokið}","\\goldrule",
 "Þrír dagar, tíu leikir, og heil ferð í einni helgi. Þetta er DEMO-útgáfa — sýnir ljóst, prentvænt útlit minningabókarinnar með placeholder-myndum. Engar raunverulegar myndir, engin nöfn.","",
 "\\lead{Þvílík helgi, þvílíkur hópur. Áfram LIÐ-X!}","\\clearpage",
 "\\dayhead{Fimmtudagur}{Fyrsti dagur — þrír sigrar}",
 "\\gamehead{LIÐ-X \\textendash\\ Andstæðingur A}{4\\,–\\,1}","\\meta{kl. 13:40 \\, · \\, sigur}",
 "\\glassphoto{img/d1.jpg}{LIÐ-X gegn Andstæðingi A}","\\clearpage",
 "\\dayhead{Föstudagur}{Annar dagur — eldskírnin}",
 "\\gamehead{LIÐ-X \\textendash\\ Andstæðingur B}{1\\,–\\,2}","\\meta{kl. 15:00 \\, · \\, tap}",
 "\\glassphoto{img/d2.jpg}{LIÐ-X gegn Andstæðingi B}","\\clearpage",
 "\\dayhead{Lokastaðan}{Tíu leikir, þrír dagar}","\\goldrule",
 "LIÐ-X lék \\textbf{10 leiki á þremur dögum}: \\textbf{4 sigrar}, 6 töp, markatala \\textbf{14\\,–\\,18}.","\\clearpage",
 "\\dayhead{Umgjörðin}{Ferðin og hópurinn}","\\goldrule",
 "\\glassphoto{img/d4.jpg}{}",
 "```"]
(W/"index.qmd").write_text("\n".join(L)+"\n")

env = dict(os.environ, PATH="/Library/TeX/texbin:"+os.environ.get("PATH",""))
subprocess.run(["quarto","render","index.qmd","--to","pdf"], cwd=W, env=env, check=True)
pdf = W/"_book"/"Saga-KA2-TM-motid-2026.pdf"
if pdf.exists():
    shutil.copy(pdf, DEMO/"minningabok-demo.pdf")
    print("DEMO PDF:", DEMO/"minningabok-demo.pdf", pdf.stat().st_size//1024, "KB")
