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
begin と end の組が崩れている文書が1つでもあれば、何も書かずにエラーで終わる。
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
    "pm": "PM",
}
REQUIRED = ("id", "stage", "target", "check", "judge")
ALLOWED = REQUIRED + ("group", "judge_text", "critical", "level", "refers", "note", "defined_in")
BEGIN = re.compile(r"^<!-- checks:begin(?: (.+?))? -->$")
END = "<!-- checks:end -->"
HEADING = re.compile(r"^#{1,6} (.+)$")
NOTICE = "<!-- この区間は tools/checks_table.py が checks.yaml から作る。直接は直さない -->"
CRITICAL = "重大な検査"
LINK = re.compile(r"\]\(([^)]+)\)")


def as_list(value):
    return value if isinstance(value, list) else [value]


def anchors(path, cache={}):
    """文書の見出しから、リンクのアンカーの一覧を作る。"""
    if path not in cache:
        found, fenced = set(), False
        with open(path, encoding="utf-8") as f:
            for text in f.read().split("\n"):
                if text.startswith("```"):
                    fenced = not fenced
                m = None if fenced else HEADING.match(text)
                if m:
                    slug = re.sub(r"[^\w\- ]", "", m.group(1).strip().lower())
                    found.add(slug.replace(" ", "-"))
        cache[path] = found
    return cache[path]


def load(ledger, docs):
    """台帳を読み、書式の誤りを挙げる。"""
    with open(ledger, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict) or not isinstance(data.get("checks"), list):
        return [], ["台帳に count と checks がない"]
    entries, errors, seen, texts, numbers = data["checks"], [], set(), {}, {}
    if data.get("count") != len(entries):
        errors.append(f"count が {data.get('count')} で、項目は {len(entries)} 件ある")
    for e in entries:
        eid = str(e.get("id", "(idなし)"))
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
        if re.fullmatch(prefix + r"-\d\d", eid):
            numbers.setdefault(prefix, []).append(int(eid[-2:]))
        else:
            errors.append(f"{eid}: id が {prefix}-nn の形でない")
        if e.get("check") in texts:
            errors.append(f"{eid}: check の文面が {texts[e.get('check')]} と同じである")
        texts.setdefault(e.get("check"), eid)
        for j in as_list(e.get("judge", [])):
            if j not in JUDGES:
                errors.append(f"{eid}: 知らない判定者 {j}")
        if not isinstance(e.get("critical", False), bool):
            errors.append(f"{eid}: critical が true でも false でもない")
        if e.get("level", "warning") != "warning":
            errors.append(f"{eid}: level は warning だけを書ける")
        target = e.get("defined_in")
        if target:
            path, _, anchor = target.partition("#")
            path = os.path.join(docs, path)
            if not os.path.exists(path):
                errors.append(f"{eid}: defined_in の文書がない {target}")
            elif anchor and anchor not in anchors(path):
                errors.append(f"{eid}: defined_in の見出しがない {target}")
    for e in entries:
        for ref in as_list(e.get("refers", [])):
            if ref not in seen:
                errors.append(f"{e.get('id')}: refers の先がない {ref}")
    for prefix, found in sorted(numbers.items()):
        gaps = sorted(set(range(1, max(found) + 1)) - set(found))
        if gaps:
            errors.append(f"{prefix}: 連番が飛んでいる {gaps}")
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
    text += "。重大な検査" if e.get("critical") else ""
    return text + ("。警告" if e.get("level") == "warning" else "")


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


def outside(lines, path):
    """区間の外の行を返す。begin と end の組が崩れていれば、エラーにする。"""
    kept, inside = [], False
    for number, text in enumerate(lines, 1):
        text = text.strip()
        if BEGIN.match(text):
            if inside:
                raise ValueError(f"{path}:{number}: end の前に次の begin がある")
            inside = True
        elif text == END:
            if not inside:
                raise ValueError(f"{path}:{number}: begin のない end がある")
            inside = False
        elif "checks:begin" in text or "checks:end" in text:
            raise ValueError(f"{path}:{number}: begin か end の書き方が違う")
        elif not inside:
            kept.append(text)
    if inside:
        raise ValueError(f"{path}: begin の後に end がない")
    return kept


def rebuild(path, docs, entries, claimed, used):
    """文書を読み、区間を作り直した全文と、元の全文を返す。区間がなければ None。"""
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    before = outside(lines, path)
    m = re.match(r"(\d\d)-", os.path.basename(path))
    stage = int(m.group(1)) if m else None
    doc = os.path.relpath(path, docs).replace(os.sep, "/")
    out, skipping, found = [], False, False
    for text in lines:
        begin = BEGIN.match(text.strip())
        if begin:
            found, skipping = True, True
            body = render(begin.group(1), stage, entries, claimed, doc, used)
            out += [text, NOTICE, ""] + body + [""]
        elif text.strip() == END:
            skipping = False
            out.append(text)
        elif not skipping:
            out.append(text)
    if outside(out, path) != before:
        raise ValueError(f"{path}: 区間の外の文面が変わる。書き込まない")
    return ("\n".join(out), "\n".join(lines)) if found else None


def stats(entries):
    checks = [e for e in entries if "refers" not in e]
    print(f"検査の件数: {len(checks)}(束ねて指す項目 {len(entries) - len(checks)} 件を含めると {len(entries)})")
    print("以下は、束ねて指す項目を除いて数える。")
    print("工程ごと(複数の工程で使う検査は、それぞれの工程で数える):")
    for stage in sorted({s for e in checks for s in as_list(e["stage"])}):
        count = sum(1 for e in checks if stage in as_list(e["stage"]))
        print(f"  工程{stage}: {count}")
    multi = sum(1 for e in checks if len(as_list(e["stage"])) > 1)
    print(f"  うち、複数の工程で使う検査: {multi}")
    print("判定者ごと(判定者が複数の検査は、それぞれで数える):")
    for key, label in JUDGES.items():
        count = sum(1 for e in checks if key in as_list(e["judge"]))
        print(f"  {label}: {count}")
    print(f"重大な検査: {sum(1 for e in checks if e.get('critical'))}")
    print(f"警告の検査: {sum(1 for e in checks if e.get('level') == 'warning')}")


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
                begin = BEGIN.match(text.strip())
                if begin and begin.group(1) and begin.group(1) != CRITICAL:
                    claimed.add(begin.group(1))

    used, stale, broken = set(), {}, []
    for path in paths:
        try:
            result = rebuild(path, docs, entries, claimed, used)
        except ValueError as error:
            broken.append(str(error))
            continue
        if result is not None and result[0] != result[1]:
            stale[path] = result[0]
    if broken:
        print("区間が崩れている。何も書いていない:", *broken, sep="\n  ")
        return 1
    if not args.check:
        for path, text in stale.items():
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
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
