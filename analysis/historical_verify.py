"""Verify the 27 November 2024 Towers games from the operator's raw share-bet JSON (as archived by the
Wayback Machine, evidence/historical-bets-2024/wayback-raw/).

For every game, from the record's own fields:
  * replay: each of the 10 rows' bomb tiles (field `bombs`, 1 = bomb) must equal the placement computed
    from the revealed server seed, client seed and game seed (HMAC-SHA256, first 13 hex digits -> index
    into the bomb arrangements) - the same function used for the October 2026 session;
  * every played row (`choice`) must be a safe tile, and `winWorth` must equal the payout of the cash-out row;
  * chain: each game seed must lie on the SHA-256 chain of the account id (game seed n = sha256^n(id));
    positions must increase with the game date;
  * payouts: the record lists a server-computed payout for each of its 10 rows (270 row payout values in
    all); 27 of them, one per game, are the amounts actually paid (the cash-out row). Each is compared, in
    integer units, with
        floor(stake x step^n)               full compounded multiplier
        floor(stake x trunc_k(step^n))      exact multiplier truncated to k = 3, 4, 5, 6, 7, 8 decimals
        floor(stake x label3(n))            the client's 3-decimal ladder label as JavaScript evaluates it,
                                            Math.floor(1e3*Math.pow(step,n))/1e3 with the client's Number step
                                            (differs from exact 3-decimal truncation at Medium row 3: 6.858)
    The check FAILS unless the full multiplier reproduces every row payout value and every paid amount;
  * fixed-5% benchmark per row: stake x 0.95 x (choices/safe)^n;
  * units and display: stake/1666 and winWorth/1666, rounded to cents, against what the share page displayed
    (share-page-display.json); displayed time minus server UTC.

Usage: python3 -I -B analysis/historical_verify.py --out <dir>
"""
from decimal import Decimal as D, ROUND_FLOOR, ROUND_HALF_UP, getcontext
from collections import Counter
from itertools import combinations
from pathlib import Path
import argparse, datetime, hashlib, hmac, json, math, sys

getcontext().prec = 80
ROOT = Path(__file__).resolve().parents[1]
HD = ROOT / 'evidence/historical-bets-2024'
CH = {'easy': (3, 1), 'medium': (2, 1), 'hard': (3, 2)}
STEP = {'easy': D('1.425'), 'medium': D('1.9'), 'hard': D('2.85')}
UNITS_PER_USD = D(1666)
TRUNC = (3, 4, 5, 6, 7, 8)
PARAMS = json.loads((ROOT / 'data/payout-parameters.json').read_text())['towers']['difficulties']
failures = []

def client_label3(mode, n):
    # the captured client's ladder label, evaluated in IEEE doubles exactly as the JavaScript writes it;
    # analysis/run_all.py checks these 30 values against the JavaScript output of analysis/client_ladders.mjs
    return D(format(math.floor(1e3 * math.pow(float(PARAMS[mode]['client_step_number']), n)) / 1e3, '.3f'))

def check(ok, msg):
    if not ok: failures.append(msg)
    return ok

def placement(server, client, game, rnd, difficulty):
    c, b = CH[difficulty]; arr = list(combinations(range(c), b))
    d = hmac.new(server.encode(), f'{client}:{game}:{rnd}'.encode(), hashlib.sha256).hexdigest()
    return arr[int(d[:13], 16) * len(arr) // 2 ** 52]

def fl(x): return x.to_integral_value(rounding=ROUND_FLOOR)
def trunc(m, k): return m.quantize(D(1).scaleb(-k), rounding=ROUND_FLOOR)
def cents(x): return x.quantize(D('0.01'), rounding=ROUND_HALF_UP)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    idx = json.loads((HD / 'wayback-raw/index.json').read_text())['records']
    recs = []
    for e in idx:
        b = (HD / 'wayback-raw' / f"{e['game_id']}.json").read_bytes()
        check(hashlib.sha256(b).hexdigest() == e['body_sha256'], f"{e['game_id']}: body hash")
        recs.append(json.loads(b))
    disp = {d['bet_id']: d for d in json.loads((HD / 'share-page-display.json').read_text())['records']}
    c = Counter(); rows_out = []; payout_rows = []
    accounts = {r['user']['id'] for r in recs}; check(len(accounts) == 1, 'records from one account')
    root = recs[0]['user']['id']; seeds = {r['gameSeed'] for r in recs}; pos = {}; g = root
    for n in range(1, 20001):
        g = hashlib.sha256(g.encode()).hexdigest()
        if g in seeds: pos[g] = n
    for r in recs:
        mode = r['difficultyString']; c0, b0 = CH[mode]; w = D(r['worth'])
        check(r['difficultyData'] == {'key': mode, 'choices': c0, 'bombs': b0}, f"{r['id']}: difficulty data")
        check(len(r['rounds']) == 10, f"{r['id']}: 10 rows")
        for k, x in enumerate(r['rounds']):
            got = tuple(i for i, v in enumerate(x['bombs']) if v == 1)
            ok = got == placement(r['serverSeed'], r['clientSeed'], r['gameSeed'], k, mode)
            c['rows'] += 1; c['rows_replayed'] += ok; check(ok, f"{r['id']} row {k + 1}: replay")
            if 'choice' in x:
                c['rows_played'] += 1; c['played_rows_safe'] += x['bombs'][x['choice']] == 0
            m = STEP[mode] ** (k + 1); p = D(x['payout']); bench = w * D('0.95') * (D(c0) / D(c0 - b0)) ** (k + 1)
            paid = k + 1 == r['currentRound']
            c['payout_full'] += p == fl(w * m)
            for t in TRUNC: c[f'payout_trunc{t}'] += p == fl(w * trunc(m, t))
            c['payout_client_label3'] += p == fl(w * client_label3(mode, k + 1))
            if paid:
                c['cashouts'] += 1; c['cashout_full'] += p == fl(w * m)
                for t in TRUNC: c[f'cashout_trunc{t}'] += p == fl(w * trunc(m, t))
                c['cashout_client_label3'] += p == fl(w * client_label3(mode, k + 1))
            c['payout_below_fixed5'] += p < bench; c['payout_above_fixed5'] += p > bench
            if k >= 1: c['rows2plus'] += 1; c['rows2plus_below_fixed5'] += p < fl(bench)
            payout_rows.append({'game': r['id'], 'row': k + 1, 'paid_cash_out': paid, 'stake_units': int(w), 'payout_units': int(p), 'full_prediction': format((w * m).normalize(), 'f'),
                                'fixed5_benchmark_units': format(bench.normalize(), 'f')})
        c['winworth_equals_cashout_row'] += r['winWorth'] == r['rounds'][r['currentRound'] - 1]['payout']
        c['on_chain'] += r['gameSeed'] in pos
        dd = disp.get(r['id']);
        if dd:
            c['display_records'] += 1
            c['stake_units_match_display'] += cents(w / UNITS_PER_USD) == D(dd['displayed_stake_usd'])
            c['win_units_match_display'] += cents(D(r['winWorth']) / UNITS_PER_USD) == D(dd['displayed_gross_win_usd'])
            u = datetime.datetime.fromisoformat(r['date'].replace('Z', '+00:00')).replace(tzinfo=None, microsecond=0)
            shown = datetime.datetime.strptime(dd['displayed_datetime'], '%m/%d/%Y, %I:%M:%S %p')
            c[f'display_offset_hours_{(shown - u).total_seconds() / 3600:+g}'] += 1
        rows_out.append({'game': r['id'], 'date_utc': r['date'], 'balance': r['balance'], 'difficulty': mode, 'stake_units': r['worth'], 'cash_out_row': r['currentRound'],
                         'win_units': r['winWorth'], 'stake_usd_at_1666': str(cents(w / UNITS_PER_USD)), 'win_usd_at_1666': str(cents(D(r['winWorth']) / UNITS_PER_USD)),
                         'chain_position': pos.get(r['gameSeed']), 'server_seed': r['serverSeed'], 'client_seed': r['clientSeed']})
    order = sorted(rows_out, key=lambda x: x['date_utc'])
    chain_ordered = [x['chain_position'] for x in order] == sorted(x['chain_position'] for x in order if x['chain_position'])
    n = len(recs)
    trunc_table = {'records': n, 'row_payout_values': c['rows'], 'full_multiplier': c['payout_full'], **{f'truncated_{t}dp': c[f'payout_trunc{t}'] for t in TRUNC},
                   'client_js_label_3dp': c['payout_client_label3'],
                   'paid_cash_outs': {'count': c['cashouts'], 'full_multiplier': c['cashout_full'], **{f'truncated_{t}dp': c[f'cashout_trunc{t}'] for t in TRUNC}, 'client_js_label_3dp': c['cashout_client_label3']},
                   'note': 'truncated_kdp = the exact compounded multiplier truncated to k decimals before multiplying; client_js_label_3dp = the label the captured client computes in JavaScript. Truncation at 7 or 8 decimals reproduces the same values as the full multiplier at these stakes, so the exact internal precision is not uniquely established; the 3-decimal ladder is ruled out.'}
    res = {'scope': '27 Towers games from one account, dated 8 and 13 November 2024 by the operator\'s own records, as served by the operator\'s share-bet endpoint, archived by the Wayback Machine and retrieved on 2026-10-28. Selected winning games shared by the account holder; not a sample of play.',
           'account': {'id': root, 'public_name': recs[0]['user']['username'], 'note': 'published with the account holder\'s consent'},
           'counts': {k: v for k, v in c.items()}, 'precision_test': trunc_table,
           'chain': {'seeds_on_chain': c['on_chain'], 'min_position': min(pos.values()), 'max_position': max(pos.values()), 'positions_increase_with_date': chain_ordered,
                     'distinct_server_seeds': len({r['serverSeed'] for r in recs}), 'distinct_client_seeds': len({r['clientSeed'] for r in recs})},
           'difficulties': dict(Counter(r['difficultyString'] for r in recs)), 'balances': dict(Counter(r['balance'] for r in recs)),
           'dates_utc': dict(Counter(r['date'][:10] for r in recs)),
           'client_labels_3dp_used': {m: [str(client_label3(m, k)) for k in range(1, 11)] for m in CH},
           'games': rows_out, 'payout_rows': payout_rows}
    ex = [x for x in payout_rows if x['game'] == '673498dd37bae6ae49b68c49' and x['row'] == 2][0]
    res['precision_example'] = {**ex, 'payout_usd_exact': format((D(ex['payout_units']) / UNITS_PER_USD).normalize(), 'f'),
                                'displayed_usd': disp['673498dd37bae6ae49b68c49']['displayed_gross_win_usd'],
                                'three_dp_ladder_usd': str(cents(D(ex['stake_units']) * D('2.030') / UNITS_PER_USD)),
                                'fixed5_usd': str(cents(D(ex['stake_units']) * D('2.1375') / UNITS_PER_USD))}
    check(n == 27 and c['rows'] == 270 and c['rows_replayed'] == 270, 'replay 270/270')
    check(c['payout_full'] == 270, 'every row payout value equals floor(stake x full multiplier)')
    check(c['cashouts'] == 27 and c['cashout_full'] == 27, 'every paid amount (27 cash-outs) equals floor(stake x full multiplier)')
    check(c['rows_played'] == c['played_rows_safe'] and c['winworth_equals_cashout_row'] == 27, 'played rows safe; winWorth = cash-out row payout')
    check(c['on_chain'] == 27 and chain_ordered, 'all game seeds on the account chain, in date order')
    check(c['payout_above_fixed5'] == 0 and c['rows2plus_below_fixed5'] == c['rows2plus'], 'no payout above the fixed-5% benchmark; every row from 2 below it')
    check(c['display_records'] == 27 and c['stake_units_match_display'] == 27 and c['win_units_match_display'] == 27, 'unit scale 1666 = $1 against share-page display')
    res['failures'] = failures
    (out / 'historical-2024.json').write_text(json.dumps(res, indent=1) + '\n')
    print(f"historical: games {n}, rows replayed {c['rows_replayed']}/{c['rows']}, played rows safe {c['played_rows_safe']}/{c['rows_played']}, "
          f"seeds on chain {c['on_chain']}/27 (positions {min(pos.values())}-{max(pos.values())}, date order {chain_ordered}), "
          f"row payout values full {c['payout_full']}/{c['rows']}, exact multiplier truncated 3/4/5/6/7/8 dp {'/'.join(str(c[f'payout_trunc{t}']) for t in TRUNC)}, "
          f"client JS 3-dp labels {c['payout_client_label3']}/{c['rows']}, paid cash-outs full {c['cashout_full']}/{c['cashouts']} (client labels {c['cashout_client_label3']}/{c['cashouts']}), "
          f"above fixed-5% {c['payout_above_fixed5']}, units 1666=$1 stake {c['stake_units_match_display']}/27 win {c['win_units_match_display']}/27; failures: {len(failures)}")
    for f in failures: print('FAIL:', f, file=sys.stderr)
    return 0 if not failures else 1

if __name__ == '__main__':
    sys.exit(main())
