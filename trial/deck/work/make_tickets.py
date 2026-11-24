#!/usr/bin/env python3
"""章の作業票を、上流の成果物から機械的に抜き出して作る(PM)。要約はしない。
使い方: python trial/deck/work/make_tickets.py   (リポジトリの根で実行)
"""
import re, sys, yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
D = ROOT / 'trial/deck'
OUT = D / 'work'

def y(p): return yaml.safe_load(open(D / p, encoding='utf-8'))
def dump(o): return yaml.safe_dump(o, allow_unicode=True, sort_keys=False, width=1000)

brief = (D / '00-brief.md').read_text(encoding='utf-8')
claims = y('02-claims.yaml')
chapters = y('03-chapters.yaml')
story = y('04-storyline.yaml')
states = y('04-chapter-states.yaml')
proof = {p['id']: p for p in y('05-proof.yaml')}
patterns = y('06-patterns.yaml')
style_text = (D / 'style.yaml').read_text(encoding='utf-8')
terms = y('terms.yaml')
model = y('01-model.yaml')
model_head = ''.join(l for l in (D / '01-model.yaml').read_text(encoding='utf-8').splitlines(True) if l.startswith('#'))
pdata = (ROOT / 'tools/patterns-data.md').read_text(encoding='utf-8')

facts = {}
for f in y('01-sources.yaml'):
    facts[f['id']] = f
for p in sorted((D / 'incoming').glob('*.yaml')):
    doc = yaml.safe_load(open(p, encoding='utf-8'))
    items = doc if isinstance(doc, list) else (doc or {}).get('facts') or []
    for f in items:
        if isinstance(f, dict) and 'id' in f and f['id'] not in facts:
            facts[f['id']] = f

samples = {}
for p in sorted((D / '06-samples').glob('*.yaml')):
    s = yaml.safe_load(open(p, encoding='utf-8'))
    samples[s['id']] = (p, s)

rel2pat = {r['relation']: r['pattern'] for r in patterns}
els = {e['id']: e for e in model['elements']}
rels = {r['id']: r for r in model['relations']}
scns = {s['id']: s for s in model['scenarios']}

ch_ids = [c['id'] for c in chapters['chapters']] + ['appendix']
def chap_of(sid): return next(s['chapter'] for s in story if s['id'] == sid)

def build(ch):
    fname = 'ap' if ch == 'appendix' else ch
    slides = [s for s in story if s['chapter'] == ch]
    cdef = next((c for c in chapters['chapters'] if c['id'] == ch), None)
    out = []
    w = out.append
    w(f'# 章の作業票: {fname}\n\n')
    w('PMが上流の成果物から `trial/deck/work/make_tickets.py` で機械的に抜き出した。要約していない。正本は各成果物。\n\n')
    # 担当の範囲
    w('## 担当の範囲\n\n')
    w(f'成果物: `trial/deck/07-slides/{fname}.yaml`(スライドの配列。順はストーリーラインの順)。\n\n')
    w('| スライド | 型 | 扱い |\n|---|---|---|\n')
    for s in slides:
        p = proof.get(s['id'], {})
        pat = rel2pat.get(p.get('relation'), '?')
        if s['id'] in samples:
            h = f'型の見本(承認済み)。PMが `06-samples/{samples[s["id"]][0].name}` をそのまま入れる。書き直さない'
        else:
            h = '執筆する'
        w(f'| {s["id"]} | {pat} | {h} |\n')
    w('\n章扉、目次、章のまとめ、出典の一覧は、描画の道具が上流の成果物から作る。書かない。\n\n')
    # ブリーフ
    w('## ブリーフ(`00-brief.md` の全文)\n\n')
    w(brief.replace('\n# ', '\n### ').replace('\n## ', '\n### ') + '\n\n')
    # 章
    w('## 章(`03-chapters.yaml`)\n\n')
    if cdef:
        w('```yaml\n' + dump(cdef) + '```\n\n')
    else:
        w('付録。章構成の `omitted`:\n\n```yaml\n' + dump(chapters['omitted']) + '```\n\n')
    # 主張
    cl = (cdef or {}).get('claims') or []
    if cl:
        w('## 章の主張(`02-claims.yaml`)\n\n')
        w('資料の answer と summary:\n\n```yaml\n' + dump({'answer': claims['answer'], 'summary': claims['summary']}) + '```\n\n')
        w('```yaml\n' + dump([c for c in claims['claims'] if c['id'] in cl]) + '```\n\n')
    else:
        w('## 資料の結論(`02-claims.yaml`)\n\n```yaml\n' + dump({'answer': claims['answer'], 'summary': claims['summary']}) + '```\n\n')
    # 章の前提と到達点
    st = next((x for x in states if x['chapter'] == ch), None)
    if st:
        w('## 章の前提と到達点(`04-chapter-states.yaml`)\n\n```yaml\n' + dump(st) + '```\n\n')
    # スライドごと
    w('## スライドごとの見出しと立証の設計(`04-storyline.yaml`、`05-proof.yaml`)\n\n')
    w('見出し(`headline`)は1文字も変えずに写す。`source` は出典の行として道具が描く(仕様には書かない)。使ってよい事実は、立証の設計の `facts` だけ。\n\n')
    for s in slides:
        p = proof.get(s['id'])
        w(f'### {s["id"]}\n\n型: `{rel2pat.get((p or {}).get("relation"), "?")}`\n\n```yaml\n# ストーリーライン\n' + dump(s) + '# 立証の設計\n' + dump(p) + '```\n\n')
    # 参照されるスライド(他章)
    refs = set()
    for s in slides:
        p = proof.get(s['id']) or {}
        refs |= set(re.findall(r'(?:ch\d|ap)-s\d+', dump(p) + dump(s)))
    refs = [r for r in refs if any(x['id'] == r for x in story) and chap_of(r) != ch]
    if refs:
        w('## 立証の設計が参照する、ほかの章のスライドの見出し\n\n| スライド | 見出し |\n|---|---|\n')
        for r in sorted(refs):
            w(f'| {r} | {next(x["headline"] for x in story if x["id"] == r)} |\n')
        w('\n')
    # 前後の章
    if ch != 'appendix':
        i = ch_ids.index(ch)
        w('## 前後の章の見出し\n\n')
        for j in (i - 1, i + 1):
            if 0 <= j < len(ch_ids):
                oc = ch_ids[j]
                ocd = next((c for c in chapters['chapters'] if c['id'] == oc), None)
                w(f'### {oc}' + (f' {ocd["title"]}' if ocd else ' 付録') + '\n\n')
                for x in story:
                    if x['chapter'] == oc:
                        w(f'- {x["id"]}: {x["headline"]}\n')
                w('\n')
    # 事実
    fids = []
    for s in slides:
        for f in ((proof.get(s['id']) or {}).get('facts') or []) + (s.get('evidence') or []):
            if f not in fids: fids.append(f)
    w('## この章のスライドが使う事実(`01-sources.yaml`、`incoming/`)\n\n')
    if fids:
        w('```yaml\n' + dump([facts.get(f, {'id': f, 'missing': '素材台帳にない'}) for f in fids]) + '```\n\n')
    else:
        w('なし(立証の設計の facts が空)。\n\n')
    # 仕組みの定義
    eids, rids, sids = [], [], []
    def add(lst, v):
        if v not in lst: lst.append(v)
    for s in slides:
        v = (proof.get(s['id']) or {}).get('view') or {}
        for e in v.get('elements') or []: add(eids, e)
        for r in v.get('relations') or []: add(rids, r)
        if v.get('scenario'): add(sids, v['scenario'])
        if s['id'] in samples:
            b = samples[s['id']][1].get('body') or {}
            for e in b.get('elements') or []: add(eids, e)
            for r in b.get('relations') or []: add(rids, r)
            if b.get('scenario'): add(sids, b['scenario'])
    for sc in sids:
        for r in scns[sc].get('steps') or []: add(rids, r)
    for r in rids:
        if r in rels:
            add(eids, rels[r]['from']); add(eids, rels[r]['to'])
    if eids or rids or sids:
        w('## 仕組みの定義の該当する部分(`01-model.yaml`)\n\n```yaml\n' + model_head + dump({
            'elements': [els[e] for e in eids if e in els],
            'relations': [rels[r] for r in rids if r in rels],
            'scenarios': [scns[x] for x in sids]}) + '```\n\n')
    # 語彙
    text = brief + dump(cdef) + dump(slides) + dump([proof.get(s['id']) for s in slides]) + dump(st) + dump([facts.get(f) for f in fids])
    metrics = {facts[f].get('metric') for f in fids if f in facts}
    tsel = [t for t in terms['terms'] if t['term'] in text or t['term'] in metrics or t['id'] in metrics]
    w('## この章に関わる語彙(`terms.yaml` から、章の上流の文に出る語と、事実の metric の語)\n\n')
    w('```yaml\nterms:\n' + dump(tsel).replace('\n', '\n  ').rstrip() + '\n' + dump({'banned': terms['banned'], 'model_labels': terms['model_labels'], 'candidates': terms['candidates']}) + '```\n\n')
    # 表現規約
    w('## 資料の表現規約(`style.yaml` の全文)\n\n```yaml\n' + style_text + '```\n\n')
    w('## 表現の対応表(`06-patterns.yaml`)\n\n```yaml\n' + dump(patterns) + '```\n\n')
    # 見本
    used = sorted({rel2pat.get((proof.get(s['id']) or {}).get('relation')) for s in slides} - {None})
    w('## この章で使う型の見本の仕様(`06-samples/`)\n\n')
    for pat in used:
        f = D / '06-samples' / f'{pat}.yaml'
        if f.exists():
            w(f'### {pat}(`06-samples/{pat}.yaml`、画像は `06-samples/{pat}.png`)\n\n```yaml\n' + f.read_text(encoding='utf-8') + '```\n\n')
    # patterns-data
    w('## 型ごとの body の書式と収容量(`tools/patterns-data.md` の全文)\n\n')
    w(pdata.replace('\n# ', '\n### ').replace('\n## ', '\n### ') + '\n')
    (OUT / f'{fname}.md').write_text(''.join(out), encoding='utf-8')
    print('wrote', OUT / f'{fname}.md', len(''.join(out)))

for ch in ch_ids:
    build(ch)
