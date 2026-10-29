# 500 Casino Towers: technical evidence

**Actual: up to 40.13%.**

Version **v1.0.0**. This repository holds the technical evidence behind the ProvablyFair.org report
on 500 Casino's Towers game: how the server settles a winning climb, what the client code and help
pages say, what the operator paid in observed games, and the arithmetic of two fixed-return
comparators. Every figure below is reproduced offline by one command (see [VERIFY.md](VERIFY.md)).

- Report: https://provablyfair.org/investigations/500casino-towers, published 29 October 2026 ([report-reference.json](report-reference.json))
- Claim index (claim, exhibit, command, expected result): [CLAIMS.md](CLAIMS.md)
- Responses and corrections: [RESPONSE.md](RESPONSE.md); contact audit@provablyfair.org

The report's aggregate financial analysis is not part of this repository and is not checked by it.

## Findings

1. **The server applies 5% on every row, and it compounds.** 27 game records dated 8 and 13 November
   2024 by the operator, retrieved on 28 October 2026 from Wayback Machine captures of its share-bet API,
   list a server-computed payout for each of their 10 rows: 270 row payout values, 27 of which are the
   amounts actually paid at cash-out. All 270 equal floor(stake x step^n) with step = 0.95 x
   choices/safe; in the public bet feed of 7-9 October 2026, all 330 winning Towers payouts follow the
   same function. The client code of 1 November 2025 and 7 October 2026 builds its ladder the same way.
   The return of a cash-out after row *n* is therefore 0.95^n and the edge 1 - 0.95^n: 5% at row 1,
   rising to **40.126306076162109375%** at row 10 (displayed **40.13%**).
   ([C02](CLAIMS.md#c02-compounded-return-and-up-to-4013-edge))
2. **The operator documents a fixed edge.** Its help page archived on 25 September 2023 reads
   *"Towes has a fixed house edge set at 5% for all 3 difficulty modes."* (original spelling), the Towers
   page captured on 7 October 2026 says the RTP *"is typically around 95%"*, and the current help page,
   captured on 28 October 2026, reads *"Towers has a fixed house edge set at 5% for all 3 difficulty
   modes."* ([C01](CLAIMS.md#c01-advertised-fixed-5-and-approximately-95-rtp))
3. **Observed payouts are consistent with the full compounded multiplier, not the 3-decimal ladder.**
   The client's 3-decimal ladder labels, as its JavaScript computes them, reproduce 40 of the 270
   November 2024 row payout values (2 of the 27 paid amounts) and 199 of the 330 October 2026 feed
   payouts; the exact multiplier truncated to 3 decimals reproduces 41 and 202. The full multiplier
   reproduces all of them, and so does truncation at 7 or 8 decimals, so the exact internal precision
   is not uniquely established. In 33 games played on 9 October 2026 ($18.09 staked) every result
   replays from the revealed seeds, and the ten selected balance readings are consistent with the same
   payouts (gross credits $19.84882796875). A $100 Easy row-2 win dated 13 November 2024 was paid 338,302 units (about $203.0624), shown as
   $203.06 (the 3-decimal ladder would pay $203.00).
   ([C03](CLAIMS.md#c03-33-game-replay-and-october-credits), [C04](CLAIMS.md#c04-historical-documentation-and-payouts))
4. **The same game in 2024 and 2026.** The records dated November 2024 use the same seed scheme (game seeds on
   the account's SHA-256 chain, positions 958 to 1923), the same tile-placement function (270 of 270 rows
   replay) and the same payout function as the October 2026 observations.
5. **Per winning bet, the difference against a fixed 5% is large at deep rows.** A $100 Medium cash-out
   after row 4 pays $1303.21 gross, against $1520.00 if 5% were charged once.
   ([C06](CLAIMS.md#c06-per-bet-winning-payout-comparisons))
6. **Fixed-return comparators.** Stake states a 2% edge (98% RTP) for Dragon Tower, one egg in four tiles
   for Master, and Master payouts of 3.92x and 256,901.12x at the first and top rows, which equal
   0.98 x 4^1 and 0.98 x 4^9; the rows between are calculated. Shuffle's official Tower chart lists the
   nine Hard (one-in-two) multipliers 1.96 ... 501.76, equal to 0.98 x 2^n. Neither is a live settlement
   audit. ([C05](CLAIMS.md#c05-fixed-return-competitor-comparison))

## What this repository does not show

- Randomness: replaying outcomes from revealed seeds is consistent with the published algorithm; it is
  not a test of uniformity.
- What the game did between the observed dates (November 2024, November 2025 client code, September
  2026 announcement, October 2026).
- Intent, or any contact with the operator before publication.
- Any aggregate or site-wide figure. The public feed leans heavily to wins (330 of 416 Towers entries),
  so it is used only to test the payout function.

## Layout

| path | contents |
|---|---|
| [evidence/client/](evidence/client/) | client code (live 2026-10-07 and archived 2025-11-01), Towers page, limits article, redesign announcement, current help pages (2026-10-28) |
| [evidence/help-history/](evidence/help-history/) | five historical help-centre captures (2023-2024) |
| [evidence/historical-bets-2024/](evidence/historical-bets-2024/) | raw server records of 27 November 2024 games (Wayback), share-page display, [analysis](evidence/historical-bets-2024/analysis.md) |
| [evidence/session-2026-10-09/](evidence/session-2026-10-09/) | session log and screenshots |
| [evidence/comparators/](evidence/comparators/) | Stake guide, game page and game-event rules; Shuffle chart and game-event rules |
| [data/](data/) | normalized inputs: payout parameters, session transcription, sanitized feed |
| [analysis/](analysis/) | verification scripts (Python standard library and Node) |
| [results/](results/) | generated tables and outputs ([tables.md](results/tables.md)) |
| [tests/](tests/) | independent expectations, negative tests, one labelled synthetic fixture |
| [SOURCES.json](SOURCES.json) | every source: URL, dates, hashes, transformations, claim coverage |
| [REDACTIONS.md](REDACTIONS.md) | privacy transformations and retained identifiers |
| [METHODOLOGY.md](METHODOLOGY.md) | how each item was collected, how the session was operated, precision and limits |
| [SHA256SUMS](SHA256SUMS) | hash of every distributed file |

## License and citation

Code in `analysis/` and `tests/`: MIT. Data, results and text: CC BY 4.0. Captured operator and
third-party material in `evidence/` remains its owners' and is not covered by either license. See
[LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Cite as: ProvablyFair.org, "500 Casino Towers technical evidence", version 1.0.0, October 2026.
