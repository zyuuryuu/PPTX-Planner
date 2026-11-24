#!/usr/bin/env python3
"""06-samples の見本の仕様を、07-slides の章のファイルに写し直す(PM)。見本のスライドのブロックだけを置き換える。"""
import yaml
from pathlib import Path
D = Path(__file__).resolve().parents[1]
for p in sorted((D / '06-samples').glob('*.yaml')):
    s = p.read_text(encoding='utf-8'); smp = yaml.safe_load(s); sid = smp['id']
    out = []; started = False
    for l in s.splitlines():
        if not started and l.strip() and not l.startswith('#'):
            out.append('- ' + l); started = True
        else:
            out.append(('  ' + l) if l.strip() else '')
    new = '\n'.join(out) + '\n'
    for f in (D / '07-slides').glob('*.yaml'):
        t = f.read_text(encoding='utf-8')
        key = f'- id: {sid}\n'
        if key not in t: continue
        i = t.index(key); j = t.find('\n- id:', i); j = len(t) if j < 0 else j + 1
        t2 = t[:i] + new + t[j:]
        cur = [x for x in yaml.safe_load(t) if x['id'] == sid][0]
        if cur != smp:
            f.write_text(t2, encoding='utf-8')
            assert [x for x in yaml.safe_load(t2) if x['id'] == sid][0] == smp
            print('写し直した', sid, f.name)
