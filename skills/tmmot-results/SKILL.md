---
name: tmmot-results
description: Fetch a team's tournament results + analysis from a live/official results page (e.g. tmmotid.is) and write the data layer (matches, standings, full-tournament analysis, sibling teams). The user only supplies WHICH TEAM they followed — the system fetches the story of the tournament. USE WHEN building a tournament dashboard's data, "sækja úrslit", "fetch tournament results", "tournament analysis for <team>", monitor a results page on an interval, or feeding the tmmot-album skill. Pairs with tmmot-album.
---

# tmmot-results — the data + analysis layer

**You give it one thing: the team you were following.** It fetches the rest —
every played game, the group standings, and a full-tournament analysis — straight
from the official results feed. No invented data; only games that were actually played.

This is **Skill 1 of 2**. It produces the `data.json` data layer that
**`tmmot-album`** (Skill 2) turns into a site + PDF memory book.

## Inputs

- **Team name** (exactly as it appears on the feed, e.g. `KA-2`).
- **Results URL** (the official feed, e.g. `https://urslit.tmmotid.is`). The day
  pages are scraped (`?day=A/B/C`), only rows with a final score count.
- (optional) **Heart-rate window** — if the owner wore a Garmin and you have their
  HR in InfluxDB, `puls-magnus.py` adds a "how excited was the parent" series per game.

## What it writes into `data.json`

- `matches[]` / `games[]` — the team's games (day, time, venue, opponent, score, result).
- `groupResults[]` + `analysis.ka_family[]` — the group table + the team's siblings
  (e.g. all KA-1..KA-4) with per-game form.
- `analysis` — tournament-wide stats (games played, goals, average, number of teams)
  and the team in context (goals for/against, defence percentile, etc.).
- `wrapup.record` — the final W/L/GF/GA once the tournament is done.

## Tools

- `tools/refresh-urslit.py` — scrape the official feed, write CSV + compute the
  analysis into `data.json`. **Idempotent:** exit `0` = unchanged, exit `3` = changed
  (so a cron/agent can rebuild only on a real change). Parameterise `TEAM`, the feed
  URL, the day codes, and the group at the top of the file.
- `tools/puls-magnus.py` — (optional) pull the owner's heart-rate per game window
  from InfluxDB. Iterates ALL of the team's games via `analysis.ka_family`.

## Rules

1. **Only played games count.** No guessing, no projected scores. Show "last updated".
2. **Honest provenance.** If a game is hand-added (a placement final not yet on the
   feed), record it as hand-entered — never claim it came "straight from the official
   system". The dashboard's caption must say so.
3. **Run on an interval, rebuild on change.** A small Python agent on a timer scrapes
   the feed; only `exit 3` triggers a redeploy. Add a killswitch date so it stops
   after the tournament.

## Run as an agent

A large-language-model-powered agent + this Python on a schedule = live results that
update themselves. The agent decides when something material changed and narrates it;
the Python does the deterministic scrape + diff.

— pattern by Magnús Smári Smárason · https://www.smarason.is
