# Redactions, retained identifiers and lineage

Every distributed evidence or data file is listed in [SOURCES.json](SOURCES.json) with its original
sha256, its public sha256 and the transformation between them. Originals that were redacted are kept
privately by ProvablyFair.org and are not in this repository or its history. Redactions were made with
deterministic code (solid rectangles, line or token removal), never with generative tools, and only
outside claim-relevant content.

## Transformations

| public file | original | transformation | why |
|---|---|---|---|
| `evidence/session-2026-10-09/log.redacted.txt` | `log.txt` | one token replaced: the browser tab id | not needed to verify anything |
| `evidence/session-2026-10-09/shots/*.redacted.png` (13 files) | the same names as .jpg/.png | solid black rectangles over areas already pixelated before assembly; re-encoded as PNG | live-wins ticker, High Wins and bet tables showing other players' usernames, avatars and levels |
| `evidence/client/towers-live-2026-10-07/screenshot.redacted.png` | `screenshot.png` | three solid rectangles | ticker, High Wins and All Bets usernames of other players |
| `evidence/client/towers-live-2026-10-07/page-excerpt.txt` | `page.txt` | verbatim lines 428-473 and 775-838 only | the rest is public chat and bet tables with other players' usernames |
| `evidence/client/redesign-tweet-2026-10-07/x-page/page.redacted.txt` | `x-page/page.txt` | lines 16-32 replaced by one marked line | three replies by third-party accounts |
| `evidence/client/redesign-tweet-2026-10-07/x-page/screenshot.redacted.png` | `x-page/screenshot.png` | one solid rectangle | the same replies |
| `evidence/client/towers-chunk-2026-10-07/archive.ph-uAhyA.redacted.html` | `archive.ph-uAhyA.html` | the `<head>` comment (original lines 1-4) replaced by one marked comment | archive.ph writes a per-request comment with a token, the browser user agent and the requesting machine's IP address |
| `evidence/client/towers-chunk-2026-10-07/archived-headers.redacted.txt` | `archived-headers.txt` | the `x-as`, `x-nid` and `set-cookie` lines removed | requester network and the archive's load-balancer cookie |
| `evidence/historical-bets-2024/wayback-raw/*.headers.redacted.txt` (27) | response headers | the `x-as`, `x-nid`, `set-cookie` and `x-archive-orig-set-cookie` lines removed | requester network, archive cookie, and the session cookie the operator set on the archiving request |
| `evidence/historical-bets-2024/share-page-display.json` | transcription of the share pages | displayed fields only | usernames, avatars and verifier-link parameters were never transcribed |
| `evidence/comparators/stake-dragon-tower-game-2026-10-28/page.redacted.txt` | rendered text | lines 352-471 (live bets table) replaced by one marked line | other players' usernames, stakes and payouts |
| `evidence/*/*-2026-10-28/capture.json` (7) | capture metadata | derived: URLs, title, acquisition time, language, hashes; capture tool name and full browser user agent omitted | capture-side detail, not page content |
| page HTML of the seven 2026-10-28 captures | page HTML | not distributed; sha256 in each `capture.json` | extension-injected markup of the capturing browser (01-04), Cloudflare per-request parameters (01, 03, 05), live bets table (05); 06 and 07 withheld under the same rule |
| `data/feed/towers-entries.sanitized.jsonl` | three raw feed files (all games) | Towers entries only; usernames, avatar URLs, levels, roles, account ids and transaction ids removed | other players' identifiers; transaction ids are not needed for payout matching |
| `data/feed/collection-gaps.jsonl` | `gaps.ndjson` | process id and launch flag removed | not evidence |

Rectangle coordinates and line numbers for every file are in the `transformations` field of SOURCES.json.
Page HTML and link lists of pages showing other players or third-party accounts, unrelated and third-party
scripts, the raw feed and the collector are not distributed (reasons in SOURCES.json).

## Review (28 October 2026)

- Every image in the repository was viewed at full resolution after redaction: 32 session screenshots, 4 page
  screenshots of 7 October 2026, 1 announcement image, 4 historical help screenshots and the 8 screenshots of
  the 28 October 2026 captures.
- `analysis/privacy_scan.py` (text patterns including e-mail addresses, credentials, IPv4/IPv6 addresses,
  archive requester comments and requester-network headers; image metadata; player fields in `data/` and
  `results/`; the synthetic-fixture boundary) passes; every finding and the reason it is allowed are in
  `results/privacy-scan.json`. The remaining IPv4-shaped strings are SVG path coordinates in captured markup.
- A separate scan searched every distributed text file for each account id, avatar URL and username present in
  the raw feed corpus (4,260 account ids, 2,294 avatar URLs, 2,590 usernames) and for the third-party handles seen
  in captured pages. It found no account id or avatar URL; its username hits were ordinary words inside captured
  code and HTML ("Collapse", "Anonymous", "Slaughter", "opponent", "nt bro").
- No authentication secret, session cookie or password is distributed. Revealed server seeds are retired seeds
  needed for replay, not credentials.
- The four historical help screenshots are named `.png` but contain JPEG data; they are kept byte-identical.

## Retained identifiers

Kept because the verification uses them:

- **October 2026 test account**: account id `6a9ae61b8fb4004f64eae1e0` (root of its game-seed chain; the
  operator's public username is `user-` plus its last six hex digits, `user-eae1e0`). It appears in the log,
  `data/session-2026-10-09.json` and screenshots S02/S03; the account is identifiable. Its screens in the
  screenshots (avatar, level badge, balance) are part of the readings used for reconciliation; the username is
  masked.
- **October 2026 seeds and bets**: revealed server seeds `c32b9c84...770f` and `a558bb39...116e`, the later
  committed hashes shown on screen, client seeds `97BCXIhqj6`, `pf500radb9081b2d` and `pf500r941933b51b`, four
  bet ids and the operator's verify links.
- **November 2024 account** (records published with the account holder's consent): account id
  `66d8a460c92633f73b8f9dd7`, username `user-8f9dd7`, level and the other fields of the operator's own
  share-bet records, 27 game ids and share URLs, two revealed server seeds and two client seeds.
- **Feed entries**: receipt and event timestamps, raw amounts and currency labels per Towers entry (no player
  field); someone holding the operator's own records could link an entry to a player.
