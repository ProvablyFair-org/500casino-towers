"""Extract the Towers payout-math snippets from the archived (1 Nov 2025) and current (7 Oct 2026) chunks.
Prints each pattern's verbatim match per file, so the comparison can be re-run from the saved files."""
import re, hashlib
FILES = {
  'archived 2025-11-01 towers.55a86d17.js (Wayback 20251101025405, decompressed)': 'archived-towers.55a86d17.js',
  'current 2026-10-07 1828.89aa27f6.js (loaded by https://500.casino/towers)': '1828.89aa27f6.js',
  'current 2026-10-07 towers.af02258b.js (loaded by https://500.casino/towers)': 'towers.af02258b.js',
}
PATTERNS = {
  'roundMultiplier':   r'roundMultiplier(?:\(\)|:function\(\))\{[^}]*\}',
  'ladder (winningsByRound push)': r'\.push\(\{value:parseInt\([^)]*\)+,multiplier:[^}]*\}',
  'houseEdge source (getInfo)': r'houseEdge:i,minBet:a\}=e\.data|r=i\.houseEdge',
  'tile display multiplierText': r'multiplierText(?:\(\)|:function\(\))\{[^}]*\}',
  'resultMultiplierText': r'resultMultiplierText(?:\(\)|:function\(\))\{[^}]*\}',
}
for label, f in FILES.items():
    b = open(f, 'rb').read(); s = b.decode('utf-8', 'replace')
    print(f'## {label}\nsha256 {hashlib.sha256(b).hexdigest()}  bytes {len(b)}')
    for name, pat in PATTERNS.items():
        ms = [m.group(0) for m in re.finditer(pat, s)]
        print(f'- {name}: {len(ms)} match(es)')
        for m in dict.fromkeys(ms): print(f'    {m}')
    print()
