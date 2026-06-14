#!/bin/bash
# Robust re-harvest fyrir KA-2 albúm — Chrome 149 --headless=new + sjálf-timeout.
set -u
LINK="https://photos.app.goo.gl/wA5TJgeVhDJHq1Pz8"
DEST="$HOME/Pictures/Eyjamot-2026-final"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SLUG="eyjamot-2026-final"
mkdir -p "$DEST/raw"; cd "$DEST"

# dríp allt fast frá fyrri tilraun
pkill -f "HarvestSharedAlbum" 2>/dev/null
pkill -f "virtual-time-budget=20000" 2>/dev/null
sleep 1

PROFILE="$(mktemp -d)"
echo "render: --headless=new → album-rendered.html"
"$CHROME" --headless=new --disable-gpu --no-sandbox \
  --user-data-dir="$PROFILE" --virtual-time-budget=25000 \
  --window-size=1400,6000 --dump-dom "$LINK" > album-rendered.html 2>/dev/null &
CHPID=$!
# sjálf-timeout: bíð allt að 60s eftir non-empty DOM, dríp svo
for i in $(seq 1 60); do
  sleep 1
  if ! kill -0 "$CHPID" 2>/dev/null; then break; fi
  if [ -s album-rendered.html ] && [ "$(wc -c < album-rendered.html)" -gt 50000 ]; then
    sleep 2; kill "$CHPID" 2>/dev/null; break
  fi
done
kill "$CHPID" 2>/dev/null; wait "$CHPID" 2>/dev/null
rm -rf "$PROFILE"
echo "rendered bytes: $(wc -c < album-rendered.html)"

python3 - "$SLUG" <<'EOF'
import re, sys
slug = sys.argv[1]
html = open('album-rendered.html').read()
pats = [
    re.compile(r'\[&quot;(AF1Qip[A-Za-z0-9_-]+)&quot;,\[&quot;(https://lh3\.googleusercontent\.com/pw/[A-Za-z0-9_-]+)&quot;,(\d+),(\d+)'),
    re.compile(r'\["(AF1Qip[A-Za-z0-9_-]+)",\["(https://lh3\.googleusercontent\.com/pw/[A-Za-z0-9_-]+)",(\d+),(\d+)'),
]
items = {}
for p in pats:
    for m in p.findall(html):
        items[m[0]] = (m[1], int(m[2]), int(m[3]))
if not items:
    sys.exit("ERROR: no media items parsed (html bytes=%d)" % len(html))
with open('items.tsv', 'w') as f:
    for pid, (url, w, h) in sorted(items.items()):
        f.write(f"{pid}\t{url}\t{w}\t{h}\n")
print(f"parsed {len(items)} media items")
EOF
[ -s items.tsv ] || { echo "PARSE FAILED"; exit 1; }

n=0
while IFS=$'\t' read -r pid url w h; do
  n=$((n+1)); fn=$(printf "raw/%s-%03d" "$SLUG" "$n")
  curl -s -A "Mozilla/5.0" "${url}=d" -o "$fn.tmp"
  ft=$(file -b --mime-type "$fn.tmp")
  case "$ft" in
    image/jpeg) mv "$fn.tmp" "$fn.jpg";; image/png) mv "$fn.tmp" "$fn.png";;
    image/heic) mv "$fn.tmp" "$fn.heic";; video/*) mv "$fn.tmp" "$fn.mp4";;
    *) mv "$fn.tmp" "$fn.bin";;
  esac
done < items.tsv
echo "downloaded $(ls raw | wc -l | tr -d ' ')/$(wc -l < items.tsv | tr -d ' ') → $DEST/raw ($(du -sh raw | cut -f1))"
