"""Offline source checks: captured client code, verbatim quotations, nested manifests, source inventory
hashes and relative links. Reads files; executes none of the captured code.

Usage: python3 -I -B analysis/source_check.py --out <dir>
"""
from pathlib import Path
import argparse, gzip, hashlib, json, re, sys

ROOT = Path(__file__).resolve().parents[1]
failures = []

def check(ok, msg):
    if not ok: failures.append(msg)
    return ok

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

CHUNK = 'evidence/client/towers-chunk-2026-10-07/'
LITERALS = [  # (file, byte offset or None, exact bytes)
    ('evidence/client/towers-live-2026-10-07/js/app.3088e4a4.js', 1363940, b'towersHouseEdge:.05'),
    (CHUNK + '1828.89aa27f6.js', 33117, b'roundMultiplier:function(){var t=this.difficultyData.choices/(this.difficultyData.choices-this.difficultyData.bombs),e=1-this.game.houseEdge;return new l.A(t).times(e).toNumber()}'),
    (CHUNK + '1828.89aa27f6.js', None, b'.push({value:parseInt(i*Math.pow(this.roundMultiplier,a)),multiplier:Math.floor(1e3*Math.pow(this.roundMultiplier,a))/1e3}'),
    (CHUNK + '1828.89aa27f6.js', None, b'multiplierText:function(){var t=Math.floor(100*this.multiplier)/100;return"".concat(t.toFixed(2),"x")}'),
    (CHUNK + '1828.89aa27f6.js', None, b'r=i.houseEdge'),
    (CHUNK + 'archived-towers.55a86d17.js', None, b'roundMultiplier(){const e=this.difficultyData.choices/(this.difficultyData.choices-this.difficultyData.bombs),t=1-this.game.houseEdge;return new o.a(e).times(t).toNumber()}'),
    (CHUNK + 'archived-towers.55a86d17.js', None, b'.push({value:parseInt(i*this.roundMultiplier**a),multiplier:Math.floor(this.roundMultiplier**a*1e3)/1e3}'),
    (CHUNK + 'archived-towers.55a86d17.js', None, b'houseEdge:i,minBet:a}=e.data'),
    (CHUNK + 'archived-headers.redacted.txt', None, b'memento-datetime: Sat, 01 Nov 2025 02:54:05 GMT'),
    (CHUNK + 'archived-headers.redacted.txt', None, b'link: <https://500.casino/static/js/towers.55a86d17.js>; rel="original"'),
]
QUOTES = [  # (file, verbatim text) - quoted in CLAIMS.md / README.md
    ('evidence/help-history/2023-09-25-odds.txt', 'Towes has a fixed house edge set at 5% for all 3 difficulty modes.'),
    ('evidence/help-history/2023-09-25-odds.txt', 'The odds of Easy difficulty is 0.6666 per level.'),
    ('evidence/help-history/2023-09-25-odds.txt', 'The odds of Medium difficulty is 0.5 per level.'),
    ('evidence/help-history/2023-09-25-odds.txt', 'The odds of Hard difficulty is 0.3333 per level.'),
    ('evidence/help-history/2023-09-25-house-edge.txt', "The house edge on Towers functions similar to as of Duels' and is set at 5%."),
    ('evidence/help-history/2023-09-25-house-edge.txt', '500 Casino takes a fixed 5% rake for every played duel.'),
    ('evidence/help-history/2023-09-25-limits.txt', 'Towers has a global win limit of $100,000 per round.'),
    ('evidence/help-history/2023-09-25-limits.txt', 'The maximum multiplier for Easy is ~345x.'),
    ('evidence/help-history/2023-09-25-limits.txt', 'the maximum bet is up to ~$163.10 per round.'),
    ('evidence/help-history/2024-04-19-limits.txt', 'Towers has a global win limit of $200,000 per round.'),
    ('evidence/help-history/2024-04-19-limits.txt', 'The maximum multiplier for Easy is ~34,5x.'),
    ('evidence/help-history/2024-04-19-limits.txt', 'the maximum bet is up to ~$326.20 per round.'),
    ('evidence/help-history/2024-12-08-limits.txt', 'the maximum bet is up to ~$326.20 per round.'),
    ('evidence/client/limits-article-2026-10-07/page.txt', 'Towers has a global win limit of $200,000 per round.'),
    ('evidence/client/limits-article-2026-10-07/page.txt', 'May 21, 2024'),
    ('evidence/client/towers-live-2026-10-07/page-excerpt.txt', 'The game’s RTP is typically around 95%'),
    ('evidence/comparators/stake-dragon-tower-blog-2026-10-07/page.txt', 'for Dragon Tower is 2%, which means that the theoretical RTP is 98%.'),
    ('evidence/comparators/stake-dragon-tower-blog-2026-10-07/page.txt', 'a correct prediction at the bottom of the tower will result in a payout of 3.92x your stake, and if you make it to the top, the payout will be a massive 256,901.12x.'),
    ('evidence/client/redesign-tweet-2026-10-07/syndication.json', '"created_at":"2026-09-14T10:09:41.000Z"'),
    ('evidence/client/redesign-tweet-2026-10-07/syndication.json', 'TOWERS redesign is live'),
    # current pages captured 2026-10-28
    ('evidence/client/help-odds-of-towers-2026-10-28/page.txt', 'Towers has a fixed house edge set at 5% for all 3 difficulty modes.'),
    ('evidence/client/help-odds-of-towers-2026-10-28/page.txt', 'The odds of Easy difficulty is 0.6666 per level.'),
    ('evidence/client/help-odds-of-towers-2026-10-28/page.txt', 'The odds of Medium difficulty is 0.50 per level.'),
    ('evidence/client/help-odds-of-towers-2026-10-28/page.txt', 'The odds of Hard difficulty is 0.3333 per level.'),
    ('evidence/client/help-odds-of-towers-2026-10-28/page.txt', 'April 29, 2024'),
    ('evidence/client/help-house-edge-2026-10-28/page.txt', "The house edge on Towers functions similar to as of Duels' and is set at 5%."),
    ('evidence/client/help-house-edge-2026-10-28/page.txt', '500 Casino takes a fixed 5% rake for every played duel.'),
    ('evidence/client/help-house-edge-2026-10-28/page.txt', 'June 6, 2026'),
    ('evidence/comparators/shuffle-tower-chart-2026-10-28/page.txt', 'Please note that the multipliers have been visually truncated to 2 decimal points for readability.'),
    ('evidence/comparators/shuffle-game-events-2026-10-28/page.txt', 'There are a total of 9 rows in the tower.'),
    ('evidence/comparators/shuffle-game-events-2026-10-28/page.txt', 'Hard: 2 columns - 1 key and 1 poison apple per row'),
    ('evidence/comparators/stake-game-events-2026-10-28/page.txt', 'A Dragon Tower game is generated with 9 separate game events'),
    ('evidence/comparators/stake-game-events-2026-10-28/page.txt', 'master: { count: 1, size: 4 },'),
    ('evidence/comparators/stake-dragon-tower-game-2026-10-28/page.redacted.txt', 'Retorno ao jogador:\u00a0\n98,00%'),
    ('evidence/comparators/stake-dragon-tower-game-2026-10-28/page.redacted.txt', 'of 98%, meaning that the Dragon Tower \nhouse edge\n is just 2%.'),
    ('evidence/comparators/stake-dragon-tower-blog-2026-10-28/page.txt', 'for Dragon Tower is 2%, which means that the theoretical RTP is 98%.'),
    ('evidence/comparators/stake-dragon-tower-blog-2026-10-28/page.txt', 'a correct prediction at the bottom of the tower will result in a payout of 3.92x your stake, and if you make it to the top, the payout will be a massive 256,901.12x.'),
]
NESTED = [  # (manifest, expected sha256 of the manifest itself or None)
    ('evidence/help-history/SHA256SUMS.txt', None),
]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    res = {'literals': [], 'quotes': [], 'nested_manifests': [], 'sources_json': {}, 'links': {}}
    for f, off, lit in LITERALS:
        b = (ROOT / f).read_bytes()
        found = b.find(lit) if off is None else (off if b[off:off + len(lit)] == lit else -1)
        ok = check(found >= 0, f'literal not found in {f} at {off}: {lit[:60]!r}')
        res['literals'].append({'file': f, 'required_offset': off, 'found_offset': found, 'text': lit.decode(), 'ok': ok})
    gz = gzip.decompress((ROOT / CHUNK / 'archived-towers.55a86d17.js.gz').read_bytes())
    res['archived_gzip_decompresses_to_js'] = check(gz == (ROOT / CHUNK / 'archived-towers.55a86d17.js').read_bytes(), 'archived gzip != js')
    live_dup = ROOT / 'evidence/client/towers-live-2026-10-07/js-index.json'
    idx = json.loads(live_dup.read_text())
    res['js_index_lists_both_towers_files'] = check({'1828.89aa27f6.js', 'towers.af02258b.js', 'app.3088e4a4.js'} <= {e['file'] for e in idx}, 'js-index entries')
    for f, q in QUOTES:
        ok = check(q in (ROOT / f).read_text(), f'quote not verbatim in {f}: {q[:60]}')
        res['quotes'].append({'file': f, 'quote': q, 'ok': ok})
    for man, want in NESTED:
        mp = ROOT / man; lines = [l for l in mp.read_text().splitlines() if l.strip()]; good = 0
        for l in lines:
            h, name = l.split(None, 1); name = name.lstrip('*')
            good += check(sha(mp.parent / name) == h, f'{man}: {name}')
        own = sha(mp); ok_own = True if want is None else check(own == want, f'{man}: manifest hash {own} != {want}')
        res['nested_manifests'].append({'manifest': man, 'entries': len(lines), 'entries_ok': good, 'manifest_sha256': own, 'expected_manifest_sha256': want, 'manifest_hash_ok': ok_own})
    # SOURCES.json inventory: every public path exists with the recorded hash, and every file under
    # evidence/ and data/ is listed (complete provenance inventory)
    S = json.loads((ROOT / 'SOURCES.json').read_text()); n = bad = 0; listed = set()
    for src in S['sources']:
        for pf in src['public_files']:
            n += 1; listed.add(pf['public_path'])
            p = ROOT / pf['public_path']
            if not check(p.is_file() and sha(p) == pf['public_sha256'], f'SOURCES.json: {pf["public_path"]}'): bad += 1
    on_disk = sorted(str(p.relative_to(ROOT)) for d in ('evidence', 'data') for p in (ROOT / d).rglob('*') if p.is_file())
    unlisted = [f for f in on_disk if f not in listed]
    for f in unlisted: check(False, f'SOURCES.json: {f} is not listed')
    res['sources_json'] = {'public_files_listed': n, 'mismatches': bad, 'evidence_and_data_files': len(on_disk), 'unlisted': unlisted}
    # relative links in markdown resolve
    nlinks = broken = 0
    for md in sorted(ROOT.rglob('*.md')):
        if '.git' in md.parts or 'evidence' in md.parts: continue
        for target in re.findall(r'\]\(([^)\s]+)\)', md.read_text()):
            if re.match(r'[a-z]+:', target) or target.startswith('#'): continue
            nlinks += 1
            if not check((md.parent / target.split('#')[0]).exists(), f'broken link in {md.relative_to(ROOT)}: {target}'): broken += 1
    res['links'] = {'relative_links_checked': nlinks, 'broken': broken}
    res['failures'] = failures
    (out / 'source-checks.json').write_text(json.dumps(res, indent=1) + '\n')
    print(f"sources: literals {sum(x['ok'] for x in res['literals'])}/{len(LITERALS)}, quotes {sum(x['ok'] for x in res['quotes'])}/{len(QUOTES)}, "
          f"nested manifests {sum(m['entries_ok'] == m['entries'] and m['manifest_hash_ok'] for m in res['nested_manifests'])}/{len(NESTED)}, "
          f"SOURCES.json files {n - bad}/{n} (unlisted evidence/data files {len(unlisted)}), relative links {nlinks - broken}/{nlinks}; failures: {len(failures)}")
    for f in failures: print('FAIL:', f, file=sys.stderr)
    return 0 if not failures else 1

if __name__ == '__main__':
    sys.exit(main())
