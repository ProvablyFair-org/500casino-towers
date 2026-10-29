"""Negative tests: each check must FAIL (non-zero exit) when one input is changed.

Every mutation is applied to a fresh temporary copy of the repository; the checkout itself is never
modified (its evidence/data digest is compared before and after). Usage:
    python3 -I -B tests/run_negative.py
"""
from pathlib import Path
import hashlib, json, os, shutil, subprocess, sys, tempfile

ROOT = Path(__file__).resolve().parents[1]
PY = [sys.executable, '-I', '-B']
NODE = os.environ.get('NODE') or shutil.which('node')

def digest():
    h = hashlib.sha256()
    for d in ('evidence', 'data', 'results'):
        for p in sorted((ROOT / d).rglob('*')):
            if p.is_file(): h.update(str(p.relative_to(ROOT)).encode() + hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()

def edit_json(rel, fn):
    def apply(tmp):
        p = tmp / rel; d = json.loads(p.read_text()); fn(d); p.write_text(json.dumps(d, indent=1))
    return apply

def edit_text(rel, old, new):
    def apply(tmp):
        p = tmp / rel; s = p.read_text(); assert old in s, (rel, old); p.write_text(s.replace(old, new, 1))
    return apply

def edit_jsonl(rel, i, fn):
    def apply(tmp):
        p = tmp / rel; L = p.read_text().splitlines(); r = json.loads(L[i]); fn(r); L[i] = json.dumps(r); p.write_text('\n'.join(L) + '\n')
    return apply

def set_(d, path, v):
    for k in path[:-1]: d = d[k]
    d[path[-1]] = v

CASES = [
    ('changed multiplier (Medium step 1.9 -> 1.91)', edit_json('data/payout-parameters.json', lambda d: set_(d, ['towers', 'difficulties', 'medium', 'client_step_number'], '1.91')), ['payout', 'expectations']),
    ('changed bet amount (game 11 stake 0.33 -> 0.34)', edit_json('data/session-2026-10-09.json', lambda d: set_(d, ['games', 11, 'stake'], '0.34')), ['session']),
    ('changed a balance reading (after game 2, 100.79 -> 100.80)', edit_json('data/session-2026-10-09.json', lambda d: set_(d, ['balance_readings_selected', 2, 'displayed'], '100.80')), ['session']),
    ('changed revealed server seed (pair 2, last hex digit)', edit_json('data/session-2026-10-09.json', lambda d: set_(d, ['server_seed_pairs', 1, 'revealed_server_seed'], d['server_seed_pairs'][1]['revealed_server_seed'][:-1] + 'f')), ['session']),
    ('changed committed hash (pair 1, first hex digit)', edit_json('data/session-2026-10-09.json', lambda d: set_(d, ['server_seed_pairs', 0, 'committed_hash'], '0' + d['server_seed_pairs'][0]['committed_hash'][1:])), ['session']),
    ('changed final chain transcription (one digit)', edit_json('data/seed-panel-transcriptions.json', lambda d: set_(d, ['transcriptions', 4, 'value'], d['transcriptions'][4]['value'][:-1] + '4')), ['session']),
    ('changed logged pick (game 0, left -> right, the row-1 bomb tile)', edit_json('data/session-2026-10-09.json', lambda d: set_(d, ['games', 0, 'picks'], [2])), ['session']),
    ('changed a 2024 server payout (game 672de575, row 3 +1 unit)', edit_text('evidence/historical-bets-2024/wayback-raw/672de575e61e8c3513e61b1e.json', '"payout":22854', '"payout":22855'), ['historical']),
    ('changed a 2024 game seed (one hex digit)', edit_text('evidence/historical-bets-2024/wayback-raw/672de575e61e8c3513e61b1e.json', '"gameSeed":"e170685e', '"gameSeed":"e170685f'), ['historical']),
    ('changed a share-page displayed win (7.22 -> 7.23)', edit_json('evidence/historical-bets-2024/share-page-display.json', lambda d: set_(d, ['records', 0, 'displayed_gross_win_usd'], '7.23')), ['historical']),
    ('changed feed payout (record 1 +1 raw unit)', edit_jsonl('data/feed/towers-entries.sanitized.jsonl', 0, lambda r: r.update(payout_amount_raw=r['payout_amount_raw'] + 1)), ['feed']),
    ('changed captured client code (houseEdge default .05 -> .04)', edit_text('evidence/client/towers-live-2026-10-07/js/app.3088e4a4.js', 'towersHouseEdge:.05', 'towersHouseEdge:.04'), ['source']),
    ('changed verbatim quotation source (Towes -> Towers)', edit_text('evidence/help-history/2023-09-25-odds.txt', 'Towes has a fixed', 'Towers has a fixed'), ['source']),
    ('changed official chart value (Shuffle Hard row 9 501.76 -> 501.77)', edit_text('evidence/comparators/shuffle-tower-chart-2026-10-28/page.txt', '501.76', '501.77'), ['payout']),
    ('changed one evidence byte (log.redacted.txt)', edit_text('evidence/session-2026-10-09/log.redacted.txt', '102.23', '102.24'), ['manifest']),
]

def run_check(kind, tmp, out):
    cmds = {'expectations': [PY + ['analysis/run_all.py', '--no-manifest', '--out', out]],
            'payout': [[NODE, 'analysis/client_ladders.mjs', '--out', out], PY + ['analysis/payout_math.py', '--out', out]],
            'session': [PY + ['analysis/session_verify.py', '--out', out]],
            'historical': [PY + ['analysis/historical_verify.py', '--out', out]],
            'feed': [PY + ['analysis/feed_verify.py', '--out', out]],
            'source': [PY + ['analysis/source_check.py', '--out', out]],
            'manifest': [PY + ['analysis/run_all.py', '--out', out]]}[kind]
    codes = [subprocess.run(c, cwd=tmp, capture_output=True, text=True).returncode for c in cmds]
    return codes[-1] if kind != 'payout' else max(codes)

def main():
    before = digest(); failures = 0
    for name, mutate, kinds in CASES:
        with tempfile.TemporaryDirectory(prefix='towers-neg-') as t:
            tmp = Path(t) / 'repo'
            shutil.copytree(ROOT, tmp, ignore=shutil.ignore_patterns('.git', '__pycache__'))
            mutate(tmp)
            for k in kinds:
                rc = run_check(k, tmp, str(Path(t) / 'out'))
                ok = rc != 0; failures += not ok
                print(f"[{'PASS' if ok else 'FAIL'}] {name}: {k} check exit {rc} ({'detected' if ok else 'NOT DETECTED'})")
    # control: an unmodified copy passes every individual check
    with tempfile.TemporaryDirectory(prefix='towers-ctl-') as t:
        tmp = Path(t) / 'repo'; shutil.copytree(ROOT, tmp, ignore=shutil.ignore_patterns('.git', '__pycache__'))
        rcs = {k: run_check(k, tmp, str(Path(t) / 'out')) for k in ['payout', 'session', 'historical', 'feed', 'source']}
        ok = all(v == 0 for v in rcs.values()); failures += not ok
        print(f"[{'PASS' if ok else 'FAIL'}] control (unmodified copy): exit codes {rcs}")
    after = digest()
    ok = before == after; failures += not ok
    print(f"[{'PASS' if ok else 'FAIL'}] checkout unchanged by the tests (evidence/data/results digest {after[:16]}...)")
    print(f'NEGATIVE TESTS: {"PASS" if not failures else "FAIL"} ({failures} failure(s))')
    return 0 if not failures else 1

if __name__ == '__main__':
    sys.exit(main())
