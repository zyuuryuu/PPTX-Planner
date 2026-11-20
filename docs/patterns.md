# 型の定義

[目次に戻る](README.md)

状態: 草案。付属する型の一覧と、収容量の値は未確定である。

型は、スライドの中身を表す形である。型の違いは工程の定義には書かず、型の定義としてデータで持つ。[工程6](stages/06-patterns.md)の表現設計が、型の定義から資料で使う型を選ぶ。

## 定義の項目

| 項目 | 内容 |
|---|---|
| `id` | 型の名前。描画の実装の名前や記法を含めない |
| `relations` | 対応する主張の種類([語彙と区分](vocabulary.md)) |
| `expresses` | この型が表せる関係。[形が伝える意味](visual-grammar.md)の含意の語彙で書く |
| `implies` | この型を使うと、読み手が必ず受け取る関係。同じ語彙で書く |
| `data` | 必要な項目(手順なら、各段の名前と説明など) |
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
capacity: {steps: null, name_chars: null, description_chars: null}   # 値は未確定
overflow_to: null
renderers: {}
```

`implies` は、型の形から決まる。[形が伝える意味](visual-grammar.md)の手がかりの表で、強と書かれた含意を全て挙げる。

型の定義には、情報を運ばない要素(影、グラデーション、意味のないアイコン)を置かない。

## 置き場と追加

資料の型と同じく、Plannerに付属する定義、個人の定義、資料の定義の3層で持つ。

大きな一覧を先に作り込まない。足りない型は、フィードバックをもとに追加する。追加のたびに、既存の型と整理する([表現規約](style-rules.md))。同じ含意を持つ型が既にあれば、新しい型を足さずに既存の型を使う。

## 付属する型の候補

| 区分 | 型 | 主張の種類 | 形が伝える含意 |
|---|---|---|---|
| 数量 | 棒グラフ | 項目の比較 | `comparable`、`proportional` |
| 数量 | 積み上げ棒グラフ | 構成比(複数の対象を比べる場合) | `partition`、`proportional`、`comparable` |
| 数量 | 折れ線グラフ | 推移 | `ordered`、`proportional` |
| 数量 | 円グラフ | 構成比(項目が少ない場合) | `partition`、`proportional` |
| 数量 | 散布図 | 相関 | `proportional` |
| 数量 | 度数の分布図 | 分布 | `ordered`、`proportional` |
| 数量 | 大きな数字 | 言い切り(1つの数値を述べる場合) | `emphasized` |
| 概念 | 段階の流れ | 手順 | `ordered` |
| 概念 | 階層の木 | 構造・階層 | `hierarchical` |
| 概念 | 2案の対比 | 対比(2案) | `opposed`、`comparable` |
| 概念 | 前後の対比 | 対比(前後) | `opposed`、`ordered` |
| 概念 | 因果の連鎖 | 因果 | `causal`、`ordered` |
| 概念 | 2軸の配置 | 位置づけ | `independent-axes`、`comparable` |
| 概念 | 箇条書き | 並列の列挙 | なし |
| 概念 | 言い切り | 言い切り | `emphasized` |
| 共通 | 表 | 項目の比較(指標が複数の場合)、並列の列挙(項目が共通の観点を持つ場合) | `comparable` |
| 仕組みの記述 | 構成図 | 構成 | `connected` |
| 仕組みの記述 | ER図 | 要素の関係 | `connected` |
| 仕組みの記述 | シーケンス図 | やり取り | `ordered`、`connected` |
| 仕組みの記述 | 状態遷移図 | 状態の遷移 | `connected` |
| 仕組みの記述 | フローチャート | 分岐のある流れ | `ordered`、`connected` |
| 仕組みの記述 | ガントチャート | 日程 | `ordered`、`proportional` |

横に並べた箱(カード)は、付属する型に含めない。全体を1つの基準で分けたものを示す場合には使えるが、その場合の主張の種類は構造・階層であり、分類の軸の明示を条件とする。並列の列挙には使わない。

並列の列挙の主な型は、囲みのない縦の箇条書きとする。項目の間に関係がないことを、そのまま示す形である。
