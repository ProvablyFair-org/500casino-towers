# Offline verification

Requirements: Python 3 (standard library only) and Node.js. No network access, account, API key,
wager, collector or package install is used. From a fresh checkout, at the repository root:

```
python3 -I -B analysis/run_all.py            # all checks; writes to a new temporary folder
python3 -I -B tests/run_negative.py          # every check must fail when one input is changed
```

`run_all.py` prints the output folder; `verification-log.txt` in it records the runtimes, each step
and the before/after digest of `evidence/` and `data/`. To write elsewhere: `--out DIR`. Nothing in
the repository is modified by either command. `NODE=/path/to/node` selects a Node binary.

Runtimes: CI ([.github/workflows/verify.yml](.github/workflows/verify.yml)) pins Python 3.12.14 and
Node 24.19.0. Release v1.0.0 was checked locally with Python 3.12.12, 3.13.16 and 3.9.6, and Node 22.22.0, 22.23.1 and 26.7.0.

## Steps and expected results

| step | command (inside run_all) | expected |
|---|---|---|
| 1 input integrity | every line of [SHA256SUMS](SHA256SUMS) | all files match; no distributed file unlisted |
| 2 snapshot | sha256 of every file under `evidence/` and `data/` | recorded |
| 3 client display layers | `node analysis/client_ladders.mjs --out OUT` | `30 rows; live/archived expression mismatches: 0` |
| 4a payout mathematics | `python3 -I -B analysis/payout_math.py --out OUT` | `30 ladder rows, 10 curve rows, 10 $100 Medium examples, 30 UI labels checked, 18 comparator rows; failures: 0` |
| 4b session | `python3 -I -B analysis/session_verify.py --out OUT` | `games 33/33, tiles 53, cash-outs 13, bombs 20, staked 18.09, commitments 2/2, chain observations 10/10, screenshot layout rows 18/18; H-3dp: credits 19.84574, final 102.23574 (shown 102.23), readings 10/10; H-full: credits 19.84882796875, final 102.23882796875 (shown 102.23), readings 10/10; failures: 0` |
| 4c November 2024 records | `python3 -I -B analysis/historical_verify.py --out OUT` | `games 27, rows replayed 270/270, played rows safe 82/82, seeds on chain 27/27 (positions 958-1923, date order True), row payout values full 270/270, exact multiplier truncated 3/4/5/6/7/8 dp 41/105/255/269/270/270, client JS 3-dp labels 40/270, paid cash-outs full 27/27 (client labels 2/27), above fixed-5% 0, units 1666=$1 stake 27/27 win 27/27; failures: 0` |
| 4d feed | `python3 -I -B analysis/feed_verify.py --out OUT` | `entries 416, winners 330, zero payouts 86, unique matches 330, unmatched 0, ambiguous 0, equal floor 330, exact multiplier truncated 3/4/5/6/7/8 dp 202/309/321/330/330/330, client JS 3-dp labels 199/330, unrounded equal/below/above 6/324/0; failures: 0` |
| 4e sources | `python3 -I -B analysis/source_check.py --out OUT` | `literals 10/10, quotes 37/37, nested manifests 1/1, SOURCES.json files N/N (unlisted evidence/data files 0), relative links N/N; failures: 0` |
| 4f privacy | `python3 -I -B analysis/privacy_scan.py --out OUT` | `unexpected 0` |
| 5 expectations | results vs [tests/expected/expected.json](tests/expected/expected.json) (hand-written literals) | `0 mismatches` |
| 6 claim index | [claims-index.json](claims-index.json) values vs results and documents | `43 values`, all equal and present |
| 7 committed results | fresh outputs vs [results/](results/) | byte-identical |
| 8 no mutation | snapshot after = snapshot before | unchanged |

The 4c and 4d checks fail if any payout is not reproduced by the full multiplier; 4b fails if the ten balance
readings do not reconcile under the full multiplier; 4e fails if any file under `evidence/` or `data/` is missing
from SOURCES.json. Step 5 also checks that the Python re-evaluation of the client's JavaScript labels (used for the
client-label counts in 4c and 4d) equals the JavaScript output of step 3. The run ends with
`RESULT: PASS (0 failed step(s))`. The negative tests change, in a temporary copy, a multiplier, a bet
amount, a balance reading, a server seed, a committed hash, the final chain transcription, a logged pick, a November 2024
server payout and game seed, a share-page displayed win, a feed payout, the captured client code, a quoted
source, an official chart value and one evidence byte; each must make its check exit non-zero, an
unmodified copy must pass, and the checkout must be unchanged afterwards.

## Material limitations

The checks validate the included evidence and arithmetic. They do not establish RNG uniformity or what
the game did between the observed dates, and they do not check the report's financial analysis.
