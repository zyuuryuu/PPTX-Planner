#!/usr/bin/env python3
"""検査の台帳(docs/checks.yaml)から、文書の中の合格条件の一覧を作る。

使い方:
  python3 tools/checks_table.py            文書を書き換える
  python3 tools/checks_table.py --check    文書が台帳と一致するかだけを確かめる。ずれていれば終了コード1
  python3 tools/checks_table.py --stats    工程ごと、判定者ごとの件数を出す

文書の中の、次の2行の間を書き換える。

  <!-- checks:begin -->        工程の文書(stages/NN-*.md)で、その工程の検査の全て
  <!-- checks:begin 名前 -->   group が「名前」の検査。「重大な検査」は、critical が true の検査の表
  <!-- checks:end -->

名前つきの区間に出した group は、名前のない区間には出さない。
台帳の中のリンクは、docs/ からの相対で書く。書き込む文書の場所に合わせて直す。
"""
import argparse
import os
import re
import sys

import yaml

JUDGES = {
    "machine": "機械",
    "inspector": "検査セッション",
    "user": "ユーザー",
    "reader": "読み手の役のセッション",
    "designer": "設計セッション",
}
REQUIRED = ("id", "stage", "target", "check", "judge")
ALLOWED = REQUIRED + ("group", "judge_text", "critical", "note", "defined_in")
BEGIN = re.compile(r"^<!-- checks:begin(?: (.+?))? -->$")
END = "<!-- checks:end -->"
NOTICE = "<!-- この区間は tools/checks_table.py が checks.yaml から作る。直接は直さない -->"
CRITICAL = "重大な検査"
LINK = re.compile(r"\]\(([^)]+)\)")


def as_list(value):
    return value if isinstance(value, list) else [value]


def load(ledger, docs):
    """台帳を読み、書式の誤りを挙げる。"""
    with open(ledger, encoding="utf-8") as f:
        entries = yaml.safe_load(f)
    errors, seen = [], set()
    for e in entries:
        eid = e.get("id", "(idなし)")
        for key in REQUIRED:
            if key not in e:
                errors.append(f"{eid}: {key} がない")
        for key in e:
            if key not in ALLOWED:
                errors.append(f"{eid}: 知らない項目 {key}")
        if eid in seen:
            errors.append(f"{eid}: id が重なっている")
        seen.add(eid)
        stages = as_list(e.get("stage", []))
        prefix = "KX" if len(stages) > 1 else "K%02d" % stages[0] if stages else "K"
        if not re.fullmatch(prefix + r"-\d\d", str(eid)):
            errors.append(f"{eid}: id が {prefix}-nn の形でない")
        for j in as_list(e.get("judge", [])):
            if j not in JUDGES:
                errors.append(f"{eid}: 知らない判定者 {j}")
        target = e.get("defined_in")
        if target and not os.path.exists(os.path.join(docs, target.split("#")[0])):
            errors.append(f"{eid}: defined_in の文書がない {target}")
    return entries, errors


def relink(text, doc_dir):
    """docs/ からの相対のリンクを、文書の場所からの相対に直す。"""
    def fix(m):
        target = m.group(1)
        if target.startswith(("http", "#")):
            return m.group(0)
        path, _, anchor = target.partition("#")
        rel = os.path.relpath(path, doc_dir).replace(os.sep, "/")
        return "](" + rel + ("#" + anchor if anchor else "") + ")"
    return LINK.sub(fix, text)


def judge_text(e):
    text = e.get("judge_text") or "と".join(JUDGES[j] for j in as_list(e["judge"]))
    return text + ("。重大な検査" if e.get("critical") else "")


def line(e, doc, doc_dir):
    """検査の1行。定義のある文書へのリンクは、行の中にも、書き込む文書にもない場合に付ける。"""
    text = f"- {e['check']}({judge_text(e)})。{e.get('note', '')} `{e['id']}`"
    target = e.get("defined_in")
    if target:
        linked = [t.split("#")[0] for t in LINK.findall(text + (e.get("group") or ""))]
        if target.split("#")[0] not in linked + [doc]:
            text += f" [定義]({target})"
    return relink(text, doc_dir)


def render(name, stage, entries, claimed, doc, used):
    """1つの区間の中身を、行の一覧で返す。doc は、docs/ から見た文書のパス。"""
    doc_dir = os.path.dirname(doc) or "."
    if name == CRITICAL:
        rows = [e for e in entries if e.get("critical")]
        out = ["| 工程 | 重大な検査 | ID |", "|---|---|---|"]
        for e in rows:
            stages = "、".join(str(s) for s in as_list(e["stage"]))
            out.append(relink(f"| {stages} | {e['check']} | `{e['id']}` |", doc_dir))
        return out
    rows = [e for e in entries if stage is None or stage in as_list(e["stage"])]
    if name:
        rows = [e for e in rows if e.get("group") == name]
    else:
        rows = [e for e in rows if e.get("group") not in claimed]
    out, group = [], None
    for e in rows:
        used.add(e["id"])
        if not name and e.get("group") != group:
            group = e.get("group")
            out += ([""] if out else []) + [relink(group, doc_dir) + ":", ""]
        out.append(line(e, doc, doc_dir))
    return out


def documents(docs):
    for root, _, files in sorted(os.walk(docs)):
        for name in sorted(files):
            if name.endswith(".md"):
                yield os.path.join(root, name)


def rebuild(path, docs, entries, claimed, used):
    """文書を読み、区間を作り直した全文を返す。区間がなければ None。"""
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    m = re.match(r"(\d\d)-", os.path.basename(path))
    stage = int(m.group(1)) if m else None
    doc = os.path.relpath(path, docs).replace(os.sep, "/")
    out, skipping, found = [], False, False
    for text in lines:
        begin = BEGIN.match(text)
        if begin:
            found, skipping = True, True
            body = render(begin.group(1), stage, entries, claimed, doc, used)
            out += [text, NOTICE, ""] + body + [""]
        elif text == END:
            skipping = False
            out.append(text)
        elif not skipping:
            out.append(text)
    if skipping:
        raise SystemExit(f"{path}: {END} がない")
    return ("\n".join(out), "\n".join(lines)) if found else None


def stats(entries):
    print(f"検査の件数: {len(entries)}")
    print("工程ごと(複数の工程で使う検査は、それぞれの工程で数える):")
    for stage in sorted({s for e in entries for s in as_list(e["stage"])}):
        count = sum(1 for e in entries if stage in as_list(e["stage"]))
        print(f"  工程{stage}: {count}")
    multi = sum(1 for e in entries if len(as_list(e["stage"])) > 1)
    print(f"  うち、複数の工程で使う検査: {multi}")
    print("判定者ごと(判定者が複数の検査は、それぞれで数える):")
    for key, label in JUDGES.items():
        count = sum(1 for e in entries if key in as_list(e["judge"]))
        print(f"  {label}: {count}")
    print(f"重大な検査: {sum(1 for e in entries if e.get('critical'))}")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(description="検査の台帳から、合格条件の一覧を作る")
    parser.add_argument("--check", action="store_true", help="文書が台帳と一致するかだけを確かめる")
    parser.add_argument("--stats", action="store_true", help="件数を出す")
    parser.add_argument("--docs", default=os.path.join(here, "..", "docs"), help="文書のディレクトリ")
    args = parser.parse_args()
    docs = os.path.normpath(args.docs)

    entries, errors = load(os.path.join(docs, "checks.yaml"), docs)
    if errors:
        print("台帳に誤りがある:", *errors, sep="\n  ")
        return 1
    if args.stats:
        stats(entries)
        return 0

    paths = list(documents(docs))
    claimed = set()
    for path in paths:
        with open(path, encoding="utf-8") as f:
            for text in f.read().split("\n"):
                begin = BEGIN.match(text)
                if begin and begin.group(1) and begin.group(1) != CRITICAL:
                    claimed.add(begin.group(1))

    used, stale = set(), []
    for path in paths:
        result = rebuild(path, docs, entries, claimed, used)
        if result is None or result[0] == result[1]:
            continue
        stale.append(path)
        if not args.check:
            with open(path, "w", encoding="utf-8") as f:
                f.write(result[0])
    missing = [e["id"] for e in entries if e["id"] not in used]
    if missing:
        print("どの文書にも出ていない検査がある:", *missing, sep="\n  ")
    if args.check and stale:
        print("台帳とずれている文書がある:", *stale, sep="\n  ")
    elif stale:
        print("書き換えた文書:", *stale, sep="\n  ")
    elif not missing:
        print("文書は台帳と一致している")
    return 1 if missing or (args.check and stale) else 0


if __name__ == "__main__":
    sys.exit(main())
