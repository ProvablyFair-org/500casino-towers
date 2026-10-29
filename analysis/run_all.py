"""One offline command for a fresh checkout: python3 -I -B analysis/run_all.py

Steps (every failure is recorded; the process exits 1 if any step fails):
  1. input integrity: every file listed in SHA256SUMS matches, and every distributed file is listed
  2. snapshot sha256 of evidence/ and data/ before any check
  3. client display layers in JavaScript (node analysis/client_ladders.mjs)
  4. payout mathematics, session replay/reconciliation, historical records, feed matching,
     source checks, privacy scan (Python standard library only)
  5. generated results vs independent literal expectations (tests/expected/expected.json)
  6. claim index: every stated value equals its generated result and appears in the named documents
  7. generated results vs the committed results/ folder (byte-identical)
  8. snapshot of evidence/ and data/ after: must equal step 2 (no input mutation)
Writes only to --out (default: a new temporary directory), including verification-log.txt.
No network, login, wager, API key or package install is used.

Options: --out DIR   output directory (use --out results only when regenerating the committed tables)
         --no-manifest   skip step 1 (used while building, before SHA256SUMS exists)
"""
from pathlib import Path
import argparse, datetime, hashlib, json, os, platform, shutil, subprocess, sys, tempfile

ROOT = Path(__file__).resolve().parents[1]
RESULT_FILES = ['client-ladders.json', 'payout-math.json', 'tables.md', 'session-2026-10-09.json', 'historical-2024.json',
                'feed-towers.json', 'source-checks.json', 'privacy-scan.json']
log_lines, failed = [], []

def log(s=''):
    print(s); log_lines.append(s)

def step(name, ok, detail=''):
    log(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f' - {detail}' if detail else ''))
    if not ok: failed.append(name)

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def tree_digest(dirs):
    h = hashlib.sha256(); n = 0
    for d in dirs:
        for p in sorted((ROOT / d).rglob('*')):
            if p.is_file(): h.update(f'{p.relative_to(ROOT)}\0{sha(p)}\n'.encode()); n += 1
    return h.hexdigest(), n

def distributed_files():
    return sorted(str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file() and '.git' not in p.relative_to(ROOT).parts
                  and str(p.relative_to(ROOT)) != 'SHA256SUMS' and '__pycache__' not in p.parts)

def get(obj, path):
    for part in path.split('.'):
        obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    return obj

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out'); ap.add_argument('--no-manifest', action='store_true'); a = ap.parse_args()
    out = Path(a.out).resolve() if a.out else Path(tempfile.mkdtemp(prefix='towers-verify-'))
    out.mkdir(parents=True, exist_ok=True)
    node = os.environ.get('NODE') or shutil.which('node')
    log(f'500 Casino Towers technical evidence - offline verification')
    log(f'started_utc: {datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}')
    log(f'python: {platform.python_version()} ({sys.executable})')
    nv = subprocess.run([node, '--version'], capture_output=True, text=True).stdout.strip() if node else 'NOT FOUND'
    log(f'node: {nv} ({node})'); log(f'output: {out}'); log('')

    if a.no_manifest:
        log('[SKIP] 1 input integrity (--no-manifest)')
    else:
        lines = [l for l in (ROOT / 'SHA256SUMS').read_text().splitlines() if l.strip()]
        listed = {}; bad = []
        for l in lines:
            h, name = l.split('  ', 1); listed[name] = h
            if not (ROOT / name).is_file() or sha(ROOT / name) != h: bad.append(name)
        unlisted = [f for f in distributed_files() if f not in listed]
        step('1 input integrity (SHA256SUMS)', not bad and not unlisted, f'{len(lines)} entries, {len(bad)} mismatched, {len(unlisted)} unlisted' + (f': {(bad + unlisted)[:5]}' if bad or unlisted else ''))

    before, n_ev = tree_digest(['evidence', 'data'])
    log(f'[INFO] 2 evidence+data snapshot before: {n_ev} files, digest {before}')

    def run(name, cmd):
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        detail = (r.stdout.strip().splitlines() or [''])[-1]
        step(name, r.returncode == 0, detail)
        for l in r.stderr.strip().splitlines()[:20]: log('    ' + l)
    py = [sys.executable, '-I', '-B']
    if node: run('3 client display layers (JavaScript)', [node, 'analysis/client_ladders.mjs', '--out', str(out)])
    else: step('3 client display layers (JavaScript)', False, 'node not found')
    run('4a payout mathematics', py + ['analysis/payout_math.py', '--out', str(out)])
    run('4b session replay and reconciliation', py + ['analysis/session_verify.py', '--out', str(out)])
    run('4c historical records', py + ['analysis/historical_verify.py', '--out', str(out)])
    run('4d feed matching', py + ['analysis/feed_verify.py', '--out', str(out)])
    run('4e source checks', py + ['analysis/source_check.py', '--out', str(out)])
    run('4f privacy scan', py + ['analysis/privacy_scan.py', '--out', str(out)])

    # 5 independent expectations
    E = json.loads((ROOT / 'tests/expected/expected.json').read_text()); mism = []
    def eq(label, got, want):
        if got != want: mism.append(f'{label}: got {got!r}, expected {want!r}')
    try:
        cl = json.loads((out / 'client-ladders.json').read_text()); pm = json.loads((out / 'payout-math.json').read_text())
        se = json.loads((out / 'session-2026-10-09.json').read_text()); hi = json.loads((out / 'historical-2024.json').read_text())
        fe = json.loads((out / 'feed-towers.json').read_text())
        rows = {(r['difficulty'], r['row']): r for r in cl['rows']}
        for d, vals in E['client_label_3dp'].items():
            for i, v in enumerate(vals, 1): eq(f'label {d}/{i}', rows[(d, i)]['client_label_3dp'], v)
        for k, v in E['client_tile_label_2dp_critical'].items():
            d, n = k.split('/'); eq(f'tile {k}', rows[(d, int(n))]['client_tile_label_2dp'], v)
        eq('row5 nominal', pm['ideal_return_curve'][4]['nominal_edge_percent_exact'], E['nominal_edge_percent']['row5'])
        eq('row10 nominal', pm['ideal_return_curve'][9]['nominal_edge_percent_exact'], E['nominal_edge_percent']['row10'])
        eq('row5 nominal display', pm['ideal_return_curve'][4]['nominal_edge_percent_2dp_half_up'], E['nominal_edge_percent_display']['row5'])
        eq('row10 nominal display', pm['ideal_return_curve'][9]['nominal_edge_percent_2dp_half_up'], E['nominal_edge_percent_display']['row10'])
        m5 = [r for r in pm['ladders'] if r['difficulty'] == 'medium' and r['row'] == 5][0]
        eq('medium row5 ladder edge', m5['captured_ladder_edge_percent_exact'], E['medium_row5_captured_ladder_edge_percent'])
        eq('medium row5 ladder edge display', m5['captured_ladder_edge_percent_2dp_half_up'], E['medium_row5_captured_ladder_edge_percent_display'])
        ex4 = pm['medium_100_examples'][3]
        eq('medium100 full', ex4['gross_payout_full_formula_cents_half_up'], E['medium_100']['row4_full_gross'])
        eq('medium100 fixed5', ex4['gross_payout_fixed5_benchmark'], E['medium_100']['row4_fixed5_gross'])
        eq('medium100 diff', ex4['successful_cashout_difference_gross'], E['medium_100']['row4_difference'])
        c = se['counts']; es = E['session']
        for k, kk in [('games', 'games_matching'), ('tiles', 'tiles_replayed'), ('cash_outs', 'cash_outs'), ('bombs', 'bombs'), ('staked', 'staked'), ('commitments', 'commitments_matching')]:
            eq(f'session {k}', c[kk], es[k])
        eq('final chain', se['final_chain_value_full'], es['final_chain_value'])
        eq('game32', se['replay'][32]['game_seed'], es['game32_value'])
        for h in ('H-3dp', 'H-full'):
            r = se['reconciliation'][h]
            eq(f'{h} credits', r['credits_total'], es[h]['credits']); eq(f'{h} final', r['final_balance_exact'], es[h]['final'])
            eq(f'{h} shown', r['final_balance_shown'], es[h]['shown']); eq(f'{h} readings', r['selected_readings_matched'], es[h]['readings_matched'])
        eh = E['historical']; hc = hi['counts']
        eq('historical games', len(hi['games']), eh['games'])
        for k in ['rows', 'rows_replayed', 'payout_full', 'payout_trunc3', 'payout_trunc4', 'payout_trunc5', 'payout_trunc6', 'payout_client_label3',
                  'cashouts', 'cashout_full', 'cashout_client_label3', 'stake_units_match_display', 'win_units_match_display']:
            eq(f'historical {k}', hc[k], eh[k])
        # the Python re-evaluation of the client's JavaScript labels must equal the JavaScript output (step 3)
        for d, vals in hi['client_labels_3dp_used'].items():
            for i, v in enumerate(vals, 1): eq(f'python client label {d}/{i} vs JavaScript', v, rows[(d, i)]['client_label_3dp'])
        eq('historical chain', (hi['chain']['seeds_on_chain'], hi['chain']['min_position'], hi['chain']['max_position']), (eh['seeds_on_chain'], eh['chain_min'], eh['chain_max']))
        pe = hi['precision_example']; ee = eh['example_673498dd37bae6ae49b68c49']
        eq('example payout units', pe['payout_units'], ee['payout_units']); eq('example displayed', pe['displayed_usd'], ee['displayed'])
        eq('example 3dp', pe['three_dp_ladder_usd'], ee['three_dp']); eq('example fixed5', pe['fixed5_usd'], ee['fixed5'])
        for k in ['entries', 'winners', 'zero_payout', 'unique_matches', 'unmatched', 'ambiguous', 'equals_floor_of_prediction', 'unrounded_equal', 'unrounded_below', 'unrounded_above']:
            eq(f'feed {k}', fe['counts'][k], E['feed'][k])
        for t in (3, 4, 5, 6): eq(f'feed trunc{t}', fe['precision_test'][f'truncated_{t}dp'], E['feed'][f'trunc{t}'])
        eq('feed client label3', fe['precision_test']['client_js_label_3dp'], E['feed']['client_label3'])
        eq('feed distinct all games', fe['collection']['distinct_transaction_ids_all_games'], E['feed']['distinct_all_games'])
        eq('stake', [r['calculated_multiplier'] for r in pm['comparators']['stake_dragon_tower_master']['rows']], E['stake_master'])
        eq('shuffle', [r['calculated_multiplier'] for r in pm['comparators']['shuffle_tower_hard']['rows']], E['shuffle_hard'])
        eq('shuffle official chart', pm['comparators']['shuffle_tower_hard'].get('official_chart_hard_column'), E['shuffle_hard_official_chart'])
        fx = json.loads((ROOT / 'tests/fixtures/synthetic-winning-difference.json').read_text())
        from decimal import Decimal as D
        bench = D(fx['stake']) * D('0.95') * D(2) ** fx['row']
        eq('synthetic fixture benchmark', format(bench.normalize(), 'f'), fx['expected_fixed5_gross_benchmark'])
        eq('synthetic fixture difference', format((bench - D(fx['observed_gross_payout'])).normalize(), 'f'), fx['expected_difference'])
        step('5 independent expectations', not mism, f'{len(mism)} mismatches' + (f': {mism[:5]}' if mism else ''))
    except Exception as e:
        step('5 independent expectations', False, f'could not read results: {e}')

    # 6 claim index
    CI = json.loads((ROOT / 'claims-index.json').read_text()); bad = []
    docs = {}
    for v in CI['values']:
        f, path = v['result'].split(':', 1)
        try: got = get(json.loads((out / f).read_text()), path)
        except Exception as e: got = f'<{e}>'
        if got != v['value']: bad.append(f"{v['claim']} {v['what']}: result {got!r} != stated {v['value']!r}")
        for d in v['docs']:
            docs.setdefault(d, (ROOT / d).read_text())
            if str(v['value']) not in docs[d]: bad.append(f"{v['claim']} {v['what']}: {v['value']} not found in {d}")
    step('6 claim index (stated values = generated results)', not bad, f"{len(CI['values'])} values" + (f': {bad[:5]}' if bad else ''))

    # 7 committed results
    if out == (ROOT / 'results').resolve():
        log('[SKIP] 7 committed results comparison (output is results/)')
    else:
        diff = [f for f in RESULT_FILES if not (ROOT / 'results' / f).is_file() or (ROOT / 'results' / f).read_bytes() != (out / f).read_bytes()]
        step('7 generated results identical to committed results/', not diff, f'{len(RESULT_FILES)} files' + (f', differing: {diff}' if diff else ''))

    after, n2 = tree_digest(['evidence', 'data'])
    step('8 no input mutation (evidence+data digest unchanged)', after == before and n2 == n_ev, f'after: {n2} files, digest {after}')
    log('')
    log(f'RESULT: {"PASS" if not failed else "FAIL"} ({len(failed)} failed step(s){": " + ", ".join(failed) if failed else ""})')
    log('Scope: technical checks only. Passing them does not certify report-only analysis or any publication gate.')
    if out != (ROOT / 'results').resolve():  # the committed results/ folder holds generated tables only
        (out / 'verification-log.txt').write_text('\n'.join(log_lines) + '\n')
    return 0 if not failed else 1

if __name__ == '__main__':
    sys.exit(main())
