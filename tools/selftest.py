#!/usr/bin/env python3
"""check.py の確かめ。見本(fixtures/mini)が合格し、わざと壊した写しが不合格になることを確かめる。

使い方: python tools/selftest.py
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
MINI = HERE / "fixtures" / "mini"


def run(deck, *args):
    p = subprocess.run([sys.executable, str(HERE / "check.py"), str(deck), "--json", *args],
                       capture_output=True, text=True)
    return p.returncode, json.loads(p.stdout)["results"]


def edit(deck, name, old, new):
    path = deck / name
    text = path.read_text(encoding="utf-8")
    assert old in text, f"{name} に {old!r} がない"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


PATTERNS = """\
- {relation: statement, size: any, base: none, pattern: statement}
- {relation: causality, size: any, base: none, pattern: cause-chain}
- {relation: composition, size: within, base: none, pattern: pie-chart}
- {relation: contrast-before-after, size: any, base: none, pattern: before-after}
- {relation: list, size: within, base: none, pattern: plain-list}
"""
MODEL = """\
elements:
  - {id: E-bot, kind: component, name: チャットボット, evidence: [F005]}
  - {id: E-desk, kind: actor, name: 窓口の担当者, evidence: [F009]}
relations:
  - {id: R-bot-desk, kind: send, from: E-bot, to: E-desk, label: 答えられない問い合わせを渡す, evidence: [F005]}
scenarios:
  - {id: S-escalate, name: 担当者への引き継ぎ, steps: [R-bot-desk], evidence: [F005]}
"""


def stage6(deck):
    (deck / "06-patterns.yaml").write_text(PATTERNS, encoding="utf-8")
    (deck / "06-samples").mkdir()
    for name in ("statement", "cause-chain", "pie-chart", "before-after", "plain-list"):
        (deck / "06-samples" / f"{name}.yaml").write_text("{}\n", encoding="utf-8")


# (名前, 壊し方, 不合格になるはずの条件の一部。None は合格を期待する)
CASES = [
    ("見本のまま", lambda d: None, None),
    ("参照先のないID: 立証設計の facts", lambda d: edit(d, "05-proof.yaml", "facts: [F002]", "facts: [F002, F999]"),
     "facts が全て素材台帳にあり"),
    ("参照先のないID: ストーリーラインの from", lambda d: edit(d, "04-storyline.yaml", "from: [Q1.2]", "from: [Q9]"),
     "参照先がある"),
    ("参照先のないID: 章構成の claims", lambda d: edit(d, "03-chapters.yaml", "claims: [C1, C2]", "claims: [C1, C2, C7]"),
     "参照先がある"),
    ("必須の項目の欠落: fact の quote", lambda d: edit(d, "01-sources.yaml", '  quote: "4月から9月の月平均は1,200件"\n', ""),
     "全ての fact に source、locator、quote がある"),
    ("必須の項目の欠落: 章の slides_reason", lambda d: edit(d, "03-chapters.yaml", "    slides_reason: 求める判断を1枚で述べる\n", ""),
     "全ての章に slides_reason がある"),
    ("必須の項目の欠落: ブリーフの項目", lambda d: edit(d, "00-brief.md", "## 扱わない範囲", "## 範囲"),
     "ブリーフに全ての項目があり"),
    ("ブリーフに推定が残る", lambda d: edit(d, "00-brief.md", "## 伝え方\n- 状態: 確定", "## 伝え方\n- 状態: 推定"),
     "推定のまま残る項目がない"),
    ("verified: false の事実を使う", lambda d: edit(d, "01-sources.yaml", "  stance: {H1: contradicts, H2: supports}\n  verified: true",
                                              "  stance: {H1: contradicts, H2: supports}\n  verified: false"),
     "facts が全て素材台帳にあり"),
    ("主張が本論の章にない", lambda d: edit(d, "03-chapters.yaml", "claims: [C1, C2]", "claims: [C1]"),
     "全ての主張が、いずれかの本論の章に割り当てられている"),
    ("章の枚数が配分を超える", lambda d: edit(d, "03-chapters.yaml", "slides: 7", "slides: 6"),
     "章構成の配分以下である"),
    ("壊れたYAML", lambda d: edit(d, "04-storyline.yaml", "- id: ch1-s2", "- id: [ch1-s2"),
     "成果物が読める"),
    ("工程6を足す", stage6, None),
    ("工程6: 型の含意が holds にない",
     lambda d: (stage6(d), edit(d, "06-patterns.yaml", "pattern: cause-chain", "pattern: step-flow"),
                edit(d, "05-proof.yaml", "holds: [causal, ordered]", "holds: [causal]")),
     "型の implies がスライドの holds に含まれる"),
    ("工程6: 対応表に行がない", lambda d: (stage6(d), edit(d, "06-patterns.yaml", "- {relation: list, size: within, base: none, pattern: plain-list}\n", "")),
     "対応表にある"),
    ("仕組みの定義を足す", lambda d: ((d / "01-model.yaml").write_text(MODEL, encoding="utf-8"),
                              edit(d, "05-proof.yaml", "  show: 試行の前と後",
                                   "  real: true\n  view: {scenario: S-escalate}\n  show: 試行の前と後")), None),
    ("仕組みの定義にない要素を選ぶ", lambda d: ((d / "01-model.yaml").write_text(MODEL, encoding="utf-8"),
                                  edit(d, "05-proof.yaml", "  show: 試行の前と後",
                                       "  real: true\n  view: {elements: [E-none]}\n  show: 試行の前と後")),
     "仕組みの定義にある"),
]


def main():
    bad = 0
    for name, mutate, expect in CASES:
        with tempfile.TemporaryDirectory() as tmp:
            deck = Path(tmp) / "deck"
            shutil.copytree(MINI, deck, ignore=shutil.ignore_patterns("build"))
            mutate(deck)
            code, results = run(deck)
        failed = [r for r in results if r["status"] == "不合格"]
        if expect is None:
            ok = code == 0 and not failed
        else:
            ok = code == 1 and any(expect in r["condition"] for r in failed)
        bad += not ok
        print(f"[{'OK' if ok else 'NG'}] {name}: 終了コード {code}、不合格 {len(failed)}件")
        for r in failed:
            for w in r["where"][:2]:
                print(f"       {r['condition'][:28]}… {w}")
    print("確かめの結果: " + ("全て期待の通り" if not bad else f"{bad}件が期待と違う"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
