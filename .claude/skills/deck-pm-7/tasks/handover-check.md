<!-- 道具 tools/build_skills.py が作った。直接は直さない -->

# `handover-check` 引き継ぎの検査で説明を書き、合否を判定する

道具 `tools/build_skills.py` が作ったファイルである。直接は直さない。正本は、工程表 `docs/tasks.yaml`、検査の台帳 `docs/checks.yaml`、`docs/` の文書である。直すときは、正本を直して、道具を実行する。

担当はPM、工程は7である。

## 条件と覚え書き

- 合否は、検査セッションが比べた結果(compare-handover)と、設計セッションの判断(decide-handover-fixes)を受けて判定する

## 入力

- `00-brief.md`
- `01-hypotheses.yaml`
- `01-plan.yaml`
- `01-sources.yaml`
- `01-model.yaml`
- `02-answers.yaml`
- `02-claims.yaml`
- `03-chapters.yaml`
- `04-storyline.yaml`
- `04-chapter-states.yaml`
- `04-scenarios.yaml`
- `05-proof.yaml`
- `06-patterns.yaml`
- `06-samples/`
- `style.yaml`
- `terms.yaml`
- `decisions.md`

## 読まないもの

入力に挙げたもの以外を読まない。このファイルと、スキルの「守ること」は読む。正本の文書(`docs/`)は開かない。要る箇所は、このファイルに写してある。

ファイルをまるごと渡す入力は、次の定めによる。

### 引き継ぎの検査(`docs/organization.md`)

製造の時期に入る前に行う。新しく起こしたPMに成果物だけを読ませ、次を確かめる。

- 資料の結論、章の構成、各章の要点を、自分の言葉で説明できる。
- 設計の判断の記録にある却下した案を、再び提案しない。
- 作業を始めるうえで分からない点がない。

## 手順

この作業では、「守ること」の表より、入力の制限が優先する。

### 引き継ぎの検査(`docs/organization.md`)

このファイルの上に写してある。

### 説明を書く(`docs/organization.md`)

担当: PM。

1. 成果物だけを読む。設計セッションに尋ねない。
2. 資料の結論、章の構成、各章の要点の説明を書く。変えたい点と、分からない点があれば、あわせて書く。`work/answers/handover-check.yaml` に置く。
3. 検査セッションが比べた結果を受けて、合否を判定する。食い違いも、分からない点もなければ、合格とする。残ったものの全てに、直さない理由が設計の判断の記録にある場合も、合格とする。

## 成果物

- `work/answers/handover-check.yaml`

## 検査

### 判定する検査

次の検査を判定する。

- `K07-01` 引き継ぎの検査に通っている(PM)。 定義は、写してある「引き継ぎの検査」にある。

## 参照

工程表に、参照する箇所がない。

## 次の作業

分かれる場合と、順序が決まっていない場合がある。

- `compare-handover` PMの説明を設計の成果物と比べる(検査セッション、スキル `deck-inspect`)
- `make-chapter-brief` 章の作業票を作る(機械)
