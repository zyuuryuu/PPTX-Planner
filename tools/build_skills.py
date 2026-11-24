#!/usr/bin/env python3
"""工程表、工程の文書、検査の台帳から、スキル(.claude/skills/)を作る。

使い方:
  python3 tools/build_skills.py            スキルを作り直す
  python3 tools/build_skills.py --check    スキルが正本と一致するかだけを確かめる。ずれていれば終了コード1
  python3 tools/build_skills.py --stats    スキルごとの行数とバイト数、先頭に収まる範囲を出す

正本は、工程表(docs/tasks.yaml)、検査の台帳(docs/checks.yaml)、docs/ の文書である。
スキルは生成物で、直接は直さない。

スキルは、工程表の skills に挙げたものを作る。
  SKILL.md            守ること、作業の一覧、作業ごとの手順の順に書く
  tasks/<作業>.md     作業ごとの手順。次の場合に、SKILL.md から出す
                        収集、執筆、検査、読み手の役のスキル(全ての作業)
                        複数の工程で行う作業(最初の工程のスキルが持ち、後の工程のスキルは指すだけにする)
                        SKILL.md が行数の上限を超える場合の、長い作業

守ることは、工程表の roles の rules が指す見出しの文面である。
作業の手順は、工程表の sections が指す見出しの文面である。どちらも、言い換えずに写す。
リンクの先だけを、スキルの置き場から届く形に直す。references は、文面を写さず、場所だけを挙げる。

--check が確かめること:
  - 工程表に誤りがない(tools/tasks_table.py と同じ確かめ)。
  - スキルのファイルが、正本から作り直したものと一致する。
  - 作り直したものにないファイルが、スキルのディレクトリにない。
  - SKILL.md の先頭の name と description が YAML として読める。SKILL.md が500行未満である。

道具が作ったファイルは、目印の行を持つ。作り直すとき、目印のある余分なファイルは消す。
目印のない余分なファイルは消さずに、誤りとして挙げる。
"""
import argparse
import os
import re
import sys

import yaml

import checks_table
import tasks_table
from tasks_table import PREAMBLE, ROLES, as_list, stage_text

MARK = "<!-- 道具 tools/build_skills.py が作った。直接は直さない -->"
ORIGIN = ("道具 `tools/build_skills.py` が作ったファイルである。直接は直さない。"
          "正本は、工程表 `docs/tasks.yaml`、検査の台帳 `docs/checks.yaml`、`docs/` の文書である。"
          "直すときは、正本を直して、道具を実行する。")
SKILL_FILE = "SKILL.md"
MAX_LINES = 500          # SKILL.md は、この行数より短くする
SPLIT_AT = MAX_LINES   # この行数以上になったら、長い作業を tasks/ に出す
HEAD_BYTES = 12000       # 先頭の約5,000トークンに当たる量の目安
PER_STAGE = ("designer", "pm")   # 工程ごとにスキルを持ち、手順を SKILL.md に入れる担当
COMMENT = re.compile(r"^<!-- .* -->$")
LINK = checks_table.LINK


class Source:
    """正本。工程表、文書、検査の台帳をまとめて持つ。"""

    def __init__(self, root):
        self.root = os.path.normpath(root)
        self.docs_dir = os.path.join(self.root, "docs")
        self.out_dir = os.path.join(self.root, ".claude", "skills")
        self.docs = tasks_table.Docs(self.docs_dir)
        self.plan, self.errors = tasks_table.load_plan(os.path.join(self.docs_dir, "tasks.yaml"))
        entries, errors = checks_table.load(os.path.join(self.docs_dir, "checks.yaml"), self.docs_dir)
        self.errors += errors
        self.ledger = {e["id"]: e for e in entries}
        if not self.errors:
            judges = {cid: as_list(e["judge"]) for cid, e in self.ledger.items()}
            self.errors = tasks_table.check(self.plan, self.docs, judges)

    def stage_title(self, stage):
        """工程の文書の題。「工程1 探索」の形。"""
        for name in sorted(os.listdir(os.path.join(self.docs_dir, "stages"))):
            if name.startswith("%02d-" % stage):
                return self.docs.get("stages/" + name).headings[0]["title"]
        return f"工程{stage}"


def relink(lines, source, out_dir):
    """リンクの先を、書き出すファイルの場所から届く形に直す。source は、元の文書の絶対パス。"""
    def fix(m):
        target = m.group(1)
        if re.match(r"[a-z]+:", target):
            return m.group(0)
        path, _, anchor = target.partition("#")
        full = os.path.normpath(os.path.join(os.path.dirname(source), path)) if path else source
        rel = os.path.relpath(full, out_dir).replace(os.sep, "/")
        return "](" + rel + ("#" + anchor if anchor else "") + ")"
    out, fenced = [], False
    for text in lines:
        if text.lstrip().startswith("```"):
            fenced = not fenced
        out.append(text if fenced else LINK.sub(fix, text))
    return out


def excerpt(src, ref, out_dir):
    """「文書#見出し」が指す文面を、(見出し, 行の一覧)で返す。見出しの行と、道具の目印の行は除く。"""
    path, _, title = ref.partition("#")
    doc = src.docs.get(path)
    numbers = sorted(doc.span(title))
    body = [t for t in doc.lines[numbers[0] + 1:numbers[-1] + 1] if not COMMENT.match(t.strip())]
    while body and not body[0].strip():
        body.pop(0)
    while body and not body[-1].strip():
        body.pop()
    label = doc.headings[0]["title"] + "の前文" if title == PREAMBLE else title
    return label, relink(body, os.path.join(src.docs_dir, path), out_dir)


def place(ref):
    """「文書#見出し」を、リポジトリの根からのパスと見出しで書く。"""
    path, _, title = ref.partition("#")
    if not title:
        return f"`docs/{path}` の全体"
    return f"`docs/{path}` の「{'題から最初の見出しまで' if title == PREAMBLE else title}」"


def places(refs):
    """見出しの一覧を、文書ごとにまとめて書く。"""
    grouped = {}
    for ref in refs:
        path, _, title = ref.partition("#")
        grouped.setdefault(path, []).append(title)
    out = []
    for path, titles in grouped.items():
        if titles == [""]:
            out.append(f"- `docs/{path}` の全体")
        else:
            names = "".join(f"「{'題から最初の見出しまで' if t == PREAMBLE else t}」" for t in titles)
            out.append(f"- `docs/{path}` の{names}")
    return out


def input_text(entry):
    """inputs の1件を、読む者に向けて書く。"""
    name, sep, item = entry.partition("#")
    if name.startswith("「"):
        return f"{name}(ファイル名は決まっていない)" + (f"の「{item}」" if sep else "")
    return f"`{name}`" + (f" の「{item}」だけ" if sep else "")


def input_lines(task):
    if not task["inputs"]:
        return ["工程表に、入力のファイルの定めがない。"]
    return ["- " + input_text(e) for e in task["inputs"]]


def unread_lines(src, task):
    """読まないものを書く。"""
    if not task.get("restricted"):
        return ["この作業だけの制限はない。「守ること」に従う。"]
    out = ["入力に挙げたもの以外を読まない。スキルの手順と、手順の「参照」に挙げた文書の箇所は読む。"]
    by = [f"検査 `{r}`" if r in src.ledger else place(r) for r in task.get("restricted_by", [])]
    if by:
        out += ["", "ファイルをまるごと渡す入力は、次の定めによる: " + "、".join(by) + "。"]
    return out


def output_lines(task):
    if not task["outputs"]:
        return ["工程表に、成果物のファイルの定めがない。"]
    return [f"- `{name}`" for name in task["outputs"]]


def check_line(src, e, out_dir):
    text = f"- `{e['id']}` {e['check']}({checks_table.judge_text(e)})。{e.get('note', '')}".rstrip()
    if e.get("defined_in"):
        text += f" [定義]({e['defined_in']})"
    return relink([text], os.path.join(src.docs_dir, "checks.yaml"), out_dir)[0]


def check_lines(src, task, out_dir, hashes):
    """検査を、判定するものと、満たすものに分けて書く。"""
    judged = [src.ledger[c] for c in task["checks"] if task["role"] in as_list(src.ledger[c]["judge"])]
    met = [src.ledger[c] for c in task["checks"] if task["role"] not in as_list(src.ledger[c]["judge"])]
    if not task["checks"]:
        return ["工程表に、この作業の検査がない。"]
    out = []
    for title, lead, entries in (
            ("判定する検査", "次の検査を判定する。", judged),
            ("満たす合格条件", "成果物は、次の条件を満たす。括弧の中は、判定者である。「警告」とある条件は、合否にしない。", met)):
        if not entries:
            continue
        out += ([""] if out else []) + [f"{hashes} {title}", "", lead, ""]
        for e in entries:
            out.append(check_line(src, e, out_dir))
            for cid in as_list(e.get("refers", [])):
                if cid not in task["checks"]:
                    out.append("  " + check_line(src, src.ledger[cid], out_dir))
    return out


def next_lines(src, task):
    if not task["next"]:
        return ["次の作業はない。ここで終わる。"]
    out = []
    for tid in task["next"]:
        t = src.plan.by_id[tid]
        who = ROLES[t["role"]] + (f"、スキル `{t['skill']}`" if t["skill"] else "")
        out.append(f"- `{tid}` {t['name']}({who})")
    if len(out) > 1:
        out = ["分かれる場合と、順序が決まっていない場合がある。", ""] + out
    return out


def task_lines(src, task, out_dir, level, printed=None):
    """作業1件の手順を、行の一覧で返す。level は、作業の題の見出しの深さ。

    printed は、同じファイルに既に写した見出しから、写した作業への対応。同じ文面を2度は写さない。"""
    h1, h2, h3 = "#" * level, "#" * (level + 1), "#" * (level + 2)
    stages = as_list(task["stage"])
    out = [f"{h1} `{task['id']}` {task['name']}", ""]
    out += [f"担当は{ROLES[task['role']]}、工程は{stage_text(stages)}である。", ""]
    if task.get("notes"):
        out += [f"{h2} 条件と覚え書き", ""] + [f"- {n}" for n in task["notes"]] + [""]
    out += [f"{h2} 入力", ""] + input_lines(task) + [""]
    out += [f"{h2} 読まないもの", ""] + unread_lines(src, task) + [""]
    out += [f"{h2} 手順", ""]
    if not task["sections"]:
        out += ["工程表に、手順を定めた見出しがない。" + ("「検査」の条件の文に従う。" if task["checks"] else ""), ""]
    for ref in task["sections"]:
        label, body = excerpt(src, ref, out_dir)
        out += [f"{h3} {label}(`docs/{ref.partition('#')[0]}`)", ""]
        if printed is not None and ref in printed:
            out += [f"上の `{printed[ref]}` の手順に写した文面と同じである。", ""]
            continue
        if printed is not None:
            printed[ref] = task["id"]
        out += body + [""]
    out += [f"{h2} 成果物", ""] + output_lines(task) + [""]
    out += [f"{h2} 検査", ""] + check_lines(src, task, out_dir, h3) + [""]
    out += [f"{h2} 参照", ""]
    rules = src.plan.roles[task["role"]]["rules"]
    copied = [r for r in task["references"] if r in rules]
    others = [r for r in task["references"] if r not in rules]
    if others:
        out += ["次の箇所は、文面を写していない。必要なときに読む。パスは、リポジトリの根からである。", ""]
        out += places(others) + [""]
    if copied:
        out += [f"次の箇所は、スキル `{task['skill']}` の「守ること」に写してある。", ""] + places(copied) + [""]
    if not task["references"]:
        out += ["工程表に、参照する箇所がない。", ""]
    out += [f"{h2} 次の作業", ""] + next_lines(src, task) + [""]
    return out


def skill_title(src, skill):
    if skill["role"] not in PER_STAGE:
        return ROLES[skill["role"]]
    stages = skill["stages"]
    name = src.stage_title(stages[0]) if len(stages) == 1 else f"工程{stage_text(stages)}"
    return f"{ROLES[skill['role']]}: {name}"


def skill_lines(src, skill, files):
    """SKILL.md の行の一覧を返す。files は、tasks/ に出す作業の id の集合。"""
    skill_dir = os.path.join(src.out_dir, skill["name"])
    listed = src.plan.tasks_of(skill)
    front = yaml.safe_dump({"name": skill["name"], "description": skill["description"]},
                           allow_unicode=True, sort_keys=False, width=10000).rstrip("\n")
    out = ["---", front, "---", MARK, "", f"# {skill_title(src, skill)}", ""]
    if skill["role"] in PER_STAGE:
        out += ["作業票が指す作業の手順に従う。手順が別のファイルにある作業は、そのファイルを読む。", ""]
    else:
        out += ["作業票が指す作業のファイルを1つだけ読む。ほかの作業のファイルを読まない。", ""]
    out += [ORIGIN, "", "## 守ること", ""]
    for ref in src.plan.roles[skill["role"]]["rules"]:
        label, body = excerpt(src, ref, skill_dir)
        out += [f"### {label}(`docs/{ref.partition('#')[0]}`)", ""] + body + [""]
    out += ["## 作業の一覧", "", "| 順 | 作業 | 名前 | 工程 | 手順 |", "|---|---|---|---|---|"]
    for number, (task, owned) in enumerate(listed, 1):
        if not owned:
            where = f"[`{task['skill']}`](../{task['skill']}/tasks/{task['id']}.md) が持つ"
        elif task["id"] in files:
            where = f"[tasks/{task['id']}.md](tasks/{task['id']}.md)"
        else:
            where = "下にある"
        out.append(f"| {number} | `{task['id']}` | {task['name']} | {stage_text(task['stage'])} | {where} |")
    out.append("")
    head = len("\n".join(out).encode("utf-8"))
    inline = [t for t, owned in listed if owned and t["id"] not in files]
    if inline:
        out += ["## 作業ごとの手順", ""]
        printed = {}
        for task in inline:
            out += task_lines(src, task, skill_dir, 3, printed)
    while out and not out[-1]:
        out.pop()
    return out, head


def build(src):
    """全てのファイルを作る。(パスから中身への対応, スキルごとの統計)を返す。パスは、スキルの置き場から。"""
    expected, stats = {}, []
    for skill in src.plan.skills:
        owned = [t for t, mine in src.plan.tasks_of(skill) if mine]
        if skill["role"] in PER_STAGE:
            files = {t["id"] for t in owned if len(as_list(t["stage"])) > 1}
        else:
            files = {t["id"] for t in owned}
        sizes = {t["id"]: len(task_lines(src, t, "", 3)) for t in owned}
        while True:
            lines, head = skill_lines(src, skill, files)
            rest = [t["id"] for t in owned if t["id"] not in files]
            if len(lines) < SPLIT_AT or not rest:
                break
            files.add(max(rest, key=lambda tid: sizes[tid]))
        moved = sorted(files - {t["id"] for t in owned if len(as_list(t["stage"])) > 1}) \
            if skill["role"] in PER_STAGE else []
        expected[f"{skill['name']}/{SKILL_FILE}"] = "\n".join(lines) + "\n"
        task_dir = os.path.join(src.out_dir, skill["name"], "tasks")
        for task in owned:
            if task["id"] in files:
                body = [MARK, ""] + task_lines(src, task, task_dir, 1)
                body[4:4] = [ORIGIN, ""]
                while not body[-1]:
                    body.pop()
                expected[f"{skill['name']}/tasks/{task['id']}.md"] = "\n".join(body) + "\n"
        stats.append({"skill": skill["name"], "head": head, "moved": moved,
                      "paths": [p for p in expected if p.startswith(skill["name"] + "/")]})
    return expected, stats


def validate(expected):
    """作ったスキルの書式を確かめ、誤りを挙げる。"""
    errors = []
    for path, text in expected.items():
        if os.path.basename(path) != SKILL_FILE:
            continue
        name, lines = path.split("/")[0], text.split("\n")
        if len(lines) - 1 >= MAX_LINES:
            errors.append(f"{path}: {len(lines) - 1}行ある。{MAX_LINES}行未満にする")
        try:
            end = lines.index("---", 1)
            front = yaml.safe_load("\n".join(lines[1:end])) if lines[0] == "---" else None
        except (ValueError, yaml.YAMLError) as error:
            errors.append(f"{path}: 先頭の name と description が YAML として読めない({error})")
            continue
        if not isinstance(front, dict) or set(front) != {"name", "description"}:
            errors.append(f"{path}: 先頭の項目が name と description でない")
        elif front["name"] != name or not isinstance(front["description"], str) or not front["description"]:
            errors.append(f"{path}: name がディレクトリの名前と違う。または description がない")
    return errors


def on_disk(out_dir):
    """スキルの置き場にあるファイルを、パスから中身への対応で返す。"""
    found = {}
    for folder, _, files in os.walk(out_dir):
        for name in files:
            full = os.path.join(folder, name)
            with open(full, "rb") as f:
                found[os.path.relpath(full, out_dir).replace(os.sep, "/")] = f.read()
    return found


def marked(data):
    return MARK.encode("utf-8") in data


def compare(src, expected):
    """作り直したものと、置き場にあるものを比べる。(ずれ, ない, 余分, 手で置いた余分)を返す。

    余分とするのは、道具の持ち場にあって、作り直したものにないファイルである。
    持ち場は、工程表にあるスキルのディレクトリと、目印のある SKILL.md を持つディレクトリである。
    ほかのディレクトリは、道具が作ったスキルではないので、見ない。"""
    found = on_disk(src.out_dir)
    mine = {s["name"] for s in src.plan.skills}
    mine |= {p.split("/")[0] for p, data in found.items() if p.endswith("/" + SKILL_FILE) and marked(data)}
    stale = sorted(p for p, text in expected.items() if p in found and found[p] != text.encode("utf-8"))
    missing = sorted(p for p in expected if p not in found)
    extra = sorted(p for p in found if p not in expected and (p.split("/")[0] in mine or marked(found[p])))
    return stale, missing, [p for p in extra if marked(found[p])], [p for p in extra if not marked(found[p])]


def write(src, expected, stale, missing, extra):
    for path in stale + missing:
        full = os.path.join(src.out_dir, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as f:
            f.write(expected[path])
    for path in extra:
        full = os.path.join(src.out_dir, path)
        os.remove(full)
        folder = os.path.dirname(full)
        while folder != src.out_dir and not os.listdir(folder):
            os.rmdir(folder)
            folder = os.path.dirname(folder)


def print_stats(expected, stats):
    print(f"スキル {len(stats)} 個、ファイル {len(expected)} 個")
    print(f"先頭に収める量の目安は {HEAD_BYTES:,} バイト(約5,000トークン)。「先頭」は、守ることと作業の一覧が終わる位置である。")
    print("スキルごと(SKILL.md の行数とバイト数、先頭、作業のファイルの数と合計のバイト数):")
    for s in stats:
        text = expected[f"{s['skill']}/{SKILL_FILE}"]
        others = [expected[p] for p in s["paths"] if not p.endswith("/" + SKILL_FILE)]
        fits = "収まる" if s["head"] <= HEAD_BYTES else "収まらない"
        line = (f"  {s['skill']}: {text.count(chr(10))}行、{len(text.encode('utf-8')):,}バイト、"
                f"先頭 {s['head']:,}バイト({fits})、作業のファイル {len(others)}個")
        if others:
            line += f" {sum(len(t.encode('utf-8')) for t in others):,}バイト"
        print(line)
        if s["moved"]:
            print(f"    行数の上限のために出した作業: {'、'.join(s['moved'])}")
    longest = max((p for p in expected if "/tasks/" in p), key=lambda p: len(expected[p]), default=None)
    if longest:
        print(f"最も長い作業のファイル: {longest}({expected[longest].count(chr(10))}行、"
              f"{len(expected[longest].encode('utf-8')):,}バイト)")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(description="工程表、工程の文書、検査の台帳から、スキルを作る")
    parser.add_argument("--check", action="store_true", help="スキルが正本と一致するかだけを確かめる")
    parser.add_argument("--stats", action="store_true", help="行数とバイト数を出す")
    parser.add_argument("--root", default=os.path.join(here, ".."), help="リポジトリの根")
    args = parser.parse_args()

    src = Source(args.root)
    if src.errors:
        print("正本に誤りがある。何も書いていない:", *src.errors, sep="\n  ")
        return 1
    expected, stats = build(src)
    errors = validate(expected)
    if errors:
        print("作ったスキルの書式に誤りがある。何も書いていない:", *errors, sep="\n  ")
        return 1
    if args.stats:
        print_stats(expected, stats)
        return 1 if any(s["head"] > HEAD_BYTES for s in stats) else 0

    stale, missing, extra, foreign = compare(src, expected)
    if args.check:
        for title, paths in (("正本とずれているファイルがある:", stale), ("ないファイルがある:", missing),
                             ("余分なファイルがある:", extra + foreign)):
            if paths:
                print(title, *[os.path.join(".claude/skills", p) for p in paths], sep="\n  ")
        if stale or missing or extra or foreign:
            return 1
        print(f"スキルは正本と一致している(スキル {len(stats)} 個、ファイル {len(expected)} 個)")
        return 0
    write(src, expected, stale, missing, extra)
    for title, paths in (("書いたファイル:", stale + missing), ("消したファイル:", extra)):
        if paths:
            print(title, *[os.path.join(".claude/skills", p) for p in paths], sep="\n  ")
    if foreign:
        print("道具が作っていない余分なファイルがある。消していない:",
              *[os.path.join(".claude/skills", p) for p in foreign], sep="\n  ")
        return 1
    if not (stale or missing or extra):
        print(f"スキルは正本と一致している(スキル {len(stats)} 個、ファイル {len(expected)} 個)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
