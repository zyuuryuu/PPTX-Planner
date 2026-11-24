#!/usr/bin/env python3
"""工程表(docs/tasks.yaml)から、作業1件の作業票を標準出力に出す。

使い方:
  python3 tools/work_order.py <作業のid> [--chapter ch2] [--target <ファイルやコミットなど>]
  python3 tools/work_order.py --list      作業の一覧を、順序つきで出す

作業票は、子セッションを起こすときの最初のメッセージにする。
設計セッションとPMは、自分が次に行う作業の確認に使う。

担当によって、出すものが違う。
  LLMの担当   1行目に「/スキルの名前」。続けて、作業、対象、入力、読まないもの、成果物、報告の書式。
              手順の文面は写さない。手順は、スキル(tools/build_skills.py が作る)が持つ。
  機械         実行するコマンド。工程表の command が null の作業は、道具がないと出す。
  ユーザー     ユーザーに示すものと、答えてもらうこと(判定者がユーザーの検査)。

--target は、対象を何回でも渡せる。機械の作業では、コマンドの「<資料のディレクトリ>」を、最初の対象に置き換える。
"""
import argparse
import os
import sys

import build_skills
from build_skills import input_lines, output_lines, place, places, unread_lines
from tasks_table import ROLES, as_list, stage_text

PLACEHOLDER = "<資料のディレクトリ>"
LAUNCH = ("子セッションを起こすときの版の指定には、ブランチの名前を使う。短いコミットIDを使わない。"
          "対象のコミットは、この作業票の「対象」に書く。")


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


def where(src, task):
    """手順のある場所。スキルの置き場からのパス。"""
    path = f"{task['skill']}/tasks/{task['id']}.md"
    if os.path.isfile(os.path.join(src.out_dir, path)):
        return f"スキル `{task['skill']}` の `tasks/{task['id']}.md`"
    return f"スキル `{task['skill']}` の「`{task['id']}` {task['name']}」"


def for_session(src, task, args):
    """LLMの担当の作業票。"""
    out = [f"/{task['skill']}", "", header(task), f"手順は、{where(src, task)} にある。ほかの作業の手順は読まない。", ""]
    out += target_lines(args) + note_lines(task)
    out += ["", "入力:"] + input_lines(task)
    out += ["", "読まないもの:"] + [t for t in unread_lines(src, task) if t]
    out += ["", "成果物:"] + output_lines(task)
    report = src.plan.roles[task["role"]].get("report", [])
    if report:
        out += ["", "報告の書式: 次の定めによる。"] + places(report)
    elif task["role"] not in build_skills.PER_STAGE:
        out += ["", "報告の書式: 文書に定めがない。"]
    if task["role"] not in build_skills.PER_STAGE:
        out += ["", "版の指定: " + LAUNCH]
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
    out += ["", "成果物:"] + output_lines(task)
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
    make = {"machine": for_machine, "user": for_user}.get(task["role"], for_session)
    print("\n".join(make(src, task, args)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
