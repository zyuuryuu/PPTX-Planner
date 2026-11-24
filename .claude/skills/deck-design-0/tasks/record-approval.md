<!-- 道具 tools/build_skills.py が作った。直接は直さない -->

# `record-approval` ユーザーの承認を状態の記録に書く

道具 `tools/build_skills.py` が作ったファイルである。直接は直さない。正本は、工程表 `docs/tasks.yaml`、検査の台帳 `docs/checks.yaml`、`docs/` の文書である。直すときは、正本を直して、道具を実行する。

担当は設計セッション、工程は0〜6である。

## 条件と覚え書き

- ユーザーが成果物を承認するたびに行う
- 承認を記録する命令の道具は、まだない
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

### 承認の記録(`docs/rework.md`)

スキル `deck-design-0` の「守ること」に写してある。

## 成果物

- `status.yaml`(書式は、このファイルの「状態の記録」に定める)

### 状態の記録(`docs/rework.md`)

書くのは、機械の命令だけである。検査のコマンドが、検査の記録と成果物の差分から書く。承認は、承認を記録する命令が書く。人とセッションは、直接は書かない。状態について事情の説明が要るときは、設計セッションが設計の判断の記録に書く。

```yaml
artifacts:
  01-sources.yaml:
    state: checked           # draft / checked / approved / invalid
    commit: 3f2a9c1
    rounds: 2
    checks: [checks/inspect-sources--all--2.yaml]
  02-claims.yaml:
    state: approved
    commit: 8b1d44e
    approved_by: user
    approved_on: 2026-11-23
slides:
  ch2-s3:
    state: invalid
    reason: F015 の値が変わった
```

| `state` | 意味 |
|---|---|
| `draft` | 作成中。合否にする検査のうち、通っていないものがある |
| `checked` | 検査済み。`commit` の版が、合否にする検査の全てに通った |
| `approved` | 承認済み。`commit` の版を、`approved_by` の者が承認した |
| `invalid` | 無効。合格または承認の後に、前提にした上流の項目か、成果物そのものが変わった |

- `rounds` は、検査した回数である。往復の回数は、これより1つ少ない。`checks` は、最後の回の検査の記録である。
- `approved_by` は、承認した者である。ユーザーは `user`、章を受け入れたPMは `pm` と書く。
- `slides` は、スライドごとの状態である。無効になった理由を `reason` に書く。
- スライドの保留は、スライド仕様の `status` が持つ。状態の記録には写さない。

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
