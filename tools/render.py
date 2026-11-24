#!/usr/bin/env python3
"""スライド仕様(YAML)からスライドを描く。

使い方: python tools/render.py <資料のディレクトリ> [--only ID ...] [--no-png]

読むもの: 03-chapters.yaml、04-storyline.yaml(順序、見出し、出典の行)、02-claims.yaml と 01-plan.yaml(章扉の問い)、
01-sources.yaml(事実の値)、01-model.yaml と terms.yaml(仕組みの定義の名前)、05-proof.yaml(仮置き)、style.yaml(色と文字の下限)、
06-samples/*.yaml(見本の仕様。1ファイル1枚)、07-slides/*.yaml(章ごとの仕様。スライドの配列。同じIDなら見本より優先)。

出すもの(<資料のディレクトリ>/build/): slides/<ID>.html、slides/<ID>.png、deck.html、diagnostics.json。
診断(文字のあふれ、文字の大きさの下限、要素の重なり、描けなかった内容)は標準出力にも出す。
文字を下限より小さくしない。収まらない内容は、スライドを分けずに診断として報告する。
型ごとの書式と収容量は tools/patterns-data.md に書く。
"""
import argparse
import html
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import yaml
from PIL import ImageFont

E = html.escape
W, H = 1280, 720
MX = 48                 # 左右の余白
CW = W - 2 * MX         # 中身の幅 1184
BAND_TOP = 648          # 結論1行の帯の上端
INK = '#111827'
GRAY_LINE = '#9CA3AF'
TEXT2 = '#374151'
PART = '#E5E7EB'
FONT_FAMILY = "'IPAPGothic','IPAGothic',sans-serif"
HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------- 文字の計測と折り返し

def _font_path():
    try:
        p = subprocess.run(['fc-match', '-f', '%{file}', 'IPAPGothic'], capture_output=True, text=True, timeout=20).stdout.strip()
        if p and Path(p).is_file():
            return p
    except (OSError, subprocess.SubprocessError):
        pass
    sys.exit('描けない: 計測に使うフォント(IPAPGothic)が見つからない')


_FONT = None


def tw(text, size, bold=False):
    """文字列の幅(px)。描画と同じフォントで測る。太字は合成されるため少し広く見積もる。"""
    global _FONT
    if _FONT is None:
        _FONT = ImageFont.truetype(_font_path(), 100)
    return _FONT.getlength(text) * size / 100 * (1.03 if bold else 1.0)


NO_START = set('、。,.)）]」』】〉》ーｰ…‥!?！？:：;；%％・ゃゅょっャュョッぁぃぅぇぉァィゥェォ')
NO_END = set('(（[「『【〈《')
BREAK_AFTER = set('のをにがはとでへやても、')
_TOKEN = re.compile(r'[A-Za-z0-9][A-Za-z0-9.,&%+\-_/#]*|\s+|.', re.S)


def wrap(text, size, maxw, bold=False, balance=True):
    """折り返した行の一覧と、語の途中で切ったかを返す。禁則(行頭の句読点、行末の開き括弧)を守る。
    balance: 行の数を変えない範囲で幅を狭め、行の長さをそろえる(最後の行だけが短く残らないように)。"""
    lines, broke = _wrap(text, size, maxw, bold)
    if balance and len(lines) > 1 and not broke and '\n' not in str(text):
        lo, hi = maxw / len(lines), maxw
        for _ in range(12):
            mid = (lo + hi) / 2
            l2, b2 = _wrap(text, size, mid, bold)
            if len(l2) == len(lines) and not b2 and max(tw(x, size, bold) for x in l2) <= mid + 0.5:
                hi = mid
            else:
                lo = mid
        lines, broke = _wrap(text, size, hi, bold)
    return lines, broke


def _wrap(text, size, maxw, bold=False):
    lines, broke = [], False
    for para in str(text).split('\n'):
        toks = _TOKEN.findall(para)
        cur = ''
        for t in toks:
            if t.isspace() and not cur:
                continue
            if tw(cur + t, size, bold) <= maxw or not cur:
                if not cur and tw(t, size, bold) > maxw and len(t) > 1:
                    # 1語が幅を越える: 文字で切る
                    broke = True
                    for ch in t:
                        if cur and tw(cur + ch, size, bold) > maxw:
                            lines.append(cur)
                            cur = ''
                        cur += ch
                    continue
                cur += t
                continue
            if t[0] in NO_START:          # 行頭に置けない字は、前の行にぶら下げる
                cur += t
                continue
            if t.isspace():
                lines.append(cur.rstrip())
                cur = ''
                continue
            k = max(cur.rfind('('), cur.rfind('（'))
            pk = max((i for i, ch in enumerate(cur) if ch in BREAK_AFTER), default=-1) + 1
            if (k <= 0 or tw(cur[k:] + t, size, bold) > maxw) and pk >= max(2, len(cur) // 3) and pk < len(cur) \
                    and _CJK.match(cur[pk]) and cur[pk] not in BREAK_AFTER and tw(cur[pk:] + t, size, bold) <= maxw:   # 助詞の後で切る
                lines.append(cur[:pk])
                cur = cur[pk:] + t
                continue
            if k > 0 and tw(cur[k:] + t, size, bold) <= maxw:   # 括弧書きは、開き括弧の前で切る
                lines.append(cur[:k].rstrip())
                cur = cur[k:] + t
                continue
            if cur[-1] in NO_END and len(cur) > 1:   # 行末に置けない字は次の行へ送る
                lines.append(cur[:-1])
                cur = cur[-1] + t
                continue
            lines.append(cur.rstrip())
            cur = t
        lines.append(cur.rstrip())
    return lines, broke


def maxw(lines, size, bold=False):
    return max([tw(l, size, bold) for l in lines] or [0])


# ---------------------------------------------------------------- SVG の部品

class Svg:
    """図の部品を積む。全ての図形と文字に、診断用の印(data-ov、data-in、data-role)を付ける。"""

    def __init__(self, ctx):
        self.ctx = ctx
        self.parts = []
        self.n = 0
        self.w = 0
        self.h = 0

    def nid(self, prefix='n'):
        self.n += 1
        return f'{prefix}{self.n}'

    def ext(self, x, y):
        self.w = max(self.w, x)
        self.h = max(self.h, y)

    def text(self, x, y, t, fs, anchor='start', color=INK, bold=False, role='figure', inside=None, ov=True, name=None):
        tid = self.nid('t')
        a = [f'x="{x:.1f}"', f'y="{y:.1f}"', f'font-size="{fs}"', f'text-anchor="{anchor}"', f'fill="{color}"', f'data-role="{role}"']
        if bold:
            a.append('font-weight="bold"')
        if inside:
            a.append(f'data-in="{inside}"')
        elif ov:
            a.append(f'data-ov="{tid}"')
        if name:
            a.append(f'data-name="{E(name)}"')
        self.parts.append(f'<text {" ".join(a)}>{E(t)}</text>')
        w = tw(t, fs, bold)
        x0 = x - (w / 2 if anchor == 'middle' else w if anchor == 'end' else 0)
        self.ext(x0 + w, y + fs * 0.3)
        return tid

    def lines(self, cx, cy, lines, fs, color=INK, bold=False, role='figure', inside=None, anchor='middle', x=None, lh=1.25):
        """複数行を、cy を中心に縦に並べる"""
        n = len(lines)
        top = cy - (n - 1) * fs * lh / 2
        for i, l in enumerate(lines):
            self.text(cx if x is None else x, top + i * fs * lh + fs * 0.35, l, fs, anchor, color, bold, role, inside)

    def rect(self, x, y, w, h, fill=PART, stroke=GRAY_LINE, sw=2, rx=10, dash=None, name=None, anc=(), ov=True, rid=None):
        rid = rid or self.nid('r')
        d = f' stroke-dasharray="{dash}"' if dash else ''
        a = f' data-ov="{rid}"' if ov else ''
        if anc:
            a += f' data-anc="{" ".join(anc)}"'
        if name:
            a += f' data-name="{E(name)}"'
        self.parts.append(f'<rect id="{rid}" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}{a}/>')
        self.ext(x + w, y + h)
        return rid

    def diamond(self, cx, cy, w, h, name=None, stroke='#6B7280', sw=2, dash=None):
        rid = self.nid('d')
        p = f'{cx:.1f},{cy - h / 2:.1f} {cx + w / 2:.1f},{cy:.1f} {cx:.1f},{cy + h / 2:.1f} {cx - w / 2:.1f},{cy:.1f}'
        d = f' stroke-dasharray="{dash}"' if dash else ''
        nm = f' data-name="{E(name)}"' if name else ''
        self.parts.append(f'<polygon id="{rid}" points="{p}" fill="#fff" stroke="{stroke}" stroke-width="{sw}" data-shape="diamond" data-ov="{rid}"{d}{nm}/>')
        self.ext(cx + w / 2, cy + h / 2)
        return rid

    def line(self, pts, arrow=True, w=3, color=TEXT2, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        m = ' marker-end="url(#a)"' if arrow else ''
        p = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        self.parts.append(f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="{w}"{d}{m}/>')
        for x, y in pts:
            self.ext(x, y)

    def path(self, d, arrow=True, w=3, color=TEXT2):
        m = ' marker-end="url(#a)"' if arrow else ''
        self.parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}"{m}/>')

    def raw(self, s):
        self.parts.append(s)

    def svg(self, w=None, h=None):
        w = w if w else math.ceil(self.w) + 4
        h = h if h else math.ceil(self.h) + 4
        return (f'<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg" style="overflow:visible;display:block">'
                '<defs><marker id="a" markerUnits="userSpaceOnUse" markerWidth="16" markerHeight="16" refX="14" refY="8" orient="auto">'
                '<path d="M0,0 L16,8 L0,16 z" fill="#374151"/></marker></defs>' + ''.join(self.parts) + '</svg>')


# ---------------------------------------------------------------- 資料の読み込み

def load_yaml(path, required=True):
    if not path.is_file():
        if required:
            sys.exit(f'描けない: {path} がない')
        return None
    try:
        return yaml.safe_load(path.read_text(encoding='utf-8'))
    except yaml.YAMLError as e:
        mark = getattr(e, 'problem_mark', None)
        pos = f'{mark.line + 1}行 {mark.column + 1}列' if mark else '位置不明'
        sys.exit(f'描けない: {path}: {pos}: YAMLとして読めない')


def pt2px(v):
    return float(str(v).replace('pt', '')) * 4 / 3


_CJK = re.compile(r'[぀-ヿ㐀-鿿]')


def strip_gloss(name):
    """名前から、日本語を含まない括弧書き(原文の語)を除く。例: 端末(endpoints) → 端末"""
    out = re.sub(r'[(（]([^()（）]*)[)）]', lambda m: '' if not _CJK.search(m.group(1)) else m.group(0), str(name))
    return out.strip()


class Deck:
    def __init__(self, root):
        self.root = root
        st = load_yaml(root / 'style.yaml') or {}
        common = st.get('common') or {}
        fm = common.get('font_min') or {}
        self.min = {
            'headline': pt2px(fm.get('headline', '24pt')), 'source': pt2px(fm.get('source_line', '16pt')),
            'body': pt2px(fm.get('body', '18pt')), 'takeaway': pt2px(fm.get('body', '18pt')),
            'figure': pt2px(fm.get('figure_text', '16pt')), 'note': pt2px(fm.get('note', '14pt')),
        }
        self.colors = common.get('colors') or {}
        self.max_hues = common.get('max_hues_per_slide')
        self.chapters_doc = load_yaml(root / '03-chapters.yaml') or {}
        self.chapters = [c for c in self.chapters_doc.get('chapters') or [] if isinstance(c, dict)]
        self.storyline = [s for s in load_yaml(root / '04-storyline.yaml') or [] if isinstance(s, dict)]
        self.S = {s['id']: s for s in self.storyline}
        self.facts = {f['id']: f for f in load_yaml(root / '01-sources.yaml') or [] if isinstance(f, dict) and 'id' in f}
        model = load_yaml(root / '01-model.yaml', required=False) or {}
        self.el = {e['id']: e for e in model.get('elements') or []}
        self.rel = {r['id']: r for r in model.get('relations') or []}
        self.scn = {s['id']: s for s in model.get('scenarios') or []}
        terms = load_yaml(root / 'terms.yaml', required=False) or {}
        self.model_labels = terms.get('model_labels') or {}
        claims = load_yaml(root / '02-claims.yaml', required=False) or {}
        self.claims = {c['id']: c for c in claims.get('claims') or []}
        self.plan = {q['id']: q for q in load_yaml(root / '01-plan.yaml', required=False) or [] if isinstance(q, dict)}
        proof = load_yaml(root / '05-proof.yaml', required=False) or []
        self.proof = {p.get('id'): p for p in proof if isinstance(p, dict)}
        pats = load_yaml(root / '06-patterns.yaml', required=False) or []
        self.pattern_of = {(p['relation'], p.get('base', 'none')): p['pattern'] for p in pats if isinstance(p, dict)}
        # スライド仕様: 見本 → 章ごと(後のものが優先)
        self.specs, self.spec_file = {}, {}
        for f in sorted((root / '06-samples').glob('*.yaml')):
            d = load_yaml(f)
            if isinstance(d, dict) and d.get('id'):
                self.specs[d['id']] = d
                self.spec_file[d['id']] = f.relative_to(root).as_posix()
        for f in sorted((root / '07-slides').glob('*.yaml')) if (root / '07-slides').is_dir() else []:
            for d in load_yaml(f) or []:
                if isinstance(d, dict) and d.get('id'):
                    self.specs[d['id']] = d
                    self.spec_file[d['id']] = f.relative_to(root).as_posix()

    def name(self, eid, labels=None):
        if labels and eid in labels:
            return str(labels[eid])
        if eid in self.model_labels:
            return strip_gloss(self.model_labels[eid])
        if eid in self.el:
            return strip_gloss(self.el[eid]['name'])
        return None

    def color_of(self, name):
        """色の割り当ての対象と名前が一致すれば、その色"""
        if name is None:
            return None
        base = re.sub(r'[(（].*?[)）]', '', str(name)).strip()
        return self.colors.get(str(name)) or self.colors.get(base)


# ---------------------------------------------------------------- 1枚の文脈

class Ctx:
    def __init__(self, deck, sid, spec):
        self.deck, self.sid, self.spec = deck, sid, spec or {}
        self.body = (spec or {}).get('body') or {}
        self.diags = []
        self.wraps = []
        self.colors_used = set()
        self.avail_h = 400

    def diag(self, kind, message, severity='error', target=None):
        self.diags.append({'slide': self.sid, 'kind': kind, 'severity': severity, 'target': target, 'message': message})

    def wrap(self, text, size, width, bold=False, what=None):
        lines, broke = wrap(text, size, width, bold)
        if len(lines) > 1:
            self.wraps.append({'target': what or str(text)[:20], 'lines': lines})
        if broke:
            self.diag('overflow', f'語の途中で改行した: 「{text}」', 'warning', what)
        return lines

    def color(self, name):
        c = self.deck.color_of(name)
        if c:
            self.colors_used.add(c)
        return c

    def color_key(self, key, target):
        if key in self.deck.colors:
            self.colors_used.add(self.deck.colors[key])
            return self.deck.colors[key]
        self.diag('unrendered', f'色の割り当てにない名前「{key}」を色に指定した。黒で描いた', 'error', target)
        return INK

    def fact(self, fid, target):
        f = self.deck.facts.get(fid)
        if f is None:
            self.diag('unrendered', f'事実 {fid} が素材台帳にない', 'error', target)
        elif fid not in (self.spec.get('sources') or []):
            self.diag('unrendered', f'事実 {fid} が、このスライドの sources にない', 'warning', target)
        return f

    def text(self, s, target='text'):
        """{F001}(値と単位)、{F001:value}、{F001:unit}、{F001:metric} を素材台帳の値に置き換える"""
        def rep(m):
            fid, field = m.group(1), m.group(2) or ''
            f = self.fact(fid, target)
            if f is None:
                return f'[{fid}?]'
            if field == 'value' or field == '':
                if f.get('value') is None:
                    self.diag('unrendered', f'事実 {fid} に value がない', 'error', target)
                    return f'[{fid}?]'
                v = fmt_num(f['value'])
                return v if field == 'value' else v + fmt_unit(f.get('unit'))
            if field in ('unit', 'metric'):
                return str(f.get(field) or '')
            self.diag('unrendered', f'参照の書式 {{{fid}:{field}}} が分からない', 'error', target)
            return f'[{fid}?]'
        return re.sub(r'\{(F\d+)(?::(\w+))?\}', rep, str(s))

    def value(self, v, target):
        """数値の参照: F207(事実の value)、または {fact: F207, as: 27, round: 0}。as の数は事実の本文にあること"""
        if isinstance(v, str) and re.fullmatch(r'F\d+', v):
            f = self.fact(v, target)
            if f is None or not isinstance(f.get('value'), (int, float)):
                if f is not None:
                    self.diag('unrendered', f'事実 {v} の value が数でない', 'error', target)
                return None, '', ''
            return float(f['value']), fmt_num(f['value']), str(f.get('unit') or '')
        if isinstance(v, dict) and 'fact' in v:
            f = self.fact(v['fact'], target)
            if f is None:
                return None, '', ''
            if 'as' not in v:
                return self.value(v['fact'], target)
            num = v['as']
            hay = ' '.join(str(f.get(k) or '') for k in ('statement', 'quote', 'value')) + ' ' + ' '.join(map(str, f.get('qualifiers') or []))
            hay = hay.replace(',', '')
            if not re.search(r'(?<![\d.])' + re.escape(fmt_num(num).replace(',', '')) + r'(?![\d])', hay):
                self.diag('unrendered', f'数 {num} が事実 {v["fact"]} の本文(statement、quote、qualifiers)にない', 'error', target)
            shown = float(num)
            label = fmt_num(num)
            if 'round' in v:
                r = round(float(num), int(v['round']))
                r = int(r) if int(v['round']) == 0 else r
                if r != float(num):
                    label = '約' + fmt_num(r)
            return shown, label, str(v.get('unit') or f.get('unit') or '')
        self.diag('unrendered', f'数値は事実のIDで参照する(書かれた値: {v})', 'error', target)
        return None, '', ''


def fmt_num(v):
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, int) or (isinstance(v, float) and v.is_integer() and abs(v) >= 1):
        return f'{int(v):,}'
    if isinstance(v, float):
        return f'{v:g}'
    return str(v)


def fmt_unit(u):
    if not u:
        return ''
    return (' ' + u) if re.match(r'[A-Za-z]', str(u)) else str(u)


def parse_index(h, name):
    """'steps[0]' → 0"""
    m = re.fullmatch(rf'{name}\[(\d+)\]', str(h or ''))
    return int(m.group(1)) if m else None


# ---------------------------------------------------------------- 型ごとの描画
# どの関数も (図の HTML, 図の下に置く文の HTML) を返す。収まらないときは診断を出し、文字は縮めない。

FIG = 22      # 図の中の文字(16pt の下限 21.3px の上)
NOTE = 19     # 図の注記(14pt の下限 18.7px の上)
BODY = 24     # 本文(18pt の下限 24px)


def check_height(ctx, h, what='図'):
    if h > ctx.avail_h + 0.5:
        ctx.diag('overflow', f'{what}の高さ {h:.0f}px が、使える高さ {ctx.avail_h:.0f}px を越える', 'error', what)


def check_width(ctx, w, what='図', limit=CW):
    if w > limit + 0.5:
        ctx.diag('overflow', f'{what}の幅 {w:.0f}px が、使える幅 {limit:.0f}px を越える', 'error', what)


def r_statement(ctx):
    b = ctx.body
    hl = b.get('highlight')
    text = b.get('text')
    q = b.get('quote_of')
    if q:
        f = ctx.fact(q, 'quote_of')
        if text is None and f is not None:
            text = f.get('quote')
    if not text:
        ctx.diag('unrendered', 'statement に text がない', 'error', 'text')
        text = ''
    text = ctx.text(text)
    em = 'border:5px solid #111827;' if hl == 'text' else ''
    if q:
        attr = f'<div data-role="figure" style="font-size:{FIG}px;color:#4B5563;margin-top:10px">{E(ctx.text(b["attribution"]))}</div>' if b.get('attribution') else ''
        main = (f'<div data-role="body" style="{em}border-left:8px solid #9CA3AF;padding:18px 28px;font-size:28px;line-height:1.6;background:#F9FAFB">'
                f'「{E(text)}」{attr}</div>')
    else:
        main = f'<div data-role="body" style="{em}padding:14px 22px;font-size:32px;font-weight:bold;line-height:1.5;display:inline-block">{E(text)}</div>'
    cav = ''
    if b.get('caveat'):
        if hl == 'caveat':
            cav = f'<div data-role="body" style="margin-top:34px;display:inline-block;border:5px solid #111827;padding:14px 26px;font-size:28px;font-weight:bold">{E(ctx.text(b["caveat"]))}</div>'
        else:
            cav = f'<div data-role="body" style="margin-top:30px;font-size:26px;color:{TEXT2}">{E(ctx.text(b["caveat"]))}</div>'
    if hl not in ('text', 'caveat', None):
        ctx.diag('unrendered', f'highlight「{hl}」は text か caveat で書く', 'error', 'highlight')
    return main + cav


def tag(mark, ctx):
    if not mark:
        return ''
    key = {'案': '案の印', '運用': 'このSOCの運用の印'}.get(mark)
    if key is None:
        ctx.diag('unrendered', f'mark「{mark}」は 案 か 運用 で書く', 'error', 'mark')
        return ''
    c = ctx.color_key(key, 'mark')
    return f'<span class="tag" data-role="note" style="background:{c}">{E(mark)}</span>'


def r_plain_list(ctx):
    b = ctx.body
    items = b.get('items') or []
    if not items:
        ctx.diag('unrendered', 'plain-list に items がない', 'error', 'items')
    hl = b.get('highlight')
    hi = parse_index(hl, 'items')
    out = tag(b.get('mark'), ctx)
    if b.get('title'):
        st = 'border:5px solid #111827;padding:4px 14px;font-weight:bold' if hl == 'title' else 'font-weight:bold;padding:4px 0'
        out += f'<span data-role="body" style="display:inline-block;{st};font-size:26px;vertical-align:middle">{E(ctx.text(b["title"]))}</span>'
    elif hl == 'title':
        ctx.diag('unrendered', 'highlight が title だが title がない', 'error', 'highlight')
    lis = ''
    for i, it in enumerate(items):
        t = it.get('text') if isinstance(it, dict) else it
        sub = it.get('sub') if isinstance(it, dict) else None
        st = 'border:5px solid #111827;padding:0 10px;font-weight:bold;display:inline-block' if hi == i else ''
        s = f'<li><span style="{st}">・{E(ctx.text(t))}</span>'
        if sub:
            s += '<ul style="list-style:none;padding-left:40px;font-size:24px;line-height:1.5;color:#374151">' + ''.join(f'<li>{E(ctx.text(x))}</li>' for x in sub) + '</ul>'
        lis += s + '</li>'
    if hi is not None and hi >= len(items):
        ctx.diag('unrendered', f'highlight {hl} に当たる項目がない', 'error', 'highlight')
    out += f'<ul data-role="body" style="margin-top:18px;list-style:none;font-size:28px;line-height:1.75;padding-left:24px">{lis}</ul>'
    return out


def paras(ctx, desc, where):
    """説明: 文字列、または段落の配列(段落は文字列か {text, color})"""
    if desc is None:
        return []
    if not isinstance(desc, list):
        desc = [desc]
    out = []
    for p in desc:
        if isinstance(p, dict):
            out.append((ctx.text(p.get('text', '')), ctx.color_key(p['color'], where) if p.get('color') else INK, bool(p.get('color'))))
        else:
            out.append((ctx.text(p), INK, False))
    return out


def r_step_flow(ctx):
    b = ctx.body
    steps = b.get('steps') or []
    n = len(steps)
    if n == 0:
        ctx.diag('unrendered', 'step-flow に steps がない', 'error', 'steps')
        return ''
    hi = parse_index(b.get('highlight'), 'steps')
    if b.get('highlight') and hi is None:
        ctx.diag('unrendered', f'highlight「{b.get("highlight")}」は steps[番号] で書く', 'error', 'highlight')
    start = b.get('numbering', 1)
    labels = [s.get('next') for s in steps[:-1]]
    gap = max([70] + [tw(l, FIG) + 24 for l in labels if l])
    bw = (CW - (n - 1) * gap) / n
    if bw < 170:
        ctx.diag('overflow', f'段が {n} 個あり、1つの箱の幅が {bw:.0f}px になる(下限 170px)', 'error', 'steps')
    inner = bw - 40
    NFS, DFS = 26, 24
    boxes = []
    for i, s in enumerate(steps):
        nm = ('' if start is None else f'{start + i}. ') + ctx.text(s.get('name', ''))
        nl = ctx.wrap(nm, NFS, inner, True, f'steps[{i}].name')
        ps = []
        for t, c, bold in paras(ctx, s.get('description'), f'steps[{i}]'):
            ps.append((ctx.wrap(t, DFS, inner, bold, f'steps[{i}].description'), c, bold))
        h = 28 + len(nl) * NFS * 1.25 + sum(18 + len(l) * DFS * 1.4 for l, _, _ in ps) + 26
        boxes.append((nl, ps, h))
        if maxw(nl, NFS, True) > inner + 1 or any(maxw(l, DFS, bd) > inner + 1 for l, _, bd in ps):
            ctx.diag('overflow', f'段 {i} の文字が箱の幅に収まらない', 'error', f'steps[{i}]')
    hmax = max(h for _, _, h in boxes)
    sv = Svg(ctx)
    cy = hmax / 2 + 4
    for i, (nl, ps, h) in enumerate(boxes):
        x = i * (bw + gap)
        y = cy - h / 2
        em = hi == i
        rid = sv.rect(x, y, bw, h, fill='#fff', stroke=INK if em else GRAY_LINE, sw=5 if em else 2, name=f'steps[{i}]')
        yy = y + 28
        for l in nl:
            sv.text(x + bw / 2, yy + NFS * 0.85, l, NFS, 'middle', INK, True, inside=rid)
            yy += NFS * 1.25
        for lines, c, bold in ps:
            yy += 18
            for l in lines:
                sv.text(x + bw / 2, yy + DFS * 1.0, l, DFS, 'middle', c, bold, inside=rid)
                yy += DFS * 1.4
        if i < n - 1:
            x1, x2 = x + bw, x + bw + gap - 6
            sv.line([(x1, cy), (x2, cy)])
            if labels[i]:
                sv.text((x1 + x2) / 2, cy - 12, ctx.text(labels[i]), FIG, 'middle', TEXT2)
    if hi is not None and hi >= n:
        ctx.diag('unrendered', f'highlight steps[{hi}] に当たる段がない', 'error', 'highlight')
    check_height(ctx, hmax + 8)
    return sv.svg(CW, hmax + 8)


def r_cause_chain(ctx):
    b = ctx.body
    chain = b.get('chain') or []
    n = len(chain)
    if n < 2:
        ctx.diag('unrendered', 'cause-chain の chain は2つ以上', 'error', 'chain')
        if n == 0:
            return ''
    hi = parse_index(b.get('highlight'), 'chain')
    if b.get('highlight') and hi is None:
        ctx.diag('unrendered', f'highlight「{b.get("highlight")}」は chain[番号] で書く', 'error', 'highlight')
    gap = max(100, tw(b.get('link', 'ので'), FIG) + 40)
    bw = (CW - (n - 1) * gap) / n
    if bw < 160:
        ctx.diag('overflow', f'要素が {n} 個あり、1つの箱の幅が {bw:.0f}px になる(下限 160px)', 'error', 'chain')
    FS = 24
    nodes = []
    for i, c in enumerate(chain):
        t = ctx.text(c.get('text') if isinstance(c, dict) else c)
        lines = ctx.wrap(t, FS, bw - 40, hi == i, f'chain[{i}]')
        nodes.append((t, lines))
    bh = max(120, max(len(l) for _, l in nodes) * FS * 1.3 + 44)
    sv = Svg(ctx)
    y = 10
    for i, (t, lines) in enumerate(nodes):
        x = i * (bw + gap)
        em = hi == i
        col = ctx.color(t)
        if em:
            rid = sv.rect(x, y, bw, bh, fill='#fff', stroke=INK, sw=5, name=f'chain[{i}]')
            sv.lines(x + bw / 2, y + bh / 2, lines, FS, INK, True, inside=rid)
        elif col:      # 色の割り当てのある対象は、塗らずに色の枠と色の文字
            rid = sv.rect(x, y, bw, bh, fill='#fff', stroke=col, sw=3, name=f'chain[{i}]')
            sv.lines(x + bw / 2, y + bh / 2, lines, FS + 4 if len(lines) == 1 else FS, col, False, inside=rid)
        else:
            rid = sv.rect(x, y, bw, bh, name=f'chain[{i}]')
            sv.lines(x + bw / 2, y + bh / 2, lines, FS, INK, False, inside=rid)
        if maxw(lines, FS, em) > bw - 30:
            ctx.diag('overflow', f'chain[{i}] の文字が箱に収まらない', 'error', f'chain[{i}]')
        if i < n - 1:
            x1 = x + bw
            sv.line([(x1, y + bh / 2), (x1 + gap - 10, y + bh / 2)], w=6)
            sv.text(x1 + gap / 2, y + bh / 2 - 16, b.get('link', 'ので'), FIG, 'middle')
    if hi is not None and hi >= n:
        ctx.diag('unrendered', f'highlight chain[{hi}] に当たる要素がない', 'error', 'highlight')
    h = y + bh + 6
    out = sv.svg(CW, h)
    if b.get('example'):
        out += f'<div data-role="body" style="margin-top:24px;font-size:{BODY}px;color:{TEXT2}">{E(ctx.text(b["example"]))}</div>'
    check_height(ctx, h + (60 if b.get('example') else 0))
    return out


def r_pie_chart(ctx):
    b = ctx.body
    data = b.get('data') or []
    if not data:
        ctx.diag('unrendered', 'pie-chart に data がない', 'error', 'data')
        return ''
    hl = b.get('highlight')
    rows = []
    for i, d in enumerate(data):
        v, label, unit = ctx.value(d.get('value'), f'data[{i}]')
        rows.append((str(d.get('label', '')), v, label, unit, d.get('bound', '')))
    vals = [r[1] or 0 for r in rows]
    total = sum(vals)
    if rows and all(r[3] == '%' for r in rows) and not (95 <= total <= 105):
        ctx.diag('unrendered', f'構成比の合計が {total:g}% で、100% にならない', 'error', 'data')
    if hl and hl not in [r[0] for r in rows]:
        ctx.diag('unrendered', f'highlight「{hl}」に当たる label がない', 'error', 'highlight')
    LFS, PITCH = 26, 66
    leg_h = len(rows) * PITCH
    r = max(120, min(165, (ctx.avail_h - 20) / 2))
    sv = Svg(ctx)
    cx, cy = r + 25, r + 25
    ang = -90.0
    fallback = ['#9CA3AF', '#6B7280', '#4B5563', '#D1D5DB']
    cols = []
    for i, (lab, v, *_rest) in enumerate(rows):
        c = ctx.color(lab)
        if not c:
            c = fallback[i % len(fallback)]
            ctx.diag('unrendered', f'「{lab}」に色の割り当てがない。灰色で描いた', 'warning', f'data[{i}]')
        cols.append(c)
    for i, (lab, v, *_rest) in enumerate(rows):
        if not v or total <= 0:
            continue
        sweep = v / total * 360
        a1, a2 = math.radians(ang), math.radians(ang + sweep)
        x1, y1, x2, y2 = cx + r * math.cos(a1), cy + r * math.sin(a1), cx + r * math.cos(a2), cy + r * math.sin(a2)
        em = lab == hl
        large = 1 if sweep > 180 else 0
        if sweep >= 359.9:
            sv.raw(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{cols[i]}"/>')
        else:
            sv.raw(f'<path d="M{cx},{cy} L{x1:.1f},{y1:.1f} A{r},{r} 0 {large} 1 {x2:.1f},{y2:.1f} z" fill="{cols[i]}" stroke="{INK if em else "#fff"}" stroke-width="{6 if em else 2}"/>')
        ang += sweep
    sv.ext(cx + r, cy + r)
    lx = 2 * r + 80
    for i, (lab, v, vl, unit, bound) in enumerate(rows):
        em = lab == hl
        y = 50 + i * PITCH
        thin = v is not None and total > 0 and v / total * 360 < 1.5
        t = f'{lab} {vl}{fmt_unit(unit)}{bound}' + ('(細すぎて円に出ない)' if thin else '')
        sv.raw(f'<rect x="{lx}" y="{y}" width="34" height="34" fill="{cols[i]}"/>')
        sv.text(lx + 48, y + 27, t, LFS, bold=em, name=f'data[{i}]')
        if lx + 48 + tw(t, LFS, em) > CW:
            ctx.diag('overflow', f'凡例「{t}」が右端を越える', 'error', f'data[{i}]')
    h = max(2 * r + 50, 50 + leg_h)
    check_height(ctx, h)
    return sv.svg(CW, h)


def r_table(ctx):
    b = ctx.body
    cols = b.get('columns') or []
    rows = b.get('rows') or []
    if not cols or not rows:
        ctx.diag('unrendered', 'table に columns と rows が要る', 'error', 'columns')
        return ''
    hl = str(b.get('highlight') or '')
    hc, hr = parse_index(hl, 'columns'), parse_index(hl, 'rows')
    m = re.fullmatch(r'cells\[(\d+)\]\[(\d+)\]', hl)
    hcell = (int(m.group(1)), int(m.group(2))) if m else None
    if hl and hc is None and hr is None and hcell is None:
        ctx.diag('unrendered', f'highlight「{hl}」は columns[番号]、rows[番号]、cells[行][列] で書く', 'error', 'highlight')
    names = [c.get('name') if isinstance(c, dict) else c for c in cols]
    aligns = []
    for j, c in enumerate(cols):
        a = c.get('align') if isinstance(c, dict) else None
        if a is None:   # 全てのセルが事実の参照で始まる列は右に寄せる
            a = 'right' if all(isinstance(r, list) and j < len(r) and re.match(r'(\{?F\d+)', str(r[j])) for r in rows) else 'left'
        aligns.append(a)
    td = 'padding:12px;border-bottom:1px solid #D1D5DB'
    BK = '5px solid #111827'
    out = f'<table data-role="body" style="border-collapse:collapse;font-size:{BODY}px;width:{CW - 34}px"><tr style="background:#F3F4F6">'
    for j, nm in enumerate(names):
        em = f';border:{BK};border-bottom:none' if hc == j else ''
        out += f'<th style="text-align:{aligns[j]};{td}{em}">{E(ctx.text(nm))}</th>'
    out += '</tr>'
    for i, r in enumerate(rows):
        if not isinstance(r, list) or len(r) != len(cols):
            ctx.diag('unrendered', f'rows[{i}] のセルの数が列の数と違う', 'error', f'rows[{i}]')
            r = (r if isinstance(r, list) else [r]) + [''] * len(cols)
        out += '<tr>'
        for j in range(len(cols)):
            cell = str(r[j])
            if re.fullmatch(r'F\d+', cell):
                cell = '{' + cell + '}'
            em = ''
            if hc == j:
                em = f';border-left:{BK};border-right:{BK}' + (f';border-bottom:{BK}' if i == len(rows) - 1 else '')
            if hr == i:
                em = f';border-top:{BK};border-bottom:{BK}' + (f';border-left:{BK}' if j == 0 else '') + (f';border-right:{BK}' if j == len(cols) - 1 else '') + ';font-weight:bold'
            if hcell == (i, j):
                em = f';border:{BK};font-weight:bold'
            out += f'<td style="{td};text-align:{aligns[j]}{em}">{E(ctx.text(cell, f"rows[{i}][{j}]"))}</td>'
        out += '</tr>'
    return out + '</table>'


def r_tree(ctx):
    b = ctx.body
    root = b.get('root')
    if not root:
        ctx.diag('unrendered', 'tree に root がない', 'error', 'root')
        return ''
    hl = b.get('highlight')
    levels = b.get('levels') or []
    FS = FIG
    nodes = []   # (depth, name, parent_index)

    def walk(items, depth, parent):
        for it in items or []:
            nm = ctx.text(it.get('name') if isinstance(it, dict) else it)
            nodes.append([depth, nm, parent, None])
            me = len(nodes) - 1
            if isinstance(it, dict):
                walk(it.get('children'), depth + 1, me)
    nodes.append([0, ctx.text(root), None, None])
    walk(b.get('children'), 1, 0)
    if hl and sum(1 for n in nodes if n[1] == hl) != 1:
        ctx.diag('unrendered', f'highlight「{hl}」に当たる節がない、または同じ名前の節が複数ある', 'error', 'highlight')
    depth = max(n[0] for n in nodes)
    colw = []
    for d in range(depth + 1):
        ws = [tw(n[1], 26 if d == 0 else FS, d == 0 or n[1] == hl) for n in nodes if n[0] == d]
        colw.append(max(140, max(ws) + 44))
    GAPX, NH, GAPY = 90, 52, 16
    xs = [0]
    for d in range(1, depth + 1):
        xs.append(xs[-1] + colw[d - 1] + GAPX)
    top = 40 if levels else 4
    # 葉を上から並べ、親は子の中央に置く
    kids = {i: [j for j, n in enumerate(nodes) if n[2] == i] for i in range(len(nodes))}
    slot = [top]

    def place(i):
        if not kids[i]:
            nodes[i][3] = slot[0] + NH / 2
            slot[0] += NH + GAPY
        else:
            for k in kids[i]:
                place(k)
            ys = [nodes[k][3] for k in kids[i]]
            nodes[i][3] = (min(ys) + max(ys)) / 2
    place(0)
    sv = Svg(ctx)
    for d, lab in enumerate(levels):
        if d + 1 <= depth:
            sv.text(xs[d + 1], top - 18, ctx.text(lab), FS, color=TEXT2)
    ids = {}
    for i, (d, nm, p, y) in enumerate(nodes):
        em = nm == hl
        h = 64 if d == 0 else NH
        ids[i] = sv.rect(xs[d], y - h / 2, colw[d], h, stroke=INK if em else GRAY_LINE, sw=5 if em else 2, name=nm)
        sv.text(xs[d] + colw[d] / 2, y + (26 if d == 0 else FS) * 0.35, nm, 26 if d == 0 else FS, 'middle', INK, d == 0 or em, inside=ids[i])
        if p is not None:
            pd = nodes[p][0]
            x0 = xs[pd] + colw[pd]
            xm = x0 + GAPX / 2
            py = nodes[p][3]
            sv.line([(x0, py), (xm, py), (xm, y), (xs[d], y)], arrow=False, w=2, color=GRAY_LINE)
    used_w = xs[-1] + colw[-1]
    a = b.get('aside')
    if a:
        aw = CW - used_w - 40
        ax = used_w + 30
        if aw < 260:
            ctx.diag('overflow', f'aside を置く幅が {aw:.0f}px しかない', 'error', 'aside')
            aw = 260
        lines = ctx.wrap(ctx.text(a.get('text', '')), FS, aw - 28, False, 'aside')
        ah = 50 + len(lines) * FS * 1.3 + 14
        ay = max(top, nodes[0][3] - ah / 2)
        mark = a.get('mark')
        col = ctx.color_key('案の印', 'aside') if mark == '案' else GRAY_LINE
        rid = sv.rect(ax, ay, aw, ah, fill='#fff', stroke=col, sw=2, rx=8, dash='8 6', name='aside')
        if mark:
            sv.text(ax + 14, ay + 28, mark, NOTE, color=col, bold=True, role='note', inside=rid)
        for k, l in enumerate(lines):
            sv.text(ax + 14, ay + 60 + k * FS * 1.3, l, FS, inside=rid)
        used_w = ax + aw
    check_width(ctx, used_w)
    check_height(ctx, sv.h + 4)
    return sv.svg(CW)


# ---------------------------------------------------------------- 流れ図(仕組みの定義の場面から)

def r_flowchart(ctx):
    b, dk = ctx.body, ctx.deck
    sc = dk.scn.get(b.get('scenario'))
    if sc is None:
        ctx.diag('unrendered', f'場面 {b.get("scenario")} が仕組みの定義にない', 'error', 'scenario')
        return ''
    labels = b.get('labels') or {}
    rels = []
    for rid in sc.get('steps') or []:
        r = dk.rel.get(rid)
        if r is None:
            ctx.diag('unrendered', f'つながり {rid} が仕組みの定義にない', 'error', rid)
        else:
            rels.append(r)
    outs = {}
    for r in rels:
        outs.setdefault(r['from'], []).append(r)
    for k in outs:
        outs[k].sort(key=lambda r: r.get('order') or 0)
    start = b.get('start') or (rels[0]['from'] if rels else None)
    if start not in outs:
        ctx.diag('unrendered', f'始まりの {start} から出るつながりが場面にない', 'error', 'start')
        return ''

    def lab(rid, key, default):
        v = labels.get(rid)
        if isinstance(v, dict):
            return str(v.get(key, default) if v.get(key) is not None else default)
        if isinstance(v, str) and key == 'label':
            return v
        return default

    def elname(eid):
        n = dk.name(eid, labels)
        if n is None:
            ctx.diag('unrendered', f'要素 {eid} が仕組みの定義にない', 'error', eid)
            return eid
        return n

    proposals = set(b.get('proposal_parts') or []) | {r['id'] for r in rels if r.get('proposal')}
    hlv = b.get('highlight')
    hl_ids = set(hlv.get('ids') or []) if isinstance(hlv, dict) else ({hlv} if hlv else set())
    hl_label = hlv.get('label') if isinstance(hlv, dict) else None
    for h in hl_ids:
        if h not in dk.rel and h not in dk.el:
            ctx.diag('unrendered', f'highlight の {h} が仕組みの定義にない', 'error', 'highlight')

    FS = FIG
    LH = FS * 1.25
    G = 34   # 「いいえ」は矢印の上に置く。ひし形の角の上の空きにかかってよい

    # 主の列: 始まり → 分かれ目(最後の道を除く) → 最後の道の行き先。行き先がさらに道を持てば、その先は腕で描く
    cols = []
    sbold = dk.el.get(start, {}).get('kind') == 'action'
    sl = ctx.wrap(elname(start), FS, 110, sbold, start)
    cols.append({'kind': 'start', 'lines': sl, 'w': maxw(sl, FS, sbold) + 40, 'h': max(76, len(sl) * LH + 30), 'id': start})
    routes = outs[start]
    for r in routes[:-1]:
        t = lab(r['id'], 'condition', r.get('condition', ''))
        tl = ctx.wrap(t, FS, 120, False, r['id'] + '.condition')
        wt, ht = maxw(tl, FS), len(tl) * LH
        dl = ctx.wrap(lab(r['id'], 'label', strip_gloss(r.get('label', ''))), FS, 200, True, r['id'] + '.label')
        dw, dh = maxw(dl, FS, True) + 36, max(56, len(dl) * LH + 26)
        cols.append({'kind': 'dec', 'r': r, 'lines': tl, 'wt': wt, 'ht': ht,
                     'dest': dl, 'dw': max(120, dw), 'dh': dh, 'dcol': ctx.color(elname(r['to']))})
    # ひし形: 高さをそろえ、文字が収まる幅にする(|x|/半幅 + |y|/半高 <= 1)
    DH = max([120] + [2 * c['ht'] + 30 for c in cols if c['kind'] == 'dec'])
    for c in cols:
        if c['kind'] == 'dec':
            c['h'] = DH
            c['w'] = max(130, c['wt'] / (1 - c['ht'] / DH) + 24)
    last = routes[-1]
    nxt = last['to']
    # 行き先がさらに道を持たなければ、その道の札(label)を載せる
    nl = ctx.wrap(elname(nxt) if nxt in outs else lab(last['id'], 'label', strip_gloss(last.get('label', '')) or elname(nxt)), FS, 140 if nxt in outs else 200, True, nxt)
    node = {'kind': 'node', 'lines': nl, 'w': max(120, maxw(nl, FS, True) + 36), 'h': max(56, len(nl) * LH + 26), 'id': nxt,
            'col': ctx.color(elname(nxt)), 'r': last}
    cols.append(node)
    arms = outs.get(nxt, [])
    if len(arms) > 2:
        ctx.diag('unrendered', f'{nxt} から出る道が3つ以上あり、描けない(上と下の2つまで)', 'error', nxt)
        arms = arms[:2]
    # start を指定したときは、start から届く道だけを描く(場面のほかの道は対象外)
    for k in outs:
        if k not in (start, nxt) and not b.get('start'):
            ctx.diag('unrendered', f'{k} から出る道は描けない(始まりと、その最後の行き先からの道だけを描く)', 'error', k)
    # 腕: 最後の道は下、それ以外は右(条件の札を行き先の上に置き、札を通って行き先へ進む)
    arm_up = arms[:-1] if len(arms) == 2 else []
    arm_down = arms[-1:] if arms else []

    def arm_box(r):
        dl = ctx.wrap(lab(r['id'], 'label', strip_gloss(r.get('label', ''))), FS, 200, True, r['id'] + '.label')
        cl = ctx.wrap(lab(r['id'], 'condition', r.get('condition', '')), FS, 160, False, r['id'] + '.condition')
        return {'r': r, 'dest': dl, 'dw': max(120, maxw(dl, FS, True) + 36), 'dh': max(56, len(dl) * LH + 26),
                'cond': cl, 'cw': maxw(cl, FS) + 28, 'ch': len(cl) * LH + (40 if r['id'] in proposals else 16),
                'dcol': ctx.color(elname(r['to']))}
    ups = [arm_box(r) for r in arm_up]
    downs = [arm_box(r) for r in arm_down]

    # 横の位置
    # 主の列の幅で並べ、下の行き先どうしが重なるときだけ右へずらす
    x = 0
    prev_right = -1e9
    for i, c in enumerate(cols):
        dw = c.get('dw', 0) if c['kind'] == 'dec' else max([0] + [a['dw'] for a in downs]) if c['kind'] == 'node' else 0
        cx = x + c['w'] / 2
        if dw:
            cx = max(cx, dw / 2, prev_right + 16 + dw / 2)
            prev_right = cx + dw / 2
        c['cx'] = cx
        g = 0
        if i < len(cols) - 1:   # 「いいえ」が、両側のひし形の角の上の空きに収まる間隔にする
            free = lambda d: d['w'] / 2 * 14 / d['h'] * 2 if d['kind'] == 'dec' else 0
            g = max(G, tw('いいえ', FS) + 12 - free(c) - free(cols[i + 1])) if c['kind'] == 'dec' else G
        x = cx + c['w'] / 2 + g
    x = max(x, prev_right)
    for a in ups:
        rw = max(a['cw'], a['dw'])
        a['cx'] = x + 24 + rw / 2
        x += 24 + rw
    total_w = x
    # 縦の位置
    up_h = max([a['ch'] + 28 + a['dh'] / 2 - node['h'] / 2 for a in ups] or [0])
    hl_room = 40 if hl_ids & {c['r']['id'] for c in cols if c['kind'] == 'dec'} else 0
    maxh = max(c['h'] for c in cols)
    yc = max(up_h + node['h'] / 2, hl_room + maxh / 2 + 6) + 4
    sv = Svg(ctx)
    if total_w > CW:
        ctx.diag('overflow', f'流れ図の幅 {total_w:.0f}px が {CW}px を越える(分かれ目が多すぎるか、文字が長い)', 'error', 'flowchart')
    ydest = yc + maxh / 2 + 54
    dec_ids = []

    def dest(cx, y, lines, w, h, col, name, proposal=False):
        col = col or INK
        rid = sv.rect(cx - w / 2, y, w, h, fill='#fff', stroke=col, sw=3, rx=min(h / 2, 28), name=name)
        sv.lines(cx, y + h / 2, lines, FS, col, True, inside=rid)
        return rid

    for i, c in enumerate(cols):
        cx = c['cx']
        if c['kind'] == 'start':
            scol = ctx.color(elname(c['id'])) if dk.el.get(c['id'], {}).get('kind') == 'action' else None
            if scol:   # 始まりが行き先(閉じる、調べる、上げる)なら、行き先の札の形と色で描く
                rid = sv.rect(cx - c['w'] / 2, yc - c['h'] / 2, c['w'], c['h'], fill='#fff', stroke=scol, sw=3, rx=min(c['h'] / 2, 28), name=c['id'])
                sv.lines(cx, yc, c['lines'], FS, scol, True, inside=rid)
            else:
                rid = sv.rect(cx - c['w'] / 2, yc - c['h'] / 2, c['w'], c['h'], name=c['id'])
                sv.lines(cx, yc, c['lines'], FS, inside=rid)
        elif c['kind'] == 'dec':
            r = c['r']
            prop = r['id'] in proposals
            em = r['id'] in hl_ids and len(hl_ids) == 1
            did = sv.diamond(cx, yc, c['w'], c['h'], name=r['id'], stroke=INK if em else (dk.colors.get('案の印') if prop else '#6B7280'),
                             sw=5 if em else 2, dash='8 6' if prop else None)
            sv.lines(cx, yc, c['lines'], FS, inside=did)
            dec_ids.append((r['id'], cx, c))
            sv.line([(cx, yc + c['h'] / 2), (cx, ydest - 4)])
            sv.text(cx + 10, (yc + c['h'] / 2 + ydest) / 2 + 8, 'はい', FS, color=TEXT2)
            dest(cx, ydest, c['dest'], c['dw'], c['dh'], c['dcol'], r['to'] + ':' + r['id'])
        else:
            em = c['id'] in hl_ids
            col = c['col'] or INK
            rid = sv.rect(cx - c['w'] / 2, yc - c['h'] / 2, c['w'], c['h'], fill='#fff', stroke=INK if em else col, sw=5 if em else 3,
                          rx=min(c['h'] / 2, 28), name=c['id'])
            sv.lines(cx, yc, c['lines'], FS, col, True, inside=rid)
            for a in ups:      # 右の腕: 行き先を主の列の高さに置き、その上に条件の札(案なら破線)を置く
                r = a['r']
                ax = a['cx']
                prop = r['id'] in proposals
                by = yc - a['dh'] / 2 - 28 - a['ch']
                pc = dk.colors.get('案の印', '#7C3AED') if prop else None
                cid = sv.rect(ax - a['cw'] / 2, by, a['cw'], a['ch'], fill='#fff', stroke=pc or '#fff', sw=2 if prop else 0, rx=8,
                              dash='8 6' if prop else None, name=r['id'] + '.condition')
                yy = by + 10
                if prop:
                    ctx.colors_used.add(pc)
                    sv.text(ax - a['cw'] / 2 + 10, by + 24, '案の基準', NOTE, color=pc, bold=True, role='note', inside=cid)
                    yy = by + 34
                for l in a['cond']:
                    sv.text(ax, yy + FS * 0.9, l, FS, 'middle', inside=cid)
                    yy += LH
                xr = cx + c['w'] / 2
                sv.line([(xr, yc), (xr + 10, yc), (xr + 10, by + a['ch'] / 2), (ax - a['cw'] / 2 - 2, by + a['ch'] / 2)])
                sv.line([(ax, by + a['ch']), (ax, yc - a['dh'] / 2 - 2)])
                dest(ax, yc - a['dh'] / 2, a['dest'], a['dw'], a['dh'], a['dcol'], r['to'] + ':' + r['id'])
            for a in downs:
                r = a['r']
                sv.line([(cx, yc + c['h'] / 2), (cx, ydest - 4)])
                ly = (yc + c['h'] / 2 + ydest) / 2
                for k, l in enumerate(a['cond']):
                    sv.text(cx + 10, ly + 8 + (k - (len(a['cond']) - 1) / 2) * LH, l, FS, color=TEXT2)
                dest(cx, ydest, a['dest'], a['dw'], a['dh'], a['dcol'], r['to'] + ':' + r['id'])
        if i < len(cols) - 1:
            nx = cols[i + 1]
            x1 = cx + c['w'] / 2
            x2 = nx['cx'] - nx['w'] / 2 - 4
            sv.line([(x1, yc), (x2, yc)])
            if cols[i]['kind'] == 'dec':
                sv.text((x1 + x2) / 2, yc - 20, 'いいえ', FS, 'middle', TEXT2)
    # 複数の分かれ目の強調: まとめて1つの枠で囲む
    group = [(cx, c) for rid_, cx, c in dec_ids if rid_ in hl_ids]
    if len(hl_ids) > 1 and group:
        x0 = min(cx - c['w'] / 2 for cx, c in group) - 14
        x1 = max(cx + c['w'] / 2 for cx, c in group) + 14
        hh = max(c['h'] for _, c in group) + 26
        sv.raw(f'<rect x="{x0:.1f}" y="{yc - hh / 2:.1f}" width="{x1 - x0:.1f}" height="{hh:.1f}" rx="14" fill="none" stroke="{INK}" stroke-width="5"/>')
        if hl_label:
            sv.text((x0 + x1) / 2, yc - hh / 2 - 10, hl_label, FS, 'middle', INK, True)
        if len(group) != len(hl_ids):
            ctx.diag('unrendered', 'highlight の ids に、分かれ目でないものがある', 'error', 'highlight')
    check_height(ctx, sv.h + 4)
    return sv.svg(CW)


# ---------------------------------------------------------------- 構成図、要素の関係(graphviz で配置)

FLOW_KINDS = {'send', 'produce', 'notify', 'aggregate', 'route', 'retrieve'}


def dot_layout(nodes, edges, clusters, rankdir='LR', nodesep=40, ranksep=50, same=()):
    """nodes: {id: (w, h)}、edges: [(id, tail, head, label_lines, attrs)]、clusters: {cid: (label_h, [node ids], [child cids])}
    返すもの: node 中心、edge の制御点とラベル位置、cluster の枠(左上原点、px)。"""
    q = lambda s: '"' + str(s).replace('"', '\\"') + '"'
    out = [f'digraph G {{ rankdir={rankdir}; compound=true; nodesep={nodesep / 72:.3f}; ranksep={ranksep / 72:.3f}; '
           'node [shape=box fixedsize=true label=""]; edge [arrowhead=none fontname="IPAPGothic" fontsize=22];']
    done = set()

    def emit_cluster(cid):
        lh, ns, subs = clusters[cid]
        s = [f'subgraph {q("cluster_" + cid)} {{ label={q(chr(92).join(['']) + (chr(92) + 'n').join(lh))}; labelloc=t; fontname="IPAPGothic"; fontsize=22; margin=16;']
        for sub in subs:
            s.append(emit_cluster(sub))
        for n in ns:
            w, h = nodes[n]
            s.append(f'{q(n)} [width={w / 72:.3f} height={h / 72:.3f}];')
            done.add(n)
        s.append('}')
        return '\n'.join(s)
    tops = [c for c in clusters if not any(c in v[2] for v in clusters.values())]
    for c in tops:
        out.append(emit_cluster(c))
    for n, (w, h) in nodes.items():
        if n not in done:
            out.append(f'{q(n)} [width={w / 72:.3f} height={h / 72:.3f}];')
    for a_, b_ in same:
        out.append(f'{{ rank=same; {q(a_)}; {q(b_)}; }}')
    for eid, t, hd, lab, attrs in edges:
        a = [f'id={q(eid)}']
        if lab:
            a.append('label=' + q('\\n'.join(lab)))
        for k, v in attrs.items():
            a.append(f'{k}={q(v)}')
        out.append(f'{q(t)} -> {q(hd)} [{" ".join(a)}];')
    out.append('}')
    src = '\n'.join(out)
    try:
        res = subprocess.run(['dot', '-Tjson'], input=src, capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        sys.exit('描けない: graphviz(dot)がない。apt-get install graphviz')
    if res.returncode != 0:
        raise RuntimeError(res.stderr)
    g = json.loads(res.stdout)
    bb = [float(v) for v in g['bb'].split(',')]
    gh = bb[3]
    P = lambda x, y: (float(x), gh - float(y))
    pos, cl, ed = {}, {}, {}
    for o in g.get('objects', []):
        if 'nodes' in o and o.get('name', '').startswith('cluster_'):
            x0, y0, x1, y1 = [float(v) for v in o['bb'].split(',')]
            cl[o['name'][8:]] = (x0, gh - y1, x1 - x0, y1 - y0)
        elif 'pos' in o:
            x, y = o['pos'].split(',')
            pos[o['name']] = P(x, y)
    for e in g.get('edges', []):
        pts = []
        for tok in e.get('pos', '').split():
            if tok.startswith(('e,', 's,')):
                continue
            x, y = tok.split(',')
            pts.append(P(x, y))
        lp = None
        if e.get('lp'):
            x, y = e['lp'].split(',')
            lp = P(x, y)
        ed[e.get('id')] = (pts, lp)
    return pos, ed, cl, (bb[2], bb[3])


def graph_figure(ctx, kind):
    """er-diagram と architecture-diagram の共通の描画。仕組みの定義の要素とつながりを引き、graphviz で置く。"""
    b, dk = ctx.body, ctx.deck
    labels = b.get('labels') or {}
    els = list(b.get('elements') or [])
    rels = list(b.get('relations') or [])
    for e in els:
        if e not in dk.el:
            ctx.diag('unrendered', f'要素 {e} が仕組みの定義にない', 'error', e)
    els = [e for e in els if e in dk.el]
    R = []
    for r in rels:
        rr = dk.rel.get(r)
        if rr is None:
            ctx.diag('unrendered', f'つながり {r} が仕組みの定義にない', 'error', r)
            continue
        for end in (rr['from'], rr['to']):
            if end not in els:
                ctx.diag('unrendered', f'つながり {r} の端 {end} が elements にない', 'error', r)
        if rr['from'] in els and rr['to'] in els:
            R.append(rr)
    proof = dk.proof.get(ctx.sid) or {}
    view = proof.get('view') or {}
    if proof.get('real') and view:
        for e in els:
            if e not in (view.get('elements') or []):
                ctx.diag('unrendered', f'要素 {e} が立証設計の view にない', 'error', e)
        for r in R:
            if r['id'] not in (view.get('relations') or []):
                ctx.diag('unrendered', f'つながり {r["id"]} が立証設計の view にない', 'error', r['id'])
    hl = b.get('highlight')
    annotations = b.get('annotations') or {}
    details = b.get('details') or {}
    groups = b.get('groups') or [] if kind == 'architecture' else []
    hg = parse_index(hl, 'groups')
    if hl and hg is None and hl not in els and hl not in [r['id'] for r in R]:
        ctx.diag('unrendered', f'highlight「{hl}」に当たる要素、つながり、groups[番号] がない', 'error', 'highlight')
    FS = FIG
    LH = FS * 1.25
    # 入れ子(contain): 構成図では、含む側を枠にする
    parent = {}
    if kind == 'architecture':
        for r in R:
            if r['kind'] == 'contain':
                parent[r['to']] = r['from']
    containers = set(parent.values())
    connected = {r['from'] for r in R} | {r['to'] for r in R}
    isolated = [e for e in els if e not in connected and e not in containers]
    # 部品の大きさ
    info = {}
    for e in els:
        nm = dk.name(e, labels)
        bold = e == hl
        lines = ctx.wrap(nm, FS, 176, bold, e)
        det = [l for x in details.get(e, []) for l in ctx.wrap(ctx.text(x), NOTE, 150, False, e + '.details')]
        w = max(150, maxw(lines, FS, bold) + 48)
        h = max(64, len(lines) * LH + 34)
        if det:
            w = max(w, maxw(det, NOTE) + 40)
            h = len(lines) * LH + 26 + len(det) * NOTE * 1.45 + 14
        ann = ctx.wrap(ctx.text(annotations[e]), FS, 460, False, e + '.annotation') if e in annotations else []
        info[e] = {'name': nm, 'lines': lines, 'det': det, 'w': w, 'h': h, 'ann': ann,
                   'aw': maxw(ann, FS), 'ah': len(ann) * LH + (10 if ann else 0), 'iso': e in isolated}
    # つながりの描き方: 流れは矢印(retrieve は取りに行く側へデータが来る向き)。そのほかは矢印のない線
    edges = []
    for r in R:
        if r['kind'] == 'contain' and kind == 'architecture':
            continue
        t, hd = (r['to'], r['from']) if r['kind'] == 'retrieve' else (r['from'], r['to'])
        lt = labels.get(r['id'], strip_gloss(r.get('label', '')))
        ll = ctx.wrap(ctx.text(lt), FS, 180, False, r['id']) if lt else []
        edges.append({'r': r, 't': t, 'h': hd, 'lab': ll, 'arrow': r['kind'] in FLOW_KINDS})
    # 配置の単位: groups が互いにつながらなければ、group ごとに置いて横に並べる
    gsets = [list(g.get('elements') or []) for g in groups]
    for gi, g in enumerate(gsets):
        for e in g:
            if e not in els:
                ctx.diag('unrendered', f'groups[{gi}] の {e} が elements にない', 'error', f'groups[{gi}]')
    gsets = [[e for e in g if e in els] for g in gsets]
    ingroup = {e: gi for gi, g in enumerate(gsets) for e in g}
    cross = any(ingroup.get(x['t']) != ingroup.get(x['h']) for x in edges)
    if cross and groups:
        ctx.diag('unrendered', 'groups をまたぐつながりがある。groups ごとの横並びにせず、1つの図として置いた', 'warning', 'groups')
    units = []
    if groups and not cross:
        for gi, g in enumerate(gsets):
            units.append((gi, [e for e in g if not info[e]['iso']]))
        rest = [e for e in els if e not in ingroup and not info[e]['iso']]
        if rest:
            units.append((None, rest))
    else:
        units.append((None, [e for e in els if not info[e]['iso']]))
    sv = Svg(ctx)
    x_off = 0
    top_title = 40 if groups else 0
    ids = {}
    for gi, members in units:
        if not members:
            continue
        mset = set(members)
        nodes, clusters = {}, {}
        same, eds = [], []
        for e in members:
            if e in containers:
                continue
            i = info[e]
            nodes[e] = (i['w'], i['h'])
            if i['ann']:   # 注記は、部品のすぐ下に置く別の点として配置する
                nodes['ann_' + e] = (i['aw'] + 8, i['ah'])
                same.append((e, 'ann_' + e))
                eds.append(('inv_' + e, e, 'ann_' + e, [], {'style': 'invis'}))
        for c in containers & mset:
            kids = [e for e in members if parent.get(e) == c and e not in containers]
            subs = [e for e in members if parent.get(e) == c and e in containers]
            clusters[c] = (info[c]['lines'], kids, subs)
        for x in edges:
            if x['t'] in mset and x['h'] in mset:
                attrs = {}
                t, hd = x['t'], x['h']
                if t in containers:
                    attrs['ltail'] = 'cluster_' + t
                    t = next((k for k in members if parent.get(k) == t), t)
                if hd in containers:
                    attrs['lhead'] = 'cluster_' + hd
                    hd = next((k for k in members if parent.get(k) == hd), hd)
                eds.append((x['r']['id'], t, hd, x['lab'], attrs))
        dirn = (groups[gi].get('direction') if gi is not None else None) or b.get('direction') or 'LR'
        if dirn not in ('LR', 'TB'):
            ctx.diag('unrendered', f'direction「{dirn}」は LR か TB で書く', 'error', 'direction')
            dirn = 'LR'
        pos, epos, cpos, (gw, gh) = dot_layout(nodes, eds, clusters, rankdir=dirn, same=same if dirn == 'LR' else ())
        ox, oy = x_off, top_title
        title = groups[gi].get('title') if gi is not None else None
        if title:
            sv.text(ox, 26, ctx.text(title), 24, bold=True, role='figure')
        # 枠(入れ子)
        for c, (cx0, cy0, cw_, ch_) in sorted(cpos.items(), key=lambda kv: -kv[1][2] * kv[1][3]):
            em = c == hl
            anc = []
            p = parent.get(c)
            while p:
                anc.append(ids.get(p, ''))
                p = parent.get(p)
            ids[c] = sv.rect(ox + cx0, oy + cy0, cw_, ch_, fill=PART if not parent.get(c) else '#fff', stroke=INK if em else GRAY_LINE,
                             sw=5 if em else 2, name=c, anc=[a for a in anc if a])
            sv.lines(ox + cx0 + cw_ / 2, oy + cy0 + 10 + len(info[c]['lines']) * LH / 2, info[c]['lines'], FS, INK, em, inside=ids[c])
        for e, (px, py) in pos.items():
            if e.startswith('ann_'):    # 注記の場所は配置で空けてあり、文字は部品のすぐ下から書く
                i = info[e[4:]]
                bx, by_ = pos[e[4:]]
                for k, l in enumerate(i['ann']):
                    sv.text(ox + bx - i['w'] / 2, oy + by_ + i['h'] / 2 + 8 + FS + k * LH, l, FS, color=TEXT2)
                continue
            if e not in info:
                continue
            i = info[e]
            w, h = i['w'], i['h']
            x0, y0 = ox + px - w / 2, oy + py - h / 2
            em = e == hl
            anc = []
            p = parent.get(e)
            while p:
                anc.append(ids.get(p, ''))
                p = parent.get(p)
            fill = '#fff' if parent.get(e) else PART
            ids[e] = sv.rect(x0, y0, w, h, fill=fill, stroke=INK if em else GRAY_LINE, sw=5 if em else 2, name=e, anc=[a for a in anc if a])
            sv.lines(x0 + w / 2, y0 + h / 2, i['lines'], 26 if em and len(i['lines']) == 1 else FS, INK, em, inside=ids[e])
        for x in edges:
            if x['r']['id'] not in epos or not (x['t'] in mset and x['h'] in mset):
                continue
            pts, lp = epos[x['r']['id']]
            pts = [(ox + a, oy + c) for a, c in pts]
            if len(pts) >= 4:
                d = f'M{pts[0][0]:.1f},{pts[0][1]:.1f} ' + ' '.join(
                    f'C{pts[k][0]:.1f},{pts[k][1]:.1f} {pts[k + 1][0]:.1f},{pts[k + 1][1]:.1f} {pts[k + 2][0]:.1f},{pts[k + 2][1]:.1f}'
                    for k in range(1, len(pts) - 2, 3))
                em = x['r']['id'] == hl
                sv.path(d, arrow=x['arrow'], w=(5 if em else 3) if x['arrow'] else 2)
            if lp and x['lab']:
                lx, ly = ox + lp[0], oy + lp[1]
                if dirn == 'TB':
                    lx += 8
                for k, l in enumerate(x['lab']):
                    sv.text(lx, ly + FS * 0.35 + (k - (len(x['lab']) - 1) / 2) * LH, l, FS, 'middle', TEXT2, x['r']['id'] == hl)
        # 群の強調の枠と、群の説明
        gx1 = ox + gw
        if gi is not None and hg == gi:
            sv.raw(f'<rect x="{ox - 2:.1f}" y="{oy - 6:.1f}" width="{gw + 10:.1f}" height="{gh + 12:.1f}" rx="14" fill="none" stroke="{INK}" stroke-width="5"/>')
            gx1 += 8
        if gi is not None and groups[gi].get('caption'):
            cl_ = ctx.wrap(ctx.text(groups[gi]['caption']), BODY, max(gw, 300), False, f'groups[{gi}].caption')
            for k, l in enumerate(cl_):
                sv.text(ox, oy + gh + 34 + k * BODY * 1.3, l, BODY, color=TEXT2, role='body')
            gx1 = max(gx1, ox + maxw(cl_, BODY))
        content_right = gx1
        if title:
            gx1 = max(gx1, ox + tw(title, 24, True))
        x_off = gx1 + 40
    if hg is not None and hg >= len(groups):
        ctx.diag('unrendered', f'highlight groups[{hg}] に当たる群がない', 'error', 'highlight')
    # つながりのない要素: 右に離して置き、「経路は出典にない」と添える(style.yaml の arrows: 線なし)
    if isolated:
        if units:
            x_off = content_right + 40   # 群の題の下は空いているため、題の右端でなく中身の右端から置く
        iy = top_title + 8
        for e in isolated:
            i = info[e]
            w = max(i['w'], tw('経路は出典にない', NOTE) + 28)
            h = i['h'] + NOTE * 1.4 + 14
            rid = sv.rect(x_off, iy, w, h, fill='#F9FAFB', stroke=GRAY_LINE, sw=2, rx=8, dash='4 4', name=e)
            yy = iy + 10
            for l in i['lines']:
                sv.text(x_off + 12, yy + NOTE + 4, l, NOTE + 2 if not i['det'] else NOTE, bold=True, role='note', inside=rid)
                yy += LH
            for d in i['det']:
                sv.text(x_off + 20, yy + NOTE + 6, d, NOTE, role='note', inside=rid)
                yy += NOTE * 1.45
            sv.text(x_off + 12, iy + h - 12, '経路は出典にない', NOTE, color='#4B5563', role='note', inside=rid)
            iy += h + 20
    check_width(ctx, sv.w)
    check_height(ctx, sv.h + 4)
    return sv.svg(CW)


def r_er(ctx):
    return graph_figure(ctx, 'er')


def r_arch(ctx):
    return graph_figure(ctx, 'architecture')


RENDERERS = {
    'statement': r_statement, 'plain-list': r_plain_list, 'step-flow': r_step_flow, 'cause-chain': r_cause_chain,
    'pie-chart': r_pie_chart, 'table': r_table, 'tree': r_tree, 'flowchart': r_flowchart,
    'er-diagram': r_er, 'architecture-diagram': r_arch,
}
FIGURE_TYPES = set(RENDERERS) - {'statement'}


# ---------------------------------------------------------------- ページ

CSS = f"""
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:{W}px;height:{H}px;background:#fff;font-family:{FONT_FAMILY};color:{INK};position:relative;overflow:hidden}}
.top{{position:absolute;left:{MX}px;top:26px;width:{CW}px}}
.h{{font-size:32px;font-weight:bold;line-height:1.3}}
.src{{font-size:22px;color:{TEXT2};line-height:1.35;margin-top:6px}}
.fig{{margin-top:22px}}
.after{{margin-top:20px;font-size:{BODY}px;color:{TEXT2};line-height:1.45}}
.tk{{position:absolute;left:0;bottom:0;width:{W}px;height:{H - BAND_TOP}px;background:#F3F4F6;font-size:26px;padding:20px {MX}px;border-top:2px solid #D1D5DB;white-space:nowrap;overflow:hidden}}
.tag{{display:inline-block;font-size:19px;padding:2px 10px;border-radius:12px;color:#fff;margin-right:8px;vertical-align:middle}}
.ph{{border:2px dashed #9CA3AF;padding:18px 22px;font-size:24px;line-height:1.5;color:#4B5563}}
.ph b{{color:#111827}}
.center{{position:absolute;left:{MX}px;width:{CW}px}}
"""


def page(title_html, body_html, takeaway=None, mins=None):
    tk = f'<div class="tk fit" data-role="takeaway" data-name="takeaway">{E(takeaway)}</div>' if takeaway else ''
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>'
            f'<div class="top">{title_html}{body_html}</div>{tk}</body></html>')


def head_html(headline, source):
    s = f'<div class="h" data-role="headline">{E(headline)}</div>'
    if source:
        s += f'<div class="src" data-role="source">出典: {E(source)}</div>'
    return s


def top_height(headline, source, mark):
    hl = len(wrap(headline, 32, CW, True)[0])
    sl = len(wrap('出典: ' + source, 22, CW)[0]) if source else 0
    return 26 + hl * 32 * 1.3 + (6 + sl * 22 * 1.35 if source else 0) + 22 + (34 if mark else 0)


def render_content(deck, sid):
    """本編と付録のスライド1枚。仕様がなければ、立証設計から仮置きを描く。"""
    s = deck.S[sid]
    spec = deck.specs.get(sid)
    ctx = Ctx(deck, sid, spec)
    src = s.get('source') or ''
    if spec is None:
        p = deck.proof.get(sid) or {}
        pat = deck.pattern_of.get((p.get('relation'), p.get('base', 'none')))
        ctx.diag('placeholder', 'スライド仕様がない。仮置きを描いた', 'info')
        bits = []
        if pat or p.get('relation'):
            bits.append(f'<b>型</b>: {E(str(pat or "未定"))}(主張の種類 {E(str(p.get("relation")))})')
        if p.get('show'):
            bits.append(f'<b>見せるもの</b>: {E(p["show"])}')
        if p.get('focus'):
            bits.append(f'<b>注目させる点</b>: {E(p["focus"])}')
        body = f'<div class="fig"><div class="ph fit" data-role="body" data-name="仮置き" style="max-height:{BAND_TOP - 16 - top_height(s["headline"], src, None):.0f}px">{"<br>".join(bits) or "(立証設計がない)"}</div></div>'
        return page(head_html(s['headline'], src), body), ctx
    b = spec.get('body') or {}
    t = b.get('type')
    if spec.get('headline') != s.get('headline'):
        ctx.diag('unrendered', 'スライド仕様の headline がストーリーラインと違う。ストーリーラインの見出しで描いた', 'warning', 'headline')
    if spec.get('status') == 'blocked':
        ctx.diag('placeholder', f'保留のスライド({spec.get("issue") or "Issue の番号なし"})', 'info')
    p = deck.proof.get(sid) or {}
    want = deck.pattern_of.get((p.get('relation'), p.get('base', 'none')))
    if want and t != want:
        ctx.diag('unrendered', f'body.type {t} が表現の対応表の型 {want} と違う', 'warning', 'body.type')
    if not spec.get('takeaway') and s.get('chapter') != 'appendix':
        ctx.diag('unrendered', '結論1行(takeaway)がない', 'error', 'takeaway')
    mark = b.get('mark') if t != 'plain-list' else None
    text_after = spec.get('text')
    after_h = 0
    if text_after:
        after_h = 20 + len(wrap(ctx.text(text_after), BODY, CW)[0]) * BODY * 1.45
    ctx.avail_h = BAND_TOP - 16 - top_height(s['headline'], src, mark) - after_h
    fn = RENDERERS.get(t)
    if fn is None:
        ctx.diag('unrendered', f'型 {t} の描画がない(描ける型: {", ".join(sorted(RENDERERS))})', 'error', 'body.type')
        fig = f'<div class="ph" data-role="body">型 {E(str(t))} は描けない</div>'
    else:
        try:
            fig = fn(ctx)
        except Exception as e:    # 描画の失敗も診断として出し、ほかのスライドは続ける
            ctx.diag('unrendered', f'描画に失敗した: {type(e).__name__}: {e}', 'error', 'body')
            fig = f'<div class="ph" data-role="body">描画に失敗した</div>'
    if t in FIGURE_TYPES and not b.get('highlight'):
        ctx.diag('unrendered', '強調する要素(highlight)の指定がない', 'warning', 'highlight')
    pre = tag(mark, ctx) if mark else ''
    after = f'<div class="after" data-role="body">{E(ctx.text(text_after))}</div>' if text_after else ''
    if deck.max_hues:
        hues = {c for c in ctx.colors_used if not is_gray(c)}
        if len(hues) > deck.max_hues:
            ctx.diag('hue-count', f'1枚で使う色相が {len(hues)} で、上限 {deck.max_hues} を越える', 'error')
    for c in ctx.colors_used:
        if contrast(c, '#ffffff') < 3.0 and c in [v for k, v in deck.colors.items() if k in ('閉じる', '調べる', '上げる', '誤検知', '案の印')]:
            ctx.diag('contrast', f'色 {c} の文字と白地の色の差が小さい({contrast(c, "#ffffff"):.1f})', 'warning')
    return page(head_html(s['headline'], src), f'<div class="fig">{pre}{fig}</div>{after}', spec.get('takeaway'), deck.min), ctx


def is_gray(c):
    r, g, b = (int(c[i:i + 2], 16) for i in (1, 3, 5))
    return max(r, g, b) - min(r, g, b) < 40


def contrast(a, b):
    def lum(c):
        v = [int(c[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        v = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in v]
        return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]
    la, lb = sorted([lum(a), lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


# ---------------------------------------------------------------- 導出と半導出のスライド

def chapter_questions(deck, ch):
    """章で答える問い: 章構成の cover_question(D013)があればそれ。なければ章の主張の question、
    主張のない章は章のスライドの from の問い"""
    cq = ch.get('cover_question')
    if cq:
        return [(None, q) for q in (cq if isinstance(cq, list) else [cq])]
    qs = [deck.claims[c]['question'] for c in ch.get('claims') or [] if c in deck.claims and deck.claims[c].get('question')]
    if not qs:
        for s in deck.storyline:
            if s.get('chapter') == ch['id']:
                for q in s.get('from') or []:
                    if q not in qs:
                        qs.append(q)
    return [(q, deck.plan[q]['question']) for q in qs if q in deck.plan]


def simple_page(kicker, title, lines_html, ctx_id):
    ctx = Ctx(None, ctx_id, None)
    body = (f'<div class="center" style="top:150px"><div data-role="body" style="font-size:26px;color:{TEXT2}">{E(kicker)}</div>'
            f'<div class="fit" data-role="headline" data-name="title" style="font-size:44px;font-weight:bold;line-height:1.3;margin-top:10px;max-height:120px">{E(title)}</div>'
            f'{lines_html}</div>')
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{body}</body></html>'), ctx


def render_toc(deck):
    rows = ''
    for i, ch in enumerate(deck.chapters, 1):
        rows += f'<li style="margin:8px 0"><span style="display:inline-block;width:110px;color:{TEXT2}">第{i}章</span>{E(ch.get("title", ""))}</li>'
    if any(s.get('chapter') == 'appendix' for s in deck.storyline):
        rows += f'<li style="margin:8px 0"><span style="display:inline-block;width:110px;color:{TEXT2}">付録</span></li>'
    rows += f'<li style="margin:8px 0"><span style="display:inline-block;width:110px;color:{TEXT2}">出典</span>出典の一覧</li>'
    html_ = (f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>'
             f'<div class="top"><div class="h" data-role="headline">目次</div>'
             f'<ul class="fit" data-role="body" data-name="目次" style="list-style:none;font-size:28px;margin-top:40px;line-height:1.5;max-height:{BAND_TOP - 140}px">{rows}</ul></div></body></html>')
    return html_, Ctx(deck, 'toc', None)


def render_cover(deck, i, ch):
    qs = chapter_questions(deck, ch)
    ctx = Ctx(deck, f'{ch["id"]}-cover', None)
    if not qs:
        ctx.diag('unrendered', f'章 {ch["id"]} で答える問いが上流の成果物にない(主張も、スライドの from もない)。章の題だけを載せた', 'warning')
    ql = ''.join(f'<li data-role="body" style="margin-top:12px">{E(t)}</li>' for _, t in qs)
    lines = (f'<div data-role="body" style="margin-top:56px;font-size:24px;color:{TEXT2}">この章で答える問い</div>'
             f'<ul class="fit" data-name="問い" style="list-style:none;font-size:30px;line-height:1.45;max-height:300px;border-left:6px solid #D1D5DB;padding-left:22px;margin-top:8px">{ql}</ul>') if qs else ''
    h, _ = simple_page(f'第{i}章', ch.get('title', ''), lines, ctx.sid)
    return h, ctx


def render_summary(deck, i, ch):
    ctx = Ctx(deck, f'{ch["id"]}-summary', None)
    lines = (f'<div class="fit" data-role="body" data-name="章の主張" style="margin-top:48px;font-size:32px;line-height:1.55;max-height:330px">{E(ch.get("message", ""))}</div>')
    h, _ = simple_page(f'第{i}章のまとめ', ch.get('title', ''), lines, ctx.sid)
    return h, ctx


def render_appendix_cover():
    h, ctx = simple_page('付録', '付録', '', 'appendix-cover')
    return h, ctx


def source_entries(deck, order):
    used = {}
    for sid in order:
        spec = deck.specs.get(sid)
        fids = (spec or {}).get('sources') or deck.S.get(sid, {}).get('evidence') or []
        for fid in fids:
            f = deck.facts.get(fid)
            if not f:
                continue
            key = strip_gloss(str(f.get('source') or '')) or '(出典の記録なし)'
            used.setdefault(key, [])
            if sid not in used[key]:
                used[key].append(sid)
    return list(used.items())


def render_sources(deck, order):
    """出典の一覧。1枚に収まらない分は、続きの1枚に送る(導出のスライドのため、枚数は中身で決まる)"""
    entries = source_entries(deck, order)
    pages, cur, h = [], [], 0
    limit = BAND_TOP - 26 - 42 - 30
    FS = 22   # 出典の行と同じ下限(16pt)を当てる
    for name, sids in entries:
        t = f'{name}(使ったスライド: {", ".join(sids)})'
        eh = len(wrap(t, FS, CW - 20)[0]) * FS * 1.4 + 6
        if cur and h + eh > limit:
            pages.append(cur)
            cur, h = [], 0
        cur.append(t)
        h += eh
    if cur:
        pages.append(cur)
    out = []
    for k, items in enumerate(pages, 1):
        sid = f'sources-{k}'
        li = ''.join(f'<li style="margin-bottom:6px">{E(t)}</li>' for t in items)
        ttl = '出典の一覧' + (f'({k}/{len(pages)})' if len(pages) > 1 else '')
        html_ = (f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>'
                 f'<div class="top"><div class="h" data-role="headline">{ttl}</div>'
                 f'<ul class="fit" data-role="source" data-name="出典" style="list-style:none;font-size:{FS}px;line-height:1.4;margin-top:20px;max-height:{limit + 4}px">{li}</ul></div></body></html>')
        out.append((sid, html_, Ctx(deck, sid, None)))
    return out


# ---------------------------------------------------------------- 全体

def deck_order(deck):
    """(ID, 区分, 描く関数) の一覧。章の順、章の中はストーリーラインの順。付録は最後"""
    seq = [('toc', '目次', lambda: render_toc(deck))]
    for i, ch in enumerate(deck.chapters, 1):
        sl = [s['id'] for s in deck.storyline if s.get('chapter') == ch['id']]
        seq.append((f'{ch["id"]}-cover', '章扉', lambda i=i, ch=ch: render_cover(deck, i, ch)))
        for sid in sl:
            seq.append((sid, '本編', lambda sid=sid: render_content(deck, sid)))
        # 章のまとめ: 章構成の枚数に、扉と中身のほかに1枚の余地があるときだけ置く(例外 D010 の ch1 は余地がない)
        if (ch.get('slides') or 0) >= len(sl) + 2:
            seq.append((f'{ch["id"]}-summary', '章のまとめ', lambda i=i, ch=ch: render_summary(deck, i, ch)))
    app = [s['id'] for s in deck.storyline if s.get('chapter') == 'appendix']
    if app:
        seq.append(('appendix-cover', '付録の扉', render_appendix_cover))
        for sid in app:
            seq.append((sid, '付録', lambda sid=sid: render_content(deck, sid)))
    known = {c['id'] for c in deck.chapters} | {'appendix'}
    for s in deck.storyline:
        if s.get('chapter') not in known:
            seq.append((s['id'], '本編', lambda sid=s['id']: render_content(deck, sid)))
    return seq


def main():
    ap = argparse.ArgumentParser(description='スライド仕様からスライドを描く')
    ap.add_argument('deck')
    ap.add_argument('--only', nargs='*', help='このIDのスライドだけを描く(deck.html は全体で作り直す)')
    ap.add_argument('--no-png', action='store_true', help='PNG を撮らない(診断は取る)')
    a = ap.parse_args()
    root = Path(a.deck).resolve()
    deck = Deck(root)
    out = root / 'build'
    sd = out / 'slides'
    sd.mkdir(parents=True, exist_ok=True)
    seq = deck_order(deck)
    content_ids = [sid for sid, kind, _ in seq if kind in ('本編', '付録')]
    for sid in deck.specs:
        if sid not in deck.S:
            print(f'警告: スライド仕様 {sid}({deck.spec_file[sid]})がストーリーラインにない。描かない', file=sys.stderr)
    rendered = []   # (id, kind, ctx)
    slides = []
    for sid, kind, fn in seq:
        h, ctx = fn()
        slides.append((sid, kind))
        if a.only and sid not in a.only:
            continue
        (sd / f'{sid}.html').write_text(h, encoding='utf-8')
        rendered.append((sid, kind, ctx))
    for sid, h, ctx in render_sources(deck, content_ids):
        slides.append((sid, '出典の一覧'))
        if a.only and sid not in a.only:
            continue
        (sd / f'{sid}.html').write_text(h, encoding='utf-8')
        rendered.append((sid, '出典の一覧', ctx))
    # ブラウザで診断を取り、PNG を撮る
    jobs = [{'id': sid, 'html': str(sd / f'{sid}.html'), 'png': None if a.no_png else str(sd / f'{sid}.png'), 'min': deck.min}
            for sid, _, _ in rendered]
    jf, rf = out / '.jobs.json', out / '.results.json'
    jf.write_text(json.dumps(jobs, ensure_ascii=False), encoding='utf-8')
    res = subprocess.run(['node', str(HERE / 'render_shot.js'), str(jf), str(rf)], capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit('描けない: ブラウザでの描画に失敗した\n' + res.stderr[-2000:])
    browser = json.loads(rf.read_text(encoding='utf-8'))
    jf.unlink()
    rf.unlink()
    # 診断をまとめる
    old = {}
    dpath = out / 'diagnostics.json'
    if a.only and dpath.is_file():
        old = {d['id']: d for d in json.loads(dpath.read_text(encoding='utf-8')).get('slides', [])}
    per = dict(old)
    for sid, kind, ctx in rendered:
        ds = list(ctx.diags)
        for d in browser.get(sid, []):
            ds.append({'slide': sid, **d})
        per[sid] = {'id': sid, 'kind': kind, 'spec': deck.spec_file.get(sid), 'type': ((deck.specs.get(sid) or {}).get('body') or {}).get('type'),
                    'diagnostics': ds, 'wraps': ctx.wraps}
    ordered = [per[sid] for sid, _ in slides if sid in per]
    allds = [d for s in ordered for d in s['diagnostics']]
    summary = {k: sum(1 for d in allds if d['severity'] == k) for k in ('error', 'warning', 'info')}
    dpath.write_text(json.dumps({'summary': summary, 'slides': ordered}, ensure_ascii=False, indent=1), encoding='utf-8')
    # deck.html
    secs = ''
    for k, (sid, kind) in enumerate(slides, 1):
        spec = deck.specs.get(sid) or {}
        notes = f'<div class="notes">ノート: {E(str(spec["notes"]))}</div>' if spec.get('notes') else ''
        nd = len([d for d in per.get(sid, {}).get('diagnostics', []) if d['severity'] == 'error'])
        badge = f' <span class="bad">診断 {nd}件</span>' if nd else ''
        secs += (f'<section id="{E(sid)}"><div class="cap">{k}. {E(sid)}({E(kind)}){badge}</div>'
                 f'<iframe src="slides/{E(sid)}.html" width="{W}" height="{H}" loading="lazy"></iframe>{notes}</section>')
    (out / 'deck.html').write_text(
        '<!doctype html><html><head><meta charset="utf-8"><title>deck</title><style>'
        f'body{{background:#e5e7eb;font-family:{FONT_FAMILY};margin:20px}}section{{margin:0 auto 28px;width:{W}px}}'
        'iframe{border:1px solid #9ca3af;background:#fff;display:block}.cap{font-size:14px;color:#374151;margin:4px 0}'
        '.bad{color:#b91c1c;font-weight:bold}.notes{font-size:14px;color:#374151;margin-top:4px;white-space:pre-wrap}'
        f'</style></head><body>{secs}</body></html>', encoding='utf-8')
    # 標準出力
    print(f'描いた: {len(rendered)} 枚(全体 {len(slides)} 枚) → {out}')
    for s in ordered:
        for d in s['diagnostics']:
            if d['severity'] == 'info' and s['kind'] not in ('本編', '付録'):
                continue
            tgt = f' [{d["target"]}]' if d.get('target') else ''
            print(f'{d["severity"]:7s} {s["id"]:14s} {d["kind"]:16s}{tgt} {d["message"]}')
    ph = sum(1 for d in allds if d['kind'] == 'placeholder')
    print(f'診断: エラー {summary["error"]}、警告 {summary["warning"]}、情報 {summary["info"]}(うち仮置き {ph} 枚)')
    return 1 if summary['error'] else 0


if __name__ == '__main__':
    sys.exit(main())
