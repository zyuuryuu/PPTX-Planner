# 章の作業票: ch5

PMが上流の成果物から `trial/deck/work/make_tickets.py` で機械的に抜き出した。要約していない。正本は各成果物。

## 担当の範囲

成果物: `trial/deck/07-slides/ch5.yaml`(スライドの配列。順はストーリーラインの順)。

| スライド | 型 | 扱い |
|---|---|---|
| ch5-s1 | plain-list | 執筆する |
| ch5-s2 | statement | 執筆する |
| ch5-s3 | plain-list | 執筆する |
| ch5-s4 | statement | 執筆する |
| ch5-s5 | plain-list | 執筆する |
| ch5-s6 | statement | 執筆する |
| ch5-s7 | plain-list | 執筆する |
| ch5-s8 | statement | 執筆する |

章扉、目次、章のまとめ、出典の一覧は、描画の道具が上流の成果物から作る。書かない。

## ブリーフ(`00-brief.md` の全文)

# ブリーフ

SOCの新人アナリスト向けの講義資料。題材は、アラートの一次解析の進め方。

### 資料の型
- 状態: 確定

training(研修資料)。新人が一次解析を「できない」から「できる」に変わることを目的とするため。

### 伝え方
- 状態: 確定

口頭で説明する(講義で映して説明する)

### 主な読み手
- 状態: 確定

SOCに配属された新人アナリスト3人。ネットワークまたはサーバーの運用を2〜3年経験している。セキュリティ製品を触ったことはない。

### 副次的な読み手
- 状態: 確定

なし

### 読み手が既に知っていること
- 状態: 確定

TCP/IP、WindowsとLinuxの基本、ログというものの概念。

次は知らないため、資料で説明する: ログの見方、攻撃の手口の体系(ATT&CKなど)、SIEMの相関の仕組み、EDRが何を記録しているか、解析の進め方そのもの。

### 読み手の立場と懸念
- 状態: 確定
- 立場: 中立
- 懸念: 誤検知ばかりで、何を見ればいいか分からない
- 懸念: 間違って閉じるのが怖い
- 懸念: どこまで調べたら上に上げていいのか分からない

新人が実際に言っていること。最も重いのは「間違って閉じるのが怖い」(依頼者の判断)。

立場は、教わる側として中立とした。

### 目的
- 状態: 確定

今は、届いたアラートをどう扱えばよいか分からない。配属から3か月で、届いたアラートを見て、誤検知として閉じる、調査を続ける、上に上げる、のいずれかを1人で決められるようにする。

### 答えるべき問い
- 状態: 確定

新人がアラートを受けてから「誤検知として閉じる/調査を続ける/上に上げる」を決めるまでに、何をどの順で確かめ、何を基準に決めればよいか

### 扱わない範囲
- 状態: 確定

一次解析の後の工程(上に上げた後の詳しい調査、インシデント対応)。特定の製品の画面や操作(製品名を出さず、SIEMやEDRに共通する説明にする)

### 使われる場面
- 状態: 確定

講義で映して説明する。1つの資料を、90分の講義2回に分けて使う。講義の中で演習を行う

### 書き手の立場
- 状態: 確定

受講者が配属されたSOCのリーダー(受講者の上司)

### 制約
- 状態: 確定
- 枚数の上限: 50
- 発表時間: 90分を2回
- 言語: 日本語

### 外に出せない情報
- 状態: 確定

会社名、社内のホスト名、社員の名前、過去に実際に起きた事案の日時と部署。

資料に載せるアラートの例は全て架空のものにする。社内のアラートの実例は使わない。

### 手元の資料
- 状態: 確定

なし。社内の手順書は古いため使わない。公開されている資料を調べて使う。

### 型ごとの追加の項目
- 状態: 確定

受講者の今の水準: ネットワークまたはサーバーの運用を2〜3年。セキュリティ製品の経験はない。
受講後に何で習得を確かめるか: 講義の中の演習。架空のアラートの例を数件見せ、「閉じる/調査を続ける/上に上げる」のどれかと、その根拠を答えさせる。配属後の実務での確認は、資料とは別に行う。


## 章(`03-chapters.yaml`)

```yaml
id: ch5
cover_question: 架空のアラートで、閉じる・調べる・上げるを自分で決められるか
kind: closing
title: 演習とまとめ
message: 新人は、この講義の最後の演習で、架空のアラートを3つに分け、閉じる、調べる、上げるのどれにするかと根拠を答え、配属から3か月で1人で決められるようにする
slides: 10
slides_reason: 習得を演習で確かめる(ブリーフ)。架空のアラート1件につき問題と解説の2枚を4件分(8枚)と、章扉、章のまとめ(講義全体のまとめを兼ねる)の2枚を充てる
```

## 資料の結論(`02-claims.yaml`)

```yaml
answer: 新人が、届いたアラートを、根拠とログから誤検知、想定内の検知、攻撃の疑いの3つに分け、影響の大きさで優先度を付けたうえで、閉じる、調べる、上げるを根拠とともに1人で決められる
summary: アラートは、誤検知、想定内の検知、攻撃の疑いの3つに分ける。根拠をもって誤検知か想定内と言えるものだけを記録して閉じ、迷ったら上げる。
```

## 章の前提と到達点(`04-chapter-states.yaml`)

```yaml
chapter: ch5
entry:
  terms:
  - 誤検知
  - 想定内の検知
  - 閉じる
  - 調べる
  - 上げる
  accepted:
  - C1
  - C2
  - C3
  - C4
  open_questions:
  - 自分で決められるか
exit:
  terms: []
  accepted: []
  answered:
  - 自分で決められるか
  open_questions: []
```

## スライドごとの見出しと立証の設計(`04-storyline.yaml`、`05-proof.yaml`)

見出し(`headline`)は1文字も変えずに写す。`source` は出典の行として道具が描く(仕様には書かない)。使ってよい事実は、立証の設計の `facts` だけ。

### ch5-s1

型: `plain-list`

```yaml
# ストーリーライン
id: ch5-s1
chapter: ch5
section: null
question: 演習1では、どんなアラートが届いたのか
headline: '演習1: 一覧に載ったスキャン用の端末から、一覧の時刻に、多数の宛先への接続のアラートが届いた'
# 立証の設計
id: ch5-s1
relation: list
show: '演習1の架空のアラートの項目: 検知のルール(多数の宛先への接続)、接続元の端末、時刻、宛先の数。横に、リーダーの一覧(架空)の抜粋(スキャン用の端末と、スキャンの時間帯)を表示する。架空であることを明記する'
focus: 端末と時刻が一覧と合うこと
facts: []
axis: null
base: none
holds: []
relation_reason: 架空のアラートの項目を並べる。実物ではないため exhibit にしない
```

### ch5-s2

型: `statement`

```yaml
# ストーリーライン
id: ch5-s2
chapter: ch5
section: null
question: 演習1の答えは何か
headline: '演習1の答え: 端末と時刻が一覧と合うため、想定内の検知として記録して閉じる'
# 立証の設計
id: ch5-s2
relation: statement
show: '答えの1文と、当てはめた規則のスライドの番号: 端末と時刻が一覧と合うため、想定内の検知として記録して閉じる(ch3-s6 の規則を当てはめる)'
focus: 当てはめた規則
facts: []
axis: null
base: none
holds: []
relation_reason: 答えの1文と、当てはめた規則を示すスライドで、比べる対象も順序もない
```

### ch5-s3

型: `plain-list`

```yaml
# ストーリーライン
id: ch5-s3
chapter: ch5
section: null
question: 演習2では、どんなアラートが届いたのか
headline: '演習2: 管理ツールの定期の通信に、緩く書かれたルールが反応したアラートが届いた'
# 立証の設計
id: ch5-s3
relation: list
show: '演習2の架空のアラートの項目: 検知のルールの条件(緩く書かれた条件)、接続元(管理ツールのサーバ)、通信の周期(定期)。架空であることを明記する'
focus: ルールの条件が緩く、無害な通信に合っていること
facts: []
axis: null
base: none
holds: []
relation_reason: 架空のアラートの項目を並べる。実物ではないため exhibit にしない
```

### ch5-s4

型: `statement`

```yaml
# ストーリーライン
id: ch5-s4
chapter: ch5
section: null
question: 演習2の答えは何か
headline: '演習2の答え: 検知の条件が無害な活動に反応した誤検知として、根拠を記録して閉じる'
# 立証の設計
id: ch5-s4
relation: statement
show: '答えの1文と、当てはめた規則のスライドの番号: 検知の条件の誤りと根拠をもって言えるため、誤検知として記録して閉じる(ch3-s5 を当てはめる)'
focus: 当てはめた規則
facts: []
axis: null
base: none
holds: []
relation_reason: 答えの1文と、当てはめた規則を示すスライドで、比べる対象も順序もない
```

### ch5-s5

型: `plain-list`

```yaml
# ストーリーライン
id: ch5-s5
chapter: ch5
section: null
question: 演習3では、どんなアラートが届いたのか
headline: '演習3: 外部から既知の攻撃の通信が届き、防がれた記録があるアラートが届いた'
# 立証の設計
id: ch5-s5
relation: list
show: '演習3の架空のアラートの項目: 検知のルール(既知の攻撃の通信)、接続元(外部)、防がれた記録。架空であることを明記する'
focus: 攻撃の試みが防がれた記録があること
facts: []
axis: null
base: none
holds: []
relation_reason: 架空のアラートの項目を並べる。実物ではないため exhibit にしない
```

### ch5-s6

型: `statement`

```yaml
# ストーリーライン
id: ch5-s6
chapter: ch5
section: null
question: 演習3の答えは何か
headline: '演習3の答え: 侵害に至らなかった攻撃の試みで、配属から3か月の新人は全て上げる'
# 立証の設計
id: ch5-s6
relation: statement
show: '答えの1文と、当てはめた規則のスライドの番号: 侵害に至らなかった攻撃の試みで、配属から3か月の新人は全て上げる(ch3-s14 を当てはめる)'
focus: 当てはめた規則
facts: []
axis: null
base: none
holds: []
relation_reason: 答えの1文と、当てはめた規則を示すスライドで、比べる対象も順序もない
```

### ch5-s7

型: `plain-list`

```yaml
# ストーリーライン
id: ch5-s7
chapter: ch5
section: null
question: 演習4では、どんなアラートが届いたのか
headline: '演習4: 重要でない業務用のPCで、一覧にない見慣れないプロセスが動いたアラートが届いた'
# 立証の設計
id: ch5-s7
relation: list
show: '演習4の架空のアラートの項目: 端末(重要でない業務用のPC)、見慣れないプロセス名。横に、リーダーの一覧(架空)の抜粋を表示し、当てはまる行がないことを示す。架空であることを明記する'
focus: 一覧にない活動で、資産が重要でないこと
facts: []
axis: null
base: none
holds: []
relation_reason: 架空のアラートの項目を並べる。実物ではないため exhibit にしない
```

### ch5-s8

型: `statement`

```yaml
# ストーリーライン
id: ch5-s8
chapter: ch5
section: null
question: 演習4の答えは何か
headline: '演習4の答え: 閉じずに調べ、30分の中で誤検知と根拠をもって言えなければ、見たことを付けて上げる'
# 立証の設計
id: ch5-s8
relation: statement
show: '答えの1文と、当てはめた規則のスライドの番号: 閉じずに調べ、30分の中で誤検知と根拠をもって言えなければ、見たことを付けて上げる(ch3-s6、ch3-s11、ch3-s13 を当てはめる)'
focus: 当てはめた規則
facts: []
axis: null
base: none
holds: []
relation_reason: 答えの1文と、当てはめた規則を示すスライドで、比べる対象も順序もない
```

## 立証の設計が参照する、ほかの章のスライドの見出し

| スライド | 見出し |
|---|---|
| ch3-s11 | このSOCでは、配属から3か月の新人の持ち時間は1件30分で、過ぎたら見たことを付けて上げる |
| ch3-s13 | このSOCでは、30分調べても閉じる根拠がなく迷うなら、閉じずに上げる |
| ch3-s14 | このSOCでは、配属から3か月の新人は攻撃の試みも全て上げ、溢れたらリーダーが対処する |
| ch3-s5 | 案として、検知の条件かデータの誤りで出たと根拠をもって言えるときだけ、誤検知として閉じる |
| ch3-s6 | このSOCでは、新人が想定内の検知として閉じてよいのは、リーダーの一覧にある活動だけ |

## 前後の章の見出し

### ch4 誤りやすい点

- ch4-s1: 2013年のTargetの侵害では、緊急のアラートが出たが対応がなかったと報告されている
- ch4-s2: 米上院の報告は、アラートが頻繁だったなら、誤検知とみなされた可能性があると推定する
- ch4-s3: ベンダーの調査では、IT専門職の56%が、過去の誤検知を理由にアラートを無視したと答えた

### appendix 付録

- ap-s1: 扱う量は出典で大きく違い、1つのSOCの実測は1日約13,764件、自己申告は1日平均4,484件
- ap-s2: 上げるのが遅れる誤りも、上げすぎる誤りも、割合を測った公開の調査は見つからなかった

## この章のスライドが使う事実(`01-sources.yaml`、`incoming/`)

なし(立証の設計の facts が空)。

## この章に関わる語彙(`terms.yaml` から、章の上流の文に出る語と、事実の metric の語)

```yaml
terms:
- id: T-close
    term: 閉じる
    kind: action
    definition: アラートを、誤検知か想定内の検知と判断して、調べたことと判断を記録し、対応を終える
    note: 依頼者が決めた3つの行き先の1つ(2026-11-24)
    defined_in: ch1-s1
    no_definition: null
  - id: T-investigate
    term: 調べる
    kind: action
    definition: 閉じるか上げるかを決めるために、持ち時間の中でログなどを確かめ続ける
    note: 依頼者が決めた3つの行き先の1つ。ブリーフの「調査を続ける」と同じ
    defined_in: ch1-s1
    no_definition: null
  - id: T-escalate
    term: 上げる
    kind: action
    definition: アラートを、経過と証拠を添えて上位の担当者に引き継ぐ
    note: 依頼者が決めた3つの行き先の1つ。ブリーフの「上に上げる」と同じ
    defined_in: ch1-s1
    no_definition: null
  - id: T-log
    term: ログ
    kind: noun
    definition: イベントを書き残したもの
    note: 依頼者が決めた(2026-11-23)
    defined_in: ch2-s4
    no_definition: null
    not:
    - T-event
  - id: T-alert
    term: アラート
    kind: noun
    definition: 検知の仕組みが、決められた条件に合うイベントを見つけて出す知らせ。この時点では本物の攻撃かどうかは分からない
    note: 依頼者が決めた(2026-11-23)
    defined_in: ch2-s1
    no_definition: null
    not:
    - T-incident
    - T-event
  - id: T-incident
    term: インシデント
    kind: noun
    definition: 調べた結果、実際に侵害や被害がある、と判断したもの。新人は自分でインシデントと決めず、その疑いがあれば上に上げる
    note: 依頼者が決めた(2026-11-23)。製品(Microsoft Sentinel、Defender)の「インシデント」はアラートのまとまりで、この語とは違う
    defined_in: null
    no_definition: 本編の見出しと図では使わない。製品の呼び名は model_labels で「アラートのまとまり」と書き分ける。出典の語として出る場合は、ノートで意味を補う
    not:
    - T-alert
  - id: T-false-positive
    term: 誤検知
    kind: noun
    definition: 検知の条件そのものが誤っていて、無害な活動に反応したアラート(緩すぎるルール、誤ったデータなど)
    note: 依頼者が決めた(2026-11-23)。想定内の検知を含めない
    defined_in: ch2-s8
    no_definition: null
    not:
    - T-expected-detection
  - id: T-expected-detection
    term: 想定内の検知
    kind: noun
    definition: 検知の条件どおりに正しく反応したが、業務上は問題のない活動によるアラート(社内の脆弱性スキャン、委託したペネトレーションテストなど)。出典では benign trigger、Benign Positive、Informational, expected activity などと呼ばれる
    note: 依頼者が名前を決めた(2026-11-23)
    defined_in: ch2-s9
    no_definition: null
    not:
    - T-false-positive
  - id: T-attack-attempt
    term: 攻撃の試み
    kind: noun
    definition: 侵害に至らなかった攻撃によるアラート(出典の attack attempts)
    not:
    - T-attack-suspect
    defined_in: ch2-s6
    no_definition: null
  - id: T-list
    term: 一覧
    kind: noun
    definition: リーダーが事前に作った、想定内の活動(承認済みのスキャン、委託した診断など)の一覧。新人が想定内の検知として閉じてよいのは、これに当てはまるものだけ
    defined_in: ch3-s6
    no_definition: null
  - id: T-rule
    term: ルール
    kind: noun
    definition: 検知の仕組みが、イベントがアラートに当たるかを決める条件。出典の signature(シグネチャ)と analytics rule を含む
    defined_in: ch2-s2
    no_definition: null
  - id: T-siem
    term: SIEM
    kind: noun
    definition: 複数のログ源のデータを集めて相関させ、重要なイベントを特定する仕組み
    not:
    - T-edr
    defined_in: ch2-s2
    no_definition: null
  - id: T-edr
    term: EDR
    kind: noun
    definition: 端末の振る舞いの記録を継続して集め、脅威を検知してアラートを出す仕組み
    not:
    - T-siem
    defined_in: ch2-s3
    no_definition: null
  - id: T-attck
    term: ATT&CK
    kind: noun
    definition: 攻撃者の戦術と技術の、実世界の観測に基づく知識ベース(MITRE)
    defined_in: ch2-s5
    no_definition: null
  - id: T-proposal
    term: 案
    kind: noun
    definition: 公開資料の材料から、この講義が組み立てた基準。公的な基準でも、このSOCの運用でもない
    not:
    - T-soc-ops
    defined_in: ch3-s2
    no_definition: null
  - id: T-newbie
    term: 新人
    kind: noun
    definition: 配属から3か月の解析者。この講義の受講者
    defined_in: null
    no_definition: ブリーフの主な読み手とその関係者で、受講者が既に知っている
  - id: T-leader
    term: リーダー
    kind: noun
    definition: このSOCで、新人が閉じたアラートを見直し、一覧を作る人
    defined_in: null
    no_definition: ブリーフの主な読み手とその関係者で、受講者が既に知っている
banned:
- term: 良性のトリガー
  reason: 想定内の検知と同じ対象を指す。出典の訳語
  use:
  - T-expected-detection
- term: 調査を続ける
  reason: 3つの行き先は「閉じる・調べる・上げる」で揃える(依頼者の指定)
  use:
  - T-investigate
- term: 上に上げる
  reason: 同上
  use:
  - T-escalate
- term: エスカレーション
  reason: 同上。出典の語として引く場合を除く
  use:
  - T-escalate
- term: 警報
  reason: アラートと同じ対象を指す(依頼者の指定)。出典の引用の訳を除く
  use:
  - T-alert
- term: シグネチャ
  reason: ルールと同じ対象を指す。出典の語として出典の行で示す場合を除く
  use:
  - T-rule
- term: 偽陽性
  reason: 誤検知と同じ対象を指す。出典の False positive の訳
  use:
  - T-false-positive
- term: 真陽性
  reason: この資料は使わない。攻撃の疑い、攻撃の試み、侵害に至った攻撃のどれを指すかが決まらない
  use:
  - T-attack-suspect
  - T-attack-attempt
- term: トリアージ
  reason: 一次解析の全体か、優先度付けだけかが出典で割れる。この資料は「分ける」「優先度を付ける」で書く
  use:
  - T-priority
- term: 持ち時間の目安
  reason: 公的な目安と、このSOCの持ち時間が混ざる。このSOCの値は「持ち時間」、外の値は出典の行で示す
  use:
  - T-timebox
- term: 深刻度
  reason: 重大度と同じ対象を指す(依頼者の指定)
  use:
  - T-severity
model_labels:
  D-sentinel-incident: 'アラートのまとまり(製品の呼び名: インシデント。資料で言うインシデントではない)'
  D-mde-incident: 'アラートのまとまり(製品の呼び名: インシデント。資料で言うインシデントではない)'
  D-significant-event: 重要と判断されたイベント(まだアラートではない)
candidates:
- kind: 同じ概念か
  terms:
  - 重大度
  - 深刻度
  decision: 同じ対象。製品が付けた重大度で、言葉は「重大度」にそろえる。深刻度は banned(依頼者が工程6で決めた。F009)
  note: このSOCの運用の「重大度が高い」と、ch3-s7 の「SIEMの深刻度」
- kind: 同じ概念か
  terms:
  - ルール
  - シグネチャ
  decision: 同じ対象。資料ではルールで書き、シグネチャは banned(依頼者が工程6で同意)
- kind: 同じ概念か
  terms:
  - アラート
  - 警報
  decision: 同じ対象。警報は banned(依頼者が工程4で指定)
- kind: 同じ概念か
  terms:
  - 攻撃の疑い
  - 攻撃の試み
  decision: 別の概念。攻撃の試みは攻撃の疑いの一部(依頼者が工程6で同意)
- kind: 同じ概念か
  terms:
  - 想定内の検知
  - 想定内の活動
  decision: 別の概念。想定内の活動は一覧に載る業務、想定内の検知はそれによるアラート(依頼者が工程6で同意)
- kind: 2つの意味
  terms:
  - インシデント
  decision: 資料の意味(実際に侵害や被害があると判断したもの)と、製品の呼び名(アラートのまとまり)。製品の呼び名は model_labels で書き分ける(依頼者が工程1で決めた)
- kind: 2つの意味
  terms:
  - 一覧
  decision: 資料ではリーダーの一覧だけを指す(依頼者が工程6で同意)
```

## 資料の表現規約(`style.yaml` の全文)

```yaml
# 資料の表現規約(SOC試行)
# 資料の型の定義(docs/deck-types.md の training)の limits は null であるため、値を写せない。
# 主張の数の上限などは、使う工程(工程2)に入る前に、ユーザーと決めて書き足す。決めるまでは null とする。
deck_type: training
delivery: oral
limits:
  max_claims: 5   # 設計セッションが決めた(D003)。研修資料の分解の4つに、1つの余裕
  headline_chars: 50   # 見出しは2行まで(D006)。骨組みの資料の画面で1行が約37字
# 個人の表現規約は、資料のディレクトリの外に置くとされるが、実体がない。
# docs/style-rules.md が定める個人の表現規約の初期値を、ここに写す。
# 機械で検出する辞書(docs/writing.md)がまだないため、全て inspection とする。
rules:
  - id: P001
    rule: 情報を足さない飾りの形容を書かない
    reason: 読み手の注意を、情報のない語に使わせない
    check: inspection
    issue: null
    exceptions: []
  - id: P002
    rule: 読み手が知っている前提を説明しない
    reason: ブリーフの「読み手が既に知っていること」は資料で説明しない
    check: inspection
    issue: null
    exceptions: []
  - id: P003
    rule: 本題の前に前置きを書かない
    reason: 情報のない文で読み手の時間を使わない
    check: inspection
    issue: null
    exceptions: []
  - id: P004
    rule: 資料自身の狙いや構成を語る文を書かない
    reason: 構成は目次と章扉で示す。本文で繰り返さない
    check: inspection
    issue: null
    exceptions: []
  - id: P005
    rule: 依頼や検討の経緯を写した文を書かない
    reason: 読み手に要るのは結論と根拠で、作る過程ではない
    check: inspection
    issue: null
    exceptions: []
  - id: P006
    rule: 専門用語と略語は、補足なしに使わない
    reason: 読み手はセキュリティ製品の経験がない
    check: inspection
    issue: null
    exceptions: []
  - id: P007
    rule: 接続詞の代わりに矢印や記号を使わない
    reason: 記号は、因果、順序、変換のどれを指すかが曖昧になる
    check: inspection
    issue: null
    exceptions: []
  - id: P008
    rule: 意味を持たないアイコン、見た目のために揃えた項目の数、意味のない囲みを使わない
    reason: 形は読み手に意味を伝える(docs/visual-grammar.md)
    check: inspection
    issue: null
    exceptions: []
# 資料に共通の規則(工程6、docs/stages/06-patterns.md の表)。テンプレートがないため全て設計セッションが決め、見本で依頼者の同意を得る。
# 大きさは 16:9、1280×720 ピクセルの描画で測る(1pt = 4/3 px として換算)。
common:
  font_min:                    # 文字の大きさの下限
    headline: 24pt
    source_line: 16pt          # 出典の行。後ろの席から読める大きさ(D006 の依頼者の条件)
    body: 18pt                 # 説明、箇条書き、表のセル、図の外に置く説明の文
    figure_text: 16pt          # 図の中の文字
    note: 14pt                 # 図の注記
  colors:                      # 同じ対象は全ての図で同じ色。割り当てた色を別の対象に使わない
    閉じる: '#2563EB'
    調べる: '#B45309'
    上げる: '#DC2626'
    誤検知: '#6B7280'
    想定内の検知: '#0E7490'
    攻撃の試み: '#EA580C'
    侵害に至った攻撃: '#7F1D1D'
    分類できないもの: '#D1D5DB'
    案の印: '#7C3AED'          # 「案」の札と、案の部分の破線の枠
    このSOCの運用の印: '#111827' # 「運用」の札
    仕組みの部品: '#E5E7EB'    # 仕組みの図の部品の塗り(色で区別しない)
  emphasis: 注目させる点だけを、太い黒(#111827)の枠と太字で示す。強調に色を使わない(色は対象の区別に使っているため)。1枚に1か所
  arrows:
    実線の矢印: 流れ(次の段に進む、データが渡る、行き先に進む)
    太い実線の矢印と「ので」のラベル: 因果
    ラベル付きの細い線(矢印なし): 流れでない関係(問い合わせる、含む など)。ラベルで関係を書く
    線なし: 出典につながりがない(仕組みの定義の途切れ)。途切れには「経路は出典にない」の注記を付け、近さでつながりを読ませない位置に置く
  shapes:
    角の丸い四角: 部品、データ、段、状態
    ひし形: 分かれ目(判定)
    両端の丸い札: 行き先(閉じる、調べる、上げる)
    破線の枠: 案の部分
  flow_direction: 左から右(時間、手順、因果、データの流れ)。分かれ目からの行き先だけは下に出す
  positions:
    headline: 上端
    source_line: 見出しのすぐ下(D006)
    figure: 中央
    legend: 図の右上
    unit: 値のすぐ後ろ、または凡例
    note: 図の左下
    takeaway: 下端の帯(結論1行)
  max_hues_per_slide: 4        # 灰色と黒を除き、colors で割り当てた色を1つずつ数える(色相の近さでまとめない)
  takeaway_on_slide: true      # 結論1行を下端の帯に載せる
  summary_form: 要約の文だけ。読み手に求めることは載せない(研修資料で、新人に判断を求める資料ではないため)
  metadata: 作成者の欄は空にする。題は「SOCのアラートの一次解析(新人研修)」とし、会社名、社内の名前を入れない(ブリーフの出せない情報)
exceptions:
  - target: 02-claims.yaml summary
    rule: summary は1文で、結論と理由をまとめる(docs/stages/02-claims.md の合格条件)
    reason: 依頼者の指定。研修資料の冒頭と最後に置く文は新人に覚えさせる文であり、結論だけの短い2文にする(D004)
  - target: 04-storyline.yaml の演習の問題のスライド(ch5-s1、s3、s5、s7)
    rule: 見出しが否定の検査と具体性の検査を通る(docs/stages/04-storyline.md の合格条件)
    reason: 演習の問題は架空のアラートの描写で、主張ではない。否定の検査の対象外とし、question は「どんなアラートが届いたのか」として見出しが答える形にする(D007)
  - target: 03-chapters.yaml ch1 の章のまとめ
    rule: 全ての章に章扉と章のまとめを置く(docs/vocabulary.md の半導出。tools/check.py の工程4の枚数の検査は、章の枚数に章扉と章のまとめの2枚を足して数える)
    reason: 依頼者の指示。第1章は扉も中身2枚も結論そのもので、まとめを足すと同じ文が3回続く(D010)。工程4の枚数の機械の検査は ch1 で不合格になるが、この例外による
  - target: 07-slides の演習(ch5-s1、s3、s5、s7)の架空のアラートの項目と、架空の例(ch2-s8 の「宛先のポートが443」など)
    rule: text、body.data、notes に、事実のIDによらない数値がない(docs/stages/07-slide-spec.md の合格条件)
    reason: 架空の例の数値は事実ではなく、台帳に載せるものではない。スライドに「架空」と明記することを条件に、事実のIDによらずに書いてよい(D013)。事実を述べる数値には適用しない
terms: terms.yaml
```

## 表現の対応表(`06-patterns.yaml`)

```yaml
- relation: statement
  size: any
  base: none
  pattern: statement
- relation: list
  size: any
  base: none
  pattern: plain-list
- relation: process
  size: any
  base: none
  pattern: step-flow
- relation: branching-flow
  size: any
  base: none
  pattern: flowchart
- relation: architecture
  size: any
  base: none
  pattern: architecture-diagram
- relation: composition
  size: any
  base: none
  pattern: pie-chart
- relation: item-comparison
  size: any
  base: none
  pattern: table
  note: 項目の比較の主な型を表とした。この資料の項目の比較(ch3-s1 の段の並び、ap-s1 の調べ方の違う値)は量を同じ尺度で比べるものではなく、棒グラフの proportional が成り立たないため
- relation: entity-relation
  size: any
  base: none
  pattern: er-diagram
- relation: structure
  size: any
  base: none
  pattern: tree
- relation: causality
  size: any
  base: none
  pattern: cause-chain
```

## この章で使う型の見本の仕様(`06-samples/`)

### plain-list(`06-samples/plain-list.yaml`、画像は `06-samples/plain-list.png`)

```yaml
# 型の見本のスライド仕様(工程6)。工程7でそのまま使う。
id: ch3-s15
status: done
headline: 案として、上げるときは、出どころとID、調べた経過、証拠、判定の仮説、次の手順を添える
takeaway: 文脈のない引き継ぎでは、受けた側が調べ直すことになる
body:
  type: plain-list
  mark: 案
  title: 上げるときに添える5項目
  items:
  - アラートの出どころとID
  - 調べた経過
  - 集めた証拠
  - 現時点の判定の仮説
  - 次に勧める手順
  highlight: title
sources:
- F413
- F414
notes: 送信元のIPアドレスを書き漏らすと、受けた側が元のイベントを探し直すことになる(F414 の例)。
```

### statement(`06-samples/statement.yaml`、画像は `06-samples/statement.png`)

```yaml
# 型の見本のスライド仕様(工程6)。工程7でそのまま使う。
id: ch4-s2
status: done
headline: 米上院の報告は、アラートが頻繁だったなら、誤検知とみなされた可能性があると推定する
takeaway: 見過ごしの原因は確かめられていないが、慣れが見過ごしにつながりうる
body:
  type: statement
  quote_of: F501
  text: システムが頻繁に警報を鳴らしていたのであれば、職員はこのアラートを誤検知とみなした可能性がある
  attribution: 報告の原文(英語)の日本語訳。報道を引いた記述
  caveat: 推定であり、確認された原因ではない
  highlight: caveat
sources:
- F501
notes: 報告は報道(Bloomberg Businessweek)を引いて推定を述べている。報告自身は原因を確かめていない。
```

## 型ごとの body の書式と収容量(`tools/patterns-data.md` の全文)

# 型ごとの body の書式と収容量

スライド仕様(`07-slides/<章>.yaml`)の `body` に書くデータの書式。描くのは `tools/render.py`。

```
python tools/render.py trial/deck            # 全体を描く(build/slides/*.html、*.png、deck.html、diagnostics.json)
python tools/render.py trial/deck --only ch2-s3 --no-png   # 1枚だけ描き直し、診断だけを見る
```

依存: Python 3、PyYAML、Pillow、graphviz(`dot`)、Node.js と Playwright(Chromium)。

### 全ての型に共通

スライド仕様の項目(工程7の定義のとおり): `id`、`status`、`headline`、`takeaway`、`body`、`text`、`sources`、`notes`。

| 項目 | 描き方 |
|---|---|
| `headline` | ストーリーラインの見出しで描く。仕様と違えば警告 |
| 出典の行 | ストーリーラインの `source` を見出しの下に描く(仕様には書かない) |
| `takeaway` | 下端の帯に1行。1行に収まらなければエラー(全角で約44字まで) |
| `text` | 図の下に本文の大きさで描く。全角で約48字で1行 |
| `notes` | スライドには描かない。`build/deck.html` のスライドの下に出す |
| `body.mark` | `案` か `運用`。図の上に札を置く(plain-list では題の前) |
| `body.highlight` | 強調する1か所。型ごとの書き方は下の表。図と表の型で省くと警告 |

数値は直接書かず、事実を参照する。`text` と、`body` の文字列の中では次の書き方を使える。

| 書き方 | 置き換わるもの | 例(F201: value 13764、unit 件/日) |
|---|---|---|
| `{F201}` | 値と単位 | 13,764件/日 |
| `{F201:value}` | 値だけ | 13,764 |
| `{F201:unit}`、`{F201:metric}` | 単位、`metric` の語 | |

参照した事実が台帳にない、`sources` にない、`value` がない場合は診断に出す。

仕組みの定義を参照する型(flowchart、er-diagram、architecture-diagram)は、要素とつながりの名前を定義から引く。順は `body.labels` の指定 → 語彙表の `model_labels` → 定義の `name`(日本語を含まない括弧書きを除く。`端末(endpoints)` → `端末`)。図に載せる短い名前が定義にないときだけ `labels` に書く。

文字の大きさは style.yaml の下限から決め、縮めない。図の中 22px(16pt)、注記 19px(14pt)、本文 24px(18pt)。

### 収容量の前提

下の収容量は、見出し2行と出典の行2行(図に使える高さ約430px)で、合成したデータを描いて診断がエラーにならなかった最大の値である(`render.py` で測った。字数は全角)。見出しか出典の行が1行なら、高さは約40px ずつ増える。収容量の内でも、文が長いと診断に出ることがある。最後は診断で確かめる。

### statement(言い切り)

| 項目 | 必須 | 内容 |
|---|---|---|
| `text` | 必須(`quote_of` があれば省ける) | 言い切る文。`quote_of` があれば引用として「」で囲む |
| `quote_of` | 任意 | 引用元の事実のID。`text` を省くと、事実の `quote`(原文)を載せる |
| `attribution` | 任意 | 引用の下の説明(訳であること、引用の出どころ) |
| `caveat` | 任意 | 但し書き |
| `highlight` | 任意 | `text` か `caveat` |

収容量: `text` は約200字まで(但し書き1行を含む)。

```yaml
body:
  type: statement
  quote_of: F501
  text: システムが頻繁に警報を鳴らしていたのであれば、職員はこのアラートを誤検知とみなした可能性がある
  attribution: 報告の原文(英語)の日本語訳。報道を引いた記述
  caveat: 推定であり、確認された原因ではない
  highlight: caveat
```

### plain-list(箇条書き)

| 項目 | 必須 | 内容 |
|---|---|---|
| `items` | 必須 | 項目の配列。項目は文字列、または `{text, sub: [下の項目]}` |
| `title` | 任意 | 一覧の題 |
| `mark` | 任意 | `案` か `運用` |
| `highlight` | 任意 | `title` か `items[番号]` |

収容量: 7項目まで(各1行)。1項目は約40字まで(それを越えると2行になり、収まる項目が減る)。

```yaml
body:
  type: plain-list
  mark: 案
  title: 上げるときに添える5項目
  items: [アラートの出どころとID, 調べた経過, 集めた証拠, 現時点の判定の仮説, 次に勧める手順]
  highlight: title
```

### step-flow(段階の流れ)

| 項目 | 必須 | 内容 |
|---|---|---|
| `steps` | 必須 | 段の配列。段は `{name, description, next}` |
| `steps[].name` | 必須 | 段の名前。番号は自動で付く |
| `steps[].description` | 任意 | 文字列、または段落の配列。段落は文字列か `{text, color}`(`color` は style.yaml の色の名前。例: `上げる`) |
| `steps[].next` | 任意 | 次の段への矢印に添える語(例: それ以外) |
| `numbering` | 任意 | 番号の始まり。既定は1。`null` で番号なし |
| `highlight` | 任意 | `steps[番号]` |

収容量: 5段まで(箱の幅の下限 170px)。説明は、3段で約60字、4段で約40字、5段で約20字まで。名前は約8字まで。

```yaml
body:
  type: step-flow
  numbering: 0
  steps:
  - name: 重大度を見る
    description: [製品の重大度が High 以上なら, {text: まず上げる, color: 上げる}]
    next: それ以外
  - name: 3つに分ける
    description: [誤検知, 想定内の検知, 攻撃の疑い]
  - name: 行き先を決める
    description: 閉じる、調べる、上げる
  highlight: steps[0]
```

### cause-chain(因果の連鎖)

| 項目 | 必須 | 内容 |
|---|---|---|
| `chain` | 必須 | 原因から結果への順の配列(2つ以上)。名前が style.yaml の色の対象と同じなら、その色の枠と文字で描く |
| `link` | 任意 | 矢印のラベル。既定は「ので」 |
| `example` | 任意 | 図の下の1行(架空の例など) |
| `highlight` | 任意 | `chain[番号]` |

収容量: 4つまで(箱の幅の下限 160px)。1つは、3つなら約40字、4つなら約30字まで。

### pie-chart(円グラフ)

| 項目 | 必須 | 内容 |
|---|---|---|
| `data` | 必須 | `{label, value, bound}` の配列。`label` は style.yaml の色の対象の名前にする(ないと灰色で描き、警告) |
| `data[].value` | 必須 | 事実のID(事実の `value` を使う)、または `{fact: ID, as: 数, round: 桁}`。1つの事実が複数の値を述べるときに `as` で選ぶ。`as` の数は事実の statement、quote、qualifiers にあること。`round` で丸め、値が変われば「約」を付ける |
| `data[].bound` | 任意 | 値の後ろに付ける語(以上、未満など) |
| `highlight` | 任意 | `label` の1つ |

単位が % の場合、合計が95から105に入らなければエラー。円に出ないほど小さい値(1.5度未満)には「細すぎて円に出ない」と添える。

収容量: 5項目まで。ラベルは約14字まで(値と合わせて凡例が1行)。色相は1枚に4つまで(style.yaml)なので、色の付く項目は実質4つまで。

```yaml
  data:
  - {label: 侵害に至った攻撃, value: F207}
  - {label: 攻撃の試み, value: {fact: F207, as: 27}, bound: 以上}
  - {label: 分類できないもの, value: {fact: F207, as: 23.72, round: 0}}
```

### table(表)

| 項目 | 必須 | 内容 |
|---|---|---|
| `columns` | 必須 | 列の名前の配列。列は文字列か `{name, align}`(`left`、`right`) |
| `rows` | 必須 | 行の配列。行はセルの配列(列と同じ数)。セルは文字列(`{F...}` の参照を含めてよい)か、事実のIDだけ |
| `highlight` | 任意 | `columns[番号]`、`rows[番号]`、`cells[行][列]` |

全てのセルが事実の参照で始まる列は、右に寄せる。

収容量(行の数、列の数を問わず1セル1行のとき): セルが約10字までなら8行(5列では5行)。約16字なら5行、約24字なら4行、約40字なら3列で4行。

### tree(階層の木)

| 項目 | 必須 | 内容 |
|---|---|---|
| `root` | 必須 | 根の名前 |
| `children` | 必須 | 子の配列。子は文字列か `{name, children}` |
| `levels` | 任意 | 階層ごとの見出し(1つ目が根の子の列) |
| `aside` | 任意 | 木の右に置く説明 `{mark: 案, text}`。案なら破線の枠 |
| `highlight` | 任意 | 節の名前(木の中で1つだけのもの) |

収容量: 葉(子のない節)が6つまで。名前は約12字まで(長いと列の幅が広がり、`aside` の幅が足りなくなる)。階層は3段まで(根を含む)を目安とする。

### flowchart(分岐のある流れ)

仕組みの定義の場面(`route` のつながり)から描く。

| 項目 | 必須 | 内容 |
|---|---|---|
| `scenario` | 必須 | 場面のID |
| `start` | 任意 | 始まりの要素。既定は場面の最初のつながりの `from` |
| `labels` | 任意 | 図に載せる短い名前。要素は `ID: 名前`。つながりは `ID: {condition: 分かれ目の問い, label: 行き先の札}`。`\n` で改行を指定できる |
| `proposal_parts` | 任意 | 案の部分のつながり。定義の `proposal` が空でないつながりも案として描く(紫の破線と「案の基準」) |
| `highlight` | 任意 | つながりか要素のID、または `{ids: [ID, ...], label: 枠の上の語}`(隣り合う分かれ目をまとめて1つの枠で囲む) |

描き方: 始まりから出る道を `order` の順に、分かれ目(ひし形)として左から右に並べる。「はい」の行き先は下に出す。最後の道は「いいえ」として次の要素に進む。その要素から出る道は2つまで描ける。1つ目は右(条件の札を通って行き先へ)、2つ目は下。これより深い流れは描けない(診断に出る)。

収容量: 始まりから出る道は、分かれ目の問いが約10字(5字の2行)、行き先の札が約18字(9字の2行)なら4つまで(ひし形3つ)。問いが約8字以上を1行にすると3つまで。

### er-diagram(要素の関係)、architecture-diagram(構成図)

仕組みの定義の要素とつながりを引き、graphviz で置く。

| 項目 | 必須 | 内容 |
|---|---|---|
| `elements` | 必須 | 要素のID。立証設計の `view` にあるものだけ |
| `relations` | 必須 | つながりのID。両端が `elements` にあること |
| `labels` | 任意 | 短い名前(要素、つながり)。つながりを `''` にするとラベルなし |
| `annotations` | 任意 | `要素ID: 文`。要素のすぐ下に添える |
| `details` | 任意 | `要素ID: [項目]`。要素の中に一覧で描く |
| `direction` | 任意 | `LR`(既定、左から右)か `TB`(上から下) |
| `groups` | 任意(構成図だけ) | `{title, elements, caption, direction}` の配列。群どうしがつながらなければ、群ごとに置いて横に並べる |
| `highlight` | 任意 | 要素かつながりのID。構成図では `groups[番号]` も |

描き方:

- 流れのつながり(send、produce、notify、aggregate、route、retrieve)は矢印。retrieve は、データが来る向きに描く。そのほか(query、contain、example_of など)は矢印のない線とラベル。
- 構成図では、contain は含む側を枠にして、含まれる側を中に置く。
- どのつながりにも出ない要素は、図から離して右に置き、「経路は出典にない」と添える(style.yaml の「線なし」)。

収容量: 左から右に1列につなぐ場合、名前が約4字なら4つ、約8字以上なら3つまで。それより長い連なりは `direction: TB` にする。1つから出る枝は4つから5つまで。構成図の群は2つ(つながらない要素の列を足して3列)まで。

### 描けないもの、診断

`build/diagnostics.json` と標準出力に、スライドごとに出す。

| 種類 | 内容 |
|---|---|
| `overflow` | 枠や領域に収まらない文字、図の幅や高さの超過、見出しが3行、結論1行が2行、語の途中での改行(警告) |
| `font-too-small` | 文字の大きさが style.yaml の下限より小さい |
| `overlap` | 図形どうし、図形と文字の重なり(入れ子と、自分の枠の中の文字は除く) |
| `unrendered` | 描けなかった内容(参照先がない、書式の誤り、型の描画がない) |
| `hue-count`、`contrast` | 1枚の色相の数、色と白地の差 |
| `placeholder` | スライド仕様がない、または保留(情報)。立証設計から仮置きを描く |

`wraps` に、折り返した位置(図の中の文字)を記録する。

