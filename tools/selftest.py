#!/usr/bin/env python3
"""道具の自己確認。見本(tools/fixtures/mini)と、見本を壊す差分(tools/fixtures/breaks.yaml)で確かめる。

使い方:
  python3 tools/selftest.py                        全てを確かめる
  python3 tools/selftest.py --break K04-03 <出力先>  検査1件を不合格にする、壊した版を作る
  python3 tools/selftest.py --list                 壊し方の一覧を出す

確かめること:
  1. 見本が、工程0から7の実装済みの検査の全てに通る。警告も、書式の誤りもない。記録の書式も通る。
  2. 検査ごとに、壊した版が、その検査のIDで不合格(警告の検査は警告)になる。
  3. 書式と参照の確かめ、記録の書式の確かめが、壊した版で誤りを出す。
  4. 実装した検査と、未実装の理由の表が、台帳と合う。壊した版がない検査を一覧で出す。
  5. 状態の記録の命令(tools/status.py)が、決まりの通りに書き、拒む。
終了コード: 確かめに落ちたものがあれば1。
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

import check as C

HERE = Path(__file__).resolve().parent
MINI = HERE / "fixtures" / "mini"
BREAKS = HERE / "fixtures" / "breaks.yaml"


def tool(name, *args):
    p = subprocess.run([sys.executable, str(HERE / name), *map(str, args)], capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def check(deck, *args):
    code, out, err = tool("check.py", deck, "--json", *args)
    try:
        return code, json.loads(out)
    except ValueError:
        raise SystemExit(f"check.py の出力を読めない: {args}\n{out}\n{err}")


def apply_edits(deck, edits):
    for e in edits:
        path = Path(deck) / e["file"]
        if e.get("delete"):
            path.unlink()
        elif "write" in e:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(e["write"], encoding="utf-8")
        else:
            text = path.read_text(encoding="utf-8")
            if text.count(e["old"]) != 1:
                raise SystemExit(f"壊し方が見本に合わない。{e['file']} に、次の文面がちょうど1か所ない:\n{e['old']}")
            path.write_text(text.replace(e["old"], e["new"]), encoding="utf-8")


def broken_copy(edits, dest=None):
    dest = Path(dest) if dest else Path(tempfile.mkdtemp(prefix="selftest-")) / "deck"
    shutil.copytree(MINI, dest)
    apply_edits(dest, edits)
    return dest


def load_breaks():
    return yaml.safe_load(BREAKS.read_text(encoding="utf-8"))


class Tally:
    def __init__(self):
        self.ok, self.ng = 0, []

    def expect(self, cond, name, detail=""):
        if cond:
            self.ok += 1
        else:
            self.ng.append(name)
            print(f"× {name}" + (f": {detail}" if detail else ""))


def test_fixture(t):
    for stage in range(0, 8):
        code, out = check(MINI, "--stage", stage)
        bad = sorted({r["check"] for r in out["results"] if r["verdict"] != "pass"})
        t.expect(code == 0 and not bad and not out["format_errors"], f"見本が工程{stage}の検査に通る",
                 f"終了コード {code}、通らない検査 {bad}、書式の誤り {out['format_errors']}")
    code, out, _ = tool("check.py", "--records", MINI)
    t.expect(code == 0, "見本の検査の記録と実行の記録が、書式の確かめに通る", out.strip())


def test_cases(t, breaks):
    for case in breaks["cases"]:
        cid = case["check"]
        deck = broken_copy(case["edits"])
        args = ["--id", cid] + (["--stage", case["stage"]] if "stage" in case else [])
        code, out = check(deck, *args)
        rows = [r for r in out["results"] if r["check"] == cid and r["verdict"] == "fail"
                and ("item" not in case or r["item"] == case["item"])]
        want = "warning" if C.is_warning(cid) else "fail"
        ok = bool(rows) and all(r["level"] == want for r in rows) and (want == "warning" or code == 1)
        t.expect(ok, f"{cid} が壊した版で{'警告' if want == 'warning' else '不合格'}になる({case['how']})",
                 f"終了コード {code}、行 {[(r['item'], r['level']) for r in out['results'] if r['check'] == cid][:5]}")
        shutil.rmtree(deck.parent)


def test_format(t, breaks):
    for case in breaks["format"]:
        deck = broken_copy(case["edits"])
        code, out = check(deck, "--stage", case["stage"])
        hit = [e for e in out["format_errors"] if case["expect"] in e["error"]]
        t.expect(code == 1 and bool(hit), f"書式の確かめが誤りを出す({case['name']})", f"{out['format_errors'][:3]}")
        shutil.rmtree(deck.parent)
    for case in breaks["records"]:
        deck = broken_copy(case["edits"])
        code, out, _ = tool("check.py", "--records", deck)
        t.expect(code == 1 and case["expect"] in out, f"記録の書式の確かめが誤りを出す({case['name']})", out.strip()[:200])
        shutil.rmtree(deck.parent)


def test_tables(t, breaks):
    table, orphan = C.coverage()
    t.expect(not orphan, "実装した検査と未実装の理由の表が、台帳と合う", f"{orphan}")
    covered = {c["check"] for c in breaks["cases"]}
    unknown = sorted(covered - set(C.CHECKS))
    t.expect(not unknown, "壊し方が、実装した検査だけを指す", f"{unknown}")
    return [c for c in C.CHECKS if c not in covered]


def test_status(t):
    deck = broken_copy([])
    for path in (deck / "checks").glob("*"):
        path.unlink()
    for stage in range(0, 8):
        code, out, err = tool("check.py", deck, "--stage", stage, "--write")
        t.expect(code == 0, f"工程{stage}の検査の記録を書く", (out + err)[-300:])
    code, out, _ = tool("check.py", "--records", deck)
    t.expect(code == 0, "道具が書いた検査の記録が、書式の確かめに通る", out.strip()[-300:])
    status = yaml.safe_load((deck / "status.yaml").read_text(encoding="utf-8"))
    states = {n: e["state"] for n, e in status["artifacts"].items()}
    t.expect(states and all(s == "checked" for s in states.values()), "検査に通った成果物が checked になる", f"{states}")
    t.expect(set(states) >= {"00-brief.md", "02-claims.yaml", "04-storyline.yaml", "07-slides/ch1.yaml"},
             "状態の記録に、検査した成果物が載る", f"{sorted(states)}")
    code, out, _ = tool("status.py", "record-approval", deck, "02-claims.yaml", "--by", "user", "--on", "2026-11-24")
    entry = yaml.safe_load((deck / "status.yaml").read_text(encoding="utf-8"))["artifacts"]["02-claims.yaml"]
    t.expect(code == 0 and entry["state"] == "approved" and entry["approved_by"] == "user"
             and str(entry["approved_on"]) == "2026-11-24" and "commit" in entry, "承認を記録する", f"{entry}")
    code, _, _ = tool("status.py", "record-approval", deck, "99-nothing.yaml", "--by", "user")
    t.expect(code == 1, "状態の記録にない成果物の承認を拒む")
    old = deck.parent / "old"
    shutil.copytree(deck, old)
    apply_edits(deck, [{"file": "01-sources.yaml", "old": "value: 62\n", "new": "value: 63\n"}])
    code, out, _ = tool("status.py", "invalidate", deck, "--old", old)
    status = yaml.safe_load((deck / "status.yaml").read_text(encoding="utf-8"))
    states = {n: e["state"] for n, e in status["artifacts"].items()}
    want = {"01-sources.yaml", "02-answers.yaml", "02-claims.yaml", "05-proof.yaml", "07-slides/ch1.yaml"}
    t.expect(all(states.get(n) == "invalid" for n in want), "事実の値が変わると、それを根拠にする成果物が invalid になる", f"{states}")
    t.expect(states.get("03-chapters.yaml") == "checked", "変わった事実を使わない成果物は、そのままである", f"{states.get('03-chapters.yaml')}")
    t.expect(status["slides"].get("ch1-s4", {}).get("state") == "invalid" and "ch2-s1" not in status["slides"],
             "事実を使うスライドだけが invalid になる", f"{status['slides']}")
    code, out = check(deck, "--id", "K08-03")
    t.expect(code == 1, "無効の成果物があると、K08-03 が不合格になる")
    code, _, _ = tool("status.py", "record-approval", deck, "02-answers.yaml", "--by", "user")
    t.expect(code == 1, "checked でない成果物の承認を拒む")
    code, out, _ = tool("status.py", "record-check", deck)
    status = yaml.safe_load((deck / "status.yaml").read_text(encoding="utf-8"))
    t.expect(code == 1 and status["artifacts"]["02-answers.yaml"]["state"] == "invalid",
             "無効になる前の検査の記録では、invalid を解かない", out.strip()[-300:])
    code, out, err = tool("check.py", deck, "--stage", 1, "--write")
    status = yaml.safe_load((deck / "status.yaml").read_text(encoding="utf-8"))
    entry = status["artifacts"]["01-sources.yaml"]
    t.expect(code == 1 and entry["state"] == "draft" and entry["rounds"] == 2 and entry["checks"] == ["checks/check-sources-machine--all--2.yaml"],
             "不合格のある成果物は checked にせず、draft にする", f"{entry}")
    code, out, _ = tool("status.py", "show", deck)
    t.expect(code == 0 and "01-sources.yaml | draft" in out, "状態の記録を表で出す")
    shutil.rmtree(deck.parent)


def main(argv=None):
    ap = argparse.ArgumentParser(description="道具の自己確認。")
    ap.add_argument("--break", dest="brk", nargs=2, metavar=("検査のID", "出力先"), help="壊した版を作る")
    ap.add_argument("--list", action="store_true", help="壊し方の一覧を出す")
    args = ap.parse_args(argv)
    breaks = load_breaks()
    if args.list:
        for c in breaks["cases"]:
            print(f"{c['check']} {c['how']}")
        return 0
    if args.brk:
        cid, dest = args.brk
        cases = [c for c in breaks["cases"] if c["check"] == cid]
        if not cases:
            print(f"{cid} の壊し方がない。", file=sys.stderr)
            return 2
        if Path(dest).exists():
            print(f"{dest} が既にある。", file=sys.stderr)
            return 2
        broken_copy(cases[0]["edits"], dest)
        print(f"{dest} に、{cid} が不合格になる版を作った({cases[0]['how']})")
        return 0

    t = Tally()
    test_fixture(t)
    test_cases(t, breaks)
    test_format(t, breaks)
    uncovered = test_tables(t, breaks)
    test_status(t)
    print(f"確かめ {t.ok + len(t.ng)}件のうち、通ったもの {t.ok}件、落ちたもの {len(t.ng)}件")
    print(f"実装した検査 {len(C.CHECKS)}件のうち、壊した版があるもの {len(C.CHECKS) - len(uncovered)}件")
    print("壊した版がない検査: " + ("、".join(uncovered) if uncovered else "なし"))
    return 1 if t.ng else 0


if __name__ == "__main__":
    sys.exit(main())
