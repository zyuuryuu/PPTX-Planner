<!-- 道具 tools/build_skills.py が作った。直接は直さない -->

# `hand-over` ユーザーの承認を状態の記録に書いて引き渡す

道具 `tools/build_skills.py` が作ったファイルである。直接は直さない。正本は、工程表 `docs/tasks.yaml`、検査の台帳 `docs/checks.yaml`、`docs/` の文書である。直すときは、正本を直して、道具を実行する。

担当はPM、工程は9である。

## 条件と覚え書き

- 承認を記録する命令の道具は、まだない

## 入力

工程表に、入力のファイルの定めがない。

## 読まないもの

この作業だけの制限はない。「守ること」に従う。

## 手順

番号は、正本の手順の番号のままである。この作業にない番号の手順は、次の作業が行う。

- 「1. 最終のビルドを行い、出力を機械的に検査する」: `build-final`(機械)
- 「2. 検査の報告を作る」: `make-inspection-report`(機械)
- 「3. 抜き取りで確かめる」: `sample-check`(ユーザー)
- 「4. ユーザーが、実際に使う形で通す」: `walk-through`(ユーザー)
- 「5. 実際の環境で確かめる」: `check-real-environment`(ユーザー)
- 「6. ユーザーが承認する」: `approve-final`(ユーザー)
- 「8. 発表の後に、反応を記録する」: `record-reactions`(設計セッション)
- 「9. 集計する」: `tally-metrics`(機械)

### 7. 引き渡す(`docs/stages/09-finish.md`)

担当: PM。

- ユーザーの承認を、状態の記録に書く([不合格と修正の手順](../../../../docs/rework.md)の「承認の記録」)。
- 以後のPowerPointでの手直しは自由とする。作り直すと手直しが消えることを伝える。

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
- `docs/rework.md` の「承認の記録」

## 次の作業

分かれる場合と、順序が決まっていない場合がある。

- `record-reactions` 発表の後の反応を記録する(設計セッション、スキル `deck-design-production`)
- `tally-metrics` 集計の記録を作る(機械)
