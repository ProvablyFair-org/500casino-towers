"""Match the 416 sanitized Towers feed entries (7-9 October 2026) to the payout formula.

Reads data/feed/towers-entries.sanitized.jsonl. Amounts are raw feed units; their scale is NOT verified
and no currency conversion is attempted. A field named 'balance' in the raw feed carried a currency label
(btc, xrp, usdc, ...), not an account bankroll; it is exported as currency_label.

Rule, fixed before matching: for a winning entry (payout > 0), the candidate set is every
(difficulty, row) with |payout - stake x step^row| < 1 raw unit, using the exact compounded step
(1.425, 1.9, 2.85) and rows 1-10. Exactly one candidate is required; zero = unmatched, two or more =
ambiguous, both reported and both fail the check. For the unique candidate the script also tests
payout == floor(stake x step^row) and classifies payout as equal to / below / above the unrounded value.

Precision test: for each uniquely matched winner, payout is also compared with floor(stake x trunc_k(step^row))
(the exact multiplier truncated to k = 3..8 decimals) and with floor(stake x label3(row)), the client's 3-decimal
ladder label as JavaScript evaluates it, Math.floor(1e3*Math.pow(step,row))/1e3 (it differs from exact 3-decimal
truncation at Medium row 3: 6.858). The check FAILS unless the full multiplier reproduces every winner.

The feed is the operator's public bet feed and leans heavily to wins (330 of 416 entries), so it is not a
sample of play; outputs are limited to counts, matching and precision. Nothing is summed across players or
currencies.

Usage: python3 -I -B analysis/feed_verify.py --out <dir>
"""
from decimal import Decimal as D, ROUND_FLOOR, getcontext
from collections import Counter
from pathlib import Path
import argparse, json, math, sys

getcontext().prec = 80
ROOT = Path(__file__).resolve().parents[1]
STEP = {'easy': D('1.425'), 'medium': D('1.9'), 'hard': D('2.85')}
PARAMS = json.loads((ROOT / 'data/payout-parameters.json').read_text())['towers']['difficulties']
FORBIDDEN_KEYS = {'username', 'userId', 'avatar', 'level', 'role', 'transactionId', 'referenceTransactionId'}
failures = []

def check(ok, msg):
    if not ok: failures.append(msg)
    return ok

def client_label3(mode, n):
    # the captured client's ladder label in IEEE doubles, as the JavaScript writes it (checked against
    # analysis/client_ladders.mjs by analysis/run_all.py)
    return D(format(math.floor(1e3 * math.pow(float(PARAMS[mode]['client_step_number']), n)) / 1e3, '.3f'))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    recs = [json.loads(l) for l in (ROOT / 'data/feed/towers-entries.sanitized.jsonl').read_text().splitlines() if l.strip()]
    for r in recs: check(not (FORBIDDEN_KEYS & set(r)), f'record {r.get("record")}: player field present')
    c = Counter(); rows = []; by_candidate = Counter(); by_currency = Counter()
    for r in recs:
        stake = D(str(r['bet_amount_raw'])); pay = D(str(r['payout_amount_raw'] or 0)); c['entries'] += 1; by_currency[r['currency_label']] += 1
        if pay == 0: c['zero_payout'] += 1; continue
        c['winners'] += 1
        hits = [(m, n, stake * s ** n) for m, s in STEP.items() for n in range(1, 11) if abs(pay - stake * s ** n) < 1]
        if len(hits) == 0: c['unmatched'] += 1; rows.append({'record': r['record'], 'status': 'unmatched'}); continue
        if len(hits) > 1: c['ambiguous'] += 1; rows.append({'record': r['record'], 'status': 'ambiguous', 'candidates': [(m, n) for m, n, _ in hits]}); continue
        m, n, v = hits[0]; c['unique_matches'] += 1; by_candidate[f'{m}/{n}'] += 1
        fl = v.to_integral_value(rounding=ROUND_FLOOR)
        c['equals_floor_of_prediction'] += pay == fl
        mm = STEP[m] ** n
        for t in (3, 4, 5, 6, 7, 8):
            c[f'trunc{t}_matches'] += pay == (stake * mm.quantize(D(1).scaleb(-t), rounding=ROUND_FLOOR)).to_integral_value(rounding=ROUND_FLOOR)
        c['client_label3_matches'] += pay == (stake * client_label3(m, n)).to_integral_value(rounding=ROUND_FLOOR)
        rel = 'equal' if pay == v else ('below' if pay < v else 'above')
        c['unrounded_' + rel] += 1
        rows.append({'record': r['record'], 'status': 'unique', 'difficulty': m, 'row': n, 'stake_raw': int(stake), 'payout_raw': int(pay),
                     'prediction_exact': format(v.normalize(), 'f'), 'payout_equals_floor': pay == fl, 'payout_vs_unrounded': rel})
    for k in ['unmatched', 'ambiguous', 'unrounded_equal', 'unrounded_below', 'unrounded_above', 'client_label3_matches']: c.setdefault(k, 0)
    summ = json.loads((ROOT / 'data/feed/collection-summary.json').read_text())
    res = {'scope': 'Passive logged-out public feed, 7-9 Oct 2026, Towers entries only. Raw units; scale unverified. Selected by game name, not a complete record of Towers activity (see collection gaps). Not used for any aggregate or site-wide estimate.',
           'rule': 'unique (difficulty,row) with |payout - stake*step^row| < 1 raw unit; then payout == floor(stake*step^row)',
           'counts': dict(c), 'precision_test': {'winners': c['winners'], 'full_multiplier': c['equals_floor_of_prediction'], **{f'truncated_{t}dp': c[f'trunc{t}_matches'] for t in (3, 4, 5, 6, 7, 8)}, 'client_js_label_3dp': c['client_label3_matches'],
                              'note': 'truncated_kdp = the exact compounded multiplier truncated to k decimals before multiplying; client_js_label_3dp = the label the captured client computes in JavaScript. Truncation at 6 or more decimals reproduces the same values as the full multiplier here, so the exact internal precision is not uniquely established; the 3-decimal ladder is ruled out.'}, 'matches_by_difficulty_row': dict(sorted(by_candidate.items())), 'entries_by_currency_label': dict(sorted(by_currency.items())),
           'collection': {k: summ[k] for k in ['distinct_transaction_ids_all_games', 'towers_entries', 'conflicting_duplicates', 'first_received_utc', 'last_received_utc']},
           'per_entry': rows}
    check(c['entries'] == 416 and c['winners'] == 330 and c['zero_payout'] == 86, 'entry counts 416/330/86')
    check(c['unique_matches'] == 330 and c['unmatched'] == 0 and c['ambiguous'] == 0, 'unique matching 330, none unmatched/ambiguous')
    check(c['equals_floor_of_prediction'] == 330, 'all winners equal floor(stake*step^row)')
    check(c['unrounded_equal'] == 6 and c['unrounded_below'] == 324 and c['unrounded_above'] == 0, 'equal 6 / below 324 / above 0')
    check(summ['towers_entries'] == 416, 'summary towers entries')
    res['failures'] = failures
    (out / 'feed-towers.json').write_text(json.dumps(res, indent=1) + '\n')
    print(f"feed: entries {c['entries']}, winners {c['winners']}, zero payouts {c['zero_payout']}, unique matches {c['unique_matches']}, unmatched {c['unmatched']}, ambiguous {c['ambiguous']}, "
          f"equal floor {c['equals_floor_of_prediction']}, exact multiplier truncated 3/4/5/6/7/8 dp {'/'.join(str(c[f'trunc{t}_matches']) for t in (3, 4, 5, 6, 7, 8))}, client JS 3-dp labels {c['client_label3_matches']}/{c['winners']}, unrounded equal/below/above {c['unrounded_equal']}/{c['unrounded_below']}/{c['unrounded_above']}; failures: {len(failures)}")
    for f in failures: print('FAIL:', f, file=sys.stderr)
    return 0 if not failures else 1

if __name__ == '__main__':
    sys.exit(main())
