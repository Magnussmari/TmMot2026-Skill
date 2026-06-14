---
name: tmmot-album
description: Turn a shared photo album + the tmmot-results data into a gated tournament site AND a printable PDF memory book. Harvest a shared album, match photos to games by EXIF time, describe them with a LOCAL vision model (nothing leaves the machine), let the owner pick cover + gallery, and build a light print-ready keepsake. USE WHEN building the photo/story half of a tournament site, "minningabók", "memory book PDF", "harvest the album", "photo gallery for the team", or after tmmot-results has produced the data. Pairs with tmmot-results.
---

# tmmot-album — the album + story + keepsake layer

Takes the data layer from **`tmmot-results`** (Skill 1) and a shared photo album, and
produces two artifacts that share one `data.json`:

1. A **self-hosted, PIN-gated dashboard** (zero-dependency Node server).
2. A **light, print-ready PDF memory book** (Quarto + xelatex).

This is **Skill 2 of 2**.

## Pipeline

```
  shared photo album (Google Photos link)
        │  harvest-album.sh  → headless Chrome (--headless=new) → originals + EXIF
        ▼
  match-photos.py   EXIF datetime → which game's time-window
        ▼
  LOCAL vision model (e.g. Gemma 3 12B on your own hardware)
        │  "looks at" each photo, writes metadata — NOTHING leaves the box
        ▼
  editor.py   owner picks COVER + GALLERY (local web picker)
        ▼
  apply-selection.py → build-album.py → Quarto → light PDF  +  site gallery  + deploy
```

## Two media, one identity (the load-bearing lesson)

- **Screen (website):** dark "broadcast night" with **liquid glass** — translucent
  panels, `backdrop-filter: blur()`, gold. Great on a display.
- **Print (PDF book):** **LIGHT**. White paper, dark ink, gold used sparingly. Dark
  full-bleed pages are wrong for print — ink-heavy and physically heavy ("þung").
  Keep the SAME fonts + crest so the two read as one identity; never ship a dark
  album to print.

## Tools

- `tools/harvest-album.sh <shared-link> <dest>` — robust headless-Chrome harvest.
- `tools/match-photos.py` — EXIF datetime → game window.
- `tools/build-album.py` + `tools/_brand.tex` + `tools/_quarto.yml` — the LIGHT PDF.
- `tools/editor.py` + `tools/apply-selection.py` — local web picker: choose cover +
  gallery from every harvested photo, then auto-build + deploy.
- `tools/fonts/` — bundled TTFs (load by `Path=` in fontspec) so PDF rendering is
  reproducible without system fonts.
- `templates/` — `server.mjs` (gated, zero-dep), `gate.html`, `index.html`,
  `docker-compose.yml`, `Dockerfile`, `data.example.json`.

## Vendor-agnostic — a Sumarhús staple (do not lock to one provider)

The **photo source is an adapter.** `harvest-album.sh` is just the Google Photos
adapter. Swap it freely:

| Source | How |
|---|---|
| **A local folder** (universal — works out of the box) | skip `harvest-album.sh`; point `match-photos.py` at any folder of photos. This is the simplest, most portable source. |
| **Dropbox / iCloud shared album / S3 / Nextcloud** | write a small adapter that downloads originals (with EXIF) into a folder, then continue exactly as with the local folder. |
| **Google Photos shared link** | `harvest-album.sh` (headless Chrome). |

Everything downstream (`match-photos.py` → editor → build → site) only ever sees a
**folder of original photos** — so any source that can produce that folder works. The
same agnosticism applies to the results feed, the vision model, and the hosting.
Never hard-code a single vendor.

## Rules (do NOT skip)

1. **Photos are unaltered — and any alteration is disclosed.** No image is changed
   by the system beyond what the phone that took it already does. The local vision
   model only *describes and sorts* photos; it never edits them. If any photo is
   edited beyond that, it is stated plainly on the page. Put this statement on the
   "Um síðuna"/About page.
2. **Privacy first.** Children on the open internet: `noindex/nofollow/noarchive`,
   robots `Disallow: /`, ALL content (incl. the album link) behind the PIN, no
   children's names except messages the owner wrote. The vision model runs on the
   owner's own hardware so photos never leave the box.
3. **The owner picks the photos.** Auto-selection is only a starting point — ship the
   `editor.py` picker. Cover photo: never let a dark gradient hide half the team —
   light treatment, all faces visible.
4. **Verify the WHOLE page in a real browser after EVERY change.** Reading one field
   via eval is not verification — an out-of-scope reference threw at load and blanked
   the entire JS-rendered page while one earlier field still showed. Load the full page
   headless, force `.reveal` sections visible, check `0` console/page errors, screenshot
   at the owner's real viewport. Lazy-loaded images read as "blank" in a full-page shot
   — scroll + `img.decode()` before judging.
5. **Quarto:** set `latex-auto-install: false` with a full MacTeX so it doesn't choke
   on tlmgr.

— pattern by Magnús Smári Smárason · https://www.smarason.is
