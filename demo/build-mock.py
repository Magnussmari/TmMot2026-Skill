#!/usr/bin/env python3
# Byggir MOCK-minningabók: falskt lið (Eldey U11), fölsk úrslit, fake myndir gerðar
# með nano-banana-pro (ekki raunverulegt fólk). Sýnishorn fyrir README. Ljós, prentvæn.
import pathlib, shutil, subprocess, os
from PIL import Image, ImageOps

DEMO = pathlib.Path(__file__).parent
TOOLS = DEMO.parent/"skills"/"tmmot-album"/"tools"
PHOTOS = DEMO/"mock-src"
W = DEMO/"_work"; IMG = W/"img"
if W.exists(): shutil.rmtree(W)
IMG.mkdir(parents=True)

# brand + fontar; sérsníð kápu-titil fyrir mock-liðið
brand = (TOOLS/"_brand.tex").read_text()
brand = (brand.replace("SAGA KA\\textcolor{goldbright}{-}2", "ELDEY\\,\\textcolor{goldbright}{U11}")
              .replace("TM-MÓTIÐ Í VESTMANNAEYJUM", "SUMARMÓTIÐ 2026")
              .replace("11.–13. júní 2026 · 10 leikir · Riðill C10", "Sýnishorn · teiknimyndir · bara gaman")
              .replace("SAGA KA-2", "ELDEY U11"))
(W/"_brand.tex").write_text(brand)
shutil.copy(TOOLS/"_quarto.yml", W/"_quarto.yml")
shutil.copytree(TOOLS/"fonts", W/"fonts")

def proc(src, dest, mx, q=90):
    im = Image.open(src); im = ImageOps.exif_transpose(im)
    if im.mode != "RGB": im = im.convert("RGB")
    im.thumbnail((mx, mx)); im.save(dest, "JPEG", quality=q, optimize=True)

proc(PHOTOS/"cover.jpg", IMG/"forsida.jpg", 2200, 92)
for src, dst in [("g1.jpg","d1.jpg"),("g4.jpg","d2.jpg"),("g3.jpg","d3.jpg"),("g2.jpg","d4.jpg")]:
    if (PHOTOS/src).exists(): proc(PHOTOS/src, IMG/dst, 1600)

L = ["---","format: pdf","---","","```{=latex}",
 "\\glasscover{img/forsida.jpg}",
 "\\dayhead{Minningabók · Sýnishorn}{Mótinu lokið}","\\goldrule",
 "\\textit{Þetta er sýnishorn — bara gaman.} Stúlknaliðið Eldey U11, úrslitin og myndirnar eru \\textbf{öll skálduð}. Myndirnar eru ýktar \\textbf{teiknimyndir} gerðar með myndalíkani — ekkert raunverulegt fólk, bara ýktar Vestmannaeyjar með hvölum, lundum og þjóðhátíðarstemmingu. Sýnir ljóst, prentvænt útlit minningabókarinnar sem kerfið býr til úr alvöru móti.","",
 "\\lead{Þrír dagar, tíu leikir, ein helgi — svona lítur keepsake-bókin út.}","\\clearpage",
 "\\dayhead{Fimmtudagur}{Fyrsti dagur — þrír sigrar}",
 "\\gamehead{Eldey \\textendash\\ Vík-2}{3\\,–\\,1}","\\meta{kl. 13:40 \\, · \\, sigur}",
 "Galvösk byrjun. Eldey mætti einbeitt og lét engan velkjast í vafa um hver væri kominn til að keppa.",
 "\\glassphoto{img/d1.jpg}{Eldey U11 á Sumarmótinu}","\\clearpage",
 "\\dayhead{Föstudagur}{Annar dagur — eldskírnin}",
 "\\gamehead{Eldey \\textendash\\ Fram-1}{1\\,–\\,2}","\\meta{kl. 15:00 \\, · \\, tap}",
 "Hársbreidd gegn einu sterkasta liði mótsins. Höfuðið hátt — þetta var leikur jafningja.",
 "\\glassphoto{img/d3.jpg}{Fagnað marki}","\\clearpage",
 "\\dayhead{Lokastaðan}{Tíu leikir, þrír dagar}","\\goldrule",
 "Eldey U11 lék \\textbf{10 leiki á þremur dögum}: \\textbf{5 sigrar}, 5 töp, markatala \\textbf{18\\,–\\,16}. Komust í úrslitakeppnina.","",
 "\\glassphoto{img/d2.jpg}{Umgjörðin — vellirnir í Eyjum}","\\clearpage",
 "\\dayhead{Umgjörðin}{Ferðin og hópurinn}","\\goldrule",
 "\\glassphoto{img/d4.jpg}{}",
 "```"]
(W/"index.qmd").write_text("\n".join(L)+"\n")

env = dict(os.environ, PATH="/Library/TeX/texbin:"+os.environ.get("PATH",""))
subprocess.run(["quarto","render","index.qmd","--to","pdf"], cwd=W, env=env, check=True)
pdf = W/"_book"/"Saga-KA2-TM-motid-2026.pdf"
if pdf.exists():
    shutil.copy(pdf, DEMO/"minningabok-demo.pdf")
    # forsíðu-mynd fyrir README
    proc(PHOTOS/"cover.jpg", DEMO/"sample-cover.jpg", 1400, 85)
    print("MOCK PDF:", DEMO/"minningabok-demo.pdf", pdf.stat().st_size//1024, "KB")
