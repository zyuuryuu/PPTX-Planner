#!/usr/bin/env python3
"""機械の検査。検査の台帳(docs/checks.yaml)のIDごとに、成果物を検査する。

使い方:
  python3 tools/check.py <資料のディレクトリ> --stage N        工程Nの機械の検査
  python3 tools/check.py <資料のディレクトリ> --task <作業のid>  工程表の機械の作業の検査
  python3 tools/check.py <資料のディレクトリ> --id K04-03       検査1件
  python3 tools/check.py <資料のディレクトリ>                   工程0から8の全て
  python3 tools/check.py --coverage                            台帳の機械の検査の、実装の状況
  python3 tools/check.py --records <資料のディレクトリ>          検査の記録と実行の記録の書式を確かめる

  --chapter <章のID>  工程7の検査を、その章のスライドに限る。付録は appendix
  --write             結果を検査の記録(checks/)に書き、状態の記録(status.yaml)を更新する
  --json              結果をJSONで出す
  -v                  合格の行も出す

終了コード: 不合格か書式の誤りがあれば1。警告だけなら0。引数の誤りは2。

検査の条件は、台帳の check の文と、defined_in が指す文書の定めだけから実装している。
台帳にない確かめ(YAMLの書式、必須の項目、IDの参照先)は、「書式」として別に出す。
依存: Python 3 の標準ライブラリと PyYAML。
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from fractions import Fraction
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
DOCS = HERE.parent / "docs"

VERDICT_JA = {"pass": "合格", "fail": "不合格", "warning": "警告"}


def as_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def dicts(x):
    return [i for i in as_list(x) if isinstance(i, dict)]


def text_of(x):
    return x if isinstance(x, str) else "" if x is None else str(x)


def short(x, n=60):
    s = text_of(x).replace("\n", " ")
    return s if len(s) <= n else s[: n - 1] + "…"


# ---------------------------------------------------------------- 正本(docs)から読むもの

def read_doc(name):
    return (DOCS / name).read_text(encoding="utf-8")


def md_table(name, heading):
    """文書の見出しの下にある最初の表を、行ごとの辞書の一覧で返す。"""
    lines = read_doc(name).split("\n")
    rows, header, inside = [], None, False
    for line in lines:
        if re.match(r"^#{1,6} ", line):
            if inside and header:
                break
            inside = line.lstrip("#").strip() == heading
            continue
        if not inside:
            continue
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if header is None:
                header = cells
            elif not all(re.fullmatch(r":?-+:?", c) for c in cells):
                rows.append(dict(zip(header, cells)))
        elif header:
            break
    return rows


def ticks(cell):
    return re.findall(r"`([^`]+)`", cell)


_cache = {}


def cached(fn):
    def wrapper():
        if fn.__name__ not in _cache:
            _cache[fn.__name__] = fn()
        return _cache[fn.__name__]
    return wrapper


@cached
def ledger():
    data = yaml.safe_load(read_doc("checks.yaml"))
    return {e["id"]: e for e in data["checks"]}


@cached
def tasks():
    data = yaml.safe_load(read_doc("tasks.yaml"))
    return {t["id"]: t for t in data["tasks"]}


def is_machine(entry):
    return "machine" in as_list(entry.get("judge")) and "refers" not in entry


def is_warning(cid):
    return ledger().get(cid, {}).get("level") == "warning"


def stages_of(entry):
    return as_list(entry.get("stage"))


@cached
def relations_vocab():
    return {t for r in md_table("vocabulary.md", "主張の種類の語彙") for t in ticks(r.get("識別子", ""))}


@cached
def implications_vocab():
    return {t for r in md_table("visual-grammar.md", "含意の語彙") for t in ticks(r.get("識別子", ""))}


@cached
def scenario_ids():
    return [t for r in md_table("stages/08-integration.md", "場面と読み方") for t in ticks(r.get("識別子", ""))]


@cached
def finding_kinds():
    return {t for r in md_table("stages/08-integration.md", "通読で見つけるもの") for t in ticks(r.get("識別子", ""))}


@cached
def brief_items():
    return [r["項目"] for r in md_table("stages/00-brief.md", "成果物")]


@cached
def roles_vocab():
    return {t for r in md_table("vocabulary.md", "要点のないスライド") for t in ticks(r.get("識別子", ""))}


@cached
def point_positions():
    return {t for r in md_table("stages/06-patterns.md", "要点の位置") for t in ticks(r.get("識別子", ""))}


@cached
def bundled_deck_types():
    """docs/deck-types.md の「付属する定義」の定義。名前と id で引く。"""
    text = read_doc("deck-types.md")
    part = text.split("## 付属する定義", 1)[-1]
    found = {}
    for m in re.finditer(r"^### (.+?)\n+```yaml\n(.*?)```", part, re.S | re.M):
        d = yaml.safe_load(m.group(2))
        if isinstance(d, dict) and d.get("id"):
            d["name"] = m.group(1).strip()
            found[d["id"]] = d
    return found


@cached
def bundled_patterns():
    """docs/patterns.md の「付属する型の候補」の表。expresses は表にない。"""
    found = {}
    for r in md_table("patterns.md", "付属する型の候補"):
        ids = ticks(r.get("識別子", ""))
        if not ids:
            continue
        found[ids[0]] = {
            "id": ids[0],
            "group": r.get("区分", ""),
            "base": "image" if r.get("土台", "") == "画像" else "none",
            "implies": ticks(r.get("形が伝える含意", "")),
        }
    return found


# ---------------------------------------------------------------- 成果物

BRIEF = "00-brief.md"
STYLE = "style.yaml"
HYPS = "01-hypotheses.yaml"
PLAN = "01-plan.yaml"
SOURCES = "01-sources.yaml"
MODEL = "01-model.yaml"
ANSWERS = "02-answers.yaml"
CLAIMS = "02-claims.yaml"
CHAPTERS = "03-chapters.yaml"
STORY = "04-storyline.yaml"
STATES = "04-chapter-states.yaml"
SCENARIOS = "04-scenarios.yaml"
PROOF = "05-proof.yaml"
PATTERNS = "06-patterns.yaml"
SAMPLES = "06-samples/"
SLIDES = "07-slides/"
TERMS = "terms.yaml"
STATUS = "status.yaml"
DECISIONS = "decisions.md"
DECK_TYPE_FILE = "definitions/deck-type.yaml"
PATTERN_DEFS_FILE = "definitions/patterns.yaml"

# 描画の結果(tools/render.py の出力)の置き場。None なら <資料のディレクトリ>/build。--build で変える。
BUILD_DIR = None
DIAGNOSTICS = "diagnostics.json"
# 描画が読む成果物。描画上の診断が今の成果物のものかを、要約値で確かめる(tools/render.py の inputs_hash と同じ計算)。
RENDER_INPUT_FILES = [BRIEF, STYLE, TERMS, SOURCES, MODEL, CHAPTERS, STORY, PROOF, PATTERNS]
RENDER_INPUT_DIRS = ["definitions", "06-samples", "07-slides"]

# 成果物ごとの、作る工程と最上位の型。
ARTIFACTS = {
    BRIEF: (0, None), STYLE: (0, dict),
    HYPS: (1, list), PLAN: (1, list), SOURCES: (1, list), MODEL: (1, dict), TERMS: (1, dict),
    ANSWERS: (2, list), CLAIMS: (2, dict),
    CHAPTERS: (3, dict),
    STORY: (4, list), STATES: (4, list), SCENARIOS: (4, list),
    PROOF: (5, list),
    PATTERNS: (6, list), SAMPLES: (6, None),
    SLIDES: (7, None),
}
OPTIONAL = {MODEL}

FACT_KINDS = {"fact", "derived", "testimony", "image", "inference", "opinion"}
USABLE_KINDS = {"fact", "derived", "testimony", "image"}
RESULTS = {"answered", "partial", "not-found", "disputed"}
STANCES = {"supports", "contradicts", "neutral"}
BRIEF_STATES = {"確定", "推定", "未定"}


class Deck:
    """資料のディレクトリ。成果物を読み、読めなかったものを覚える。"""

    def __init__(self, root, chapter=None):
        self.root = Path(root)
        self.chapter = chapter
        self._data = {}
        self.broken = {}      # 名前 -> 理由

    # -- 読み込み

    def exists(self, name):
        return (self.root / name).exists()

    def load(self, name):
        if name in self._data:
            return self._data[name]
        path, data = self.root / name, None
        kind = ARTIFACTS.get(name, (None, None))[1]
        if path.is_file():
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
            except yaml.YAMLError as e:
                mark = getattr(e, "problem_mark", None)
                where = f"{mark.line + 1}行{mark.column + 1}列" if mark else ""
                self.broken[name] = f"YAMLとして読めない {where}".strip()
            else:
                if kind and not isinstance(data, kind):
                    self.broken[name] = "最上位が" + ("並び" if kind is list else "項目の集まり") + "でない"
                    data = None
        self._data[name] = data
        return data

    def load_dir(self, name):
        """ディレクトリの中の YAML を、ファイル名 -> スライド仕様の並び で返す。"""
        if name in self._data:
            return self._data[name]
        out = {}
        base = self.root / name
        if base.is_dir():
            for path in sorted(base.glob("*.yaml")):
                rel = name + path.name
                try:
                    data = yaml.safe_load(path.read_text(encoding="utf-8"))
                except yaml.YAMLError:
                    self.broken[rel] = "YAMLとして読めない"
                    continue
                if not isinstance(data, list):
                    self.broken[rel] = "最上位が並びでない"
                    continue
                out[rel] = dicts(data)
        self._data[name] = out
        return out

    def text(self, name):
        path = self.root / name
        return path.read_text(encoding="utf-8") if path.is_file() else None

    # -- 描画の結果

    def inputs_hash(self):
        if "inputs_hash" not in self._data:
            files = [self.root / n for n in RENDER_INPUT_FILES]
            for sub in RENDER_INPUT_DIRS:
                files += sorted((self.root / sub).glob("*.yaml")) if (self.root / sub).is_dir() else []
            h = hashlib.sha1()
            for f in files:
                if f.is_file():
                    h.update(f.relative_to(self.root).as_posix().encode("utf-8") + b"\0" + f.read_bytes() + b"\0")
            self._data["inputs_hash"] = h.hexdigest()
        return self._data["inputs_hash"]

    def diagnostics(self, sub=None):
        """描画上の診断(tools/render.py が書く diagnostics.json)。(全体, スライドのID -> 1件, 表示する置き場, 読めない理由) を返す。"""
        key = "diagnostics/" + (sub or "")
        if key not in self._data:
            base = Path(BUILD_DIR) if BUILD_DIR else self.root / "build"
            path = (base / sub if sub else base) / DIAGNOSTICS
            shown = "build/" + (sub + "/" if sub else "") + DIAGNOSTICS
            doc, problem = None, None
            how = "python3 tools/render.py <資料のディレクトリ>" + (" --samples" if sub == "samples" else "")
            if not path.is_file():
                problem = f"描画の結果がない。先に描く({how})"
            else:
                try:
                    doc = json.loads(path.read_text(encoding="utf-8"))
                except ValueError:
                    doc = None
                if not isinstance(doc, dict) or not isinstance(doc.get("slides"), list):
                    doc, problem = None, f"描画上の診断を読めない。描き直す({how})"
            slides = {e.get("id"): e for e in (doc or {}).get("slides", []) if isinstance(e, dict)}
            self._data[key] = (doc, slides, shown, problem)
        return self._data[key]

    def diagnosed(self, R, sub, sid):
        """スライド1枚の描画上の診断。ない場合と、今の成果物より古い場合は、不合格を書いて None を返す。"""
        doc, slides, shown, problem = self.diagnostics(sub)
        if problem:
            R.ng(sid, shown, problem)
            return None
        e = slides.get(sid)
        if e is None:
            R.ng(sid, shown, "このスライドの描画上の診断がない。描き直す")
            return None
        if e.get("inputs_hash") != self.inputs_hash():
            R.ng(sid, shown, "描画の結果が、今の成果物より古い。描き直す")
            return None
        return e

    # -- ブリーフ

    @property
    def brief(self):
        """項目の名前 -> {state, attrs: [(名前, 値)], body}。書式は tools/README.md に定める。"""
        if "brief" in self._data:
            return self._data["brief"]
        text, items, cur = self.text(BRIEF), {}, None
        if text is not None:
            for line in text.split("\n"):
                if line.startswith("## "):
                    cur = {"state": None, "attrs": [], "body": []}
                    items[line[3:].strip()] = cur
                elif cur is not None:
                    m = re.match(r"^- ([^:：]+)[:：]\s*(.*)$", line)
                    if m:
                        key, value = m.group(1).strip(), m.group(2).strip()
                        if key == "状態":
                            cur["state"] = value
                        else:
                            cur["attrs"].append((key, value))
                    elif line.strip():
                        cur["body"].append(line.strip())
        self._data["brief"] = items if text is not None else None
        return self._data["brief"]

    def brief_attrs(self, item, key):
        b = self.brief or {}
        return [v for k, v in b.get(item, {}).get("attrs", []) if k == key]

    # -- 型の定義

    @property
    def deck_type(self):
        """ブリーフで選んだ資料の型の定義。決められなければ None。"""
        if "deck_type" in self._data:
            return self._data["deck_type"]
        found = None
        local = self.root / DECK_TYPE_FILE
        if local.is_file():
            try:
                d = yaml.safe_load(local.read_text(encoding="utf-8"))
                found = d if isinstance(d, dict) else None
            except yaml.YAMLError:
                found = None
        elif self.brief and "資料の型" in self.brief:
            body = " ".join(self.brief["資料の型"]["body"])
            hits = [d for d in bundled_deck_types().values() if d["id"] in body or d["name"] in body]
            if len(hits) == 1:
                found = hits[0]
        self._data["deck_type"] = found
        return found

    @property
    def pattern_defs(self):
        """型の定義。docs/patterns.md の表に、資料の定義(definitions/patterns.yaml)を重ねる。"""
        if "pattern_defs" in self._data:
            return self._data["pattern_defs"]
        defs = {k: dict(v) for k, v in bundled_patterns().items()}
        local = self.root / PATTERN_DEFS_FILE
        if local.is_file():
            try:
                for d in dicts(yaml.safe_load(local.read_text(encoding="utf-8"))):
                    if d.get("id"):
                        merged = dict(defs.get(d["id"], {}))
                        merged.update(d)
                        defs[d["id"]] = merged
            except yaml.YAMLError:
                self.broken[PATTERN_DEFS_FILE] = "YAMLとして読めない"
        self._data["pattern_defs"] = defs
        return defs

    # -- よく使う引き方

    @property
    def style(self):
        return self.load(STYLE) or {}

    def limit(self, key):
        v = (self.style.get("limits") or {}).get(key) if isinstance(self.style.get("limits"), dict) else None
        return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None

    @property
    def facts(self):
        return {f["id"]: f for f in dicts(self.load(SOURCES)) if "id" in f}

    @property
    def plan(self):
        return {q["id"]: q for q in dicts(self.load(PLAN)) if "id" in q}

    def children(self, qid):
        return [q["id"] for q in self.plan.values() if q.get("parent") == qid]

    def leaves(self):
        return [q for q in self.plan.values() if not self.children(q["id"])]

    def depth(self, qid):
        n, seen = 0, set()
        while qid in self.plan and self.plan[qid].get("parent") is not None and qid not in seen:
            seen.add(qid)
            qid = self.plan[qid]["parent"]
            n += 1
        return n

    def descendants(self, qid):
        out, todo = set(), [qid]
        while todo:
            for c in self.children(todo.pop()):
                if c not in out:
                    out.add(c)
                    todo.append(c)
        return out

    @property
    def answers(self):
        return {a["question"]: a for a in dicts(self.load(ANSWERS)) if "question" in a}

    def answer_evidence(self, qid, seen=None):
        """答えの根拠の事実。from でたどった子の答えの根拠を含める。"""
        seen = seen if seen is not None else set()
        if qid in seen or qid not in self.answers:
            return []
        seen.add(qid)
        a = self.answers[qid]
        out = list(as_list(a.get("evidence")))
        for sub in as_list(a.get("from")):
            out += self.answer_evidence(sub, seen)
        return out

    @property
    def claims_doc(self):
        return self.load(CLAIMS) or {}

    @property
    def claims(self):
        return {c["id"]: c for c in dicts(self.claims_doc.get("claims")) if "id" in c}

    @property
    def chapters(self):
        return dicts((self.load(CHAPTERS) or {}).get("chapters"))

    @property
    def sections(self):
        """節のID -> (章, 節)。"""
        return {s["id"]: (ch, s) for ch in self.chapters for s in dicts(ch.get("sections")) if "id" in s}

    @property
    def story(self):
        return dicts(self.load(STORY))

    @property
    def story_by_id(self):
        return {s["id"]: s for s in self.story if "id" in s}

    @property
    def proof(self):
        return {p["id"]: p for p in dicts(self.load(PROOF)) if "id" in p}

    @property
    def model(self):
        return self.load(MODEL) or {}

    def model_ids(self, key):
        return {e["id"]: e for e in dicts(self.model.get(key)) if "id" in e}

    @property
    def terms_doc(self):
        return self.load(TERMS) or {}

    @property
    def terms(self):
        return dicts(self.terms_doc.get("terms"))

    @property
    def table(self):
        return dicts(self.load(PATTERNS))

    def slide_specs(self, chapter=None):
        """(ファイル名, スライド仕様) の一覧。章を指定すると、その章のスライドに限る。"""
        chapter = chapter if chapter is not None else self.chapter
        out = []
        for name, specs in self.load_dir(SLIDES).items():
            for s in specs:
                if chapter is None or self.story_by_id.get(s.get("id"), {}).get("chapter") == chapter:
                    out.append((name, s))
        return out

    def has_point(self, slide):
        return isinstance(slide.get("point"), str) or slide.get("point_from") is not None

    def all_ids(self):
        """資料の中の全てのID。内部のIDの検査と、参照の検査に使う。"""
        ids = set(self.facts) | set(self.plan) | set(self.claims) | set(self.sections) | set(self.story_by_id)
        ids |= {h.get("id") for h in dicts(self.load(HYPS))}
        ids |= {c.get("id") for c in self.chapters}
        ids |= {t.get("id") for t in self.terms}
        for key in ("elements", "relations", "scenarios"):
            ids |= set(self.model_ids(key))
        return {i for i in ids if isinstance(i, str)}


# ---------------------------------------------------------------- 数値

SCALES = {"千": 10 ** 3, "万": 10 ** 4, "億": 10 ** 8, "兆": 10 ** 12}
UNITS = [
    "%", "パーセント", "ポイント", "倍", "円", "ドル", "年度", "年間", "年", "か月", "カ月", "ヶ月", "ヵ月", "月",
    "週間", "週", "日間", "日", "時間", "時台", "時", "分", "秒", "件", "人", "社", "枚", "個", "回", "割", "台",
    "点", "位", "名", "本", "つ", "歳", "種類", "種", "章", "節", "項", "行", "文", "字", "語", "桁", "段", "番",
    "号", "版", "km", "cm", "mm", "kg", "GB", "MB", "px", "pt",
]
NUMBER = re.compile(r"(?<![A-Za-z0-9.,_-])\d[\d,]*(?:\.\d+)?")
NUMBER_AT = re.compile(r"\d[\d,]*(?:\.\d+)?")


def norm_unit(u):
    u = unicodedata.normalize("NFKC", text_of(u)).strip()
    return "%" if u == "パーセント" else u


def split_unit(value, unit):
    """value と unit の組を、桁の語(兆、億、万、千)を掛けた値と、残りの単位にする。"""
    u = norm_unit(unit)
    v = Fraction(str(value))
    if len(u) > 1 and u[0] in SCALES:
        return v * SCALES[u[0]], u[1:]
    return v, u


def quantities(text, units):
    """文の中の数値を、(値, 単位, 元の表記) の一覧で返す。全角と半角、桁区切り、桁の語を正規化する。"""
    s = unicodedata.normalize("NFKC", text_of(text))
    out, pos = [], 0
    while True:
        m = NUMBER.search(s, pos)
        if not m:
            return out
        start, pos, total = m.start(), m.end(), Fraction(0)
        cur = m
        while True:
            n = Fraction(cur.group().replace(",", ""))
            if pos < len(s) and s[pos] in SCALES:
                total += n * SCALES[s[pos]]
                pos += 1
                cur = NUMBER_AT.match(s, pos)
                if cur:
                    pos = cur.end()
                    continue
            else:
                total += n
            break
        unit = next((u for u in units if s.startswith(u, pos)), "")
        pos += len(unit)
        out.append((total, norm_unit(unit), s[start:pos]))


def fmt_q(q):
    return q[2] if len(q) > 2 else f"{q[0]}{q[1]}"


class Numbers:
    """数値の照合。単位の一覧は、決めた一覧に、素材台帳の unit を足して作る。"""

    def __init__(self, deck):
        extra = set()
        for f in deck.facts.values():
            if f.get("unit") is not None:
                u = norm_unit(f["unit"])
                extra.add(u)
                if len(u) > 1 and u[0] in SCALES:
                    extra.add(u[1:])
        self.units = sorted(set(UNITS) | {u for u in extra if u}, key=len, reverse=True)
        self.deck = deck

    def of_text(self, text):
        return quantities(text, self.units)

    def of_fact(self, fact):
        """事実の値。value と unit の組と、statement、quote、qualifiers に書かれた数値。"""
        found = set()
        if isinstance(fact.get("value"), (int, float)) and not isinstance(fact.get("value"), bool):
            found.add(split_unit(fact["value"], fact.get("unit")))
        for part in [fact.get("statement"), fact.get("quote")] + as_list(fact.get("qualifiers")):
            found |= {(v, u) for v, u, _ in self.of_text(part)}
        return found

    def of_facts(self, ids):
        found = set()
        for i in ids:
            if i in self.deck.facts:
                found |= self.of_fact(self.deck.facts[i])
        return found

    def missing(self, text, allowed):
        return [q for q in self.of_text(text) if (q[0], q[1]) not in allowed]


# ---------------------------------------------------------------- 文

KANJI = "一-龥々〆ヶ"
HIRA = "ぁ-ゖ"
ID_PATTERNS = [
    r"[FACHD]\d+", r"Q\d+(?:\.\d+)*", r"[TERS]-[A-Za-z0-9][A-Za-z0-9-]*", r"R\d{2,}",
    r"ch\d+(?:-s?\d+)?", r"ap-s\d+", r"K(?:\d\d|X)-\d\d",
]
ID_RE = re.compile(r"(?<![A-Za-z0-9_-])(?:" + "|".join(ID_PATTERNS) + r")(?![A-Za-z0-9_-])")
REF_RE = re.compile(r"\{([^{}]*)\}")
# 題が名詞で終わらないと言い切れる文末。形態素解析をしないため、これに当たらない題は名詞で終わるとみなす。
NON_NOUN_ENDINGS = [
    "する", "した", "して", "している", "される", "された", "できる", "できた", "なる", "なった", "ある", "あった",
    "いる", "いた", "ない", "である", "であった", "です", "ます", "ました", "でした", "だ", "だった", "について",
    "により", "による", "ため", "か", "を", "が", "は", "に", "へ", "で", "と", "も", "や", "から", "まで", "より",
    "れる", "せる", "える", "った", "えた", "びた", "んだ", "いく", "くる",
]
BAD_POINT_ENDINGS = ["がわかる", "が分かる", "について", "すべき"]
STRICT_KINDS = {"summary", "claim", "title", "point"}


class Text:
    """読み手に見せる文の1件。"""

    def __init__(self, artifact, item, field, kind, value):
        self.artifact, self.item, self.field, self.kind, self.value = artifact, item, field, kind, value

    @property
    def where(self):
        return f"{self.item} {self.field}" if self.item else self.field


def sentences(s):
    return [p for p in re.split(r"[。！？!?\n]", s) if p.strip()]


def body_strings(body, known_ids):
    """スライド仕様の中身から、読み手が目にする文を取り出す。型の名前、要素や素材を指す項目、IDだけの値は除く。"""
    out = []

    def walk(x, path):
        if isinstance(x, str):
            if x not in known_ids:
                out.append((path, x))
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, f"{path}[{i}]")
        elif isinstance(x, dict):
            for k, v in x.items():
                walk(v, f"{path}.{k}")

    if isinstance(body, dict):
        for key, value in body.items():
            if key not in ("type", "highlight", "asset", "crop", "scenario"):
                walk(value, f"body.{key}")
    return out


def stage_texts(deck, stage):
    """工程ごとの、読み手に見せる文。"""
    out = []
    if stage == 2:
        doc = deck.claims_doc
        if isinstance(doc.get("answer"), str):
            out.append(Text(CLAIMS, None, "answer", "claim", doc["answer"]))
        if isinstance(doc.get("summary"), str):
            out.append(Text(CLAIMS, None, "summary", "summary", doc["summary"]))
        for c in deck.claims.values():
            if isinstance(c.get("statement"), str):
                out.append(Text(CLAIMS, c["id"], "statement", "claim", c["statement"]))
    elif stage == 3:
        for ch in deck.chapters:
            for unit in [ch] + dicts(ch.get("sections")):
                for field in ("title", "point"):
                    if isinstance(unit.get(field), str):
                        out.append(Text(CHAPTERS, unit.get("id"), field, field, unit[field]))
    elif stage == 4:
        for s in deck.story:
            for field in ("title", "point"):
                if isinstance(s.get(field), str):
                    out.append(Text(STORY, s.get("id"), field, field, s[field]))
    elif stage == 7:
        known = deck.all_ids()
        for f in deck.facts.values():
            known |= {r.get("id") for r in dicts(f.get("regions"))}
        for name, s in deck.slide_specs():
            for field, kind in (("title", "title"), ("point", "point"), ("text", "text"), ("notes", "notes")):
                if isinstance(s.get(field), str):
                    out.append(Text(name, s.get("id"), field, kind, s[field]))
            for path, value in body_strings(s.get("body"), known):
                out.append(Text(name, s.get("id"), path, "body", value))
    return out


def strip_refs(s):
    return REF_RE.sub("", s)


class Vocabulary:
    """使う語彙の照合。形態素解析をしない。登録した語を文から消し、残った漢字、カタカナ、英字の並びを、登録のない語とする。"""

    def __init__(self, deck):
        doc = deck.terms_doc
        self.terms = [t["term"] for t in deck.terms if isinstance(t.get("term"), str)]
        names = [e["name"] for e in deck.model_ids("elements").values() if isinstance(e.get("name"), str)]
        self.allowed = [a for a in as_list(doc.get("allowed")) if isinstance(a, str)]
        self.banned = [b["term"] for b in dicts(doc.get("banned")) if isinstance(b.get("term"), str)]
        self.words = sorted(set(self.terms + names + self.allowed), key=len, reverse=True)
        stems = set()
        for w in self.words:
            m = re.match(rf"^(.*[^{HIRA}])[{HIRA}]+$", w)
            if m:
                stems.add(m.group(1))
        self.stems = sorted(stems, key=len, reverse=True)
        self.units = Numbers(deck).units

    def mask(self, s, stems=True):
        s = strip_refs(s)
        for w in self.words:
            s = s.replace(w, "\0")
        if stems:
            for w in self.stems:
                s = re.sub(re.escape(w) + rf"(?=[{HIRA}]|$)", "\0", s)
        return s

    def unknown(self, s):
        masked = self.mask(s)
        for _, _, raw in quantities(masked, self.units):
            masked = masked.replace(raw, "\0", 1)
        masked = re.sub(r"\d[\d,.]*", "\0", masked)
        return re.findall(rf"[{KANJI}]+|[ァ-ヴー]+|[A-Za-z][A-Za-z0-9-]*", masked)

    def banned_in(self, s):
        masked = self.mask(s, stems=False)
        return [b for b in self.banned if b in masked]

    def variants(self, s):
        """語彙表の語の、表記の揺れ。長音の有無、全角と半角、漢字の間の送り仮名を正規化して比べる。"""
        found = []
        plain = strip_refs(s)

        def norm(x):
            return unicodedata.normalize("NFKC", x).replace("ー", "")

        for t in self.terms:
            if norm(t) and norm(plain).count(norm(t)) > plain.count(t):
                found.append(t)
                continue
            kanji = [c for c in t if re.match(rf"[{KANJI}]", c)]
            if len(kanji) < 2:
                continue
            first = t.index(kanji[0])
            last = len(t) - t[::-1].index(kanji[-1])
            kernel = t[first:last]
            pattern = f"[{HIRA}]{{0,2}}".join(re.escape(c) for c in kernel if not re.match(rf"[{HIRA}]", c))
            if not re.fullmatch(pattern, kernel):      # 間のひらがなが長い語は、句であり、送り仮名の揺れを見ない
                continue
            if any(m.group() != kernel for m in re.finditer(pattern, plain)):
                found.append(t)
        return found


# ---------------------------------------------------------------- 結果

class Report:
    def __init__(self):
        self.rows = []

    def add(self, cid, artifact, item, verdict, quote, reason=None):
        self.rows.append({"check": cid, "artifact": artifact, "item": item, "verdict": verdict,
                          "quote": short(quote, 120) or "(空)", "reason": reason})

    def of(self, cid, artifact):
        return Bound(self, cid, artifact)


class Bound:
    """検査1件と成果物1つに結んだ、結果の書き手。"""

    def __init__(self, report, cid, artifact):
        self.report, self.cid, self.artifact = report, cid, artifact

    def ok(self, item, quote):
        self.report.add(self.cid, self.artifact, item, "pass", quote)

    def ng(self, item, quote, reason):
        self.report.add(self.cid, self.artifact, item, "fail", quote, reason)

    def judge(self, cond, item, quote, reason):
        (self.ok(item, quote) if cond else self.ng(item, quote, reason))


CHECKS = {}        # 検査のID -> (関数, 読む成果物, 一部だけ実装の説明)
FUNCTIONS = []     # (関数, IDの一覧, 読む成果物)


def check(*ids, needs=(), partial=None):
    def deco(fn):
        FUNCTIONS.append((fn, ids, needs))
        for cid in ids:
            CHECKS[cid] = (fn, needs, (partial or {}).get(cid) if isinstance(partial, dict) else partial)
        return fn
    return deco


# 実装していない機械の検査と、その理由。理由の先頭の語が、分類である。
R_RENDER = "描画の結果が要る"
R_FORMAT = "書式や置き場が未定義"
R_VALUE = "上限や辞書が未確定"
R_MORPH = "形態素解析が要る"
R_AMBIG = "条件が機械で1つに決まらない"
R_EXTERNAL = "GitやIssueの状態が要る"
TODO = {
    "K00-07": (R_FORMAT, "資料の型の定義の limits が null で、個人の表現規約の置き場がない。写したことを確かめられない"),
    "K01-07": (R_FORMAT, "formula の書式がない"),
    "K01-23": (R_FORMAT, "引用元の表記に必要な情報の項目がない"),
    "K02-13": (R_AMBIG, "「主張に明記する」を確かめる項目がない"),
    "K02-14": (R_AMBIG, "条件が合否の形でない。ユーザーに示したことの記録の置き場がない"),
    "K04-17": (R_VALUE, "接続の語の一覧が「など」で終わり、定まらない"),
    "K05-06": (R_AMBIG, "「該当する種類の要素」を決める定めがない"),
    "K06-05": (R_FORMAT, "収容量を超える理由の置き場がない。収容量の値も未確定"),
    "K06-08": (R_FORMAT, "資料に共通の規則を style.yaml に書く項目の名前がない"),
    "K06-09": (R_FORMAT, "色の割り当ての書式と、図に出る対象の引き方がない"),
    "K06-17": (R_FORMAT, "候補とユーザーの判断の記録の置き場がない"),
    "K06-19": (R_FORMAT, "banned に入れるかを決めた記録の置き場がない"),
    "K07-10": (R_EXTERNAL, "章のブランチと、比べる元の版の指定が要る"),
    "K07-18": (R_RENDER, "印と説明を置いた位置が要る"),
    "K07-23": (R_VALUE, "型の収容量の値と、項目との対応が未確定"),
    "K07-30": (R_FORMAT, "色の割り当ての書式と、図や表のデータの中の対象の引き方がない"),
    "K07-31": (R_FORMAT, "色の割り当ての書式がない"),
    "K07-32": (R_FORMAT, "グラフの軸の範囲を書く項目がない"),
    "K07-33": (R_FORMAT, "グラフの軸と構成比のデータの書式がない"),
    "K07-35": (R_VALUE, "型の収容量の値が未確定"),
    "K07-36": (R_FORMAT, "アイコンを書く項目がない"),
    "K07-37": (R_VALUE, "型の収容量の値が未確定"),
    "K07-39": (R_VALUE, "言い回しと文型の数え方と、目安の値が未確定"),
    "K07-42": (R_EXTERNAL, "重大度はIssueにある。到達点のうち語のほかの項目を、実行の記録と照合する方法がない"),
    "K08-05": (R_RENDER, "ビルドした実物から抜き出した枚数、題、要点が要る"),
    "K08-06": (R_RENDER, "ビルドした実物の中の語の並びが要る"),
    "K08-07": (R_FORMAT, "要約のスライドの仕様のファイル名がない。章のまとめと節のまとめは、ビルドが組み立てる"),
    "K08-08": (R_FORMAT, "要約に添えた根拠の書式がない"),
    "K08-10": (R_AMBIG, "つなぎ目を「通った」と判定する定めがない"),
    "K08-11": (R_EXTERNAL, "Issueの状態が要る"),
    "K08-13": (R_FORMAT, "検査の報告 09-report.md の書式がない"),
    "K09-01": (R_RENDER, "最終の出力の診断が要る"),
    "K09-03": (R_RENDER, "最終の出力から抜き出した枚数、題、要点が要る"),
    "K09-04": (R_RENDER, "最終の出力の目次、ページ番号、言及が要る"),
    "K09-05": (R_RENDER, "最終の出力から抜き出した文字が要る"),
    "K09-06": (R_RENDER, "最終の出力の出典の一覧が要る"),
    "K09-07": (R_RENDER, "最終の出力から抜き出した文字が要る"),
    "K09-08": (R_RENDER, "最終の出力のノートが要る"),
    "K09-09": (R_RENDER, "最終の出力の付帯情報が要る。表現規約の書式もない"),
    "K09-10": (R_VALUE, "話す速さの値が未確定。最終の出力のノートが要る"),
    "K09-11": (R_FORMAT, "検査の報告 09-report.md の書式がない"),
    "K09-12": (R_FORMAT, "集計の記録 metrics.yaml の書式がない"),
    "KX-01": (R_VALUE, "項目の種類ごとの字数の上限の値と、置く項目の名前が未確定"),
    "KX-03": (R_MORPH, "助詞の見分けが要る。連続の数え方と上限も未確定"),
    "KX-05": (R_VALUE, "冗長な言い回しの辞書がない"),
    "KX-06": (R_VALUE, "中身のない形容と強調の辞書がない"),
    "KX-07": (R_VALUE, "書き出しの決まり文句の辞書がない。条件の文の例は「など」で終わる"),
    "KX-08": (R_VALUE, "LLMに多い語の辞書がない"),
    "KX-09": (R_VALUE, "ぼかしを数える範囲と、上限の値が未確定"),
    "KX-10": (R_VALUE, "割合を測る範囲と、上限の値が未確定"),
    "KX-11": (R_MORPH, "語の切り分けが要る。近い位置の範囲と上限も未確定"),
    "KX-12": (R_MORPH, "である調の文末(動詞の終止形など)の見分けが要る"),
}


# ---------------------------------------------------------------- 工程0

@check("K00-01", needs=[BRIEF])
def k00_01(d, r):
    R = r.of("K00-01", BRIEF)
    for name, item in d.brief.items():
        R.judge(item["state"] in ("確定", "未定"), name, f"状態: {item['state']}", "状態が確定でも未定でもない")


@check("K00-02", needs=[BRIEF])
def k00_02(d, r):
    R = r.of("K00-02", BRIEF)
    for name in ("主な読み手", "目的", "答えるべき問い"):
        state = d.brief.get(name, {}).get("state")
        R.judge(state == "確定", name, f"状態: {state}", "確定でない")


@check("K00-08", needs=[BRIEF], partial="画像を使わない資料でも、確定でなければ不合格とする(条件の1文目による)")
def k00_08(d, r):
    R = r.of("K00-08", BRIEF)
    state = d.brief.get("外に出せない情報", {}).get("state")
    images = [f["id"] for f in d.facts.values() if f.get("kind") == "image"]
    reason = "確定でない" + (f"。画像の素材がある({'、'.join(images)})" if images else "")
    R.judge(state == "確定", "外に出せない情報", f"状態: {state}", reason)


# ---------------------------------------------------------------- 工程1

@check("K01-01", needs=[PLAN])
def k01_01(d, r):
    R = r.of("K01-01", PLAN)
    for q in d.plan.values():
        if d.children(q["id"]):
            R.judge(bool(q.get("axis")), q["id"], f"axis: {q.get('axis')}", "枝分かれに axis がない")
        else:
            lack = [k for k in ("evidence_type", "priority") if not q.get(k)]
            R.judge(not lack, q["id"], f"evidence_type: {q.get('evidence_type')}、priority: {q.get('priority')}",
                    "末端の問いに " + "、".join(lack) + " がない")


@check("K01-02", needs=[PLAN, BRIEF])
def k01_02(d, r):
    R = r.of("K01-02", PLAN)
    if not d.deck_type:
        return R.ng(None, "資料の型", "ブリーフの「資料の型」から、資料の型の定義を1つに決められない")
    seen = {q.get("perspective") for q in d.plan.values()}
    for p in as_list(d.deck_type.get("perspectives")):
        R.judge(p in seen, p, f"perspectives: {p}", "この観点を perspective に持つ問いがない")


@check("K01-06", needs=[SOURCES])
def k01_06(d, r):
    R = r.of("K01-06", SOURCES)
    for f in d.facts.values():
        if f.get("kind") == "fact":
            lack = [k for k in ("source", "locator", "quote") if not f.get(k)]
            R.judge(not lack, f["id"], f.get("quote") or f.get("statement"), "、".join(lack) + " がない")


@check("K01-09", needs=[SOURCES])
def k01_09(d, r):
    R = r.of("K01-09", SOURCES)
    num = Numbers(d)
    for f in d.facts.values():
        if f.get("kind") != "fact" or f.get("value") is None:
            continue
        if isinstance(f["value"], bool) or not isinstance(f["value"], (int, float)):
            R.ng(f["id"], f"value: {f['value']}", "value が数値でない")
            continue
        want = split_unit(f["value"], f.get("unit"))
        got = {(v, u) for v, u, _ in num.of_text(f.get("quote"))}
        R.judge(want in got, f["id"], f.get("quote"),
                f"quote の中に、value と unit({f['value']}{text_of(f.get('unit'))})に合う数値と単位がない")


@check("K01-11", needs=[SOURCES, TERMS])
def k01_11(d, r):
    R = r.of("K01-11", SOURCES)
    known = {t.get("id") for t in d.terms} | {t.get("term") for t in d.terms}
    for f in d.facts.values():
        if f.get("value") is not None:
            m = f.get("metric")
            R.judge(bool(m) and m in known, f["id"], f"metric: {m}",
                    "metric がない" if not m else "metric が語彙表の語でない")


@check("K01-12", needs=[SOURCES, PLAN])
def k01_12(d, r):
    R = r.of("K01-12", SOURCES)
    groups = {}
    for f in d.facts.values():
        if f.get("metric") and f.get("value") is not None:
            key = (f["metric"], text_of(f.get("as_of")), tuple(sorted(map(text_of, as_list(f.get("qualifiers"))))))
            groups.setdefault(key, []).append(f)
    for key, fs in groups.items():
        values = {split_unit(f["value"], f.get("unit")) for f in fs if isinstance(f["value"], (int, float))}
        if len(values) < 2:
            continue
        ids = "、".join(f["id"] for f in fs)
        live = [f for f in fs if not f.get("superseded_by")]
        disputed = all(d.plan.get(q, {}).get("result") == "disputed" for f in live for q in as_list(f.get("answers"))) \
            and all(as_list(f.get("answers")) for f in live)
        settled = len({split_unit(f["value"], f.get("unit")) for f in live}) < 2 or disputed
        R.judge(settled, ids, f"metric: {key[0]}、as_of: {key[1]}",
                "時点と範囲が同じで値が違う。使わない事実に superseded_by がなく、該当する問いの結果も disputed でない")


@check("K01-13", needs=[SOURCES])
def k01_13(d, r):
    R = r.of("K01-13", SOURCES)
    for f in d.facts.values():
        if f.get("kind") == "testimony":
            R.judge(bool(f.get("source")), f["id"], f.get("source") or f.get("statement"), "source がない")


@check("K01-14", needs=[PLAN])
def k01_14(d, r):
    R = r.of("K01-14", PLAN)
    for q in d.leaves():
        R.judge(q.get("result") in RESULTS, q["id"], f"result: {q.get('result')}", "末端の問いに result がない")


@check("K01-16", needs=[SOURCES, HYPS])
def k01_16(d, r):
    R = r.of("K01-16", SOURCES)
    hyps = [h["id"] for h in dicts(d.load(HYPS)) if "id" in h]
    for f in d.facts.values():
        if f.get("kind") == "image":
            continue
        stance = f.get("stance") if isinstance(f.get("stance"), dict) else {}
        lack = [h for h in hyps if stance.get(h) not in STANCES]
        R.judge(not lack, f["id"], f"stance: {stance}", "、".join(lack) + " に対する stance がない")


@check("K01-17", needs=[HYPS], partial="仮説が2つ以上あることを見る。互いに対立するかは見ない")
def k01_17(d, r):
    hyps = dicts(d.load(HYPS))
    r.of("K01-17", HYPS).judge(len(hyps) >= 2, None, f"仮説 {len(hyps)}件", "仮の結論のほかに仮説がない")


@check("K01-18", needs=[PLAN], partial="終了の判断の1つ目の条件だけを見る。2つ目と3つ目は、記録の置き場がないため確かめられず、不合格とする")
def k01_18(d, r):
    R = r.of("K01-18", PLAN)
    high = [q for q in d.leaves() if q.get("priority") == "high"]
    open_ = [q["id"] for q in high if q.get("result") not in ("answered", "disputed")]
    R.judge(not open_, None, f"重要度が high の問い {len(high)}件",
            "重要度が high の問いに、answered でも disputed でもないものがある(" + "、".join(open_) +
            ")。終了の判断の残りの2つの条件は、機械で確かめられない")


@check("K01-19", needs=[SOURCES])
def k01_19(d, r):
    R = r.of("K01-19", SOURCES)
    for f in d.facts.values():
        if f.get("kind") == "image":
            ok = bool(f.get("source")) and (f.get("version") is not None or f.get("captured_at") is not None)
            R.judge(ok, f["id"], f"source: {f.get('source')}、version: {f.get('version')}、captured_at: {f.get('captured_at')}",
                    "source、または version と captured_at の両方がない")


def verified(d, ids):
    return [i for i in as_list(ids) if d.facts.get(i, {}).get("verified") is True]


@check("K01-24", "K01-28", needs=[SOURCES])
def k01_model(d, r):
    R24, R28 = r.of("K01-24", MODEL), r.of("K01-28", MODEL)
    if not d.exists(MODEL):
        R24.ok(None, "仕組みの定義がない")
        R28.ok(None, "仕組みの定義がない")
        return
    rels = d.model_ids("relations")
    for key in ("elements", "relations", "scenarios"):
        for e in d.model_ids(key).values():
            R24.judge(bool(verified(d, e.get("evidence"))), e["id"], f"evidence: {e.get('evidence')}",
                      "verified: true の事実が紐づいていない")
    for e in rels.values():
        if "summarizes" not in e:
            continue
        chain = [rels.get(i) for i in as_list(e["summarizes"])]
        ok = bool(chain) and all(chain)
        if ok:
            ok = chain[0].get("from") == e.get("from") and chain[-1].get("to") == e.get("to") and \
                all(a.get("to") == b.get("from") for a, b in zip(chain, chain[1:]))
        R28.judge(ok, e["id"], f"summarizes: {e['summarizes']}", "元のつながりを順にたどっても、このつながりの両端にならない")


# ---------------------------------------------------------------- 工程2

def unknown_answer(a):
    return text_of(a).strip().rstrip("。") == "分からない"


@check("K02-01", "K02-02", "K02-05", needs=[PLAN, ANSWERS, SOURCES])
def k02_answers(d, r):
    R1, R2, R5 = r.of("K02-01", ANSWERS), r.of("K02-02", ANSWERS), r.of("K02-05", ANSWERS)
    num = Numbers(d)
    for q in d.plan.values():
        a = d.answers.get(q["id"])
        R1.judge(bool(a and a.get("answer")), q["id"], a.get("answer") if a else q.get("question"), "この問いに答えがない")
    for q in d.leaves():
        a = d.answers.get(q["id"])
        if a and not unknown_answer(a.get("answer")):
            R2.judge(bool(verified(d, a.get("evidence"))), q["id"], f"evidence: {a.get('evidence')}",
                     "verified: true の事実が紐づいていない")
    for qid, a in d.answers.items():
        miss = num.missing(a.get("answer"), num.of_facts(d.answer_evidence(qid)))
        R5.judge(not miss, qid, a.get("answer"), "根拠の事実の値にない数値がある: " + "、".join(map(fmt_q, miss)))


@check("K02-06", needs=[CLAIMS, PLAN])
def k02_06(d, r):
    R = r.of("K02-06", CLAIMS)
    depths = {c["id"]: d.depth(c.get("question")) for c in d.claims.values() if c.get("question") in d.plan}
    common = max(set(depths.values()), key=list(depths.values()).count) if depths else None
    for c in d.claims.values():
        if c["id"] not in depths:
            R.ng(c["id"], f"question: {c.get('question')}", "主張の question が探索の計画にない")
        else:
            R.judge(depths[c["id"]] == common, c["id"], f"question: {c['question']}(階層 {depths[c['id']]})",
                    f"ほかの主張の問い(階層 {common})と階層が違う")


@check("K02-07", needs=[CLAIMS, STYLE])
def k02_07(d, r):
    R = r.of("K02-07", CLAIMS)
    limit, n = d.limit("max_claims"), len(d.claims)
    if limit is None:
        return R.ng(None, f"主張 {n}件", "資料の表現規約に、主張の数の上限(limits.max_claims)がない")
    R.judge(n <= limit, None, f"主張 {n}件、上限 {limit}", "主張の数が上限を超える")


@check("K02-10", "K02-12", needs=[CLAIMS, SOURCES])
def k02_claims(d, r):
    R10, R12 = r.of("K02-10", CLAIMS), r.of("K02-12", CLAIMS)
    num = Numbers(d)
    for c in d.claims.values():
        R10.judge(bool(verified(d, c.get("evidence"))), c["id"], f"evidence: {c.get('evidence')}",
                  "verified: true の事実が紐づいていない")
        miss = num.missing(c.get("statement"), num.of_facts(as_list(c.get("evidence"))))
        R12.judge(not miss, c["id"], c.get("statement"), "根拠の事実の値にない数値がある: " + "、".join(map(fmt_q, miss)))


@check("K02-17", needs=[CLAIMS, SOURCES])
def k02_17(d, r):
    R = r.of("K02-17", CLAIMS)
    h = d.claims_doc.get("hypothesis")
    if not h:
        return R.ok(None, "hypothesis: null(採った仮説がない)")
    listed = {c.get("fact") for c in dicts(d.claims_doc.get("contradictions"))}
    for f in d.facts.values():
        if isinstance(f.get("stance"), dict) and f["stance"].get(h) == "contradicts":
            R.judge(f["id"] in listed, f["id"], f.get("statement"), f"採った仮説 {h} を否定する事実が contradictions にない")


@check("K02-20", "K02-21", needs=[CLAIMS, SOURCES, STYLE])
def k02_summary(d, r):
    R20, R21 = r.of("K02-20", CLAIMS), r.of("K02-21", CLAIMS)
    s = text_of(d.claims_doc.get("summary"))
    limit = d.limit("summary_max_chars")
    problems = []
    if not s:
        problems.append("summary がない")
    if len(sentences(s)) > 1:
        problems.append("1文でない")
    if limit is None:
        problems.append("資料の表現規約に、要約の文の字数の上限(limits.summary_max_chars)がない")
    elif len(s) > limit:
        problems.append(f"{len(s)}字で、上限の{limit}字を超える")
    R20.judge(not problems, None, s, "。".join(problems))
    num = Numbers(d)
    in_claims, in_facts = set(), set()
    for c in d.claims.values():
        in_claims |= {(v, u) for v, u, _ in num.of_text(c.get("statement"))}
        in_facts |= num.of_facts(as_list(c.get("evidence")))
    miss = [q for q in num.of_text(s) if (q[0], q[1]) not in in_claims or (q[0], q[1]) not in in_facts]
    R21.judge(not miss, None, s, "主張の中の数値、または主張の根拠の事実の値にない数値がある: " + "、".join(map(fmt_q, miss)))


# ---------------------------------------------------------------- 工程3

@check("K03-01", "K03-02", needs=[CHAPTERS, CLAIMS])
def k03_claims(d, r):
    R1, R2 = r.of("K03-01", CHAPTERS), r.of("K03-02", CHAPTERS)
    assigned = {c for ch in d.chapters if ch.get("kind") == "body" for c in as_list(ch.get("claims"))}
    for cid, c in d.claims.items():
        R1.judge(cid in assigned, cid, c.get("statement"), "どの本論の章にも割り当てられていない")
    for ch in d.chapters:
        has = bool(as_list(ch.get("claims")))
        if ch.get("kind") == "body":
            R2.judge(has, ch.get("id"), f"kind: body、claims: {ch.get('claims')}", "本論の章に claims がない")
        else:
            R2.judge(not has, ch.get("id"), f"kind: {ch.get('kind')}、claims: {ch.get('claims')}", "導入または結びの章に claims がある")


@check("K03-03", needs=[CHAPTERS])
def k03_03(d, r):
    R = r.of("K03-03", CHAPTERS)
    for o in dicts(d.load(CHAPTERS).get("omitted")):
        lack = [k for k in ("to", "reason") if not o.get(k)]
        R.judge(not lack, o.get("question"), f"to: {o.get('to')}、reason: {o.get('reason')}", "、".join(lack) + " がない")


@check("K03-04", needs=[CHAPTERS])
def k03_04(d, r):
    R = r.of("K03-04", CHAPTERS)
    for ch in d.chapters:
        secs = dicts(ch.get("sections"))
        lack = [k for k in ("title", "question", "point") if not isinstance(ch.get(k), str) or not ch[k].strip()]
        if not secs:
            lack.append("sections")
        R.judge(not lack, ch.get("id"), ch.get("title"), "章に " + "、".join(lack) + " がない")
        for s in secs:
            if len(secs) == 1:
                ok = s.get("point_from") == "chapter" and not s.get("point") and bool(s.get("title"))
                R.judge(ok, s.get("id"), f"title: {s.get('title')}、point_from: {s.get('point_from')}",
                        "節が1つだけの章の節が、章の要点を引いていない(point_from: chapter)。または題がない")
            else:
                ok = bool(s.get("title")) and isinstance(s.get("point"), str) and bool(s["point"].strip())
                R.judge(ok, s.get("id"), f"title: {s.get('title')}、point: {s.get('point')}", "節に題または要点がない")


@check("K03-05", needs=[CHAPTERS, CLAIMS, PLAN])
def k03_05(d, r):
    R = r.of("K03-05", CHAPTERS)
    for ch in d.chapters:
        if ch.get("kind") != "body":
            continue
        qs = [d.claims[c].get("question") for c in as_list(ch.get("claims")) if c in d.claims]
        under = set().union(*[d.descendants(q) for q in qs]) if qs else set()
        for s in dicts(ch.get("sections")):
            if under:
                frm = as_list(s.get("from"))
                bad = [q for q in frm if q not in under]
                R.judge(bool(frm) and not bad, s.get("id"), f"from: {s.get('from')}",
                        "節に from がない" if not frm else "from の答えが、主張の問いの下にない: " + "、".join(map(str, bad)))
            else:
                R.judge(s.get("point_from") == "chapter", s.get("id"), f"point_from: {s.get('point_from')}",
                        "主張の問いに子の問いがない章の節が、章の要点を引いていない")


@check("K03-06", needs=[CHAPTERS, CLAIMS, ANSWERS])
def k03_06(d, r):
    R = r.of("K03-06", CHAPTERS)
    num = Numbers(d)
    for ch in d.chapters:
        if isinstance(ch.get("point"), str):
            allowed = set()
            for c in as_list(ch.get("claims")):
                allowed |= {(v, u) for v, u, _ in num.of_text(d.claims.get(c, {}).get("statement"))}
            miss = num.missing(ch["point"], allowed)
            R.judge(not miss, ch.get("id"), ch["point"], "割り当てた主張にない数値がある: " + "、".join(map(fmt_q, miss)))
        for s in dicts(ch.get("sections")):
            if isinstance(s.get("point"), str):
                allowed = set()
                for q in as_list(s.get("from")):
                    allowed |= {(v, u) for v, u, _ in num.of_text(d.answers.get(q, {}).get("answer"))}
                miss = num.missing(s["point"], allowed)
                R.judge(not miss, s.get("id"), s["point"], "from の答えにない数値がある: " + "、".join(map(fmt_q, miss)))


@check("K03-10", "K03-12", needs=[CHAPTERS, CLAIMS])
def k03_contra(d, r):
    R10, R12 = r.of("K03-10", CHAPTERS), r.of("K03-12", CHAPTERS)
    doc = d.load(CHAPTERS)
    placed = {c.get("fact") for c in dicts(doc.get("contradictions")) if c.get("chapter")}
    for c in dicts(d.claims_doc.get("contradictions")):
        if c.get("handling") in ("rebut", "qualify"):
            R10.judge(c.get("fact") in placed, c.get("fact"), f"handling: {c.get('handling')}", "触れる章が contradictions にない")
    listed = {(o.get("claim"), o.get("index")) for o in dicts(doc.get("objections"))}
    for cid, c in d.claims.items():
        for i, o in enumerate(dicts(c.get("objections"))):
            R12.judge((cid, i) in listed, f"{cid} objections[{i}]", o.get("objection"), "この反論が章構成の objections にない")


def brief_slide_limit(d):
    for v in d.brief_attrs("制約", "枚数の目安"):
        m = re.search(r"\d+", unicodedata.normalize("NFKC", v))
        if m:
            return int(m.group())
    return None


@check("K03-13", "K03-14", needs=[CHAPTERS, BRIEF])
def k03_slides(d, r):
    R13, R14 = r.of("K03-13", CHAPTERS), r.of("K03-14", CHAPTERS)
    limit = brief_slide_limit(d)
    counts = [ch.get("slides") for ch in d.chapters]
    if limit is None:
        R13.ng(None, "制約", "ブリーフの「制約」に、枚数の目安(- 枚数の目安: 数)がない")
    elif not all(isinstance(n, int) and not isinstance(n, bool) for n in counts):
        R13.ng(None, f"slides: {counts}", "slides が整数でない章がある")
    else:
        R13.judge(sum(counts) <= limit, None, f"枚数の合計 {sum(counts)}、ブリーフの枚数の目安 {limit}", "枚数の合計がブリーフの制約を超える")
    for ch in d.chapters:
        R14.judge(bool(ch.get("slides_reason")), ch.get("id"), ch.get("slides_reason") or ch.get("title"), "slides_reason がない")


# ---------------------------------------------------------------- 工程4

def main_slides(d):
    return [s for s in d.story if s.get("chapter") != "appendix"]


def section_slides(d, sid):
    return [s for s in main_slides(d) if s.get("section") == sid]


@check("K04-01", "K04-03", "K04-13", needs=[STORY])
def k04_shape(d, r):
    R1, R3, R13 = r.of("K04-01", STORY), r.of("K04-03", STORY), r.of("K04-13", STORY)
    for s in d.story:
        sid = s.get("id")
        R1.judge(isinstance(s.get("title"), str) and bool(s["title"].strip()), sid, s.get("title"), "題がない")
        wrote = isinstance(s.get("point"), str) and bool(s["point"].strip())
        pulls = s.get("point_from") == "section"
        role = s.get("role") in roles_vocab()
        forms = [wrote and s.get("point_from") is None and s.get("role") is None,
                 pulls and s.get("point") is None and s.get("role") is None,
                 role and s.get("point") is None and s.get("point_from") is None]
        R3.judge(sum(forms) == 1, sid, f"point: {short(s.get('point'), 30)}、point_from: {s.get('point_from')}、role: {s.get('role')}",
                 "要点を書く、節の要点を引く、要点を持たずに役割を書く、のいずれか1つの形でない")
        if d.has_point(s):
            R13.judge(isinstance(s.get("question"), str) and bool(s["question"].strip()), sid,
                      s.get("question") or s.get("title"), "要点を持つスライドに、問いが1つない")


@check("K04-02", needs=[STORY, BRIEF])
def k04_02(d, r):
    R = r.of("K04-02", STORY)
    if not d.deck_type:
        return R.ng(None, "資料の型", "ブリーフの「資料の型」から、資料の型の定義を1つに決められない")
    ann = d.deck_type.get("annotation") if isinstance(d.deck_type.get("annotation"), dict) else {}
    if ann.get("provenance", "none") == "none":
        return R.ok(None, f"annotation: {ann}(出どころの区別を求めない)")
    for s in d.story:
        p = s.get("provenance")
        if p not in ("cited", "proposal", "practice"):
            R.ng(s.get("id"), f"provenance: {p}", "provenance がない")
        elif p == "cited" and d.has_point(s) and not as_list(s.get("evidence")):
            R.ng(s.get("id"), "provenance: cited", "cited とした、要点を持つスライドに evidence がない")
        else:
            R.ok(s.get("id"), f"provenance: {p}")


@check("K04-04", "K04-05", "K04-06", needs=[STORY, CHAPTERS, STYLE])
def k04_sections(d, r):
    R4, R5, R6 = r.of("K04-04", STORY), r.of("K04-05", STORY), r.of("K04-06", STORY)
    for s in main_slides(d):
        R4.judge(s.get("section") in d.sections, s.get("id"), f"section: {s.get('section')}", "章構成にある節に入っていない")
    max_n, min_n = d.limit("section_max_slides"), d.limit("section_summary_min_slides")
    for sid, (ch, sec) in d.sections.items():
        slides = section_slides(d, sid)
        n = len(slides)
        R4.judge(n >= 1, sid, f"節のスライド {n}枚", "この節にスライドがない")
        if max_n is None:
            R5.ng(sid, f"節の項の数 {n}", "資料の表現規約に、limits.section_max_slides がない")
        else:
            R5.judge(n <= max_n, sid, f"節の項の数 {n}、上限 {max_n}", "節の項の数が上限を超える")
        if not slides:
            continue
        pulling = [s.get("id") for s in slides if s.get("point_from") == "section"]
        last = slides[-1].get("id")
        quote = f"項の数 {n}、境目 {min_n}、節の要点を引くスライド: {pulling or 'なし'}"
        if min_n is None:
            R6.ng(sid, quote, "資料の表現規約に、limits.section_summary_min_slides がない")
        elif n >= min_n:
            R6.judge(not pulling, sid, quote, "項の数が境目の枚数以上の節では、節のまとめが節の要点を載せる。節の要点を引くスライドを置かない")
        else:
            must = any(not d.has_point(s) for s in slides) or n == 1 or len(dicts(ch.get("sections"))) == 1
            if any(p != last for p in pulling) or len(pulling) > 1:
                R6.ng(sid, quote, f"節の要点を引くスライドが、節の最後のスライド({last})でない")
            elif must and pulling != [last]:
                R6.ng(sid, quote, f"節の最後のスライド({last})が、節の要点を引いていない(point_from: section)")
            else:
                R6.ok(sid, quote)


@check("K04-07", needs=[STORY, BRIEF])
def k04_07(d, r):
    R = r.of("K04-07", STORY)
    if not d.deck_type:
        return R.ng(None, "資料の型", "ブリーフの「資料の型」から、資料の型の定義を1つに決められない")
    used = {x for s in d.story for x in as_list(s.get("required"))}
    need = [x.get("id") for x in dicts(d.deck_type.get("required_slides"))]
    if not need:
        return R.ok(None, "required_slides: [](必ず置くスライドがない)")
    for x in need:
        R.judge(x in used, x, f"required_slides: {x}", "required でこれを参照するスライドがない")


def auto_slide_counts(d):
    """自動で作るスライドのうち、章構成とストーリーラインから数えられるもの。"""
    min_n = d.limit("section_summary_min_slides")
    chapters = len(d.chapters)
    ch_sum = sum(1 for ch in d.chapters if len(dicts(ch.get("sections"))) > 1)
    sec_sum = sum(1 for sid in d.sections if min_n is not None and len(section_slides(d, sid)) >= min_n)
    return f"章扉 {chapters}枚、章のまとめ {ch_sum}枚、節のまとめ {sec_sum}枚"


@check("K04-09", needs=[STORY, CHAPTERS],
       partial="自動で作るスライドは、章扉、章のまとめ、節のまとめの枚数だけを出す。表紙、目次、要約などは数えない")
def k04_09(d, r):
    R = r.of("K04-09", STORY)
    auto = auto_slide_counts(d)
    for ch in d.chapters:
        n = len([s for s in d.story if s.get("chapter") == ch.get("id")])
        cap = ch.get("slides")
        if not isinstance(cap, int):
            R.ng(ch.get("id"), f"{n}枚", "章構成に slides がない")
        else:
            R.judge(n <= cap, ch.get("id"), f"{n}枚、配分 {cap}枚。自動で作るスライド: {auto}", "章の枚数が章構成の配分を超える")


@check("K04-10", "K04-11", "K04-12", "K04-14", needs=[STORY, CHAPTERS])
def k04_refs(d, r):
    R10, R11, R12, R14 = (r.of(c, STORY) for c in ("K04-10", "K04-11", "K04-12", "K04-14"))
    doc = d.load(CHAPTERS)
    appendix = [s for s in d.story if s.get("chapter") == "appendix"]
    for s in appendix:
        R10.judge(bool(s.get("appendix_of")), s.get("id"), f"appendix_of: {s.get('appendix_of')}", "appendix_of がない")
    for o in dicts(doc.get("omitted")):
        if o.get("to") == "appendix":
            hit = [s.get("id") for s in appendix if o.get("question") in as_list(s.get("from"))]
            R11.judge(bool(hit), f"omitted {o.get('question')}", f"参照する付録のスライド: {hit or 'なし'}",
                      "付録に回した答えを from で参照する付録のスライドがない")
    for o in dicts(doc.get("objections")):
        key = (o.get("claim"), o.get("index"))
        pool = appendix if o.get("to") == "appendix" else main_slides(d)
        hit = [s.get("id") for s in pool
               if isinstance(s.get("objection"), dict) and (s["objection"].get("claim"), s["objection"].get("index")) == key]
        R11.judge(bool(hit), f"objections {key[0]}[{key[1]}]", f"to: {o.get('to')}、参照するスライド: {hit or 'なし'}",
                  "この反論を objection で参照するスライドが、決めた置き場にない")
    for c in dicts(doc.get("contradictions")):
        hit = [s for s in d.story if s.get("contradiction") == c.get("fact") and s.get("chapter") == c.get("chapter")]
        if not hit:
            R12.ng(c.get("fact"), f"chapter: {c.get('chapter')}", "contradiction でこの事実を参照するスライドが、決めた章にない")
        else:
            bad = [s.get("id") for s in hit if c.get("fact") not in as_list(s.get("evidence"))]
            R12.judge(not bad, c.get("fact"), f"スライド: {[s.get('id') for s in hit]}",
                      "スライドの evidence がこの事実を含まない: " + "、".join(map(str, bad)))
    body = {ch.get("id") for ch in d.chapters if ch.get("kind") == "body"}
    for s in d.story:
        if s.get("chapter") in body and d.has_point(s):
            lack = [k for k in ("from", "evidence") if not as_list(s.get(k))]
            R14.judge(not lack, s.get("id"), f"from: {s.get('from')}、evidence: {s.get('evidence')}", "、".join(lack) + " がない")


@check("K04-16", needs=[STORY, SOURCES])
def k04_16(d, r):
    R = r.of("K04-16", STORY)
    num = Numbers(d)
    for s in d.story:
        if isinstance(s.get("point"), str):
            miss = num.missing(s["point"], num.of_facts(as_list(s.get("evidence"))))
            R.judge(not miss, s.get("id"), s["point"], "evidence の事実の値にない数値がある: " + "、".join(map(fmt_q, miss)))


@check("K04-26", "K04-27", "K04-28", needs=[STATES, CHAPTERS, BRIEF],
       partial={"K04-28": "答えないと決めた記録は、設計の判断の記録(decisions.md)に懸念の文がそのまま書かれていることで見る"})
def k04_states(d, r):
    R26, R27, R28 = (r.of(c, STATES) for c in ("K04-26", "K04-27", "K04-28"))
    by = {s.get("chapter"): s for s in dicts(d.load(STATES))}
    seen = {"terms": set(), "accepted": set(), "open_questions": set()}
    answered, last = set(), None
    for ch in d.chapters:
        st = by.get(ch.get("id"))
        if not st:
            R26.ng(ch.get("id"), ch.get("title"), "この章の前提と到達点がない")
            continue
        entry = st.get("entry") if isinstance(st.get("entry"), dict) else {}
        exit_ = st.get("exit") if isinstance(st.get("exit"), dict) else {}
        lack = []
        for key in ("terms", "accepted"):
            lack += [f"{key}: {x}" for x in as_list(entry.get(key)) if x not in seen[key]]
        lack += [f"open_questions: {x}" for x in as_list(entry.get("open_questions"))
                 if x not in seen["open_questions"] or x in answered]
        R26.judge(not lack, ch.get("id"), f"entry: {entry}", "前の章の出口の状態にないものがある: " + "、".join(lack))
        for key in seen:
            seen[key] |= set(map(text_of, as_list(exit_.get(key)))) if key != "accepted" else set(as_list(exit_.get(key)))
        answered |= set(as_list(exit_.get("answered")))
        last = (ch.get("id"), exit_)
    if last:
        left = as_list(last[1].get("open_questions"))
        R27.judge(not left, last[0], f"open_questions: {left}", "最後の章の出口に、残る疑問がある")
    done = {c for s in by.values() if isinstance(s.get("exit"), dict) for c in as_list(s["exit"].get("concerns_answered"))}
    notes = d.text(DECISIONS) or ""
    for c in d.brief_attrs("読み手の立場と懸念", "懸念"):
        if c in done:
            R28.ok(c, f"concerns_answered: {c}")
        elif c in notes:
            R28.ok(c, f"{DECISIONS}: {c}")
        else:
            R28.ng(c, c, "どの章の concerns_answered にもなく、設計の判断の記録にもこの懸念の記述がない")


@check("K04-29", needs=[SCENARIOS])
def k04_29(d, r):
    R = r.of("K04-29", SCENARIOS)
    by = {s.get("scenario"): s for s in dicts(d.load(SCENARIOS))}
    for sid in scenario_ids():
        s = by.get(sid)
        if not s:
            R.ng(sid, sid, "この場面がない")
        elif s.get("applicable") is False:
            R.judge(bool(s.get("reason")), sid, f"applicable: false、reason: {s.get('reason')}", "該当しない場面に reason がない")
        else:
            R.judge(isinstance(s.get("expected"), str) and bool(s["expected"].strip()), sid, s.get("expected") or sid,
                    "expected がない")


# ---------------------------------------------------------------- 工程5

@check("K05-01", "K05-02", "K05-03", "K05-07", "K05-08", "K05-11", needs=[PROOF, STORY, SOURCES],
       partial={"K05-08": "理由は relation_reason に書くものとして見る(項目の名前は道具が決めた)"})
def k05_each(d, r):
    R1, R2, R3, R7, R8, R11 = (r.of(c, PROOF) for c in ("K05-01", "K05-02", "K05-03", "K05-07", "K05-08", "K05-11"))
    for sid, p in d.proof.items():
        R1.judge(p.get("relation") in relations_vocab(), sid, f"relation: {p.get('relation')}", "主張の種類の語彙にない")
        bad = []
        for f in as_list(p.get("facts")):
            fact = d.facts.get(f)
            if not fact:
                bad.append(f"{f}(素材台帳にない)")
            elif fact.get("verified") is not True:
                bad.append(f"{f}(verified: true でない)")
            elif fact.get("superseded_by"):
                bad.append(f"{f}(superseded_by がある)")
        R2.judge(not bad, sid, f"facts: {p.get('facts')}", "使えない事実がある: " + "、".join(bad))
        slide = d.story_by_id.get(sid, {})
        lack = [e for e in as_list(slide.get("evidence")) if e not in as_list(p.get("facts"))]
        R3.judge(not lack, sid, f"facts: {p.get('facts')}", "ストーリーラインの evidence を含まない: " + "、".join(map(str, lack)))
        empty = [k for k in ("show", "focus") if not text_of(p.get(k)).strip()]
        if slide.get("role") == "exercise" and "focus" in empty:
            empty.remove("focus")
        R7.judge(not empty, sid, f"show: {short(p.get('show'), 30)}、focus: {short(p.get('focus'), 30)}", "、".join(empty) + " が空である")
        flat = p.get("relation") in ("statement", "list")
        if flat:
            R8.judge(bool(text_of(p.get("relation_reason")).strip()), sid, p.get("relation_reason") or f"relation: {p.get('relation')}",
                     "ほかの種類に当てはまらない理由(relation_reason)がない")
        if "holds" not in p or not isinstance(p["holds"], list):
            R11.ng(sid, f"holds: {p.get('holds')}", "holds の項目がない")
        else:
            R11.judge(not (flat and p["holds"]), sid, f"relation: {p.get('relation')}、holds: {p['holds']}",
                      "並列の列挙、言い切りのスライドの holds が空でない")
    for s in d.story:
        if s.get("id") not in d.proof:
            R7.ng(s.get("id"), s.get("title"), "このスライドの立証の設計がない")


def view_parts(d, view):
    """view が選んだ要素、つながり、場面。場面を選んだ場合は、その steps のつながりを含める。"""
    view = view if isinstance(view, dict) else {}
    elements = set(as_list(view.get("elements")))
    relations = set(as_list(view.get("relations")))
    scenarios = set(as_list(view.get("scenario"))) | set(as_list(view.get("scenarios")))
    for s in scenarios:
        relations |= set(as_list(d.model_ids("scenarios").get(s, {}).get("steps")))
    return elements, relations, scenarios


@check("K05-04", "K05-10", needs=[PROOF])
def k05_view(d, r):
    R4, R10 = r.of("K05-04", PROOF), r.of("K05-10", PROOF)
    els, rels, scs = (d.model_ids(k) for k in ("elements", "relations", "scenarios"))
    shown = set()
    for p in d.proof.values():
        if p.get("relation") in ("architecture", "entity-relation"):
            shown |= view_parts(d, p.get("view"))[0]
    for sid, p in d.proof.items():
        if p.get("real") is True:
            view = p.get("view") if isinstance(p.get("view"), dict) else None
            if not view:
                R4.ng(sid, "real: true", "view がない")
            else:
                bad = [x for x in as_list(view.get("elements")) if x not in els]
                bad += [x for x in as_list(view.get("relations")) if x not in rels]
                bad += [x for x in as_list(view.get("scenario")) + as_list(view.get("scenarios")) if x not in scs]
                R4.judge(not bad, sid, f"view: {view}", "仕組みの定義にない: " + "、".join(map(str, bad)))
        if p.get("relation") in ("interaction", "state-transition"):
            elements, relations, _ = view_parts(d, p.get("view"))
            for rid in relations:
                elements |= {rels.get(rid, {}).get("from"), rels.get(rid, {}).get("to")} - {None}
            lack = sorted(e for e in elements if e not in shown)
            R10.judge(not lack, sid, f"view の要素: {sorted(elements)}",
                      "構成または要素の関係の図に出ない要素がある: " + "、".join(lack))


@check("K05-09", needs=[PROOF])
def k05_09(d, r):
    R = r.of("K05-09", PROOF)
    users = {}
    for sid, p in d.proof.items():
        for f in as_list(p.get("facts")):
            users.setdefault(f, []).append(sid)
    for f, sids in users.items():
        R.judge(len(sids) < 2, f, f"使うスライド: {sids}", "同じ事実を複数のスライドが使う")


# ---------------------------------------------------------------- 工程6

def table_rows(d, relation, base):
    return [t for t in d.table if t.get("relation") == relation and t.get("base", "none") == base]


def decide_pattern(d, proof):
    """立証の設計の1件に、対応表が定める型。量の区分は決められないので、区分によらず型が1つに決まる場合だけ返す。"""
    rows = table_rows(d, proof.get("relation"), proof.get("base") or "none")
    sizes = {t.get("size") for t in rows}
    patterns = {t.get("pattern") for t in rows}
    if not rows:
        return None, "主張の種類と土台の組が、表現の対応表にない"
    if "any" in sizes and len(rows) == 1:
        return rows[0].get("pattern"), None
    if sizes == {"within", "over"} and len(patterns) == 1:
        return patterns.pop(), None
    if sizes == {"within", "over"}:
        return None, "量の区分(within、over)で型が分かれる。量の区分は、収容量の値が未確定のため機械で決められない"
    return None, f"対応表の行が size: {sorted(map(str, sizes))} だけで、量の区分を機械で決められない"


@check("K06-01", "K06-03", "K06-04", needs=[PATTERNS, PROOF],
       partial={"K06-01": "量の区分は決められない。size が any の行か、within と over の両方の行がある組だけを、対応表にあるとする",
                "K06-03": "expresses は、資料の型の定義(definitions/patterns.yaml)にあるものを使う。ない型は不合格とする"})
def k06_table(d, r):
    R1, R3, R4 = r.of("K06-01", PATTERNS), r.of("K06-03", PATTERNS), r.of("K06-04", PATTERNS)
    for sid, p in d.proof.items():
        rel, base = p.get("relation"), p.get("base") or "none"
        sizes = {t.get("size") for t in table_rows(d, rel, base)}
        covered = "any" in sizes or {"within", "over"} <= sizes
        why = "この組の行がない" if not sizes else "行が size: " + "、".join(sorted(map(str, sizes))) + " だけで、量の区分を機械で決められない"
        R1.judge(covered, sid, f"relation: {rel}、base: {base}、対応表の size: {sorted(map(str, sizes)) or 'なし'}", why)
        pattern, problem = decide_pattern(d, p)
        if not pattern:
            R3.ng(sid, f"relation: {rel}、base: {base}", "型を決められない。" + problem)
            continue
        pdef = d.pattern_defs.get(pattern)
        if not pdef:
            R3.ng(sid, f"pattern: {pattern}", "型の定義にない型である")
            continue
        holds = as_list(p.get("holds"))
        implies = [i for i in as_list(pdef.get("implies")) if i != "emphasized"]
        false_ = [i for i in implies if i not in holds]
        quote = f"pattern: {pattern}、implies: {implies}、holds: {holds}"
        if false_:
            R3.ng(sid, quote, "型の implies が holds に含まれない: " + "、".join(false_))
        elif holds and "expresses" not in pdef:
            R3.ng(sid, quote, "型の定義に expresses がなく、主な関係を表せるかを確かめられない")
        elif holds and holds[0] not in as_list(pdef.get("expresses")):
            R3.ng(sid, quote, f"holds の主な関係({holds[0]})が、型の expresses に含まれない")
        else:
            R3.ok(sid, quote)
        if {"grouped", "partition"} & set(as_list(pdef.get("implies"))):
            R4.judge(bool(text_of(p.get("axis")).strip()), sid, f"pattern: {pattern}、axis: {p.get('axis')}",
                     "まとまりや分割を伝える型なのに、立証の設計の axis が空である")


@check("K06-02", needs=[PATTERNS])
def k06_02(d, r):
    R = r.of("K06-02", PATTERNS)
    users = {}
    for t in d.table:
        if t.get("size") in ("any", "within"):
            users.setdefault((t.get("base", "none"), t.get("pattern")), set()).add(t.get("relation"))
    for (base, pattern), rels in users.items():
        R.judge(len(rels) < 2, pattern, f"base: {base}、relation: {sorted(map(str, rels))}", "主な型が、複数の主張の種類に使われている")


@check("K06-07", "K06-10", needs=[PATTERNS, STYLE])
def k06_style(d, r):
    R7, R10 = r.of("K06-07", STYLE), r.of("K06-10", SAMPLES)
    used = sorted({t.get("pattern") for t in d.table if t.get("pattern")})
    pos = d.style.get("point_position")
    sampled = {s.get("body", {}).get("type") for specs in d.load_dir(SAMPLES).values()
               for s in specs if isinstance(s.get("body"), dict)}
    for p in used:
        if not isinstance(pos, dict):
            R7.ng(p, "point_position", "資料の表現規約に point_position がない")
        else:
            v = pos.get(p, pos.get("default"))
            R7.judge(v in point_positions(), p, f"point_position: {v}", "要点の位置が、認める3つのいずれかでない")
        R10.judge(p in sampled, p, f"見本のある型: {sorted(map(str, sampled))}", "この型の見本が 06-samples/ にない")


@check("K06-18", needs=[TERMS])
def k06_18(d, r):
    R = r.of("K06-18", TERMS)
    for t in d.terms:
        if t.get("kind") == "noun":
            ok = bool(t.get("defined_in")) or bool(text_of(t.get("no_definition")).strip())
            R.judge(ok, t.get("id"), f"{t.get('term')}: defined_in: {t.get('defined_in')}、no_definition: {t.get('no_definition')}",
                    "defined_in も、定義が要らない理由(no_definition)もない")


# ---------------------------------------------------------------- 工程7

FLAT_PATTERNS = {"plain-list", "statement", "big-number"}


def is_figure(d, ptype):
    """図や表を載せる型か。docs/patterns.md の区分で決める。画像の区分と、箇条書き、言い切り、大きな数字は含めない。"""
    group = d.pattern_defs.get(ptype, {}).get("group")
    if ptype in FLAT_PATTERNS or group == "画像":
        return False
    return True


def count_highlight(body):
    n = 0
    if isinstance(body, dict):
        for k, v in body.items():
            if k == "highlight" and v not in (None, [], ""):
                n += len(v) if isinstance(v, list) else 1
            else:
                n += count_highlight(v)
    elif isinstance(body, list):
        n += sum(count_highlight(v) for v in body)
    return n


def strings_in(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, list):
        for v in x:
            yield from strings_in(v)
    elif isinstance(x, dict):
        for k, v in x.items():
            yield str(k)
            yield from strings_in(v)


@check("K07-02", "K07-03", "K07-04", "K07-05", "K07-06", "K07-07", "K07-08", "K07-12", "K07-16", "K07-34", "K07-38",
       needs=[STORY, PROOF, PATTERNS, SOURCES],
       partial={"K07-03": "量の区分は決められない。区分によらず型が1つに決まる場合だけ照合し、決まらない場合は不合格とする",
                "K07-05": "sources がその事実を含むことを見る。中身の文が事実を述べているかは、検査セッションが見る",
                "K07-06": "中身(body)に書かれた、仕組みの定義のIDを全て拾って照合する",
                "K07-07": "図や表を載せる型は、型の定義の区分で決める。箇条書き、言い切り、大きな数字と、画像の区分の型は除く",
                "K07-34": "body.type が型の定義にあることを見る。立体のグラフは型の定義に置かない",
                "K07-38": "Issueの番号は issue に書くものとして見る(項目の名前は道具が決めた)"})
def k07_each(d, r):
    num = Numbers(d)
    model_all = set(d.model_ids("elements")) | set(d.model_ids("relations")) | set(d.model_ids("scenarios"))
    specs = d.slide_specs()
    if not specs:
        return
    for name, s in specs:
        R = {c: r.of(c, name) for c in ("K07-02", "K07-03", "K07-04", "K07-05", "K07-06", "K07-07", "K07-08",
                                        "K07-12", "K07-16", "K07-34", "K07-38")}
        sid = s.get("id")
        story, proof = d.story_by_id.get(sid), d.proof.get(sid)
        body = s.get("body") if isinstance(s.get("body"), dict) else {}
        ptype = body.get("type")
        if story is None:
            R["K07-02"].ng(sid, f"id: {sid}", "ストーリーラインにないスライドである")
        else:
            diff = [k for k in ("title", "point", "point_from", "role", "qualifiers", "provenance") if s.get(k) != story.get(k)]
            R["K07-02"].judge(not diff, sid, f"title: {s.get('title')}", "ストーリーラインと一致しない: " + "、".join(diff))
        if proof is None:
            R["K07-03"].ng(sid, f"body.type: {ptype}", "このスライドの立証の設計がない")
            R["K07-04"].ng(sid, f"sources: {s.get('sources')}", "このスライドの立証の設計がない")
        else:
            pattern, problem = decide_pattern(d, proof)
            if not pattern:
                R["K07-03"].ng(sid, f"body.type: {ptype}", "表現の対応表が定める型を決められない。" + problem)
            else:
                R["K07-03"].judge(ptype == pattern, sid, f"body.type: {ptype}、対応表の型: {pattern}", "表現の対応表が定める型と違う")
            extra = [x for x in as_list(s.get("sources")) if x not in as_list(proof.get("facts"))]
            R["K07-04"].judge(not extra, sid, f"sources: {s.get('sources')}", "立証設計の facts にない: " + "、".join(map(str, extra)))
            if proof.get("real") is True:
                elements, relations, scenarios = view_parts(d, proof.get("view"))
                allowed = elements | relations | scenarios
                used = sorted({x for x in strings_in(body) if x in model_all})
                bad = [x for x in used if x not in allowed]
                R["K07-06"].judge(not bad, sid, f"使う仕組みの定義のID: {used}", "立証設計の view にない: " + "、".join(bad))
        if story and story.get("contradiction"):
            R["K07-05"].judge(story["contradiction"] in as_list(s.get("sources")), sid, f"sources: {s.get('sources')}",
                              f"sources が、結論を否定する事実 {story['contradiction']} を含まない")
        if ptype and is_figure(d, ptype):
            R["K07-07"].judge(body.get("highlight") not in (None, "", []), sid, f"body.type: {ptype}、highlight: {body.get('highlight')}",
                              "図や表を載せるスライドに、強調する要素(body.highlight)の指定がない")
        n = count_highlight(body)
        R["K07-08"].judge(n <= 1, sid, f"highlight の指定 {n}か所", "強調が1枚に2か所以上ある")
        if isinstance(s.get("point"), str):
            miss = num.missing(s["point"], num.of_facts(as_list(s.get("sources"))))
            R["K07-12"].judge(not miss, sid, s["point"], "sources の事実の値にない数値がある: " + "、".join(map(fmt_q, miss)))
        if "asset" in body:
            asset = d.facts.get(body.get("asset"))
            if not asset or asset.get("kind") != "image":
                R["K07-16"].ng(sid, f"asset: {body.get('asset')}", "画像の素材が素材台帳にない")
            else:
                regions = {x.get("id") for x in dicts(asset.get("regions"))}
                refs = as_list(body.get("crop")) + (list(body["captions"]) if isinstance(body.get("captions"), dict) else [])
                if isinstance(body.get("highlight"), str):
                    refs.append(body["highlight"])
                bad = [x for x in refs if x not in regions]
                R["K07-16"].judge(not bad, sid, f"参照する regions: {refs}", "画像の素材の regions にない: " + "、".join(map(str, bad)))
        R["K07-34"].judge(ptype in d.pattern_defs, sid, f"body.type: {ptype}", "型の定義にない型である")
        if s.get("status") == "blocked":
            R["K07-38"].judge(bool(text_of(s.get("issue")).strip()), sid, f"status: blocked、issue: {s.get('issue')}",
                              "保留のスライドに、Issueの番号(issue)がない")


@check("K07-11", "K07-24", needs=[SOURCES, STORY])
def k07_refs(d, r):
    known = d.all_ids()
    for f in d.facts.values():
        known |= {x.get("id") for x in dicts(f.get("regions"))}
    targets = set(d.facts) | set(d.story_by_id)
    for name, s in d.slide_specs():
        R11, R24 = r.of("K07-11", name), r.of("K07-24", name)
        sid = s.get("id")
        body = s.get("body") if isinstance(s.get("body"), dict) else {}
        bad = []

        def scan(x, path):
            if isinstance(x, bool) or x is None:
                return
            if isinstance(x, (int, float)):
                bad.append(f"{path}: {x}")
            elif isinstance(x, str):
                rest = strip_refs(x)
                if x not in known and re.search(r"[0-9０-９]", ID_RE.sub("", rest)):
                    bad.append(f"{path}: {short(x, 30)}")
            elif isinstance(x, list):
                for i, v in enumerate(x):
                    scan(v, f"{path}[{i}]")
            elif isinstance(x, dict):
                for k, v in x.items():
                    scan(v, f"{path}.{k}")

        scan(s.get("text"), "text")
        scan(body.get("data"), "body.data")
        scan(s.get("notes"), "notes")
        R11.judge(not bad, sid, f"text: {short(s.get('text'), 40)}", "事実のIDによらない数値がある: " + "、".join(bad))
        refs = [m for x in strings_in({k: v for k, v in s.items() if k != "id"}) for m in REF_RE.findall(x)]
        dangling = [f"{{{x}}}" for x in refs if x not in targets]
        R24.judge(not dangling, sid, f"参照: {['{' + x + '}' for x in refs] or 'なし'}",
                  "実在する事実もスライドも指さない参照がある: " + "、".join(dangling))


# ---------------------------------------------------------------- 描画の結果を読む検査(工程6、7、8)
# 描画上の診断は、tools/render.py が build/diagnostics.json(見本は build/samples/diagnostics.json)に書く。

# K07-41 の条件の文が挙げる診断(文字のあふれ、要素の重なり、描かれなかった内容、文字の大きさの下限)に当たる種類。
# 題が1行に収まらない、要点が2行を超える、は、文字のあふれに含める。
DIAG_KINDS_BUILD = {"overflow", "title-lines", "point-lines", "overlap", "unrendered", "font-too-small"}
DIAG_MEASURES = {"text-contrast": "text_contrast_min", "adjacent-contrast": "adjacent_contrast_min", "hue-count": "hues"}


def diag_quote(entries):
    return "、".join(f"{x.get('kind')}: {short(x.get('message'), 40)}" for x in entries[:3]) + (f" ほか{len(entries) - 3}件" if len(entries) > 3 else "")


@check("K06-06", "K06-11", needs=[PATTERNS],
       partial={"K06-06": "描ける型の一覧は、tools/render.py が診断に書いたものを使う。テンプレートで実現できるかは見ない",
                "K06-11": "色の差と色相の数の基準は、道具が決めた値による(tools/patterns-data.md)。重大度がエラーの診断を数える"})
def k06_render(d, r):
    R6, R11 = r.of("K06-06", PATTERNS), r.of("K06-11", SAMPLES)
    doc, _, shown, problem = d.diagnostics("samples")
    used = sorted({t.get("pattern") for t in d.table if t.get("pattern")})
    for p in used:
        if problem:
            R6.ng(p, shown, problem)
        else:
            can = as_list(doc.get("patterns"))
            R6.judge(p in can, p, f"描ける型: {can}", "描画の実装が描けない型である。代わりの型を選ぶか、描画の実装への要望として記録する")
    for name, specs in d.load_dir(SAMPLES).items():
        for s in specs:
            sid = s.get("id")
            e = d.diagnosed(R11, "samples", sid)
            if e is None:
                continue
            bad = [x for x in as_list(e.get("diagnostics")) if isinstance(x, dict) and x.get("severity") == "error"]
            R11.judge(not bad, sid, f"描画上の診断 {len(bad)}件" + (": " + diag_quote(bad) if bad else ""), "見本の描画上の診断がある")


@check("K07-40", "K07-41", needs=[STORY])
def k07_render(d, r):
    specs = d.slide_specs()
    doc, slides, shown, problem = d.diagnostics()
    file_of = {}
    for name, s in specs:
        file_of.setdefault(d.story_by_id.get(s.get("id"), {}).get("chapter"), name)
    targets = [(name, s.get("id")) for name, s in specs]
    # 章扉、節のまとめ、章のまとめも、その章をビルドした実物に含める
    targets += [(file_of[e.get("chapter")], sid) for sid, e in slides.items()
                if e.get("kind") not in ("本編", "付録") and e.get("chapter") in file_of]
    for name, sid in targets:
        R40, R41 = r.of("K07-40", name), r.of("K07-41", name)
        e = d.diagnosed(R41, None, sid)
        if e is None:
            R40.ng(sid, shown, problem or "このスライドの描画上の診断がない、または古い")
            continue
        colors = e.get("colors") if isinstance(e.get("colors"), dict) else {}
        missing = [m for m, key in DIAG_MEASURES.items() if m not in as_list(doc.get("measures")) or key not in colors]
        R40.judge(not missing, sid, "診断の項目: " + "、".join(f"{k}={colors.get(v)}" for k, v in DIAG_MEASURES.items()),
                  "描画上の診断に含まれない項目がある: " + "、".join(missing))
        bad = [x for x in as_list(e.get("diagnostics")) if isinstance(x, dict) and x.get("kind") in DIAG_KINDS_BUILD]
        R41.judge(not bad, sid, f"描画上の診断 {len(bad)}件" + (": " + diag_quote(bad) if bad else ""), "描画上の診断がある")


@check("K08-04", needs=[STORY])
def k08_04(d, r):
    R = r.of("K08-04", "build/")
    doc, slides, shown, problem = d.diagnostics()
    if problem:
        return R.ng(None, shown, problem)
    R.judge(doc.get("level") == "full" and doc.get("count") == len(slides), None, f"level: {doc.get('level')}、{len(slides)}枚(全体 {doc.get('count')}枚)",
            "全スライドをビルドした結果でない。全体を描き直す")
    for s in d.story:
        sid = s.get("id")
        e = d.diagnosed(R, None, sid)
        if e is not None and e.get("mode") != "spec":
            R.ng(sid, f"mode: {e.get('mode')}", "スライド仕様から描いていない(仮置き、または骨組み)")
    for sid, e in slides.items():
        if sid not in d.story_by_id and e.get("inputs_hash") != d.inputs_hash():
            R.ng(sid, shown, "描画の結果が、今の成果物より古い。描き直す")
        bad = [x for x in as_list(e.get("diagnostics")) if isinstance(x, dict) and x.get("severity") == "error"]
        R.judge(not bad, sid, f"描画上の診断 {len(bad)}件" + (": " + diag_quote(bad) if bad else ""), "描画上の診断がある")


# ---------------------------------------------------------------- 工程8

@check("K08-01", partial="工程0から7の、実装した機械の検査を再実行する。実装していない検査は実行しない")
def k08_01(d, r):
    """再実行は run() が行う。"""


@check("K08-02", needs=[STORY])
def k08_02(d, r):
    for name, s in [(n, s) for n, ss in d.load_dir(SLIDES).items() for s in ss]:
        r.of("K08-02", name).judge(s.get("status") != "blocked", s.get("id"), f"status: {s.get('status')}", "保留のスライドである")


@check("K08-03")
def k08_03(d, r):
    R = r.of("K08-03", STATUS)
    doc = d.load(STATUS) if d.exists(STATUS) else None
    if not isinstance(doc, dict):
        return R.ng(None, STATUS, "状態の記録がない、または読めない")
    for key in ("artifacts", "slides"):
        for name, st in (doc.get(key) or {}).items():
            if isinstance(st, dict):
                R.judge(st.get("state") != "invalid", name, f"state: {st.get('state')}", "合格が無効になっている: " + text_of(st.get("reason")))


@check("K08-09", needs=[SCENARIOS], partial="場面ごとに、実行の記録(runs/場面の識別子--回.yaml)が1つ以上あることを見る")
def k08_09(d, r):
    R = r.of("K08-09", "runs/")
    by = {s.get("scenario"): s for s in dicts(d.load(SCENARIOS))}
    for sid in scenario_ids():
        if by.get(sid, {}).get("applicable") is False:
            R.ok(sid, f"applicable: false、reason: {by[sid].get('reason')}")
            continue
        files = sorted(p.name for p in (d.root / "runs").glob(f"{sid}--*.yaml")) if (d.root / "runs").is_dir() else []
        R.judge(bool(files), sid, f"実行の記録: {files or 'なし'}", "この場面の実行の記録がない")


# ---------------------------------------------------------------- 文の機械の検査と、語彙の検査

@check("KX-02", "KX-04", partial={"KX-02": "上限は limits.max_commas に書くものとして見る(項目の名前は道具が決めた)",
                                  "KX-04": "上限は limits.max_kanji_run に書くものとして見る(項目の名前は道具が決めた)"})
def kx_measure(d, r, texts):
    commas, run = d.limit("max_commas"), d.limit("max_kanji_run")
    for t in texts:
        R2, R4 = r.of("KX-02", t.artifact), r.of("KX-04", t.artifact)
        plain = strip_refs(t.value)
        worst = max([s.count("、") for s in sentences(plain)] or [0])
        if commas is None:
            R2.ng(t.where, t.value, "資料の表現規約に、読点の数の上限(limits.max_commas)がない")
        else:
            R2.judge(worst <= commas, t.where, t.value, f"1文の読点が{worst}個で、上限の{commas}個を超える")
        longest = max(re.findall(rf"[{KANJI}]+", plain) or [""], key=len)
        if run is None:
            R4.ng(t.where, t.value, "資料の表現規約に、漢字の連なりの上限(limits.max_kanji_run)がない")
        else:
            R4.judge(len(longest) <= run, t.where, t.value, f"漢字が{len(longest)}字連なり(「{longest}」)、上限の{run}字を超える")


@check("KX-13", "KX-14",
       partial={"KX-13": "名詞で終わるかは、名詞で終わらないと言い切れる文末(する、である、です、について、助詞など)だけを見つける。字数の上限は limits.title_max_chars",
                "KX-14": "字数の上限は limits.point_max_chars に書くものとして見る(項目の名前は道具が決めた)"})
def kx_title_point(d, r, texts):
    tmax, pmax = d.limit("title_max_chars"), d.limit("point_max_chars")
    for t in texts:
        v = t.value.strip()
        if t.kind == "title":
            problems = []
            if "。" in v:
                problems.append("句点がある")
            end = next((e for e in sorted(NON_NOUN_ENDINGS, key=len, reverse=True) if v.rstrip("。").endswith(e)), None)
            if end:
                problems.append(f"名詞で終わらない(「{end}」で終わる)")
            if tmax is None:
                problems.append("資料の表現規約に、題の字数の上限(limits.title_max_chars)がない")
            elif len(v) > tmax:
                problems.append(f"{len(v)}字で、上限の{tmax}字を超える")
            r.of("KX-13", t.artifact).judge(not problems, t.where, v, "。".join(problems))
        elif t.kind == "point":
            problems = []
            if len(sentences(v)) != 1:
                problems.append("1文でない")
            end = next((e for e in BAD_POINT_ENDINGS if v.rstrip("。").endswith(e)), None)
            if end:
                problems.append(f"文末が「{end}」である")
            if pmax is None:
                problems.append("資料の表現規約に、要点の字数の上限(limits.point_max_chars)がない")
            elif len(v) > pmax:
                problems.append(f"{len(v)}字で、上限の{pmax}字を超える")
            r.of("KX-14", t.artifact).judge(not problems, t.where, v, "。".join(problems))


@check("KX-15", "KX-16",
       partial={"KX-15": "IDの書式は、資料にあるIDと、定義の例の形(F001、Q1.1、T-xxx、ch1-s1 など)とする",
                "KX-16": "句点の決まりは、スライド仕様の中身(body)の文にだけ当てる"})
def kx_notation(d, r, texts):
    known = sorted(d.all_ids(), key=len, reverse=True)
    for t in texts:
        plain = strip_refs(t.value)
        found = [m.group() for m in ID_RE.finditer(plain)]
        found += [i for i in known if i not in found and re.search(r"(?<![A-Za-z0-9_-])" + re.escape(i) + r"(?![A-Za-z0-9_-])", plain)]
        r.of("KX-15", t.artifact).judge(not found, t.where, t.value, "内部のIDがある: " + "、".join(found))
        problems = []
        if re.search(r"[０-９]", plain):
            problems.append("全角の数字がある")
        if re.search(r"[Ａ-Ｚａ-ｚ]", plain):
            problems.append("全角の英字がある")
        if re.search(r"[()]", plain):
            problems.append("半角の括弧がある")
        if re.search(r"[､｡]|(?<!\d),|,(?!\d)|(?<![A-Za-z0-9])\.|\.(?![A-Za-z0-9])", plain):
            problems.append("半角の句読点がある")
        if t.kind == "body":
            n = plain.count("。")
            if n == 1 and plain.rstrip().endswith("。"):
                problems.append("1文だけの項目に句点がある")
            elif n >= 1 and not plain.rstrip().endswith("。"):
                problems.append("複数の文なのに、句点のない文がある")
        r.of("KX-16", t.artifact).judge(not problems, t.where, t.value, "。".join(problems))


@check("KX-17", "KX-18", "KX-19", needs=[TERMS],
       partial={"KX-17": "形態素解析をしない。登録した語を消して残った、漢字、カタカナ、英字の並びを、登録のない語とする。ひらがなだけの語は拾わない。"
                         "要約の文、主張、題、要点だけを見る。説明、表のセル、ノートなど、一般語の辞書を使う文は見ない",
                "KX-19": "長音の有無、全角と半角、漢字の間の送り仮名の揺れを見る。語の末尾の送り仮名の揺れは見ない"})
def kx_vocabulary(d, r, texts):
    voc = Vocabulary(d)
    for t in texts:
        if t.kind in STRICT_KINDS:
            words = list(dict.fromkeys(voc.unknown(t.value)))
            r.of("KX-17", t.artifact).judge(not words, t.where, t.value, "語彙表にも allowed にもない語がある: " + "、".join(words))
        banned = voc.banned_in(t.value)
        r.of("KX-18", t.artifact).judge(not banned, t.where, t.value, "banned の語がある: " + "、".join(banned))
        var = voc.variants(t.value)
        r.of("KX-19", t.artifact).judge(not var, t.where, t.value, "語彙表の語と表記が違う語がある: " + "、".join(var))


KX_FUNCTIONS = (kx_measure, kx_title_point, kx_notation, kx_vocabulary)
KX_STAGES = (2, 3, 4, 7)
KX_NEEDS = {2: [CLAIMS], 3: [CHAPTERS], 4: [STORY], 7: [STORY]}


# ---------------------------------------------------------------- 書式(台帳にない確かめ)

def check_format(d, names, required):
    """成果物の書式と、IDの参照先を確かめる。(成果物, 箇所, 誤り) の一覧を返す。"""
    errors = []

    def err(name, where, message):
        errors.append((name, where, message))

    def need(name, item, where, keys):
        for k in keys:
            if k not in item or item[k] is None and k not in ("parent", "hypothesis"):
                err(name, where, f"{k} がない")

    def enum(name, where, key, value, allowed):
        if value is not None and value not in allowed:
            err(name, where, f"{key}: {value} は、定めた値({'、'.join(sorted(map(str, allowed)))})でない")

    def refs(name, where, key, values, pool, label):
        for v in as_list(values):
            if v not in pool:
                err(name, where, f"{key}: {v} が{label}にない")

    def unique(name, ids):
        seen = set()
        for i in ids:
            if i in seen:
                err(name, str(i), "id が重なっている")
            seen.add(i)

    for name in names:
        kind = ARTIFACTS[name][1]
        if name in (SAMPLES, SLIDES):
            if not (d.root / name).is_dir():
                if name in required:
                    err(name, "", "ディレクトリがない")
                continue
            d.load_dir(name)
        elif not d.exists(name):
            if name in required and name not in OPTIONAL:
                err(name, "", "ファイルがない")
            continue
        elif kind:
            d.load(name)
    for name, why in d.broken.items():
        err(name, "", why)

    have = lambda n: n in names and n not in d.broken and (d.exists(n) if not n.endswith("/") else (d.root / n).is_dir())
    facts, plan, claims = d.facts, d.plan, d.claims
    hyps = {h.get("id") for h in dicts(d.load(HYPS))} if d.exists(HYPS) else set()
    els, rels, scs = (d.model_ids(k) for k in ("elements", "relations", "scenarios"))
    story = d.story_by_id
    chapter_ids = {c.get("id") for c in d.chapters}

    if have(BRIEF):
        b = d.brief
        for item in brief_items():
            if item not in b:
                err(BRIEF, item, "項目がない")
            elif b[item]["state"] not in BRIEF_STATES:
                err(BRIEF, item, f"状態: {b[item]['state']} は、確定、推定、未定のいずれでもない")
            elif b[item]["state"] == "未定" and not d.brief_attrs(item, "決める人と時期"):
                err(BRIEF, item, "未定の項目に「- 決める人と時期: 」がない")
    if have(STYLE):
        st = d.load(STYLE)
        for key in ("limits", "point_position"):
            if key in st and not isinstance(st[key], dict):
                err(STYLE, key, "項目の集まりでない")
        for i, rule in enumerate(dicts(st.get("rules"))):
            need(STYLE, rule, f"rules[{i}]", ("id", "rule", "check"))
            enum(STYLE, f"rules[{i}]", "check", rule.get("check"), {"structure", "mechanical", "inspection"})
    if have(HYPS):
        items = dicts(d.load(HYPS))
        unique(HYPS, [h.get("id") for h in items])
        for h in items:
            need(HYPS, h, str(h.get("id")), ("id", "statement", "proposed_by"))
            enum(HYPS, str(h.get("id")), "proposed_by", h.get("proposed_by"), {"user", "session"})
    if have(PLAN):
        items = dicts(d.load(PLAN))
        unique(PLAN, [q.get("id") for q in items])
        for q in items:
            w = str(q.get("id"))
            need(PLAN, q, w, ("id", "question", "parent"))
            if q.get("parent") is not None:
                refs(PLAN, w, "parent", q.get("parent"), plan, "探索の計画")
            enum(PLAN, w, "priority", q.get("priority"), {"high", "low"})
            enum(PLAN, w, "result", q.get("result"), RESULTS)
    if have(SOURCES):
        items = dicts(d.load(SOURCES))
        unique(SOURCES, [f.get("id") for f in items])
        for f in items:
            w = str(f.get("id"))
            need(SOURCES, f, w, ("id", "kind", "statement", "verified"))
            enum(SOURCES, w, "kind", f.get("kind"), FACT_KINDS)
            if "verified" in f and not isinstance(f["verified"], bool):
                err(SOURCES, w, "verified が true でも false でもない")
            if have(PLAN):
                refs(SOURCES, w, "answers", f.get("answers"), plan, "探索の計画")
            if f.get("superseded_by"):
                refs(SOURCES, w, "superseded_by", f["superseded_by"], facts, "素材台帳")
            if isinstance(f.get("stance"), dict):
                if have(HYPS):
                    refs(SOURCES, w, "stance", list(f["stance"]), hyps, "仮説の一覧")
                for v in f["stance"].values():
                    enum(SOURCES, w, "stance", v, STANCES)
            if f.get("kind") == "derived" and not f.get("formula"):
                err(SOURCES, w, "derived に formula がない")
            if f.get("kind") == "image":
                need(SOURCES, f, w, ("file",))
                unique(SOURCES, [f"{w} regions {x.get('id')}" for x in dicts(f.get("regions"))])
                for x in dicts(f.get("regions")):
                    wr = f"{w} regions {x.get('id')}"
                    need(SOURCES, x, wr, ("id", "label", "box", "box_origin"))
                    enum(SOURCES, wr, "box_origin", x.get("box_origin"), {"recorded", "user", "estimated"})
                    box = x.get("box")
                    if box is not None and not (isinstance(box, list) and len(box) == 4 and all(isinstance(n, (int, float)) for n in box)):
                        err(SOURCES, wr, "box が4つの数値(左、上、幅、高さ)でない")
                    if x.get("element") and have(MODEL):
                        refs(SOURCES, wr, "element", x["element"], els, "仕組みの定義の要素")
    if have(MODEL):
        for key, pool in (("elements", els), ("relations", rels), ("scenarios", scs)):
            unique(MODEL, [e.get("id") for e in dicts(d.model.get(key))])
        for e in els.values():
            need(MODEL, e, e["id"], ("kind", "name"))
        for e in rels.values():
            need(MODEL, e, e["id"], ("kind", "from", "to"))
            refs(MODEL, e["id"], "from", e.get("from"), els, "要素")
            refs(MODEL, e["id"], "to", e.get("to"), els, "要素")
            refs(MODEL, e["id"], "summarizes", e.get("summarizes"), rels, "つながり")
        for e in scs.values():
            need(MODEL, e, e["id"], ("name", "steps"))
            refs(MODEL, e["id"], "steps", e.get("steps"), rels, "つながり")
        if have(SOURCES):
            for pool in (els, rels, scs):
                for e in pool.values():
                    refs(MODEL, e["id"], "evidence", e.get("evidence"), facts, "素材台帳")
    if have(TERMS):
        doc = d.terms_doc
        unique(TERMS, [t.get("id") for t in d.terms])
        tids = {t.get("id") for t in d.terms}
        for t in d.terms:
            w = str(t.get("id"))
            need(TERMS, t, w, ("id", "term", "kind", "definition"))
            enum(TERMS, w, "kind", t.get("kind"), {"noun", "action"})
            refs(TERMS, w, "not", t.get("not"), tids, "語彙表")
            if t.get("defined_in") and have(STORY):
                refs(TERMS, w, "defined_in", t["defined_in"], story, "ストーリーライン")
        for i, b in enumerate(dicts(doc.get("banned"))):
            need(TERMS, b, f"banned[{i}]", ("term", "reason"))
            refs(TERMS, f"banned[{i}]", "use", b.get("use"), tids, "語彙表")
        if not all(isinstance(a, str) for a in as_list(doc.get("allowed"))):
            err(TERMS, "allowed", "語でないものがある")
    if have(ANSWERS):
        for a in dicts(d.load(ANSWERS)):
            w = str(a.get("question"))
            need(ANSWERS, a, w, ("question", "answer"))
            if have(PLAN):
                refs(ANSWERS, w, "question", a.get("question"), plan, "探索の計画")
                refs(ANSWERS, w, "from", a.get("from"), plan, "探索の計画")
            if have(SOURCES):
                refs(ANSWERS, w, "evidence", a.get("evidence"), facts, "素材台帳")
    if have(CLAIMS):
        doc = d.claims_doc
        for k in ("answer", "summary", "hypothesis", "axis", "claims"):
            if k not in doc:
                err(CLAIMS, "", f"{k} がない")
        if doc.get("hypothesis") is not None and have(HYPS):
            refs(CLAIMS, "", "hypothesis", doc["hypothesis"], hyps, "仮説の一覧")
        unique(CLAIMS, [c.get("id") for c in dicts(doc.get("claims"))])
        for c in dicts(doc.get("claims")):
            w = str(c.get("id"))
            need(CLAIMS, c, w, ("id", "statement", "question"))
            if have(PLAN):
                refs(CLAIMS, w, "question", c.get("question"), plan, "探索の計画")
            if have(SOURCES):
                refs(CLAIMS, w, "evidence", c.get("evidence"), facts, "素材台帳")
            for i, o in enumerate(dicts(c.get("objections"))):
                need(CLAIMS, o, f"{w} objections[{i}]", ("objection", "response"))
                if have(SOURCES):
                    refs(CLAIMS, f"{w} objections[{i}]", "evidence", o.get("evidence"), facts, "素材台帳")
        for i, c in enumerate(dicts(doc.get("contradictions"))):
            need(CLAIMS, c, f"contradictions[{i}]", ("fact", "handling"))
            enum(CLAIMS, f"contradictions[{i}]", "handling", c.get("handling"), {"rebut", "qualify", "change"})
            if have(SOURCES):
                refs(CLAIMS, f"contradictions[{i}]", "fact", c.get("fact"), facts, "素材台帳")
    if have(CHAPTERS):
        doc = d.load(CHAPTERS)
        order = doc.get("order") if isinstance(doc.get("order"), dict) else {}
        if not order:
            err(CHAPTERS, "order", "order がない")
        enum(CHAPTERS, "order", "conclusion", order.get("conclusion"), {"first", "last"})
        enum(CHAPTERS, "order", "basis", order.get("basis"), {"time", "structure", "importance"})
        if not d.chapters:
            err(CHAPTERS, "chapters", "章がない")
        unique(CHAPTERS, [c.get("id") for c in d.chapters] + [s.get("id") for c in d.chapters for s in dicts(c.get("sections"))])
        for ch in d.chapters:
            w = str(ch.get("id"))
            need(CHAPTERS, ch, w, ("id", "kind"))
            enum(CHAPTERS, w, "kind", ch.get("kind"), {"intro", "body", "closing"})
            if have(CLAIMS):
                refs(CHAPTERS, w, "claims", ch.get("claims"), claims, "主張の骨子")
            for s in dicts(ch.get("sections")):
                ws = str(s.get("id"))
                need(CHAPTERS, s, ws, ("id",))
                enum(CHAPTERS, ws, "point_from", s.get("point_from"), {"chapter"})
                if have(PLAN):
                    refs(CHAPTERS, ws, "from", s.get("from"), plan, "探索の計画")
        for i, o in enumerate(dicts(doc.get("omitted"))):
            need(CHAPTERS, o, f"omitted[{i}]", ("question",))
            enum(CHAPTERS, f"omitted[{i}]", "to", o.get("to"), {"appendix", "drop"})
            if have(PLAN):
                refs(CHAPTERS, f"omitted[{i}]", "question", o.get("question"), plan, "探索の計画")
        for i, c in enumerate(dicts(doc.get("contradictions"))):
            need(CHAPTERS, c, f"contradictions[{i}]", ("fact", "chapter"))
            refs(CHAPTERS, f"contradictions[{i}]", "chapter", c.get("chapter"), chapter_ids, "章構成")
            if have(SOURCES):
                refs(CHAPTERS, f"contradictions[{i}]", "fact", c.get("fact"), facts, "素材台帳")
        for i, o in enumerate(dicts(doc.get("objections"))):
            need(CHAPTERS, o, f"objections[{i}]", ("claim", "index", "to"))
            enum(CHAPTERS, f"objections[{i}]", "to", o.get("to"), {"body", "appendix"})
            if have(CLAIMS) and o.get("claim") is not None:
                n = len(dicts(claims.get(o["claim"], {}).get("objections")))
                if o["claim"] not in claims or not isinstance(o.get("index"), int) or not 0 <= o["index"] < n:
                    err(CHAPTERS, f"objections[{i}]", f"claim: {o.get('claim')}、index: {o.get('index')} の反論が主張の骨子にない")
    if have(STORY):
        unique(STORY, [s.get("id") for s in d.story])
        for s in d.story:
            w = str(s.get("id"))
            need(STORY, s, w, ("id", "chapter"))
            if have(CHAPTERS) and s.get("chapter") != "appendix":
                refs(STORY, w, "chapter", s.get("chapter"), chapter_ids, "章構成")
            enum(STORY, w, "role", s.get("role"), roles_vocab())
            enum(STORY, w, "point_from", s.get("point_from"), {"section"})
            enum(STORY, w, "provenance", s.get("provenance"), {"cited", "proposal", "practice"})
            if have(PLAN):
                refs(STORY, w, "from", s.get("from"), plan, "探索の計画")
            if have(SOURCES):
                refs(STORY, w, "evidence", s.get("evidence"), facts, "素材台帳")
                refs(STORY, w, "contradiction", s.get("contradiction"), facts, "素材台帳")
            if s.get("appendix_of"):
                target = story.get(s["appendix_of"])
                if not target or target.get("chapter") == "appendix":
                    err(STORY, w, f"appendix_of: {s['appendix_of']} が本編のスライドでない")
            if isinstance(s.get("objection"), dict) and have(CLAIMS):
                o = s["objection"]
                n = len(dicts(claims.get(o.get("claim"), {}).get("objections")))
                if o.get("claim") not in claims or not isinstance(o.get("index"), int) or not 0 <= o["index"] < n:
                    err(STORY, w, f"objection: {o} の反論が主張の骨子にない")
    if have(STATES):
        for st in dicts(d.load(STATES)):
            w = str(st.get("chapter"))
            need(STATES, st, w, ("chapter", "entry", "exit"))
            if have(CHAPTERS):
                refs(STATES, w, "chapter", st.get("chapter"), chapter_ids, "章構成")
            for key in ("entry", "exit"):
                part = st.get(key)
                if part is not None and not isinstance(part, dict):
                    err(STATES, w, f"{key} が項目の集まりでない")
                elif isinstance(part, dict) and have(CLAIMS):
                    refs(STATES, w, f"{key}.accepted", part.get("accepted"), claims, "主張の骨子")
    if have(SCENARIOS):
        for i, s in enumerate(dicts(d.load(SCENARIOS))):
            need(SCENARIOS, s, f"[{i}]", ("scenario",))
            enum(SCENARIOS, f"[{i}]", "scenario", s.get("scenario"), set(scenario_ids()))
    if have(PROOF):
        items = dicts(d.load(PROOF))
        unique(PROOF, [p.get("id") for p in items])
        for p in items:
            w = str(p.get("id"))
            need(PROOF, p, w, ("id",))
            if have(STORY):
                refs(PROOF, w, "id", p.get("id"), story, "ストーリーライン")
            enum(PROOF, w, "base", p.get("base"), {"none", "image"})
            for h in as_list(p.get("holds")):
                enum(PROOF, w, "holds", h, implications_vocab())
            if "real" in p and not isinstance(p["real"], bool):
                err(PROOF, w, "real が true でも false でもない")
    if have(PATTERNS):
        for i, t in enumerate(d.table):
            w = f"[{i}]"
            need(PATTERNS, t, w, ("relation", "size", "base", "pattern"))
            enum(PATTERNS, w, "relation", t.get("relation"), relations_vocab())
            enum(PATTERNS, w, "size", t.get("size"), {"any", "within", "over"})
            enum(PATTERNS, w, "base", t.get("base"), {"none", "image"})
            if t.get("pattern") is not None and t["pattern"] not in d.pattern_defs:
                err(PATTERNS, w, f"pattern: {t['pattern']} が型の定義にない")
    for dirname in (SAMPLES, SLIDES):
        if not have(dirname):
            continue
        seen = set()
        for name, specs in d.load_dir(dirname).items():
            for s in specs:
                w = str(s.get("id"))
                need(name, s, w, ("id",) if dirname == SAMPLES else ("id", "status"))
                if s.get("id") in seen:
                    err(name, w, "id が重なっている")
                seen.add(s.get("id"))
                enum(name, w, "status", s.get("status"), {"done", "blocked"})
                if not isinstance(s.get("body"), dict) or not s["body"].get("type"):
                    err(name, w, "body.type がない")
                if have(SOURCES):
                    refs(name, w, "sources", s.get("sources"), facts, "素材台帳")
    return errors


# ---------------------------------------------------------------- 実行

STAGE_NAMES = {0: "依頼の確定", 1: "探索", 2: "主張の整理", 3: "章立て設計", 4: "ストーリーライン",
               5: "立証設計", 6: "表現設計", 7: "スライド仕様", 8: "全体検査", 9: "仕上げ"}


def machine_ids(stage=None):
    out = []
    for cid, e in ledger().items():
        if is_machine(e) and (stage is None or stage in stages_of(e)):
            out.append(cid)
    return out


def available(deck, name):
    if name == BRIEF:
        return deck.brief is not None
    if name.endswith("/"):
        return True
    return deck.load(name) is not None


def run_checks(deck, selection):
    """selection は (検査のID, 工程) の一覧。KX の検査は、工程ごとの文に当てる。"""
    report = Report()
    wanted = {}
    for cid, stage in selection:
        wanted.setdefault(cid, []).append(stage)

    def run(fn, ids, needs, *args):
        missing = [n for n in needs if not available(deck, n)]
        before = len(report.rows)
        if missing:
            for cid in ids:
                report.add(cid, missing[0], None, "fail", missing[0],
                           "成果物がない、または読めない: " + "、".join(f"{m}({deck.broken.get(m, 'ない')})" for m in missing))
            return
        try:
            fn(deck, report, *args)
        except Exception as e:      # 書式の誤りで検査を続けられない場合
            for cid in ids:
                report.add(cid, needs[0] if needs else None, None, "fail", type(e).__name__, f"検査を実行できない。書式の誤りがある: {e}")
        report.rows[before:] = [row for row in report.rows[before:] if row["check"] in ids]
        done = {row["check"] for row in report.rows[before:]}
        for cid in ids:
            if cid not in done:
                report.add(cid, None, None, "pass", "対象がない")

    for fn, ids, needs in FUNCTIONS:
        if fn in KX_FUNCTIONS:
            for stage in KX_STAGES:
                chosen = [c for c in ids if stage in wanted.get(c, [])]
                if chosen:
                    before = len(report.rows)
                    run(fn, chosen, list(needs) + KX_NEEDS[stage], stage_texts(deck, stage))
                    for row in report.rows[before:]:
                        row["stage"] = stage
        else:
            chosen = [c for c in ids if c in wanted]
            if chosen:
                run(fn, chosen, needs)
    return report.rows


def select(stage=None, task=None, cid=None):
    """実行する検査を選ぶ。(実装した検査の (ID, 工程) の一覧、実装していない検査のIDの一覧) を返す。"""
    pairs = []
    if task is not None:
        t = tasks()[task]
        stage_of_task = as_list(t.get("stage"))
        for c in as_list(t.get("checks")):
            e = ledger().get(c)
            if e and is_machine(e):
                for s in (stage_of_task if c.startswith("KX") else stages_of(e)[:1]):
                    pairs.append((c, s))
    elif cid is not None:
        e = ledger()[cid]
        targets = e.get("refers") or [cid]
        for c in targets:
            if is_machine(ledger()[c]):
                for s in (stages_of(e) if c.startswith("KX") and "refers" in e else stages_of(ledger()[c])):
                    if stage is None or s == stage:
                        pairs.append((c, s))
    else:
        for s in ([stage] if stage is not None else range(0, 9)):
            for c in machine_ids(s):
                pairs.append((c, s))
    todo = sorted({c for c, _ in pairs if c not in CHECKS})
    return [(c, s) for c, s in pairs if c in CHECKS], todo


def format_scope(deck, stage=None, task=None):
    """書式を確かめる成果物と、なければ誤りとする成果物。"""
    if task is not None:
        names = set()
        for i in as_list(tasks()[task].get("inputs")):
            base = i.split("#")[0]
            if base in ARTIFACTS:
                names.add(base)
        return sorted(names), names
    top = 8 if stage is None else stage
    names = [n for n, (s, _) in ARTIFACTS.items() if s <= top]
    required = {n for n in names if stage is not None and ARTIFACTS[n][0] == stage}
    if stage is None:
        required = {n for n in names if deck.exists(n)}
    return names, required


def level(row):
    if row["verdict"] == "pass":
        return "pass"
    return "warning" if is_warning(row["check"]) else "fail"


def print_results(rows, errors, todo, verbose):
    if errors:
        print(f"書式: 誤り {len(errors)}件")
        for name, where, message in errors:
            print(f"  {name} {where}: {message}".replace("  :", ":"))
    by = {}
    for row in rows:
        by.setdefault(row["check"], []).append(row)
    counts = {"pass": 0, "fail": 0, "warning": 0}
    order = list(ledger())
    for cid, items in sorted(by.items(), key=lambda kv: order.index(kv[0])):
        worst = "fail" if any(level(i) == "fail" for i in items) else "warning" if any(level(i) == "warning" for i in items) else "pass"
        counts[worst] += 1
        bad = [i for i in items if i["verdict"] == "fail"]
        e = ledger()[cid]
        print(f"{cid} {VERDICT_JA[worst]} {e['check']}({len(items)}件のうち、条件を満たさないもの {len(bad)}件)")
        for i in items if verbose else bad:
            where = " ".join(x for x in (i["artifact"], i["item"]) if x) or "全体"
            mark = "○" if i["verdict"] == "pass" else "×"
            print(f"  {mark} {where}: 「{i['quote']}」" + (f" 理由: {i['reason']}" if i["reason"] else ""))
    print(f"合格 {counts['pass']}件、不合格 {counts['fail']}件、警告 {counts['warning']}件、書式の誤り {len(errors)}件")
    if todo:
        print(f"実装していない機械の検査 {len(todo)}件: " + "、".join(todo))


# ---------------------------------------------------------------- 検査の記録を書く

def git_commit(root):
    """資料のディレクトリの版。Gitで管理していなければ None。"""
    try:
        out = subprocess.run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"], capture_output=True, text=True)
    except OSError:
        return None
    return out.stdout.strip() or None if out.returncode == 0 else None


def git_dirty(root):
    """コミットしていない変更がある成果物の一覧。検査の記録と状態の記録は除く。"""
    try:
        out = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--", "."], capture_output=True, text=True)
    except OSError:
        return []
    if out.returncode != 0:
        return []
    names = [line[3:].strip().strip('"') for line in out.stdout.split("\n") if line.strip()]
    return [n for n in names if "checks/" not in n and not n.endswith(STATUS) and "runs/" not in n]


def next_round(root, task, target):
    best = 0
    for p in (Path(root) / "checks").glob(f"{task}--{target}--*.yaml"):
        m = re.fullmatch(rf"{re.escape(task)}--{re.escape(target)}--(\d+)\.yaml", p.name)
        if m:
            best = max(best, int(m.group(1)))
    return best + 1


def write_record(root, task, target, rows, commit):
    """検査の記録を1つ書く。書式は docs/rework.md の「検査の記録」。"""
    root = Path(root)
    (root / "checks").mkdir(exist_ok=True)
    rnd = next_round(root, task, target)
    artifacts = sorted({r["artifact"] for r in rows if r["artifact"] and (root / r["artifact"]).exists()
                        and r["artifact"] not in (STATUS,) and not r["artifact"].endswith("/")})
    results = []
    for r in rows:
        out = {"check": r["check"]}
        if r["item"]:
            out["item"] = r["item"]
        out["verdict"] = r["verdict"]
        out["quote"] = r["quote"]
        if r["verdict"] == "fail":
            out["reason"] = r["reason"]
        results.append(out)
    if not artifacts:
        artifacts = sorted({r["artifact"] for r in rows if r["artifact"]}) or ["all"]
    doc = {"task": task, "target": artifacts[0] if len(artifacts) == 1 else artifacts,
           "commit": commit, "round": rnd, "results": results}
    path = root / "checks" / f"{task}--{target}--{rnd}.yaml"
    path.write_text(f"# checks/{path.name}\n" + yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=1000),
                    encoding="utf-8")
    return path


# ---------------------------------------------------------------- 記録の書式を確かめる

def target_files(target):
    return [t for t in as_list(target) if isinstance(t, str)]


def check_records(root):
    """検査の記録(checks/)と実行の記録(runs/)の書式を確かめる。(ファイル, 箇所, 誤り) の一覧を返す。"""
    root, errors = Path(root), []
    deck = Deck(root)
    chapter_ids = {c.get("id") for c in deck.chapters} | {"appendix"}

    def err(path, where, message):
        errors.append((str(path.relative_to(root)), where, message))

    for path in sorted((root / "checks").glob("*")) if (root / "checks").is_dir() else []:
        m = re.fullmatch(r"(.+?)--(.+?)--(\d+)\.yaml", path.name)
        if not m:
            err(path, "", "ファイル名が「作業のid--対象--回.yaml」の形でない")
            continue
        task, target, rnd = m.group(1), m.group(2), int(m.group(3))
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            err(path, "", "YAMLとして読めない")
            continue
        if not isinstance(doc, dict):
            err(path, "", "最上位が項目の集まりでない")
            continue
        t = tasks().get(task)
        if not t:
            err(path, "", f"作業 {task} が工程表にない")
        if target != "all" and deck.chapters and target not in chapter_ids:
            err(path, "", f"対象 {target} が、all でも章のIDでもない")
        for key in ("task", "target", "commit", "round", "results"):
            if key not in doc:
                err(path, "", f"{key} がない")
        if doc.get("task") != task:
            err(path, "task", f"task: {doc.get('task')} が、ファイル名の作業と違う")
        if doc.get("round") != rnd:
            err(path, "round", f"round: {doc.get('round')} が、ファイル名の回と違う")
        if "target" in doc and not target_files(doc["target"]):
            err(path, "target", "target に対象がない")
        if "commit" in doc and not (doc["commit"] is None or isinstance(doc["commit"], (str, int))):
            err(path, "commit", "commit が版のIDでない")
        if t:
            machine = t.get("role") == "machine"
            if machine and "model" in doc:
                err(path, "model", "機械的な検査の記録が model を持つ")
            if not machine and not doc.get("model"):
                err(path, "model", "判定したモデル(model)がない")
        allowed = set(as_list(t.get("checks"))) if t else set()
        if not isinstance(doc.get("results"), list) or not doc["results"]:
            err(path, "results", "results に行がない")
        for i, row in enumerate(as_list(doc.get("results"))):
            w = f"results[{i}]"
            if not isinstance(row, dict):
                err(path, w, "項目の集まりでない")
                continue
            cid = row.get("check")
            if cid not in ledger():
                err(path, w, f"check: {cid} が検査の台帳にない")
            elif "refers" in ledger()[cid]:
                err(path, w, f"check: {cid} は検査を束ねる項目である。指す検査のIDで書く")
            elif t and cid not in allowed:
                err(path, w, f"check: {cid} が、作業 {task} の検査でない")
            if row.get("verdict") not in ("pass", "fail"):
                err(path, w, f"verdict: {row.get('verdict')} が pass でも fail でもない")
            if not isinstance(row.get("quote"), str) or not row["quote"].strip():
                err(path, w, "quote がない。合格の行にも引用を書く")
            if row.get("verdict") == "fail" and not text_of(row.get("reason")).strip():
                err(path, w, "不合格の行に reason がない")
            for key in row:
                if key not in ("check", "item", "verdict", "quote", "reason"):
                    err(path, w, f"知らない項目 {key}")

    for path in sorted((root / "runs").glob("*")) if (root / "runs").is_dir() else []:
        m = re.fullmatch(r"(.+?)--(\d+)\.yaml", path.name)
        if not m:
            err(path, "", "ファイル名が「場面の識別子--回.yaml」の形でない")
            continue
        scenario, rnd = m.group(1), int(m.group(2))
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            err(path, "", "YAMLとして読めない")
            continue
        if not isinstance(doc, dict):
            err(path, "", "最上位が項目の集まりでない")
            continue
        if scenario not in scenario_ids():
            err(path, "", f"場面 {scenario} が、定めた識別子でない")
        for key in ("scenario", "commit", "round", "steps"):
            if key not in doc:
                err(path, "", f"{key} がない")
        if doc.get("scenario") != scenario:
            err(path, "scenario", f"scenario: {doc.get('scenario')} が、ファイル名の場面と違う")
        if doc.get("round") != rnd:
            err(path, "round", f"round: {doc.get('round')} が、ファイル名の回と違う")
        if not isinstance(doc.get("steps"), list) or not doc["steps"]:
            err(path, "steps", "steps に行がない")
        for i, step in enumerate(as_list(doc.get("steps"))):
            w = f"steps[{i}]"
            if not isinstance(step, dict):
                err(path, w, "項目の集まりでない")
                continue
            if not step.get("slide"):
                err(path, w, "slide がない")
            if not isinstance(step.get("understood"), str) or not step["understood"].strip():
                err(path, w, "understood がない")
            if "carried" in step and not (isinstance(step["carried"], list) and all(isinstance(x, str) for x in step["carried"])):
                err(path, w, "carried が語の並びでない")
            for key in step:
                if key not in ("slide", "understood", "carried", "stuck"):
                    err(path, w, f"知らない項目 {key}")
        if "findings" in doc and doc["findings"] is not None and not isinstance(doc["findings"], list):
            err(path, "findings", "findings が並びでない")
        for i, f in enumerate(as_list(doc.get("findings"))):
            w = f"findings[{i}]"
            if not isinstance(f, dict):
                err(path, w, "項目の集まりでない")
                continue
            if not f.get("slide"):
                err(path, w, "slide がない")
            if f.get("kind") not in finding_kinds():
                err(path, w, f"kind: {f.get('kind')} が、エラーの種類の識別子でない")
            if not isinstance(f.get("note"), str) or not f["note"].strip():
                err(path, w, "note がない")
    return errors


# ---------------------------------------------------------------- 実装の状況

def coverage():
    """(工程, 実装済み, 一部だけ実装, 未実装) の一覧と、分類のない検査の一覧を返す。"""
    table, orphan = [], []
    keys = list(range(0, 10)) + ["X"]
    for key in keys:
        ids = [c for c, e in ledger().items() if is_machine(e) and
               (c.startswith("KX") if key == "X" else not c.startswith("KX") and stages_of(e) == [key])]
        full = [c for c in ids if c in CHECKS and not CHECKS[c][2]]
        part = [c for c in ids if c in CHECKS and CHECKS[c][2]]
        none = [c for c in ids if c not in CHECKS]
        orphan += [c for c in none if c not in TODO] + [c for c in ids if c in CHECKS and c in TODO]
        table.append((key, full, part, none))
    return table, orphan


def print_coverage():
    table, orphan = coverage()
    total = [0, 0, 0]
    print("台帳の機械の検査の、実装の状況(束ねる項目を除く)")
    print("| 工程 | 機械の検査 | 実装済み | うち一部だけ | 未実装 |")
    print("|---|---|---|---|---|")
    for key, full, part, none in table:
        n = len(full) + len(part) + len(none)
        total = [total[0] + len(full) + len(part), total[1] + len(part), total[2] + len(none)]
        name = "複数の工程" if key == "X" else f"{key} {STAGE_NAMES[key]}"
        print(f"| {name} | {n} | {len(full) + len(part)} | {len(part)} | {len(none)} |")
    print(f"| 計 | {total[0] + total[2]} | {total[0]} | {total[1]} | {total[2]} |")
    for key, full, part, none in table:
        name = "複数の工程で使う検査" if key == "X" else f"工程{key}"
        print(f"\n{name}")
        print("  実装済み: " + ("、".join(full) or "なし"))
        for c in part:
            print(f"  一部だけ実装: {c} {CHECKS[c][2]}")
        for c in none:
            kind, why = TODO.get(c, ("分類なし", ""))
            print(f"  未実装: {c} [{kind}] {why}")
    kinds = {}
    for c, (kind, _) in TODO.items():
        if c not in CHECKS:
            kinds.setdefault(kind, []).append(c)
    print("\n未実装の理由の分類")
    for kind, ids in kinds.items():
        print(f"  {kind}: {len(ids)}件")
    if orphan:
        print("\n道具の誤り。実装と未実装の表が台帳と合わない: " + "、".join(orphan))
    return 1 if orphan else 0


# ---------------------------------------------------------------- 入口

def chapters_with_specs(deck):
    order = [c.get("id") for c in deck.chapters] + ["appendix"]
    have = {deck.story_by_id.get(s.get("id"), {}).get("chapter") for _, s in deck.slide_specs(chapter=None)}
    return [c for c in order if c in have]


def run(root, stage=None, task=None, cid=None, chapter=None):
    """検査を実行する。(結果の行, 書式の誤り, 実装していない検査のID) を返す。"""
    deck = Deck(root, chapter)
    selection, todo = select(stage, task, cid)
    task_stage = as_list(tasks()[task].get("stage"))[0] if task else None
    scope_stage = stage if stage is not None else task_stage if task else (max(s for _, s in selection) if cid and selection else None)
    names, required = format_scope(deck, scope_stage, task if task else None)
    errors = check_format(deck, names, required)
    rows = run_checks(deck, [p for p in selection if p[0] != "K08-01"])
    if any(c == "K08-01" for c, _ in selection):
        inner = Deck(root)
        inner_sel = [(c, s) for s in range(0, 8) for c in machine_ids(s) if c in CHECKS]
        inner_names, inner_req = format_scope(inner, None, None)
        inner_errors = check_format(inner, inner_names, inner_req)
        inner_rows = run_checks(inner, inner_sel)
        bad = sorted({r["check"] for r in inner_rows if level(r) == "fail"})
        ok = not bad and not inner_errors
        why = "機械的な検査に不合格がある: " + "、".join(bad) if bad else f"書式の誤りが {len(inner_errors)}件ある"
        rows.append({"check": "K08-01", "artifact": None, "item": None, "verdict": "pass" if ok else "fail",
                     "quote": f"工程0から7の機械の検査 {len({r['check'] for r in inner_rows})}件を再実行した",
                     "reason": None if ok else why})
    return rows, errors, todo


def main(argv=None):
    ap = argparse.ArgumentParser(description="機械の検査。台帳のIDごとに、成果物を検査する。")
    ap.add_argument("deck", nargs="?", help="資料のディレクトリ")
    ap.add_argument("--stage", type=int, choices=range(0, 10), metavar="N", help="工程の番号(0から9)")
    ap.add_argument("--task", help="工程表の機械の作業の id")
    ap.add_argument("--id", dest="cid", help="検査のID")
    ap.add_argument("--chapter", help="工程7の検査を、この章のスライドに限る")
    ap.add_argument("--build", help="描画の結果(tools/render.py の出力)の置き場。既定は <資料のディレクトリ>/build")
    ap.add_argument("--write", action="store_true", help="検査の記録と状態の記録を書く")
    ap.add_argument("--allow-uncommitted", action="store_true", help="コミットしていない変更があっても記録を書く。commit は null になる")
    ap.add_argument("--coverage", action="store_true", help="台帳の機械の検査の、実装の状況を出す")
    ap.add_argument("--records", action="store_true", help="検査の記録と実行の記録の書式を確かめる")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true", help="合格の行も出す")
    args = ap.parse_args(argv)

    if args.coverage:
        return print_coverage()
    if args.build:
        global BUILD_DIR
        BUILD_DIR = args.build
    if not args.deck:
        ap.error("資料のディレクトリがない")
    if not Path(args.deck).is_dir():
        ap.error(f"{args.deck} はディレクトリでない")
    if args.records:
        errors = check_records(args.deck)
        if args.json:
            print(json.dumps([{"file": f, "where": w, "error": m} for f, w, m in errors], ensure_ascii=False, indent=2))
        else:
            for f, w, m in errors:
                print(f"{f} {w}: {m}".replace(" :", ":"))
            print(f"記録の書式の誤り {len(errors)}件")
        return 1 if errors else 0
    if sum(x is not None for x in (args.stage, args.task, args.cid)) > 1 and not (args.cid and args.stage is not None and args.task is None):
        ap.error("--stage、--task、--id は、どれか1つを指定する(--id に --stage を添えるのはよい)")
    if args.task is not None and (args.task not in tasks() or tasks()[args.task].get("role") != "machine"):
        ap.error(f"{args.task} は、工程表の機械の作業でない")
    if args.cid is not None and args.cid not in ledger():
        ap.error(f"{args.cid} は、検査の台帳にない")
    if args.write and args.task is None and args.stage is None:
        ap.error("--write には、--task か --stage が要る")

    rows, errors, todo = run(args.deck, args.stage, args.task, args.cid, args.chapter)
    written = []
    if args.write:
        import status
        dirty = git_dirty(args.deck)
        commit = git_commit(args.deck)
        if dirty and not args.allow_uncommitted:
            print("コミットしていない変更があるため、記録を書かない: " + "、".join(dirty[:5]), file=sys.stderr)
            return 2
        if dirty:
            commit = None
        if errors:
            print("書式の誤りがあるため、記録を書かない。", file=sys.stderr)
        else:
            names = [args.task] if args.task else [t["id"] for t in tasks().values()
                                                   if t.get("role") == "machine" and as_list(t.get("stage")) == [args.stage]]
            for name in names:
                ids = {c for c, _ in select(task=name)[0]}
                if not ids:
                    continue
                per_chapter = any(i.split("#")[0] == SLIDES for i in as_list(tasks()[name].get("inputs"))) \
                    and as_list(tasks()[name].get("stage")) == [7]
                if per_chapter:
                    deck = Deck(args.deck)
                    for ch in ([args.chapter] if args.chapter else chapters_with_specs(deck)):
                        ch_rows, _, _ = run(args.deck, task=name, chapter=ch)
                        written.append(write_record(args.deck, name, ch, ch_rows, commit))
                else:
                    task_rows = [r for r in rows if r["check"] in ids] if args.task is None else rows
                    if task_rows:
                        written.append(write_record(args.deck, name, "all", task_rows, commit))
            for line in status.record_check(args.deck, [p.name for p in written]):
                print(line, file=sys.stderr)

    if args.json:
        print(json.dumps({"results": [dict(r, level=level(r)) for r in rows],
                          "format_errors": [{"artifact": a, "where": w, "error": m} for a, w, m in errors],
                          "not_implemented": todo,
                          "written": [str(p) for p in written]}, ensure_ascii=False, indent=2))
    else:
        print_results(rows, errors, todo, args.verbose)
        for p in written:
            print(f"検査の記録を書いた: {p}")
    return 1 if errors or any(level(r) == "fail" for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
