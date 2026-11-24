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
  6. 描画の道具(tools/render.py、tools/build.py)が見本を診断なしで描き、描画の結果を読む検査が、壊した版で不合格になる。
終了コード: 確かめに落ちたものがあれば1。
描画の確かめには、Node.js と Playwright の Chromium が要る(tools/patterns-data.md)。見本の検査は、一時の置き場に描いた結果で行う。
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


_BUILD = {}


def render(deck, out=None, *args):
    """全スライドと型の見本を描く。出力先(既定は deck/build)を返す。"""
    out = Path(out) if out else Path(deck) / "build"
    code, text, err = tool("render.py", deck, "--no-png", "--out", out, *args)
    code2, text2, err2 = tool("render.py", deck, "--samples", "--no-png", "--out", out / "samples")
    return out, code, code2, text + err + text2 + err2


def fixture_build():
    """見本を描いた結果の置き場。見本のディレクトリには書かず、一時の置き場に1回だけ描く。"""
    if "dir" not in _BUILD:
        _BUILD["tmp"] = Path(tempfile.mkdtemp(prefix="selftest-build-"))
        _BUILD["dir"], _BUILD["code"], _BUILD["code_samples"], _BUILD["log"] = render(MINI, _BUILD["tmp"] / "build", "--pdf")
    return _BUILD["dir"]


def check(deck, *args):
    if Path(deck) == MINI:
        args = (*args, "--build", fixture_build())
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


def diag(build, sub=None):
    path = (build / sub if sub else build) / "diagnostics.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    return doc, {s["id"]: s for s in doc["slides"]}


def failed(deck, cid, *args):
    code, out = check(deck, "--id", cid, *args)
    return [r for r in out["results"] if r["check"] == cid and r["verdict"] == "fail"]


def test_render(t):
    """描画の道具と、描画の結果を読む検査(K06-06、K06-11、K07-40、K07-41、K08-04)。"""
    build = fixture_build()
    t.expect(_BUILD["code"] == 0 and _BUILD["code_samples"] == 0, "見本を、描画上の診断(エラー)なしで描く", _BUILD["log"][-600:])
    doc, slides = diag(build)
    kinds = {}
    for e in doc["slides"]:
        kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
    want = {"目次": 1, "章扉": 2, "本編": 9, "節のまとめ": 1, "章のまとめ": 2, "付録の扉": 1, "付録": 3, "出典の一覧": 1}
    t.expect(kinds == want, "自動で作るスライドが、正本の決まりの通りに入る", f"{kinds}")
    t.expect(all(len(e["title"]) == 1 for e in doc["slides"]) and all(len(e["point"]) <= 1 for e in doc["slides"]),
             "全てのスライドで、題が1か所、要点が1か所以下である")
    t.expect(slides["ch1-s6"]["point"] == ["応答率は、午前が48%で、午後の74%より低い"] and slides["ch1-s2"]["point"] == [],
             "節の要点を引くスライドに節の要点を描き、要点のないスライドに要点を描かない", f"{slides['ch1-s6']['point']}、{slides['ch1-s2']['point']}")
    text = (build / "deck.html").read_text(encoding="utf-8")
    body = __import__("re").sub(r"<[^>]+>", " ", text.split("<body>", 1)[1])
    t.expect("ch1-s2" not in body and "F016" not in body and "{" not in body and "応答率の数え方」に示す" in body,
             "読み手向けの出力に内部のIDを出さず、参照を題に置き換える")
    t.expect((build / "deck.pdf").is_file() and (build / "deck.pdf").stat().st_size > 10000 and "iframe" not in text,
             "全スライドを、1つの HTML と1つの PDF に出す")
    try:
        from pypdf import PdfReader
        pages = len(PdfReader(str(build / "deck.pdf")).pages)
        t.expect(pages == doc["count"], "PDF のページの数が、スライドの数と合う", f"{pages}ページ、{doc['count']}枚")
    except ImportError:
        pass
    for cid in ("K06-06", "K06-11", "K07-40", "K07-41", "K08-04"):
        t.expect(not failed(MINI, cid), f"{cid} が見本の描画の結果で合格になる")
    for level, n in (("toc", 3), ("skeleton", 20), ("placeholder", 20)):
        out = _BUILD["tmp"] / level
        code, text, err = tool("build.py", MINI, "--level", level, "--no-png", "--out", out)
        d = json.loads((out / "diagnostics.json").read_text(encoding="utf-8")) if (out / "diagnostics.json").is_file() else {}
        t.expect(code == 0 and d.get("count") == n, f"確認用の資料({level})を、診断なしで {n}枚描く", (text + err)[-300:])
    # 描いていない資料と、描いた後に成果物が変わった資料は、不合格にする
    deck = broken_copy([])
    rows = failed(deck, "K07-41")
    t.expect(rows and "描画の結果がない" in rows[0]["reason"], "描画の結果がないと、K07-41 が不合格になる")
    _, c1, c2, log = render(deck)
    t.expect(c1 == 0 and c2 == 0 and not failed(deck, "K07-41") and not failed(deck, "K06-11"), "描いた後は、K07-41 と K06-11 が合格になる", log[-300:])
    apply_edits(deck, [{"file": "07-slides/ch2.yaml", "old": "highlight: after", "new": "highlight: before"}])
    rows = failed(deck, "K07-41")
    t.expect(rows and "古い" in rows[0]["reason"], "描いた後にスライド仕様が変わると、K07-41 が不合格になる")
    # 題が1行に収まらない、要点が2行を超える、強調が2か所以上、を診断に出す
    apply_edits(deck, [
        {"file": "04-storyline.yaml", "old": "title: 年度ごとの応答率\n", "new": "title: 2024年度と2025年度の窓口の代表番号への着信に対する年度ごとの応答率の変化の一覧\n"},
        {"file": "04-storyline.yaml", "old": "point: 応答できなかった社員のかけ直しが、着信をさらに増やしている",
         "new": "point: " + "応答できなかった社員のかけ直しが、着信をさらに増やしている。" * 5},
        {"file": "07-slides/ch1.yaml", "old": "- {label: 応答した着信, value: F001}", "new": "- {label: 応答した着信, value: F001, highlight: true}"},
        {"file": "07-slides/ch1.yaml", "old": "数え方は「{ch1-s2}」に示す", "new": "数え方は ch1-s2 と「{ch9-s9}」に示す"},
    ])
    _, c1, c2, log = render(deck)
    doc, slides = diag(deck / "build")
    kind_of = lambda sid: {x["kind"] for x in slides[sid]["diagnostics"]}
    t.expect(c1 == 1 and "title-lines" in kind_of("ch1-s1"), "題が1行に収まらないと、診断に出る", f"{kind_of('ch1-s1')}")
    t.expect("point-lines" in kind_of("ch1-s3"), "要点が2行を超えると、診断に出る", f"{kind_of('ch1-s3')}")
    t.expect("emphasis" in kind_of("ch1-s4"), "強調が2か所以上あると、診断に出る", f"{kind_of('ch1-s4')}")
    t.expect({"internal-id", "unrendered"} <= kind_of("ch1-s3"), "内部のIDと、先のない参照が、診断に出る", f"{kind_of('ch1-s3')}")
    rows = failed(deck, "K07-41", "--chapter", "ch1")
    t.expect({r["item"] for r in rows} >= {"ch1-s1", "ch1-s3"} and not failed(deck, "K07-41", "--chapter", "ch2"),
             "K07-41 が、診断のある章だけで不合格になる", f"{[(r['item'], r['reason']) for r in rows][:4]}")
    t.expect(bool(failed(deck, "K08-04")) and bool(failed(deck, "K06-11")), "K08-04 と K06-11 が、診断のある資料で不合格になる")
    shutil.rmtree(deck.parent)
    # 描けない型と、スライド仕様のないスライド
    deck = broken_copy([{"file": "06-patterns.yaml", "old": "pattern: bar-chart", "new": "pattern: histogram"},
                        {"file": "07-slides/appendix.yaml", "delete": True}])
    render(deck)
    rows = failed(deck, "K06-06")
    t.expect([r["item"] for r in rows] == ["histogram"], "K06-06 が、描けない型で不合格になる", f"{rows[:2]}")
    rows = failed(deck, "K08-04")
    t.expect({"ap-s1", "ap-s2"} <= {r["item"] for r in rows}, "K08-04 が、スライド仕様のないスライドで不合格になる", f"{[r['item'] for r in rows]}")
    shutil.rmtree(deck.parent)


def test_status(t):
    deck = broken_copy([])
    for path in (deck / "checks").glob("*"):
        path.unlink()
    render(deck)
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
    test_render(t)
    test_status(t)
    if "tmp" in _BUILD:
        shutil.rmtree(_BUILD["tmp"])
    print(f"確かめ {t.ok + len(t.ng)}件のうち、通ったもの {t.ok}件、落ちたもの {len(t.ng)}件")
    print(f"実装した検査 {len(C.CHECKS)}件のうち、壊した版があるもの {len(C.CHECKS) - len(uncovered)}件")
    print("壊した版がない検査: " + ("、".join(uncovered) if uncovered else "なし"))
    return 1 if t.ng else 0


if __name__ == "__main__":
    sys.exit(main())
