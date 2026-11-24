---
name: deck-inspect
description: スライド資料の検査セッションが、成果物を検査する手順。作業票の1行目がこの名前のときに使う。
---
<!-- 道具 tools/build_skills.py が作った。直接は直さない -->

# 検査セッション

作業票が指す作業のファイルを1つだけ読む。ほかの作業のファイルを読まない。

道具 `tools/build_skills.py` が作ったファイルである。直接は直さない。正本は、工程表 `docs/tasks.yaml`、検査の台帳 `docs/checks.yaml`、`docs/` の文書である。直すときは、正本を直して、道具を実行する。

## 守ること

### セッションの分離(`docs/organization.md`)

| セッション | 読むもの | してはいけないこと |
|---|---|---|
| 収集 | 調査依頼、外部の資料 | 主張、題、要点を書くこと、仮説の一覧を読むこと |
| 執筆 | 承認済みの上流の成果物 | Web検索や資料の直接の読み込み、台帳にない事実の記述 |
| 検査 | 検査対象の成果物と、その上流の成果物 | 検査対象を自分で直すこと |
| 読み手の役 | ブリーフの読み手の情報と、ビルドした実物 | 設計の成果物を読むこと、スライドを直すこと |

読み手の役のセッションは、工程7の章の受け入れと、工程8の結合テストで、PMが起こす。実行のたびに新しく起こす。

検査は、機械の検査を先に行う。検査セッションは、機械の検査に通ったものを検査する。

分ける理由:

- 執筆中のLLMは、文を完成させるために必要な事実を補ってしまう。事実を台帳のIDでしか参照できなくすれば、補う余地がなくなる。
- 生の資料が執筆の文脈に入らないため、読み込み量が抑えられる。
- 書いた本人による検査は、自分の誤りを見逃しやすい。

分離だけでは、収集セッション自身の捏造は防げない。そのため素材台帳に引用箇所を記録させ、検査セッションが出典と突き合わせる。

### 原則(`docs/rework.md`)

1. 直すのは、その成果物を書いたセッションである。検査した側は直さない。
2. 原因が上流にある場合は、その場で辻褄を合わせない。上流に戻す。
3. 検査の指摘に、異を唱える経路を持つ。検査セッションの指摘には誤検出がある。
4. 検査し直すのは、落ちた条件と、直した箇所に依存する条件に限る。
5. 往復に上限を持つ。超えたら人が決める。
6. 合格も不合格も、記録に残す。記録は、検査した側が書く。

### 検査と記録を守る(`docs/rework.md`)

検査で品質を守る以上、検査そのものと、その記録が書き換えられないことが前提になる。

- 検査のコマンド、辞書、検査の記録、状態の記録、上流の成果物は、執筆のセッションの作業の枝で変更できない。変更が含まれる場合は、受け入れを拒む。
- 受け入れる側は、執筆のセッションの作業の枝にある検査のコマンドを使わない。受け入れ済みの本流にある検査のコマンドと辞書で、自分で実行する。
- ユーザーが承認した成果物は、承認のときにタグを付ける。タグを付ける担当: PM。承認の後に内容が変わった成果物は、検査のコマンドがタグとの差分から機械的に挙げ、承認を取り直すまで、下流の工程の開始を止める。設計セッションが、検査を通すために承認済みの成果物を直すことを、これで拾う。
- 検査を通すための書き換えや、検査の回避が見つかった場合は、PMまたは設計セッションが、変更を取り消し、そのセッションを新しいセッションに替える。事実をIssueに記録する。

## 作業の一覧

| 順 | 作業 | 名前 | 工程 | 手順 |
|---|---|---|---|---|
| 1 | `inspect-brief` | ブリーフを検査する | 0 | [tasks/inspect-brief.md](tasks/inspect-brief.md) |
| 2 | `inspect-plan` | 探索の計画を検査する | 1 | [tasks/inspect-plan.md](tasks/inspect-plan.md) |
| 3 | `inspect-sources` | 素材台帳の事実を出典と突き合わせる | 1 | [tasks/inspect-sources.md](tasks/inspect-sources.md) |
| 4 | `inspect-images` | 画像の素材を検査する | 1 | [tasks/inspect-images.md](tasks/inspect-images.md) |
| 5 | `inspect-model` | 仕組みの定義を出典と突き合わせる | 1 | [tasks/inspect-model.md](tasks/inspect-model.md) |
| 6 | `extract-model-independently` | 同じ出典から、仕組みの定義を独立に抜き出す | 1 | [tasks/extract-model-independently.md](tasks/extract-model-independently.md) |
| 7 | `inspect-claims` | 問いごとの答えと主張の骨子を検査する | 2 | [tasks/inspect-claims.md](tasks/inspect-claims.md) |
| 8 | `derive-answer-independently` | ブリーフの問いと素材台帳だけから答えを書く | 2 | [tasks/derive-answer-independently.md](tasks/derive-answer-independently.md) |
| 9 | `read-summary-alone` | 要約の文だけを読んで結論と理由を述べる | 2 | [tasks/read-summary-alone.md](tasks/read-summary-alone.md) |
| 10 | `inspect-chapters` | 章構成を検査する | 3 | [tasks/inspect-chapters.md](tasks/inspect-chapters.md) |
| 11 | `inspect-storyline` | スライドの題と要点を検査する | 4 | [tasks/inspect-storyline.md](tasks/inspect-storyline.md) |
| 12 | `inspect-proof` | 立証の設計を検査する | 5 | [tasks/inspect-proof.md](tasks/inspect-proof.md) |
| 13 | `restore-point-from-proof` | 立証の設計だけから要点を書く | 5 | [tasks/restore-point-from-proof.md](tasks/restore-point-from-proof.md) |
| 14 | `read-relations-from-sample` | 見本の画像だけから関係を読み取る | 6 | [tasks/read-relations-from-sample.md](tasks/read-relations-from-sample.md) |
| 15 | `inspect-samples` | 型の見本を検査する | 6 | [tasks/inspect-samples.md](tasks/inspect-samples.md) |
| 16 | `inspect-chapter` | 章のスライド仕様を検査する | 7 | [tasks/inspect-chapter.md](tasks/inspect-chapter.md) |
| 17 | `inspect-unsupported-sentences` | 裏付けのない文がないかを検査する | 7 | [tasks/inspect-unsupported-sentences.md](tasks/inspect-unsupported-sentences.md) |
| 18 | `read-back-slides` | スライドの文だけを読んで意味を書き直す | 7 | [tasks/read-back-slides.md](tasks/read-back-slides.md) |
| 19 | `inspect-chapter-images` | 描いた結果の画像を検査する | 7 | [tasks/inspect-chapter-images.md](tasks/inspect-chapter-images.md) |
| 20 | `inspect-summary-evidence` | 要約に添えた根拠を検査する | 8 | [tasks/inspect-summary-evidence.md](tasks/inspect-summary-evidence.md) |
| 21 | `inspect-final-images` | 最終の出力の画像の写り込みを検査する | 9 | [tasks/inspect-final-images.md](tasks/inspect-final-images.md) |
