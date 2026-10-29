"""Layer 1 (ideal mathematics), fixed-5% benchmarks, captured-ladder edges, per-bet examples,
cap checks and comparator ladders. Exact Decimal/Fraction arithmetic; rounding only at display.

Reads data/payout-parameters.json and <out>/client-ladders.json (written by
analysis/client_ladders.mjs, so the 3-decimal client labels come from JavaScript, not from a
Decimal imitation). Also checks the JavaScript 2-decimal layer against the labels the operator
displayed, as recorded in text evidence.

Usage: python3 -I -B analysis/payout_math.py --out <dir>
Writes <dir>/payout-math.json and <dir>/tables.md. Exit 1 on any failed check.
"""
from decimal import Decimal as D, ROUND_HALF_UP, ROUND_FLOOR, getcontext
from fractions import Fraction as F
from pathlib import Path
import argparse, json, re, sys

getcontext().prec = 100
ROOT = Path(__file__).resolve().parents[1]
CENT = D('0.01')
failures = []

def check(ok, msg):
    if not ok: failures.append(msg)
    return ok

def pct(x):  # Decimal fraction -> exact percent string without exponent
    return format((x * 100).normalize(), 'f')

def half_up(x, places):
    return (x).quantize(D(1).scaleb(-places), rounding=ROUND_HALF_UP)

def frac_to_dec(fr):
    return D(fr.numerator) / D(fr.denominator)

def terminates(fr):
    d = fr.denominator
    for q in (2, 5):
        while d % q == 0: d //= q
    return d == 1

def exact(fr):
    """Exact decimal string when the fraction terminates, otherwise 'numerator/denominator'."""
    if terminates(fr): return format(frac_to_dec(fr).normalize(), 'f')
    return f'{fr.numerator}/{fr.denominator}'

def rnd(fr, places):  # ROUND_HALF_UP of an exact fraction at a display boundary
    return str(half_up(frac_to_dec(fr), places))

def floor_cents(fr):
    return str((frac_to_dec(fr)).quantize(CENT, rounding=ROUND_FLOOR))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); a = ap.parse_args()
    out = Path(a.out)
    P = json.loads((ROOT / 'data/payout-parameters.json').read_text())
    T = P['towers']; keep = 1 - F(T['house_edge'])
    js = json.loads((out / 'client-ladders.json').read_text())
    jsrow = {(r['difficulty'], r['row']): r for r in js['rows']}

    ladders = []
    for diff, d in T['difficulties'].items():
        c, b = d['choices'], d['bombs']; safe = c - b
        p = F(safe, c)
        step = keep / p                              # exact: 1.425 / 1.9 / 2.85
        check(step == F(d['client_step_number']), f'{diff}: exact step {step} differs from client Number {d["client_step_number"]}')
        for n in range(1, T['rows'] + 1):
            full = step ** n                         # layer 1 full multiplier (0.95/p)^n
            ret = p ** n * full
            check(ret == keep ** n, f'{diff} row {n}: p^n*multiplier != 0.95^n')
            fixed5 = keep / p ** n                   # fixed-5% winning benchmark 0.95/p^n
            r = jsrow[(diff, n)]
            label3 = F(r['client_label_3dp'])
            ladder_return = label3 * p ** n
            ladders.append({
                'difficulty': diff, 'row': n, 'p_survive': f'{(p ** n).numerator}/{(p ** n).denominator}',
                'layer1_full_multiplier_exact': exact(full),
                'layer2_client_label_3dp': r['client_label_3dp'],
                'layer3_client_tile_label_2dp': r['client_tile_label_2dp'],
                'fixed5_benchmark_multiplier_exact': exact(fixed5),
                'benchmark_minus_full_multiplier': exact(fixed5 - full),
                'nominal_return_exact': exact(ret),
                'nominal_edge_percent_exact': exact((1 - ret) * 100),
                'nominal_edge_percent_2dp_half_up': rnd((1 - ret) * 100, 2),
                'captured_ladder_return_exact': exact(ladder_return),
                'captured_ladder_edge_percent_exact': exact((1 - ladder_return) * 100),
                'captured_ladder_edge_percent_12dp': rnd((1 - ladder_return) * 100, 12),
                'captured_ladder_edge_percent_2dp_half_up': rnd((1 - ladder_return) * 100, 2),
            })

    curve = [{'row': n, 'nominal_return_exact': exact(keep ** n),
              'nominal_return_percent_2dp': rnd(keep ** n * 100, 2),
              'nominal_edge_percent_exact': exact((1 - keep ** n) * 100),
              'nominal_edge_percent_2dp_half_up': rnd((1 - keep ** n) * 100, 2)} for n in range(1, 11)]

    # all ten $100 Medium successful-cash-out examples
    stake = F(100); med = T['difficulties']['medium']; mp = F(med['choices'] - med['bombs'], med['choices']); mstep = keep / mp
    examples = []
    for n in range(1, 11):
        full = stake * mstep ** n
        lad = stake * F(jsrow[('medium', n)]['client_label_3dp'])
        bench = stake * keep / mp ** n
        fc, bc = D(rnd(full, 2)), D(rnd(bench, 2))
        examples.append({'row': n, 'stake_usd': '100.00',
                         'gross_payout_full_formula_exact': exact(full),
                         'gross_payout_full_formula_cents_half_up': str(fc),
                         'gross_payout_client_3dp_label': rnd(lad, 2),
                         'gross_payout_fixed5_benchmark': str(bc),
                         'successful_cashout_difference_gross': str(bc - fc),
                         'profit_full_formula_cents_half_up': str(fc - 100),
                         'profit_fixed5_benchmark': str(bc - 100)})

    # cap check: rounded published maximum stake vs both candidate maxima
    m10_full = mstep ** 10; m10_label = F(jsrow[('medium', 10)]['client_label_3dp'])
    caps = []
    for cp in P['limits']['checkpoints']:
        cap = F(cp['cap_usd'])
        row = {**cp, 'cap_over_full_multiplier_12dp': rnd(cap / m10_full, 12), 'cap_over_client_label_12dp': rnd(cap / m10_label, 12),
               'floor_to_cent_full': floor_cents(cap / m10_full), 'floor_to_cent_label': floor_cents(cap / m10_label),
               'half_up_to_cent_full': rnd(cap / m10_full, 2), 'half_up_to_cent_label': rnd(cap / m10_label, 2)}
        row['displayed_reproduced_by_floor_both'] = row['floor_to_cent_full'] == row['floor_to_cent_label'] == cp['max_medium_stake_displayed']
        row['displayed_reproduced_by_half_up_both'] = row['half_up_to_cent_full'] == row['half_up_to_cent_label'] == cp['max_medium_stake_displayed']
        check(row['displayed_reproduced_by_floor_both'], f'cap check {cp["snapshot"]}')
        caps.append(row)

    comps = {}
    for name, cfg in P['comparators'].items():
        k = 1 - F(cfg['house_edge']); fs = F(cfg['choices'], cfg['safe'])
        rows = []
        for n in range(1, cfg['rows'] + 1):
            m = k * fs ** n
            rows.append({'row': n, 'calculated_multiplier': exact(m), 'return_exact': exact(m * F(cfg['safe'], cfg['choices']) ** n)})
        comps[name] = {'formula': f'{exact(k)} x {exact(fs)}^n', 'status': cfg['status'], 'rows': rows}

    # Shuffle official chart (captured 2026-10-28): parse the 9 x 6 table from the rendered text
    st = (ROOT / 'evidence/comparators/shuffle-tower-chart-2026-10-28/page.txt').read_text()
    body = st[st.index('Master (1/4)') + len('Master (1/4)'):st.index('If you would like')]
    toks = re.findall(r'(?m)^\s*(\d+(?:\.\d+)?)\s*$', body)
    check(len(toks) == 54, f'shuffle chart: expected 54 cells, got {len(toks)}')
    grid = [toks[i:i + 6] for i in range(0, 54, 6)]
    check([g[0] for g in grid] == [str(i) for i in range(1, 10)], 'shuffle chart row numbers')
    hard = [g[3] for g in grid]; master = [g[5] for g in grid]
    calc = [r['calculated_multiplier'] for r in comps['shuffle_tower_hard']['rows']]
    trunc2 = [str(D(c).quantize(D('0.01'), rounding=ROUND_FLOOR)) for c in calc]
    comps['shuffle_tower_hard']['official_chart_hard_column'] = hard
    comps['shuffle_tower_hard']['official_chart_equals_calculation_truncated_2dp'] = check(hard == trunc2, f'shuffle hard chart {hard} vs {trunc2}')
    comps['shuffle_tower_hard']['official_chart_master_column'] = master
    comps['shuffle_tower_hard']['chart_source'] = 'evidence/comparators/shuffle-tower-chart-2026-10-28/page.txt'

    # layer 3 against labels the operator displayed (text evidence)
    observed = {}
    ex = (ROOT / 'evidence/client/towers-live-2026-10-07/page-excerpt.txt').read_text().split('\n')
    i = ex.index('Easy')
    labs = [l for l in ex[i:] if re.fullmatch(r'\d+\.\d\dx', l)]
    check(len(labs) == 30, 'easy labels in page excerpt: expected 30 tiles')
    observed['easy'] = {'source': 'evidence/client/towers-live-2026-10-07/page-excerpt.txt (logged out, 2026-10-07)', 'row1_first': [labs[j][:-1] for j in range(0, 30, 3)][::-1]}
    log = (ROOT / 'evidence/session-2026-10-09/log.redacted.txt').read_text()
    mm = re.search(r'medium ladder displayed: ([\d. ]+)\.', log); hm = re.search(r'hard ladder displayed: ([\d. ]+)', log)
    observed['medium'] = {'source': 'evidence/session-2026-10-09/log.redacted.txt 12:06:50Z', 'row1_first': mm.group(1).split()}
    observed['hard'] = {'source': 'evidence/session-2026-10-09/log.redacted.txt (line after 12:07:28Z)', 'row1_first': hm.group(1).split()}
    ui_checks = []
    for diff, ob in observed.items():
        check(len(ob['row1_first']) == 10, f'{diff}: expected 10 observed labels')
        for n, v in enumerate(ob['row1_first'], 1):
            js2 = jsrow[(diff, n)]['client_tile_label_2dp']
            ui_checks.append({'difficulty': diff, 'row': n, 'observed_label': v, 'js_layer3': js2, 'match': v == js2})
            check(v == js2, f'UI label {diff} row {n}: observed {v} vs JS {js2}')

    res = {'scope': 'Payout construction and comparator arithmetic. Layer 1 = ideal mathematics (exact). Layer 2/3 = client labels from JavaScript. Settlement hypotheses are in session/historical/feed outputs.',
           'ladders': ladders, 'ideal_return_curve': curve, 'medium_100_examples': examples,
           'cap_checks': caps, 'comparators': comps, 'ui_label_checks': ui_checks,
           'observed_ui_labels': observed, 'failures': failures}
    (out / 'payout-math.json').write_text(json.dumps(res, indent=1) + '\n')

    md = ['# Generated technical tables', '', 'Generated by `analysis/payout_math.py` from `data/payout-parameters.json` and the JavaScript layer `analysis/client_ladders.mjs`. Do not edit by hand.', '',
          '## All 30 rows: four layers kept apart', '',
          '| difficulty | row | layer 1 full multiplier (exact) | layer 2 client 3-dp label (JS) | layer 3 client 2-dp tile (JS) | fixed-5% benchmark multiplier | nominal edge % (exact) | nominal edge % (2 dp) | captured-ladder edge % (12 dp) | captured-ladder edge % (2 dp) |',
          '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in ladders:
        md.append(f"| {r['difficulty']} | {r['row']} | {r['layer1_full_multiplier_exact']} | {r['layer2_client_label_3dp']} | {r['layer3_client_tile_label_2dp']} | {r['fixed5_benchmark_multiplier_exact']} | {r['nominal_edge_percent_exact']} | {r['nominal_edge_percent_2dp_half_up']} | {r['captured_ladder_edge_percent_12dp']} | {r['captured_ladder_edge_percent_2dp_half_up']} |")
    md += ['', '## Ideal return curve (every difficulty): return = 0.95^n, edge = 1 - 0.95^n', '', '| row | return (exact) | return % | edge % (exact) | edge % (2 dp, half-up) |', '|---:|---:|---:|---:|---:|']
    md += [f"| {c['row']} | {c['nominal_return_exact']} | {c['nominal_return_percent_2dp']} | {c['nominal_edge_percent_exact']} | {c['nominal_edge_percent_2dp_half_up']} |" for c in curve]
    md += ['', '## $100 Medium successful cash-outs (gross includes the stake; profit excludes it)', '', '| row | full formula gross (exact) | full formula gross, cents | client 3-dp label gross | fixed-5% benchmark gross | benchmark minus full (gross) | full-formula profit | benchmark profit |', '|---:|---:|---:|---:|---:|---:|---:|---:|']
    md += [f"| {e['row']} | {e['gross_payout_full_formula_exact']} | {e['gross_payout_full_formula_cents_half_up']} | {e['gross_payout_client_3dp_label']} | {e['gross_payout_fixed5_benchmark']} | {e['successful_cashout_difference_gross']} | {e['profit_full_formula_cents_half_up']} | {e['profit_fixed5_benchmark']} |" for e in examples]
    md += ['', '## Published cap and rounded maximum Medium stake', '', '| snapshot | cap | displayed max Medium stake (~) | cap / 613.1066257801 | cap / 613.106 | both truncated to cents | both half-up to cents |', '|---|---:|---:|---:|---:|---:|---:|']
    md += [f"| {c['snapshot']} | {c['cap_usd']} | {c['max_medium_stake_displayed']} | {c['cap_over_full_multiplier_12dp']} | {c['cap_over_client_label_12dp']} | {c['floor_to_cent_full']} / {c['floor_to_cent_label']} | {c['half_up_to_cent_full']} / {c['half_up_to_cent_label']} |" for c in caps]
    md += ['', 'Truncated to cents, both candidate Medium row-10 multipliers give the displayed approximate maximum stake; rounded half-up, both give 326.21 for the $200,000 cap. The published figures therefore support the broad multiplier family but do not distinguish 613.106 from 613.1066257801 and do not establish the cap convention.', '']
    for name, cpm in comps.items():
        md += [f'## Comparator: {name} ({cpm["formula"]}), calculated', '', f'Status: {cpm["status"]}', '', '| row | calculated multiplier | return |', '|---:|---:|---:|']
        if 'official_chart_hard_column' in cpm:
            md += [f"| {r['row']} | {r['calculated_multiplier']} | {r['return_exact']} |" for r in cpm['rows']]
            md += ['', f"Official Shuffle chart, Hard (1/2) column, captured 2026-10-28 (values shown truncated to 2 dp): {', '.join(cpm['official_chart_hard_column'])}. Equal to the calculation: {cpm['official_chart_equals_calculation_truncated_2dp']}.", '']
        else:
            md += [f"| {r['row']} | {r['calculated_multiplier']} | {r['return_exact']} |" for r in cpm['rows']] + ['']
    (out / 'tables.md').write_text('\n'.join(md))
    print(f'payout math: {len(ladders)} ladder rows, {len(curve)} curve rows, {len(examples)} $100 Medium examples, {len(ui_checks)} UI labels checked, {sum(len(c["rows"]) for c in comps.values())} comparator rows; failures: {len(failures)}')
    for f in failures: print('FAIL:', f, file=sys.stderr)
    return 0 if not failures else 1

if __name__ == '__main__':
    sys.exit(main())
