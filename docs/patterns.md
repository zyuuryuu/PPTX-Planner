# 型の定義

[目次に戻る](README.md)

状態: 草案。付属する型の一覧と、収容量の値は未確定である。

型は、スライドの中身を表す形である。型の違いは工程の定義には書かず、型の定義としてデータで持つ。[工程6](stages/06-patterns.md)の表現設計が、型の定義から資料で使う型を選ぶ。

## 定義の項目

| 項目 | 内容 |
|---|---|
| `id` | 型の名前。描画の実装の名前や記法を含めない |
| `relations` | 対応する主張の種類([語彙と区分](vocabulary.md)) |
| `base` | 土台。なし、または画像 |
| `expresses` | この型が表せる関係。[形が伝える意味](visual-grammar.md)の含意の語彙で書く |
| `implies` | この型を使うと、読み手が必ず受け取る関係。同じ語彙で書く |
| `data` | 必要な項目(手順なら、各段の名前と説明など) |
| `point_position` | 要点を置く位置の既定。`below-title`(題の直下)、`below-body`(中身の下)、`body`(中身そのもの)のいずれか。資料ごとの対応は、[工程6](stages/06-patterns.md)で決める |
| `capacity` | 収容量。項目の数と、項目ごとの字数の上限 |
| `overflow_to` | 収容量を超えた場合に使う型 |
| `renderers` | 描画の実装ごとに、どの機能で描くか |

例:

```yaml
id: step-flow
relations: [process]
expresses: [ordered]
implies: [ordered]
data:
  steps: [{name: 段の名前, description: 説明}]
point_position: below-body
capacity: {steps: null, name_chars: null, description_chars: null}   # 値は未確定
overflow_to: null
renderers: {}
```

`implies` は、型の形から決まる。[形が伝える意味](visual-grammar.md)の手がかりの表で、強と書かれた含意を全て挙げる。

`point_position` の既定は、`below-title` とする。数量の区分の型、段階の流れ、因果の連鎖、フローチャートは `below-body` とする。言い切りと大きな数字は `body` とする。

型の定義には、情報を運ばない要素(影、グラデーション、意味のないアイコン)を置かない。

## 置き場と追加

資料の型と同じく、Plannerに付属する定義、個人の定義、資料の定義の3層で持つ。

大きな一覧を先に作り込まない。足りない型は、フィードバックをもとに追加する。追加のたびに、既存の型と整理する([表現規約](style-rules.md))。同じ含意を持つ型が既にあれば、新しい型を足さずに既存の型を使う。

## 付属する型の候補

| 区分 | 型 | 識別子 | 主張の種類 | 土台 | 形が伝える含意 |
|---|---|---|---|---|---|
| 数量 | 棒グラフ | `bar-chart` | 項目の比較 | なし | `comparable`、`proportional` |
| 数量 | 積み上げ棒グラフ | `stacked-bar-chart` | 構成比(収容量を超えた場合の型。複数の対象を比べる) | なし | `partition`、`proportional`、`comparable` |
| 数量 | 折れ線グラフ | `line-chart` | 推移 | なし | `ordered`、`proportional` |
| 数量 | 円グラフ | `pie-chart` | 構成比 | なし | `partition`、`proportional` |
| 数量 | 散布図 | `scatter-chart` | 相関 | なし | `proportional` |
| 数量 | 度数の分布図 | `histogram` | 分布 | なし | `ordered`、`proportional` |
| 概念 | 段階の流れ | `step-flow` | 手順 | なし | `ordered` |
| 概念 | 階層の木 | `tree` | 構造・階層 | なし | `hierarchical` |
| 概念 | 2案の対比 | `versus` | 2案の対比 | なし | `opposed`、`comparable` |
| 概念 | 前後の対比 | `before-after` | 前後の対比 | なし | `opposed`、`ordered` |
| 概念 | 因果の連鎖 | `cause-chain` | 因果 | なし | `causal`、`ordered` |
| 概念 | 2軸の配置 | `two-axis` | 位置づけ | なし | `independent-axes`、`comparable` |
| 概念 | 箇条書き | `plain-list` | 並列の列挙 | なし | なし |
| 概念 | 言い切り | `statement` | 言い切り | なし | `emphasized` |
| 概念 | 大きな数字 | `big-number` | 言い切り(収容量の区分を問わず、1つの数値を述べる場合) | なし | `emphasized` |
| 共通 | 表 | `table` | 収容量を超えた場合の型として、項目の比較、並列の列挙で使う | なし | `comparable` |
| 仕組みの記述 | 構成図 | `architecture-diagram` | 構成 | なし | `connected` |
| 仕組みの記述 | ER図 | `er-diagram` | 要素の関係 | なし | `connected` |
| 仕組みの記述 | シーケンス図 | `sequence-diagram` | やり取り | なし | `ordered`、`connected` |
| 仕組みの記述 | 状態遷移図 | `state-diagram` | 状態の遷移 | なし | `connected` |
| 仕組みの記述 | フローチャート | `flowchart` | 分岐のある流れ | なし | `ordered`、`connected` |
| 仕組みの記述 | ガントチャート | `gantt-chart` | 日程 | なし | `ordered`、`proportional` |
| 画像 | 注釈つきの画像(番号の印) | `annotated-image-steps` | 手順 | 画像 | `ordered` |
| 画像 | 注釈つきの画像(引き出しの説明) | `annotated-image-callouts` | 構成 | 画像 | `connected` |
| 画像 | 画像の前後の対比 | `image-before-after` | 前後の対比 | 画像 | `opposed`、`ordered` |
| 画像 | 実物の提示 | `exhibit-image` | 実物の提示 | 画像 | なし |

土台は、型が画像の素材の上に描かれるかどうかを示す。同じ主張の種類でも、画像を土台にする場合は別の型を使う。表現の対応表は、主張の種類、量の区分、土台の3つを鍵にする。

「言い切り」の種類には、型が2つある(言い切り、大きな数字)。数値を1つだけ述べる場合に大きな数字を使う。この書き分けの鍵は未確定である。

横に並べた箱(カード)は、付属する型に含めない。全体を1つの基準で分けたものを示す場合には使えるが、その場合の主張の種類は構造・階層であり、分類の軸の明示を条件とする。並列の列挙には使わない。

画像の型は、画像の素材([工程1](stages/01-exploration.md))を土台にする。注釈は、画像の素材の `regions` を参照して置く。

並列の列挙の主な型は、囲みのない縦の箇条書きとする。項目の間に関係がないことを、そのまま示す形である。
