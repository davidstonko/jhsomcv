#!/usr/bin/env python3
"""Size every block by measurement, not estimate.

Pass 1 (grow):   render, find blocks whose text prints outside the block or collides
                 with the next one, give each one more row, repeat until clean.
Pass 2 (shrink): try taking a row back off every block that was grown, all at once;
                 restore only the ones that break. This is what stops the document
                 filling up with stray blank lines.
"""
import json, os, re, subprocess, sys, openpyxl
from audit_layout import check_overlaps
from check_clipping import check as geom_check

XLSX = 'cv.xlsx'
PDF = 'preview.pdf'
EXTRA = 'extra_rows.json'

def key(t): return re.sub(r'\s+', ' ', str(t))   # full text: a 90-char prefix collides between duplicate-prefix entries

def build():
    subprocess.run([sys.executable, 'render.py'], check=True, capture_output=True)
    subprocess.run(['bash', 'mkpreview.sh'], check=True, capture_output=True)

def load():
    return json.load(open(EXTRA)) if os.path.exists(EXTRA) else {}

def save(e):
    json.dump(e, open(EXTRA, 'w'), indent=1)

def pdf_lines(pdf):
    out = subprocess.run(['pdftotext', '-bbox', pdf, '-'], capture_output=True, text=True).stdout
    pages = []
    for page in out.split('<page ')[1:]:
        w = [(float(a), float(b), t) for a, b, c, d, t in
             re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>', page)]
        pts = sorted((y, x, t) for x, y, t in w if 20 <= y <= 745 and set(t) - set('_'))
        ys, L = [], {}
        for y, x, t in pts:
            if ys and y - ys[-1] <= 2.0: L[ys[-1]].append((x, t))
            else: ys.append(y); L[y] = [(x, t)]
        pages.append([(y, ' '.join(t for _, t in sorted(L[y]))) for y in ys])
    return pages

def offenders():
    """Keys of blocks that need another row."""
    bad = set()
    ws = openpyxl.load_workbook(XLSX).active
    cells = [c.value for row in ws.iter_rows() for c in row
             if isinstance(c.value, str) and len(c.value) > 20]
    for coord, rows, over, txt in geom_check(XLSX, PDF):
        v = ws[coord].value
        if isinstance(v, str): bad.add(key(v))
    # Measurement beats estimate. The geometric check reads the rendered PDF and is
    # ground truth for any block it can trace; the analytic wrap model is an estimate
    # that runs about one line long on paragraphs of eight lines or more. Union the
    # two and every long narrative block keeps a row it does not need, which is
    # exactly the "random extra space under the paragraph" complaint. So the analytic
    # result is consulted only for blocks the geometry could NOT trace.
    _, _unver = geom_check(XLSX, PDF, report_unverified=True)
    _unkeys = {key(ws[c].value) for c, _t in _unver if isinstance(ws[c].value, str)}
    if _unkeys:
        from audit_layout import audit as _analytic
        for kind, coord, _msg in _analytic(XLSX)[0]:
            if kind == 'CLIPPED':
                v = ws[coord].value
                if isinstance(v, str) and key(v) in _unkeys: bad.add(key(v))
    ovl = [o for o in check_overlaps(PDF) if o[0] == 'COLLISION']
    if ovl:
        pages = pdf_lines(PDF)
        for sev, pno, y, g, modal, a, b in ovl:
            lines = pages[pno - 1]
            idx = next((i for i, (yy, tt) in enumerate(lines) if abs(yy - y) < 0.5), None)
            ctx = ' '.join(tt for _, tt in lines[max(0, idx - 1):idx + 1]) if idx is not None else a
            frag = re.sub(r'\s+', ' ', ctx).replace('&quot;', '"').replace('&amp;', '&').strip()
            for tail in (frag[-28:], re.sub(r'\s+', ' ', a).strip()[-18:]):
                hit = [v for v in cells if re.sub(r'\s+', ' ', v).rstrip().endswith(tail)]
                if hit:
                    bad.add(key(min(hit, key=len))); break
    return bad

def grow():
    for i in range(8):
        build()
        bad = offenders()
        print('  grow pass %d: %d block(s) need more room' % (i, len(bad)))
        if not bad: return
        e = load()
        for k in bad: e[k] = e.get(k, 0) + 1
        save(e)

def trim():
    """Take back rows the model over-allotted. Detected geometrically: a block whose
    text ends more than a full row above its bottom edge has a spare row. Trim all of
    them, then restore only the ones that break. Iterate: each pass restores the
    blocks that broke, which frees the geometry to reveal slack the pass before it
    was masking, so a low pass cap silently leaves spare rows in the document."""
    for i in range(30):
        _, slack = geom_check(XLSX, PDF, report_slack=True)
        if not slack:
            print('  trim pass %d: no spare rows' % i); return
        ws = openpyxl.load_workbook(XLSX).active
        e = load()
        touched = {}
        for coord, rows, spare, txt in slack:
            v = ws[coord].value
            if isinstance(v, str):
                k = key(v); touched[k] = spare; e[k] = e.get(k, 0) - spare
        save(e); build()
        bad = offenders()
        if bad:
            for k in bad:
                if k in touched:
                    e[k] = e.get(k, 0) + touched[k]
            save(e); build()
            if offenders():                  # still broken: undo the whole pass
                for k, sp in touched.items():
                    e[k] = e.get(k, 0) + sp
                save(e); build()
                print('  trim pass %d: reverted' % i); return
        removed = len(touched) - len(bad & set(touched))
        print('  trim pass %d: removed %d spare row(s)' % (i, removed))
        if removed == 0:
            return

def shrink():
    for i in range(8):
        e = load()
        cand = [k for k, v in e.items() if v > 0]
        if not cand: return
        trial = {k: (v - 1 if v > 0 else v) for k, v in e.items()}
        save(trial)
        build()
        bad = offenders()
        if not bad:
            print('  shrink pass %d: removed a row from %d block(s), still clean' % (i, len(cand)))
            continue
        # restore only the blocks that actually needed the row, and stop
        for k in bad:
            trial[k] = trial.get(k, 0) + 1
        save({k: v for k, v in trial.items() if v > 0})
        build()
        if not offenders():
            print('  shrink pass %d: settled, %d block(s) keep an extra row' % (i, len(bad)))
            return
        # restoring was not enough: go back to the last known-good state
        save(e); build()
        print('  shrink pass %d: reverted' % i)
        return

if __name__ == '__main__':
    if '--reset' in sys.argv and os.path.exists(EXTRA):
        os.remove(EXTRA)
    grow()
    shrink()
    trim()
    build()
    print('final:', len(offenders()), 'offender(s);', sum(load().values()), 'extra row(s) across', len(load()), 'block(s)')
