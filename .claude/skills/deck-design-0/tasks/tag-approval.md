<!-- 道具 tools/build_skills.py が作った。直接は直さない -->

# `tag-approval` 承認した成果物にタグを付ける

道具 `tools/build_skills.py` が作ったファイルである。直接は直さない。正本は、工程表 `docs/tasks.yaml`、検査の台帳 `docs/checks.yaml`、`docs/` の文書である。直すときは、正本を直して、道具を実行する。

担当は設計セッション、工程は0〜6である。

## 条件と覚え書き

- ユーザーが成果物を承認するたびに行う
- outputs: 承認のタグ(rework.md#承認のタグ)
- next: 承認した工程の、次の作業に進む

## 入力

- `00-brief.md`
- `01-plan.yaml`
- `01-model.yaml`
- `02-claims.yaml`
- `03-chapters.yaml`
- `04-storyline.yaml`
- `05-proof.yaml`
- `06-samples/`
- `terms.yaml`

## 読まないもの

この作業だけの制限はない。「守ること」に従う。

## 手順

### 承認のタグ(`docs/rework.md`)

スキル `deck-design-0` の「守ること」に写してある。

## 成果物

工程表に、成果物のファイルの定めがない。

## 検査

工程表に、この作業の検査がない。

## 参照

次の箇所は、文面を写していない。必要なときに読む。パスは、リポジトリの根からである。

- `docs/git.md` の「管理の方法」

## 次の作業

分かれる場合と、順序が決まっていない場合がある。

- `write-hypotheses` 仮説の一覧を書く(設計セッション、スキル `deck-design-1`)
- `request-research` 調査依頼を出す(設計セッション、スキル `deck-design-1`)
- `answer-questions` 問いごとの答えを書く(設計セッション、スキル `deck-design-2`)
- `design-chapters` 章構成を書く(設計セッション、スキル `deck-design-3`)
- `write-storyline` スライドの題と要点を書く(設計セッション、スキル `deck-design-4`)
- `design-proof` スライドごとの立証の設計を書く(設計セッション、スキル `deck-design-5`)
- `map-patterns` 主張の種類ごとに型を選ぶ(設計セッション、スキル `deck-design-6`)
- `freeze-terms` 語彙表を凍結し、見本を手本として渡す(設計セッション、スキル `deck-design-6`)
