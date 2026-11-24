#!/usr/bin/env python3
"""工程表(docs/tasks.yaml)を確かめ、作業の一覧を文書に書き出す。

使い方:
  python3 tools/tasks_table.py            文書の中の作業の一覧を書き換える
  python3 tools/tasks_table.py --check    工程表と文書を確かめる。誤りがあれば終了コード1
  python3 tools/tasks_table.py --stats    作業ごと、担当ごとの読む量(バイト)を出す
  python3 tools/tasks_table.py --table    工程ごとの作業の一覧を Markdown で出す

文書の中の、次の2行の間を書き換える。

  <!-- tasks:begin -->
  <!-- tasks:end -->

begin と end の組が崩れている文書が1つでもあれば、何も書かずにエラーで終わる。

sections と references は「文書#見出し」の形で書く。見出しは、文書にある文字列のままとする。
「文書#前文」は、文書の題から最初の見出しまでを指す。見出しを付けなければ、文書まるごとを指す。
1箇所は、見出しから、次の同じ深さ以上の見出しの手前までである。

工程の文書(stages/)の見出しは、いずれかの作業の sections に割り当てる。次の見出しは対象から外す。
  - 直下に文がない見出し
  - 直下が、検査の台帳から作る区間だけの見出し(合格条件、開始の条件、終了の条件)
"""
import argparse
import os
import re
import statistics
import sys

import yaml

ROLES = {
    "user": "ユーザー",
    "designer": "設計セッション",
    "collector": "収集セッション",
    "writer": "執筆のセッション",
    "inspector": "検査セッション",
    "reader": "読み手の役のセッション",
    "pm": "PM",
    "machine": "機械",
}
SKILLS = {
    "user": None,
    "designer": "planner-designer",
    "collector": "planner-collector",
    "writer": "planner-writer",
    "inspector": "planner-inspector",
    "reader": "planner-reader",
    "pm": "planner-pm",
    "machine": None,
}
REQUIRED = ("id", "stage", "name", "role", "skill", "inputs", "outputs", "sections", "references", "checks", "next")
LISTS = ("inputs", "outputs", "sections", "references", "checks", "next")
PREAMBLE = "前文"
BEGIN = "<!-- tasks:begin -->"
END = "<!-- tasks:end -->"
NOTICE = "<!-- この区間は tools/tasks_table.py が tasks.yaml から作る。直接は直さない -->"
HEADING = re.compile(r"^(#{1,6}) (.+?)\s*$")
CHECKS_BEGIN = re.compile(r"^<!-- checks:begin(?: .+?)? -->$")
CHECKS_END = "<!-- checks:end -->"


def as_list(value):
    return value if isinstance(value, list) else [value]


class Doc:
    """文書の行と見出し。見出しごとに、範囲(end)と、直下の範囲(own_end)を持つ。"""

    def __init__(self, path):
        with open(path, encoding="utf-8") as f:
            self.lines = f.read().split("\n")
        self.sizes = [len((text + "\n").encode("utf-8")) for text in self.lines]
        if self.lines and self.lines[-1] == "":
            self.sizes[-1] = 0
        found, fenced = [], False
        for number, text in enumerate(self.lines):
            if text.startswith("```"):
                fenced = not fenced
            m = None if fenced else HEADING.match(text)
            if m:
                found.append({"line": number, "level": len(m.group(1)), "title": m.group(2)})
        total = len(self.lines)
        for k, h in enumerate(found):
            later = found[k + 1:]
            h["own_end"] = later[0]["line"] if later else total
            h["end"] = next((x["line"] for x in later if x["level"] <= h["level"]), total)
            h["parents"] = []
        stack = []
        for h in found:
            while stack and stack[-1]["level"] >= h["level"]:
                stack.pop()
            h["parents"] = [x["title"] for x in stack]
            stack.append(h)
        self.headings = found

    def span(self, title):
        """見出しの範囲を、行の番号の集合で返す。見出しがなければ、エラーの文を返す。"""
        if title is None:
            return set(range(len(self.lines)))
        if title == PREAMBLE:
            if not self.headings or self.headings[0]["level"] != 1:
                return "題がない"
            return set(range(self.headings[0]["line"], self.headings[0]["own_end"]))
        found = [h for h in self.headings if h["title"] == title]
        if len(found) != 1:
            return "見出しがない" if not found else f"同じ見出しが {len(found)} つある"
        return set(range(found[0]["line"], found[0]["end"]))

    def own_text(self, h):
        """見出しの直下の文。空行と、検査の台帳から作る区間を除く。"""
        kept, inside = [], False
        for text in self.lines[h["line"] + 1:h["own_end"]]:
            text = text.strip()
            if CHECKS_BEGIN.match(text):
                inside = True
            elif text == CHECKS_END:
                inside = False
            elif text and not inside:
                kept.append(text)
        return kept


class Docs:
    def __init__(self, root):
        self.root, self.cache = root, {}

    def get(self, path):
        if path not in self.cache:
            full = os.path.join(self.root, path)
            self.cache[path] = Doc(full) if os.path.isfile(full) else None
        return self.cache[path]

    def resolve(self, ref):
        """「文書#見出し」を、(文書, 行の集合)にする。だめなら (文書, エラーの文)。"""
        path, _, title = ref.partition("#")
        doc = self.get(path)
        if doc is None:
            return path, "文書がない"
        return path, doc.span(title or None)

    def size(self, path, numbers):
        doc = self.get(path)
        return sum(doc.sizes[n] for n in numbers)


def load(path):
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict) or not isinstance(data.get("tasks"), list):
        return [], ["工程表に count と tasks がない"]
    tasks, errors = data["tasks"], []
    if data.get("count") != len(tasks):
        errors.append(f"count が {data.get('count')} で、作業は {len(tasks)} 件ある")
    return tasks, errors


def is_stage_doc(path):
    return path.startswith("stages/")


def check(tasks, docs, ledger):
    """工程表の誤りを挙げる。"""
    errors, seen = [], set()
    for t in tasks:
        tid = str(t.get("id", "(idなし)"))
        for key in REQUIRED:
            if key not in t:
                errors.append(f"{tid}: {key} がない")
        for key in t:
            if key not in REQUIRED + ("command",):
                errors.append(f"{tid}: 知らない項目 {key}")
        if not re.fullmatch(r"[a-z][a-z0-9]*(-[a-z0-9]+)*", tid):
            errors.append(f"{tid}: id が小文字とハイフンの形でない")
        if tid in seen:
            errors.append(f"{tid}: id が重なっている")
        seen.add(tid)
        stages = as_list(t.get("stage", []))
        if not stages or any(not isinstance(s, int) or not 0 <= s <= 9 for s in stages):
            errors.append(f"{tid}: stage が0から9の番号でない")
        if not isinstance(t.get("name"), str) or not t.get("name"):
            errors.append(f"{tid}: name がない")
        role = t.get("role")
        if role not in ROLES:
            errors.append(f"{tid}: 知らない担当 {role}")
        elif t.get("skill") != SKILLS[role]:
            errors.append(f"{tid}: skill が {t.get('skill')} で、担当 {role} のスキルは {SKILLS[role]} である")
        if role == "machine":
            if "command" not in t:
                errors.append(f"{tid}: 機械の作業に command がない")
            elif t["command"] is not None and not isinstance(t["command"], str):
                errors.append(f"{tid}: command がコマンドの文でも null でもない")
        elif "command" in t:
            errors.append(f"{tid}: command は機械の作業だけに書く")
        for key in LISTS:
            if not isinstance(t.get(key, []), list):
                errors.append(f"{tid}: {key} が一覧でない")
    if errors:
        return errors
    for t in tasks:
        for key in ("sections", "references"):
            for ref in t[key]:
                _, numbers = docs.resolve(ref)
                if isinstance(numbers, str):
                    errors.append(f"{t['id']}: {key} の {ref}: {numbers}")
        for ref in t["sections"]:
            if "#" not in ref:
                errors.append(f"{t['id']}: sections の {ref}: 見出しがない。文書まるごとは references に書く")
        for target in t["next"]:
            if target not in seen:
                errors.append(f"{t['id']}: next の先がない {target}")
        for cid in t["checks"]:
            if cid not in ledger:
                errors.append(f"{t['id']}: 台帳にない検査 {cid}")
    used = {cid for t in tasks for cid in t["checks"]}
    for cid in ledger:
        if cid not in used:
            errors.append(f"{cid}: どの作業の checks にもない")
    errors += uncovered(tasks, docs)
    return errors


def uncovered(tasks, docs):
    """工程の文書の見出しのうち、どの作業の sections にも割り当たっていないものを挙げる。"""
    listed = {}
    for t in tasks:
        for ref in t["sections"]:
            path, _, title = ref.partition("#")
            listed.setdefault(path, set()).add(title)
    errors = []
    stage_dir = os.path.join(docs.root, "stages")
    for name in sorted(os.listdir(stage_dir)):
        if not name.endswith(".md"):
            continue
        path = "stages/" + name
        doc, titles = docs.get(path), listed.get("stages/" + name, set())
        for h in doc.headings:
            if not doc.own_text(h):
                continue
            if h["level"] == 1:
                covered = PREAMBLE in titles
            else:
                covered = h["title"] in titles or any(p in titles for p in h["parents"][1:])
            if not covered:
                label = PREAMBLE if h["level"] == 1 else h["title"]
                errors.append(f"{path}#{label}: どの作業の sections にもない")
    return errors


def volume(task, docs):
    """作業が読む箇所を、文書ごとの行の集合で返す。"""
    selected = {}
    for ref in task["sections"] + task["references"]:
        path, numbers = docs.resolve(ref)
        selected.setdefault(path, set()).update(numbers)
    return selected


def stats(tasks, docs):
    per_role, merged = {}, {}
    print("作業ごと(バイト):")
    for t in tasks:
        selected = volume(t, docs)
        size = sum(docs.size(path, numbers) for path, numbers in selected.items())
        per_role.setdefault(t["role"], []).append(size)
        for path, numbers in selected.items():
            merged.setdefault(t["role"], {}).setdefault(path, set()).update(numbers)
        print(f"  {t['id']}({ROLES[t['role']]}): {size:,}")
    print("担当ごと(バイト。作業の数、合計、1つの作業の最大、中央、重なりを除いた量):")
    everything = []
    for role, label in ROLES.items():
        sizes = per_role.get(role)
        if not sizes:
            continue
        everything += sizes
        union = sum(docs.size(path, numbers) for path, numbers in merged[role].items())
        print(f"  {label}: {len(sizes)}件、{sum(sizes):,}、{max(sizes):,}、{int(statistics.median(sizes)):,}、{union:,}")
    print(f"  計: {len(everything)}件、{sum(everything):,}、{max(everything):,}、{int(statistics.median(everything)):,}")


def table(tasks):
    """工程ごとの作業の一覧を、Markdown の行の一覧で返す。"""
    out = ["| 工程 | 作業 | 名前 | 担当 |", "|---|---|---|---|"]
    for t in tasks:
        stages = as_list(t["stage"])
        stage = str(stages[0]) if len(stages) == 1 else f"{stages[0]}〜{stages[-1]}"
        out.append(f"| {stage} | `{t['id']}` | {t['name']} | {ROLES[t['role']]} |")
    return out


def documents(root):
    for folder, _, files in sorted(os.walk(root)):
        for name in sorted(files):
            if name.endswith(".md"):
                yield os.path.join(folder, name)


def outside(lines, path):
    """区間の外の行を返す。begin と end の組が崩れていれば、エラーにする。"""
    kept, inside = [], False
    for number, text in enumerate(lines, 1):
        text = text.strip()
        if text == BEGIN:
            if inside:
                raise ValueError(f"{path}:{number}: end の前に次の begin がある")
            inside = True
        elif text == END:
            if not inside:
                raise ValueError(f"{path}:{number}: begin のない end がある")
            inside = False
        elif "tasks:begin" in text or "tasks:end" in text:
            raise ValueError(f"{path}:{number}: begin か end の書き方が違う")
        elif not inside:
            kept.append(text)
    if inside:
        raise ValueError(f"{path}: begin の後に end がない")
    return kept


def rebuild(path, body):
    """文書を読み、区間を作り直した全文と、元の全文を返す。区間がなければ None。"""
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    before = outside(lines, path)
    out, skipping, found = [], False, False
    for text in lines:
        if text.strip() == BEGIN:
            found, skipping = True, True
            out += [text, NOTICE, ""] + body + [""]
        elif text.strip() == END:
            skipping = False
            out.append(text)
        elif not skipping:
            out.append(text)
    if outside(out, path) != before:
        raise ValueError(f"{path}: 区間の外の文面が変わる。書き込まない")
    return ("\n".join(out), "\n".join(lines)) if found else None


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(description="工程表を確かめ、作業の一覧を文書に書き出す")
    parser.add_argument("--check", action="store_true", help="工程表と文書を確かめる")
    parser.add_argument("--stats", action="store_true", help="読む量を出す")
    parser.add_argument("--table", action="store_true", help="作業の一覧を Markdown で出す")
    parser.add_argument("--docs", default=os.path.join(here, "..", "docs"), help="文書のディレクトリ")
    args = parser.parse_args()
    root = os.path.normpath(args.docs)

    tasks, errors = load(os.path.join(root, "tasks.yaml"))
    if not errors:
        with open(os.path.join(root, "checks.yaml"), encoding="utf-8") as f:
            ledger = [e["id"] for e in yaml.safe_load(f)["checks"]]
        errors = check(tasks, Docs(root), ledger)
    if errors:
        print("工程表に誤りがある:", *errors, sep="\n  ")
        return 1
    if args.stats:
        stats(tasks, Docs(root))
        return 0
    if args.table:
        print("\n".join(table(tasks)))
        return 0

    stale, broken, found = {}, [], False
    for path in documents(root):
        try:
            result = rebuild(path, table(tasks))
        except ValueError as error:
            broken.append(str(error))
            continue
        if result is not None:
            found = True
            if result[0] != result[1]:
                stale[path] = result[0]
    if broken:
        print("区間が崩れている。何も書いていない:", *broken, sep="\n  ")
        return 1
    if not found:
        print("作業の一覧を書く区間が、どの文書にもない")
        return 1
    if not args.check:
        for path, text in stale.items():
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
    if args.check and stale:
        print("工程表とずれている文書がある:", *stale, sep="\n  ")
        return 1
    if stale:
        print("書き換えた文書:", *stale, sep="\n  ")
    else:
        print(f"工程表に誤りはない。文書は工程表と一致している(作業 {len(tasks)} 件)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
