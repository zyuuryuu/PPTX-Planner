# 章の作業票: ch2

PMが上流の成果物から `trial/deck/work/make_tickets.py` で機械的に抜き出した。要約していない。正本は各成果物。

## 担当の範囲

成果物: `trial/deck/07-slides/ch2.yaml`(スライドの配列。順はストーリーラインの順)。

| スライド | 型 | 扱い |
|---|---|---|
| ch2-s1 | er-diagram | 型の見本(承認済み)。PMが `06-samples/er-diagram.yaml` をそのまま入れる。書き直さない |
| ch2-s2 | architecture-diagram | 執筆する |
| ch2-s3 | architecture-diagram | 型の見本(承認済み)。PMが `06-samples/architecture-diagram.yaml` をそのまま入れる。書き直さない |
| ch2-s4 | plain-list | 執筆する |
| ch2-s5 | tree | 型の見本(承認済み)。PMが `06-samples/tree.yaml` をそのまま入れる。書き直さない |
| ch2-s6 | pie-chart | 型の見本(承認済み)。PMが `06-samples/pie-chart.yaml` をそのまま入れる。書き直さない |
| ch2-s7 | statement | 執筆する |
| ch2-s8 | cause-chain | 型の見本(承認済み)。PMが `06-samples/cause-chain.yaml` をそのまま入れる。書き直さない |
| ch2-s9 | plain-list | 執筆する |

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
id: ch2
kind: body
title: アラートは本物の攻撃とは限らない
message: アラートは本物の攻撃とは限らない。1つのSOCのネットワークの検知の実測では、侵害に至らなかった攻撃の試みと想定内の検知が多くを占めた
claims:
- C1
slides: 11
slides_reason: 新人は SIEM、EDR、ログの見方、攻撃の手口の分類を知らず(ブリーフ)、誤検知と想定内の検知のパターンも依頼者が残すよう求めたため、多く充てる。ログの種類(Q1.2)と攻撃の手口の分類(Q1.3)は、C1 の問い Q1 の子として、この章で扱う
```

## 章の主張(`02-claims.yaml`)

資料の answer と summary:

```yaml
answer: 新人が、届いたアラートを、根拠とログから誤検知、想定内の検知、攻撃の疑いの3つに分け、影響の大きさで優先度を付けたうえで、閉じる、調べる、上げるを根拠とともに1人で決められる
summary: アラートは、誤検知、想定内の検知、攻撃の疑いの3つに分ける。根拠をもって誤検知か想定内と言えるものだけを記録して閉じ、迷ったら上げる。
```

```yaml
- id: C1
  statement: アラートは、SIEMやEDRが検知の条件に合うイベントを見つけて出す知らせであり、本物の攻撃とは限らない。誤検知の割合は出典の定義と数え方で大きく割れている。1つの実在のSOCのネットワークの検知(Zeek)のアラートの実測(2020年12月〜2022年7月)では、侵害に至った攻撃に関連するアラートは0.01%で、侵害に至らなかった攻撃の試みが27%以上、想定内の検知が49%以上、分類できないものが約24%だった。誤検知(出典の言い方)の原因として、NISTはネットワーク型の検知の弱いシグネチャ(2003年の文書)や、異常検知型での学習期間に観測されなかった保守作業を挙げ、実務者の一部は緩く書かれたシグネチャを挙げる
  question: Q1
  evidence:
  - F100
  - F101
  - F619
  - F207
  - F208
  - F210
  - F214
  - F215
  - F216
  - F221
  objections:
  - objection: 届くアラートの8割は誤検知なので、誤検知の見分け方を覚えれば足りるのではないか
    response: 公開資料のうち8割に近い値は、ベンダーの調査で解析者がアラートの83%を「誤検知で時間をかける価値がない」と答えた自己申告だけで、誤検知と想定内の検知を区別していない。1つの実在のSOCの実測では、侵害に至らなかった攻撃の試みが27%以上あり、これは誤検知でも想定内の検知でもない
    evidence:
    - F204
    - F207
  - objection: 環境を知らない新人は、何を根拠に「想定内の検知」と言って閉じるのか
    response: 想定内の検知は、組織の環境で業務上正当と説明できるものであり、定期的な社内のスキャンのように攻撃と似た振る舞いをするものもある。依頼者は、新人が想定内の検知として閉じてよいのを、リーダーが事前に一覧にした想定内の活動に当てはまるものだけとする運用に同意した(設計セッションが示した案に、自分のSOCの運用に近いとして同意したもの)
    evidence:
    - F220
    - F215
    - F002
```

## 章の前提と到達点(`04-chapter-states.yaml`)

```yaml
chapter: ch2
entry:
  terms:
  - アラート
  - 誤検知
  - 想定内の検知
  accepted: []
  open_questions:
  - アラートとは何か
exit:
  terms:
  - イベント
  - ログ
  - SIEM
  - EDR
  - ATT&CK
  - 攻撃の試み
  accepted:
  - C1
  answered:
  - アラートとは何か
  open_questions:
  - 1件のアラートをどう扱うのか
```

## スライドごとの見出しと立証の設計(`04-storyline.yaml`、`05-proof.yaml`)

見出し(`headline`)は1文字も変えずに写す。`source` は出典の行として道具が描く(仕様には書かない)。使ってよい事実は、立証の設計の `facts` だけ。

### ch2-s1

型: `er-diagram`

```yaml
# ストーリーライン
id: ch2-s1
chapter: ch2
section: null
question: アラートとは何か
headline: アラートは、検知の仕組みが探すものを見つけたときの知らせで、本物の攻撃とは限らない
from:
- Q1.1
evidence:
- F709
- F619
- F207
source: Microsoft Learn(Microsoft Sentinel、Microsoft Defender for Endpoint の文書、2026年)、Yangら(USENIX Security 2024)。1つのSOCのネットワークの検知(Zeek)の2020年12月〜2022年7月のアラート約1,443万件を著者らが分類
# 立証の設計
id: ch2-s1
relation: entity-relation
show: '製品の例(Microsoft Sentinel)の3つのつながり: データソースがデータを集める、分析ルールが集めたデータに問い合わせる、ルールがアラートを生成する。図の下に1行で「1つのSOCのネットワークの検知の実測では、侵害に至った攻撃に関連するアラートは0.01%(ch2-s6で詳しく)」'
focus: アラートは、ルールが探すものを見つけたときに出す知らせであること
real: true
view:
  elements:
  - E-sentinel-source
  - D-sentinel-data
  - E-sentinel-rule
  - D-sentinel-alert
  relations:
  - R-sentinel-source-data
  - R-sentinel-rule-data
  - R-sentinel-rule-alert
facts:
- F709
- F619
- F207
axis: null
base: none
holds:
- connected
```

### ch2-s2

型: `architecture-diagram`

```yaml
# ストーリーライン
id: ch2-s2
chapter: ch2
section: null
question: SIEMは何を根拠にアラートを出すのか
headline: SIEMは、最も一般的にはルールで複数のログの記録値を照合し、重要なイベントを特定する
from:
- Q1.1.1
evidence:
- F100
- F101
source: NIST SP 800-92(2006年)。ルール以外の相関もある
# 立証の設計
id: ch2-s2
relation: architecture
show: ログの発生源がSIEMのサーバへログを送り(エージェントなしで発生源が送る場合の例)、サーバが全てのログ源のデータを分析して相関させ、重要と判断されたイベント(まだアラートではない)を特定する。サーバの中の注記に「相関で最も一般的なのはルール(ログ管理ソフトウェア一般の記述)」
focus: 複数のログをまとめて相関させるところ
real: true
view:
  elements:
  - E-log-source
  - E-siem-server
  - D-significant-event
  relations:
  - R-source-server-push
  - R-server-significant
facts:
- F100
- F101
axis: null
base: none
holds:
- connected
```

### ch2-s3

型: `architecture-diagram`

```yaml
# ストーリーライン
id: ch2-s3
chapter: ch2
section: null
question: EDRは何を根拠にアラートを出すのか
headline: EDRは端末の振る舞いの記録を継続して集め、製品の例では脅威を検知するとアラートを作る
from:
- Q1.1.1
evidence:
- F615
- F618
- F619
source: 米国 OMB の覚書 M-22-01(2021年)、サウジアラビア国家サイバーセキュリティ庁(NCA)のEDR標準のひな形、Microsoft Learn(Microsoft Defender for Endpoint の文書、2026年)
# 立証の設計
id: ch2-s3
relation: architecture
show: '2つの枠。左: EDRの要件の例(NCA)で、端末→エージェント→中央のデータベースと、記録を集める流れ。右: 製品の例(Microsoft Defender for Endpoint)で、製品がセンサーを持つことと、製品がアラートを作ること。右の枠の外に、製品が集める振る舞いのテレメトリの種類(プロセス、ネットワーク、ログオン、レジストリとファイルの変更)を一覧で添える。テレメトリと製品、アラートの間には矢印を描かず、「経路は出典にない」と注記する'
focus: EDRは端末の振る舞いを継続して集め、製品は脅威を検知するとアラートを作ること(2つをつなぐ経路は示さない)
real: true
view:
  elements:
  - E-endpoint
  - E-edr-agent
  - E-edr-central-db
  - E-mde
  - E-mde-sensor
  - D-mde-telemetry
  - D-mde-alert
  relations:
  - R-endpoint-agent
  - R-agent-central-db
  - R-mde-sensor
  - R-mde-alert
facts:
- F615
- F618
- F619
- F616
axis: null
base: none
holds:
- connected
```

### ch2-s4

型: `plain-list`

```yaml
# ストーリーライン
id: ch2-s4
chapter: ch2
section: null
question: アラートを確かめるには、どのログを見ればよいのか
headline: アラートの詳細はOSのログで確かめることが多く、認証のログは通常、接続元と成否を残す
from:
- Q1.2
evidence:
- F111
- F108
- F110
- F107
source: NIST SP 800-92(2006年)。「しばしば」「通常は」の記述
# 立証の設計
id: ch2-s4
relation: list
show: '2つのログと、そこから分かること: OSのログ(不審な活動の詳細。セキュリティソフトが見つけた後に参照されることが多い)、認証のログ(試行ごとの接続元、利用者、成否、日時を通常は記録する)'
focus: アラートの詳細を確かめる先としてOSのログが多く使われること
facts:
- F111
- F108
- F110
- F107
axis: null
base: none
holds: []
relation_reason: 見る先の2つのログを、それぞれ何が分かるかとともに挙げる。量の比較ではない
```

### ch2-s5

型: `tree`

```yaml
# ストーリーライン
id: ch2-s5
chapter: ch2
section: null
question: 攻撃の手口の分類(ATT&CK)は、一次解析で何に使うのか
headline: 案として、ATT&CKの戦術で、アラートの活動が攻撃のどの段階かを表し、優先度の材料にする
from:
- Q1.3
evidence:
- F114
- F116
- F125
- F610
source: MITRE ATT&CK 公式サイト(v20.1、2026年)、NIST SP 800-61 Rev.3(2025年。インシデントのリスク評価の要因に「観測された活動の段階」)から組み立てた案
# 立証の設計
id: ch2-s5
relation: structure
show: ATT&CKの戦術(なぜ)と技術(どのように)の2層と、架空のアラートの活動を1つの戦術に当てはめた例。当てはめた戦術から、優先度の要因「活動の段階」へ矢印(案)
focus: アラートの活動を戦術に当てはめると、攻撃のどの段階かを言えること
facts:
- F114
- F116
- F125
- F610
axis: null
base: none
holds:
- hierarchical
- connected
```

### ch2-s6

型: `pie-chart`

```yaml
# ストーリーライン
id: ch2-s6
chapter: ch2
section: null
question: 届くアラートのうち、本物の攻撃はどれだけあるのか
headline: 1つのSOCの実測では、侵害に至った攻撃は0.01%、攻撃の試みは27%以上、想定内は49%以上
from:
- Q1.1.3
evidence:
- F207
source: Yangら(USENIX Security 2024)。1つのSOCのネットワークの検知(Zeek)の2020年12月〜2022年7月のアラート約1,443万件を著者らが分類
# 立証の設計
id: ch2-s6
relation: composition
show: 1つのSOCのアラートの内訳を1本の帯で示す。侵害に至った攻撃0.01%、攻撃の試み27%以上、想定内の検知49%以上、分類できないもの約24%。27%と49%が下限であることを帯に書く
focus: 誤検知でも想定内でもない攻撃の試みの帯(27%以上)
facts:
- F207
axis: アラートが何によるものか(著者らの分類)
base: none
holds:
- partition
- proportional
```

### ch2-s7

型: `statement`

```yaml
# ストーリーライン
id: ch2-s7
chapter: ch2
section: null
question: 届くアラートの8割は誤検知ではないのか
headline: 「8割が誤検知」に近い値は、調べた範囲ではベンダーの調査の自己申告(83%)だけだった
from:
- Q1.1.3
evidence:
- F204
- F220
objection:
  claim: C1
  index: 0
source: Vectra AI の調査(2023年、解析者2,000人の回答)。「誤検知」の定義は示されていない
# 立証の設計
id: ch2-s7
relation: statement
show: '「83%」の値と、その条件の注記: ベンダーの調査、解析者の自己申告、「誤検知」の定義が示されていない。別の出典では誤検知と想定内の検知を分けて定義していることを1行で添える'
focus: 調べた範囲で8割に近い値はこの自己申告の1つだけで、その「誤検知」の定義も示されていないこと
facts:
- F204
- F220
axis: null
base: none
holds: []
relation_reason: 1つの値(83%)と、その値の条件を示すスライドで、比べる対象や順序がない
```

### ch2-s8

型: `cause-chain`

```yaml
# ストーリーライン
id: ch2-s8
chapter: ch2
section: null
question: 誤検知はなぜ起きるのか
headline: 誤検知の原因には、弱いルールや緩く書かれたルールなど、検知の条件の誤りがある
from:
- Q1.1.4
evidence:
- F208
- F214
source: NIST の文書(2003年、ネットワーク型の検知)、Alahmadiら(USENIX Security 2022、一部の解析者の認識)。原文の語は signature
# 立証の設計
id: ch2-s8
relation: causality
show: 緩く書かれた(弱い)検知のルール→無害な通信にも合ってしまう→誤検知、のつながり。ルールの書き方の例を架空で添える
focus: 原因が検知の条件の側にあること
facts:
- F208
- F214
axis: null
base: none
holds:
- causal
- ordered
```

### ch2-s9

型: `plain-list`

```yaml
# ストーリーライン
id: ch2-s9
chapter: ch2
section: null
question: 想定内の検知はなぜ起きるのか
headline: 1つのSOCの実測では、社内の脆弱性スキャンや外部の診断が想定内の検知を起こしていた
from:
- Q1.1.4
evidence:
- F215
- F221
source: Yangら(USENIX Security 2024)。1つのSOCのネットワークの検知(Zeek)の2020年12月〜2022年7月のアラート約1,443万件を著者らが分類
# 立証の設計
id: ch2-s9
relation: list
relation_reason: 原因の例を挙げるスライドで、例の間に順序、比較の観点、全体を分ける関係がない
show: '1つのSOCの実測で、想定内の検知を起こした業務上正当な活動の2例: 定期の内部の脆弱性スキャン、外部のベンダーによる診断(ペネトレーションテスト)'
focus: どちらも業務上正当な活動で、ルールは正しく反応していること
facts:
- F215
- F221
axis: null
base: none
holds: []
```

## 前後の章の見出し

### ch1 この講義で身につけること

- ch1-s1: 重大度 High 以上はまず上げ、残りを3つに分けて、閉じる・調べる・上げるを決める
- ch1-s2: 根拠をもって誤検知か想定内と言えるものだけを記録して閉じ、迷ったら上げる

### ch3 1件のアラートの扱い方

- ch3-s1: 何から確かめるかは出典で食い違い、NISTは確認を、民間の解説は優先付けを判定より先に置く
- ch3-s2: 閉じる・調べる・上げるの線は調べた公的な文書になく、この講義の線は案とこのSOCの運用である
- ch3-s3: 案として、重大度で上げるものを除いた後、根拠とログで3つに分け、影響で優先度を付ける
- ch3-s4: 案として、アラートを出したルールの条件と、含まれる利用者や端末を、元のログと照らす
- ch3-s5: 案として、検知の条件かデータの誤りで出たと根拠をもって言えるときだけ、誤検知として閉じる
- ch3-s6: このSOCでは、新人が想定内の検知として閉じてよいのは、リーダーの一覧にある活動だけ
- ch3-s7: 案として、優先度は製品の重大度だけでなく、資産の重要度、影響、活動の段階で付ける
- ch3-s9: 案として、閉じるときは、発火した内容、調べたこと、証拠、下した判断を記録する
- ch3-s10: このSOCでは、新人が閉じたアラートは後で見直される
- ch3-s11: このSOCでは、配属から3か月の新人の持ち時間は1件30分で、過ぎたら見たことを付けて上げる
- ch3-s16: このSOCでは、製品の重大度が High 以上のアラートは30分を待たずにすぐ上げる
- ch3-s12: 案として、重要な資産での疑い、横展開の証拠、守備範囲の超過のどれかなら上げる
- ch3-s13: このSOCでは、30分調べても閉じる根拠がなく迷うなら、閉じずに上げる
- ch3-s14: このSOCでは、配属から3か月の新人は攻撃の試みも全て上げ、溢れたらリーダーが対処する
- ch3-s15: 案として、上げるときは、出どころとID、調べた経過、証拠、判定の仮説、次の手順を添える
- ch3-s17: 配属から3か月の新人は、重大度 High 以上か攻撃の試みなら上げ、一覧なら閉じ、残りは調べる

## この章のスライドが使う事実(`01-sources.yaml`、`incoming/`)

```yaml
- id: F709
  statement: Microsoft Sentinel は、組織の全体からデータを集めた後、定期的に実行される脅威検知のルール(分析ルール)で、集めたデータに問い合わせて分析する。ルールは探しているものを見つけるとアラートを生成する。アラートは関わる実体(利用者、端末、アドレスなど)を含み、集約と相関によってインシデントにまとめられる
  kind: fact
  source: Microsoft Learn, Threat detection in Microsoft Sentinel
  locator: https://learn.microsoft.com/en-us/azure/sentinel/threat-detection  冒頭の本文
  as_of: 2026-05-14
  quote: After setting up Microsoft Sentinel to collect data from all over your organization, you need to constantly dig through all that data to detect security threats to your environment. To accomplish this task, Microsoft Sentinel provides threat detection rules that run regularly, querying the collected data and analyzing it to discover threats. These rules come in a few different flavors and are collectively known as analytics rules. These rules generate alerts when they find what they’re looking for. Alerts contain information about the events detected, such as the entities (users, devices, addresses, and other items) involved. Alerts are aggregated and correlated into incidents—case files—that you can assign and investigate to learn the full extent of the detected threat and respond accordingly.
  qualifiers:
  - 製品の定義(Microsoft Sentinel)
  - 文書の適用範囲は Microsoft Sentinel in the Microsoft Defender portal と Microsoft Sentinel in the Azure portal(Applies to)
  - 同じページの冒頭に、新しいルールの作成には custom detections が最良の方法になったとの注記がある
  origin: Microsoft(製品の公式文書)
  answers: []
  verified: true
  collected_verified: false
  request: R7
  stance:
    H1: neutral
    H2: neutral
    H3: neutral
- id: F619
  statement: Microsoft Defender for Endpoint では、脅威を検知するとアラートが作られ、同じ攻撃の手法や同じ攻撃者によるアラートはインシデントにまとめられる。検知の機能は端末の全ての操作を記録する監査やログの仕組みではなく、センサーには同じ事象の大量の繰り返しを間引く仕組みがある
  kind: fact
  source: Microsoft Learn, Overview of endpoint detection and response capabilities - Microsoft Defender for Endpoint
  locator: https://learn.microsoft.com/en-us/defender-endpoint/overview-endpoint-detection-response  本文と Note
  as_of: 2026-06-02
  quote: When a threat is detected, alerts are created in the system for an analyst to investigate. Alerts with the same attack techniques or attributed to the same attacker are aggregated into an entity called an incident. [...] Defender for Endpoint detection is not intended to be an auditing or logging solution that records every operation or activity that happens on a given endpoint. Our sensor has an internal throttling mechanism, so the high rate of repeat identical events don't flood the logs.
  qualifiers:
  - 製品の定義(Microsoft Defender for Endpoint)
  - 文書の適用範囲は Microsoft Defender for Endpoint Plans 1 and 2 と Microsoft Defender XDR(Applies to)
  - '[...] は収集セッションによる省略'
  origin: Microsoft(製品の公式文書)
  answers:
  - Q1.1.1
  verified: true
  collected_verified: false
  request: R6
  stance:
    H1: neutral
    H2: neutral
    H3: neutral
- id: F207
  statement: 実SOCの実測では、アラートのうち真の攻撃に関連するのは0.01%。攻撃の試み(侵害に至らなかった攻撃)が27%、正当な業務上の理由がある「良性のトリガー」が49%を占めた
  value: 0.01
  unit: '%'
  kind: fact
  source: Yang et al., 'True Attacks, Attack Attempts, or Benign Triggers? An Empirical Measurement of Network Alerts in a Security Operations Center' (USENIX Security 2024)
  locator: https://par.nsf.gov/servlets/purl/10530815 Abstract
  as_of: '2024'
  metric: 真の攻撃に関連するアラートの割合
  superseded_by: null
  quote: Through analysis, we observe that SOC analysts are facing excessive alerts (24K–134K per day), but only a small percentage of the alerts (0.01%) are associated with true attacks. While the majority of true attacks can be detected within the same day, the post-attack investigation takes much longer time (53 days on average). Furthermore, we observe a significant portion of the alerts are related to “attack attempts” (attacks that did not lead to true compromises, 27%), and “benign triggers” (correctly matched security events but had business-justified explanations, 49%).
  qualifiers:
  - 1つのSOC
  - 割合は表4の期間(2020-12〜2022-07、14,429,534件)のもの
  - 27%と49%は下限(論文は『at least』と述べる。良性のトリガーは明確な証拠があるものだけを数えた)
  - 分類不能(Unknown)が23.72%残る
  - 「攻撃の試み」は侵害に至らなかった攻撃、「良性のトリガー」は正しく一致したが業務上の説明があるセキュリティ事象と定義されている
  origin: 同SOCのZeekアラートログ(著者らが実測)
  answers:
  - Q1.1.3
  - Q1.1.4
  verified: true
  collected_verified: false
  request: R2
  stance:
    H1: neutral
    H2: neutral
    H3: neutral
- id: F100
  statement: SIEMは、複数のログ源のデータを分析し、ログ項目間でイベントを相関させ、重要なイベントを特定して優先順位を付ける
  kind: fact
  source: NIST SP 800-92 Guide to Computer Security Log Management
  locator: https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-92.pdf 3.4 Security Information and Event Management Software
  as_of: 2006-09
  quote: Regardless of how it receives log data (through agents or an agentless method), an SIEM server analyzes the data from all the different log sources, correlates events among the log entries, identifies and prioritizes significant events, and initiates responses to events if desired.
  qualifiers:
  - 2006年版
  - 応答の開始は「必要な場合」
  - SP 800-92 は CSRC のページで Final(2006-09)。撤回の表示なし(確認日 2026-11-23)
  - 優先順位付けは一部のSIEM製品の機能。脚注37に 'Some SIEM products can prioritize events based on correlating events with other sources of information, such as the result of vulnerability scans.' とある
  origin: NIST SP 800-92
  answers:
  - Q1.1.1
  verified: true
  collected_verified: false
  request: R1
  stance:
    H1: neutral
    H2: neutral
    H3: neutral
- id: F101
  statement: ログのイベント相関で最も一般的なのは、タイムスタンプ、IPアドレス、イベント種別などの記録値に基づいて複数のログ項目を照合するルールベース相関である
  kind: fact
  source: NIST SP 800-92 Guide to Computer Security Log Management
  locator: https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-92.pdf 3.2 Functions(Analysis)
  as_of: 2006-09
  quote: Event correlation is finding relationships between two or more log entries. The most common form of event correlation is rule-based correlation, which matches multiple log entries from a single source or multiple sources based on logged values, such as timestamps, IP addresses, and event types.
  qualifiers:
  - 2006年版
  - ログ管理ソフトウェア一般の機能として記述
  - SP 800-92 は CSRC のページで Final(2006-09)。撤回の表示なし(確認日 2026-11-23)
  - 同じ節に 'Event correlation can also be performed in other ways, such as using statistical methods or visualization tools.' とあり、ルール以外の相関もある
  origin: NIST SP 800-92
  answers:
  - Q1.1.1
  verified: true
  collected_verified: false
  request: R1
  stance:
    H1: neutral
    H2: neutral
    H3: neutral
- id: F615
  statement: 米国 OMB の覚書 M-22-01 は、EDRを、端末のデータのリアルタイムで継続的な監視と収集に、ルールに基づく自動の対応と分析の機能を組み合わせたものと説明している
  kind: fact
  source: OMB Memorandum M-22-01, Improving Detection of Cybersecurity Vulnerabilities and Incidents on Federal Government Systems through Endpoint Detection and Response
  locator: https://bidenwhitehouse.archives.gov/wp-content/uploads/2021/10/M-22-01.pdf  p.1 "Endpoint Detection and Response"
  as_of: 2021-10-08
  quote: EDR combines real-time continuous monitoring and collection of endpoint data (for example, networked computing devices such as workstations, mobile phones, servers) with rules-based automated response and analysis capabilities.
  qualifiers:
  - 米国連邦政府機関向けの覚書
  - 国防総省と情報機関は対象外(覚書の脚注2)
  - 原文 PDF では rules- と based が行末で分かれている。ハイフンは語の一部として残した
  origin: 米国 行政管理予算局(OMB)
  answers:
  - Q1.1.1
  verified: true
  collected_verified: false
  request: R6
  stance:
    H1: neutral
    H2: neutral
    H3: neutral
- id: F618
  statement: Microsoft Defender for Endpoint は、プロセスの情報、ネットワークの活動、カーネルとメモリ管理の深い観測、利用者のログオンの活動、レジストリとファイルシステムの変更などの振る舞いのテレメトリを継続的に集め、6か月保存する
  kind: fact
  value: 6
  unit: か月
  metric: EDRのテレメトリの保存期間
  source: Microsoft Learn, Overview of endpoint detection and response capabilities - Microsoft Defender for Endpoint
  locator: https://learn.microsoft.com/en-us/defender-endpoint/overview-endpoint-detection-response  本文
  as_of: 2026-06-02
  quote: Inspired by the "assume breach" mindset, Defender for Endpoint continuously collects behavioral cyber telemetry. This includes process information, network activities, deep optics into the kernel and memory manager, user login activities, registry and file system changes, and others. The information is stored for six months, enabling an analyst to travel back in time to the start of an attack.
  qualifiers:
  - 製品の定義(Microsoft Defender for Endpoint)
  - 文書の適用範囲は Microsoft Defender for Endpoint Plans 1 and 2 と Microsoft Defender XDR(Applies to)
  origin: Microsoft(製品の公式文書)
  answers:
  - Q1.1.1
  verified: true
  collected_verified: false
  request: R6
  stance:
    H1: neutral
    H2: neutral
    H3: neutral
- id: F616
  statement: サウジアラビア国家サイバーセキュリティ庁(NCA)のEDR標準のひな形は、EDRのエージェントが、プロセス、接続、活動量、データの転送などの端末のデータを中央のデータベースに集め、収集するデータにプロセス、接続、ファイル、ドライバ、自動起動、システム、マシン、利用者の領域を含めることを求めている
  kind: fact
  source: National Cybersecurity Authority (Saudi Arabia), Endpoint Detection and Response Standard Template
  locator: https://cdn.nca.gov.sa/api/files/public/upload/e0790c91-e283-4349-995b-eca0639bb989_Standard_EDR_Template_en_.pdf  2 Data Collection and Monitoring, Objective と 2-6, 2-7 (下端の番号 p.6-7、PDF の7-8ページ目)
  as_of: 2023-11
  quote: 'Objective: EDR software agents must properly monitor and collect endpoint data, such as processes, connections, volume of activity and data transfers into a central database. [...] 2-6 EDR solution must collect and monitor relevant data to build a complete picture of endpoint activity. 2-7 Relevant data for EDR solution must include information covering the following areas: Processes, Connections, Files, Drivers, Autorun, System, Machine, Users. Additional data sources may be used, including but not limited to: logs, performance monitoring, file details, running processes, and configuration data.'
  qualifiers:
  - 組織が自組織に合わせて直して使う例示のひな形(文書の Disclaimer)
  - 版 1.0
  - as_of は PDF の作成日
  - '[...] は収集セッションによる省略'
  - 「Objective:」と項番(2-6、2-7)は表の左列の見出しと番号で、収集セッションが右列の本文の先頭に置いて連結した。行 2-7 は Relevant data ... から configuration data. までの1つの行
  - 2-7 の箇条(原文は「•」付き)をコンマで連結した
  origin: サウジアラビア 国家サイバーセキュリティ庁(NCA)
  answers:
  - Q1.1.1
  verified: true
  collected_verified: false
  request: R6
  stance:
    H1: neutral
    H2: neutral
    H3: neutral
- id: F111
  statement: OSログは、特定のホストに関する不審な活動の特定と調査に最も役立つ。セキュリティソフトが不審な活動を見つけた後に、詳細を得るために参照されることが多い
  kind: fact
  source: NIST SP 800-92 Guide to Computer Security Log Management
  locator: https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-92.pdf 2.1.2 Operating Systems
  as_of: 2006-09
  quote: OS logs are most beneficial for identifying or investigating suspicious activity involving a particular host. After suspicious activity is identified by security software, OS logs are often consulted to get more information on the activity.
  qualifiers:
  - 2006年版
  - 「しばしば」(often)の記述
  - SP 800-92 は CSRC のページで Final(2006-09)。撤回の表示なし(確認日 2026-11-23)
  origin: NIST SP 800-92
  answers:
  - Q1.2
  verified: true
  collected_verified: false
  request: R1
  stance:
    H1: neutral
    H2: neutral
    H3: neutral
- id: F108
  statement: 認証サーバのログは、認証の試行ごとに、接続元、ユーザー名、成否、日時を記録する
  kind: fact
  source: NIST SP 800-92 Guide to Computer Security Log Management
  locator: https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-92.pdf 2.1.1 Security Software(Authentication Servers)
  as_of: 2006-09
  quote: Authentication servers, including directory servers and single sign-on servers, typically log each authentication attempt, including its origin, username, success or failure, and date and time.
  qualifiers:
  - 2006年版
  - 「通常は」(typically)の記述
  - ディレクトリサーバとシングルサインオンサーバを含む
  - SP 800-92 は CSRC のページで Final(2006-09)。撤回の表示なし(確認日 2026-11-23)
  origin: NIST SP 800-92
  answers:
  - Q1.2
  verified: true
  collected_verified: false
  request: R1
  stance:
    H1: neutral
    H2: neutral
    H3: neutral
- id: F110
  statement: OSの監査記録は、認証の成功と失敗、ファイルアクセス、セキュリティポリシーの変更、アカウントの変更、権限の使用などのセキュリティ事象の情報を含む
  kind: fact
  source: NIST SP 800-92 Guide to Computer Security Log Management
  locator: https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-92.pdf 2.1.2 Operating Systems(Audit Records)
  as_of: 2006-09
  quote: Audit records contain security event information such as successful and failed authentication attempts, file accesses, security policy changes, account changes (e.g., account creation and deletion, account privilege assignment), and use of privileges.
  qualifiers:
  - 原文は 'such as'(例示であり、全てではない)
  - 2006年版
  - 記録する事象の種類は管理者が指定できる(OSによる)
  - SP 800-92 は CSRC のページで Final(2006-09)。撤回の表示なし(確認日 2026-11-23)
  origin: NIST SP 800-92
  answers:
  - Q1.2
  verified: true
  collected_verified: false
  request: R1
  stance:
    H1: neutral
    H2: neutral
    H3: neutral
- id: F107
  statement: マルウェア対策ソフトの最も一般的な形であるウイルス対策ソフトは、通常、検出した全てのマルウェア、駆除の試み、隔離を記録する
  kind: fact
  source: NIST SP 800-92 Guide to Computer Security Log Management
  locator: https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-92.pdf 2.1.1 Security Software(Antimalware Software)
  as_of: 2006-09
  quote: The most common form of antimalware software is antivirus software, which typically records all instances of detected malware, file and system disinfection attempts, and file quarantines.
  qualifiers:
  - 記録する主体は、マルウェア対策ソフト全般ではなく、その最も一般的な形であるウイルス対策ソフト(antivirus software)
  - 2006年版
  - 「通常は」(typically)の記述
  - SP 800-92 は CSRC のページで Final(2006-09)。撤回の表示なし(確認日 2026-11-23)
  origin: NIST SP 800-92
  answers:
  - Q1.2
  verified: true
  collected_verified: false
  request: R1
  stance:
    H1: neutral
    H2: neutral
    H3: neutral
- id: F114
  statement: MITRE ATT&CKは、実世界の観測に基づく攻撃者の戦術と技術の、世界中から利用できる知識ベースである
  kind: fact
  source: MITRE ATT&CK 公式サイト(トップページ)
  locator: https://attack.mitre.org/ 冒頭の説明文
  as_of: 2026-10(ATT&CK v20.1。Version History ページでの現行版。取得時点)
  quote: MITRE ATT&CK® is a globally-accessible knowledge base of adversary tactics and techniques based on real-world observations.
  qualifiers:
  - 取得時点の現行版 v20.1
  - 日付は Version History ページの「October 13, 2026 - current」
  origin: MITRE ATT&CK
  answers:
  - Q1.3
  verified: true
  collected_verified: false
  request: R1
  stance:
    H1: neutral
    H2: neutral
    H3: neutral
- id: F116
  statement: ATT&CKでは、戦術は ATT&CK の技術または副技術の「なぜ」を表す
  kind: fact
  source: MITRE ATT&CK FAQ
  locator: https://attack.mitre.org/resources/faq/ 見出し "What are tactics?" / "What are techniques?"
  as_of: 2026-10(取得時点。ページに日付なし)
  quote: Tactics represent the “why” of an ATT&CK technique or sub-technique.
  qualifiers:
  - 取得時点の版
  origin: MITRE ATT&CK
  answers:
  - Q1.3
  verified: true
  collected_verified: false
  request: R1
  stance:
    H1: neutral
    H2: neutral
    H3: neutral
- id: F125
  statement: ATT&CKでは、技術は、攻撃者が行動を実行して戦術上の目的を達成する「どのように」を表す
  kind: fact
  source: MITRE ATT&CK FAQ
  locator: https://attack.mitre.org/resources/faq/ 見出し "What are techniques?"
  as_of: 2026-11-23取得(ページに日付なし)
  quote: Techniques represent “how” an adversary achieves a tactical goal by performing an action.
  qualifiers:
  - 取得時点の版
  origin: MITRE ATT&CK
  answers:
  - Q1.3
  verified: true
  collected_verified: false
  request: R1
  stance:
    H1: neutral
    H2: neutral
    H3: neutral
- id: F610
  statement: NIST SP 800-61 Rev.3 は、インシデントのトリアージ、優先度付け、エスカレーション、上位への引き上げ、復旧を始める判断を、一連のリスク評価の要因に基づかせるよう推奨し、要因の例として、資産の重要度、機能への影響、データへの影響、観測された活動の段階、脅威主体の特徴、回復可能性を挙げている
  kind: fact
  source: NIST SP 800-61 Rev. 3
  locator: https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r3.pdf  3.2節 Table 3, RS.MA (Incident Management) R2, N2 (p.26-27)
  as_of: 2025-04
  quote: 'R2: Incident triage, prioritization, escalation, and elevation and decisions regarding when to initiate recovery processes should all be based on a set of risk evaluation factors. This set can range from simple to incredibly complex, depending on the needs and maturity of an organization. N2: Examples of possible risk evaluation factors include asset criticality, functional impact of the incident, data impact of the incident, stage of observed activity, threat actor characterization, and recoverability.'
  qualifiers:
  - CSF 2.0 Community Profile の推奨事項と注記
  - 要因は例示
  - 要因の組み合わせは組織の必要と成熟度による
  origin: NIST
  answers:
  - Q3.3.1
  verified: true
  collected_verified: false
  request: R6
  stance:
    H1: neutral
    H2: supports
    H3: neutral
- id: F204
  statement: 業界調査(ベンダーのVectra)では、解析者は受けるアラートの67%に対応できず、アラートの83%が誤検知で時間をかける価値がないと答えた
  value: 83
  unit: '%'
  kind: fact
  source: Vectra AI, 2023 State of Threat Detection
  locator: https://www.vectra.ai/resources/research-reports/2023-state-of-threat-detection (ページ本文) / Methodology
  as_of: '2023'
  metric: 誤検知の割合
  superseded_by: null
  quote: On average, security analysts are unable to deal with over two-thirds (67%) of the daily alerts they receive . What’s more, they say 83% of these alerts are false positives and not worth their time .
  qualifiers:
  - ベンダーの調査。宣伝目的を含むため一次情報として扱わない
  - 解析者の自己申告(測定値ではない)
  - 「誤検知」の定義は示されていない(下のF205・F207は、この語に正当な検知を含めうることを示す)
  - Sapio Research(Vectra委託)の2023年3〜4月の調査。対象は従業員1,000人超の組織のIT security analysts 2,000人(米英仏独伊など。出典 Methodology)
  origin: Vectra AI の調査(2023)
  answers:
  - Q1.1.3
  verified: true
  collected_verified: false
  request: R2
  stance:
    H1: supports
    H2: neutral
    H3: neutral
- id: F220
  statement: Yangらは、良性のトリガーを『組織の環境における業務上正当で許容される挙動によって説明される、正しく発火したアラート』と定義し、一般的な『誤検知』(良性の挙動に対して誤って発火したアラート。悪い規則・エラー・誤設定による等)とは異なると述べる
  kind: fact
  source: Yang et al., 'True Attacks, Attack Attempts, or Benign Triggers? An Empirical Measurement of Network Alerts in a Security Operations Center' (USENIX Security 2024)
  locator: https://par.nsf.gov/servlets/purl/10530815 §6.2 Benign Triggers
  as_of: '2024'
  superseded_by: null
  quote: Alerts that are neither “true attacks” nor “attack attempts” cannot be simply marked as false positives (FP). Many of them can be benign triggers. Benign triggers [4] are correctly fired alerts, explained by business-justified, acceptable behaviors in the organization’s environment. As such, analysts may choose to ignore them. An example would be an alert fired correctly because a weak SSL key is detected, but SOC can ignore the alert knowing the host is retiring and disconnected from the public network. This definition is different from the generic “false positives” which usually refer to alerts that are incorrectly fired on benign behaviors (e.g., due to bad rules, errors, or misconfigurations).
  qualifiers:
  - 論文中の用語の定義
  origin: Yang ら(論文内の定義。[4]=Alahmadi らを引用)
  answers:
  - Q1.1.3
  - Q1.1.4
  verified: true
  collected_verified: false
  request: R2
  stance:
    H1: neutral
    H2: neutral
    H3: neutral
- id: F208
  statement: NISTの文書は、誤検知を『通常の非悪性の背景トラフィックで起きたアラート』と定義し、ネットワークIDSでの原因に、弱いシグネチャ、正当なネットワーク管理ツールのトラフィックを挙げる。誤検知率はネットワーク環境ごとに異なることがある
  kind: fact
  source: NIST ITL Bulletin 'Testing Intrusion Detection Systems' (2003-07)
  locator: https://csrc.nist.gov/files/pubs/shared/itlb/itlbul2003-07.pdf p.1-2 (Probability of False Alarms。引用はp.1末尾からp.2先頭へ改ページをまたぐ)
  as_of: 2003-07
  superseded_by: null
  quote: A false positive or false alarm is an alert caused by normal non-malicious background traffic. Some causes for Network IDS (NIDS) include weak signatures that alert on all traffic to a high-numbered port used by a backdoor; search for the occurrence of a common word such as help in the first 100 bytes of SNMP or other TCP connections; or detection of common violations of the TCP protocol. They can also be caused by normal network monitoring and maintenance traffic generated by network management tools. It is difficult to measure false alarms because an IDS may have a different false positive rate in each network environment, and there is no such thing as a standard network.
  qualifiers:
  - NIDS(ネットワーク型IDS)について
  - 2003年の文書
  - 「標準的なネットワークはない」ため、誤検知の測定は難しいとされている
  origin: NIST ITL Bulletin (2003-07)
  answers:
  - Q1.1.4
  verified: true
  collected_verified: false
  request: R2
  stance:
    H1: supports
    H2: neutral
    H3: neutral
- id: F214
  statement: SOC実務者の一部は、シグネチャが『緩く(広く)書かれている』ことで多くの誤検知が出ると述べた
  kind: fact
  source: 'Alahmadi, Axon, Martinovic, ''99% False Positives: A Qualitative Study of SOC Analysts'' Perspectives on Security Alarms'' (USENIX Security 2022)'
  locator: 'https://www.usenix.org/conference/usenixsecurity22/presentation/alahmadi (全文: https://ora.ox.ac.uk/objects/uuid%3A0be05f6b-7470-4210-acb6-2018d5dc6ca0/files/rsj139244b) 節 ''Reported by Interviewees'' 内の ''Unreliable signature'''
  as_of: 2022-08
  superseded_by: null
  quote: Some analysts reported that signatures are “loosely written”, meaning written to be general to capture a variety of activities. This results in a high volume of FPs,
  qualifiers:
  - インタビュー参加者の一部(『Some analysts』)の認識(定性)
  origin: 著者らのインタビュー(n=21)
  answers:
  - Q1.1.4
  verified: true
  collected_verified: false
  request: R2
  stance:
    H1: supports
    H2: neutral
    H3: neutral
- id: F215
  statement: 同SOCで、定期的な内部スキャン(脆弱性・設定不備の確認)は、悪性のスキャンと似た振る舞いをするが、アラートは無視してよい良性のトリガーの共通の原因の1つだった
  kind: fact
  source: Yang et al., 'True Attacks, Attack Attempts, or Benign Triggers? An Empirical Measurement of Network Alerts in a Security Operations Center' (USENIX Security 2024)
  locator: https://par.nsf.gov/servlets/purl/10530815 §6.4 Understanding Benign Triggers (Table 7)
  as_of: '2024'
  superseded_by: null
  quote: The first common cause of benign triggers is scheduled internal scanning to proactively check for vulnerabilities and misconfigurations. These scans have similar behavior patterns as malicious scans, but the alerts can be safely ignored.
  qualifiers:
  - 1つのSOC
  - 本文は『最初の一般的な原因』と述べる
  origin: 同SOCのZeekアラートログ(著者らが実測)
  answers:
  - Q1.1.4
  verified: true
  collected_verified: false
  request: R2
  stance:
    H1: supports
    H2: neutral
    H3: neutral
- id: F221
  statement: 同SOCで、第三者のセキュリティベンダーによる外部のペネトレーションテストと年次の監査に対応するアラートが約270万件あった。うち92%は2022年前半のLog4j関連だった
  value: 2.7
  unit: 百万件
  kind: fact
  source: Yang et al., 'True Attacks, Attack Attempts, or Benign Triggers? An Empirical Measurement of Network Alerts in a Security Operations Center' (USENIX Security 2024)
  locator: https://par.nsf.gov/servlets/purl/10530815 §6.4 External Pen Test
  as_of: '2024'
  metric: 外部ペンテストに起因する良性のトリガーの件数
  superseded_by: null
  quote: The SOC also worked with third-party (external) security vendors to perform penetration tests and the annual compliance auditing. The corresponding alerts are identified based on known vendor IPs (2.7 million alerts). While the external scanners have triggered varied types of alerts such as address scan, port scan, and vulnerability scan, the majority (92%) are related to Log4j in early 2022.
  qualifiers:
  - 1つのSOC
  - 既知のベンダーIPで識別
  - 92%はLog4j関連(2022年前半)
  origin: 同SOCのZeekアラートログ(著者らが実測)
  answers:
  - Q1.1.4
  verified: true
  collected_verified: false
  request: R2
  stance:
    H1: supports
    H2: neutral
    H3: neutral
```

## 仕組みの定義の該当する部分(`01-model.yaml`)

```yaml
# 仕組みの定義(調査依頼 R7。収集セッションが作成)
# 範囲: (1) SIEM がログの発生源からアラートを出すまで、(2) EDR が端末の記録を集め、検知し、アラートとインシデントにするまで。
# 出典は4系統。混ぜずに、要素とつながりを出典の系統ごとに分けて登録した。
#   - SIEM の一般の記述: NIST SP 800-92(2006年版)
#   - SIEM の製品の例: Microsoft Sentinel(note に製品名)
#   - EDR の一般の記述: OMB M-22-01、NCA の EDR 標準のひな形(要件の文書で、製品の動作の記述ではない)
#   - EDR の製品の例: Microsoft Defender for Endpoint、Symantec EDR(note に製品名)
# evidence の F7xx は trial/deck/incoming/R7.yaml の事実(verified: false)。それ以外は 01-sources.yaml の verified: true の事実。
#
# 種類の語:
#   要素 kind: component(部品・製品) / actor(人) / data(データ)
#   つながり kind:
#     send(データが from から to へ渡る) / retrieve(from が to からデータを取りに行く)
#     contain(from が to を含む、または to が from の上に置かれる) / example_of(from は to の種類の例)
#     produce(from が to を作る) / query(from が to に問い合わせて分析する) / aggregate(from が to にまとめられる)
#     notify(from が to に知らせる) / investigate(from が to を調べる)
#     store_in(from のログの保存先が to である。経路や転送は表さない) / based_on(from が to を基にする)
#   basis: description(出典が仕組みを記述している) / requirement(標準の要件・ひな形の「〜しなければならない」) / product(特定の製品の記述)
#     / operation(依頼者のSOCの運用。依頼者の証言 F002〜F009。工程5で設計セッションが足した)
#   要素 kind に action(新人の行き先: 閉じる、調べる、上げる)を、つながり kind に route(from の状態から、condition のとき to の行き先へ進む)を足した(工程5)
#   order: 同じ from から出る route を確かめる順(1から。最初に当たった道に進む。F007)
#   proposal: そのつながりのうち、依頼者の運用ではなく、この講義の案(D001、D008)である部分。空なら全て運用
#   mode: 送り方(push / pull / リアルタイムなど)。condition: つながりが成り立つ条件。書かれていないものは unknown。
#
# 出典で裏付けられず、つながりを登録しなかった箇所(図では途切れとして示す必要がある):
#   - SIEM(NIST SP 800-92): エージェント型で、ログの発生源の中のログがエージェントに渡る経路と方式。
#   - SIEM(NIST SP 800-92): SIEMサーバからデータベースサーバへログが渡る経路(R-server-db は保存先を表すだけ)。
#   - SIEM(NIST SP 800-92): SIEM 自身がアラートを生成すること。アラートの生成は、ログ管理基盤の記述(F705)にだけあり、
#     主体を「SIEM を基にしたログ管理基盤」(E-siem-infra。SIEM を基にするのは typically)とした。SIEM の場面は、重要なイベントの特定で終える。
#   - SIEM(NIST SP 800-92): アラートを受け取る人や画面。3.1 の第3層(コンソール)はログ管理基盤一般の記述で、アラートを受け取るとは書かれていない。
#   - EDR(NCA): 中央のデータベースから、脅威のパターンを識別する分析への経路。
#   - EDR(NCA): EDR のエージェントが端末の上で動くこと(「エージェント型で導入する」とだけある)。端末からエージェントへの段の送り方。
#   - EDR(NCA)から SIEM への経路。NCA の 4-2(F708)は SIEM などとの統合と共有を求めるが、向きと内容を書いていない。
#   - EDR(NCA): インシデント。NCA のひな形には、検知や通知をインシデントにまとめる記述がない。
#   - EDR(Microsoft Defender for Endpoint): テレメトリがどこからどこへ集められるか(出典は集める主体だけを書く)。
#     集めたテレメトリが検知に使われる経路、テレメトリの保存場所、センサーの置き場所。
#   - EDR(Microsoft Defender for Endpoint)から Microsoft Sentinel への経路。F711 の「ほかの Microsoft のセキュリティ製品」に Defender for Endpoint が含まれるとは、読んだ出典に書かれていない。
elements:
- id: E-sentinel-source
  basis: product
  kind: component
  name: データソース(data sources)
  evidence:
  - F712
  note: Microsoft Sentinel。例として Microsoft Entra ID、Azure Activity、Azure Storage
- id: D-sentinel-data
  basis: product
  kind: data
  name: 集めたデータ(collected data)
  evidence:
  - F709
  note: Microsoft Sentinel
- id: E-sentinel-rule
  basis: product
  kind: component
  name: 分析ルール(analytics rules)
  evidence:
  - F709
  - F710
  note: Microsoft Sentinel。最も一般的な種類はスケジュールされたルール(Scheduled rules)
- id: D-sentinel-alert
  basis: product
  kind: data
  name: アラート(alerts)
  evidence:
  - F709
  - F710
  note: Microsoft Sentinel。関わる実体(利用者、端末、アドレスなど)を含む
- id: E-log-source
  basis: description
  kind: component
  name: ログの発生源(log generators、log generating hosts、log sources)
  evidence:
  - F700
  - F701
  - F702
  - F703
  - F704
- id: E-siem-server
  basis: description
  kind: component
  name: SIEMサーバ(SIEM server、log servers)
  evidence:
  - F701
  - F702
  - F100
  functions:
  - 事象の絞り込みと集約、ログの正規化(エージェントなしの場合。F702)
  - 分析(analysis。F701、F702、F100)
  - 事象の相関(correlates events。F100、F101)
  - 重要なイベントの特定(identifies significant events。F100)
  - 重要なイベントの優先順位付け(prioritizes。F100。脚注37によると一部のSIEM製品(some SIEM products)の機能)
- id: D-significant-event
  basis: description
  kind: data
  name: 重要なイベント(significant events)
  evidence:
  - F100
- id: E-endpoint
  basis: description
  kind: component
  name: 端末(endpoints)
  evidence:
  - F615
  - F616
  - F714
  note: 例として OMB はワークステーション、携帯電話、サーバ(F615)。Microsoft Defender for Endpoint の文書はノートPC、電話、タブレット、PC、アクセスポイント、ルータ、ファイアウォール(F714)
- id: E-edr-agent
  basis: requirement
  kind: component
  name: EDRのエージェント(EDR software agents)
  evidence:
  - F616
  - F706
- id: E-edr-central-db
  basis: requirement
  kind: component
  name: 中央のデータベース(central database)
  evidence:
  - F616
- id: E-mde
  basis: product
  kind: component
  name: Microsoft Defender for Endpoint
  evidence:
  - F714
  - F618
  - F619
  note: Microsoft Defender for Endpoint
- id: E-mde-sensor
  basis: product
  kind: component
  name: センサー(sensor)
  evidence:
  - F619
  attributes:
    throttling: 同じ事象の大量の繰り返しを間引く仕組みを持つ(F619)
    location: unknown
  note: Microsoft Defender for Endpoint
- id: D-mde-telemetry
  basis: product
  kind: data
  name: 振る舞いのテレメトリ(behavioral cyber telemetry)
  evidence:
  - F618
  attributes:
    retention: 6か月(F618)
    storage_location: unknown
  note: Microsoft Defender for Endpoint。プロセスの情報、ネットワークの活動、カーネルとメモリ管理の観測、利用者のログオンの活動、レジストリとファイルシステムの変更など
- id: D-mde-alert
  basis: product
  kind: data
  name: アラート(alerts)
  evidence:
  - F619
  note: Microsoft Defender for Endpoint
relations:
- id: R-sentinel-source-data
  basis: product
  kind: send
  from: E-sentinel-source
  to: D-sentinel-data
  label: データを集める(データコネクタ、CEF、Syslog、REST API)
  mode: 多くのデータコネクタはリアルタイムの連携(F712)。そのほかは unknown
  condition: unknown
  evidence:
  - F712
  - F709
  note: Microsoft Sentinel
- id: R-sentinel-rule-data
  basis: product
  kind: query
  from: E-sentinel-rule
  to: D-sentinel-data
  label: 集めたデータに問い合わせて分析する
  mode: 定期的に実行(run regularly)。スケジュールされたルールは一定の間隔で、定めた遡りの期間の生データを調べる
  condition: unknown
  evidence:
  - F709
  - F710
  note: Microsoft Sentinel
- id: R-sentinel-rule-alert
  basis: product
  kind: produce
  from: E-sentinel-rule
  to: D-sentinel-alert
  label: アラートを生成する
  mode: unknown
  condition: 探しているものを見つけたとき。スケジュールされたルールでは、問い合わせの結果の件数が閾値を超えたとき
  evidence:
  - F709
  - F710
  note: Microsoft Sentinel
- id: R-source-server-push
  basis: description
  kind: send
  from: E-log-source
  to: E-siem-server
  label: ホストがログ(D-log-data)を送る(push)
  data: D-log-data
  mode: push。通常はホストがサーバに認証して定期的に送る(usually)
  condition: エージェントなしの場合
  evidence:
  - F702
- id: R-server-significant
  basis: description
  kind: produce
  from: E-siem-server
  to: D-significant-event
  label: 全てのログ源のデータを分析し、事象を相関させ、重要なイベントを特定して優先順位を付ける
  mode: unknown
  condition: エージェント型、エージェントなしのどちらで受け取った場合も(regardless of how it receives log data)
  evidence:
  - F100
  - F101
  note: F100 の脚注によると、優先順位付けは一部の SIEM 製品の機能。相関で最も一般的なのはルールに基づく相関(F101。ログ管理ソフトウェア一般の記述)
- id: R-endpoint-agent
  basis: requirement
  kind: retrieve
  from: E-edr-agent
  to: E-endpoint
  label: エージェントが端末のデータ(D-endpoint-data)を監視して集める
  data: D-endpoint-data
  mode: unknown
  condition: unknown
  evidence:
  - F616
  note: NCA の要件(must)。エージェントが端末の上で動くかは書かれていない
- id: R-agent-central-db
  basis: requirement
  kind: send
  from: E-edr-agent
  to: E-edr-central-db
  label: 端末のデータを中央のデータベースに集める
  data: D-endpoint-data
  mode: unknown
  condition: unknown
  evidence:
  - F616
  note: NCA の要件(must)
- id: R-mde-sensor
  basis: product
  kind: contain
  from: E-mde
  to: E-mde-sensor
  label: Defender for Endpoint のセンサー(our sensor)
  mode: unknown
  condition: unknown
  evidence:
  - F619
  note: Microsoft Defender for Endpoint
- id: R-mde-alert
  basis: product
  kind: produce
  from: E-mde
  to: D-mde-alert
  label: アラートを作る
  mode: unknown
  condition: 脅威を検知したとき
  evidence:
  - F619
  note: Microsoft Defender for Endpoint
scenarios: []
```

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
  - id: T-escalate
    term: 上げる
    kind: action
    definition: アラートを、経過と証拠を添えて上位の担当者に引き継ぐ
    note: 依頼者が決めた3つの行き先の1つ。ブリーフの「上に上げる」と同じ
    defined_in: ch1-s1
    no_definition: null
  - id: T-event
    term: イベント
    kind: noun
    definition: システムやネットワークで起きた出来事そのもの。良い悪いは問わない。新人はログを見てイベントを知る
    note: 依頼者が決めた(2026-11-23)
    defined_in: ch2-s2
    no_definition: null
    not:
    - T-log
    - T-alert
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
  - id: T-fp-share
    term: 誤検知の割合
    kind: noun
    definition: 届いたアラートのうち、誤検知と判断されたものの割合。出典ごとに数え方が違い、想定内の検知を含む出典がある
    defined_in: null
    no_definition: 素材台帳の metric の照合に使う指標の名前で、スライドの語ではない
  - id: T-true-attack-share
    term: 真の攻撃に関連するアラートの割合
    kind: noun
    definition: アラートのうち、侵害に至った実際の攻撃に関連するものの割合
    defined_in: null
    no_definition: 素材台帳の metric の照合に使う指標の名前で、スライドの語ではない
  - id: T-benign-pentest-count
    term: 外部ペンテストに起因する良性のトリガーの件数
    kind: noun
    definition: 委託した外部のペネトレーションテストや監査が原因で発火したアラートの件数
    defined_in: null
    no_definition: 素材台帳の metric の照合に使う指標の名前で、スライドの語ではない
  - id: T-edr-retention
    term: EDRのテレメトリの保存期間
    kind: noun
    definition: EDRが集めた端末の記録を保存する期間
    defined_in: null
    no_definition: 素材台帳の metric の照合に使う指標の名前で、スライドの語ではない
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
  - id: T-tactic
    term: 戦術
    kind: noun
    definition: ATT&CK で、攻撃者がその行動をとる目的(なぜ)
    not:
    - T-technique
    defined_in: ch2-s5
    no_definition: null
  - id: T-technique
    term: 技術
    kind: noun
    definition: ATT&CK で、攻撃者が目的を達成する方法(どのように)
    not:
    - T-tactic
    defined_in: ch2-s5
    no_definition: null
  - id: T-priority
    term: 優先度
    kind: noun
    definition: 複数のアラートのうち、どれから扱うかの順位
    not:
    - T-severity
    defined_in: ch3-s7
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

### architecture-diagram(`06-samples/architecture-diagram.yaml`、画像は `06-samples/architecture-diagram.png`)

```yaml
# 型の見本のスライド仕様(工程6)。工程7でそのまま使う。
id: ch2-s3
status: done
headline: EDRは端末の振る舞いの記録を継続して集め、製品の例では脅威を検知するとアラートを作る
takeaway: EDRの材料は、端末の振る舞いを集め続けた記録である
body:
  type: architecture-diagram
  elements:
  - E-endpoint
  - E-edr-agent
  - E-edr-central-db
  - E-mde
  - E-mde-sensor
  - D-mde-telemetry
  - D-mde-alert
  relations:
  - R-endpoint-agent
  - R-agent-central-db
  - R-mde-sensor
  - R-mde-alert
  groups:
  - title: EDRの要件の例(NCA)
    elements:
    - E-endpoint
    - E-edr-agent
    - E-edr-central-db
    caption: プロセス、接続、ファイルなどの端末の記録を集める
  - title: 製品の例(Microsoft Defender for Endpoint)
    elements:
    - E-mde
    - E-mde-sensor
    - D-mde-alert
    direction: TB
  labels:
    E-edr-agent: エージェント
    E-mde: Defender for Endpoint
    D-mde-telemetry: 製品が集める記録
    R-endpoint-agent: ''
    R-agent-central-db: ''
    R-mde-alert: 作る
  details:
    D-mde-telemetry:
    - プロセス
    - ネットワーク
    - ログオン
    - レジストリとファイルの変更
  highlight: groups[0]
sources:
- F615
- F616
- F618
- F619
notes: 左は要件の文書、右は製品の文書で、出典が違う。右の記録からアラートへの経路は出典に書かれていないので描かない。
```

### cause-chain(`06-samples/cause-chain.yaml`、画像は `06-samples/cause-chain.png`)

```yaml
# 型の見本のスライド仕様(工程6)。工程7でそのまま使う。
id: ch2-s8
status: done
headline: 誤検知の原因には、弱いルールや緩く書かれたルールなど、検知の条件の誤りがある
takeaway: 誤検知の原因は、活動の側ではなく検知の条件の側にある
body:
  type: cause-chain
  chain:
  - 検知のルールが緩く書かれている
  - 無害な通信にも条件が合ってしまう
  - 誤検知
  example: '架空の例: 「宛先のポートが443」だけを条件にしたルールは、ふつうのWebの閲覧にも合う'
  highlight: chain[0]
sources:
- F208
- F214
notes: NIST の文書は弱いシグネチャを原因に挙げ、実務者の一部は緩く書かれたシグネチャを挙げた。資料では「ルール」と呼ぶ。
```

### er-diagram(`06-samples/er-diagram.yaml`、画像は `06-samples/er-diagram.png`)

```yaml
# 型の見本のスライド仕様(工程6)。工程7でそのまま使う。
id: ch2-s1
status: done
headline: アラートは、検知の仕組みが探すものを見つけたときの知らせで、本物の攻撃とは限らない
takeaway: アラートは「条件に合った」という知らせで、「攻撃だ」という判定ではない
body:
  type: er-diagram
  elements:
  - E-sentinel-source
  - D-sentinel-data
  - E-sentinel-rule
  - D-sentinel-alert
  relations:
  - R-sentinel-source-data
  - R-sentinel-rule-data
  - R-sentinel-rule-alert
  labels:
    R-sentinel-source-data: 集める
    R-sentinel-rule-data: 問い合わせる
    R-sentinel-rule-alert: 生成する
  annotations:
    D-sentinel-alert: ルールが探すものを見つけたときに出る
  highlight: D-sentinel-alert
text: 1つのSOCのネットワークの検知の実測では、侵害に至った攻撃に関連するアラートは {F207}
sources:
- F709
- F619
- F207
notes: 製品の例は Microsoft Sentinel。ほかの製品でも、条件に合うと知らせる点は同じだが、仕組みの細部は製品ごとに違う。内訳は ch2-s6 で示す。
```

### pie-chart(`06-samples/pie-chart.yaml`、画像は `06-samples/pie-chart.png`)

```yaml
# 型の見本のスライド仕様(工程6)。工程7でそのまま使う。
id: ch2-s6
status: done
headline: 1つのSOCの実測では、侵害に至った攻撃は0.01%、攻撃の試みは27%以上、想定内は49%以上
takeaway: 誤検知でも想定内でもない攻撃の試みが、少なくとも4分の1ある
body:
  type: pie-chart
  data:
  - label: 侵害に至った攻撃
    value: F207
  - label: 攻撃の試み
    value:
      fact: F207
      as: 27
    bound: 以上
  - label: 想定内の検知
    value:
      fact: F207
      as: 49
    bound: 以上
  - label: 分類できないもの
    value:
      fact: F207
      as: 23.72
      round: 0
  highlight: 攻撃の試み
sources:
- F207
notes: 27%と49%は論文が「少なくとも」とする下限。想定内の検知は明確な証拠があるものだけを数えた。
```

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

### tree(`06-samples/tree.yaml`、画像は `06-samples/tree.png`)

```yaml
# 型の見本のスライド仕様(工程6)。工程7でそのまま使う。
id: ch2-s5
status: done
headline: 案として、ATT&CKの戦術で、アラートの活動が攻撃のどの段階かを表し、優先度の材料にする
takeaway: 戦術に当てはめると、そのアラートが攻撃のどこにいるかを言える
body:
  type: tree
  root: ATT&CK
  levels:
  - 戦術(なぜ)の例
  - 技術(どのように)の例
  children:
  - 初期アクセス
  - name: 実行
    children:
    - コマンドの実行
  - 横展開
  - 持ち出し
  aside:
    mark: 案
    text: 架空のアラート「見慣れないコマンドが動いた」は戦術「実行」に当たる。これを優先度の要因「活動の段階」に使う
  highlight: 実行
sources:
- F114
- F116
- F125
- F610
notes: 戦術と技術の名前は例示で、ATT&CK の全体ではない。当てはめ方と優先度へのつなぎ方は案。
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

