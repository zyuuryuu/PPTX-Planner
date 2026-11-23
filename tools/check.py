#!/usr/bin/env python3
"""機械的な検査の最小版。

使い方: python tools/check.py <資料のディレクトリ> [--stage N] [--json]

工程0から6の合格条件のうち、「(機械)」と書かれ、構造だけで判定できるものを検査する。
文の検査(字数、読点、辞書、語彙の抜き出し、数値の正規化照合)は実装していない。
実装していない条件は「未実装」として一覧に出す。
"""
import argparse
import json
import re
import sys
from pathlib import Path

import yaml

PASS, FAIL, WARN, TODO, UNKNOWN, ABSENT = "合格", "不合格", "警告", "未実装", "判定不能", "成果物なし"

STAGE_NAMES = {
    0: "依頼の確定", 1: "探索", 2: "主張の整理", 3: "章立て設計",
    4: "ストーリーライン", 5: "立証設計", 6: "表現設計",
}

# 成果物ごとの、工程と最上位の型。任意の成果物は、なくても「成果物なし」を出さない。
ARTIFACTS = {
    "00-brief.md": (0, None),
    "style.yaml": (0, dict),
    "01-hypotheses.yaml": (1, list),
    "01-plan.yaml": (1, list),
    "01-sources.yaml": (1, list),
    "01-model.yaml": (1, dict),
    "02-answers.yaml": (2, list),
    "02-claims.yaml": (2, dict),
    "03-chapters.yaml": (3, dict),
    "04-storyline.yaml": (4, list),
    "04-chapter-states.yaml": (4, list),
    "04-scenarios.yaml": (4, list),
    "05-proof.yaml": (5, list),
    "06-patterns.yaml": (6, list),
    "terms.yaml": (None, dict),
}
OPTIONAL = {"01-model.yaml", "terms.yaml"}

BRIEF_ITEMS = [
    "資料の型", "伝え方", "主な読み手", "副次的な読み手", "読み手が既に知っていること",
    "読み手の立場と懸念", "目的", "答えるべき問い", "扱わない範囲", "使われる場面",
    "書き手の立場", "制約", "外に出せない情報", "手元の資料", "型ごとの追加の項目",
]
BRIEF_STATES = {"確定", "推定", "未定"}
BRIEF_MUST_BE_FIXED = ["主な読み手", "目的", "答えるべき問い"]

FACT_KINDS = {"fact", "derived", "testimony", "image", "inference", "opinion"}
USABLE_KINDS = {"fact", "derived", "testimony", "image"}
RESULTS = {"answered", "partial", "not-found", "disputed"}
STANCES = {"supports", "contradicts", "neutral"}

# docs/vocabulary.md の主張の種類
RELATIONS = {
    "composition", "item-comparison", "trend", "distribution", "correlation",
    "process", "structure", "contrast-options", "contrast-before-after", "causality",
    "positioning", "list", "statement",
    "architecture", "entity-relation", "interaction", "state-transition",
    "branching-flow", "schedule", "exhibit",
}
# docs/visual-grammar.md の含意の語彙
IMPLICATIONS = {
    "grouped", "partition", "equal-weight", "comparable", "ordered", "causal",
    "hierarchical", "cyclic", "connected", "proportional", "independent-axes",
    "distinct-kinds", "emphasized", "opposed", "contained", "shared", "ascending",
    "main-and-sub",
}
# docs/patterns.md の「付属する型の候補」の表の「形が伝える含意」
PATTERN_IMPLIES = {
    "bar-chart": ["comparable", "proportional"],
    "stacked-bar-chart": ["partition", "proportional", "comparable"],
    "line-chart": ["ordered", "proportional"],
    "pie-chart": ["partition", "proportional"],
    "scatter-chart": ["proportional"],
    "histogram": ["ordered", "proportional"],
    "step-flow": ["ordered"],
    "tree": ["hierarchical"],
    "versus": ["opposed", "comparable"],
    "before-after": ["opposed", "ordered"],
    "cause-chain": ["causal", "ordered"],
    "two-axis": ["independent-axes", "comparable"],
    "plain-list": [],
    "statement": ["emphasized"],
    "big-number": ["emphasized"],
    "table": ["comparable"],
    "architecture-diagram": ["connected"],
    "er-diagram": ["connected"],
    "sequence-diagram": ["ordered", "connected"],
    "state-diagram": ["connected"],
    "flowchart": ["ordered", "connected"],
    "gantt-chart": ["ordered", "proportional"],
    "annotated-image-steps": ["ordered"],
    "annotated-image-callouts": ["connected"],
    "image-before-after": ["opposed", "ordered"],
    "exhibit-image": [],
}
# docs/stages/08-integration.md の「テストの場面」の表
SCENARIOS = ["主な読み手の通読", "反対の立場の通読", "要約だけ", "途中から", "発表の通し", "過去の指摘"]

# 実装していない条件。(工程, 条件, 理由)
NOT_IMPLEMENTED = [
    (0, "style.yaml が、資料の型の定義の limits と個人の表現規約を写している",
     "style.yaml があることだけを見る。limits の値と、資料の型の定義の置き場が未確定"),
    (1, "資料の型の定義が定める観点が、全て問いに含まれる", "資料の型の定義がデータとして置かれていない"),
    (1, "全ての derived の計算式が、元の事実の値から再計算して一致する",
     "formula の書式が未定義。formula があることだけを見る"),
    (1, "fact の value と unit が、quote の中の数値と単位に一致する", "数値の正規化照合"),
    (1, "引用した図では、引用元の表記に必要な情報がある", "必要な項目が未定義"),
    (2, "問いごとの答えの中の数値が、根拠の事実の値と一致する", "数値の正規化照合"),
    (2, "主張の中の数値が、根拠の事実の値と一致する", "数値の正規化照合"),
    (2, "summary が1文である。字数が上限以下である", "文の検査"),
    (2, "summary の中の数値が、主張と事実の値と一致する", "数値の正規化照合"),
    (2, "answer、summary、各主張が、文章の書き方の検査と、使う語彙の検査を通る", "文の検査、語彙の抜き出し"),
    (3, "章の message が、文章の書き方の検査と、使う語彙の検査を通る", "文の検査、語彙の抜き出し"),
    (4, "「また」「および」などの接続を含む見出しを挙げる", "文の検査"),
    (4, "見出しの字数が、資料の表現規約が定める上限以下である", "文の検査"),
    (4, "見出しが、文章の書き方の検査と、使う語彙の検査を通る", "文の検査、語彙の抜き出し"),
    (4, "同じ事実、同じ対象を扱う見出しの組を挙げる", "対象の抜き出しが文の検査にあたる"),
    (4, "見出しの中の数値が、evidence の事実の値と一致する", "数値の正規化照合"),
    (5, "見出しが「全体」を述べるスライドの view が、該当する種類の要素を全て含む", "見出しの文の判定が要る"),
    (5, "「言い切り」と「並列の列挙」の割合が目安を超える場合の警告", "目安の値が未確定"),
    (6, "量の区分(size)を、立証の設計の中身と型の収容量から決める",
     "収容量の値が未確定。対応表との照合は、主張の種類と土台だけで行う"),
    (6, "スライドの holds の主な関係が、型の expresses に含まれる",
     "付属する型の候補の表に expresses がない"),
    (6, "size: over の行に対応するスライドに、収容量を超える理由がある", "理由の置き場が未定義"),
    (6, "全ての型が、選んだ描画の実装とテンプレートで実現できる", "描画の実装が未定"),
    (6, "成果物の表の全ての規則が、資料の表現規約にある", "style.yaml の書式が未定義"),
    (6, "複数の図に出る対象の全てに、色が割り当てられている", "style.yaml の書式が未定義"),
    (6, "見本の描画上の診断が0件である。文字の大きさ、色の差、色相の数が基準を満たす", "描画の実装が未定"),
    (6, "同じ概念を指していそうな語などの候補の全てに、ユーザーの判断が記録されている", "記録の置き場が未定義"),
    (6, "対象を指す語の全てについて、同じ対象を指しうる別の語を banned に入れるかを決めている",
     "決めた記録の置き場が未定義"),
]


def L(x):
    return x if isinstance(x, list) else []


def D(x):
    return x if isinstance(x, dict) else {}


def blank(x):
    return x is None or x == "" or x == [] or x == {}


class Checker:
    def __init__(self, root):
        self.root = Path(root)
        self.results = []
        self.data = {}      # 読めた成果物
        self.broken = set()  # 壊れている成果物
        self.load_all()

    # ---- 読み込み ----
    def load_all(self):
        for name, (_, kind) in ARTIFACTS.items():
            path = self.root / name
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as e:
                self.broken.add(name)
                self.load_errors = getattr(self, "load_errors", []) + [(name, f"{name}: 読めない({e})")]
                continue
            if kind is None:
                self.data[name] = text
                continue
            try:
                value = yaml.safe_load(text)
            except yaml.YAMLError as e:
                mark = getattr(e, "problem_mark", None)
                pos = f"{mark.line + 1}行 {mark.column + 1}列" if mark else "位置不明"
                problem = getattr(e, "problem", None) or str(e).splitlines()[0]
                self._load_error(name, f"{name}: {pos}: YAMLとして読めない({problem})")
                continue
            if not isinstance(value, kind):
                want = "一覧" if kind is list else "項目と値の組"
                self._load_error(name, f"{name}: 最上位が{want}でない")
                continue
            if kind is list and any(not isinstance(v, dict) for v in value):
                idx = [i for i, v in enumerate(value) if not isinstance(v, dict)]
                self._load_error(name, f"{name}: {idx[0] + 1}件目が、項目と値の組でない")
                continue
            self.data[name] = value

    def _load_error(self, name, message):
        self.broken.add(name)
        self.load_errors = getattr(self, "load_errors", []) + [(name, message)]

    def get(self, name):
        return self.data.get(name)

    # ---- 結果の記録 ----
    def add(self, stage, condition, status, where=(), note=""):
        self.results.append({"stage": stage, "condition": condition, "status": status,
                             "where": list(where), "note": note})

    def rule(self, stage, condition, needs, fn, level=FAIL):
        """fn は、該当箇所の一覧を返す。空なら合格。needs の成果物が読めなければ判定不能。"""
        missing = [n for n in needs if n not in self.data]
        if missing:
            # 同じ工程の成果物がない場合は「成果物なし」の行で示しているので、重ねて出さない
            if all(ARTIFACTS[n][0] == stage and n not in self.broken and n not in OPTIONAL for n in missing):
                return
            why = "、".join(n + ("が壊れている" if n in self.broken else "がない") for n in missing)
            self.add(stage, condition, UNKNOWN, note=why)
            return
        try:
            out = fn()
        except Exception as e:  # 項目の型が想定と違う場合
            self.add(stage, condition, FAIL, [f"項目の形式が想定と違う({type(e).__name__}: {e})"])
            return
        if isinstance(out, tuple):   # (状態, 該当箇所, 注)
            self.add(stage, condition, out[0], out[1], out[2] if len(out) > 2 else "")
        else:
            self.add(stage, condition, level if out else PASS, out)

    # ---- 共通の索引 ----
    def ids(self, name, key="id", sub=None):
        d = self.get(name)
        if sub:
            d = D(d).get(sub)
        return {e.get(key) for e in L(d) if isinstance(e, dict) and e.get(key) is not None}

    def facts(self):
        return {f.get("id"): f for f in L(self.get("01-sources.yaml")) if f.get("id") is not None}

    def fact_problem(self, fid, facts, need_unsuperseded=False):
        f = facts.get(fid)
        if f is None:
            return "素材台帳にない"
        if f.get("verified") is not True:
            return "verified: true でない"
        if f.get("kind") not in USABLE_KINDS:
            return f"kind が {f.get('kind')} で、根拠に使えない"
        if need_unsuperseded and not blank(f.get("superseded_by")):
            return "superseded_by に値がある"
        return None

    def plan_tree(self):
        plan = L(self.get("01-plan.yaml"))
        by_id = {q.get("id"): q for q in plan}
        children = {}
        for q in plan:
            children.setdefault(q.get("parent"), []).append(q.get("id"))
        leaves = [q for q in plan if q.get("id") not in children]
        return by_id, children, leaves

    def depth(self, qid, by_id):
        d, seen = 0, set()
        while qid in by_id and by_id[qid].get("parent") is not None and qid not in seen:
            seen.add(qid)
            qid = by_id[qid].get("parent")
            d += 1
        return d

    def dup_ids(self, name, key="id", sub=None):
        d = self.get(name)
        if sub:
            d = D(d).get(sub)
        seen, out = set(), []
        for i, e in enumerate(L(d)):
            v = e.get(key) if isinstance(e, dict) else None
            if v is None:
                out.append(f"{name}: {i + 1}件目に {key} がない")
            elif v in seen:
                out.append(f"{name}: {v} が重複している")
            seen.add(v)
        return out

    # ---- 工程0 ----
    def parse_brief(self):
        items, dups, cur = {}, [], None
        for n, line in enumerate(self.get("00-brief.md").splitlines(), 1):
            m = re.match(r"^##\s+(.+?)\s*$", line)
            if m:
                name = m.group(1)
                if name in items:
                    dups.append(f"00-brief.md:{n}: 「{name}」が2回ある")
                cur = items[name] = {"line": n, "attrs": {}, "body": []}
                continue
            if cur is None:
                continue
            m = re.match(r"^\s*[-*]\s*([^::]+?)\s*[::]\s*(.*?)\s*$", line)
            if m:
                cur["attrs"].setdefault(m.group(1), []).append(m.group(2))
            elif line.strip():
                cur["body"].append(line.strip())
        return items, dups

    def stage0(self):
        B = "00-brief.md"

        def state(item):
            return (item["attrs"].get("状態") or [None])[0]

        def items_present():
            items, dups = self.parse_brief()
            out = [f"{B}: 「{n}」の項目がない" for n in BRIEF_ITEMS if n not in items] + dups
            for n in BRIEF_ITEMS:
                if n in items and state(items[n]) not in BRIEF_STATES:
                    out.append(f"{B}:{items[n]['line']}: 「{n}」に状態(確定、推定、未定)がない")
            return out

        def no_estimated():
            items, _ = self.parse_brief()
            return [f"{B}:{i['line']}: 「{n}」が推定のまま" for n, i in items.items() if state(i) == "推定"]

        def must_fixed():
            items, _ = self.parse_brief()
            return [f"{B}: 「{n}」が確定でない" for n in BRIEF_MUST_BE_FIXED
                    if n not in items or state(items[n]) != "確定"]

        def undecided_owner():
            items, _ = self.parse_brief()
            return [f"{B}:{i['line']}: 「{n}」が未定だが、「決める人と時期」がない"
                    for n, i in items.items()
                    if state(i) == "未定" and blank((i["attrs"].get("決める人と時期") or [""])[0])]

        def secrets():
            items, _ = self.parse_brief()
            it = items.get("外に出せない情報")
            if it is None:
                return [f"{B}: 「外に出せない情報」の項目がない"]
            if state(it) == "確定":
                return []
            has_image = any(f.get("kind") == "image" for f in L(self.get("01-sources.yaml")))
            if has_image:
                return [f"{B}:{it['line']}: 画像の素材があるのに、「外に出せない情報」が確定でない"]
            return (WARN, [f"{B}:{it['line']}: 「外に出せない情報」が確定でない(画像の素材はない)"])

        self.rule(0, "ブリーフに全ての項目があり、各項目に状態がある", [B], items_present)
        self.rule(0, "全ての項目が、確定または未定である。推定のまま残る項目がない", [B], no_estimated)
        self.rule(0, "主な読み手、目的、答えるべき問いが確定である", [B], must_fixed)
        self.rule(0, "未定の項目に、誰がいつ決めるかが添えてある", [B], undecided_owner)
        self.rule(0, "「外に出せない情報」が確定である。画像を使う資料では、未定を認めない", [B], secrets)
        self.rule(0, "資料の表現規約 style.yaml がある", ["style.yaml"], lambda: [])

    # ---- 工程1 ----
    def stage1(self):
        H, P, S, M = "01-hypotheses.yaml", "01-plan.yaml", "01-sources.yaml", "01-model.yaml"

        self.rule(1, "仮説、問い、事実のIDが、それぞれ重複していない", [],
                  lambda: sum((self.dup_ids(n) for n in (H, P, S) if n in self.data), []))

        def hyp_fields():
            out = []
            for h in self.get(H):
                if blank(h.get("statement")):
                    out.append(f"{H} {h.get('id')}: statement がない")
                if h.get("proposed_by") not in ("user", "session"):
                    out.append(f"{H} {h.get('id')}: proposed_by が user でも session でもない")
            return out

        self.rule(1, "仮説に statement と proposed_by がある", [H], hyp_fields)
        self.rule(1, "仮説の一覧に、対立する仮説が1つ以上ある", [H],
                  lambda: [] if len(self.get(H)) >= 2 else [f"{H}: 仮説が{len(self.get(H))}件しかない"])

        def plan_refs():
            by_id, _, _ = self.plan_tree()
            return [f"{P} {q.get('id')}: parent の {q.get('parent')} が探索の計画にない"
                    for q in self.get(P) if q.get("parent") is not None and q.get("parent") not in by_id] + \
                   [f"{P} {q.get('id')}: question がない" for q in self.get(P) if blank(q.get("question"))]

        def plan_axis():
            by_id, children, leaves = self.plan_tree()
            out = [f"{P} {qid}: 子の問いがあるのに axis がない"
                   for qid in children if qid in by_id and blank(by_id[qid].get("axis"))]
            for q in leaves:
                if blank(q.get("evidence_type")):
                    out.append(f"{P} {q.get('id')}: 末端の問いに evidence_type がない")
                if q.get("priority") not in ("high", "low"):
                    out.append(f"{P} {q.get('id')}: 末端の問いの priority が high でも low でもない")
            return out

        def plan_result():
            _, _, leaves = self.plan_tree()
            return [f"{P} {q.get('id')}: result が {q.get('result')}(answered / partial / not-found / disputed のいずれでもない)"
                    for q in leaves if q.get("result") not in RESULTS]

        self.rule(1, "問いに question があり、parent が探索の計画にある", [P], plan_refs)
        self.rule(1, "全ての枝分かれに axis がある。全ての末端の問いに evidence_type と priority がある", [P], plan_axis)
        self.rule(1, "探索の計画の全ての末端の問いに result がある", [P], plan_result)

        def src_fields():
            out = []
            for f in self.get(S):
                if blank(f.get("statement")):
                    out.append(f"{S} {f.get('id')}: statement がない")
                if f.get("kind") not in FACT_KINDS:
                    out.append(f"{S} {f.get('id')}: kind が {f.get('kind')}(定めた種類でない)")
                if f.get("kind") in USABLE_KINDS and not isinstance(f.get("verified"), bool):
                    out.append(f"{S} {f.get('id')}: verified が true でも false でもない")
            return out

        def src_fact():
            return [f"{S} {f.get('id')}: {k} がない" for f in self.get(S) if f.get("kind") == "fact"
                    for k in ("source", "locator", "quote") if blank(f.get(k))]

        def src_derived():
            return [f"{S} {f.get('id')}: formula がない" for f in self.get(S)
                    if f.get("kind") == "derived" and blank(f.get("formula"))]

        def src_metric():
            return [f"{S} {f.get('id')}: value があるのに metric がない" for f in self.get(S)
                    if f.get("kind") != "image" and f.get("value") is not None and blank(f.get("metric"))]

        def src_metric_terms():
            terms = L(self.get("terms.yaml").get("terms"))
            known = {t.get("id") for t in terms if isinstance(t, dict)} | \
                    {t.get("term") for t in terms if isinstance(t, dict)}
            return [f"{S} {f.get('id')}: metric の {f.get('metric')} が語彙表にない"
                    for f in self.get(S) if not blank(f.get("metric")) and f.get("metric") not in known]

        def src_conflict():
            groups = {}
            for f in self.get(S):
                if f.get("value") is None or blank(f.get("metric")) or not blank(f.get("superseded_by")):
                    continue
                key = (f.get("metric"), str(f.get("as_of")), tuple(sorted(map(str, L(f.get("qualifiers"))))))
                groups.setdefault(key, []).append(f)
            out = []
            for (metric, _, _), fs in groups.items():
                if len({(str(f.get("value")), str(f.get("unit"))) for f in fs}) > 1:
                    out.append(f"{S} {'、'.join(str(f.get('id')) for f in fs)}: "
                               f"metric {metric} が同じで、時点と限定も同じなのに、値が違う")
            return (WARN, out, "使わない事実に superseded_by を書くか、問いの結果を disputed とする") if out else []

        def src_testimony():
            return [f"{S} {f.get('id')}: testimony に source(誰の、何に基づく証言か)がない"
                    for f in self.get(S) if f.get("kind") == "testimony" and blank(f.get("source"))]

        def src_image():
            out = []
            for f in self.get(S):
                if f.get("kind") != "image":
                    continue
                if blank(f.get("source")):
                    out.append(f"{S} {f.get('id')}: 画像の素材に source がない")
                if blank(f.get("version")) and blank(f.get("captured_at")):
                    out.append(f"{S} {f.get('id')}: 画像の素材に version も captured_at もない")
                if blank(f.get("file")):
                    out.append(f"{S} {f.get('id')}: 画像の素材に file がない")
                elif not (self.root / str(f.get("file"))).is_file():
                    out.append(f"{S} {f.get('id')}: file の {f.get('file')} がない")
            return out

        def src_refs():
            by_id, _, _ = self.plan_tree()
            facts = self.facts()
            out = []
            for f in self.get(S):
                out += [f"{S} {f.get('id')}: answers の {q} が探索の計画にない"
                        for q in L(f.get("answers")) if q not in by_id]
                if not blank(f.get("superseded_by")) and f.get("superseded_by") not in facts:
                    out.append(f"{S} {f.get('id')}: superseded_by の {f.get('superseded_by')} が素材台帳にない")
            return out

        def src_stance():
            hyps = self.ids(H)
            out = []
            for f in self.get(S):
                if f.get("kind") == "image":
                    continue
                st = D(f.get("stance"))
                out += [f"{S} {f.get('id')}: 仮説 {h} への stance がない" for h in sorted(hyps - set(st))]
                out += [f"{S} {f.get('id')}: stance の {h} が仮説の一覧にない" for h in st if h not in hyps]
                out += [f"{S} {f.get('id')}: stance の値が {v}(supports / contradicts / neutral のいずれでもない)"
                        for v in st.values() if v not in STANCES]
            return out

        def termination():
            _, _, leaves = self.plan_tree()
            rest = [f"{P} {q.get('id')}: priority が high で、result が {q.get('result')}"
                    for q in leaves if q.get("priority") == "high" and q.get("result") not in ("answered", "disputed")]
            if rest:
                return (WARN, rest, "1つ目の条件を満たさない。2つ目と3つ目の条件(追加の収集で新しい事実が出ない、"
                                    "ユーザーの上限)は、記録の置き場が未定義で判定できない")
            return []

        self.rule(1, "事実に statement、定めた種類の kind、verified がある", [S], src_fields)
        self.rule(1, "全ての fact に source、locator、quote がある", [S], src_fact)
        self.rule(1, "全ての derived に formula がある(再計算は未実装)", [S], src_derived)
        self.rule(1, "数値を持つ全ての事実に metric がある", [S], src_metric)
        self.rule(1, "metric が語彙表の語である", [S, "terms.yaml"], src_metric_terms)
        self.rule(1, "同じ metric で、時点と範囲が同じなのに値が違う事実を挙げる", [S], src_conflict)
        self.rule(1, "全ての testimony に、誰の、何に基づく証言かの記録がある", [S], src_testimony)
        self.rule(1, "画像の素材に source、version または captured_at があり、file が実在する", [S], src_image)
        self.rule(1, "事実の answers と superseded_by の参照先がある", [S, P], src_refs)
        self.rule(1, "画像の素材を除く全ての事実に、全ての仮説に対する stance がある", [S, H], src_stance)
        self.rule(1, "終了の判断の条件のいずれかを満たす", [P], termination)

        if M in self.data or M in self.broken:
            def model_ids():
                m = self.get(M)
                out = []
                for sub in ("elements", "relations", "scenarios"):
                    out += self.dup_ids(M, sub=sub)
                els = self.ids(M, sub="elements")
                rels = self.ids(M, sub="relations")
                for r in L(m.get("relations")):
                    out += [f"{M} {r.get('id')}: {k} の {r.get(k)} が要素にない"
                            for k in ("from", "to") if r.get(k) not in els]
                    out += [f"{M} {r.get('id')}: summarizes の {x} がつながりにない"
                            for x in L(r.get("summarizes")) if x not in rels]
                for s in L(m.get("scenarios")):
                    out += [f"{M} {s.get('id')}: steps の {x} がつながりにない"
                            for x in L(s.get("steps")) if x not in rels]
                return out

            def model_evidence():
                facts = self.facts()
                out = []
                for sub in ("elements", "relations", "scenarios"):
                    for e in L(self.get(M).get(sub)):
                        ev = L(e.get("evidence"))
                        if not ev:
                            out.append(f"{M} {e.get('id')}: evidence がない")
                        for fid in ev:
                            p = self.fact_problem(fid, facts)
                            if p:
                                out.append(f"{M} {e.get('id')}: evidence の {fid} が{p}")
                return out

            def model_summarizes():
                rels = {r.get("id"): r for r in L(self.get(M).get("relations"))}
                out = []
                for r in rels.values():
                    chain = [rels[x] for x in L(r.get("summarizes")) if x in rels]
                    if not chain or len(chain) != len(L(r.get("summarizes"))):
                        continue
                    ok = chain[0].get("from") == r.get("from") and chain[-1].get("to") == r.get("to") and \
                        all(a.get("to") == b.get("from") for a, b in zip(chain, chain[1:]))
                    if not ok:
                        out.append(f"{M} {r.get('id')}: summarizes が、from から to まで順につながっていない")
                return out

            def region_refs():
                els = self.ids(M, sub="elements")
                return [f"{S} {f.get('id')}: regions の element の {r.get('element')} が仕組みの定義にない"
                        for f in L(self.get(S)) if f.get("kind") == "image"
                        for r in L(f.get("regions")) if isinstance(r, dict)
                        and not blank(r.get("element")) and r.get("element") not in els]

            self.rule(1, "仕組みの定義のIDが重複せず、つながりと場面の参照先がある", [M], model_ids)
            self.rule(1, "全ての要素、つながり、場面に、verified: true の事実が紐づく", [M, S], model_evidence)
            self.rule(1, "summarizes のあるつながりが、元のつながりを順にたどったものになっている", [M], model_summarizes)
            self.rule(1, "画像の素材の regions の element が仕組みの定義にある", [M, S], region_refs)

    # ---- 工程2 ----
    def stage2(self):
        A, C, P, S, H = "02-answers.yaml", "02-claims.yaml", "01-plan.yaml", "01-sources.yaml", "01-hypotheses.yaml"

        def unknown_answer(a):
            return str(a.get("answer") or "").strip().rstrip("。") == "分からない"

        def ans_all():
            answered = {a.get("question") for a in self.get(A) if not blank(a.get("answer"))}
            by_id, _, _ = self.plan_tree()
            seen, dup = set(), []
            for a in self.get(A):
                if a.get("question") in seen:
                    dup.append(f"{A} {a.get('question')}: 答えが2つある")
                seen.add(a.get("question"))
            return [f"{A}: {q} の答えがない" for q in by_id if q not in answered] + dup + \
                   [f"{A} {a.get('question')}: question が探索の計画にない"
                    for a in self.get(A) if a.get("question") not in by_id] + \
                   [f"{A} {a.get('question')}: from の {q} が探索の計画にない"
                    for a in self.get(A) for q in L(a.get("from")) if q not in by_id]

        def ans_evidence():
            _, _, leaves = self.plan_tree()
            leaf_ids = {q.get("id") for q in leaves}
            facts = self.facts()
            out = []
            for a in self.get(A):
                for fid in L(a.get("evidence")):
                    if fid not in facts:
                        out.append(f"{A} {a.get('question')}: evidence の {fid} が素材台帳にない")
                if a.get("question") in leaf_ids and not unknown_answer(a):
                    if not any(self.fact_problem(fid, facts) is None for fid in L(a.get("evidence"))):
                        out.append(f"{A} {a.get('question')}: 末端の問いの答えに、verified: true の事実が紐づいていない")
            return out

        self.rule(2, "探索の計画の全ての問いに答えがある。question と from の参照先がある", [A, P], ans_all)
        self.rule(2, "末端の問いの答えに、verified: true の事実が紐づく(答えが「分からない」の場合を除く)",
                  [A, P, S], ans_evidence)

        claims = lambda: L(self.get(C).get("claims"))

        def claim_fields():
            c = self.get(C)
            out = [f"{C}: {k} がない" for k in ("answer", "summary", "axis", "claims") if blank(c.get(k))]
            if "hypothesis" not in c:
                out.append(f"{C}: hypothesis がない(どの仮説とも違う場合は null と書く)")
            out += self.dup_ids(C, sub="claims")
            for cl in claims():
                out += [f"{C} {cl.get('id')}: {k} がない" for k in ("statement", "question") if blank(cl.get(k))]
                for i, o in enumerate(L(cl.get("objections"))):
                    out += [f"{C} {cl.get('id')} objections[{i}]: {k} がない"
                            for k in ("objection", "response") if blank(D(o).get(k))]
            for i, x in enumerate(L(c.get("contradictions"))):
                if D(x).get("handling") not in ("rebut", "qualify", "change"):
                    out.append(f"{C} contradictions[{i}]: handling が rebut / qualify / change のいずれでもない")
            return out

        def claim_refs():
            c = self.get(C)
            out = []
            if c.get("hypothesis") is not None and H in self.data and c.get("hypothesis") not in self.ids(H):
                out.append(f"{C}: hypothesis の {c.get('hypothesis')} が仮説の一覧にない")
            by_id, _, _ = self.plan_tree()
            facts = self.facts()
            for cl in claims():
                if P in self.data and not blank(cl.get("question")) and cl.get("question") not in by_id:
                    out.append(f"{C} {cl.get('id')}: question の {cl.get('question')} が探索の計画にない")
                if S in self.data:
                    ev = L(cl.get("evidence")) + [f for o in L(cl.get("objections")) for f in L(D(o).get("evidence"))]
                    out += [f"{C} {cl.get('id')}: evidence の {f} が素材台帳にない" for f in ev if f not in facts]
            if S in self.data:
                out += [f"{C} contradictions[{i}]: fact の {D(x).get('fact')} が素材台帳にない"
                        for i, x in enumerate(L(c.get("contradictions"))) if D(x).get("fact") not in facts]
            return out

        def claim_level():
            by_id, _, _ = self.plan_tree()
            depths = {cl.get("id"): self.depth(cl.get("question"), by_id)
                      for cl in claims() if cl.get("question") in by_id}
            if len(set(depths.values())) > 1:
                return [f"{C}: 主張ごとの問いの階層が揃っていない({'、'.join(f'{k}は{v}階層目' for k, v in depths.items())})"]
            return []

        def claim_count():
            limit = D(self.get("style.yaml").get("limits")).get("max_claims")
            if not isinstance(limit, int):
                return (UNKNOWN, [], "style.yaml に limits.max_claims がない")
            n = len(claims())
            return [f"{C}: 主張が{n}件で、上限の{limit}件を超える"] if n > limit else []

        def claim_verified():
            facts = self.facts()
            return [f"{C} {cl.get('id')}: verified: true の事実が1件も紐づいていない" for cl in claims()
                    if not any(self.fact_problem(f, facts) is None for f in L(cl.get("evidence")))]

        def usable(cl, facts):
            return [facts[f] for f in L(cl.get("evidence")) if self.fact_problem(f, facts) is None]

        def claim_origin():
            facts = self.facts()
            out = []
            for cl in claims():
                fs = usable(cl, facts)
                origins = {f.get("origin") or f.get("source") for f in fs}
                if fs and len(origins) == 1:
                    out.append(f"{C} {cl.get('id')}: 根拠の origin が1つだけ({next(iter(origins))})")
            return (WARN, out, "そのことを主張に明記しているかは、人が確かめる") if out else []

        def claim_testimony():
            facts = self.facts()
            out = [f"{C} {cl.get('id')}: 根拠が testimony だけ" for cl in claims()
                   if usable(cl, facts) and all(f.get("kind") == "testimony" for f in usable(cl, facts))]
            return (WARN, out, "承認の際にユーザーに示す") if out else []

        def contradictions():
            c = self.get(C)
            if c.get("hypothesis") is None:
                return []
            listed = {D(x).get("fact") for x in L(c.get("contradictions"))}
            return [f"{C}: {f.get('id')} は {c.get('hypothesis')} を否定するが、contradictions にない"
                    for f in self.get(S)
                    if D(f.get("stance")).get(c.get("hypothesis")) == "contradicts" and f.get("id") not in listed]

        self.rule(2, "主張の骨子に必須の項目があり、主張のIDが重複していない", [C], claim_fields)
        self.rule(2, "主張の骨子の hypothesis、question、evidence、contradictions の参照先がある", [C], claim_refs)
        self.rule(2, "全ての主張が、問いの木の同じ階層の問いに対応する", [C, P], claim_level)
        self.rule(2, "主張の数が、資料の表現規約が定める上限以下である", [C, "style.yaml"], claim_count)
        self.rule(2, "全ての主張に、verified: true の事実が1件以上紐づく", [C, S], claim_verified)
        self.rule(2, "1つの origin だけに頼る主張がない", [C, S], claim_origin)
        self.rule(2, "testimony だけに頼る主張を挙げる", [C, S], claim_testimony)
        self.rule(2, "採った仮説を否定する事実の全てが、contradictions にある", [C, S], contradictions)

    # ---- 工程3 ----
    def stage3(self):
        CH, C, B, P, S = "03-chapters.yaml", "02-claims.yaml", "00-brief.md", "01-plan.yaml", "01-sources.yaml"
        chapters = lambda: L(self.get(CH).get("chapters"))

        def fields():
            d = self.get(CH)
            out = self.dup_ids(CH, sub="chapters")
            order = D(d.get("order"))
            if order.get("conclusion") not in ("first", "last"):
                out.append(f"{CH}: order.conclusion が first でも last でもない")
            if order.get("basis") not in ("time", "structure", "importance"):
                out.append(f"{CH}: order.basis が time / structure / importance のいずれでもない")
            if not chapters():
                out.append(f"{CH}: chapters がない")
            for ch in chapters():
                if ch.get("kind") not in ("intro", "body", "closing"):
                    out.append(f"{CH} {ch.get('id')}: kind が intro / body / closing のいずれでもない")
                out += [f"{CH} {ch.get('id')}: {k} がない" for k in ("title", "message") if blank(ch.get(k))]
                if not isinstance(ch.get("slides"), int) or isinstance(ch.get("slides"), bool):
                    out.append(f"{CH} {ch.get('id')}: slides が整数でない")
            return out

        def refs():
            d = self.get(CH)
            ch_ids = self.ids(CH, sub="chapters")
            out = []
            if C in self.data:
                cl = {c.get("id"): c for c in L(self.get(C).get("claims"))}
                out += [f"{CH} {ch.get('id')}: claims の {x} が主張の骨子にない"
                        for ch in chapters() for x in L(ch.get("claims")) if x not in cl]
                for i, o in enumerate(L(d.get("objections"))):
                    o = D(o)
                    n = len(L(D(cl.get(o.get("claim"))).get("objections")))
                    if o.get("claim") not in cl:
                        out.append(f"{CH} objections[{i}]: claim の {o.get('claim')} が主張の骨子にない")
                    elif not isinstance(o.get("index"), int) or not 0 <= o.get("index") < n:
                        out.append(f"{CH} objections[{i}]: {o.get('claim')} に index {o.get('index')} の反論がない")
                    if o.get("to") not in ("body", "appendix"):
                        out.append(f"{CH} objections[{i}]: to が body でも appendix でもない")
            for i, x in enumerate(L(d.get("contradictions"))):
                x = D(x)
                if x.get("chapter") not in ch_ids:
                    out.append(f"{CH} contradictions[{i}]: chapter の {x.get('chapter')} が章構成にない")
                if S in self.data and x.get("fact") not in self.facts():
                    out.append(f"{CH} contradictions[{i}]: fact の {x.get('fact')} が素材台帳にない")
            if P in self.data:
                by_id, _, _ = self.plan_tree()
                out += [f"{CH} omitted[{i}]: question の {D(x).get('question')} が探索の計画にない"
                        for i, x in enumerate(L(d.get("omitted"))) if D(x).get("question") not in by_id]
            return out

        def all_claims_assigned():
            assigned = {x for ch in chapters() if ch.get("kind") == "body" for x in L(ch.get("claims"))}
            return [f"{CH}: 主張 {c.get('id')} が、どの本論の章にも割り当てられていない"
                    for c in L(self.get(C).get("claims")) if c.get("id") not in assigned]

        def claims_by_kind():
            out = []
            for ch in chapters():
                if ch.get("kind") == "body" and blank(ch.get("claims")):
                    out.append(f"{CH} {ch.get('id')}: 本論の章に claims がない")
                if ch.get("kind") in ("intro", "closing") and not blank(ch.get("claims")):
                    out.append(f"{CH} {ch.get('id')}: 導入または結びの章に claims がある")
            return out

        def omitted():
            out = []
            for i, x in enumerate(L(self.get(CH).get("omitted"))):
                x = D(x)
                if x.get("to") not in ("appendix", "drop"):
                    out.append(f"{CH} omitted[{i}]: to が appendix でも drop でもない")
                if blank(x.get("reason")):
                    out.append(f"{CH} omitted[{i}]: reason がない")
            return out

        def contradictions():
            placed = {D(x).get("fact") for x in L(self.get(CH).get("contradictions"))
                      if not blank(D(x).get("chapter"))}
            return [f"{CH}: {D(x).get('fact')}(扱いは {D(x).get('handling')})に触れる章が、contradictions にない"
                    for x in L(self.get(C).get("contradictions"))
                    if D(x).get("handling") in ("rebut", "qualify") and D(x).get("fact") not in placed]

        def objections():
            placed = {(D(o).get("claim"), D(o).get("index")) for o in L(self.get(CH).get("objections"))}
            return [f"{CH}: {c.get('id')} の反論 index {i} が objections にない"
                    for c in L(self.get(C).get("claims"))
                    for i in range(len(L(c.get("objections")))) if (c.get("id"), i) not in placed]

        def total():
            items, _ = self.parse_brief()
            raw = (D(items.get("制約")).get("attrs", {}).get("枚数の上限") or [""])[0]
            m = re.search(r"\d+", raw)
            if not m:
                return (UNKNOWN, [], "ブリーフの「制約」に「- 枚数の上限: 数」がない")
            n = sum(ch.get("slides") for ch in chapters() if isinstance(ch.get("slides"), int))
            return [f"{CH}: 枚数の合計が{n}枚で、ブリーフの上限の{m.group()}枚を超える"] if n > int(m.group()) else []

        self.rule(3, "章構成に必須の項目があり、章のIDが重複していない", [CH], fields)
        self.rule(3, "章構成の claims、contradictions、objections、omitted の参照先がある", [CH], refs)
        self.rule(3, "全ての主張が、いずれかの本論の章に割り当てられている", [CH, C], all_claims_assigned)
        self.rule(3, "本論の章の全てに claims がある。導入と結びの章には claims がない", [CH], claims_by_kind)
        self.rule(3, "omitted の全てに、行き先と理由がある", [CH], omitted)
        self.rule(3, "主張の骨子の contradictions のうち、扱いが反駁または条件付きのものの全てに、触れる章が決まっている",
                  [CH, C], contradictions)
        self.rule(3, "主張の骨子の全ての反論が、objections にある", [CH, C], objections)
        self.rule(3, "枚数の合計がブリーフの制約に収まる", [CH, B], total)
        self.rule(3, "全ての章に slides_reason がある", [CH],
                  lambda: [f"{CH} {ch.get('id')}: slides_reason がない" for ch in chapters()
                           if blank(ch.get("slides_reason"))])

    # ---- 工程4 ----
    def stage4(self):
        ST, CH, A, S, C, B = ("04-storyline.yaml", "03-chapters.yaml", "02-answers.yaml",
                              "01-sources.yaml", "02-claims.yaml", "00-brief.md")
        CS, SC = "04-chapter-states.yaml", "04-scenarios.yaml"
        slides = lambda: self.get(ST)
        chapters = lambda: L(self.get(CH).get("chapters"))
        is_ap = lambda s: s.get("chapter") == "appendix"

        def one_each():
            return [f"{ST} {s.get('id')}: {k} が、空でない1つの文でない" for s in slides()
                    for k in ("question", "headline") if not isinstance(s.get(k), str) or not s.get(k).strip()]

        def refs():
            ch_ids = self.ids(CH, sub="chapters") | {"appendix"}
            out = []
            for s in slides():
                if CH in self.data and s.get("chapter") not in ch_ids:
                    out.append(f"{ST} {s.get('id')}: chapter の {s.get('chapter')} が章構成にない")
                if A in self.data:
                    qs = self.ids(A, key="question")
                    out += [f"{ST} {s.get('id')}: from の {q} が問いごとの答えにない"
                            for q in L(s.get("from")) if q not in qs]
                if S in self.data:
                    facts = self.facts()
                    ev = L(s.get("evidence")) + ([s.get("contradiction")] if s.get("contradiction") is not None else [])
                    out += [f"{ST} {s.get('id')}: {f} が素材台帳にない" for f in ev if f not in facts]
                if C in self.data and s.get("objection") is not None:
                    o = D(s.get("objection"))
                    cl = {c.get("id"): c for c in L(self.get(C).get("claims"))}
                    n = len(L(D(cl.get(o.get("claim"))).get("objections")))
                    if o.get("claim") not in cl or not isinstance(o.get("index"), int) or not 0 <= o.get("index") < n:
                        out.append(f"{ST} {s.get('id')}: objection の {o.get('claim')} index {o.get('index')} が主張の骨子にない")
            return out

        def body_from_evidence():
            body = {ch.get("id") for ch in chapters() if ch.get("kind") == "body"}
            return [f"{ST} {s.get('id')}: 本論の章のスライドに {k} がない" for s in slides()
                    if s.get("chapter") in body for k in ("from", "evidence") if blank(s.get(k))]

        def counts():
            out = []
            for ch in chapters():
                n = sum(1 for s in slides() if s.get("chapter") == ch.get("id"))
                if isinstance(ch.get("slides"), int) and n + 2 > ch.get("slides"):
                    out.append(f"{ST} {ch.get('id')}: {n}枚に章扉と章のまとめの2枚を足すと{n + 2}枚で、"
                               f"配分の{ch.get('slides')}枚を超える")
            return out

        def appendix_of():
            main = {s.get("id") for s in slides() if not is_ap(s)}
            out = []
            for s in slides():
                if is_ap(s) and blank(s.get("appendix_of")):
                    out.append(f"{ST} {s.get('id')}: 付録のスライドに appendix_of がない")
                elif not blank(s.get("appendix_of")) and s.get("appendix_of") not in main:
                    out.append(f"{ST} {s.get('id')}: appendix_of の {s.get('appendix_of')} が本編のスライドにない")
            return out

        def omitted_and_objections():
            d = self.get(CH)
            out = []
            for x in L(d.get("omitted")):
                q = D(x).get("question")
                if D(x).get("to") == "appendix" and not any(is_ap(s) and q in L(s.get("from")) for s in slides()):
                    out.append(f"{ST}: 付録に回した {q} を from で参照する付録のスライドがない")
            for o in L(d.get("objections")):
                o = D(o)
                hit = [s for s in slides() if D(s.get("objection")).get("claim") == o.get("claim")
                       and D(s.get("objection")).get("index") == o.get("index")]
                where = f"{o.get('claim')} の反論 index {o.get('index')}"
                if not hit:
                    out.append(f"{ST}: {where} を objection で参照するスライドがない")
                elif not any(is_ap(s) == (o.get("to") == "appendix") for s in hit):
                    out.append(f"{ST} {hit[0].get('id')}: {where} の置き場が、章構成の {o.get('to')} と違う")
            return out

        def contradictions():
            out = []
            for x in L(self.get(CH).get("contradictions")):
                x = D(x)
                hit = [s for s in slides() if s.get("contradiction") == x.get("fact")]
                if not hit:
                    out.append(f"{ST}: {x.get('fact')} を contradiction で参照するスライドがない")
                    continue
                hit_ch = [s for s in hit if s.get("chapter") == x.get("chapter")]
                if not hit_ch:
                    out.append(f"{ST} {hit[0].get('id')}: {x.get('fact')} に触れるスライドが、章構成が決めた {x.get('chapter')} にない")
                out += [f"{ST} {s.get('id')}: evidence に {x.get('fact')} がない"
                        for s in (hit_ch or hit) if x.get("fact") not in L(s.get("evidence"))]
            return out

        self.rule(4, "スライドのIDが重複していない", [ST], lambda: self.dup_ids(ST))
        self.rule(4, "1スライドに、問いと見出しが1つずつある", [ST], one_each)
        self.rule(4, "スライドの chapter、from、evidence、contradiction、objection の参照先がある", [ST], refs)
        self.rule(4, "本論の章の全てのスライドに、from と evidence がある", [ST, CH], body_from_evidence)
        self.rule(4, "章ごとの枚数が、導出と半導出のスライドを合算して、章構成の配分以下である", [ST, CH], counts)
        self.rule(4, "付録の全てのスライドに appendix_of があり、本編のスライドを指す", [ST], appendix_of)
        self.rule(4, "付録に回した答えと、章構成の objections の全てに、参照するスライドが決めた置き場にある",
                  [ST, CH], omitted_and_objections)
        self.rule(4, "章構成の contradictions の全てに、参照するスライドが決めた章にあり、evidence がその事実を含む",
                  [ST, CH], contradictions)

        def states_in_order():
            by_ch = {s.get("chapter"): s for s in self.get(CS)}
            return [(ch.get("id"), by_ch.get(ch.get("id"))) for ch in chapters()]

        def states_fields():
            ch_ids = self.ids(CH, sub="chapters")
            out = [f"{CS}: {cid} の前提と到達点がない" for cid, st in states_in_order() if st is None]
            out += [f"{CS} {s.get('chapter')}: chapter が章構成にない" for s in self.get(CS)
                    if s.get("chapter") not in ch_ids]
            out += [f"{CS} {s.get('chapter')}: {k} がない" for s in self.get(CS)
                    for k in ("entry", "exit") if not isinstance(s.get(k), dict)]
            if C in self.data:
                cl = self.ids(C, sub="claims")
                out += [f"{CS} {s.get('chapter')}: {k}.accepted の {x} が主張の骨子にない" for s in self.get(CS)
                        for k in ("entry", "exit") for x in L(D(s.get(k)).get("accepted")) if x not in cl]
            return out

        def states_chain():
            out = []
            have = {"terms": set(), "accepted": set(), "open_questions": set()}
            for cid, st in states_in_order():
                if st is None:
                    continue
                for k in have:
                    out += [f"{CS} {cid}: entry.{k} の「{x}」が、前の章の exit にない"
                            for x in L(D(st.get("entry")).get(k)) if x not in have[k]]
                    have[k] |= set(L(D(st.get("exit")).get(k)))
            return out

        def last_open():
            last = [st for _, st in states_in_order() if st is not None][-1:]
            return [f"{CS} {st.get('chapter')}: 最後の章の exit.open_questions に「{x}」が残る"
                    for st in last for x in L(D(st.get("exit")).get("open_questions"))]

        def concerns():
            items, _ = self.parse_brief()
            wanted = D(items.get("読み手の立場と懸念")).get("attrs", {}).get("懸念") or []
            if not wanted:
                return (UNKNOWN, [], "ブリーフの「読み手の立場と懸念」に「- 懸念: 文」がない")
            got = {x for s in self.get(CS) for x in L(D(s.get("exit")).get("concerns_answered"))}
            out = [f"{CS}: 懸念「{x}」が、どの章の exit.concerns_answered にもない" for x in wanted if x not in got]
            return (WARN, out, "答えないと決めた記録の置き場が未定義のため、不合格にしない。文字列の完全一致で照合する") if out else []

        def scenarios():
            by = {s.get("scenario"): s for s in self.get(SC)}
            out = [f"{SC}: 場面「{n}」がない" for n in SCENARIOS if n not in by]
            for n, s in by.items():
                if n not in SCENARIOS:
                    out.append(f"{SC}: 場面「{n}」は工程8が定める場面でない")
                elif s.get("applicable") is False:
                    if blank(s.get("reason")):
                        out.append(f"{SC} {n}: 該当しないとしたが reason がない")
                elif blank(s.get("expected")):
                    out.append(f"{SC} {n}: expected がない")
            return out

        self.rule(4, "全ての章に前提と到達点(entry と exit)がある", [CS, CH], states_fields)
        self.rule(4, "全ての章の入口の状態が、それより前の章の出口の状態で満たされている", [CS, CH], states_chain)
        self.rule(4, "最後の章の出口で、残る疑問がない", [CS, CH], last_open)
        self.rule(4, "ブリーフの読み手の懸念の全てが、いずれかの章の到達点にある", [CS, B], concerns)
        self.rule(4, "工程8が定める全ての場面に、期待する結果が書かれている。該当しない場面は、該当しないと記録する",
                  [SC], scenarios)

    # ---- 工程5 ----
    def stage5(self):
        PR, ST, S, M = "05-proof.yaml", "04-storyline.yaml", "01-sources.yaml", "01-model.yaml"
        proofs = lambda: self.get(PR)

        def cover():
            a, b = self.ids(PR), self.ids(ST)
            return self.dup_ids(PR) + \
                [f"{PR}: スライド {x} の立証の設計がない" for x in sorted(b - a, key=str)] + \
                [f"{PR} {x}: ストーリーラインにないスライドである" for x in sorted(a - b, key=str)]

        def facts_ok():
            facts = self.facts()
            out = []
            for p in proofs():
                for f in L(p.get("facts")):
                    prob = self.fact_problem(f, facts, need_unsuperseded=True)
                    if prob:
                        out.append(f"{PR} {p.get('id')}: facts の {f} が{prob}")
            return out

        def facts_cover():
            pr = {p.get("id"): p for p in proofs()}
            return [f"{PR} {s.get('id')}: facts が、ストーリーラインの evidence の {f} を含まない"
                    for s in self.get(ST) if s.get("id") in pr
                    for f in L(s.get("evidence")) if f not in L(pr[s.get("id")].get("facts"))]

        def model_parts():
            m = D(self.get(M))
            return (self.ids(M, sub="elements"), {r.get("id"): r for r in L(m.get("relations"))},
                    {s.get("id"): s for s in L(m.get("scenarios"))})

        def view_elements(p):
            _, rels, scs = model_parts()
            v = D(p.get("view"))
            els = set(L(v.get("elements")))
            rids = list(L(v.get("relations"))) + list(L(D(scs.get(v.get("scenario"))).get("steps")))
            for r in rids:
                els |= {D(rels.get(r)).get("from"), D(rels.get(r)).get("to")} - {None}
            return els

        def real_view():
            out = []
            for p in proofs():
                if "real" in p and not isinstance(p.get("real"), bool):
                    out.append(f"{PR} {p.get('id')}: real が true でも false でもない")
                if p.get("real") is not True:
                    continue
                v = p.get("view")
                if not isinstance(v, dict) or not any(not blank(v.get(k)) for k in ("elements", "relations", "scenario")):
                    out.append(f"{PR} {p.get('id')}: real が true なのに view がない")
                    continue
                if M not in self.data:
                    out.append(f"{PR} {p.get('id')}: view があるが、{M} が{'壊れている' if M in self.broken else 'ない'}")
                    continue
                els, rels, scs = model_parts()
                out += [f"{PR} {p.get('id')}: view.elements の {x} が仕組みの定義にない"
                        for x in L(v.get("elements")) if x not in els]
                out += [f"{PR} {p.get('id')}: view.relations の {x} が仕組みの定義にない"
                        for x in L(v.get("relations")) if x not in rels]
                if not blank(v.get("scenario")) and v.get("scenario") not in scs:
                    out.append(f"{PR} {p.get('id')}: view.scenario の {v.get('scenario')} が仕組みの定義にない")
            return out

        def reason():
            return [f"{PR} {p.get('id')}: relation が {p.get('relation')} なのに relation_reason がない"
                    for p in proofs() if p.get("relation") in ("statement", "list") and blank(p.get("relation_reason"))]

        def reuse():
            used = {}
            for p in proofs():
                for f in dict.fromkeys(L(p.get("facts"))):
                    used.setdefault(f, []).append(str(p.get("id")))
            out = [f"{PR}: {f} を {'、'.join(ids)} が使う" for f, ids in used.items() if len(ids) > 1]
            return (WARN, out, "意図した再掲かどうかを、工程5の承認のときに決める") if out else []

        def behavior_elements():
            if M not in self.data:
                return []
            structural = set()
            for p in proofs():
                if p.get("relation") in ("architecture", "entity-relation"):
                    structural |= view_elements(p)
            out = [f"{PR} {p.get('id')}: 要素 {e} が、構成または要素の関係の図に出ない"
                   for p in proofs() if p.get("relation") in ("interaction", "state-transition")
                   for e in sorted(view_elements(p) - structural, key=str)]
            return (WARN, out) if out else []

        def holds():
            out = []
            for p in proofs():
                h = p.get("holds")
                if not isinstance(h, list):
                    out.append(f"{PR} {p.get('id')}: holds がない(関係がない場合は空の一覧 [] と書く)")
                    continue
                out += [f"{PR} {p.get('id')}: holds の {x} が含意の語彙にない" for x in h if x not in IMPLICATIONS]
                if p.get("relation") in ("statement", "list") and h:
                    out.append(f"{PR} {p.get('id')}: relation が {p.get('relation')} なのに holds が空でない")
            return out

        self.rule(5, "ストーリーラインの全てのスライドに、立証の設計が1つずつある", [PR, ST], cover)
        self.rule(5, "relation が主張の種類の語彙にある", [PR],
                  lambda: [f"{PR} {p.get('id')}: relation の {p.get('relation')} が語彙にない"
                           for p in proofs() if p.get("relation") not in RELATIONS])
        self.rule(5, "facts が全て素材台帳にあり、verified: true で、superseded_by が空である", [PR, S], facts_ok)
        self.rule(5, "facts が、ストーリーラインの evidence を全て含む", [PR, ST], facts_cover)
        self.rule(5, "real が true のスライドに view があり、その要素、つながり、場面が全て仕組みの定義にある",
                  [PR], real_view)
        self.rule(5, "全てのスライドの show と focus が空でない", [PR],
                  lambda: [f"{PR} {p.get('id')}: {k} が空" for p in proofs()
                           for k in ("show", "focus") if blank(p.get(k)) or not str(p.get(k)).strip()])
        self.rule(5, "base が none または image である", [PR],
                  lambda: [f"{PR} {p.get('id')}: base が {p.get('base')}" for p in proofs()
                           if p.get("base", "none") not in ("none", "image")])
        self.rule(5, "「言い切り」と「並列の列挙」のスライドに、ほかの種類に当てはまらない理由がある", [PR], reason)
        self.rule(5, "同じ事実を複数のスライドが使う場合は、警告とする", [PR], reuse)
        self.rule(5, "やり取りや状態の遷移の図に出る要素が、構成または要素の関係の図のいずれかにも出る",
                  [PR], behavior_elements)
        self.rule(5, "全てのスライドに holds があり、含意の語彙で書かれている。並列の列挙と言い切りでは空である",
                  [PR], holds)

    # ---- 工程6 ----
    def stage6(self):
        PT, PR, T, ST = "06-patterns.yaml", "05-proof.yaml", "terms.yaml", "04-storyline.yaml"
        rows = lambda: self.get(PT)
        key = lambda r: (r.get("relation"), r.get("base", "none") or "none")

        def main_row(p):
            for r in rows():
                if key(r) == (p.get("relation"), p.get("base", "none") or "none") and r.get("size", "any") != "over":
                    return r
            return None

        def fields():
            out = []
            for i, r in enumerate(rows()):
                w = f"{PT} {i + 1}件目"
                if r.get("relation") not in RELATIONS:
                    out.append(f"{w}: relation の {r.get('relation')} が語彙にない")
                if r.get("size") not in ("any", "within", "over"):
                    out.append(f"{w}: size が any / within / over のいずれでもない")
                if r.get("base") not in ("none", "image"):
                    out.append(f"{w}: base が none でも image でもない")
                if blank(r.get("pattern")):
                    out.append(f"{w}: pattern がない")
                elif r.get("pattern") not in PATTERN_IMPLIES:
                    out.append(f"{w}: pattern の {r.get('pattern')} が、付属する型の候補にない")
            return out

        def covered():
            return [f"{PR} {p.get('id')}: relation {p.get('relation')}、base {p.get('base', 'none')} の行が対応表にない"
                    for p in self.get(PR) if main_row(p) is None]

        def not_shared():
            use = {}
            for r in rows():
                if r.get("size") != "over":
                    use.setdefault((r.get("pattern"), r.get("base")), set()).add(r.get("relation"))
            return [f"{PT}: 主な型 {pat}(base {base})を {'、'.join(sorted(map(str, rel)))} が使う"
                    for (pat, base), rel in use.items() if len(rel) > 1]

        def implies():
            out = []
            for p in self.get(PR):
                r = main_row(p)
                if r is None or r.get("pattern") not in PATTERN_IMPLIES:
                    continue
                lack = [x for x in PATTERN_IMPLIES[r.get("pattern")]
                        if x != "emphasized" and x not in L(p.get("holds"))]
                if lack:
                    out.append(f"{PR} {p.get('id')}: 型 {r.get('pattern')} の含意 {'、'.join(lack)} が holds にない")
            return out

        def axis():
            out = []
            for p in self.get(PR):
                r = main_row(p)
                imp = PATTERN_IMPLIES.get(D(r).get("pattern"), [])
                if {"grouped", "partition"} & set(imp) and blank(p.get("axis")):
                    out.append(f"{PR} {p.get('id')}: 型 {r.get('pattern')} がまとまりや分割を伝えるのに、axis が空")
            return out

        def samples():
            d = self.root / "06-samples"
            have = {x.stem for x in d.iterdir()} | {x.name for x in d.iterdir()} if d.is_dir() else set()
            used = {D(main_row(p)).get("pattern") for p in self.get(PR)} - {None}
            return [f"06-samples/: 型 {x} の見本がない" for x in sorted(used) if x not in have]

        def terms_def():
            slides = self.ids(ST) if ST in self.data else None
            out = []
            for t in L(self.get(T).get("terms")):
                t = D(t)
                if t.get("kind") != "noun":
                    continue
                if blank(t.get("defined_in")) and blank(t.get("no_definition")):
                    out.append(f"{T} {t.get('id')}: defined_in も、定義が要らない理由(no_definition)もない")
                elif not blank(t.get("defined_in")) and slides is not None and t.get("defined_in") not in slides:
                    out.append(f"{T} {t.get('id')}: defined_in の {t.get('defined_in')} がストーリーラインにない")
            return out

        self.rule(6, "対応表の各行に、語彙にある relation、size、base、付属する型の候補にある pattern がある", [PT], fields)
        self.rule(6, "立証設計に現れる全ての主張の種類と土台の組が、対応表にある(量の区分は未実装)", [PT, PR], covered)
        self.rule(6, "主な型が、同じ土台の中で、複数の主張の種類に使われていない", [PT], not_shared)
        self.rule(6, "全てのスライドについて、型の implies がスライドの holds に含まれる(emphasized を除く)",
                  [PT, PR], implies)
        self.rule(6, "型の implies に grouped、partition がある場合は、立証の設計の axis が空でない", [PT, PR], axis)
        self.rule(6, "資料で使う全ての型に、見本がある", [PT, PR], samples)
        self.rule(6, "対象を指す語の全てに、defined_in か、定義が要らない理由がある", [T], terms_def)

    # ---- 実行 ----
    def run(self, only=None):
        for name, message in getattr(self, "load_errors", []):
            stage = ARTIFACTS[name][0]
            self.add(0 if stage is None else stage, "成果物が読める", FAIL, [message])
        for stage in range(7):
            if only is not None and stage != only:
                continue
            names = [n for n, (s, _) in ARTIFACTS.items() if s == stage]
            present = [n for n in names if n in self.data or n in self.broken]
            if stage == 6 and (self.root / "06-samples").is_dir():
                present.append("06-samples/")
            if not present:
                self.add(stage, "成果物がある", ABSENT, note="、".join(n for n in names if n not in OPTIONAL))
                continue
            for n in names:
                if n not in present and n not in OPTIONAL:
                    self.add(stage, f"{n} がある", ABSENT, note="この成果物を使う条件は検査していない")
            getattr(self, f"stage{stage}")()
            for s, cond, why in NOT_IMPLEMENTED:
                if s == stage:
                    self.add(stage, cond, TODO, note=why)
        self.results.sort(key=lambda r: r["stage"])  # 安定な並べ替え。工程の中の順は保つ
        return self.results


def render(results, root):
    out = [f"検査の対象: {root}"]
    stage = None
    for r in results:
        if r["stage"] != stage:
            stage = r["stage"]
            out.append(f"\n== 工程{stage} {STAGE_NAMES[stage]} ==")
        line = f"[{r['status']}] {r['condition']}"
        if r["note"]:
            line += f" … {r['note']}"
        out.append(line)
        out += [f"    - {w}" for w in r["where"]]
    counts = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    out.append("\n集計: " + "、".join(f"{k} {counts[k]}件" for k in (PASS, FAIL, WARN, UNKNOWN, TODO, ABSENT) if k in counts))
    out.append("結果: " + ("不合格" if counts.get(FAIL) else "不合格なし"))
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="工程0から6の機械的な検査(最小版)")
    ap.add_argument("deck", help="資料のディレクトリ")
    ap.add_argument("--stage", type=int, choices=range(7), metavar="N", help="検査する工程(0から6)。省くと全て")
    ap.add_argument("--json", action="store_true", help="結果をJSONで出す")
    args = ap.parse_args(argv)
    if not Path(args.deck).is_dir():
        print(f"資料のディレクトリがない: {args.deck}", file=sys.stderr)
        return 2
    results = Checker(args.deck).run(args.stage)
    failed = any(r["status"] == FAIL for r in results)
    if args.json:
        print(json.dumps({"deck": str(args.deck), "failed": failed, "results": results}, ensure_ascii=False, indent=2))
    else:
        print(render(results, args.deck))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
