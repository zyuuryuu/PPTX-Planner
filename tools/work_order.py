#!/usr/bin/env python3
"""工程表(docs/tasks.yaml)から、作業1件の作業票を標準出力に出す。

使い方:
  python3 tools/work_order.py <作業のid> [--chapter ch2] [--target <ファイルやコミットなど>]
  python3 tools/work_order.py <作業のid> --make-views <資料のディレクトリ> [--chapter ch2] [--views-dir <置き場>]
  python3 tools/work_order.py --list      作業の一覧を、順序つきで出す

作業票は、子セッションを起こすときの最初のメッセージにする。
設計セッションとPMは、自分が次に行う作業の確認に使う。

担当によって、出すものが違う。
  LLMの担当   1行目に「/スキルの名前」。続けて、作業、対象、入力、読まないもの、成果物、報告の書式。
              手順の文面は写さない。手順は、スキル(tools/build_skills.py が作る)が持つ。
  機械         実行するコマンド。工程表の command が null の作業は、道具がないと出す。
  ユーザー     ユーザーに示すものと、答えてもらうこと(判定者がユーザーの検査)。

--target は、対象を何回でも渡せる。機械の作業では、コマンドの「<資料のディレクトリ>」を、最初の対象に置き換える。

--make-views は、入力を限る作業(restricted)の写しを作る。決まりは docs/organization.md の「限った入力の写し」にある。
  項目まで絞った入力(「ファイル#項目」「ファイル#-項目」)ごとに、渡してよい部分だけの写しを作る。項目のない入力は、まるごと複製する。
  作業票の入力に、写しのパスを書く。写しを作れない入力は、作業票に「写しを作れない」と理由を出す。
  置き場は <リポジトリの根>/restricted/<作業のid>/。--chapter があれば restricted/<作業のid>-<章のID>/。
  写しは views/ に置く。前に作ったものは消して作り直す。
  子セッションが行う作業では、「起こす側の手順」を標準エラー出力に出す。作業票には混ぜない。中身は、写しをコミットして
  プッシュする命令、子セッションを起こすときに取得するフォルダの一覧、終わった後に結果を取り込む命令である。
  取得するフォルダの一覧は、Claude Code の子セッションに向けたものである(docs/environments/claude-code.md)。
  この道具は、Git を実行しない。リポジトリの根は、資料のディレクトリから上にたどって、.git のある場所とする。
  --views-dir は、置き場を <置き場>/<作業のid>/ に変える。起こす側の手順に、リポジトリの置き場へ写す命令が加わる。
  設計セッションとPMが自分で行う作業は、起こす側の手順を出さない。項目まで絞った入力の写しだけを作る。
"""
import argparse
import os
import re
import shutil
import sys

import yaml

import build_skills
from build_skills import (by_child, child_notice, grouped_inputs, handoff_dir, has_view, input_lines, input_text,
                          output_lines, places, results_dir, results_notice, view_notice, view_path)
from tasks_table import ROLES, as_list, stage_text

PLACEHOLDER = "<資料のディレクトリ>"

FACT_REF = re.compile(r"\{([FA]\d+)(?::(\w+))?\}")
SLIDE_REF = re.compile(r"\{([A-Za-z][\w]*-s\d+)\}")
MD_HEADING = re.compile(r"^(#{1,6}) (.+?)\s*$")
SLIDE_BODY_DROPPED = ("type", "highlight", "asset", "crop", "scenario")   # スライドの文に含めない、中身の項目


class Unmakeable(Exception):
    """写しを作れない。理由を持つ。"""


def read_yaml(path):
    if not os.path.isfile(path):
        raise Unmakeable(f"元のファイル `{os.path.basename(path)}` がない")
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError:
        raise Unmakeable(f"`{os.path.basename(path)}` を YAML として読めない")


def write_file(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def dump(data):
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=1000)


def of_chapter(stem, chapter):
    """章ごとのファイルが、対象の章のものか。節ごとのファイル(ch2-1 など)も当たる。"""
    return not chapter or stem == chapter or stem.startswith(chapter + "-")


def split_items(items):
    """項目の一覧を、(抜き出す項目, 除く項目)に分ける。"""
    drops = [i[1:] for i in items if i.startswith("-")]
    picks = [i for i in items if not i.startswith("-")]
    if picks and drops:
        raise Unmakeable("項目だけを渡す書き方と、項目を除く書き方が混ざっている")
    return picks, drops


def filter_yaml(data, picks, drops, chapter, found):
    """YAMLの中身から、項目を抜き出す、または除く。見つけた項目の名前を found に足す。"""
    def one(entry, keep_first):
        if not isinstance(entry, dict):
            return entry
        found.update(k for k in entry if k in picks or k in drops)
        if drops:
            return {k: v for k, v in entry.items() if k not in drops}
        return {k: v for n, (k, v) in enumerate(entry.items()) if k in picks or (keep_first and n == 0)}
    if isinstance(data, list):
        rows = [r for r in data if not (chapter and isinstance(r, dict) and "chapter" in r and r["chapter"] != chapter)]
        return [one(r, True) for r in rows]
    if isinstance(data, dict):
        return one(data, False)
    raise Unmakeable("中身が、項目を持つ形でない")


def filter_markdown(text, picks, drops, found):
    """Markdownから、見出しの節を抜き出す、または除く。節は、同じ深さか浅い次の見出しまでとする。"""
    lines, fenced, heads = text.split("\n"), False, []
    for number, line in enumerate(lines):
        if line.startswith("```"):
            fenced = not fenced
        m = None if fenced else MD_HEADING.match(line)
        if m:
            heads.append((number, len(m.group(1)), m.group(2)))
    chosen = set()
    for k, (number, level, title) in enumerate(heads):
        if title in picks or title in drops:
            found.add(title)
            end = next((n for n, lv, _ in heads[k + 1:] if lv <= level), len(lines))
            chosen.update(range(number, end))
    kept = [line for n, line in enumerate(lines) if (n in chosen) == bool(picks)]
    return "\n".join(kept).strip("\n") + "\n"


def view_by_items(deck, name, items, dest, chapter):
    """項目の指定から、写しを作る。作ったものについての覚え書きを返す。"""
    picks, drops = split_items(items)
    source = os.path.join(deck, name)
    if os.path.isdir(source):
        files = [f for f in sorted(os.listdir(source)) if f.endswith((".yaml", ".yml", ".md"))
                 and of_chapter(os.path.splitext(f)[0], chapter)]
        pairs = [(os.path.join(source, f), os.path.join(dest, f)) for f in files]
    elif os.path.isfile(source):
        pairs = [(source, dest)]
    else:
        raise Unmakeable(f"元の `{name}` がない")
    found, made = set(), []
    for src_path, out_path in pairs:
        if src_path.endswith((".yaml", ".yml")):
            made.append((out_path, dump(filter_yaml(read_yaml(src_path), picks, drops, chapter, found))))
        elif src_path.endswith(".md"):
            with open(src_path, encoding="utf-8") as f:
                made.append((out_path, filter_markdown(f.read(), picks, drops, found)))
        else:
            raise Unmakeable("この種類のファイルからは、項目を抜き出せない")
    missing = [i for i in picks + drops if i not in found]
    if not made or (drops and missing) or (picks and not found):
        names = "".join(f"「{i}」" for i in missing or picks + drops)
        raise Unmakeable(f"項目{names}が元にない。項目の名前か、置き場が合わない")
    for out_path, text in made:
        write_file(out_path, text)
    return "元にない項目: " + "".join(f"「{i}」" for i in missing) if missing else ""


def fmt_fact(fact, field):
    """事実への参照を、台帳の値にする。tools/render.py と同じ書き方。"""
    if field in ("unit", "metric"):
        return str(fact.get(field) or "")
    value = fact.get("value")
    if value is None:
        raise Unmakeable(f"事実 {fact.get('id')} に value がない")
    if isinstance(value, int) or (isinstance(value, float) and value.is_integer() and abs(value) >= 1):
        number = f"{int(value):,}"
    else:
        number = f"{value:g}" if isinstance(value, float) else str(value)
    unit = str(fact.get("unit") or "")
    if field == "value":
        return number
    return number + ((" " + unit) if re.match(r"[A-Za-z]", unit) else unit)


def slide_files(deck, chapter):
    folder = os.path.join(deck, "07-slides")
    if not os.path.isdir(folder):
        raise Unmakeable("元の `07-slides/` がない")
    files = sorted(f for f in os.listdir(folder) if f.endswith((".yaml", ".yml")))
    every = {f: [s for s in (read_yaml(os.path.join(folder, f)) or []) if isinstance(s, dict)] for f in files}
    mine = {f: slides for f, slides in every.items() if of_chapter(os.path.splitext(f)[0], chapter)}
    if not mine:
        raise Unmakeable("対象の章のスライド仕様がない")
    return every, mine


def view_slide_text(deck, name, dest, chapter):
    """スライドの文(docs/stages/07-slide-spec.md の「スライドの文」)。"""
    every, mine = slide_files(deck, chapter)
    if not any("title" in s for slides in mine.values() for s in slides):
        raise Unmakeable("項目「title」が元にない。項目の名前が合わない")
    facts = {f.get("id"): f for f in read_yaml(os.path.join(deck, "01-sources.yaml")) or [] if isinstance(f, dict)}
    titles = {s.get("id"): s.get("title") for slides in every.values() for s in slides}

    def fact(m):
        if m.group(1) not in facts or m.group(2) not in (None, "value", "unit", "metric"):
            raise Unmakeable(f"参照 {m.group(0)} を置き換えられない")
        return fmt_fact(facts[m.group(1)], m.group(2))

    def slide(m):
        if not titles.get(m.group(1)):
            raise Unmakeable(f"参照 {m.group(0)} を置き換えられない")
        return str(titles[m.group(1)])

    def shown(value):
        if isinstance(value, str):
            return SLIDE_REF.sub(slide, FACT_REF.sub(fact, value))
        if isinstance(value, list):
            return [shown(v) for v in value]
        if isinstance(value, dict):
            return {k: shown(v) for k, v in value.items()}
        return value

    for f, slides in mine.items():
        out = []
        for s in slides:
            entry = {"id": s.get("id")}
            entry.update({k: shown(s[k]) for k in ("title", "point", "text") if s.get(k) is not None})
            if isinstance(s.get("body"), dict):
                entry["body"] = shown({k: v for k, v in s["body"].items() if k not in SLIDE_BODY_DROPPED})
            out.append(entry)
        write_file(os.path.join(dest, f), dump(out))
    return ""


def view_used_facts(deck, name, dest, chapter):
    """対象のスライド仕様の sources に挙がる事実。"""
    _, mine = slide_files(deck, chapter)
    used = {i for slides in mine.values() for s in slides for i in (s.get("sources") or [])}
    if not used:
        raise Unmakeable("スライド仕様に `sources` がない")
    facts = read_yaml(os.path.join(deck, name)) or []
    write_file(dest, dump([f for f in facts if isinstance(f, dict) and f.get("id") in used]))
    return ""


NAMED_VIEWS = {"スライドの文": ("07-slides/", view_slide_text), "そのスライドが使う事実": ("01-sources.yaml", view_used_facts)}


def view_whole(deck, name, dest):
    """項目のない入力を、まるごと複製する。"""
    source = os.path.join(deck, name)
    if os.path.isdir(source):
        shutil.copytree(source, dest)
    elif os.path.isfile(source):
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copyfile(source, dest)
    else:
        raise Unmakeable(f"元の `{name}` がない")
    return ""


def make_views(task, deck, folder, chapter):
    """作業1件の写しを folder に作る。入力ごとの (ファイル名, 項目, 写しのパス, 作れない理由か None, 覚え書き) を返す。
    写しにしない入力は、写しのパスも理由も None にする。"""
    if os.path.isdir(folder):
        shutil.rmtree(folder)
    results = []
    for name, items in grouped_inputs(task):
        if not has_view(task, name, items) and not (items and name.startswith("「")):
            results.append((name, items, None, None, ""))
            continue
        dest = os.path.join(folder, name.rstrip("/"))
        try:
            if name.startswith("「"):
                raise Unmakeable("元のファイル名が決まっていない")
            if not items:
                memo = view_whole(deck, name, dest)
            elif len(items) == 1 and items[0] in NAMED_VIEWS:
                source, maker = NAMED_VIEWS[items[0]]
                if source != name:
                    raise Unmakeable(f"「{items[0]}」は `{source}` から作る")
                memo = maker(deck, name, dest, chapter)
            else:
                memo = view_by_items(deck, name, items, dest, chapter)
            results.append((name, items, dest + ("/" if name.endswith("/") else ""), None, memo))
        except Unmakeable as error:
            if os.path.isdir(dest):
                shutil.rmtree(dest)
            elif os.path.isfile(dest):
                os.remove(dest)
            results.append((name, items, None, str(error), ""))
    return results


def view_lines(task, args):
    """入力を限る作業の「入力」。写しを作る指定があれば作り、写しのパスを書く。"""
    if not args.make_views:
        out = input_lines(task, args.chapter)
        if view_notice(task):
            out += ["写しは、まだ作っていない。`--make-views <資料のディレクトリ>` を付けて作業票を出すと、作られる。"]
        return out
    out = []
    for name, items, path, reason, memo in make_views(task, args.make_views, os.path.join(handoff(task, args), "views"), args.chapter):
        if reason:
            out.append(f"- 写しを作れない: `{name}` {build_skills.item_text(items)}。理由: {reason}。元のファイルを代わりに渡さない。")
        elif not path:
            out.append("- " + input_text(task, name, items, args.chapter))
        else:
            out.append(f"- `{view_path(task, name, args.chapter)}`(写し。`{name}` {build_skills.item_text(items)})" + (f"。{memo}" if memo else ""))
    return out


def repo_root(deck):
    """資料のディレクトリから上にたどって、.git のある場所を返す。なければ None。"""
    path = os.path.abspath(deck)
    while True:
        if os.path.exists(os.path.join(path, ".git")):
            return path
        parent = os.path.dirname(path)
        if parent == path:
            return None
        path = parent


def handoff(task, args):
    """この作業の写しを書き出す場所。"""
    name = os.path.basename(handoff_dir(task, args.chapter))
    if args.views_dir:
        return os.path.join(args.views_dir, name)
    return os.path.join(repo_root(args.make_views) or os.path.abspath(args.make_views), build_skills.HANDOFF_DIR, name)


def launch_lines(task, args):
    """起こす側の手順。写しを置く命令、取得するフォルダの一覧、結果を取り込む命令の並び。この道具は実行しない。"""
    root = repo_root(args.make_views)
    if root is None:
        return ["起こす側の手順を出せない: 資料のディレクトリが、Git のリポジトリの中にない。"]
    deck_rel = os.path.relpath(os.path.abspath(args.make_views), root).replace(os.sep, "/")
    if deck_rel == "." or deck_rel.startswith(".."):
        return ["起こす側の手順を出せない: 資料のディレクトリが、リポジトリの根である。根の下のディレクトリにする。"]
    tid = task["id"] + (f"({args.chapter})" if args.chapter else "")
    here, results = handoff_dir(task, args.chapter), results_dir(task, args.chapter)
    current = '"$(git branch --show-current)"'
    before = []
    if args.views_dir:
        before += [f"mkdir -p {here} && rm -rf {here}/views && cp -R {handoff(task, args)}/views {here}/views"]
    before += [f"git rm -r -q --ignore-unmatch {results} && rm -rf {results}",
               f"git add -f -A {here}",
               f"git commit -m '{tid}: 写しを置く'",
               "git push origin HEAD"]
    after = [f"git pull --no-rebase origin {current}",
             f"cp -R {results}/. {deck_rel}/",
             f"git add {deck_rel}",
             f"git commit -m '{tid}: 結果を取り込む'",
             "git push origin HEAD"]
    out = [f"起こす側の手順(作業 `{tid}`)",
           "決まりは docs/organization.md の「限った入力の写し」、取得するフォルダの指定は docs/environments/claude-code.md にある。",
           "命令は、リポジトリの根で、作業のブランチのまま実行する。ブランチを作らない。この道具は実行していない。",
           "", "子セッションを起こす前(前の回の結果を消し、写しをコミットして、プッシュする):"]
    out += [f"  {line}" for line in before]
    out += ["", "子セッションを起こす。作業票を最初のメッセージにする。",
            "  版の指定: 作業のブランチの名前",
            "  取得するフォルダ:",
            f"    {here}",
            f"    .claude/skills/{task['skill']}",
            "", "子セッションが終わった後(結果を、資料のディレクトリに取り込む。写しは取り込まない):"]
    out += [f"  {line}" for line in after]
    return out


def header(task):
    return f"作業: `{task['id']}` {task['name']}(工程{stage_text(task['stage'])}、{ROLES[task['role']]})"


def target_lines(args):
    out = [f"- 章: {args.chapter}"] if args.chapter else []
    out += [f"- {t}" for t in args.target]
    return ["対象:"] + (out or ["- 指定がない。"])


def note_lines(task):
    return ["", "条件と覚え書き:"] + [f"- {n}" for n in task["notes"]] if task.get("notes") else []


def next_lines(src, task):
    if not task["next"]:
        return ["", "次の作業: ない。ここで終わる。"]
    out = ["", "次の作業:"]
    for tid in task["next"]:
        out.append(f"- `{tid}` {src.plan.by_id[tid]['name']}({ROLES[src.plan.by_id[tid]['role']]})")
    return out


def unread_lines(src, task, args):
    """読まないもの。制限の定めの文面は、作業のファイルにある。"""
    if not task.get("restricted"):
        return ["この作業だけの制限はない。スキルの「守ること」に従う。"]
    return (["入力に挙げたもの以外を読まない。作業のファイルと、スキルの「守ること」は読む。正本の文書(`docs/`)は開かない。"]
            + view_notice(task, args.chapter) + child_notice(task) + ["この作業では、「守ること」の表より、入力の制限が優先する。"])


def for_session(src, task, args):
    """LLMの担当の作業票。"""
    out = [f"/{task['skill']}", "", header(task), f"手順は、スキル `{task['skill']}` の `tasks/{task['id']}.md` にある。", ""]
    out += target_lines(args) + note_lines(task)
    out += ["", "入力:"] + (view_lines(task, args) if task.get("restricted") else input_lines(task))
    out += ["", "読まないもの:"] + unread_lines(src, task, args)
    out += ["", "成果物:"] + output_lines(src.plan, task, lambda ref: f"作業のファイルに写した「{ref.partition('#')[2]}」")
    out += results_notice(task, args.chapter)
    report = src.plan.roles[task["role"]].get("report", [])
    if report:
        out += ["", "報告の書式: 作業のファイルの「報告の書式」による。"]
    elif task["role"] not in build_skills.PER_STAGE:
        out += ["", "報告の書式: 文書に定めがない。"]
    return out + next_lines(src, task)


def for_machine(src, task, args):
    """機械の作業票。"""
    out = [header(task), ""]
    command = task.get("command")
    if command is None:
        out += ["コマンド: ない。この作業の道具は、まだ作っていない。"]
    else:
        if args.target:
            command = command.replace(PLACEHOLDER, args.target[0])
        out += ["コマンド:", f"  {command}"]
        if PLACEHOLDER in command:
            out += [f"「{PLACEHOLDER}」は、資料の成果物を置いたディレクトリに置き換える。"]
    out += [""] + target_lines(args) + note_lines(task)
    out += ["", "入力:"] + input_lines(task)
    out += ["", "成果物:"] + output_lines(src.plan, task)
    if task["checks"]:
        out += ["", "判定する検査: " + "、".join(f"`{c}`" for c in task["checks"])]
    return out + next_lines(src, task)


def for_user(src, task, args):
    """ユーザーの作業で、ユーザーに示すものと、答えてもらうことの一覧。"""
    out = [header(task), ""] + target_lines(args) + note_lines(task)
    out += ["", "ユーザーに示すもの:"] + input_lines(task)
    asked = [src.ledger[c] for c in task["checks"] if "user" in as_list(src.ledger[c]["judge"])]
    out += ["", "ユーザーに答えてもらうこと:"]
    out += [f"- `{e['id']}` {e['check']}" for e in asked] or ["- 工程表に、ユーザーが判定する検査がない。手順の定めによる。"]
    if task["sections"]:
        out += ["", "手順の定め:"] + places(task["sections"])
    return out + next_lines(src, task)


def listing(src):
    out = []
    for number, t in enumerate(src.plan.tasks, 1):
        skill = t["skill"] or "-"
        out.append(f"{number:>3}  工程{stage_text(t['stage']):<4} {t['id']:<32} {ROLES[t['role']]}  {skill}  {t['name']}")
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(description="工程表から、作業1件の作業票を出す")
    parser.add_argument("task", nargs="?", help="作業の id")
    parser.add_argument("--chapter", help="対象の章。ch2 など")
    parser.add_argument("--target", action="append", default=[], help="対象のファイル、コミットなど。何回でも書ける")
    parser.add_argument("--list", action="store_true", help="作業の一覧を出す")
    parser.add_argument("--make-views", metavar="資料のディレクトリ", help="入力を限る作業の写しを作り、入力に写しのパスを書く")
    parser.add_argument("--views-dir", metavar="置き場", help="写しを書き出すディレクトリ。省くと、リポジトリの根の restricted")
    parser.add_argument("--root", default=os.path.join(here, ".."), help="リポジトリの根")
    args = parser.parse_args()

    src = build_skills.Source(args.root)
    if src.errors:
        print("正本に誤りがある:", *src.errors, sep="\n  ", file=sys.stderr)
        return 1
    if args.list:
        print("\n".join(listing(src)))
        return 0
    task = src.plan.by_id.get(args.task)
    if task is None:
        print(f"作業 {args.task} が工程表にない。--list で一覧を出せる", file=sys.stderr)
        return 1
    if args.make_views and not task.get("restricted"):
        print(f"作業 {args.task} は、入力を限る作業でない。写しは作らない", file=sys.stderr)
    make = {"machine": for_machine, "user": for_user}.get(task["role"], for_session)
    print("\n".join(make(src, task, args)))
    if args.make_views and by_child(task):
        print("\n".join([""] + launch_lines(task, args)), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
