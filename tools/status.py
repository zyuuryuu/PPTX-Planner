#!/usr/bin/env python3
"""状態の記録(status.yaml)を書く機械の命令。書式と決まりは docs/rework.md の「状態の記録」「承認の記録」「上流が変わったとき」。

使い方:
  python3 tools/status.py record-check <資料のディレクトリ> [--strict]
      検査の記録(checks/)から、成果物の状態を checked にする。不合格のある成果物は draft にする
  python3 tools/status.py record-approval <資料のディレクトリ> <成果物>... --by user|pm [--on 日付]
      承認を記録する。成果物が checked でなければ拒む
  python3 tools/status.py invalidate <資料のディレクトリ> [--old <前の版のディレクトリ>] [--dry-run]
      検査した版から変わった項目を見つけ、合格が無効になった成果物とスライドを invalid にする
  python3 tools/status.py show <資料のディレクトリ> [--invalid]
      状態の記録を表にして出す

状態の記録は、この道具と tools/check.py --write だけが書く。人とセッションは、直接は書かない。
終了コード: 拒んだ場合と、不合格で draft にした成果物がある場合は1。引数の誤りは2。
"""
import argparse
import datetime
import subprocess
import sys
from pathlib import Path

import yaml

import check as C

HEADER = "# 状態の記録。機械の命令(tools/status.py、tools/check.py --write)だけが書く。直接は直さない。\n"

# 台帳の target の先頭の名前と、成果物のファイル。
NAMES = {
    "ブリーフ": C.BRIEF, "資料の表現規約": C.STYLE, "仮説の一覧": C.HYPS, "探索の計画": C.PLAN,
    "素材台帳": C.SOURCES, "画像の素材": C.SOURCES, "仕組みの定義": C.MODEL, "問いごとの答え": C.ANSWERS,
    "主張の骨子": C.CLAIMS, "章構成": C.CHAPTERS, "ストーリーライン": C.STORY, "章の前提と到達点": C.STATES,
    "テストの場面": C.SCENARIOS, "立証の設計": C.PROOF, "表現の対応表": C.PATTERNS, "語彙表": C.TERMS,
}
# 下流の順。ある成果物「以降の全て」を挙げるのに使う。
ORDER = [C.BRIEF, C.STYLE, C.HYPS, C.PLAN, C.SOURCES, C.MODEL, C.TERMS, C.ANSWERS, C.CLAIMS, C.CHAPTERS,
         C.STORY, C.STATES, C.SCENARIOS, C.PROOF, C.PATTERNS]


def load_status(root):
    path = Path(root) / C.STATUS
    doc = {}
    if path.is_file():
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(doc, dict):
            raise SystemExit(f"{path} が読めない。最上位が項目の集まりでない")
    doc.setdefault("artifacts", {})
    doc.setdefault("slides", {})
    for key in ("artifacts", "slides"):
        if not isinstance(doc[key], dict):
            doc[key] = {}
    return doc


def save_status(root, doc):
    out = {"artifacts": doc.get("artifacts") or {}, "slides": doc.get("slides") or {}}
    text = yaml.safe_dump(out, allow_unicode=True, sort_keys=False, width=1000)
    (Path(root) / C.STATUS).write_text(HEADER + text, encoding="utf-8")


def git(root, *args):
    try:
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    except OSError:
        return None


def unchanged_between(root, a, b, name):
    """成果物が、2つの版の間で変わっていないか。確かめられなければ False。"""
    if a == b:
        return True
    if a is None or b is None:
        return False
    out = git(root, "diff", "--quiet", str(a), str(b), "--", name)
    return out is not None and out.returncode == 0


def unchanged_since(root, commit, name):
    """成果物が、その版から今の作業の場所まで変わっていないか。確かめられなければ None。"""
    if commit is None:
        return None
    out = git(root, "diff", "--quiet", str(commit), "--", name)
    if out is None or out.returncode not in (0, 1):
        return None
    return out.returncode == 0


def latest_records(root):
    """作業と対象ごとの、最後の回の検査の記録。(ファイル名, 中身) の一覧。"""
    best = {}
    base = Path(root) / "checks"
    for path in sorted(base.glob("*.yaml")) if base.is_dir() else []:
        m = C.re.fullmatch(r"(.+?)--(.+?)--(\d+)\.yaml", path.name)
        if not m:
            continue
        key, rnd = (m.group(1), m.group(2)), int(m.group(3))
        if key not in best or rnd > best[key][0]:
            best[key] = (rnd, path)
    out = []
    for rnd, path in best.values():
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(doc, dict):
            out.append((f"checks/{path.name}", doc))
    return out


def ledger_checks_for(name):
    """その成果物を対象にする、工程0から7の合否にする検査のうち、機械と検査セッションが判定するもの。"""
    out = []
    for cid, e in C.ledger().items():
        if "refers" in e or e.get("level") == "warning" or max(C.stages_of(e)) > 7:
            continue
        head = e.get("target", "").split(":")[0].strip()
        target = NAMES.get(head)
        if head == "スライド仕様" and name.startswith(C.SLIDES):
            target = name
        if target == name and {"machine", "inspector"} & set(C.as_list(e.get("judge"))):
            out.append(cid)
    return out


OTHER = {"状態の記録": C.STATUS, "実行の記録": "runs/", "全ての成果物": "*", "Issue": "*", "スライド仕様": C.SLIDES,
         "型の見本": C.SAMPLES, "ビルドした実物": "build/", "要約": "*", "要約、章のまとめ、節のまとめ": "*"}


def concerns(cid, name):
    """検査の行が、その成果物についてのものか。台帳の target から決める。決められない検査(文の機械の検査など)は、記録の全ての対象についてのものとする。"""
    head = C.ledger().get(cid, {}).get("target", "").split(":")[0].strip()
    owner = NAMES.get(head, OTHER.get(head))
    return owner is None or owner == name or (owner.endswith("/") and name.startswith(owner))


def carriers(deck, sid):
    """スライドの合格を持つ成果物。ストーリーライン、立証の設計、そのスライドの仕様のファイル。"""
    out = [C.STORY]
    if deck.exists(C.PROOF):
        out.append(C.PROOF)
    out += [name for name, s in deck.slide_specs(chapter=None) if s.get("id") == sid]
    return out


def record_check(root, only=None, strict=False):
    """検査の記録から、状態の記録を更新する。出した知らせの行の一覧を返す。"""
    root = Path(root)
    lines = []
    errors = [e for e in C.check_records(root) if e[0].startswith("checks/")]
    if errors:
        lines.append("検査の記録に書式の誤りがあるため、状態の記録を書かない。")
        lines += [f"  {f} {w}: {m}" for f, w, m in errors]
        record_check.failed = True
        return lines
    records = latest_records(root)
    by = {}
    for name, doc in records:
        for target in C.target_files(doc.get("target")):
            if (root / target).is_file():       # 成果物のファイルだけを、状態の記録に載せる
                by.setdefault(target, []).append((name, doc))
    wanted = set(by)
    if only is not None:
        only = {o if o.startswith("checks/") else f"checks/{o}" for o in only}
        wanted = {t for t, recs in by.items() if any(n in only for n, _ in recs)}
    status = load_status(root)
    record_check.failed = False
    for target in sorted(wanted):
        recs = by[target]
        failing = sorted({row["check"] for _, doc in recs for row in C.dicts(doc.get("results"))
                          if row.get("verdict") == "fail" and not C.is_warning(row.get("check"))
                          and concerns(row.get("check"), target)})
        commits = [doc.get("commit") for _, doc in recs]
        newest = max(recs, key=lambda r: (root / r[0]).stat().st_mtime)[1].get("commit")
        same = all(unchanged_between(root, c, newest, target) for c in commits)
        done = {row.get("check") for _, doc in recs for row in C.dicts(doc.get("results"))}
        open_ = [c for c in ledger_checks_for(target) if c not in done]
        waiting = [c for c in open_ if not (C.is_machine(C.ledger()[c]) and c not in C.CHECKS)]
        entry = dict(status["artifacts"].get(target) or {})
        was = entry.get("state")
        new = {"commit": newest, "rounds": max(int(doc.get("round") or 1) for _, doc in recs),
               "checks": sorted(n for n, _ in recs)}
        if not failing and not done & set(ledger_checks_for(target)):
            lines.append(f"{target}: 状態を変えない。この成果物を対象にする、工程0から7の検査の記録がない")
            continue
        stale = sorted(set(C.as_list(entry.get("checks"))) & set(new["checks"])) if was == "invalid" else []
        if stale and not failing:
            lines.append(f"{target}: invalid のまま。無効になる前の検査の記録が残っている({'、'.join(stale)})。検査し直す")
            record_check.failed = True
            continue
        if failing:
            new = {"state": "draft", **new}
            lines.append(f"{target}: draft。不合格の検査がある({'、'.join(failing)})")
            record_check.failed = True
        elif not same:
            new = {"state": "draft", **new}
            lines.append(f"{target}: draft。検査の記録ごとに対象の版が違い、同じ内容だと確かめられない({'、'.join(map(str, commits))})")
            record_check.failed = True
        elif strict and waiting:
            new = {"state": "draft", **new}
            lines.append(f"{target}: draft。検査の記録にない検査がある({'、'.join(waiting)})")
            record_check.failed = True
        elif was == "approved" and unchanged_between(root, entry.get("commit"), newest, target):
            new = {"state": "approved", **new, "commit": entry.get("commit"),
                   "approved_by": entry.get("approved_by"), "approved_on": entry.get("approved_on")}
            lines.append(f"{target}: approved のまま。承認した版が検査に通っている")
        else:
            new = {"state": "checked", **new}
            lines.append(f"{target}: checked(版 {newest or 'なし'}、{new['rounds']}回目)")
        if open_ and not failing:
            lines.append(f"  検査の記録にない、合否にする検査: {'、'.join(open_)}")
        status["artifacts"][target] = new
    deck = C.Deck(root)
    for sid in list(status["slides"]):
        states = [(status["artifacts"].get(n) or {}).get("state") for n in carriers(deck, sid)]
        if states and all(s in ("checked", "approved") for s in states):
            del status["slides"][sid]
            lines.append(f"スライド {sid}: 無効を解いた。ストーリーライン、立証の設計、スライド仕様が検査に通っている")
    save_status(root, status)
    return lines


def record_approval(root, artifacts, by, on):
    root = Path(root)
    status = load_status(root)
    problems = []
    for name in artifacts:
        entry = status["artifacts"].get(name)
        if not entry:
            problems.append(f"{name}: 状態の記録にない。検査の記録から checked にしてから承認を記録する")
        elif entry.get("state") != "checked":
            problems.append(f"{name}: 状態が {entry.get('state')} で、checked でない")
        elif unchanged_since(root, entry.get("commit"), name) is False:
            problems.append(f"{name}: 検査した版({entry.get('commit')})の後に内容が変わっている。検査し直す")
    if problems:
        return problems, False
    lines = []
    for name in artifacts:
        entry = status["artifacts"][name]
        entry.update({"state": "approved", "approved_by": by, "approved_on": on})
        lines.append(f"{name}: approved(版 {entry.get('commit')}、{by}、{on})")
    save_status(root, status)
    return lines, True


# ---------------------------------------------------------------- 上流が変わったとき

def old_text(root, old_dir, commit, name):
    """前の版の成果物の文面。得られなければ None。"""
    if old_dir is not None:
        path = Path(old_dir) / name
        return path.read_text(encoding="utf-8") if path.is_file() else None
    if commit is None:
        return None
    top = git(root, "rev-parse", "--show-prefix")
    if top is None or top.returncode != 0:
        return None
    out = git(root, "show", f"{commit}:{top.stdout.strip()}{name}")
    return out.stdout if out is not None and out.returncode == 0 else None


def parse(text):
    try:
        return yaml.safe_load(text) if text is not None else None
    except yaml.YAMLError:
        return None


def by_key(items, key="id"):
    return {i.get(key): i for i in C.dicts(items) if i.get(key) is not None}


def changed_items(old, new, key="id", fields=None):
    """前の版と今の版で、中身が違う件、足した件、消した件のID。fields を指定すると、その項目だけを比べる。"""
    a, b = by_key(old, key), by_key(new, key)
    out = []
    for k in list(dict.fromkeys(list(a) + list(b))):
        x, y = a.get(k), b.get(k)
        if x is None or y is None:
            out.append(k)
        elif fields is None and x != y:
            out.append(k)
        elif fields is not None and any(x.get(f) != y.get(f) for f in fields):
            out.append(k)
    return out


def brief_items_of(text):
    items, cur = {}, None
    for line in (text or "").split("\n"):
        if line.startswith("## "):
            cur = line[3:].strip()
            items[cur] = []
        elif cur is not None and line.strip():
            items[cur].append(line.strip())
    return items


def invalidate(root, old_dir=None, dry_run=False):
    """変わった項目から、合格が無効になった成果物とスライドを導く。docs/rework.md の「直す成果物と、無効になる範囲」の表のうち、機械で導けるもの。"""
    root = Path(root)
    status = load_status(root)
    deck = C.Deck(root)
    arts, slides, notes = {}, {}, []

    def art(name, reason):
        arts.setdefault(name, reason)

    def slide(sid, reason):
        if sid in deck.story_by_id:
            slides.setdefault(sid, reason)
            for name in spec_file.get(sid, []):
                art(name, f"スライド {sid}: {reason}")

    def after(name, reason):
        for n in ORDER[ORDER.index(name) + 1:]:
            art(n, reason)
        for n in list(deck.load_dir(C.SLIDES)) + list(deck.load_dir(C.SAMPLES)):
            art(n, reason)
        for sid in deck.story_by_id:
            slides.setdefault(sid, reason)

    spec_file = {}
    for name, s in deck.slide_specs(chapter=None):
        spec_file.setdefault(s.get("id"), []).append(name)
    files = list(ORDER) + list(deck.load_dir(C.SLIDES)) + list(deck.load_dir(C.SAMPLES))
    if (root / C.PATTERN_DEFS_FILE).is_file():
        files.append(C.PATTERN_DEFS_FILE)
    changed = {}
    for name in files:
        entry = status["artifacts"].get(name) or {}
        before = old_text(root, old_dir, entry.get("commit"), name)
        now = (root / name).read_text(encoding="utf-8") if (root / name).is_file() else None
        if before is None or now is None or before == now:
            continue
        changed[name] = (before, now)
        if entry.get("state") in ("checked", "approved"):
            art(name, "承認の後に内容が変わった" if entry["state"] == "approved" else "検査の後に内容が変わった")

    chapter_order = [c.get("id") for c in deck.chapters]

    def slides_from(chapter_ids, reason):
        if not chapter_ids:
            return
        first = min((chapter_order.index(c) for c in chapter_ids if c in chapter_order), default=None)
        if first is None:
            return
        later = set(chapter_order[first:])
        for s in deck.story:
            if s.get("chapter") in later:
                slide(s.get("id"), reason)

    for name, (before, now) in changed.items():
        old, new = parse(before), parse(now)
        if name == C.BRIEF:
            a, b = brief_items_of(before), brief_items_of(now)
            diff = [k for k in set(a) | set(b) if a.get(k) != b.get(k)]
            core = [k for k in diff if k in ("主な読み手", "目的", "答えるべき問い")]
            if core:
                after(C.STYLE, f"ブリーフの{'、'.join(core)}が変わった")
            if "外に出せない情報" in diff:
                art(C.SOURCES, "ブリーフの「外に出せない情報」が変わった。全ての画像の写り込みの検査をやり直す")
            rest = [k for k in diff if k not in core and k != "外に出せない情報"]
            if rest:
                notes.append(f"ブリーフの{'、'.join(rest)}が変わった。影響を受ける成果物は、設計セッションが挙げる")
        elif name == C.STYLE:
            notes.append("資料の表現規約が変わった。全ての成果物に、機械的な検査を再実行する")
        elif name == C.HYPS:
            art(C.SOURCES, "仮説の一覧が変わった。全ての事実の stance を見直す")
            art(C.CLAIMS, "仮説の一覧が変わった。仮説の比較を見直す")
        elif name == C.PLAN:
            for q in changed_items(old, new, fields=("question", "parent", "axis")):
                hit = ({q} | deck.descendants(q)) & set(deck.answers)
                if hit:
                    art(C.ANSWERS, f"問い {q} が変わった")
        elif name == C.SOURCES:
            ids = changed_items(old, new, fields=("statement", "value", "unit", "qualifiers", "file", "regions", "masked", "superseded_by"))
            for f in ids:
                why = f"{f} の値、記述、限定が変わった"
                if any(f in C.as_list(a.get("evidence")) for a in deck.answers.values()):
                    art(C.ANSWERS, why)
                if any(f in C.as_list(c.get("evidence")) for c in deck.claims.values()):
                    art(C.CLAIMS, why)
                for s in deck.story:
                    if f in C.as_list(s.get("evidence")):
                        art(C.STORY, why)
                        slide(s.get("id"), why)
                for sid, p in deck.proof.items():
                    if f in C.as_list(p.get("facts")):
                        art(C.PROOF, why)
                        slide(sid, why)
                for fname, s in deck.slide_specs(chapter=None):
                    if f in C.as_list(s.get("sources")) or s.get("body", {}).get("asset") == f:
                        slide(s.get("id"), why)
                if any(f in C.as_list(e.get("evidence")) for k in ("elements", "relations", "scenarios")
                       for e in deck.model_ids(k).values()):
                    art(C.MODEL, why)
        elif name == C.MODEL:
            ids = set()
            for key in ("elements", "relations", "scenarios"):
                ids |= set(changed_items((old or {}).get(key), (new or {}).get(key)))
            for sid, p in deck.proof.items():
                els, rels, scs = C.view_parts(deck, p.get("view"))
                hit = sorted(ids & (els | rels | scs))
                if hit:
                    art(C.PROOF, f"仕組みの定義の {'、'.join(hit)} が変わった")
                    slide(sid, f"仕組みの定義の {'、'.join(hit)} が変わった")
        elif name == C.ANSWERS:
            for q in changed_items(old, new, key="question", fields=("answer",)):
                why = f"問い {q} の答えが変わった"
                if any(q in C.as_list(a.get("from")) for a in deck.answers.values()):
                    art(C.ANSWERS, why + "。親の問いの答えを見直す")
                if any(c.get("question") == q for c in deck.claims.values()):
                    art(C.CLAIMS, why)
                if any(q in C.as_list(s.get("from")) for _, s in deck.sections.values()):
                    art(C.CHAPTERS, why)
                for s in deck.story:
                    if q in C.as_list(s.get("from")):
                        art(C.STORY, why)
                        slide(s.get("id"), why)
        elif name == C.CLAIMS:
            old, new = old or {}, new or {}
            if old.get("answer") != new.get("answer"):
                after(C.CLAIMS, "主張の骨子の結論(answer)が変わった")
            ids = changed_items(old.get("claims"), new.get("claims"), fields=("statement",))
            hit = [ch.get("id") for ch in deck.chapters if set(ids) & set(C.as_list(ch.get("claims")))]
            if hit:
                art(C.CHAPTERS, f"主張 {'、'.join(map(str, ids))} の文言が変わった")
                for s in deck.story:
                    if s.get("chapter") in hit:
                        art(C.STORY, f"主張 {'、'.join(map(str, ids))} の文言が変わった")
                        slide(s.get("id"), f"主張 {'、'.join(map(str, ids))} の文言が変わった")
            if old.get("summary") != new.get("summary"):
                notes.append("要約の文(summary)が変わった。要約のスライドを作り直し、ユーザーの承認を取り直す")
        elif name == C.CHAPTERS:
            old, new = old or {}, new or {}
            ids = changed_items(old.get("chapters"), new.get("chapters"))
            if [c.get("id") for c in C.dicts(old.get("chapters"))] != [c.get("id") for c in C.dicts(new.get("chapters"))]:
                ids = chapter_order
            if ids:
                why = f"章構成の {'、'.join(map(str, ids))} が変わった"
                art(C.STORY, why)
                art(C.STATES, why)
                slides_from(ids, why)
        elif name == C.STORY:
            fields = ("title", "point", "point_from", "role", "qualifiers", "provenance", "chapter", "section")
            ids = changed_items(old, new, fields=fields)
            a = [s.get("id") for s in C.dicts(old)]
            b = [s.get("id") for s in C.dicts(new)]
            kept = [i for i in a if i in b]
            if kept != [i for i in b if i in a]:
                notes.append("スライドの順序が変わった。章の前提と到達点と、そのスライドへの言及を持つスライドを見直す")
            for sid in ids:
                why = f"ストーリーラインの {sid} が変わった"
                art(C.PROOF, why)
                art(C.STATES, why)
                slide(sid, why)
                for fname, s in deck.slide_specs(chapter=None):
                    if any("{" + str(sid) + "}" in x for x in C.strings_in(s)):
                        slide(s.get("id"), f"言及する {sid} が変わった")
        elif name == C.STATES:
            ids = changed_items(old, new, key="chapter")
            slides_from(ids, f"章の前提と到達点の {'、'.join(map(str, ids))} が変わった")
        elif name == C.SCENARIOS:
            notes.append("テストの場面が変わった。その場面の実行の結果は使えない")
        elif name == C.PROOF:
            for sid in changed_items(old, new):
                slide(sid, f"立証の設計の {sid} が変わった")
                art(C.PATTERNS, f"立証の設計の {sid} が変わった。表現の対応表の集計を見直す")
        elif name in (C.PATTERNS, C.PATTERN_DEFS_FILE):
            if name == C.PATTERNS:
                a = {(t.get("relation"), t.get("size"), t.get("base")): t.get("pattern") for t in C.dicts(old)}
                b = {(t.get("relation"), t.get("size"), t.get("base")): t.get("pattern") for t in C.dicts(new)}
                types = {p for k in set(a) | set(b) if a.get(k) != b.get(k) for p in (a.get(k), b.get(k)) if p}
                why = "表現の対応表の型の割り当てが変わった"
            else:
                types = set(changed_items(old, new))
                why = "型の定義が変わった"
            for fname, s in deck.slide_specs(chapter=None):
                if s.get("body", {}).get("type") in types:
                    slide(s.get("id"), f"{why}({s['body']['type']})")
            for fname, specs in deck.load_dir(C.SAMPLES).items():
                if any(s.get("body", {}).get("type") in types for s in specs):
                    art(fname, why)
        elif name == C.TERMS:
            a = {t.get("id"): t.get("term") for t in C.dicts((old or {}).get("terms"))}
            b = {t.get("id"): t.get("term") for t in C.dicts((new or {}).get("terms"))}
            words = [w for i, w in a.items() if b.get(i) != w and isinstance(w, str)]
            for fname, s in deck.slide_specs(chapter=None):
                hit = [w for w in words if any(w in x for x in C.strings_in(s))]
                if hit:
                    slide(s.get("id"), f"語彙表の語「{'」「'.join(hit)}」が変わった")
        elif name.startswith(C.SLIDES):
            for sid in changed_items(old, new):
                slides.setdefault(sid, "スライド仕様の中身が変わった")

    lines = []
    for name, reason in arts.items():
        entry = status["artifacts"].get(name)
        if entry and entry.get("state") in ("checked", "approved"):
            lines.append(f"{name}: invalid。{reason}")
            entry["state"], entry["reason"] = "invalid", reason
    tracked = set(status["artifacts"])
    for sid, reason in slides.items():
        if tracked & set(carriers(deck, sid)):
            lines.append(f"スライド {sid}: invalid。{reason}")
            status["slides"][sid] = {"state": "invalid", "reason": reason}
    lines += [f"知らせ: {n}" for n in notes]
    if not changed:
        lines.append("検査した版から変わった成果物はない。" if old_dir is None else "前の版から変わった成果物はない。")
    if not dry_run:
        save_status(root, status)
    return lines


def show(root, only_invalid=False):
    status = load_status(root)
    lines = ["| 成果物 | 状態 | 版 | 回 | 承認 | 理由 |", "|---|---|---|---|---|---|"]
    for name, e in status["artifacts"].items():
        if only_invalid and e.get("state") != "invalid":
            continue
        who = f"{e.get('approved_by')} {e.get('approved_on')}" if e.get("state") == "approved" else ""
        lines.append(f"| {name} | {e.get('state')} | {e.get('commit')} | {e.get('rounds', '')} | {who} | {e.get('reason', '')} |")
    if status["slides"]:
        lines += ["", "| スライド | 状態 | 理由 |", "|---|---|---|"]
        lines += [f"| {sid} | {e.get('state')} | {e.get('reason', '')} |" for sid, e in status["slides"].items()]
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser(description="状態の記録(status.yaml)を書く機械の命令。")
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("record-check", help="検査の記録から、成果物の状態を checked にする")
    p.add_argument("deck")
    p.add_argument("--strict", action="store_true", help="検査の記録にない検査(実装していない機械の検査を除く)があれば、checked にしない")
    p = sub.add_parser("record-approval", help="承認を記録する")
    p.add_argument("deck")
    p.add_argument("artifacts", nargs="+", help="成果物のファイル名(資料のディレクトリからの相対)")
    p.add_argument("--by", required=True, choices=["user", "pm"], help="承認した者")
    p.add_argument("--on", help="承認した日(YYYY-MM-DD)。省くと今日")
    p = sub.add_parser("invalidate", help="合格が無効になった成果物とスライドを invalid にする")
    p.add_argument("deck")
    p.add_argument("--old", help="前の版を置いたディレクトリ。省くと、状態の記録の版をGitから取り出す")
    p.add_argument("--dry-run", action="store_true", help="挙げるだけで、状態の記録を書かない")
    p = sub.add_parser("show", help="状態の記録を出す")
    p.add_argument("deck")
    p.add_argument("--invalid", action="store_true", help="無効のものだけを出す")
    args = ap.parse_args(argv)
    if not Path(args.deck).is_dir():
        ap.error(f"{args.deck} はディレクトリでない")

    if args.command == "record-check":
        lines = record_check(args.deck, strict=args.strict)
        print("\n".join(lines) if lines else "検査の記録がない。")
        return 1 if record_check.failed else 0
    if args.command == "record-approval":
        on = args.on or datetime.date.today().isoformat()
        try:
            datetime.date.fromisoformat(on)
        except ValueError:
            ap.error(f"--on {on} が日付(YYYY-MM-DD)でない")
        lines, ok = record_approval(args.deck, args.artifacts, args.by, on)
        print("\n".join(lines))
        if not ok:
            print("承認を記録しなかった。", file=sys.stderr)
        return 0 if ok else 1
    if args.command == "invalidate":
        print("\n".join(invalidate(args.deck, args.old, args.dry_run)))
        return 0
    print("\n".join(show(args.deck, args.invalid)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
