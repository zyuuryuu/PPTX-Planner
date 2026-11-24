#!/usr/bin/env python3
"""スライド仕様(YAML)からスライドを描く。確認用の資料(目次と章扉、骨組み、仮置き)も、同じ枠で描く。

使い方:
  python3 tools/render.py <資料のディレクトリ> [--pdf] [--only ID ...] [--chapter 章のID] [--no-png] [--out 出力先]
  python3 tools/render.py <資料のディレクトリ> --samples      型の見本(06-samples/)だけを描く
  python3 tools/render.py <資料のディレクトリ> --level toc|skeleton|placeholder   確認用の資料(tools/build.py と同じ)
  python3 tools/render.py --patterns                          描ける型の一覧を出す

読むもの: 00-brief.md と definitions/deck-type.yaml(資料の型。限定と出どころの置き場)、style.yaml(要点の位置、上限、色、文字の下限)、
03-chapters.yaml(章、節、題、問い、要点)、04-storyline.yaml(題、要点、役割、限定、出どころ、順序)、01-sources.yaml(事実の値、出典)、
01-model.yaml(仕組みの定義)、05-proof.yaml(仮置き)、06-patterns.yaml、definitions/patterns.yaml(型の定義)、
06-samples/*.yaml と 07-slides/*.yaml(スライド仕様。同じIDなら 07-slides が優先)。

出すもの(既定は <資料のディレクトリ>/build/): slides/<番号>-<ID>.html と .png、deck.html(1つのファイルで全スライド)、
deck.pdf(--pdf)、diagnostics.json(描画上の診断。tools/check.py が読む)。
文字を下限より小さくしない。収まらない内容は、スライドを分けずに診断として報告する。
型ごとの書式と収容量は tools/patterns-data.md に書く。
"""
import argparse
import base64
import hashlib
import html
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check as C   # noqa: E402  資料の型、型の定義、語彙は、check.py と同じ読み方で正本から読む


def E(s):
    return html.escape(str(s))


W, H = 1280, 720
MX = 48                 # 左右の余白
CW = W - 2 * MX         # 中身の幅 1184
TOP, BOTTOM = 28, 16    # 上下の余白
TITLE_FS, TITLE_LH = 36, 1.25      # 題
POINT_FS, POINT_LH = 27, 1.4       # 要点(題の直下、中身の下)
POINT_BODY_FS = 34                 # 要点(中身そのもの)
KICKER_FS = 20                     # 題の行の右端の小さな札(章のまとめ、節のまとめ)
FOOT_FS, FOOT_LH = 19, 1.4         # 脚注(限定、出どころ、出典)とページ番号
FOOT_MIN = 60                      # 脚注の領域の高さの下限(2行分)。要点と中身の位置を、脚注の有無で動かさない
GAP_MAIN = 20                      # 題と要点の下から、中身までの間
GAP_BELOW = 12                     # 中身から、中身の下の要点までの間
INK = '#111827'
GRAY_LINE = '#9CA3AF'
TEXT2 = '#374151'
TEXT3 = '#4B5563'
PART = '#E5E7EB'
EM_FILL = '#374151'                               # 強調する面(色の割り当てがない対象)
GRAYS = ['#D1D5DB', '#9CA3AF', '#F3F4F6', '#6B7280']   # 強調しない面(色の割り当てがない対象)
FONT_FAMILY = "'IPAPGothic','IPAGothic',sans-serif"
MAX_HUES_DEFAULT = 4
TEXT_CONTRAST_MIN, TEXT_CONTRAST_MIN_LARGE = 4.5, 3.0   # 文字と背景の色の差の下限(コントラスト比)
ADJACENT_CONTRAST_MIN = 1.3                             # 隣り合う面の色の差の下限(コントラスト比)
FONT_MIN_DEFAULT = {'title': '24pt', 'point': '18pt', 'body': '18pt', 'figure_text': '16pt', 'note': '14pt', 'footnote': '14pt'}
LEVELS = {'toc': '目次と章扉', 'skeleton': '骨組み', 'placeholder': '仮置き', 'full': '全スライド', 'samples': '型の見本'}
INPUT_FILES = ['00-brief.md', 'style.yaml', 'terms.yaml', '01-sources.yaml', '01-model.yaml', '03-chapters.yaml',
               '04-storyline.yaml', '05-proof.yaml', '06-patterns.yaml']
INPUT_DIRS = ['definitions', '06-samples', '07-slides']

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
        from PIL import ImageFont
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
            kata = lambda ch: '\u30a0' <= ch <= '\u30ff'
            if kata(cur[-1]) and kata(t[0]):    # カタカナの語の途中では切らず、語の前で切る
                k = len(cur)
                while k > 0 and kata(cur[k - 1]):
                    k -= 1
                if k > 0 and tw(cur[k:] + t, size, bold) <= maxw:
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


def inputs_hash(root):
    """描画が読む成果物の要約値。tools/check.py が、診断が今の成果物のものかを確かめるのに使う(同じ計算を check.py も持つ)。"""
    root = Path(root)
    files = [root / n for n in INPUT_FILES]
    for d in INPUT_DIRS:
        files += sorted((root / d).glob('*.yaml')) if (root / d).is_dir() else []
    h = hashlib.sha1()
    for f in files:
        if f.is_file():
            h.update(f.relative_to(root).as_posix().encode('utf-8') + b'\0' + f.read_bytes() + b'\0')
    return h.hexdigest()


def pattern_names():
    """型の識別子 → 日本語の名前(docs/patterns.md の表)"""
    out = {}
    for r in C.md_table('patterns.md', '付属する型の候補'):
        ids = C.ticks(r.get('識別子', ''))
        if ids:
            out[ids[0]] = r.get('型', ids[0])
    return out


def role_names():
    """要点のないスライドの役割の識別子 → 日本語の名前(docs/vocabulary.md の表)"""
    return {t: r.get('役割', t) for r in C.md_table('vocabulary.md', '要点のないスライド') for t in C.ticks(r.get('識別子', ''))}


PROVENANCE = {   # 出どころの値 → (印の文字, 意味)。意味は docs/stages/04-storyline.md と docs/deck-types.md による
    'cited': ('出典', '出典のある事実'),
    'proposal': ('案', '案'),
    'practice': ('運用', '今の運用'),
}
NEEDS = {
    'toc': ['03-chapters.yaml'],
    'skeleton': ['03-chapters.yaml', '04-storyline.yaml', '01-sources.yaml'],
    'placeholder': ['03-chapters.yaml', '04-storyline.yaml', '01-sources.yaml', '05-proof.yaml'],
    'full': ['03-chapters.yaml', '04-storyline.yaml', '01-sources.yaml'],
    'samples': ['01-sources.yaml'],
}


class Deck:
    def __init__(self, root, level='full'):
        self.root = root
        self.level = level
        for n in NEEDS[level]:
            if not (root / n).is_file():
                sys.exit(f'描けない: {root / n} がない({LEVELS[level]}の資料に要る)')
        ld = lambda n: load_yaml(root / n, required=False)
        self.c = C.Deck(root)
        st = ld('style.yaml') or {}
        self.style = st
        common = st.get('common') or {}
        fm = dict(FONT_MIN_DEFAULT)
        fm.update(common.get('font_min') or {})
        self.min = {
            'title': pt2px(fm['title']), 'point': pt2px(fm['point']), 'body': pt2px(fm['body']),
            'figure': pt2px(fm['figure_text']), 'note': pt2px(fm['note']), 'footnote': pt2px(fm['footnote']),
        }
        self.colors = common.get('colors') or {}
        self.max_hues = common.get('max_hues_per_slide') or MAX_HUES_DEFAULT
        self.point_position = st.get('point_position') if isinstance(st.get('point_position'), dict) else {}
        lim = st.get('limits') if isinstance(st.get('limits'), dict) else {}
        self.summary_min = lim.get('section_summary_min_slides') if isinstance(lim.get('section_summary_min_slides'), int) else None
        # 限定と出どころの置き場(資料の型の定義の annotation)
        dt = self.c.deck_type or {}
        ann = dt.get('annotation') if isinstance(dt.get('annotation'), dict) else None
        self.annotation_known = ann is not None
        ann = ann or {}
        self.ann_q = ann.get('qualifiers') if ann.get('qualifiers') in ('footnote', 'notes') else 'footnote'
        self.ann_p = ann.get('provenance') if ann.get('provenance') in ('footnote', 'notes', 'mark', 'none') else 'none'
        self.pattern_defs = self.c.pattern_defs
        self.pattern_names = pattern_names()
        self.role_names = role_names()
        self.chapters_doc = ld('03-chapters.yaml') or {}
        self.chapters = [c for c in self.chapters_doc.get('chapters') or [] if isinstance(c, dict) and c.get('id')]
        self.sections = {s['id']: (ch, s) for ch in self.chapters for s in ch.get('sections') or [] if isinstance(s, dict) and s.get('id')}
        self.storyline = [s for s in ld('04-storyline.yaml') or [] if isinstance(s, dict) and s.get('id')]
        self.S = {s['id']: s for s in self.storyline}
        self.facts = {f['id']: f for f in ld('01-sources.yaml') or [] if isinstance(f, dict) and 'id' in f}
        model = ld('01-model.yaml') or {}
        self.el = {e['id']: e for e in model.get('elements') or []}
        self.rel = {r['id']: r for r in model.get('relations') or []}
        self.scn = {s['id']: s for s in model.get('scenarios') or []}
        terms = ld('terms.yaml') or {}
        self.model_labels = terms.get('model_labels') or {}
        proof = ld('05-proof.yaml') or []
        self.proof = {p.get('id'): p for p in proof if isinstance(p, dict)}
        self.table = [p for p in ld('06-patterns.yaml') or [] if isinstance(p, dict)]
        # スライド仕様: 見本 → 章ごと(後のものが優先)。ファイルは、スライド仕様の並び、または1枚
        self.specs, self.spec_file, self.sample_ids = {}, {}, []
        for sub, sample in (('06-samples', True), ('07-slides', False)):
            if level in ('toc', 'skeleton', 'placeholder') or (level == 'samples' and not sample):
                continue
            for f in sorted((root / sub).glob('*.yaml')) if (root / sub).is_dir() else []:
                d = load_yaml(f)
                for spec in d if isinstance(d, list) else [d]:
                    if isinstance(spec, dict) and spec.get('id'):
                        self.specs[spec['id']] = spec
                        self.spec_file[spec['id']] = f.relative_to(root).as_posix()
                        if sample and spec['id'] not in self.sample_ids:
                            self.sample_ids.append(spec['id'])
        self.all_ids = self.c.all_ids() | set(self.specs)
        self.page_of = {}     # スライドのID → ページ番号(描く順が決まった後に入る)

    # -- 仕組みの定義と色

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

    # -- 章、節、スライド

    def section_point(self, sec_id):
        """節の要点と限定。節が1つだけの章の節は、章の要点を引く(point_from: chapter)"""
        ch, sec = self.sections.get(sec_id, (None, None))
        if sec is None:
            return None, []
        if sec.get('point_from') == 'chapter' or (not sec.get('point') and len(ch.get('sections') or []) == 1):
            return ch.get('point'), list(ch.get('qualifiers') or [])
        return sec.get('point'), list(sec.get('qualifiers') or [])

    def section_slides(self, sec_id):
        return [s for s in self.storyline if s.get('section') == sec_id and s.get('chapter') != 'appendix']

    def needs_section_summary(self, sec_id):
        """節のまとめを置くか(docs/vocabulary.md の表: 項の数が境目の枚数以上)"""
        return self.summary_min is not None and len(self.section_slides(sec_id)) >= self.summary_min

    def view(self, sid):
        """スライドの題、要点、役割、限定、出どころ。ストーリーラインを正とし、ない場合(見本だけの場合)はスライド仕様から取る"""
        s = self.S.get(sid) or self.specs.get(sid) or {}
        v = {'title': s.get('title'), 'role': s.get('role'), 'qualifiers': list(s.get('qualifiers') or []),
             'provenance': s.get('provenance'), 'point': None, 'point_kind': None, 'chapter': s.get('chapter'), 'section': s.get('section')}
        if isinstance(s.get('point'), str) and s['point'].strip():
            v['point'], v['point_kind'] = s['point'], 'own'
        elif s.get('point_from') == 'section':
            sec = s.get('section') or (self.S.get(sid) or {}).get('section')
            p, q = self.section_point(sec)
            v['point'], v['point_kind'] = p, 'section'
            v['qualifiers'] = v['qualifiers'] + [x for x in q if x not in v['qualifiers']]
        return v

    def pattern_for(self, sid):
        """立証の設計と表現の対応表から決まる型。量の区分で分かれる場合は決めない"""
        p = self.proof.get(sid) or {}
        rows = [t for t in self.table if t.get('relation') == p.get('relation') and (t.get('base') or 'none') == (p.get('base') or 'none')]
        pats = {t.get('pattern') for t in rows}
        return pats.pop() if len(pats) == 1 else None

    def position(self, ptype):
        """型の要点の位置。資料の表現規約 → 規約の default → 型の定義の既定 → 題の直下"""
        pp = self.point_position
        v = pp.get(ptype) or pp.get('default') or (self.pattern_defs.get(ptype) or {}).get('point_position') or 'below-title'
        return v if v in ('below-title', 'below-body', 'body') else 'below-title'

    def source_names(self, fids, seen=None):
        """事実の出典の名前。導出した事実(derived)は、式(formula)の中の事実の出典をたどる"""
        seen = seen if seen is not None else set()
        out = []
        for fid in fids:
            f = self.facts.get(fid)
            if not f or fid in seen:
                continue
            seen.add(fid)
            names = [strip_gloss(str(f['source']))] if f.get('source') else self.source_names(re.findall(r'\b[FA]\d+\b', str(f.get('formula') or '')), seen)
            out += [n for n in names if n and n not in out]
        return out


# ---------------------------------------------------------------- 1枚の文脈

def merged_body(spec):
    """型のデータ。body.data が項目の集まりなら、body の直下の項目に重ねる(body.data を優先)。並びなら、data のまま渡す"""
    body = dict((spec or {}).get('body') or {})
    data = body.get('data')
    if isinstance(data, dict):
        body.pop('data')
        body.update(data)
    return body


def count_highlight(body):
    """強調の指定の数。数え方は docs/visual-grammar.md の「E: 注目」(highlight の指定を数える)"""
    n = 0
    if isinstance(body, dict):
        for k, v in body.items():
            if k == 'highlight' and v not in (None, [], ''):
                n += len(v) if isinstance(v, list) else 1
            else:
                n += count_highlight(v)
    elif isinstance(body, list):
        n += sum(count_highlight(v) for v in body)
    return n


class Ctx:
    def __init__(self, deck, sid, spec):
        self.deck, self.sid, self.spec = deck, sid, spec or {}
        self.body = merged_body(spec)
        self.diags = []
        self.wraps = []
        self.colors_used = set()
        self.adjacent = []        # 隣り合う面の色の組
        self.ems = set()          # 強調を付けた要素
        self.avail_h = 400
        self.center = True        # 中身を、領域の中央に置くか
        self.point_in_body = None # 要点を中身として描く位置のときの、要点の文
        self.mode, self.type, self.notes, self.point = None, None, '', None

    def diag(self, kind, message, severity='error', target=None):
        self.diags.append({'slide': self.sid, 'kind': kind, 'severity': severity, 'target': target, 'message': message})

    def em(self, key):
        self.ems.add(str(key))

    def wrap(self, text, size, width, bold=False, what=None):
        lines, broke = wrap(text, size, width, bold)
        if len(lines) > 1:
            self.wraps.append({'target': what or str(text)[:20], 'lines': lines})
        if broke:
            self.diag('word-break', f'語の途中で改行した: 「{text}」', 'warning', what)
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

    def fills(self, labels, hl, distinct=True):
        """面の色。色の割り当てがあればその色。なければ灰色で、強調する面だけを濃くする。
        distinct: 面を凡例で見分ける型(円グラフ)では、灰色の段階を面ごとに変える。段階の数を超えたら、描き分けられないと診断に出す"""
        out, k = [], 0
        for lab in labels:
            c = self.color(lab)
            if not c:
                if lab == hl:
                    c = EM_FILL
                else:
                    c = GRAYS[k % len(GRAYS)] if distinct else GRAYS[0]
                    k += 1
            out.append(c)
        if distinct and k > len(GRAYS):
            self.diag('unrendered', f'色の割り当てのない面が {k} あり、灰色の段階({len(GRAYS)}つ)で描き分けられない', 'error', 'data')
        return out

    def fact(self, fid, target):
        f = self.deck.facts.get(fid)
        if f is None:
            self.diag('unrendered', f'事実 {fid} が素材台帳にない', 'error', target)
        elif self.spec and fid not in (self.spec.get('sources') or []):
            self.diag('reference', f'事実 {fid} が、このスライドの sources にない', 'warning', target)
        return f

    def text(self, s, target='text'):
        """{F001}(値と単位)、{F001:value}、{F001:unit}、{F001:metric} を素材台帳の値に、{ch2-s1} をそのスライドの題に置き換える"""
        def rep(m):
            ref, field = m.group(1), m.group(2) or ''
            if ref in self.deck.S or (ref in self.deck.specs and not re.fullmatch(r'[FA]\d+', ref)):
                title = (self.deck.S.get(ref) or self.deck.specs.get(ref) or {}).get('title')
                if not title:
                    self.diag('unrendered', f'参照したスライド {ref} に題がない', 'error', target)
                    return '(題のないスライド)'
                return str(title)
            if not re.fullmatch(r'F\d+', ref):
                self.diag('unrendered', f'参照 {{{ref}}} の先が、事実にもスライドにもない', 'error', target)
                return '(参照先なし)'
            f = self.fact(ref, target)
            if f is None:
                return '(参照先なし)'
            if field == 'value' or field == '':
                if f.get('value') is None:
                    self.diag('unrendered', f'事実 {ref} に value がない', 'error', target)
                    return '(値なし)'
                v = fmt_num(f['value'])
                return v if field == 'value' else v + fmt_unit(f.get('unit'))
            if field == 'unit':
                return str(f.get('unit') or '')
            if field == 'metric':
                return self.term(f.get('metric'))
            self.diag('unrendered', f'参照の書式 {{{ref}:{field}}} が分からない', 'error', target)
            return '(参照先なし)'
        return re.sub(r'\{([A-Za-z][\w.-]*)(?::(\w+))?\}', rep, str(s))

    def term(self, tid):
        """語彙表のIDを、語に置き換える"""
        for t in (self.deck.c.terms or []):
            if t.get('id') == tid:
                return str(t.get('term') or '')
        return '' if tid is None else str(tid)

    def value(self, v, target):
        """数値の参照: F207(事実の value)、または {fact: F207, as: 27, round: 0}。as の数は事実の本文にあること"""
        if isinstance(v, str) and re.fullmatch(r'F\d+', v):
            f = self.fact(v, target)
            if f is None or isinstance(f.get('value'), bool) or not isinstance(f.get('value'), (int, float)):
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


# ---------------------------------------------------------------- 型ごとの描画
# どの関数も、中身の HTML を返す。要点、題、限定、出どころは描かない(枠が描く)。
# 収まらないときは診断を出し、文字は縮めない。強調を付けたら ctx.em() で知らせる。

FIG = 22      # 図の中の文字(16pt の下限 21.3px の上)
NOTE = 19     # 図の注記(14pt の下限 18.7px の上)
BODY = 24     # 本文(18pt の下限 24px)
EMB = f'5px solid {INK}'   # 強調の枠


def check_height(ctx, h, what='図'):
    if h > ctx.avail_h + 0.5:
        ctx.diag('overflow', f'{what}の高さ {h:.0f}px が、使える高さ {ctx.avail_h:.0f}px を越える', 'error', what)


def check_width(ctx, w, what='図', limit=CW):
    if w > limit + 0.5:
        ctx.diag('overflow', f'{what}の幅 {w:.0f}px が、使える幅 {limit:.0f}px を越える', 'error', what)


def r_statement(ctx):
    """言い切り。要点の位置が「中身そのもの」なら、要点の文を中身として大きく描く(枠は、要点を別の行に描かない)。
    value があれば、値を大きく示し、text を値の説明として添える。"""
    b = ctx.body
    hl = b.get('highlight')
    point = ctx.point_in_body          # 要点の文(位置が body のとき)。なければ None
    out = ''
    allowed = {None, 'point', 'text', 'caveat'} | ({'value'} if b.get('value') is not None else set())
    if hl not in allowed:
        ctx.diag('unrendered', f'highlight「{hl}」は {"、".join(sorted(x for x in allowed if x))} で書く', 'error', 'highlight')
    if b.get('value') is not None:     # 値を大きく示す
        v, vl, unit = ctx.value(b['value'], 'value')
        big = f'{vl}{fmt_unit(unit)}{b.get("bound", "")}' if v is not None else '(値なし)'
        em = f'border:{EMB};padding:10px 28px;' if hl == 'value' else 'padding:10px 0;'
        if hl == 'value':
            ctx.em('value')
        lab = f'<div data-role="body" style="font-size:26px;margin-top:4px;color:{TEXT2}">{E(ctx.text(b["text"], "data.text"))}</div>' if b.get('text') else ''
        out += (f'<div style="display:inline-block;{em}"><div data-role="body" style="font-size:96px;font-weight:bold;line-height:1.1">{E(big)}</div>{lab}</div>')
    elif b.get('quote_of'):            # 引用
        f = ctx.fact(b['quote_of'], 'quote_of')
        q = b.get('text') or (f or {}).get('quote')
        if not q:
            ctx.diag('unrendered', '引用する文(text、または事実の quote)がない', 'error', 'quote_of')
        attr = f'<div data-role="figure" style="font-size:{FIG}px;color:{TEXT3};margin-top:10px">{E(ctx.text(b["attribution"]))}</div>' if b.get('attribution') else ''
        em = f'border:{EMB};' if hl == 'text' else ''
        if hl == 'text':
            ctx.em('text')
        out += (f'<div data-role="body" style="{em}border-left:8px solid {GRAY_LINE};padding:16px 26px;font-size:28px;line-height:1.6">'
                f'「{E(ctx.text(q or ""))}」{attr}</div>')
    elif b.get('text') and not point:  # 要点を中身に描かないスライドでは、text を言い切る文として描く
        em = f'border:{EMB};padding:12px 22px;' if hl == 'text' else ''
        if hl == 'text':
            ctx.em('text')
        out += f'<div data-role="body" style="{em}font-size:{POINT_BODY_FS}px;font-weight:bold;line-height:1.45;display:inline-block">{E(ctx.text(b["text"], "data.text"))}</div>'
    elif b.get('text') and point:
        ctx.diag('unrendered', 'data.text を描かなかった。要点を中身として描くスライドでは、text は value の説明にだけ使う', 'error', 'data.text')
    if point:
        em = f'border:{EMB};padding:10px 22px;' if hl == 'point' else ''
        if hl == 'point':
            ctx.em('point')
        mt = 'margin-top:26px;' if out else ''
        out += (f'<div class="point pt-body" data-role="point" style="{mt}{em}font-size:{POINT_BODY_FS}px;font-weight:bold;line-height:1.45">{E(point)}</div>')
    elif not out:
        ctx.diag('unrendered', 'statement に描く中身がない(要点も、value も、text もない)', 'error', 'body')
    if b.get('caveat'):
        if hl == 'caveat':
            ctx.em('caveat')
            out += f'<div><div data-role="body" style="margin-top:24px;display:inline-block;border:{EMB};padding:10px 22px;font-size:{BODY}px;font-weight:bold">{E(ctx.text(b["caveat"]))}</div></div>'
        else:
            out += f'<div data-role="body" style="margin-top:22px;font-size:{BODY}px;color:{TEXT2}">{E(ctx.text(b["caveat"]))}</div>'
    ctx.center = True
    return f'<div style="width:{CW}px">{out}</div>'


def r_plain_list(ctx):
    """箇条書き。枠なしの縦の並び"""
    b = ctx.body
    items = b.get('items') or []
    if not items:
        ctx.diag('unrendered', 'plain-list に items がない', 'error', 'items')
    hl = b.get('highlight')
    hi = parse_index(hl, 'items')
    out = ''
    if b.get('title'):
        st = f'border:{EMB};padding:4px 14px;font-weight:bold' if hl == 'title' else 'font-weight:bold;padding:4px 0'
        if hl == 'title':
            ctx.em('title')
        out += f'<span data-role="body" style="display:inline-block;{st};font-size:26px;vertical-align:middle">{E(ctx.text(b["title"]))}</span>'
    elif hl == 'title':
        ctx.diag('unrendered', 'highlight が title だが title がない', 'error', 'highlight')
    if hl and hl != 'title' and hi is None:
        ctx.diag('unrendered', f'highlight「{hl}」は title か items[番号] で書く', 'error', 'highlight')
    lis = ''
    for i, it in enumerate(items):
        t = it.get('text') if isinstance(it, dict) else it
        sub = it.get('sub') if isinstance(it, dict) else None
        st = f'border:{EMB};padding:0 10px;font-weight:bold;display:inline-block' if hi == i else ''
        if hi == i:
            ctx.em(f'items[{i}]')
        s = f'<li style="padding-left:1.1em;text-indent:-1.1em"><span style="{st}">・{E(ctx.text(t, f"items[{i}]"))}</span>'
        if sub:
            s += (f'<ul style="list-style:none;padding-left:40px;text-indent:0;font-size:{BODY}px;line-height:1.5;color:{TEXT2}">'
                  + ''.join(f'<li>{E(ctx.text(x))}</li>' for x in sub) + '</ul>')
        lis += s + '</li>'
    if hi is not None and hi >= len(items):
        ctx.diag('unrendered', f'highlight {hl} に当たる項目がない', 'error', 'highlight')
    mt = 'margin-top:14px;' if b.get('title') else ''
    out += f'<ul data-role="body" style="{mt}list-style:none;font-size:28px;line-height:1.7">{lis}</ul>'
    ctx.center = False
    return f'<div style="width:{CW}px">{out}</div>'


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
    if hi is not None:
        ctx.em(f'steps[{hi}]')
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
    if hi is not None:
        ctx.em(f'chain[{hi}]')
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


def _rows(ctx, data):
    """数量の型のデータ: {label, value, bound} の並び → (label, 値, 値の表記, 単位, bound)"""
    rows = []
    for i, d in enumerate(data):
        if not isinstance(d, dict):
            ctx.diag('unrendered', f'data[{i}] が {{label, value}} の形でない', 'error', f'data[{i}]')
            continue
        v, label, unit = ctx.value(d.get('value'), f'data[{i}]')
        rows.append((ctx.text(d.get('label', ''), f'data[{i}].label'), v, label, unit, str(d.get('bound', '') or '')))
    return rows


def r_pie_chart(ctx):
    b = ctx.body
    data = b.get('data') or []
    if not isinstance(data, list) or not data:
        ctx.diag('unrendered', 'pie-chart に data(項目の並び)がない', 'error', 'data')
        return ''
    hl = b.get('highlight')
    rows = _rows(ctx, data)
    vals = [r[1] or 0 for r in rows]
    total = sum(vals)
    if rows and all(r[3] == '%' for r in rows) and not (99.5 <= total <= 100.5):
        ctx.diag('data', f'構成比の合計が {total:g}% で、100% にならない', 'error', 'data')
    labels = [r[0] for r in rows]
    if hl and hl not in labels:
        ctx.diag('unrendered', f'highlight「{hl}」に当たる label がない', 'error', 'highlight')
    elif hl:
        ctx.em(hl)
    cols = ctx.fills(labels, hl)
    n = len(rows)
    ctx.adjacent += [(cols[i], cols[(i + 1) % n]) for i in range(n if n > 2 else n - 1)]
    LFS, PITCH = 26, 62
    leg_h = n * PITCH
    r = max(120, min(180, (ctx.avail_h - 16) / 2))
    sv = Svg(ctx)
    cx, cy = r + 6, max(r + 6, leg_h / 2)
    ang = -90.0
    for i, (lab, v, *_rest) in enumerate(rows):
        if not v or total <= 0:
            continue
        sweep = v / total * 360
        a1, a2 = math.radians(ang), math.radians(ang + sweep)
        x1, y1, x2, y2 = cx + r * math.cos(a1), cy + r * math.sin(a1), cx + r * math.cos(a2), cy + r * math.sin(a2)
        large = 1 if sweep > 180 else 0
        if sweep >= 359.9:
            sv.raw(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{cols[i]}"/>')
        else:
            sv.raw(f'<path d="M{cx:.1f},{cy:.1f} L{x1:.1f},{y1:.1f} A{r:.1f},{r:.1f} 0 {large} 1 {x2:.1f},{y2:.1f} z" fill="{cols[i]}" stroke="#fff" stroke-width="2"/>')
        ang += sweep
    sv.raw(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="none" stroke="{GRAY_LINE}" stroke-width="1.5"/>')
    ang = -90.0
    for i, (lab, v, *_rest) in enumerate(rows):   # 強調する面は、太い線で囲む
        sweep = (v or 0) / total * 360 if total > 0 else 0
        if lab == hl and 0 < sweep < 359.9:
            a1, a2 = math.radians(ang), math.radians(ang + sweep)
            x1, y1, x2, y2 = cx + r * math.cos(a1), cy + r * math.sin(a1), cx + r * math.cos(a2), cy + r * math.sin(a2)
            sv.raw(f'<path d="M{cx:.1f},{cy:.1f} L{x1:.1f},{y1:.1f} A{r:.1f},{r:.1f} 0 {1 if sweep > 180 else 0} 1 {x2:.1f},{y2:.1f} z" fill="none" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>')
        ang += sweep
    sv.ext(cx + r + 6, cy + r + 6)
    lx = 2 * r + 76
    ly0 = cy - leg_h / 2
    for i, (lab, v, vl, unit, bound) in enumerate(rows):
        em = lab == hl
        y = ly0 + i * PITCH + (PITCH - 34) / 2
        thin = v is not None and total > 0 and v / total * 360 < 1.5
        t = f'{lab} {vl}{fmt_unit(unit)}{bound}' + ('(細すぎて円に出ない)' if thin else '')
        sv.raw(f'<rect x="{lx}" y="{y:.1f}" width="34" height="34" fill="{cols[i]}" stroke="{INK if em else GRAY_LINE}" stroke-width="{3 if em else 1}"/>')
        sv.text(lx + 48, y + 27, t, LFS, bold=em, name=f'data[{i}]')
        if lx + 48 + tw(t, LFS, em) > CW:
            ctx.diag('overflow', f'凡例「{t}」が右端を越える', 'error', f'data[{i}]')
    h = max(2 * r + 12, leg_h)
    check_height(ctx, h)
    return sv.svg(None, h)


def r_bar_chart(ctx):
    """棒グラフ。横の棒を上から並べる。量の軸は0から始める"""
    b = ctx.body
    data = b.get('data') or []
    if not isinstance(data, list) or not data:
        ctx.diag('unrendered', 'bar-chart に data(項目の並び)がない', 'error', 'data')
        return ''
    hl = b.get('highlight')
    rows = [r for r in _rows(ctx, data)]
    labels = [r[0] for r in rows]
    if hl and hl not in labels:
        ctx.diag('unrendered', f'highlight「{hl}」に当たる label がない', 'error', 'highlight')
    elif hl:
        ctx.em(hl)
    if len({r[3] for r in rows if r[1] is not None}) > 1:
        ctx.diag('data', '単位の違う値を、1つの軸に並べている: ' + '、'.join(sorted({r[3] or '(単位なし)' for r in rows})), 'error', 'data')
    if any(r[1] is not None and r[1] < 0 for r in rows):
        ctx.diag('unrendered', '負の値は描けない', 'error', 'data')
    cols = ctx.fills(labels, hl, distinct=False)
    ctx.adjacent += [(cols[i], cols[i + 1]) for i in range(len(cols) - 1) if cols[i] != cols[i + 1]]
    LFS, BH, PITCH, LMAX = 26, 44, 72, 340
    lab_lines = [ctx.wrap(lab, LFS, LMAX, lab == hl, f'data[{i}].label') for i, lab in enumerate(labels)]
    lw = max(maxw(l, LFS, True) for l in lab_lines)
    vtexts = [f'{vl}{fmt_unit(unit)}{bound}' if v is not None else '(値なし)' for _, v, vl, unit, bound in rows]
    vw = max(tw(t, LFS, True) for t in vtexts) + 14
    x0 = lw + 18
    bmax = min(760, CW - x0 - vw)
    top = 8
    vmax = max([r[1] or 0 for r in rows] + [0])
    sv = Svg(ctx)
    for i, (lab, v, *_rest) in enumerate(rows):
        em = lab == hl
        y = top + i * PITCH + (PITCH - BH) / 2
        w = max(2, (v or 0) / vmax * bmax) if vmax > 0 else 2
        if len(lab_lines[i]) > 2:
            ctx.diag('overflow', f'項目の名前「{lab}」が2行に収まらない', 'error', f'data[{i}].label')
        sv.lines(0, y + BH / 2, lab_lines[i], LFS, INK, em, anchor='end', x=lw)
        sv.rect(x0, y, w, BH, fill=cols[i], stroke=INK if em and cols[i] != EM_FILL else 'none', sw=5 if em and cols[i] != EM_FILL else 0, rx=0, name=f'data[{i}]')
        sv.text(x0 + w + 12, y + BH / 2 + LFS * 0.35, vtexts[i], LFS, bold=em, name=f'data[{i}].value')
    h = top + len(rows) * PITCH + 8
    sv.line([(x0, top), (x0, h - 4)], arrow=False, w=2, color=TEXT2)   # 量の軸(0)
    check_width(ctx, sv.w)
    check_height(ctx, h)
    return sv.svg(None, h)


def r_before_after(ctx):
    """前後の対比。前を左、後を右に置き、矢印でつなぐ"""
    b = ctx.body
    hl = b.get('highlight')
    if hl not in (None, 'before', 'after'):
        ctx.diag('unrendered', f'highlight「{hl}」は before か after で書く', 'error', 'highlight')
    elif hl:
        ctx.em(hl)
    BW, GAP, LFS, VFS, TFS = 430, 150, 24, 72, 28
    sides = []
    for key in ('before', 'after'):
        d = b.get(key)
        if not isinstance(d, dict):
            ctx.diag('unrendered', f'before-after に {key} がない', 'error', key)
            d = {}
        lab = ctx.wrap(ctx.text(d.get('label', ''), f'{key}.label'), LFS, BW - 48, False, f'{key}.label')
        if d.get('value') is not None:
            v, vl, unit = ctx.value(d['value'], f'{key}.value')
            big = f'{vl}{fmt_unit(unit)}{d.get("bound", "") or ""}' if v is not None else '(値なし)'
            if tw(big, VFS, True) > BW - 40:
                ctx.diag('overflow', f'{key} の値「{big}」が枠の幅に収まらない', 'error', f'{key}.value')
            body, bh, fs = [big], VFS * 1.15, VFS
        else:
            body = ctx.wrap(ctx.text(d.get('text', ''), f'{key}.text'), TFS, BW - 48, True, f'{key}.text') if d.get('text') else []
            if not body:
                ctx.diag('unrendered', f'{key} に value も text もない', 'error', key)
            bh, fs = len(body) * TFS * 1.35, TFS
        sides.append((key, lab, body, bh, fs))
    hbox = max(30 + len(lab) * LFS * 1.3 + 16 + bh + 30 for _, lab, _, bh, _ in sides)
    sv = Svg(ctx)
    for k, (key, lab, body, bh, fs) in enumerate(sides):
        x = k * (BW + GAP)
        em = hl == key
        rid = sv.rect(x, 4, BW, hbox, fill='#fff', stroke=INK if em else GRAY_LINE, sw=5 if em else 2, name=key)
        yy = 4 + 30
        for l in lab:
            sv.text(x + BW / 2, yy + LFS * 0.85, l, LFS, 'middle', TEXT2, False, inside=rid)
            yy += LFS * 1.3
        rest = 4 + hbox - 30 - yy - 16
        cy = yy + 16 + rest / 2
        sv.lines(x + BW / 2, cy, body, fs, INK, True, inside=rid, lh=1.35 if fs == TFS else 1.15)
    sv.line([(BW + 16, 4 + hbox / 2), (BW + GAP - 18, 4 + hbox / 2)], w=6)
    h = hbox + 10
    check_height(ctx, h)
    return sv.svg(None, h)


def _image_data(ctx, f):
    """画像の素材を、埋め込む形(data URI)と大きさで返す"""
    path = ctx.deck.root / str(f.get('file') or '')
    if not f.get('file') or not path.is_file():
        ctx.diag('unrendered', f'画像の素材のファイル {f.get("file")} がない', 'error', 'asset')
        return None, 0, 0
    try:
        from PIL import Image
        with Image.open(path) as im:
            iw, ih = im.size
    except Exception as e:
        ctx.diag('unrendered', f'画像の素材 {f.get("file")} を読めない: {type(e).__name__}', 'error', 'asset')
        return None, 0, 0
    mime = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.webp': 'image/webp', '.svg': 'image/svg+xml'}.get(path.suffix.lower(), 'image/png')
    return f'data:{mime};base64,' + base64.b64encode(path.read_bytes()).decode('ascii'), iw, ih


def r_annotated_image_steps(ctx):
    """注釈つきの画像(番号の印)。画像の素材を、crop の範囲が入るように切り抜き、regions の位置に番号の印を置く。
    番号は場面の順から決める。説明(captions)は、画像の右に番号の順で並べる"""
    b, dk = ctx.body, ctx.deck
    f = dk.facts.get(b.get('asset'))
    if f is None or f.get('kind') != 'image':
        ctx.diag('unrendered', f'画像の素材 {b.get("asset")} が素材台帳にない', 'error', 'asset')
        return ''
    if ctx.spec and b.get('asset') not in (ctx.spec.get('sources') or []):
        ctx.diag('reference', f'画像の素材 {b.get("asset")} が、このスライドの sources にない', 'warning', 'asset')
    regions = {r['id']: r for r in f.get('regions') or [] if isinstance(r, dict) and r.get('id')}
    captions = b.get('captions') or {}
    for rid in list(captions) + list(b.get('crop') or []):
        if rid not in regions:
            ctx.diag('unrendered', f'範囲 {rid} が、画像の素材の regions にない', 'error', str(rid))
    # 番号の順: 場面のつながりが指す要素の順。場面がなければ、captions に書いた順
    order = [r for r in captions if r in regions]
    if b.get('scenario') is not None:
        sc = dk.scn.get(b.get('scenario'))
        if sc is None:
            ctx.diag('unrendered', f'場面 {b.get("scenario")} が仕組みの定義にない', 'error', 'scenario')
        else:
            seq = []
            for rel_id in sc.get('steps') or []:
                rel = dk.rel.get(rel_id) or {}
                for rid, r in regions.items():
                    if r.get('element') and r.get('element') in (rel.get('to'), rel.get('from')) and rid in captions and rid not in seq:
                        seq.append(rid)
            for rid in order:
                if rid not in seq:
                    ctx.diag('unrendered', f'範囲 {rid} の要素が場面のつながりになく、番号を決められない', 'error', str(rid))
            order = seq
    uri, iw, ih = _image_data(ctx, f)
    # 切り抜く範囲(画像に対する割合)
    crop = [regions[r]['box'] for r in b.get('crop') or [] if r in regions and isinstance(regions[r].get('box'), list)]
    if crop:
        mx, my = 0.06, 0.08
        cx0 = max(0.0, min(c[0] for c in crop) - mx)
        cy0 = max(0.0, min(c[1] for c in crop) - my)
        cx1 = min(1.0, max(c[0] + c[2] for c in crop) + mx)
        cy1 = min(1.0, max(c[1] + c[3] for c in crop) + my)
    else:
        cx0, cy0, cx1, cy1 = 0.0, 0.0, 1.0, 1.0
    iw, ih = iw or 16, ih or 9
    pw, ph = (cx1 - cx0) * iw, (cy1 - cy0) * ih          # 切り抜いた範囲(画像のピクセル)
    MAXW, PAD = 640, 26                                   # PAD: 画像の外に印を置くための余白
    scale = min(MAXW / pw, max(120, ctx.avail_h - 2 * PAD) / ph)
    dw, dh = pw * scale, ph * scale
    if scale > 1.0 and uri:
        ctx.diag('image-scale', f'画像を {scale:.1f} 倍に拡大して描いた(元の画像 {iw}x{ih}px)', 'info', 'asset')
    sv = Svg(ctx)
    ox, oy = PAD, PAD
    if uri:
        sv.raw(f'<svg x="{ox}" y="{oy}" width="{dw:.1f}" height="{dh:.1f}" viewBox="{cx0 * iw:.2f} {cy0 * ih:.2f} {pw:.2f} {ph:.2f}" preserveAspectRatio="none">'
               f'<image href="{uri}" width="{iw}" height="{ih}"/></svg>')
    sv.raw(f'<rect x="{ox}" y="{oy}" width="{dw:.1f}" height="{dh:.1f}" fill="{"none" if uri else PART}" stroke="{GRAY_LINE}" stroke-width="1"/>')
    sv.ext(ox + dw + PAD, oy + dh + PAD)
    R = 17
    placed = []
    for n, rid in enumerate(order, 1):
        bx, by, bw_, bh_ = regions[rid]['box']
        x, y = ox + (bx - cx0) * iw * scale, oy + (by - cy0) * ih * scale
        w, h = bw_ * iw * scale, bh_ * ih * scale
        sv.raw(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="none" stroke="{INK}" stroke-width="3" data-name="{E(rid)}"/>')
        # 印は、指す範囲の外に置く(左、上、右、下の順に、画像の枠とほかの印に重ならない場所を探す)
        cands = [(x - R - 5, y + R), (x + R, y - R - 5), (x + w + R + 5, y + R), (x + R, y + h + R + 5)]
        ok = [(px, py) for px, py in cands if R <= px <= ox + dw + PAD - R and R <= py <= oy + dh + PAD - R
              and all(math.hypot(px - qx, py - qy) > 2 * R + 2 for qx, qy in placed)]
        if not ok:
            ctx.diag('overlap', f'範囲 {rid} の印を、指す対象に重ならない場所に置けない', 'error', str(rid))
            ok = [cands[0]]
        px, py = ok[0]
        placed.append((px, py))
        cid = sv.nid('c')
        sv.raw(f'<circle id="{cid}" cx="{px:.1f}" cy="{py:.1f}" r="{R}" fill="{INK}"/>')
        sv.text(px, py + FIG * 0.35, str(n), FIG, 'middle', '#ffffff', True, inside=cid)
    # 説明: 画像の右に、番号の順で並べる
    tx = ox + dw + PAD + 30
    twid = CW - tx - 46
    if twid < 240:
        ctx.diag('overflow', f'説明を置く幅が {twid:.0f}px しかない', 'error', 'captions')
        twid = 240
    yy = oy
    for n, rid in enumerate(order, 1):
        lines = ctx.wrap(ctx.text(captions.get(rid, ''), f'captions.{rid}'), BODY, twid, False, f'captions.{rid}')
        cid = sv.nid('c')
        sv.raw(f'<circle id="{cid}" cx="{tx + R:.1f}" cy="{yy + R:.1f}" r="{R}" fill="{INK}"/>')
        sv.text(tx + R, yy + R + FIG * 0.35, str(n), FIG, 'middle', '#ffffff', True, inside=cid)
        for k, l in enumerate(lines):
            sv.text(tx + 2 * R + 12, yy + R + BODY * 0.35 + k * BODY * 1.4, l, BODY, role='body')
        yy += max(2 * R, len(lines) * BODY * 1.4) + 18
    h = max(oy + dh + PAD, yy)
    check_width(ctx, sv.w)
    check_height(ctx, h)
    return sv.svg(None, h)


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
    if hl:
        ctx.em(hl)
    ctx.center = False
    names = [c.get('name') if isinstance(c, dict) else c for c in cols]
    aligns = []
    for j, c in enumerate(cols):
        a = c.get('align') if isinstance(c, dict) else None
        if a is None:   # 全てのセルが事実の参照で始まる列は右に寄せる
            a = 'right' if all(isinstance(r, list) and j < len(r) and re.match(r'(\{?F\d+)', str(r[j])) for r in rows) else 'left'
        aligns.append(a)
    td = 'padding:12px;border-bottom:1px solid #D1D5DB'
    BK = '5px solid #111827'
    out = f'<table data-role="body" style="border-collapse:collapse;font-size:{BODY}px;width:{CW}px"><tr style="background:#F3F4F6">'
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
    if hl:
        ctx.em(hl)
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
        col = TEXT3 if mark else GRAY_LINE
        rid = sv.rect(ax, ay, aw, ah, fill='#fff', stroke=col, sw=2, rx=8, dash='8 6', name='aside')
        if mark:
            sv.text(ax + 14, ay + 28, mark, NOTE, color=col, bold=True, role='note', inside=rid)
        for k, l in enumerate(lines):
            sv.text(ax + 14, ay + 60 + k * FS * 1.3, l, FS, inside=rid)
        used_w = ax + aw
    check_width(ctx, used_w)
    check_height(ctx, sv.h + 4)
    return sv.svg()


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
    if hl_ids:
        ctx.em('highlight')
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
    def no_label(i):
        # 分かれ目の「いいえ」。最後の分かれ目から次の要素へ進む道は、labels に condition があればそれを書く
        if i == len(cols) - 2 and cols[i]['kind'] == 'dec':
            return lab(last['id'], 'condition', 'いいえ')
        return 'いいえ'

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
            if c['kind'] == 'dec':
                hw_l = tw(no_label(i), FS) / 2 + 4
                g = max(G, 2 * (hw_l - free(c) / 2), 2 * (hw_l - free(cols[i + 1]) / 2) + 4)
            else:
                g = G
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
            did = sv.diamond(cx, yc, c['w'], c['h'], name=r['id'], stroke=INK if em else (dk.colors.get('案の印', '#6B7280') if prop else '#6B7280'),
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
                sv.text((x1 + x2) / 2, yc - 20, no_label(i), FS, 'middle', TEXT2)
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
    return sv.svg()


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
    if hl:
        ctx.em(hl)
    FS = FIG
    LH = FS * 1.25
    # 入れ子(contain): 構成図では、含む側を枠にする
    parent = {}
    if kind == 'architecture':
        for r in R:
            if r['kind'] == 'contain':
                parent[r['to']] = r['from']
    containers = set(parent.values())
    for e in details:
        if e in containers:
            ctx.diag('unrendered', f'details の {e} は枠(contain で中に部品を持つ要素)のため描けない', 'error', e)
        elif e not in els:
            ctx.diag('unrendered', f'details の {e} が elements にない', 'error', e)
    connected = {r['from'] for r in R} | {r['to'] for r in R}
    isolated = [e for e in els if e not in connected and e not in containers]
    # 部品の大きさ
    info = {}
    for e in els:
        nm = dk.name(e, labels)
        bold = e == hl
        lines = ctx.wrap(nm, FS, 176, bold, e)
        det = [l for x in details.get(e, []) for l in ctx.wrap(ctx.text(x), NOTE, 150 if e in isolated else 240, False, e + '.details')]
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
        ctx.diag('layout', 'groups をまたぐつながりがある。groups ごとの横並びにせず、1つの図として置いた', 'warning', 'groups')
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
            if i['det']:   # 中に一覧を持つ部品: 名前を上に、一覧をその下に描く
                yy = y0 + 12
                for l in i['lines']:
                    sv.text(x0 + w / 2, yy + FS * 0.95, l, FS, 'middle', INK, em, inside=ids[e])
                    yy += LH
                yy += 6
                for d in i['det']:
                    sv.text(x0 + 20, yy + NOTE * 1.0, d, NOTE, role='note', inside=ids[e])
                    yy += NOTE * 1.45
            else:
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
    return sv.svg()


def r_er(ctx):
    return graph_figure(ctx, 'er')


def r_arch(ctx):
    return graph_figure(ctx, 'architecture')

RENDERERS = {
    'statement': r_statement, 'plain-list': r_plain_list, 'step-flow': r_step_flow, 'cause-chain': r_cause_chain,
    'pie-chart': r_pie_chart, 'bar-chart': r_bar_chart, 'before-after': r_before_after, 'table': r_table, 'tree': r_tree,
    'flowchart': r_flowchart, 'er-diagram': r_er, 'architecture-diagram': r_arch,
    'annotated-image-steps': r_annotated_image_steps,
}


# ---------------------------------------------------------------- 枠(題、要点、中身、脚注)

CSS = f"""
.slide{{box-sizing:border-box;width:{W}px;height:{H}px;background:#fff;font-family:{FONT_FAMILY};color:{INK};position:relative;overflow:hidden;
word-break:auto-phrase;display:flex;flex-direction:column;padding:{TOP}px {MX}px {BOTTOM}px;text-align:left}}
.slide *{{box-sizing:border-box;margin:0;padding:0}}
.slide .head{{flex:none}}
.slide .kicker{{flex:none;font-size:{KICKER_FS}px;line-height:1.3;color:{TEXT3};margin-top:12px;white-space:nowrap}}
.slide .trow{{display:flex;align-items:flex-start;justify-content:space-between;gap:16px}}
.slide .title{{flex:1;min-width:0;font-size:{TITLE_FS}px;font-weight:bold;line-height:{TITLE_LH}}}
.slide .mark{{flex:none;font-size:{NOTE}px;line-height:1.3;padding:3px 12px;border:2px solid {TEXT2};border-radius:14px;margin-top:7px;white-space:nowrap}}
.slide .mark.proposal{{border-style:dashed}}
.slide .mark.practice{{border-style:double;border-width:4px;padding:1px 10px}}
.slide .point{{font-size:{POINT_FS}px;font-weight:bold;line-height:{POINT_LH}}}
.slide .head .point{{margin-top:8px}}
.slide .wk{{font-size:{NOTE}px;font-weight:normal;color:{TEXT3};border:1px dashed {GRAY_LINE};padding:1px 8px;margin-right:10px;white-space:nowrap;vertical-align:middle}}
.slide .main{{flex:1 1 0;min-height:0;margin-top:{GAP_MAIN}px;display:flex;flex-direction:column;align-items:flex-start;justify-content:flex-start}}
.slide .main.mid{{align-items:center;justify-content:center}}
.slide .after{{align-self:stretch;margin-top:18px;font-size:{BODY}px;color:{TEXT2};line-height:1.45}}
.slide .below{{flex:none;margin-top:{GAP_BELOW}px}}
.slide .foot{{flex:none;min-height:{FOOT_MIN}px;margin-top:10px;display:flex;align-items:flex-end;justify-content:space-between;gap:24px}}
.slide .fn{{flex:1;font-size:{FOOT_FS}px;line-height:{FOOT_LH};color:{TEXT3};border-top:1px solid #D1D5DB;padding-top:6px}}
.slide .fn span{{margin-right:28px}}
.slide .pg{{flex:none;margin-left:auto;font-size:{FOOT_FS}px;line-height:{FOOT_LH};color:{TEXT3};min-width:40px;text-align:right}}
.slide .ph{{align-self:stretch;border:2px dashed {GRAY_LINE};padding:18px 22px;font-size:{BODY}px;line-height:1.55;color:{TEXT2}}}
.slide .ph b{{color:{INK}}}
.slide .plain{{align-self:stretch;list-style:none;font-size:{BODY}px;line-height:1.45}}
.slide .plain li{{padding-left:1.1em;text-indent:-1.1em;margin-bottom:5px}}
.slide .cover{{align-self:stretch}}
.slide .cover .title{{font-size:48px;line-height:1.3;margin-top:6px}}
"""


def foot_html(items, page):
    fn = ''
    if items:
        fn = '<div class="fn" data-role="footnote">' + ''.join(f'<span>{E(k)}: {E(v)}</span> ' for k, v in items) + '</div>'
    pg = f'<div class="pg" data-role="footnote">{page}</div>' if page else ''
    return f'<div class="foot">{fn}{pg}</div>'


def foot_text(items):
    return ' '.join(f'{k}: {v}' for k, v in items)


def est_lines(text, fs, width, bold=False):
    return len(wrap(str(text), fs, width, bold, balance=False)[0]) if text else 0


def avail_height(title, point, pos, foot_items, kicker=None, after=None, mark=False, label=None):
    """中身に使える高さの見積もり。行の数は、同じフォントで測って見積もる。実際の配置はブラウザが決め、診断で確かめる"""
    h = H - TOP - BOTTOM - GAP_MAIN
    side = (90 if mark else 0) + (tw(kicker, KICKER_FS) + 16 if kicker else 0)
    h -= TITLE_FS * TITLE_LH * max(1, est_lines(title, TITLE_FS, CW - side, True))
    if point and pos in ('below-title', 'below-body'):
        n = est_lines(point, POINT_FS, CW - (tw(label, NOTE) + 30 if label else 0), True)
        h -= POINT_FS * POINT_LH * n + (8 if pos == 'below-title' else GAP_BELOW)
    elif label and not point:
        h -= POINT_FS * POINT_LH + 8
    fn = est_lines(foot_text(foot_items), FOOT_FS, CW - 64 - 28 * max(0, len(foot_items) - 1)) if foot_items else 0
    h -= 10 + max(FOOT_MIN, 7 + fn * FOOT_FS * FOOT_LH)
    if after:
        h -= 18 + BODY * 1.45 * est_lines(after, BODY, CW)
    return h


def frame(sid, title, main, *, kicker=None, point=None, pos='below-title', foot=(), page=None, mark=None, label=None,
          mid=False, after=None, cover=False):
    """スライド1枚の HTML。上から、題、要点(題の直下の場合)、中身、要点(中身の下の場合)、脚注。
    要点は1か所にだけ描く。pos が body の要点は、中身の側が描く。要点がなければ、要点の場所を空けない。
    label は、確認用の資料だけに出す小さな札(節の要点、要点なし)。"""
    lab = f'<span class="wk" data-role="note">{E(label)}</span>' if label else ''
    pt = f'<div class="point" data-role="point">{E(point)}</div>' if point else ''
    head = ''
    if not cover:
        mk = ''
        if mark:
            mk = f'<span class="mark {E(mark)}" data-role="note">{E(PROVENANCE[mark][0])}</span>'
        if kicker:      # 題の位置を動かさないよう、札は題の行の右端に置く
            mk = f'<span class="kicker" data-role="note">{E(kicker)}</span>' + mk
        head = f'<div class="head"><div class="trow"><div class="title" data-role="title">{E(title)}</div>{mk}</div>'
        if point and pos == 'below-title':
            head += f'<div class="point" data-role="point">{lab}<span>{E(point)}</span></div>' if lab else pt
        elif lab and not point:
            head += f'<div class="point">{lab}</div>'
        head += '</div>'
    below = ''
    if point and pos == 'below-body':
        below = (f'<div class="point below" data-role="point">{lab}<span>{E(point)}</span></div>' if lab
                 else f'<div class="point below" data-role="point">{E(point)}</div>')
    aft = f'<div class="after" data-role="body">{E(after)}</div>' if after else ''
    return (f'<div class="slide" data-sid="{html.escape(sid, quote=True)}">{head}'
            f'<div class="main{" mid" if mid else ""}">{main}{aft}</div>{below}{foot_html(list(foot), page)}</div>')


def standalone(fragment):
    return (f'<!doctype html><html lang="ja"><head><meta charset="utf-8"><style>html,body{{margin:0;padding:0;background:#fff}}{CSS}</style></head>'
            f'<body>{fragment}</body></html>')


# ---------------------------------------------------------------- 本編と付録のスライド

def relation_names():
    return {t: r.get('種類', t) for r in C.md_table('vocabulary.md', '主張の種類の語彙') for t in C.ticks(r.get('識別子', ''))}


def annotations(deck, ctx, v, fids):
    """限定、出どころ、出典を、資料の型の定義の annotation が定める置き場に分ける。(脚注の項目, 印, ノートに足す行) を返す"""
    foot, mark, notes = [], None, []
    if v['qualifiers']:
        q = '、'.join(map(str, v['qualifiers']))
        (foot if deck.ann_q == 'footnote' else notes).append(('限定', q))
    prov = v.get('provenance')
    if prov and deck.ann_p != 'none':
        if prov not in PROVENANCE:
            ctx.diag('unrendered', f'出どころ「{prov}」は cited、proposal、practice で書く', 'error', 'provenance')
        elif deck.ann_p == 'mark':
            mark = prov
        else:
            (foot if deck.ann_p == 'footnote' else notes).append(('出どころ', PROVENANCE[prov][1]))
    names = deck.source_names(fids)
    if names:
        foot.append(('出典', '、'.join(names)))
    return foot, mark, notes


def render_content(deck, sid, page):
    """本編と付録のスライド1枚。スライド仕様がある場合は型で描く。ない場合と保留の場合は、立証の設計から仮置きを、
    それもない場合は骨組み(題、要点、根拠の事実)を描く。"""
    v = deck.view(sid)
    spec = deck.specs.get(sid)
    ctx = Ctx(deck, sid, spec)
    s = deck.S.get(sid) or {}
    blocked = spec is not None and spec.get('status') == 'blocked'
    proof = deck.proof.get(sid) if deck.level != 'skeleton' else None
    mode = 'spec' if spec is not None and not blocked else 'placeholder' if proof else 'skeleton'
    ctx.mode = mode
    working = deck.level in ('skeleton', 'placeholder')
    title = v['title']
    if not title:
        ctx.diag('unrendered', '題がない', 'error', 'title')
        title = '(題なし)'
    ptype = ((spec or {}).get('body') or {}).get('type') if mode == 'spec' else deck.pattern_for(sid) if proof else None
    point = v['point']
    if v['point_kind'] == 'section' and not point:
        ctx.diag('unrendered', '節の要点を引くスライドだが、節の要点が章構成にない', 'error', 'point')
    pos = deck.position(ptype) if point else None
    fids = (spec or {}).get('sources') if mode == 'spec' else (proof or {}).get('facts') or s.get('evidence')
    foot, mark, note_lines = annotations(deck, ctx, v, fids or [])
    label = None
    if working:
        label = '節の要点' if v['point_kind'] == 'section' else None
        if not point:
            label = '要点なし(役割: ' + deck.role_names.get(v['role'], str(v['role'] or '未記入')) + ')'
    after = None
    if mode == 'spec' and spec.get('text'):
        after = ctx.text(spec['text'], 'text')
    ctx.avail_h = avail_height(title, point, pos, foot, after=after, mark=bool(mark), label=label)
    ctx.point_in_body = point if pos == 'body' else None
    ctx.type = ptype
    if mode == 'spec':
        fn = RENDERERS.get(ptype)
        if fn is None:
            ctx.diag('unrendered', f'型 {ptype} の描画がない(描ける型: {", ".join(sorted(RENDERERS))})', 'error', 'body.type')
            fig = f'<div class="ph" data-role="body">この型は描けない</div>'
        else:
            try:
                fig = fn(ctx)
            except Exception as e:    # 描画の失敗も診断として出し、ほかのスライドは続ける
                ctx.diag('unrendered', f'描画に失敗した: {type(e).__name__}: {e}', 'error', 'body')
                fig = '<div class="ph" data-role="body">描画に失敗した</div>'
        n = max(count_highlight(spec.get('body')), len(ctx.ems))
        if n >= 2:
            ctx.diag('emphasis', f'強調が1枚に {n} か所ある(1か所まで)', 'error', 'highlight')
    else:
        ctx.center = False
        if blocked:
            ctx.diag('placeholder', f'保留のスライド({spec.get("issue") or "Issue の番号なし"})。仮置きを描いた', 'info')
        elif deck.level == 'full':
            ctx.diag('placeholder', 'スライド仕様がない。' + ('仮置きを描いた' if mode == 'placeholder' else '骨組みを描いた'), 'info')
        if mode == 'placeholder':
            rel = proof.get('relation')
            what = deck.pattern_names.get(ptype) or relation_names().get(rel) or str(rel)
            bits = [f'<b>仮置き: ここに{E(what)}</b>']
            if proof.get('show'):
                bits.append(f'見せるもの: {E(proof["show"])}')
            if proof.get('focus'):
                bits.append(f'注目させる点: {E(proof["focus"])}')
            fig = f'<div class="ph" data-role="body">{"<br>".join(bits)}</div>'
        else:
            sts = []
            for fid in s.get('evidence') or []:
                f = deck.facts.get(fid)
                if f is None:
                    ctx.diag('unrendered', f'根拠の事実 {fid} が素材台帳にない', 'error', 'evidence')
                else:
                    sts.append(str(f.get('statement') or ''))
            fig = ''
            if sts:
                fig = (f'<div data-role="note" style="font-size:{NOTE}px;color:{TEXT3};margin-bottom:6px">根拠の事実</div>'
                       '<ul class="plain" data-role="body" style="font-size:24px">' + ''.join(f'<li>・{E(x)}</li>' for x in sts) + '</ul>')
    if ctx.point_in_body and not getattr(ctx, 'point_drawn', False) and not (mode == 'spec' and ptype == 'statement'):
        # 要点を中身として描く位置だが、型が要点を描かない場合は、中身の先頭に1回だけ描く
        fig = (f'<div class="point pt-body" data-role="point" style="align-self:stretch;font-size:{POINT_BODY_FS}px;line-height:1.45;margin-bottom:22px">'
               f'{E(point)}</div>') + fig
    if len({c for c in ctx.colors_used if not is_gray(c)}) > deck.max_hues:
        ctx.diag('hue-count', f'1枚で使う色相が {len({c for c in ctx.colors_used if not is_gray(c)})} で、上限 {deck.max_hues} を越える', 'error')
    for a, b in ctx.adjacent:
        if a != b and contrast(a, b) < ADJACENT_CONTRAST_MIN:
            ctx.diag('adjacent-contrast', f'隣り合う面の色 {a} と {b} の差が小さい(コントラスト比 {contrast(a, b):.2f}、下限 {ADJACENT_CONTRAST_MIN})', 'error')
    notes = []
    if mode == 'spec' and spec.get('notes'):
        notes.append(Ctx(deck, sid, spec).text(spec['notes'], 'notes'))
    notes += [f'{k}: {t}' for k, t in note_lines]
    ctx.notes = '\n'.join(notes)
    ctx.point = point
    frag = frame(sid, title, fig, point=point, pos=pos or 'below-title', foot=foot, page=page, mark=mark, label=label,
                 mid=ctx.center and mode == 'spec', after=after)
    return frag, ctx


# ---------------------------------------------------------------- 自動で作るスライド(導出と半導出)

def auto_ctx(deck, sid):
    ctx = Ctx(deck, sid, None)
    ctx.mode, ctx.notes, ctx.point, ctx.type = 'auto', '', None, None
    return ctx


def union(*lists):
    out = []
    for l in lists:
        out += [x for x in l or [] if x not in out]
    return out


def qual_foot(deck, ctx, quals):
    """自動で作るスライドの限定。載せる要点の限定を、置き場(脚注かノート)にまとめる"""
    if not quals:
        return []
    item = ('限定', '、'.join(map(str, quals)))
    if deck.ann_q == 'footnote':
        return [item]
    ctx.notes = f'{item[0]}: {item[1]}'
    return []


def render_toc(deck, page):
    """目次。章と節の題を載せる"""
    ctx = auto_ctx(deck, 'toc')
    blocks, est = [], 0
    for i, ch in enumerate(deck.chapters, 1):
        rows = f'<div data-role="body" style="font-size:26px;font-weight:bold;line-height:1.5"><span style="display:inline-block;width:64px">{i}</span>{E(ch.get("title", ""))}</div>'
        est += 39 + 10
        for j, sec in enumerate([s for s in ch.get('sections') or [] if isinstance(s, dict)], 1):
            rows += f'<div data-role="body" style="font-size:{BODY}px;line-height:1.45;padding-left:64px"><span style="display:inline-block;width:64px;color:{TEXT3}">{i}.{j}</span>{E(sec.get("title", ""))}</div>'
            est += 35
        blocks.append(f'<div style="break-inside:avoid;margin-bottom:10px">{rows}</div>')
    for name in (['付録'] if any(s.get('chapter') == 'appendix' for s in deck.storyline) else []) + (['出典の一覧'] if deck.storyline else []):
        blocks.append(f'<div data-role="body" style="break-inside:avoid;font-size:26px;font-weight:bold;line-height:1.5;margin-bottom:10px;padding-left:64px">{name}</div>')
        est += 49
    avail = avail_height('目次', None, None, [])
    cols = 'column-count:2;column-gap:48px;' if est > avail else ''
    main = f'<div style="align-self:stretch;{cols}">{"".join(blocks)}</div>'
    return frame('toc', '目次', main, page=page), ctx


def render_cover(deck, i, ch, page, detail):
    """章扉。章の題と、その章で答える問い。目次と章扉の資料(detail)では、章の要点と、節の題と要点も載せる"""
    sid = f'{ch["id"]}-cover'
    ctx = auto_ctx(deck, sid)
    q = ch.get('question')
    if not q:
        ctx.diag('unrendered', 'この章で答える問い(章構成の question)がない', 'error', 'question')
    body = (f'<div class="cover"><div data-role="body" style="font-size:26px;color:{TEXT3}">第{i}章</div>'
            f'<div class="title" data-role="title">{E(ch.get("title") or "(題なし)")}</div>')
    if q:
        body += (f'<div data-role="note" style="font-size:{KICKER_FS}px;color:{TEXT3};margin-top:{30 if detail else 52}px">この章で答える問い</div>'
                 f'<div data-role="body" style="font-size:30px;line-height:1.45;margin-top:4px">{E(q)}</div>')
    foot = []
    if detail:
        quals = list(ch.get('qualifiers') or [])
        if ch.get('point'):
            body += (f'<div data-role="note" style="font-size:{KICKER_FS}px;color:{TEXT3};margin-top:20px">章の要点</div>'
                     f'<div class="point" data-role="point" style="margin-top:4px">{E(ch["point"])}</div>')
            ctx.point = ch['point']
        else:
            ctx.diag('unrendered', '章の要点がない', 'error', 'point')
        secs = [s for s in ch.get('sections') or [] if isinstance(s, dict)]
        if secs:
            body += f'<div data-role="note" style="font-size:{KICKER_FS}px;color:{TEXT3};margin-top:20px">節の題と要点</div>'
        for j, sec in enumerate(secs, 1):
            p, sq = deck.section_point(sec.get('id'))
            same = sec.get('point_from') == 'chapter' or p == ch.get('point')
            quals = union(quals, [] if same else sq)
            ptxt = '(章の要点を引く)' if same else (p or '(要点なし)')
            body += (f'<div data-role="body" style="font-size:{BODY}px;line-height:1.45;margin-top:8px;display:flex;gap:18px">'
                     f'<span style="flex:none;color:{TEXT3}">{i}.{j}</span><span><b>{E(sec.get("title", ""))}</b><br>{E(ptxt)}</span></div>')
        foot = qual_foot(deck, ctx, quals)
    body += '</div>'
    frag = frame(sid, '', body, foot=foot, page=page, cover=True, mid=not detail)
    return frag, ctx


def render_list_slide(deck, sid, kicker, title, point, items, quals, page):
    """まとめのスライド。承認済みの文(要点)を、そのまま並べる。新しい文を書かない"""
    ctx = auto_ctx(deck, sid)
    if not point:
        ctx.diag('unrendered', 'まとめに載せる要点がない', 'error', 'point')
    foot = qual_foot(deck, ctx, quals)
    main = '<ul class="plain" data-role="body">' + ''.join(f'<li>・{E(x)}</li>' for x in items) + '</ul>' if items else ''
    ctx.point = point
    return frame(sid, title or '(題なし)', main, kicker=kicker, point=point, pos='below-title', foot=foot, page=page), ctx


def render_section_summary(deck, sec_id, page):
    """節のまとめ。節の要点と、節内のスライドの要点を順に並べる"""
    ch, sec = deck.sections[sec_id]
    p, q = deck.section_point(sec_id)
    slides = [s for s in deck.section_slides(sec_id) if isinstance(s.get('point'), str) and s['point'].strip()]
    quals = union(q, *[s.get('qualifiers') for s in slides])
    return render_list_slide(deck, f'{sec_id}-summary', '節のまとめ', sec.get('title'), p, [s['point'] for s in slides], quals, page)


def render_chapter_summary(deck, i, ch, page):
    """章のまとめ。章の要点と、その章の節の要点を順に並べる"""
    pts, quals = [], list(ch.get('qualifiers') or [])
    for sec in ch.get('sections') or []:
        p, q = deck.section_point(sec.get('id'))
        if p and p != ch.get('point'):
            pts.append(p)
            quals = union(quals, q)
    return render_list_slide(deck, f'{ch["id"]}-summary', f'第{i}章のまとめ', ch.get('title'), ch.get('point'), pts, quals, page)


def render_appendix_cover(deck, page):
    ctx = auto_ctx(deck, 'appendix-cover')
    body = '<div class="cover"><div class="title" data-role="title">付録</div></div>'
    return frame('appendix-cover', '', body, page=page, cover=True, mid=True), ctx


def render_marks(deck, page):
    """出どころの印の説明。印を使う資料(annotation の provenance が mark)に、冒頭の1枚として置く"""
    ctx = auto_ctx(deck, 'marks')
    rows = ''.join(f'<div style="display:flex;align-items:center;gap:22px;margin-bottom:22px"><span class="mark {k}" data-role="note" style="margin-top:0">{E(m)}</span>'
                   f'<span data-role="body" style="font-size:28px">{E(mean)}</span></div>' for k, (m, mean) in PROVENANCE.items())
    return frame('marks', '出どころの印', f'<div>{rows}</div>', page=page), ctx


def source_entries(deck, seq):
    """出典の名前 → 使ったスライドのページ番号"""
    used = {}
    for it in seq:
        if it['kind'] not in ('本編', '付録'):
            continue
        sid = it['id']
        spec = deck.specs.get(sid)
        blocked = spec is not None and spec.get('status') == 'blocked'
        fids = (spec.get('sources') if spec is not None and not blocked else None) or (deck.proof.get(sid) or {}).get('facts') or deck.S.get(sid, {}).get('evidence') or []
        for name in deck.source_names(fids):
            used.setdefault(name, [])
            if it['no'] not in used[name]:
                used[name].append(it['no'])
    return list(used.items())


def source_pages(deck, seq):
    """出典の一覧を、1枚に収まる分ごとに分ける"""
    limit = avail_height('出典の一覧', None, None, [])
    pages, cur, h = [], [], 0
    for name, nos in source_entries(deck, seq):
        t = f'{name}({"、".join(map(str, nos))}ページ)'
        eh = est_lines(t, BODY, CW) * BODY * 1.45 + 8
        if cur and h + eh > limit:
            pages.append(cur)
            cur, h = [], 0
        cur.append(t)
        h += eh
    if cur:
        pages.append(cur)
    return pages


def render_sources(deck, k, total, items, page):
    sid = f'sources-{k}'
    ctx = auto_ctx(deck, sid)
    li = ''.join(f'<li style="margin-bottom:8px">{E(t)}</li>' for t in items)
    ttl = '出典の一覧' + (f'({k}/{total})' if total > 1 else '')
    main = f'<ul data-role="body" style="align-self:stretch;list-style:none;font-size:{BODY}px;line-height:1.45">{li}</ul>'
    return frame(sid, ttl, main, page=page), ctx


# ---------------------------------------------------------------- 全体

def deck_order(deck):
    """描く順の一覧。1件は {id, kind, chapter, fn}。章の中は、章扉、節ごとのスライド(節のまとめは節の最後)、章のまとめの順。
    付録と出典の一覧は最後。"""
    seq = []
    add = lambda sid, kind, ch, fn: seq.append({'id': sid, 'kind': kind, 'chapter': ch, 'fn': fn})
    if deck.level == 'samples':
        for sid in deck.sample_ids:
            add(sid, '見本', (deck.S.get(sid) or {}).get('chapter'), lambda page, sid=sid: render_content(deck, sid, page))
        return seq
    detail = deck.level == 'toc'
    add('toc', '目次', None, lambda page: render_toc(deck, page))
    if not detail and deck.ann_p == 'mark':
        add('marks', '出どころの印の説明', None, lambda page: render_marks(deck, page))
    for i, ch in enumerate(deck.chapters, 1):
        cid = ch['id']
        add(f'{cid}-cover', '章扉', cid, lambda page, i=i, ch=ch: render_cover(deck, i, ch, page, detail))
        if detail:
            continue
        mine = [s for s in deck.storyline if s.get('chapter') == cid]
        secs = [s for s in ch.get('sections') or [] if isinstance(s, dict) and s.get('id')]
        done = set()
        for sec in secs:
            for s in mine:
                if s.get('section') == sec['id']:
                    add(s['id'], '本編', cid, lambda page, sid=s['id']: render_content(deck, sid, page))
                    done.add(s['id'])
            if deck.needs_section_summary(sec['id']):
                add(f'{sec["id"]}-summary', '節のまとめ', cid, lambda page, sec=sec: render_section_summary(deck, sec['id'], page))
        for s in mine:
            if s['id'] not in done:   # 節が章構成にないスライド
                add(s['id'], '本編', cid, lambda page, sid=s['id']: render_content(deck, sid, page))
        if len(secs) > 1:             # 節が1つだけの章には、章のまとめを置かない
            add(f'{cid}-summary', '章のまとめ', cid, lambda page, i=i, ch=ch: render_chapter_summary(deck, i, ch, page))
    if detail:
        return seq
    known = {c['id'] for c in deck.chapters} | {'appendix'}
    for s in deck.storyline:
        if s.get('chapter') not in known:
            add(s['id'], '本編', s.get('chapter'), lambda page, sid=s['id']: render_content(deck, sid, page))
    app = [s['id'] for s in deck.storyline if s.get('chapter') == 'appendix']
    if app:
        add('appendix-cover', '付録の扉', 'appendix', lambda page: render_appendix_cover(deck, page))
        for sid in app:
            add(sid, '付録', 'appendix', lambda page, sid=sid: render_content(deck, sid, page))
    for n, it in enumerate(seq, 1):
        it['no'] = n
    pages = source_pages(deck, seq)
    for k, items in enumerate(pages, 1):
        add(f'sources-{k}', '出典の一覧', None, lambda page, k=k, items=items: render_sources(deck, k, len(pages), items, page))
    return seq


def visible_text(fragment):
    return html.unescape(re.sub(r'<[^>]+>', '\n', fragment))


def scan_text(deck, ctx, fragment):
    """読み手に見える文に、内部のIDと、置き換えていない参照が残っていないか。要点の文が2回出ていないか"""
    text = visible_text(fragment)
    for m in set(re.findall(r'\{[^{}\n]*\}', text)):
        ctx.diag('internal-id', f'置き換えていない参照が残っている: {m}', 'error')
    for i in sorted(deck.all_ids):
        if len(i) >= 2 and re.search(r'(?<![A-Za-z0-9_-])' + re.escape(i) + r'(?![A-Za-z0-9_-])', text):
            ctx.diag('internal-id', f'内部のID {i} が、読み手に見える文に出ている', 'error')
    p = getattr(ctx, 'point', None)
    if p and ctx.mode != 'skeleton' and text.count(str(p)) >= 2:   # 骨組みでは、根拠の事実の文が要点と同じになりうる
        ctx.diag('duplicate', '要点の文が、1枚の中に2回出ている', 'error', 'point')


DECK_CSS = f"""
html,body{{margin:0;padding:0}}
body{{background:#e5e7eb;font-family:{FONT_FAMILY}}}
section{{width:{W}px;margin:0 auto;padding:14px 0 14px}}
.cap{{font-size:14px;color:#374151;margin:0 0 4px}}
.frame{{border:1px solid #9ca3af;width:{W}px;height:{H}px;box-sizing:content-box;background:#fff}}
.notes{{font-size:14px;color:#374151;margin-top:4px;white-space:pre-wrap}}
.bad{{color:#b91c1c;font-weight:bold}}
@page{{size:{W}px {H}px;margin:0}}
@media print{{
 body{{background:#fff}}
 section{{padding:0;margin:0;break-after:page;page-break-after:always;height:{H}px;overflow:hidden}}
 .cap,.notes{{display:none}}
 .frame{{border:none}}
}}
"""


def main(argv=None, level=None):
    ap = argparse.ArgumentParser(description='スライド仕様からスライドを描く')
    ap.add_argument('deck', nargs='?', help='資料のディレクトリ')
    ap.add_argument('--level', choices=['toc', 'skeleton', 'placeholder', 'full'], default=level or 'full',
                    help='toc(目次と章扉) / skeleton(骨組み) / placeholder(仮置き) / full(全スライド。既定)')
    ap.add_argument('--samples', action='store_true', help='型の見本(06-samples/)だけを描く')
    ap.add_argument('--pdf', action='store_true', help='全スライドを1つの PDF(deck.pdf)にまとめて出す')
    ap.add_argument('--only', nargs='*', help='このIDのスライドだけを描き直す(deck.html は全体で作り直す)')
    ap.add_argument('--chapter', help='この章のスライドだけを描き直す。付録は appendix')
    ap.add_argument('--no-png', action='store_true', help='PNG を撮らない(診断は取る)')
    ap.add_argument('--out', help='出力先。既定は <資料のディレクトリ>/build(確認用の資料と見本は、その下の toc、skeleton、placeholder、samples)')
    ap.add_argument('--show-ids', action='store_true', help='deck.html の見出しに、スライドのIDと診断の件数を出す(作業用。スライドの中には出さない)')
    ap.add_argument('--patterns', action='store_true', help='描ける型の一覧を出して終わる')
    a = ap.parse_args(argv)
    if a.patterns:
        print('\n'.join(sorted(RENDERERS)))
        return 0
    if not a.deck:
        ap.error('資料のディレクトリが要る')
    root = Path(a.deck).resolve()
    if not root.is_dir():
        sys.exit(f'資料のディレクトリがない: {root}')
    lv = 'samples' if a.samples else a.level
    deck = Deck(root, lv)
    out = Path(a.out).resolve() if a.out else (root / 'build' if lv == 'full' else root / 'build' / lv)
    sd = out / 'slides'
    sd.mkdir(parents=True, exist_ok=True)
    seq = deck_order(deck)
    for n, it in enumerate(seq, 1):
        it['no'] = n
        deck.page_of[it['id']] = n
    for sid in deck.specs:
        if sid not in deck.S and lv != 'samples':
            print(f'警告: スライド仕様 {sid}({deck.spec_file[sid]})がストーリーラインにない。描かない', file=sys.stderr)
    selected = lambda it: (not a.only or it['id'] in a.only) and (not a.chapter or it['chapter'] == a.chapter)
    partial = bool(a.only or a.chapter)
    if not partial:
        for old in list(sd.glob('*.html')) + list(sd.glob('*.png')):
            old.unlink()
    digest = inputs_hash(root)
    rendered = []
    for it in seq:
        frag, ctx = it['fn'](it['no'])
        scan_text(deck, ctx, frag)
        it['frag'], it['ctx'] = frag, ctx
        it['file'] = f'{it["no"]:02d}-{it["id"]}'
        if selected(it):
            (sd / f'{it["file"]}.html').write_text(standalone(frag), encoding='utf-8')
            rendered.append(it)
    # deck.html: 1つのファイルに全スライドを入れる(スライドごとのファイルを読み込まない)
    dpath = out / 'diagnostics.json'
    old = {}
    if partial and dpath.is_file():
        try:
            old = {d['id']: d for d in json.loads(dpath.read_text(encoding='utf-8')).get('slides', [])}
        except (ValueError, KeyError, TypeError):
            old = {}
    # ブラウザで診断を取り、PNG を撮り、PDF を作る
    jobs = {'min': deck.min, 'contrast': [TEXT_CONTRAST_MIN, TEXT_CONTRAST_MIN_LARGE],
            'slides': [{'id': it['id'], 'html': str(sd / f'{it["file"]}.html'), 'png': None if a.no_png else str(sd / f'{it["file"]}.png')} for it in rendered],
            'pdf': None}
    secs = ''
    for it in seq:
        cap = f'{it["no"]} / {len(seq)} ・ {E(it["kind"])}' + (f' ・ {E(it["id"])}' if a.show_ids else '')
        notes = f'<div class="notes">ノート: {E(it["ctx"].notes)}</div>' if getattr(it['ctx'], 'notes', '') else ''
        secs += (f'<section id="s{it["no"]}"><div class="cap">{cap}<!--badge:{html.escape(it["id"], quote=True)}--></div>'
                 f'<div class="frame">{it["frag"]}</div>{notes}</section>')
    name = root.name
    deck_html = (f'<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>{E(name)}({LEVELS[lv]})</title>'
                 f'<style>{DECK_CSS}{CSS}</style></head><body>{secs}</body></html>')
    hpath = out / 'deck.html'
    hpath.write_text(re.sub(r'<!--badge:[^>]*-->', '', deck_html), encoding='utf-8')
    if a.pdf:
        jobs['pdf'] = {'html': str(hpath), 'out': str(out / 'deck.pdf'), 'width': W, 'height': H}
    jf, rf = out / '.jobs.json', out / '.results.json'
    jf.write_text(json.dumps(jobs, ensure_ascii=False), encoding='utf-8')
    res = subprocess.run(['node', str(HERE / 'render_shot.js'), str(jf), str(rf)], capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit('描けない: ブラウザ(Playwright の Chromium)での描画に失敗した\n' + res.stderr[-2000:])
    browser = json.loads(rf.read_text(encoding='utf-8'))
    jf.unlink()
    rf.unlink()
    # 診断をまとめる
    per = {}
    for it in seq:
        sid, ctx = it['id'], it['ctx']
        if it not in rendered:
            if sid in old:
                per[sid] = dict(old[sid], no=it['no'])
            continue
        br = browser.get(sid) or {}
        ds = list(ctx.diags) + [{'slide': sid, **d} for d in br.get('diagnostics', [])]
        hues = sorted({c for c in ctx.colors_used if not is_gray(c)})
        adj = [round(contrast(x, y), 2) for x, y in ctx.adjacent if x != y]
        per[sid] = {
            'id': sid, 'no': it['no'], 'kind': it['kind'], 'chapter': it['chapter'], 'mode': getattr(ctx, 'mode', None),
            'spec': deck.spec_file.get(sid), 'type': getattr(ctx, 'type', None), 'file': f'slides/{it["file"]}',
            'title': br.get('titles', []), 'point': br.get('points', []),
            'colors': {'text_contrast_min': br.get('text_contrast_min'), 'adjacent_contrast_min': min(adj) if adj else None, 'hues': len(hues)},
            'emphasis': sorted(ctx.ems), 'notes': getattr(ctx, 'notes', ''), 'inputs_hash': digest,
            'diagnostics': ds, 'wraps': ctx.wraps,
        }
    ordered = [per[it['id']] for it in seq if it['id'] in per]
    allds = [d for s in ordered for d in s['diagnostics']]
    summary = {k: sum(1 for d in allds if d['severity'] == k) for k in ('error', 'warning', 'info')}
    dpath.write_text(json.dumps({
        'tool': 'tools/render.py', 'level': lv, 'inputs_hash': digest, 'count': len(seq),
        'measures': ['text-contrast', 'adjacent-contrast', 'hue-count'], 'patterns': sorted(RENDERERS),
        'pdf': 'deck.pdf' if a.pdf else None, 'summary': summary, 'slides': ordered}, ensure_ascii=False, indent=1), encoding='utf-8')
    if a.show_ids:
        def badge(m):
            n = len([d for d in per.get(html.unescape(m.group(1)), {}).get('diagnostics', []) if d['severity'] == 'error'])
            return f' <span class="bad">診断 {n}件</span>' if n else ''
        hpath.write_text(re.sub(r'<!--badge:([^>]*)-->', badge, deck_html), encoding='utf-8')
    # 標準出力
    kinds = {}
    for it in seq:
        kinds[it['kind']] = kinds.get(it['kind'], 0) + 1
    print(f'{LEVELS[lv]}: 描いた {len(rendered)} 枚(全体 {len(seq)} 枚: ' + '、'.join(f'{k} {n}' for k, n in kinds.items()) + f') → {out}')
    for s in ordered:
        for d in s['diagnostics']:
            if d['severity'] == 'info' and lv != 'full':
                continue
            tgt = f' [{d["target"]}]' if d.get('target') else ''
            print(f'{d["severity"]:7s} {s["no"]:3d} {s["id"]:16s} {d["kind"]:16s}{tgt} {d["message"]}')
    print(f'診断: エラー {summary["error"]}、警告 {summary["warning"]}、情報 {summary["info"]}')
    print(hpath)
    if a.pdf:
        print(out / 'deck.pdf')
    return 1 if summary['error'] else 0


if __name__ == '__main__':
    sys.exit(main())
