# November 2024 Towers records

27 Towers games dated 8 and 13 November 2024 by the operator's own records, from one 500 Casino account (`user-8f9dd7`,
account id `66d8a460c92633f73b8f9dd7`), published here with the account holder's consent. For each
game the operator's share-bet endpoint (`https://500.casino/api/share-bet/towers/<id>`) returns the
stake, the cash-out row, the full 10-row payout table computed by the server, the revealed server
seed, the client seed, the game seed, the bomb tiles of every row and UTC timestamps. The Wayback
Machine archived each response on 28 October 2026, and the copies here were retrieved from it that day; the bodies in [wayback-raw/](wayback-raw/) are
byte-identical to what the archive returned when fetched the same day ([index](wayback-raw/index.json)).
[share-page-display.json](share-page-display.json) records what the operator's share page displayed
for the same games when opened on 28 October 2026.

These are winning games selected for sharing. They show how the server computed payouts; they are
not a sample of play and say nothing about overall returns.

## What the records show

Checked by `python3 -I -B analysis/historical_verify.py --out OUT` (results in
[results/historical-2024.json](../../results/historical-2024.json)):

- **Payout function.** Each record lists a server-computed payout for all 10 rows, 270 row payout
  values in all; 27 of them (one per game, at the cash-out row) are the amounts actually paid. All 270
  values, and so all 27 paid amounts, equal floor(stake x step^n) in the operator's integer units, with
  step = 0.95 x choices/safe (1.425 Easy, 1.9 Medium). The 5% is applied on every row.
- **Precision.** The client's 3-decimal ladder labels, as its JavaScript computes them, reproduce 40 of
  the 270 row payout values and 2 of the 27 paid amounts. The exact multiplier truncated before
  multiplying reproduces 41 of 270 at 3 decimals, 105 at 4, 255 at 5 and 269 at 6; truncation at 7 or
  8 decimals and the untruncated multiplier reproduce all 270. The payouts are therefore consistent with
  the full compounded multiplier and rule out the 3-decimal ladder; because 7- and 8-decimal truncation
  give the same integers at these stakes, the exact internal precision is not uniquely established.
- **Fixed-5% comparison.** No row payout value exceeds stake x 0.95 x (choices/safe)^n; every value from
  row 2 upward (243 of 243) is below it, and row 1 equals it up to the floor.
- **Outcomes.** All 270 rows' bomb tiles equal the placement computed from the revealed seeds with
  the same function used for the October 2026 session; the 82 tiles actually picked are all safe; each
  game's win equals its payout at the cash-out row.
- **Seed chain.** All 27 game seeds are on the account's SHA-256 chain (game seed = sha256^n of the
  account id), at positions 958 to 1923, in the same order as the game dates. The games used two
  server seeds and two client seeds.
- **Units and time.** At 1,666 units = $1.00, stake and win, rounded to cents, equal the amounts the
  share page displayed for all 27 games (for example 3,332 units = $2.00 and 12,028 units = $7.22).
  One game was played with the bonus balance (`bux`); its units follow the same scale on the share
  page. The share page displayed every date-time exactly 4 hours ahead of the server's UTC timestamp,
  so the UTC times in the records are used.

## Example

Game [673498dd37bae6ae49b68c49](https://500.casino/?share=673498dd37bae6ae49b68c49&shareType=towers),
Easy, cashed out after row 2 on 2024-11-13 12:17:33 UTC: stake 166,600 units ($100.00), server payout
338,302 units = floor(166,600 x 1.425^2 = 338,302.125), displayed as $203.06. The 3-decimal ladder
(2.030) would pay $203.00; a fixed 5% would pay $213.75.

## Scope

The records come from one account on two days. Together with the October 2026 observations they
show the same seed chain scheme, placement function and payout function on 8 and 13 November 2024
and on 7 to 9 October 2026; they do not show what the game did between those dates.
