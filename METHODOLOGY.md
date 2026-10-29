# Methodology

## Collection

| material | when | how |
|---|---|---|
| Towers page, client code, limits article, Stake guide, redesign post | 2026-10-07, 13:43-13:50 UTC | logged-out captures in a browser (HTML, rendered text, screenshot, loaded scripts); archived Towers chunk fetched from the Wayback Machine |
| Public bet feed | 2026-10-07 13:55 UTC to 2026-10-09 | passive logged-out capture of the bet frames the Towers page receives; nothing sent, no bets |
| Session | 2026-10-09 11:47-13:12 UTC | one test account, Towers only; see [the 9 October 2026 session](#the-9-october-2026-session) |
| Historical help pages | Wayback snapshots 2023-09-25 to 2024-12-08, retrieved 2026-10-28 | browser retrieval of the exact replay URLs |
| November 2024 game records | games of 2024-11-08 and 2024-11-13; archived by the Wayback Machine 2026-10-28 | the operator's share-bet JSON fetched from each Wayback capture on 2026-10-28 15:22-15:24 UTC, logged out, one request per record about 3 s apart; the share pages were opened in a browser on 2026-10-28 07:56-07:57 UTC to record what they display |
| Current help pages, Shuffle and Stake pages | 2026-10-28, 12:47-12:51 UTC | logged-out browser sessions: rendered text, screenshot and page HTML (HTML published as a hash only) |

Exact times, URLs and hashes per file: [SOURCES.json](SOURCES.json). Snapshot or event dates are
kept separate from retrieval dates; unknown dates are null.

## The 9 October 2026 session

The session log ([log.redacted.txt](evidence/session-2026-10-09/log.redacted.txt)) is the primary
record. It was written during play, with a block added after the session and marked as such (line 65:
"added 9 Oct after the session, from the session transcript (not written during play)"). The public
copy differs from the original in one token: a browser tab id is redacted ([REDACTIONS.md](REDACTIONS.md)).
What follows states only what the log records; line numbers refer to that file.

**Browser and account.** The test account was logged in to 500 Casino in the investigator's default
Chrome, with a browser-automation extension connected to the tab and no network recorder running
(line 1, 11:47:00Z: "default Chrome, browser extension; no recorder"). Game actions were issued through
that extension: the log records a cash-out click "lost (extension disconnect)" and repeated (line 11,
12:09:25Z), a first tile click and a first Place Bet click that "did not register" and were repeated
(lines 34 and 37), and, at about 12:24Z, that the "extension tab group [was] lost; extension reported
another connected Chrome (picked it from the list)" (line 39). The block added after the session says that
when play resumed, the browser tool listed the same tab as before, logged in as the same account, and that
the resume time was not recorded (line 73). One selection was corrected before betting: "Hard was selected
by mistake first; no bet placed on it" (line 41). The log records the account showing "level 1 / '+0 USD
Level Up Bonus' banner; nothing claimed" (line 26).

**Page script and DevTools.** At about 11:48Z "a read-only websocket hook was tried in the page
(JavaScript in the tab). The hook captured 0 frames, and an injected script for the page's own context
did not run (blocked). No capture came of it." (line 72). There is therefore no websocket, HAR or video
record of the session. Before play, the Towers fairness panel stayed on "Loading", and DevTools showed the
request `rotateSeed?clientSeed=null&isUserSeed=true` answered "Pair is locked for userId
6a9ae61b8fb4004f64eae1e0" (line 4; screenshot [S02](evidence/session-2026-10-09/shots/S02-seedpair-locked-devtools.png)
shows the DevTools network panel). The log does not say whether that request was sent by the page or by hand.

**Seeds.** Seeds were read from, and rotated in, the Mines fairness panel, which shows the same "your 500
ID hashed N times" counter (line 3; it read 0 before and 3 after the first three Towers games, line 15).
Two client seeds were entered at the two rotations: `pf500radb9081b2d`, recorded as drawn with
`openssl rand -hex 5` (line 12; rotated 12:11:17Z, line 16), and `pf500r941933b51b` (line 56; rotated
13:12:34Z, line 57; the log does not say how it was drawn). Each rotation revealed the previous server seed (lines 17 and 59).

**Games.** 33 games in this order: three checkpoint bets of $0.10 (A1-A3, Easy/Medium/Hard, lines 5-14),
two probe groups of four attempts each at $2.00 (P1, Easy, cash after row 1, lines 24-27) and $1.50 (P2,
Easy, cash after row 2, lines 28-31), and 22 further bets A4-A25 (lines 32-55; the log calls them "plan bets
4-25" and stops "before bet 26", line 56). After the checkpoint bets the log records an offline check of the
first three games against their revealed seed and screenshots (lines 18-23) before the probes. Balances were
read from the screen after each settled game where the log gives them, and screenshots were saved (P1/P2 balance
crops in [shots/](evidence/session-2026-10-09/shots/)). The operator's "Verify bet" links for four games were
copied into the log after the session (lines 66-71); they also show that line 3 misread the first client seed
(`97BCXlhqj6` for `97BCXIhqj6`, line 71).

**Analysis notes in the log.** Lines 18-23 and 58-63 record checks run on 9 October with working scripts that
are not part of this repository; [analysis/session_verify.py](analysis/session_verify.py) runs the same checks from
the published inputs. Line 61 records that the first replay run showed 3 mismatches caused by encoding Medium's
right tile as 2 (Medium has tiles 0-1). Line 62 records the credit rule found on 9 October from cent-level
balances (stake x the 3-decimal ladder value); the full multiplier fits the same ten readings, and the server
records dated November 2024 and the October 2026 feed are consistent with the full multiplier and rule out the
3-decimal ladder (see below).

**Times.** Times in the log are UTC; the bet-detail panel showed "site time" three hours behind (bet 1
placed "09:04:30 (site time)", line 7, between its start at 12:03:59Z and settlement at 12:05:15Z). Two
times are not exact in the log itself: line 2 is stamped "12:0xZ", and the interruption at "~12:24Z" (line 39)
and its resume (line 73) are approximate.

### Excluded reading

The log records "Balance last seen 104.57" at about 12:24 UTC (line 39) and, in the block added after
the session, that it was read while the balance display was still animating (line 74). Under either credit
rule the displayed balances at the neighbouring game boundaries are 104.60 (after game 15) and 104.50 (after
game 16), and no boundary shows 104.57. The reading is not used for reconciliation.

## Replay and chain

Tile placement: one outcome per row, HMAC-SHA256(key = server seed, message = "client:game:round"), the first
13 hex digits as an integer i, arrangement index floor(i x C(choices, bombs) / 2^52) in lexicographic order.
It reproduces 33/33 session results, 18/18 rows read from the first three bet-detail screenshots, and 270/270
rows of the November 2024 records. Game seeds are checked at their full 64 hex characters against the chain
sha256^n(account id); the final session value was also transcribed separately from the screenshots F01 and F02.

## Precision layers

Four layers are computed and reported separately ([results/tables.md](results/tables.md)):

1. **Ideal mathematics** (exact rationals): full multiplier (0.95/p)^n, return 0.95^n, edge 1 - 0.95^n.
2. **Client 3-decimal label**, evaluated by the JavaScript engine exactly as the captured code writes it. In
   JavaScript doubles one label differs from the exact value truncated to 3 decimals: Medium row 3 is 6.858
   (exact 6.859).
3. **Client 2-decimal tile label**, `Math.floor(label*100)/100` in JavaScript.
4. **Settlement**, measured on the server's own integer amounts. The records dated November 2024 (retrieved
   28 October 2026) list a server-computed payout for every row of each game, 270 row payout values; 27 of them,
   one per game, are the amounts actually paid at cash-out.

| rule (payout = floor(stake x m)) | November 2024 row payout values (270) | of which paid at cash-out (27) | October 2026 feed winners (330) |
|---|---:|---:|---:|
| m = the client's 3-decimal label as its JavaScript computes it | 40 | 2 | 199 |
| m = exact multiplier truncated to 3 decimals | 41 | 2 | 202 |
| m = exact multiplier truncated to 4 decimals | 105 | 6 | 309 |
| m = exact multiplier truncated to 5 decimals | 255 | 26 | 321 |
| m = exact multiplier truncated to 6 decimals | 269 | 27 | 330 |
| m = exact multiplier truncated to 7 or 8 decimals | 270 | 27 | 330 |
| m = full compounded multiplier | 270 | 27 | 330 |

The client label and exact 3-decimal truncation differ only at Medium row 3 (6.858 in JavaScript, 6.859 exact).
The payouts are consistent with the full compounded multiplier and rule out the 3-decimal ladder. Truncation at
7 or 8 decimals gives the same integers at these stakes, so the exact internal precision is not uniquely
established. In the session the ten cent-level balance readings fit both the full multiplier (gross credits
$19.84882796875) and the 3-decimal ladder ($19.84574); they do not separate the two.

Quantities: the **gross payout** includes the stake; **profit** excludes it. The **fixed-5% winning benchmark**
is 0.95 / p^n (5% charged once on the fair multiplier). The **successful-cash-out difference** is the benchmark
gross payout minus the full-formula gross payout. Rounding happens only at display boundaries (half-up to cents
unless stated). Units: 1,666 units = $1.00 on the November 2024 records (27/27 against the share-page display).

## Feed matching rule

Fixed before matching: for each winner, the candidates are all (difficulty, row) with |payout - stake x step^row| < 1
raw unit, rows 1-10, exact steps 1.425 / 1.9 / 2.85. Exactly one candidate is required; unmatched and ambiguous
entries are reported and fail the check. The public feed shows mostly wins (330 of the 416 Towers entries), so it is
used only to test the payout function, never for totals or shares of play.

## Limitations

- The records dated November 2024 are winning games selected for sharing from one account, retrieved on 28 October
  2026 from Wayback Machine captures; their dates are the operator's own timestamps. They are not a sample of play.
- The October observations are one session (33 games) and a three-day feed sample with gaps.
- No empirical RNG-uniformity conclusion.
- The observations cover November 2024, the client code of November 2025 and October 2026, and the feed and
  session of October 2026; they do not show what the game did between those dates.
- No websocket, HAR or video record of the session (see above).
