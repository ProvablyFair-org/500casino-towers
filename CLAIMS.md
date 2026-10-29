# Technical claim index

Claim ids and source ids are the report's. C07 (aggregate financial analysis) and its source S13
belong to the report only and are absent here. C03.F and S08.F cover the public-feed check. Each
claim separates **source facts** (what a retained exhibit says) from **calculation** and
**inference**. Every command runs offline from the repository root; the one command that runs all
of them is `python3 -I -B analysis/run_all.py` ([VERIFY.md](VERIFY.md)). Machine-readable value
links: [claims-index.json](claims-index.json). Sources and dates: [SOURCES.json](SOURCES.json).
Every claim below has a retained exhibit.

---

## C01 Advertised fixed 5% and approximately 95% RTP

Source facts
- Help-centre article *What are the odds of Towers?*, Wayback snapshot 2023-09-25 08:46:22 UTC,
  retrieved 2026-10-28 ([text](evidence/help-history/2023-09-25-odds.txt), [image](evidence/help-history/2023-09-25-odds.png)):
  *"The odds of Easy difficulty is 0.6666 per level."*, *"The odds of Medium difficulty is 0.5 per level."*,
  *"The odds of Hard difficulty is 0.3333 per level."*, *"Towes has a fixed house edge set at 5% for all 3 difficulty modes."*
  (spelling as published).
- Help-centre article *What is the house edge on 500 Casino?*, Wayback snapshot 2023-09-25 09:40:24 UTC
  ([text](evidence/help-history/2023-09-25-house-edge.txt)): *"The house edge on Towers functions similar to as of Duels' and is set at 5%."*
  and, for Duels, *"500 Casino takes a fixed 5% rake for every played duel."*
- Towers game page captured logged out on 2026-10-07 13:49:23 UTC
  ([excerpt](evidence/client/towers-live-2026-10-07/page-excerpt.txt), [screenshot](evidence/client/towers-live-2026-10-07/screenshot.redacted.png)):
  *"The game’s RTP is typically around 95%"*.
- Current help-centre pages, captured logged out on 2026-10-28:
  - *What are the odds of Towers?*, acquired 12:47:30 UTC, page displays "April 29, 2024"
    ([text](evidence/client/help-odds-of-towers-2026-10-28/page.txt), [screenshot](evidence/client/help-odds-of-towers-2026-10-28/screenshot.jpg)):
    *"The odds of Easy difficulty is 0.6666 per level."*, *"The odds of Medium difficulty is 0.50 per level."*,
    *"The odds of Hard difficulty is 0.3333 per level."*, *"Towers has a fixed house edge set at 5% for all 3 difficulty modes."*
  - *What is the house edge on 500 Casino?*, acquired 12:48:13 UTC, page displays "June 6, 2026"
    ([text](evidence/client/help-house-edge-2026-10-28/page.txt)): *"The house edge on Towers functions similar to as of Duels' and is set at 5%."*
    and *"500 Casino takes a fixed 5% rake for every played duel."*
  The displayed article dates are the pages' own and are not authenticated.

Inference: the wording describes one fixed 5% edge per game; the Duels comparison is the operator's
own analogy and this repository does not audit Duels settlement.

Check: `python3 -I -B analysis/source_check.py --out OUT` (every quotation in this file is matched verbatim). Expected: `quotes 37/37`.

---

## C02 Compounded return and up to 40.13% edge

Report hero, unchanged: **Actual: up to 40.13%.**

Source facts: settlement
- Server records dated November 2024, retrieved 2026-10-28 from Wayback Machine captures
  ([wayback-raw/](evidence/historical-bets-2024/wayback-raw/)): each of the 270 row payout values the server lists
  for 27 games (10 rows each; 27 of them are the amounts paid at cash-out) equals floor(stake x step^n) in integer
  units, with step = 0.95 x choices/safe (1.425 Easy, 1.9 Medium).
- October 2026, public feed ([data/feed/](data/feed/)): each of the 330 winning Towers payouts equals
  floor(stake x step^row) for exactly one difficulty and row (C03.F).

Source facts: client code (consistent with the settlement above)
- Live chunk `1828.89aa27f6.js`, loaded by https://500.casino/towers on 2026-10-07, byte 33117:
  `roundMultiplier:function(){var t=this.difficultyData.choices/(this.difficultyData.choices-this.difficultyData.bombs),e=1-this.game.houseEdge;return new l.A(t).times(e).toNumber()}`,
  and the ladder `multiplier:Math.floor(1e3*Math.pow(this.roundMultiplier,a))/1e3`
  ([file](evidence/client/towers-chunk-2026-10-07/1828.89aa27f6.js)). The client store default is
  `towersHouseEdge:.05` (`app.3088e4a4.js` byte 1363940, [file](evidence/client/towers-live-2026-10-07/js/app.3088e4a4.js)).
- Archived `towers.55a86d17.js` (Wayback memento 2025-11-01 02:54:05 GMT, fetched 2026-10-07 13:43:36 UTC):
  the same construction with `this.roundMultiplier**a` ([file](evidence/client/towers-chunk-2026-10-07/archived-towers.55a86d17.js), [headers](evidence/client/towers-chunk-2026-10-07/archived-headers.redacted.txt)).
- Displayed tile labels: Easy 1.42x ... 34.52x on the logged-out page
  ([excerpt](evidence/client/towers-live-2026-10-07/page-excerpt.txt)); Medium and Hard as written in the
  session log ([log](evidence/session-2026-10-09/log.redacted.txt)) and shown in screenshots S05 and S06.

Calculation, four layers kept apart ([results/tables.md](results/tables.md))
1. Ideal mathematics: p = safe / total choices; full multiplier = (0.95/p)^n; return = p^n x multiplier = 0.95^n;
   edge = 1 - 0.95^n. Row 10: **40.126306076162109375%**, displayed **40.13%**. Row 5: 22.62190625%, displayed 22.62%.
2. Client 3-decimal label, evaluated in JavaScript: `Math.floor(1000*Math.pow(step,n))/1000` with the Number
   steps 1.425 / 1.9 / 2.85. All 30 labels are generated; e.g. Medium row 3 = **6.858**.
3. Client 2-decimal tile label `Math.floor(label*100)/100`; e.g. Easy row 2 = **2.02**. All 30 equal the labels the
   operator displayed (30/30).
4. Settlement: observed payouts are consistent with stake x the full multiplier, floored to the unit. The client's
   JavaScript labels and every truncation coarser than 7 decimals miss some of them; 7- and 8-decimal truncation fit
   them all, so the exact internal precision is not uniquely established (C03.F, C04).
- Return on the 3-decimal ladder labels (1 - label x p^n): Medium row 5 = **22.625%**, which rounds half-up to
  **22.63%**; Medium row 10 = **40.1263671875%**; Easy and Hard row 10 are 40.126633812596% and 40.126306965402%
  (12 dp). All display as 40.13%. Observed payouts follow the full multiplier (floored to one unit), so the payout edge
  is the nominal one, not the label one.

Scope of the hero figure: the edge of a row-10 cash-out, 1 - 0.95^10. A row-10 win is subject to the
published $200,000 per-round cap (a Medium row-10 stake above about $326.20 is capped). It is not every
player's realized loss.

Check: `node analysis/client_ladders.mjs --out OUT && python3 -I -B analysis/payout_math.py --out OUT`.
Expected: `30 ladder rows, 10 curve rows, 10 $100 Medium examples, 30 UI labels checked, 18 comparator rows; failures: 0`.
Settlement: C03.F and C04 checks.

---

## C03 33-game replay and October credits

Scope: one test account, 33 games, 9 October 2026.

Source facts: the session log written during play ([log.redacted.txt](evidence/session-2026-10-09/log.redacted.txt),
one browser tab id redacted), the operator's verify links recorded in it, and the seed-panel screenshots
([shots/](evidence/session-2026-10-09/shots/)); normalized in [data/session-2026-10-09.json](data/session-2026-10-09.json)
and [data/seed-panel-transcriptions.json](data/seed-panel-transcriptions.json). How the session was operated:
[METHODOLOGY.md](METHODOLOGY.md#the-9-october-2026-session).

Calculation
- Commitments 2/2: sha256 of each revealed server seed equals the hash shown before play (full 64 hex).
- Game-seed chain: game seed n = sha256^n(account id). Every observed value equals the chain at full length,
  including the final value **1005f5d5b5c4e393b4588562c8b02a0718d8ccca007b9929b20745cb4588bfa3** ("hashed 33 times"),
  which is in the log and was transcribed separately from screenshots F01 and F02.
- Replay: 33/33 logged results, 53 tiles, 13 cash-outs, 20 bombs, **$18.09** staked; 18/18 bomb rows read
  from the bet-detail screenshots of the first three games.
- Balance readings (displayed balance = running balance floored to the cent), 10 selected readings: with credits
  of stake x full multiplier, gross credits **$19.84882796875**, ending balance **$102.23882796875**, 10/10 readings.
  Credits on the 3-decimal ladder (gross **$19.84574**, ending **$102.23574**) also give 10/10: cent-level balances
  cannot separate the two; the server records (C04) and the feed (C03.F) do. The approximate reading 104.57
  (~12:24Z) is excluded because the log records it was taken while the balance animated; it matches no game
  boundary under either rule ([METHODOLOGY.md](METHODOLOGY.md#excluded-reading)).

Not shown: RNG uniformity. The account is identifiable (see [REDACTIONS.md](REDACTIONS.md)).

Check: `python3 -I -B analysis/session_verify.py --out OUT`. Expected: `games 33/33, tiles 53, cash-outs 13, bombs 20, staked 18.09, commitments 2/2, chain observations 10/10, screenshot layout rows 18/18; H-3dp: credits 19.84574, final 102.23574 (shown 102.23), readings 10/10; H-full: credits 19.84882796875, final 102.23882796875 (shown 102.23), readings 10/10; failures: 0`.

### C03.F Public-feed payouts, 7-9 October 2026

Source facts: 416 Towers entries (330 positive payouts, 86 zero) from a passive, logged-out capture of the
public bet feed, de-duplicated by transaction id within 236,603 distinct transactions across all games
([data/feed/](data/feed/)). Collection gaps are listed in [collection-gaps.jsonl](data/feed/collection-gaps.jsonl).

Calculation: each winner has exactly one (difficulty, row) with |payout - stake x step^row| < 1 raw unit
(330 unique, 0 unmatched, 0 ambiguous), and every winner equals floor(stake x step^row): 6 equal the unrounded
prediction, 324 are below it by less than one unit, none above. The client's 3-decimal labels, as its JavaScript
computes them, reproduce 199 of 330; truncating the exact multiplier first reproduces 202 at 3 decimals, 309 at 4,
321 at 5 and all 330 at 6 or more. Amounts are in the operator's internal units;
1,666 units = $1.00 on the November 2024 records (C04), and among the feed's most common stakes are 167 and 1,666
units (about $0.10 and $1.00 at that scale), but entries carry several currency labels and no conversion is made. The feed leans heavily to
wins (330 of 416), so it is not a sample of play; nothing is summed across players or currencies.

Check: `python3 -I -B analysis/feed_verify.py --out OUT`. Expected: `entries 416, winners 330, zero payouts 86, unique matches 330, unmatched 0, ambiguous 0, equal floor 330, exact multiplier truncated 3/4/5/6/7/8 dp 202/309/321/330/330/330, client JS 3-dp labels 199/330, unrounded equal/below/above 6/324/0; failures: 0`.

---

## C04 Historical documentation and payouts

Source facts
- Limits pages, Wayback snapshots 2023-09-25 10:12:56, 2024-04-19 09:15:38 and 2024-12-08 06:20:49 UTC
  ([2023](evidence/help-history/2023-09-25-limits.txt), [2024-04](evidence/help-history/2024-04-19-limits.txt), [2024-12](evidence/help-history/2024-12-08-limits.txt)):
  *"Towers has a global win limit of $100,000 per round."* with *"~$163.10"* maximum Medium bet (2023);
  *"Towers has a global win limit of $200,000 per round."* with *"~$326.20"* (2024). The 2023 Easy maximum reads
  *"~345x"* and the 2024 pages *"~34,5x"*; the 2023 value is not a reliable number. The article captured 2026-10-07
  shows the same $200,000 / ~$326.20 and displays the date May 21, 2024 ([page](evidence/client/limits-article-2026-10-07/page.txt)).
- 27 Towers games from one account (26 Easy, 1 Medium; dated 6 on 2024-11-08 and 21 on 2024-11-13 UTC by the
  operator's own records), as served by the operator's share-bet endpoint, archived by the Wayback Machine and
  retrieved on 2026-10-28 ([raw records](evidence/historical-bets-2024/wayback-raw/),
  [analysis](evidence/historical-bets-2024/analysis.md)). Published with the account holder's consent. They are winning games
  selected for sharing, not a sample of play.
- Archived client code of 2025-11-01 (C02) and the operator's redesign announcement of 2026-09-14 10:09:41 UTC
  ([syndication.json](evidence/client/redesign-tweet-2026-10-07/syndication.json)).

Calculation (all from the records' own fields)
- All 270 rows' bomb tiles equal the placement computed from the revealed seeds; the 82 picked tiles are safe.
- All 27 game seeds lie on the account's SHA-256 chain, positions **958** to **1923**, in date order.
- All **270** row payout values the server lists (27 of them paid at cash-out) equal floor(stake x step^n). The
  client's JavaScript 3-decimal labels reproduce **40** of 270 (2 of the 27 paid amounts); truncating the exact
  multiplier reproduces **41** at 3 decimals, 105 at 4, 255 at 5 and 269 at 6, and all 270 at 7 or 8. No row payout
  value exceeds the fixed-5% benchmark and every value from row 2 is below it.
- Units: at 1,666 units = $1.00, stake and win equal what the share page displayed for 27/27 games; the share page
  showed every time 4 hours ahead of the server's UTC timestamp.
- Example, [game 673498dd37bae6ae49b68c49](https://500.casino/?share=673498dd37bae6ae49b68c49&shareType=towers),
  $100 Easy, row 2: server payout **338302** units = floor(166,600 x 1.425^2), displayed $203.06; the 3-decimal ladder
  would pay $203.00 and a fixed 5% **$213.75**.
- Cap check: $200,000 / 613.1066257801 and $200,000 / 613.106 both truncate to $326.20 (both round half-up to
  $326.21), so the published maximum is consistent with the multiplier and does not fix the cap convention.

Scope: the same seed scheme, placement function and payout function appear on 8 and 13 November 2024 and on 7 to
9 October 2026; the checkpoints do not show what the game did between those dates.

Check: `python3 -I -B analysis/historical_verify.py --out OUT`. Expected: `games 27, rows replayed 270/270, played rows safe 82/82, seeds on chain 27/27 (positions 958-1923, date order True), row payout values full 270/270, exact multiplier truncated 3/4/5/6/7/8 dp 41/105/255/269/270/270, client JS 3-dp labels 40/270, paid cash-outs full 27/27 (client labels 2/27), above fixed-5% 0, units 1666=$1 stake 27/27 win 27/27; failures: 0`.

---

## C05 Fixed-return competitor comparison

Source facts
- Stake guide *How to Play Dragon Tower on Stake*, captured 2026-10-07 13:49:40 UTC and again 2026-10-28 12:51:02 UTC
  ([2026-10-07](evidence/comparators/stake-dragon-tower-blog-2026-10-07/page.txt), [2026-10-28](evidence/comparators/stake-dragon-tower-blog-2026-10-28/page.txt)):
  *"for Dragon Tower is 2%, which means that the theoretical RTP is 98%."* and, for Master mode, *"a correct
  prediction at the bottom of the tower will result in a payout of 3.92x your stake, and if you make it to the top,
  the payout will be a massive 256,901.12x."*
- Stake game page, captured 2026-10-28 12:50:27 UTC (served in the /pt/ locale; [text](evidence/comparators/stake-dragon-tower-game-2026-10-28/page.redacted.txt),
  [screenshot](evidence/comparators/stake-dragon-tower-game-2026-10-28/screenshot.png)): "Retorno ao jogador: 98,00%" and
  *"This game has a theoretical return to player percentage of 98%, meaning that the Dragon Tower house edge is just 2%."*
  (line breaks of the rendered text collapsed).
- Stake game-event rules, captured 2026-10-28 12:50:50 UTC ([text](evidence/comparators/stake-game-events-2026-10-28/page.txt)):
  *"A Dragon Tower game is generated with 9 separate game events"* and `master: { count: 1, size: 4 },` (one egg in four tiles).
- Shuffle *Tower (Shuffle Original) Multiplier Chart*, captured 2026-10-28 12:48:38 UTC, page displays "May 14, 2026"
  ([text](evidence/comparators/shuffle-tower-chart-2026-10-28/page.txt), [table screenshot](evidence/comparators/shuffle-tower-chart-2026-10-28/screenshot-table.jpg)):
  Hard (1/2) column 1.96, 3.92, 7.84, 15.68, 31.36, 62.72, 125.44, 250.88, **501.76**, with the note
  *"Please note that the multipliers have been visually truncated to 2 decimal points for readability."*
- Shuffle game-event rules, captured 2026-10-28 12:49:07 UTC ([text](evidence/comparators/shuffle-game-events-2026-10-28/page.txt)):
  *"There are a total of 9 rows in the tower."* and *"Hard: 2 columns - 1 key and 1 poison apple per row"*.

Calculation
- Stake Master, 0.98 x 4^n, rows 1-9: 3.92 ... **256901.12**, return 98% on every row. Rows 1 and 9 equal the guide;
  rows 2-8 are **calculated** from the stated 2% edge and one-in-four odds; they are not live settlements and Stake does
  not list them individually in the retained pages.
- Shuffle Hard, 0.98 x 2^n, rows 1-9: equal to the official chart's nine values (as displayed, 2 dp), return 98% per row.
- Shuffle Hard (one-in-two) and Stake Master (one-in-four) are separate ladders. Both have nine rows; Towers has ten.
  (The Shuffle chart's own Master (1/4) column shows the same nine values as the Stake calculation.)

Check: as C02 (`payout_math.py`; the comparator section parses the Shuffle chart from the captured text).

---

## C06 Per-bet winning-payout comparisons

Calculation: $100 Medium cash-out after row 4: gross payout $**1303.21** (100 x 1.9^4), against a fixed-5%
benchmark of $**1520.00** (100 x 0.95 x 2^4); difference $**216.79**. Profit, which excludes the stake, is
$1203.21 against $1420.00. All ten Medium rows are in [results/tables.md](results/tables.md). Assumptions: stake in
USD, below the $200,000 cap ([limits](evidence/client/limits-article-2026-10-07/page.txt)), before bonuses and
rebates. These are differences on a winning bet, not expected losses per bet. The November 2024 server records (C04)
are observed examples.

Check: as C02. Expected `medium_100_examples` row 4: `1303.21`, `1520.00`, `216.79`.

---

## C08 Reproduction and integrity

Release v1.0.0: the checks pass offline (see [VERIFY.md](VERIFY.md)). [SHA256SUMS](SHA256SUMS) lists every distributed
file. Hashes identify bytes; they do not prove when anything was captured.

Check: `python3 -I -B analysis/run_all.py` and `python3 -I -B tests/run_negative.py`.
