#!/usr/bin/env python3
"""工程表、工程の文書、検査の台帳から、スキル(.claude/skills/)を作る。

使い方:
  python3 tools/build_skills.py            スキルを作り直す
  python3 tools/build_skills.py --check    スキルが正本と一致するかだけを確かめる。ずれていれば終了コード1
  python3 tools/build_skills.py --stats    スキルごとの量、作業1件あたりの読む量、定めがない項目の数を出す。目安を超えたスキルは表示するだけで、終了コードは0

正本は、工程表(docs/tasks.yaml)、検査の台帳(docs/checks.yaml)、docs/ の文書である。
スキルは生成物で、直接は直さない。

スキルは、工程表の skills に挙げたものを作る。
  SKILL.md            守ることと、作業の一覧
  tasks/<作業>.md     作業ごとの手順。複数の工程で行う作業は、最初の工程のスキルが持ち、後の工程のスキルは指すだけにする

守ることは、工程表の roles の rules が指す見出しの文面である。
作業の手順は、工程表の sections が指す見出しの文面である。どちらも、言い換えずに写す。
references は、文面を写さず、場所だけを挙げる。リンクの先は、スキルの置き場から届く形に直す。

入力に制限のある作業(restricted)は、正本の文書を開かずに済む形にする。
  - 項目まで絞った入力は、機械が作る写し(work/views/<作業のid>/)を指す。写しは tools/work_order.py が作る。
  - references、検査の定義(defined_in)、制限の定め(restricted_by)、報告の書式が指す見出しの文面を、作業のファイルに写す。
  - 写した文面のリンクは、先を消して、文字だけにする。

--check が確かめること:
  - 工程表に誤りがない(tools/tasks_table.py と同じ確かめ)。
  - スキルのファイルが、正本から作り直したものと一致する。
  - 作り直したものにないファイルが、スキルのディレクトリにない。
  - SKILL.md の先頭の name と description が YAML として読める。SKILL.md が500行未満である。
  - 写した文面が指す見出しが、スキルにある。指し方は、文書へのリンクと、「」で囲んだ見出しの名前である。
      制限のある作業では、指す先の文面が、作業のファイルか「守ること」に写してある。
      文書の全体を指すリンクは、見出しまで絞れないので、確かめない。
      制限のない作業では、リンクのない「」の見出しが、写してあるか、参照に挙がっている。
  - 制限のある作業の references が、見出しまで絞られている。

道具が作ったファイルは、目印の行を持つ。作り直すとき、目印のある余分なファイルは消す。
目印のない余分なファイルは消さずに、誤りとして挙げる。
"""
import argparse
import os
import re
import statistics
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
HEAD_BYTES = 12000       # 先頭の約5,000トークンに当たる量の目安
PER_STAGE = ("designer", "pm")   # 工程ごとにスキルを持つ担当。入力の制限がなく、報告を返さない
COMMENT = re.compile(r"^<!-- .* -->$")
BACK = re.compile(r"^\[目次に戻る\]\([^)]*\)$")
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
QUOTED = re.compile(r"「([^「」]+)」")
NUMBERED = re.compile(r"^(\d+)\. ")
CHECKS = "checks.yaml"   # 検査の文面の出どころ。リンクは docs/ からの相対で書いてある
WRITES = "checks.md#独立に書く"   # この見出しを手順に持つ作業は、答えを書くだけで、合否を判定しない


def slug(title):
    """見出しから、リンクのアンカーを作る。tools/checks_table.py の anchors と同じ作り方。"""
    return re.sub(r"[^\w\- ]", "", title.strip().lower()).replace(" ", "-")


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

    def titles(self, path):
        doc = self.docs.get(path) if path.endswith(".md") else None
        return [h["title"] for h in doc.headings] if doc else []

    def target(self, link, path):
        """リンクの先を、(docs/ からの文書のパス, 見出し)にする。文書でなければ None。見出しがなければ、見出しは None。"""
        if re.match(r"[a-z]+:", link):
            return None
        name, _, anchor = link.partition("#")
        full = os.path.normpath(os.path.join(os.path.dirname(path), name)) if name else path
        full = full.replace(os.sep, "/")
        if full.startswith("..") or not self.titles(full):
            return None
        title = next((t for t in self.titles(full) if slug(t) == anchor), None) if anchor else None
        return full, title

    def defined(self, entry):
        """検査の defined_in を、「文書#見出し」にする。見出しまで絞れなければ、文書だけを返す。"""
        found = self.target(entry["defined_in"], CHECKS) if entry.get("defined_in") else None
        if not found:
            return None
        doc = self.docs.get(found[0])
        heading = next((h for h in doc.headings if h["title"] == found[1]), None)
        return f"{found[0]}#{found[1]}" if heading and doc.own_text(heading) else found[0]


def all_rules(src, role):
    """担当の「守ること」の見出し。作業の一覧の前に置くものと、後に置くものを合わせる。"""
    entry = src.plan.roles[role]
    return list(entry["rules"]) + list(entry.get("rules_after", []))


def plain(lines):
    """リンクの先を消して、文字だけにする。"""
    out, fenced = [], False
    for text in lines:
        if text.lstrip().startswith("```"):
            fenced = not fenced
        out.append(text if fenced else LINK.sub(lambda m: m.group(0) if re.match(r"[a-z]+:", m.group(2)) else m.group(1), text))
    return out


def relink(lines, source, out_dir):
    """リンクの先を、書き出すファイルの場所から届く形に直す。source は、元の文書の絶対パス。"""
    def fix(m):
        target = m.group(2)
        if re.match(r"[a-z]+:", target):
            return m.group(0)
        path, _, anchor = target.partition("#")
        full = os.path.normpath(os.path.join(os.path.dirname(source), path)) if path else source
        rel = os.path.relpath(full, out_dir).replace(os.sep, "/")
        return f"[{m.group(1)}](" + rel + ("#" + anchor if anchor else "") + ")"
    out, fenced = [], False
    for text in lines:
        if text.lstrip().startswith("```"):
            fenced = not fenced
        out.append(text if fenced else LINK.sub(fix, text))
    return out


def raw(src, ref):
    """「文書#見出し」が指す文面を、(見出し, 行の一覧)で返す。見出しの行、道具の目印の行、目次に戻る行は除く。"""
    path, _, title = ref.partition("#")
    doc = src.docs.get(path)
    numbers = sorted(doc.span(title))
    body = [t for t in doc.lines[numbers[0] + 1:numbers[-1] + 1]
            if not COMMENT.match(t.strip()) and not BACK.match(t.strip())]
    while body and not body[0].strip():
        body.pop(0)
    while body and not body[-1].strip():
        body.pop()
    return (doc.headings[0]["title"] + "の前文" if title == PREAMBLE else title), body


def mentions(src, path, lines, fallback=None):
    """文面が指す先を、(文書, 見出し, リンクがあるか)の組で挙げる。

    指し方は、文書へのリンクと、「」で囲んだ見出しの名前である。文書の題は、見出しに数えない。
    「」の名前は、同じ行で先に出たリンクの文書か、文面のある文書(fallback があれば、その文書)の見出しと比べる。"""
    found, fenced = [], False
    for text in lines:
        if text.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        tokens = [(m.start(), "link", m.group(2)) for m in LINK.finditer(text)]
        tokens += [(m.start(), "quote", m.group(1)) for m in QUOTED.finditer(text)]
        linked = None
        for _, kind, value in sorted(tokens):
            if kind == "link":
                hit = src.target(value, path)
                if hit:
                    found.append((hit[0], hit[1], True))
                    linked = hit[0]
            elif linked and value in src.titles(linked)[1:]:
                found.append((linked, value, True))
            else:
                own = fallback or (path if path != CHECKS else None)
                if own and value in src.titles(own)[1:]:
                    found.append((own, value, False))
    return found


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


VIEW_DIR = "work/views"   # 写しの置き場。資料のディレクトリから


def grouped_inputs(task):
    """inputs を、ファイルごとに (ファイル名, 項目の一覧) にまとめる。項目のない入力は、項目の一覧が空になる。"""
    grouped = {}
    for entry in task["inputs"]:
        name, sep, item = entry.partition("#")
        grouped.setdefault(name, [])
        if sep:
            grouped[name].append(item)
    return list(grouped.items())


def has_view(task, name, items):
    """この入力を、写しで渡すか。入力を限る作業の、項目まで絞った入力が当たる。"""
    return bool(task.get("restricted") and items and not name.startswith("「"))


def view_path(task, name):
    return f"{VIEW_DIR}/{task['id']}/{name}"


def item_text(items):
    """項目の一覧を、読む者に向けて書く。"""
    names = "".join(f"「{i.lstrip('-')}」" for i in items)
    return f"から{names}を除いたもの" if items[0].startswith("-") else f"の{names}だけ"


def input_text(task, name, items):
    """入力の1件を、読む者に向けて書く。"""
    if name.startswith("「"):
        return f"{name}(ファイル名は決まっていない)" + (item_text(items) if items else "")
    if has_view(task, name, items):
        return f"`{view_path(task, name)}`(写し。`{name}` {item_text(items)})"
    return f"`{name}`" + (" " + item_text(items) if items else "")


def input_lines(task):
    if not task["inputs"]:
        return ["工程表に、入力のファイルの定めがない。"]
    return ["- " + input_text(task, name, items) for name, items in grouped_inputs(task)]


def view_notice(task):
    """写しで渡す入力がある作業に添える文。"""
    if not any(has_view(task, name, items) for name, items in grouped_inputs(task)):
        return []
    return [f"`{VIEW_DIR}/` にある入力は、機械が元のファイルから作った写しである。元のファイルを開かない。"]


def output_formats(plan, task):
    """成果物のうち、書式の置き場が工程表の formats にあるものの「文書#見出し」。"""
    return [plan.formats[name] for name in task["outputs"] if name in plan.formats]


def output_lines(plan, task, where=None):
    """成果物の一覧。書式の定めがあるものには、その場所を添える。where は、場所の書き方を変える場合に渡す。"""
    if not task["outputs"]:
        return ["工程表に、成果物のファイルの定めがない。"]
    out = []
    for name in task["outputs"]:
        ref = plan.formats.get(name)
        out.append(f"- `{name}`" + (f"(書式は、{(where or place)(ref)}に定める)" if ref else ""))
    return out


class Page:
    """作業1件のファイル。写した見出しと、文面が指す先を覚えておき、後で確かめる。"""

    def __init__(self, src, task, out_dir):
        self.src, self.task, self.out_dir = src, task, out_dir
        self.restricted = bool(task.get("restricted"))
        self.rules = all_rules(src, task["role"])
        self.copied = []      # このファイルに写した「文書#見出し」
        self.found = []       # (出どころ, 文書, 見出し, リンクがあるか)
        self.pointed = set(task["references"])   # 文面を写さずに、場所を挙げた「文書#見出し」

    def text(self, lines, path, origin, fallback=None):
        """正本の文面を、書き出す形にする。指す先を覚える。"""
        self.found += [(origin,) + m for m in mentions(self.src, path, lines, fallback)]
        if self.restricted:
            return plain(lines)
        return relink(lines, os.path.join(self.src.docs_dir, path), self.out_dir)

    def copy(self, ref, hashes):
        """見出しの文面を写す。既に写したものと、「守ること」にあるものは、場所だけを書く。"""
        label, body = raw(self.src, ref)
        path = ref.partition("#")[0]
        out = [f"{hashes} {label}(`docs/{path}`)", ""]
        if ref in self.rules:
            return out + [f"スキル `{self.task['skill']}` の「守ること」に写してある。", ""]
        if ref in self.copied:
            return out + ["このファイルの上に写してある。", ""]
        self.copied.append(ref)
        return out + self.text(body, path, place(ref)) + [""]

    def has(self, ref):
        return ref in self.copied or ref in self.rules

    def check_line(self, entry):
        text = f"- `{entry['id']}` {entry['check']}({checks_table.judge_text(entry)})。{entry.get('note', '')}".rstrip()
        where = self.src.defined(entry)
        line = self.text([text], CHECKS, f"検査 {entry['id']}", where.partition("#")[0] if where else None)[0]
        if not where:
            return line
        if not self.restricted:
            self.pointed.add(where)
            return line + relink([f" [定義]({entry['defined_in']})"], os.path.join(self.src.docs_dir, CHECKS), self.out_dir)[0]
        self.found.append((f"検査 {entry['id']} の定義", where.partition("#")[0], where.partition("#")[2] or None, True))
        return line + f" 定義は、写してある「{where.partition('#')[2]}」にある。" if "#" in where else line

    def checks(self, hashes):
        """検査を、判定するものと、満たすものに分けて書く。"""
        task, ledger = self.task, self.src.ledger
        if not task["checks"]:
            return ["工程表に、この作業の検査がない。"]
        judged = [ledger[c] for c in task["checks"] if task["role"] in as_list(ledger[c]["judge"])]
        met = [ledger[c] for c in task["checks"] if task["role"] not in as_list(ledger[c]["judge"])]
        out = []
        writes = WRITES in task["sections"]
        for title, lead, entries in (
                ("書くもとになる検査", "次の検査が書かせるとしているものを書く。合否は判定しない。", judged if writes else []),
                ("判定する検査", "次の検査を判定する。", [] if writes else judged),
                ("満たす合格条件", "成果物は、次の条件を満たす。括弧の中は、判定者である。「警告」とある条件は、合否にしない。", met)):
            if not entries:
                continue
            out += ([""] if out else []) + [f"{hashes} {title}", "", lead, ""]
            for e in entries:
                out.append(self.check_line(e))
                for cid in as_list(e.get("refers", [])):
                    if cid not in task["checks"]:
                        out.append("  " + self.check_line(ledger[cid]))
        return out

    def unread(self, hashes):
        """読まないものを書く。"""
        task = self.task
        if not self.restricted:
            return ["この作業だけの制限はない。「守ること」に従う。"]
        out = ["入力に挙げたもの以外を読まない。このファイルと、スキルの「守ること」は読む。"
               "正本の文書(`docs/`)は開かない。要る箇所は、このファイルに写してある。"] + view_notice(task)
        by = task.get("restricted_by", [])
        if by:
            out += ["", "ファイルをまるごと渡す入力は、次の定めによる。"]
            for ref in by:
                if ref in self.src.ledger:
                    out += ["", f"- 検査 `{ref}`: " + self.text([self.src.ledger[ref]["check"]], CHECKS, f"検査 {ref}")[0]]
            for ref in by:
                if ref not in self.src.ledger:
                    out += [""] + self.copy(ref, hashes)[:-1]
        return out

    def siblings(self):
        """番号つきの手順のうち、この作業が行わないものを、行う作業とあわせて挙げる。"""
        out = []
        for path in dict.fromkeys(r.partition("#")[0] for r in self.task["sections"]):
            doc = self.src.docs.get(path)
            mine = {r.partition("#")[2] for r in self.task["sections"] if r.partition("#")[0] == path}
            parents = {tuple(h["parents"]) for h in doc.headings if h["title"] in mine and NUMBERED.match(h["title"])}
            for h in doc.headings:
                if tuple(h["parents"]) in parents and NUMBERED.match(h["title"]) and h["title"] not in mine:
                    owners = [t for t in self.src.plan.tasks if f"{path}#{h['title']}" in t["sections"]]
                    who = "、".join(f"`{t['id']}`({ROLES[t['role']]})" for t in owners) or "割り当てた作業がない"
                    out.append(f"- 「{h['title']}」: {who}")
        if out:
            out = ["番号は、正本の手順の番号のままである。この作業にない番号の手順は、次の作業が行う。", ""] + out + [""]
        return out

    def lines(self):
        """作業1件の手順を、行の一覧で返す。"""
        src, task = self.src, self.task
        out = [MARK, "", f"# `{task['id']}` {task['name']}", "", ORIGIN, ""]
        out += [f"担当は{ROLES[task['role']]}、工程は{stage_text(task['stage'])}である。", ""]
        if task.get("notes"):
            out += ["## 条件と覚え書き", ""] + [f"- {n}" for n in task["notes"]] + [""]
        out += ["## 入力", ""] + input_lines(task) + [""]
        out += ["## 読まないもの", ""] + self.unread("###") + [""]
        out += ["## 手順", ""]
        if self.restricted:
            out += ["この作業では、「守ること」の表より、入力の制限が優先する。", ""]
        if not task["sections"]:
            out += ["工程表に、手順を定めた見出しがない。" + ("「検査」の条件の文に従う。" if task["checks"] else ""), ""]
        out += self.siblings()
        for ref in task["sections"]:
            out += self.copy(ref, "###")
        out += ["## 成果物", ""] + output_lines(src.plan, task, lambda ref: f"このファイルの「{ref.partition('#')[2]}」") + [""]
        for ref in output_formats(src.plan, task):
            out += self.copy(ref, "###")
        out += ["## 検査", ""] + self.checks("###") + [""]
        out += ["## 参照", ""]
        refs = [r for r in task["references"] if r not in task["sections"]]
        if self.restricted:
            extra = [src.defined(src.ledger[c]) for c in task["checks"]]
            extra += [src.defined(src.ledger[r]) for c in task["checks"] for r in as_list(src.ledger[c].get("refers", []))]
            refs += [r for r in dict.fromkeys(extra) if r and "#" in r and r not in refs and r not in task["sections"]]
            refs = [r for r in refs if "#" in r and r not in self.rules]
            if refs:
                out += ["次の箇所を、正本から写した。正本の文書は開かない。", ""]
                for ref in refs:
                    out += self.copy(ref, "###")
        else:
            others = [r for r in refs if r not in self.rules]
            copied = [r for r in refs if r in self.rules]
            if others:
                out += ["次の箇所は、文面を写していない。必要なときに読む。パスは、リポジトリの根からである。", ""]
                out += places(others) + [""]
            if copied:
                out += [f"次の箇所は、スキル `{task['skill']}` の「守ること」に写してある。", ""] + places(copied) + [""]
        if not refs:
            out += ["工程表に、参照する箇所がない。", ""]
        report = src.plan.roles[task["role"]].get("report", [])
        if report:
            out += ["## 報告の書式", ""]
            for ref in report:
                out += self.copy(ref, "###")
        out += ["## 次の作業", ""]
        if not task["next"]:
            out += ["次の作業はない。ここで終わる。"]
        else:
            if len(task["next"]) > 1:
                out += ["分かれる場合と、順序が決まっていない場合がある。", ""]
            for tid in task["next"]:
                t = src.plan.by_id[tid]
                who = ROLES[t["role"]] + (f"、スキル `{t['skill']}`" if t["skill"] else "")
                out.append(f"- `{tid}` {t['name']}({who})")
        return out

    def errors(self):
        """文面が指す先のうち、スキルにないものを挙げる。lines() の後に呼ぶ。"""
        task, out = self.task, []
        for ref in task["references"]:
            if self.restricted and "#" not in ref:
                out.append(f"{task['id']}: references の {ref}: 入力に制限のある作業では、見出しまで絞る")
        for origin, path, title, linked in self.found:
            ref = f"{path}#{title}" if title else path
            if not title:
                continue      # 文書の全体を指す言及は、見出しまで絞れないので、確かめない
            if not (self.has(ref) or (not self.restricted and (linked or ref in self.pointed))):
                out.append(f"{task['id']}: {origin} が {place(ref)}を指すが、スキルに写していない。"
                           "工程表の sections か references に足す")
        return list(dict.fromkeys(out))


def skill_title(src, skill):
    if skill["role"] not in PER_STAGE:
        return ROLES[skill["role"]]
    stages = skill["stages"]
    name = src.stage_title(stages[0]) if len(stages) == 1 else f"工程{stage_text(stages)}"
    return f"{ROLES[skill['role']]}: {name}"


def skill_lines(src, skill):
    """SKILL.md の行の一覧と、誤りの一覧を返す。"""
    skill_dir = os.path.join(src.out_dir, skill["name"])
    front = yaml.safe_dump({"name": skill["name"], "description": skill["description"]},
                           allow_unicode=True, sort_keys=False, width=10000).rstrip("\n")
    out = ["---", front, "---", MARK, "", f"# {skill_title(src, skill)}", ""]
    if skill["role"] in PER_STAGE:
        out += ["いま行う作業のファイルを読む。工程の中の前後の作業のファイルは、必要なら読んでよい。", ""]
    else:
        out += ["作業票が指す作業のファイルを1つだけ読む。ほかの作業のファイルを読まない。", ""]
    out += [ORIGIN, "", "## 守ること", ""]
    rules, errors = all_rules(src, skill["role"]), []
    after = src.plan.roles[skill["role"]].get("rules_after", [])

    def rule(ref):
        label, body = raw(src, ref)
        path = ref.partition("#")[0]
        for doc, title, linked in mentions(src, path, body):
            if title and not linked and f"{doc}#{title}" not in rules:
                errors.append(f"{skill['name']}: 守ることの {place(ref)} が {place(doc + '#' + title)}を指すが、"
                              "スキルに写していない。工程表の roles の rules に足す")
        return [f"### {label}(`docs/{path}`)", ""] + relink(body, os.path.join(src.docs_dir, path), skill_dir) + [""]

    for ref in src.plan.roles[skill["role"]]["rules"]:
        out += rule(ref)
    if after:
        out += ["作業の一覧の後に、「守ること(続き)」がある。", ""]
    out += ["## 作業の一覧", "", "| 順 | 作業 | 名前 | 工程 | 手順 |", "|---|---|---|---|---|"]
    for number, (task, owned) in enumerate(src.plan.tasks_of(skill), 1):
        if owned:
            where = f"[tasks/{task['id']}.md](tasks/{task['id']}.md)"
        else:
            where = f"[`{task['skill']}`](../{task['skill']}/tasks/{task['id']}.md) が持つ"
        out.append(f"| {number} | `{task['id']}` | {task['name']} | {stage_text(task['stage'])} | {where} |")
    if after:
        out += ["", "## 守ること(続き)", ""]
        for ref in after:
            out += rule(ref)
        out.pop()
    return out, list(dict.fromkeys(errors))


def build(src):
    """全てのファイルを作る。(パスから中身への対応, 誤りの一覧)を返す。パスは、スキルの置き場から。"""
    expected, errors = {}, []
    for skill in src.plan.skills:
        lines, found = skill_lines(src, skill)
        errors += found
        expected[f"{skill['name']}/{SKILL_FILE}"] = "\n".join(lines) + "\n"
        task_dir = os.path.join(src.out_dir, skill["name"], "tasks")
        for task, owned in src.plan.tasks_of(skill):
            if owned:
                page = Page(src, task, task_dir)
                body = page.lines()
                errors += page.errors()
                expected[f"{skill['name']}/tasks/{task['id']}.md"] = "\n".join(body) + "\n"
    return expected, errors


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


def size(text):
    return len(text.encode("utf-8"))


def print_stats(src, expected):
    """量を出す。先頭に収まらないスキルは、表示するだけで、誤りにしない。収まらないスキルがあれば False を返す。"""
    fits_all, loads = True, {}
    print(f"スキル {len(src.plan.skills)} 個、ファイル {len(expected)} 個")
    print(f"先頭に収める量の目安は {HEAD_BYTES:,} バイト(約5,000トークン)。SKILL.md は、守ることと作業の一覧だけを持つ。")
    print("スキルごと(SKILL.md の行数とバイト数、作業のファイルの数と合計のバイト数):")
    for s in src.plan.skills:
        head = expected[f"{s['name']}/{SKILL_FILE}"]
        files = {p: t for p, t in expected.items() if p.startswith(s["name"] + "/tasks/")}
        fits = size(head) <= HEAD_BYTES
        fits_all = fits_all and fits
        print(f"  {s['name']}: {head.count(chr(10))}行、{size(head):,}バイト({'収まる' if fits else '収まらない'})、"
              f"作業のファイル {len(files)}個 {sum(size(t) for t in files.values()):,}バイト")
        for path, text in files.items():
            loads[path.split("/")[-1][:-3]] = (size(head) + size(text), s["role"])
    print("作業1件あたりの読む量(SKILL.md と、その作業のファイルの合計。バイト。作業の数、最大、中央):")
    for role, label in ROLES.items():
        found = sorted((n, tid) for tid, (n, r) in loads.items() if r == role)
        if found:
            print(f"  {label}: {len(found)}件、{found[-1][0]:,}({found[-1][1]})、{int(statistics.median(n for n, _ in found)):,}")
    every = sorted((n, tid) for tid, (n, _) in loads.items())
    print(f"  計: {len(every)}件、{every[-1][0]:,}({every[-1][1]})、{int(statistics.median(n for n, _ in every)):,}")
    tasks = [t for t in src.plan.tasks if t["skill"]]
    reportless = [t for t in tasks if t["role"] not in PER_STAGE and not src.plan.roles[t["role"]].get("report")]
    print(f"工程表に定めがない項目(スキルを持つ作業 {len(tasks)} 件のうち。誤りにはしない):")
    for label, found in (("入力", [t for t in tasks if not t["inputs"]]), ("成果物", [t for t in tasks if not t["outputs"]]),
                         ("手順の見出し", [t for t in tasks if not t["sections"]]),
                         ("検査", [t for t in tasks if not t["checks"]]), ("報告の書式", reportless)):
        print(f"  {label}: {len(found)}件" + (f"({'、'.join(t['id'] for t in found)})" if found else ""))
    return fits_all


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(description="工程表、工程の文書、検査の台帳から、スキルを作る")
    parser.add_argument("--check", action="store_true", help="スキルが正本と一致するかだけを確かめる")
    parser.add_argument("--stats", action="store_true", help="量と、定めがない項目の数を出す")
    parser.add_argument("--root", default=os.path.join(here, ".."), help="リポジトリの根")
    args = parser.parse_args()

    src = Source(args.root)
    if src.errors:
        print("正本に誤りがある。何も書いていない:", *src.errors, sep="\n  ")
        return 1
    expected, errors = build(src)
    errors += validate(expected)
    if errors:
        print("作ったスキルに誤りがある。何も書いていない:", *errors, sep="\n  ")
        return 1
    if args.stats:
        print_stats(src, expected)
        return 0

    stale, missing, extra, foreign = compare(src, expected)
    summary = f"スキルは正本と一致している(スキル {len(src.plan.skills)} 個、ファイル {len(expected)} 個)"
    if args.check:
        for title, paths in (("正本とずれているファイルがある:", stale), ("ないファイルがある:", missing),
                             ("余分なファイルがある:", extra + foreign)):
            if paths:
                print(title, *[os.path.join(".claude/skills", p) for p in paths], sep="\n  ")
        if stale or missing or extra or foreign:
            return 1
        print(summary)
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
        print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
