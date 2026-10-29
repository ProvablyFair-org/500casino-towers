"""Text, secret and metadata scan over every distributed file, plus the synthetic-fixture boundary.

This is a pattern scan. It cannot prove the absence of every identifier; the manual image review and
the retained-identifier list are in REDACTIONS.md. Findings that are expected (publisher addresses in
captured third-party pages, synthetic credentials inside the historical recorder self-test) are listed
in ALLOW with the reason, and any finding not in ALLOW fails the scan.

Usage: python3 -I -B analysis/privacy_scan.py --out <dir>
"""
from pathlib import Path
import argparse, ipaddress, json, re, struct, sys

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {'.git'}
PATTERNS = {
    'email': re.compile(rb'[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}(?:\.[A-Za-z]{2,})*'),
    'jwt': re.compile(rb'eyJ[A-Za-z0-9_-]{2,}\.eyJ[A-Za-z0-9_-]{2,}\.[A-Za-z0-9_-]{2,}'),
    'bearer': re.compile(rb'Bearer [A-Za-z0-9._~+/=-]{16,}'),
    'home_path': re.compile(rb'/(?:Users|home)/[A-Za-z0-9._-]+/'),
    'private_key': re.compile(rb'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    'aws_key': re.compile(rb'AKIA[0-9A-Z]{16}'),
    'cookie_header': re.compile(rb'(?im)^(?:cookie|set-cookie|x-archive-orig-set-cookie): .+$'),
    'ipv4': re.compile(rb'(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])'),
    'ipv6': re.compile(rb'(?<![0-9A-Za-z:])[0-9A-Fa-f]{0,4}(?::[0-9A-Fa-f]{0,4}){2,7}(?![0-9A-Za-z:])'),
    'archive_requester_comment': re.compile(rb'<!--\s+[0-9a-f]{32}\s+Mozilla/[^\n]*'),
    'requester_network_header': re.compile(rb'(?im)^x-(?:nid|as|client-ip|forwarded-for|real-ip): .*$'),
}
VALIDATE = {'ipv4': lambda t: all(int(o) <= 255 for o in t.split('.')),  # conservative: leading zeros still count
             'ipv6': lambda t: ':' in t and any(c in '0123456789abcdefABCDEF' for c in t) and _is_ip(t)}  # bare '::' (slice syntax) is not an address

def _is_ip(t):
    try: ipaddress.ip_address(t); return True
    except ValueError: return False
# (path glob, kind, matched text or '*', reason)
ALLOW = [
    ('*', 'email', 'audit@provablyfair.org', 'the publisher\'s corrections contact'),
    ('evidence/client/limits-article-2026-10-07/page.html', 'email', 'legal@intercom.io', 'help-centre vendor address inside the captured operator page'),
    ('evidence/comparators/stake-dragon-tower-blog-2026-10-07/page.html', 'email', '*', 'Stake support address inside the captured Stake page'),
    ('evidence/comparators/stake-dragon-tower-blog-2026-10-07/page.txt', 'email', '*', 'Stake support address inside the captured Stake page'),
    ('evidence/comparators/stake-*-2026-10-28/page*.txt', 'email', 'support@stake.com', 'Stake support address inside the captured Stake page'),
    ('evidence/client/towers-live-2026-10-07/js/app.3088e4a4.js', 'email', '*', 'operator/vendor addresses compiled into the captured operator JavaScript'),
    ('evidence/client/towers-chunk-2026-10-07/*.js', 'email', '*', 'strings compiled into captured operator JavaScript'),
    ('evidence/client/towers-chunk-2026-10-07/archive.ph-uAhyA.redacted.html', 'email', '*', 'archive.ph page markup (e.g. @archiveis, font-face rules)'),
    ('evidence/client/towers-live-2026-10-07/js/app.3088e4a4.js', 'ipv4', '1.61.72.72', 'SVG path coordinates in icon markup (context ",.88-1.61.72.72,0"), not an address'),
    ('evidence/client/towers-live-2026-10-07/js/app.3088e4a4.js', 'ipv4', '1.21.69.69', 'SVG path coordinates in icon markup, not an address'),
    ('evidence/client/towers-live-2026-10-07/js/app.3088e4a4.js', 'ipv4', '7.7.7.7', 'SVG path coordinates in icon markup ("4.9.3 7.7.7.7 1.1"), not an address'),
    ('evidence/client/towers-live-2026-10-07/js/app.3088e4a4.js', 'ipv4', '1.6.2.1', 'SVG path coordinates in icon markup, not an address'),
    ('evidence/client/towers-live-2026-10-07/js/app.3088e4a4.js', 'ipv4', '1.1.3.4', 'SVG path coordinates in icon markup, not an address'),
    ('evidence/comparators/stake-dragon-tower-blog-2026-10-07/page.html', 'ipv4', '1.04.61.83', 'SVG path coordinates (d attribute), not an address'),
    ('evidence/comparators/stake-dragon-tower-blog-2026-10-07/page.html', 'ipv4', '1.16.8.8', 'SVG path coordinates (d attribute), not an address'),
    ('evidence/comparators/stake-dragon-tower-blog-2026-10-07/page.html', 'ipv4', '1.21.87.47', 'SVG path coordinates (d attribute), not an address'),
    ('evidence/comparators/stake-dragon-tower-blog-2026-10-07/page.html', 'ipv4', '11.84.86.5', 'SVG path coordinates (d attribute), not an address'),
    ('evidence/comparators/stake-dragon-tower-blog-2026-10-07/page.html', 'ipv4', '2.87.71.71', 'SVG path coordinates (d attribute), not an address'),
    ('evidence/comparators/stake-dragon-tower-blog-2026-10-07/page.html', 'ipv4', '2.87.72.72', 'SVG path coordinates (d attribute), not an address'),
    ('evidence/comparators/stake-dragon-tower-blog-2026-10-07/page.html', 'ipv4', '3.2.81.81', 'SVG path coordinates (d attribute), not an address'),
    ('evidence/comparators/stake-dragon-tower-blog-2026-10-07/page.html', 'ipv4', '4.41.07.06', 'SVG path coordinates (d attribute), not an address'),
    ('analysis/privacy_scan.py', '*', '*', 'this scanner'),
]
FIXTURE_BANNER = 'SYNTHETIC TEST DATA - NOT CASINO EVIDENCE'

def allowed(rel, kind, text):
    for g, k, t, why in ALLOW:
        if Path(rel).match(g) and (k == '*' or k == kind) and (t == '*' or t == text): return why
    return None

def png_meta(b):
    keys = []; i = 8
    while i + 8 <= len(b):
        ln, typ = struct.unpack('>I4s', b[i:i + 8]); typ = typ.decode('latin-1')
        if typ in ('tEXt', 'iTXt', 'zTXt', 'eXIf', 'iCCP'): keys.append(typ)
        i += 12 + ln
        if typ == 'IEND': break
    return keys

def jpeg_meta(b):
    keys = []; i = 2
    while i + 4 <= len(b) and b[i] == 0xFF:
        m = b[i + 1]
        if m in (0xD9, 0xDA): break
        ln = struct.unpack('>H', b[i + 2:i + 4])[0]; seg = b[i + 4:i + 2 + ln]
        if 0xE0 <= m <= 0xEF: keys.append(f'APP{m - 0xE0}:' + seg[:5].split(b'\0')[0].decode('latin-1', 'replace'))
        if m == 0xFE: keys.append('COM')
        i += 2 + ln
    return keys

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    findings, unexpected, images = [], [], []
    EXCLUDE = {'SHA256SUMS', 'results/privacy-scan.json', 'results/verification-log.txt'}  # manifest and this scan's own output
    files = [p for p in sorted(ROOT.rglob('*')) if p.is_file() and not (SKIP_DIRS & set(p.relative_to(ROOT).parts)) and str(p.relative_to(ROOT)) not in EXCLUDE and '__pycache__' not in p.parts]
    for p in files:
        rel = str(p.relative_to(ROOT)); b = p.read_bytes()
        if p.suffix.lower() in ('.png', '.jpg', '.jpeg'):
            meta = png_meta(b) if b[:8] == b'\x89PNG\r\n\x1a\n' else jpeg_meta(b)
            bad = [k for k in meta if k in ('tEXt', 'iTXt', 'zTXt', 'eXIf') or k.startswith('APP1:') or k == 'COM']
            images.append({'file': rel, 'metadata_segments': meta, 'flagged': bad})
            if bad: unexpected.append({'file': rel, 'kind': 'image_metadata', 'text': ','.join(bad)})
            continue
        if p.suffix in ('.gz', '.tgz', '.zip'): continue
        for kind, rx in PATTERNS.items():
            for m in set(rx.findall(b)):
                t = m.decode('utf-8', 'replace')
                if kind in VALIDATE and not VALIDATE[kind](t): continue
                f = {'file': rel, 'kind': kind, 'text': t[:120]}
                why = allowed(rel, kind, t); f['allowed_because'] = why
                findings.append(f)
                if not why: unexpected.append(f)
    # data/ and results/ must not carry player fields
    for p in list((ROOT / 'data').rglob('*.json*')) + [q for q in (ROOT / 'results').rglob('*.json') if q.name != 'privacy-scan.json']:
        s = p.read_text()
        for key in ('"username"', '"userId"', '"avatar"', '"transactionId"'):
            if key in s: unexpected.append({'file': str(p.relative_to(ROOT)), 'kind': 'player_field', 'text': key})
    # synthetic boundary
    fixtures = sorted((ROOT / 'tests/fixtures').glob('*')) if (ROOT / 'tests/fixtures').exists() else []
    for p in fixtures:
        if FIXTURE_BANNER not in p.read_text(): unexpected.append({'file': str(p.relative_to(ROOT)), 'kind': 'fixture_without_banner', 'text': ''})
    for d in ('evidence', 'data', 'results'):
        for p in (ROOT / d).rglob('*'):
            if p.is_file() and p.suffix in ('.json', '.jsonl', '.md', '.txt') and FIXTURE_BANNER in p.read_text(errors='replace'):
                unexpected.append({'file': str(p.relative_to(ROOT)), 'kind': 'synthetic_outside_tests', 'text': ''})
    res = {'scope': 'Pattern scan of every distributed file (text patterns, image metadata segments, player fields in data/results, synthetic-fixture boundary). Not a substitute for the manual image review recorded in REDACTIONS.md.',
           'files_scanned': len(files), 'images_checked': len(images), 'findings_total': len(findings), 'findings_allowed': len(findings) - len([u for u in unexpected if u in findings]),
           'unexpected': unexpected, 'findings': sorted(findings, key=lambda x: (x['file'], x['kind'], x['text'])), 'allow_rules': [{'path': g, 'kind': k, 'text': t, 'reason': r} for g, k, t, r in ALLOW], 'images': images, 'fixtures_checked': len(fixtures)}
    (out / 'privacy-scan.json').write_text(json.dumps(res, indent=1) + '\n')
    print(f'privacy: files {len(files)}, images {len(images)}, pattern findings {len(findings)} (all allowed: {not [u for u in unexpected if u in findings]}), synthetic fixtures {len(fixtures)}, unexpected {len(unexpected)}')
    for u in unexpected: print('FAIL:', u, file=sys.stderr)
    return 0 if not unexpected else 1

if __name__ == '__main__':
    sys.exit(main())
