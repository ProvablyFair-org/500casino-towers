"""Replay and reconcile the 9 October 2026 session from saved inputs only.

No login, betting, seed rotation or network. Reads data/session-2026-10-09.json,
data/seed-panel-transcriptions.json and evidence/session-2026-10-09/log.redacted.txt. Writes only to --out.

Checks (any mismatch -> exit 1):
  * both server-seed commitments: sha256(revealed seed) == committed hash, full 64 hex, and the committed
    hashes equal their visual transcriptions from the seed-panel screenshots;
  * game-seed chain: g0 = account id, g(n+1) = sha256(g(n)); every observed value (verify links, panel,
    log) equals the chain at full 64-character length; g33 also equals the screenshot transcription;
  * all 33 games: outcome per pick from HMAC-SHA256(key=server seed, msg="client:game:round"), first 13
    hex digits -> index into the bomb arrangements; the logged result must be reproduced; 53 tiles;
  * screenshot layouts of games 0-2 (bomb tiles per row) must be reproduced;
  * ten selected balance readings under two settlement hypotheses (Decimal):
      H-3dp   credit = stake x floor(1000 x step^k)/1000   (literal three-decimal ladder value)
      H-full  credit = stake x step^k                      (full compounded multiplier)
    balance shown = running balance floored to the cent. These are settlement hypotheses compared at
    the precision the operator displayed; a match is not a statement about the server implementation.
    They are separate from the JavaScript display layer (analysis/client_ladders.mjs). The check FAILS
    unless all ten readings reconcile under H-full (the payout function the November 2024 server records
    and the October 2026 feed are consistent with); the H-3dp count is reported, not required.

Usage: python3 -I -B analysis/session_verify.py --out <dir>
"""
from decimal import Decimal as D, ROUND_FLOOR, getcontext
from itertools import combinations
from pathlib import Path
import argparse, hashlib, hmac, json, re, sys

getcontext().prec = 80
ROOT = Path(__file__).resolve().parents[1]
CHOICES = {'easy': (3, 1), 'medium': (2, 1), 'hard': (3, 2)}
STEP = {'easy': D('1.425'), 'medium': D('1.9'), 'hard': D('2.85')}
failures = []

def check(ok, msg):
    if not ok: failures.append(msg)
    return ok

def sha(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()

def bombs_for(server, client, game_seed, rnd, difficulty):
    c, b = CHOICES[difficulty]
    arr = list(combinations(range(c), b))
    digest = hmac.new(server.encode('utf-8'), f'{client}:{game_seed}:{rnd}'.encode('utf-8'), hashlib.sha256).hexdigest()
    idx = int(digest[:13], 16) * len(arr) // 2 ** 52      # exact integer form of floor(outcome x C)
    return set(arr[idx])

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    S = json.loads((ROOT / 'data/session-2026-10-09.json').read_text())
    TR = json.loads((ROOT / 'data/seed-panel-transcriptions.json').read_text())['transcriptions']
    log = (ROOT / 'evidence/session-2026-10-09/log.redacted.txt').read_text()
    res = {'scope': 'Outcome replay and balance reconciliation for 33 games on one test account. Does not test RNG uniformity and does not establish backend precision.'}

    # commitments
    pairs = S['server_seed_pairs']; commit_rows = []
    for pr in pairs:
        h = sha(pr['revealed_server_seed'])
        ok = check(len(pr['committed_hash']) == 64 and h == pr['committed_hash'], f'commitment pair {pr["pair"]}')
        check(pr['revealed_server_seed'] in log and pr['committed_hash'] in log, f'pair {pr["pair"]} values not found verbatim in log.txt')
        tr = [t for t in TR if t.get('commitment_pair') == pr['pair']]
        check(len(tr) >= 1 and all(t['value'] == pr['committed_hash'] for t in tr), f'pair {pr["pair"]} committed hash vs screenshot transcription')
        commit_rows.append({'pair': pr['pair'], 'sha256_of_revealed': h, 'committed': pr['committed_hash'], 'match': ok,
                            'screenshot_transcriptions_matching': len(tr)})
    res['commitments'] = commit_rows

    # chain
    g = [S['account_game_seed_root']['value']]
    for _ in range(33): g.append(sha(g[-1]))
    chain_rows = []
    for ob in S['game_seed_observations']:
        ok = check(g[ob['n']] == ob['value'] and (ob['n'] == 0 or len(ob['value']) == 64), f'chain n={ob["n"]}')
        check(ob['value'] in log, f'chain n={ob["n"]} value not verbatim in log.txt')
        chain_rows.append({'n': ob['n'], 'observed': ob['value'], 'computed': g[ob['n']], 'match': ok, 'source': ob['source']})
    for t in TR:
        if 'chain_n' in t:
            ok = check(g[t['chain_n']] == t['value'], f'chain n={t["chain_n"]} vs transcription from {t["image"]}')
            chain_rows.append({'n': t['chain_n'], 'observed': t['value'], 'computed': g[t['chain_n']], 'match': ok, 'source': 'visual transcription: ' + t['image']})
    res['chain'] = chain_rows
    res['final_chain_value_full'] = g[33]

    # replay
    games = S['games']; check(len(games) == 33 and [x['n'] for x in games] == list(range(33)), 'game list')
    replay = []; tiles = 0; cash = 0; staked = D(0)
    pair_for = lambda n: pairs[0] if n < 3 else pairs[1]
    for gm in games:
        pr = pair_for(gm['n']); result = None; picks_checked = 0
        for k, pick in enumerate(gm['picks']):
            bombs = bombs_for(pr['revealed_server_seed'], pr['client_seed'], g[gm['n']], k, gm['difficulty'])
            picks_checked += 1
            if pick in bombs:
                result = f'bomb@{k + 1}'
                check(k == len(gm['picks']) - 1, f'game {gm["n"]}: picks recorded after a bomb')
                break
        result = result or f'cash@{len(gm["picks"])}'
        tiles += picks_checked; staked += D(gm['stake']); cash += result.startswith('cash')
        ok = check(result == gm['logged'], f'game {gm["n"]} {gm["label"]}: replay {result} vs logged {gm["logged"]}')
        replay.append({'n': gm['n'], 'label': gm['label'], 'difficulty': gm['difficulty'], 'stake': gm['stake'], 'picks': gm['picks'],
                       'logged': gm['logged'], 'replayed': result, 'match': ok, 'game_seed': g[gm['n']], 'server_seed_pair': pr['pair']})
    res['replay'] = replay
    res['counts'] = {'games': len(games), 'games_matching': sum(r['match'] for r in replay), 'tiles_replayed': tiles,
                     'cash_outs': cash, 'bombs': len(games) - cash, 'staked': str(staked), 'commitments_matching': sum(r['match'] for r in commit_rows)}

    # screenshot layouts
    lay_rows = []
    for sl in S['screenshot_layouts']['games']:
        gm = games[sl['n']]; pr = pair_for(sl['n'])
        for row, want in sl['rows'].items():
            got = sorted(bombs_for(pr['revealed_server_seed'], pr['client_seed'], g[sl['n']], int(row) - 1, gm['difficulty']))
            ok = check(got == sorted(want), f'layout game {sl["n"]} row {row}: {got} vs screenshot {want}')
            lay_rows.append({'n': sl['n'], 'row': int(row), 'screenshot_bombs': want, 'replayed_bombs': got, 'match': ok, 'source': sl['source']})
    res['screenshot_layouts'] = lay_rows

    # reconciliation
    readings = {r['after_game']: r['displayed'] for r in S['balance_readings_selected']}
    hyps = {'H-3dp': lambda m: m.quantize(D('0.001'), rounding=ROUND_FLOOR), 'H-full': lambda m: m}
    recon = {}
    for name, f in hyps.items():
        bal = D(S['start_balance']['value']); credits = D(0); per = []; matches = 0
        for gm, rp in zip(games, replay):
            credit = D(0)
            if rp['replayed'].startswith('cash'):
                k = int(rp['replayed'].split('@')[1]); credit = D(gm['stake']) * f(STEP[gm['difficulty']] ** k)
            bal += credit - D(gm['stake']); credits += credit
            shown = bal.quantize(D('0.01'), rounding=ROUND_FLOOR)
            row = {'after_game': gm['n'], 'credit': format(credit.normalize(), 'f') if credit else '0', 'balance_exact': format(bal.normalize(), 'f'), 'balance_shown_floor_cent': str(shown)}
            if gm['n'] in readings:
                row['reading'] = readings[gm['n']]; row['match'] = str(shown) == readings[gm['n']]; matches += row['match']
            per.append(row)
        recon[name] = {'credits_total': format(credits.normalize(), 'f'), 'final_balance_exact': format(bal.normalize(), 'f'),
                       'final_balance_shown': str(bal.quantize(D('0.01'), rounding=ROUND_FLOOR)), 'selected_readings_matched': matches, 'per_game': per}
    res['reconciliation'] = recon
    ex = S['balance_readings_excluded'][0]
    res['excluded_reading'] = {**ex, 'any_boundary_shows_it': {h: [r['after_game'] for r in recon[h]['per_game'] if r['balance_shown_floor_cent'] == ex['displayed']] for h in recon}}

    c = res['counts']
    check(c['games'] == 33 and c['games_matching'] == 33, '33/33 games')
    check(c['tiles_replayed'] == 53, '53 tiles'); check(c['cash_outs'] == 13 and c['bombs'] == 20, '13 cash-outs / 20 bombs')
    check(c['staked'] == '18.09', 'staked 18.09'); check(c['commitments_matching'] == 2, '2/2 commitments')
    check(len(readings) == 10, 'ten selected readings')
    check(recon['H-full']['selected_readings_matched'] == len(readings), f"balance readings reconcile under H-full ({recon['H-full']['selected_readings_matched']}/{len(readings)})")
    res['failures'] = failures
    (out / 'session-2026-10-09.json').write_text(json.dumps(res, indent=1) + '\n')
    print(f"session: games {c['games_matching']}/{c['games']}, tiles {c['tiles_replayed']}, cash-outs {c['cash_outs']}, bombs {c['bombs']}, staked {c['staked']}, "
          f"commitments {c['commitments_matching']}/2, chain observations {sum(r['match'] for r in chain_rows)}/{len(chain_rows)}, "
          f"screenshot layout rows {sum(r['match'] for r in lay_rows)}/{len(lay_rows)}; "
          + '; '.join(f"{h}: credits {v['credits_total']}, final {v['final_balance_exact']} (shown {v['final_balance_shown']}), readings {v['selected_readings_matched']}/10" for h, v in recon.items())
          + f"; failures: {len(failures)}")
    for f_ in failures: print('FAIL:', f_, file=sys.stderr)
    return 0 if not failures else 1

if __name__ == '__main__':
    sys.exit(main())
