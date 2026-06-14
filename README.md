<p align="center">
  <a href="https://www.smarason.is">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="assets/sumarhus-logo-white.svg">
      <img src="assets/sumarhus-logo.svg" alt="Sumarhús — smarason.is" width="220">
    </picture>
  </a>
</p>

<h1 align="center">🏆 TmMót 2026 — tournament memory, automated</h1>

<p align="center">
  Tell it <b>which team you followed</b>. It fetches the story of the whole tournament —<br>
  every game, the standings, the analysis — pairs it with your shared photo album,<br>
  and builds two keepsakes from one source of truth:<br>
  a <b>live, private dashboard</b> and a <b>light, print-ready PDF memory book</b>.
</p>

<p align="center">
  Two Claude Code skills in one repo · built as a real experiment over one tournament
  weekend<br>(KA-2 at the TM tournament in Vestmannaeyjar, June 2026), then generalized.
  <br><br>
  <b>by Magnús Smári Smárason</b> · <a href="https://www.smarason.is">smarason.is</a>
</p>

---

## The system at a glance

```
        ┌──────────────────────────────────────────────────────────────────┐
        │  YOU PROVIDE ONLY:  the team you followed  +  a shared album link  │
        └──────────────────────────────────────────────────────────────────┘
                              │                               │
              ┌───────────────┘                               └───────────────┐
              ▼                                                                ▼
   ┌─────────────────────┐                                       ┌──────────────────────┐
   │  OFFICIAL RESULTS    │                                       │  SHARED PHOTO ALBUM   │
   │  feed (tmmotid.is)   │                                       │  (Google Photos link) │
   └──────────┬──────────┘                                       └───────────┬──────────┘
              │  agent + Python on a timer                                    │  headless Chrome
              │  scrape played games only · diff · rebuild on change          │  harvest originals + EXIF
              ▼                                                                ▼
   ╔═════════════════════ SKILL 1 · tmmot-results ═══════╗        ╔════ SKILL 2 · tmmot-album ════════╗
   ║  matches · standings · per-game form                ║        ║  EXIF time → which game            ║
   ║  full-tournament analysis · team-in-context         ║        ║  LOCAL vision model (Gemma 3 12B,  ║
   ║  (optional) parent heart-rate per game              ║        ║  on your own hardware) describes   ║
   ╚════════════════════════╤════════════════════════════╝        ║  & sorts — photos never leave box  ║
                            │                                     ║  owner picks cover + gallery        ║
                            ▼                                     ╚═══════════════╤═══════════════════╝
                  ┌───────────────────┐                                          │
                  │     data.json     │ ◄────────── one source of truth ─────────┘
                  └─────────┬─────────┘
            ┌───────────────┴────────────────┐
            ▼                                 ▼
   ┌──────────────────────┐        ┌──────────────────────────┐
   │  LIVE DASHBOARD       │        │  PDF MEMORY BOOK          │
   │  zero-dep Node server │        │  Quarto + xelatex         │
   │  PIN-gated · liquid   │        │  LIGHT · print-ready      │
   │  glass · dark (screen)│        │  same fonts + crest       │
   └──────────────────────┘        └──────────────────────────┘
```

**One `data.json` → two media, fit to each:** dark liquid-glass on the screen,
light and ink-frugal on paper. Same fonts and crest, so they read as one identity.

---

## The two skills

| Skill | Does | You give it |
|---|---|---|
| **`tmmot-results`** | Fetches the team's games, standings, and full-tournament analysis from the official feed. Runs on a timer; rebuilds only on a real change. | the **team name** + the results URL |
| **`tmmot-album`** | Harvests the shared album, matches photos to games by time, describes them with a **local** vision model, lets you pick cover + gallery, and builds the gated site + the light PDF book. | the **album link** + the data from skill 1 |

Drop `skills/tmmot-results/` and `skills/tmmot-album/` into your Claude Code
`~/.claude/skills/` (or a project `.claude/skills/`). Then just say what you want.

---

## Non-negotiable principles

- **Photos are unaltered — and any alteration is disclosed.** No image is changed by
  the system beyond what the phone that took it already does. The vision model only
  *describes and sorts*; it never edits. If a photo is edited beyond that, the page
  says so plainly.
- **Privacy first.** Children on the open internet → `noindex`, robots `Disallow: /`,
  everything (incl. the album link) behind a PIN, no children's names except the
  owner's own messages. The vision model runs on **your** hardware; photos never leave it.
- **No fake-green data.** Only games that were actually played; "last updated" shown;
  hand-added games disclosed as hand-added.
- **Verify the whole page in a real browser after every change.** (A single
  out-of-scope reference once blanked the entire JS-rendered page while one field still
  showed — read-one-field "verification" is not verification.)
- **Light for print, glass for screen.** Dark full-bleed is wrong for a printed book.

---

## Quickstart

```bash
# 1. results layer — fetch the tournament for your team
python3 skills/tmmot-results/tools/refresh-urslit.py      # edit TEAM + feed URL at top

# 2. photos — harvest the shared album, match to games
bash   skills/tmmot-album/tools/harvest-album.sh <album-link> ~/Pictures/<event>
python3 skills/tmmot-album/tools/match-photos.py

# 3. pick + build — local web picker → light PDF + site gallery + deploy
python3 skills/tmmot-album/tools/editor.py                # → http://localhost:8765

# 4. site — runs anywhere Docker + a tunnel run
cp -r skills/tmmot-album/templates/* apps/<event>/ && docker compose up -d --build
```

A full demo memory book is in [`demo/`](demo/).

---

## Demo

See **[`demo/minningabok-demo.pdf`](demo/minningabok-demo.pdf)** — the same light
print layout, built from placeholder content (no real photos), so you can see the
shape of the keepsake before you point it at your own tournament.

---

*Make it yours.* Swap the official feed, the album source, the local model, the palette
and crest. The spine — one `data.json` → a gated screen experience + a light printable
book, verified in a real browser — is the part worth keeping.

MIT licensed. Built with [Claude Code](https://claude.com/claude-code).
