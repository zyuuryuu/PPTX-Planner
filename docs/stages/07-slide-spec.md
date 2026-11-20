# 工程7 スライド仕様

[目次に戻る](../README.md)

スライドごとに、載せる内容を確定する。章ごとに1ファイルに分け、章ごとに別のセッションで書く。1章の執筆では、他の章の仕様を読まない。読むのは、ブリーフ、全体の成果物(工程2から6)、素材台帳、表現規約である。

成果物 `07-slides/ch1.yaml`:

```yaml
- id: ch1-s2
  headline: △△の領域は過去5年、年率8%で伸びている
  takeaway: 成長は一時的な要因ではなく、5年続いている   # 結論1行。本編のスライドでは必須
  body:
    type: line-chart
    data: {...}
  text: 国内市場の{F040}を占めるまでに拡大した   # 数値は事実のIDで参照する
  sources: [F015, F016, F040]
  notes: 口頭で補う説明
```

`text`、`body.data`、`notes` の数値は直接書かず、事実のIDで参照する。ビルドの際に台帳の値に置き換える。`headline` と `takeaway` は、ストーリーラインを人が読めるように数値を直接書いてよい。その数値は、そのスライドの `sources` の事実と一致させる。他のスライドへの言及は、スライドのIDで書く。

画像の型のスライドでは、画像の素材と、注釈を付ける `regions` を参照する。位置は書かない。

```yaml
- id: ch5-s2
  headline: 保存の前に、納期の欄を確かめる
  takeaway: 納期が空のまま保存すると、発注が止まる
  body:
    type: annotated-image-steps
    asset: A003
    crop: [due-date-field, save-button]   # この範囲が入るように切り抜く
    scenario: S-order-entry               # 番号は、場面の順から決まる
    notes:
      due-date-field: 納期を入力する
      save-button: 保存を押す
  sources: [A003, F120]
```

合格条件:

- `headline` がストーリーラインと一致する(機械)。
- `body.type` が、立証設計の `relation` に対応する `pattern` と一致する(機械)。
- `sources` が立証設計の `facts` に含まれる(機械)。
- `text`、`body.data`、`notes` に、事実のIDによらない数値がない(機械)。
- `headline` と `takeaway` の数値が、`sources` の事実と一致する(検査セッション)。
- 画像の型のスライドが参照する `regions` が、全て画像の素材にある(機械)。
- 位置の出どころが `estimated` の `regions` に付けた注釈について、描いた印の周辺を切り出した画像を見て、印が `label` の対象を指している(検査セッション)。
- 用語集の禁止表記と、表記の規則への違反がない(機械)。
- `takeaway`、`text`、`notes` が語彙と文体の検査を通る(検査セッション)。
- ブリーフに「聴衆が既に知っている」と書かれた内容の説明を含まない(検査セッション)。
- 資料の表現規約が定める分量の上限に収まる(機械)。
