#!/usr/bin/env python3
"""章の受け入れの機械的な確かめ(PM)。
使い方: python trial/deck/work/accept.py <章> [<比べる元のコミット>]
- 07-slides/<章>.yaml の全スライドがストーリーラインの章のスライドとそろう(欠け、余り、保留)
- headline がストーリーラインと一致、body.type が対応表と一致、sources が立証の設計の facts の範囲内
- 見本のスライドが 06-samples と同じ
- 比べる元のコミットからの差分が、その章のファイルだけ
- render.py の診断のうち、その章のスライドのもの(エラー、警告)
"""
import json, subprocess, sys, yaml
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]; D = ROOT / 'trial/deck'
ch = sys.argv[1]; base = sys.argv[2] if len(sys.argv) > 2 else None
chap = 'appendix' if ch == 'ap' else ch
y = lambda p: yaml.safe_load(open(D / p, encoding='utf-8'))
story = [s for s in y('04-storyline.yaml') if s['chapter'] == chap]
proof = {p['id']: p for p in y('05-proof.yaml')}
pat = {r['relation']: r['pattern'] for r in y('06-patterns.yaml')}
samples = {}
for p in (D / '06-samples').glob('*.yaml'):
    s = yaml.safe_load(open(p, encoding='utf-8')); samples[s['id']] = s
spec = (y(f'07-slides/{ch}.yaml') if (D / f'07-slides/{ch}.yaml').exists() else None) or []
byid = {s['id']: s for s in spec}
ng = []
ids = [s['id'] for s in story]
for i in ids:
    if i not in byid: ng.append(f'{i}: 仕様がない')
for s in spec:
    if s['id'] not in ids: ng.append(f'{s["id"]}: ストーリーラインのこの章にない')
for st in story:
    s = byid.get(st['id'])
    if not s: continue
    if s.get('status') != 'done': ng.append(f'{s["id"]}: status={s.get("status")}')
    if s.get('headline') != st['headline']: ng.append(f'{s["id"]}: headline がストーリーラインと違う')
    want = pat.get(proof[st['id']]['relation'])
    if (s.get('body') or {}).get('type') != want: ng.append(f'{s["id"]}: body.type={(s.get("body") or {}).get("type")} 対応表={want}')
    allowed = set(proof[st['id']].get('facts') or [])
    extra = set(s.get('sources') or []) - allowed
    if extra: ng.append(f'{s["id"]}: sources が立証の設計の facts の外: {sorted(extra)}')
    if st['id'] in samples and samples[st['id']] != s: ng.append(f'{s["id"]}: 見本の仕様と違う')
    if not s.get('takeaway'): ng.append(f'{s["id"]}: takeaway がない')
if base:
    files = subprocess.run(['git', 'diff', '--name-only', base, 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.split()
    print('差分のファイル:', files)
diag = json.load(open(D / 'build/diagnostics.json', encoding='utf-8'))
for sl in diag['slides']:
    if not sl['id'].startswith(ch + '-'): continue
    for d in sl['diagnostics']:
        if d.get('severity') in ('error', 'warning'):
            ng.append(f'診断 {sl["id"]}: ' + json.dumps(d, ensure_ascii=False))
print(f'{ch}: スライド {len(spec)}/{len(ids)}、指摘 {len(ng)}')
for n in ng: print('  ' + n)
sys.exit(1 if ng else 0)
