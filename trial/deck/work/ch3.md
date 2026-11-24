# 章の作業票: ch3

PMが上流の成果物から `trial/deck/work/make_tickets.py` で機械的に抜き出した。要約していない。正本は各成果物。

## 担当の範囲

成果物: `trial/deck/07-slides/ch3.yaml`(スライドの配列。順はストーリーラインの順)。

| スライド | 型 | 扱い |
|---|---|---|
| ch3-s1 | table | 執筆する |
| ch3-s2 | plain-list | 執筆する |
| ch3-s3 | step-flow | 執筆する |
| ch3-s4 | step-flow | 執筆する |
| ch3-s5 | plain-list | 執筆する |
| ch3-s6 | statement | 執筆する |
| ch3-s7 | plain-list | 執筆する |
| ch3-s9 | plain-list | 執筆する |
| ch3-s10 | statement | 執筆する |
| ch3-s11 | statement | 執筆する |
| ch3-s16 | statement | 執筆する |
| ch3-s12 | plain-list | 執筆する |
| ch3-s13 | flowchart | 執筆する |
| ch3-s14 | statement | 執筆する |
| ch3-s15 | plain-list | 型の見本(承認済み)。PMが `06-samples/plain-list.yaml` をそのまま入れる。書き直さない |
| ch3-s17 | flowchart | 型の見本(承認済み)。PMが `06-samples/flowchart.yaml` をそのまま入れる。書き直さない |

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
id: ch3
kind: body
title: 1件のアラートの扱い方
message: 閉じる・調べる・上げるの線は、調べた公的な文書にない。この講義は、3つに分けて根拠があるものだけを閉じ、迷ったら上げる案と、このSOCの運用を示す
claims:
- C2
- C3
slides: 18
slides_reason: 講義の目的そのもので、新人の3つの懸念(何を見ればよいか、閉じるのが怖い、どこまで調べたら上げるか)の全てに答える章のため、最も多く充てる。工程5で、運用を1つの流れにまとめる1枚を足した(依頼者の指示、D009)
```

## 章の主張(`02-claims.yaml`)

資料の answer と summary:

```yaml
answer: 新人が、届いたアラートを、根拠とログから誤検知、想定内の検知、攻撃の疑いの3つに分け、影響の大きさで優先度を付けたうえで、閉じる、調べる、上げるを根拠とともに1人で決められる
summary: アラートは、誤検知、想定内の検知、攻撃の疑いの3つに分ける。根拠をもって誤検知か想定内と言えるものだけを記録して閉じ、迷ったら上げる。
```

```yaml
- id: C2
  statement: 何から確かめるかの順序は出典で食い違う。NIST SP 800-61 Rev.3 は、インシデントの報告について、起きたかの確認を深刻度の見積もりより前に置き、民間の解説は、アラートの優先順位付けを真偽の判定より前に置く。この資料は案として、まずアラートの根拠とログで3つに分け、次に影響の大きさで優先度を付ける順を採る。複数の案件の間は、届いた順ではなく、リスク評価の要因で扱うとNIST Rev.3はインシデントについて述べ、この資料はアラートにも当てはめる
  question: Q2
  evidence:
  - F303
  - F312
  - F305
  - F321
  assumes:
  - インシデントについての NIST の優先順位の考え方は、アラートにも当てはまる
- id: C3
  statement: 閉じる、調べる、上げるの具体的な線は、調べた公的な文書に書かれていなかった。この資料は、線は組織が決めるものとして扱い(D001)、公開資料の材料から組み立てた案として、根拠をもって誤検知か想定内の検知と言えれば調べたことと判断を記録して閉じ、持ち時間の中で決められないとき、重要な資産での疑いがあるとき、複数のホストにまたがる横展開の証拠があるとき、迷うときは、経過と証拠を添えて上げる基準を示す。あわせて、依頼者が同意した運用(新人が閉じてよいのは誤検知と一覧にある想定内の活動だけ)と、依頼者のSOCの運用(攻撃の試みは最初の3か月は全て上げる、閉じたものは後で見直される)を、公開資料とは分けて示す
  question: Q3
  evidence:
  - F600
  - F610
  - F318
  - F406
  - F403
  - F405
  - F413
  - F002
  - F003
  - F004
  assumes:
  - 標準ではない実務者向けの資料の条件を、新人の SOC の基準の案として使う
  objections:
  - objection: 公的な基準がないのに、基準を教えてよいのか
    response: 公的な文書に線がないことを明示し、案として示す。新人の SOC で使えるかは、依頼者が決める(D001)
    evidence:
    - F610
  - objection: 「1人で決められる」とするが、判定には他の担当者との協力が要る場合がある
    response: 撤回済みの NIST SP 800-61 Rev.2 は、インシデントかの判定に協力が要る場合がありうるとしていた。この資料では、持ち時間の中で決められないときや迷うときに上げることまでを、新人が1人で行う判断に含める
    evidence:
    - F401
    - F403
    - F405
  - objection: 侵害に至らなかった攻撃の試み(27%以上)を攻撃の疑いに含めると、上げる条件に当てはめて、その大半が上に上がる
    response: 調べた公開資料には、閉じてよい試みと上げる試みを分ける線がなかった。依頼者のSOCの運用では、配属から最初の3か月の新人には攻撃の試みを全て上げさせ、上が溢れるかはリーダーの側で対処する
    evidence:
    - F207
    - F003
  - objection: 新人が間違って閉じてしまったら、取り返しがつかないのではないか
    response: 依頼者のSOCの運用では、新人が閉じたアラートは、後でリーダーかベテランが見直す。民間の解説は、閉じた全てのアラートに調べたことと判断を記録するとする(見直しの手順は書かれていない)。この資料は、その記録を見直しの材料として使う
    evidence:
    - F004
    - F318
```

## 章の前提と到達点(`04-chapter-states.yaml`)

```yaml
chapter: ch3
entry:
  terms:
  - アラート
  - 誤検知
  - 想定内の検知
  - 閉じる
  - 調べる
  - 上げる
  - ログ
  accepted:
  - C1
  open_questions:
  - 1件のアラートをどう扱うのか
exit:
  terms:
  - 持ち時間
  accepted:
  - C2
  - C3
  answered:
  - 1件のアラートをどう扱うのか
  open_questions:
  - なぜ根拠のあるものだけを閉じるのか
  concerns_answered:
  - 誤検知ばかりで、何を見ればいいか分からない
  - 間違って閉じるのが怖い
  - どこまで調べたら上に上げていいのか分からない
```

## スライドごとの見出しと立証の設計(`04-storyline.yaml`、`05-proof.yaml`)

見出し(`headline`)は1文字も変えずに写す。`source` は出典の行として道具が描く(仕様には書かない)。使ってよい事実は、立証の設計の `facts` だけ。

### ch3-s1

型: `table`

```yaml
# ストーリーライン
id: ch3-s1
chapter: ch3
section: null
question: 1件のアラートは何から確かめるのか
headline: 何から確かめるかは出典で食い違い、NISTは確認を、民間の解説は優先付けを判定より先に置く
from:
- Q2.2
evidence:
- F303
- F312
source: NIST SP 800-61 Rev.3(2025年。インシデントの報告の扱い)、CyberDefenders(SOC解析者の訓練事業者)の解説(2026年)。標準や公的文書ではない
# 立証の設計
id: ch3-s1
relation: item-comparison
show: '2つの出典の段を横に並べる。NIST SP 800-61 Rev.3(インシデントの報告): 起きたかの確認→インシデントの重さの見積もり。民間の解説(アラート): 取り込み→分類→優先付け→調べる→本物か誤検知かの判定'
focus: NISTは確認が最初で、民間の解説は判定より前に優先付けを置くこと
facts:
- F303
- F312
axis: 出典
base: none
holds:
- comparable
- ordered
```

### ch3-s2

型: `plain-list`

```yaml
# ストーリーライン
id: ch3-s2
chapter: ch3
section: null
question: 閉じる・調べる・上げるの線は、どこに決められているのか
headline: 閉じる・調べる・上げるの線は調べた公的な文書になく、この講義の線は案とこのSOCの運用である
from:
- Q3
evidence:
- F600
- F610
objection:
  claim: C3
  index: 0
source: NIST SP 800-61 Rev.3(2025年)。インシデントの基準は組織が定めるとする
# 立証の設計
id: ch3-s2
relation: list
show: '上に「調べた公的な文書の線: なし」。下に、この講義の線の出どころ2つ: 案(公開資料の材料から組み立てたもの)、このSOCの運用(リーダーが決めたもの)'
focus: 公的な文書の線がないこと
facts:
- F600
- F610
axis: null
base: none
holds: []
relation_reason: この講義の線の出どころ2つを挙げる。1つの線が両方を使うこともあり、全体を漏れなく重なりなく分けるものではない
```

### ch3-s3

型: `step-flow`

```yaml
# ストーリーライン
id: ch3-s3
chapter: ch3
section: null
question: この講義では、どの順で確かめるのか
headline: 案として、重大度で上げるものを除いた後、根拠とログで3つに分け、影響で優先度を付ける
from:
- Q2
evidence:
- F303
- F305
- F009
source: NIST SP 800-61 Rev.3(2025年)と、CyberDefenders(SOC解析者の訓練事業者)の解説(2026年)。標準や公的文書ではない。この2つの材料から組み立てた案
# 立証の設計
id: ch3-s3
relation: process
show: '手順(案): 0. 重大度 High 以上を上げる(このSOCの運用) 1. 根拠とログで3つに分ける 2. 影響の大きさで優先度を付ける'
focus: 分けるのが先で、優先度が後であること
facts:
- F303
- F305
- F009
axis: null
base: none
holds:
- ordered
```

### ch3-s4

型: `step-flow`

```yaml
# ストーリーライン
id: ch3-s4
chapter: ch3
section: null
question: アラートの根拠は、どう確かめるのか
headline: 案として、アラートを出したルールの条件と、含まれる利用者や端末を、元のログと照らす
from:
- Q1.1.1
evidence:
- F709
- F710
source: Microsoft Learn(Microsoft Sentinel の文書、2026年)の、ルールがアラートを出す仕組みから組み立てた案
# 立証の設計
id: ch3-s4
relation: process
show: '根拠の確かめ方の2段(案): 1. アラートを出したルールの条件と、アラートに含まれる利用者や端末を読む 2. それを元のログと照らす'
focus: 元のログと照らすところ
facts:
- F709
- F710
axis: null
base: none
holds:
- ordered
```

### ch3-s5

型: `plain-list`

```yaml
# ストーリーライン
id: ch3-s5
chapter: ch3
section: null
question: 誤検知として閉じてよいのは、どんなときか
headline: 案として、検知の条件かデータの誤りで出たと根拠をもって言えるときだけ、誤検知として閉じる
from:
- Q3.1.1
evidence:
- F605
- F609
- F220
source: Microsoft Learn(Microsoft Sentinel、Microsoft Defender for Endpoint の文書、2026年)、Yangら(2024年)の定義から組み立てた案
# 立証の設計
id: ch3-s5
relation: list
show: '誤検知として閉じてよい理由の2つ(案): 検知の条件の誤り、データの誤り。下に、閉じてはいけない例(根拠を言えないもの)を1行'
focus: 根拠をもって言える2つの理由だけが、誤検知として閉じる理由であること
facts:
- F605
- F609
- F220
axis: null
base: none
holds: []
relation_reason: 誤検知として閉じてよい理由を2つ挙げる(案)。2つの間に順序や重みがない
real: false
```

### ch3-s6

型: `statement`

```yaml
# ストーリーライン
id: ch3-s6
chapter: ch3
section: null
question: 想定内の検知として閉じてよいのは、どんなときか
headline: このSOCでは、新人が想定内の検知として閉じてよいのは、リーダーの一覧にある活動だけ
from:
- Q3.1
evidence:
- F002
- F220
- F215
objection:
  claim: C1
  index: 1
source: このSOCの運用
# 立証の設計
id: ch3-s6
relation: statement
relation_reason: このSOCの運用の規則を1つ述べるスライドで、比べる対象も順序もない
show: 規則の1文と、一覧の例(承認済みのスキャン、委託した診断)
focus: 一覧にあるものだけ、という範囲
facts:
- F002
- F220
- F215
axis: null
base: none
holds: []
```

### ch3-s7

型: `plain-list`

```yaml
# ストーリーライン
id: ch3-s7
chapter: ch3
section: null
question: 優先度は何で付けるのか
headline: 案として、優先度は製品の重大度だけでなく、資産の重要度、影響、活動の段階で付ける
from:
- Q2.1
- Q3.3.1
evidence:
- F610
- F305
- F306
source: NIST SP 800-61 Rev.3(2025年。インシデントのリスク評価の要因の例示)、CyberDefenders(SOC解析者の訓練事業者)の解説(2026年)。標準や公的文書ではない。2つから組み立てた案
# 立証の設計
id: ch3-s7
relation: list
relation_reason: 要因は例示で、要因の間に順序や重みの定めがない(F305)
show: '優先度の要因の例(案): 資産の重要度、機能とデータへの影響、活動の段階を並べる。別の枠に「製品(SIEM、EDR)が付けた重大度は判断の材料(入力)であり、判断の代わりではない」'
focus: 要因で付け、製品の重大度だけで決めないこと
facts:
- F610
- F305
- F306
axis: null
base: none
holds: []
```

### ch3-s9

型: `plain-list`

```yaml
# ストーリーライン
id: ch3-s9
chapter: ch3
section: null
question: 閉じるときに何を残すのか
headline: 案として、閉じるときは、発火した内容、調べたこと、証拠、下した判断を記録する
from:
- Q3.1.2
evidence:
- F318
source: CyberDefenders(SOC解析者の訓練事業者)の解説(2026年)。標準や公的文書ではない
# 立証の設計
id: ch3-s9
relation: list
relation_reason: 記録する項目の一覧で、項目の間に順序や比較の関係がない
show: '閉じるときに記録する4項目(案): 発火した内容、調べたこと、見つかった証拠、下した判断。記録の書式の形で並べる'
focus: 4項目そろえて残すこと
facts:
- F318
axis: null
base: none
holds: []
```

### ch3-s10

型: `statement`

```yaml
# ストーリーライン
id: ch3-s10
chapter: ch3
section: null
question: 間違って閉じたら、取り返しがつかないのではないか
headline: このSOCでは、新人が閉じたアラートは後で見直される
from:
- Q3.1
evidence:
- F004
- F318
objection:
  claim: C3
  index: 3
source: このSOCの運用
# 立証の設計
id: ch3-s10
relation: statement
relation_reason: このSOCの運用の規則を1つ述べるスライドで、比べる対象も順序もない
show: 規則の1文
focus: 閉じたものは後で見直される
facts:
- F004
- F318
axis: null
base: none
holds: []
```

### ch3-s11

型: `statement`

```yaml
# ストーリーライン
id: ch3-s11
chapter: ch3
section: null
question: どこまで調べたら上げてよいのか
headline: このSOCでは、配属から3か月の新人の持ち時間は1件30分で、過ぎたら見たことを付けて上げる
from:
- Q3.2
evidence:
- F005
- F403
source: 'このSOCの運用(測った値ではなく、外の目安より長めに取った)。参考: Decryption Digest の解説記事(2026年)は一次解析で12〜20分とする'
# 立証の設計
id: ch3-s11
relation: statement
show: このSOCの運用の規則の1文(配属から3か月の新人、1件30分、過ぎたら見たことを付けて上げる)
focus: 30分という区切り
facts:
- F005
- F403
axis: null
base: none
holds: []
relation_reason: このSOCの運用の規則を1つ述べるスライドで、比べる対象も順序もない。運用の流れ図は仕組みの定義にないため、図にしない
```

### ch3-s16

型: `statement`

```yaml
# ストーリーライン
id: ch3-s16
chapter: ch3
section: null
question: 30分を待たずに上げるのは、どんなときか
headline: このSOCでは、製品の重大度が High 以上のアラートは30分を待たずにすぐ上げる
from:
- Q3.3
evidence:
- F005
- F009
source: このSOCの運用
# 立証の設計
id: ch3-s16
relation: statement
relation_reason: このSOCの運用の規則を1つ述べるスライドで、比べる対象も順序もない
show: このSOCの運用の規則の1文(製品が付けた重大度が High 以上のアラートは30分を待たずにすぐ上げる)
focus: 30分を待たないこと
facts:
- F005
- F009
axis: null
base: none
holds: []
```

### ch3-s12

型: `plain-list`

```yaml
# ストーリーライン
id: ch3-s12
chapter: ch3
section: null
question: どんなときに上げるのか
headline: 案として、重要な資産での疑い、横展開の証拠、守備範囲の超過のどれかなら上げる
from:
- Q3.3.1
evidence:
- F406
- F407
source: Decryption Digest の解説記事(2026年)、Security Scientist の解説(日付なし)。どちらも標準や公的文書ではない
# 立証の設計
id: ch3-s12
relation: list
relation_reason: 条件はどれか1つで足りる並列のもので、順序や重みがない
show: '上げる条件の3つ(案): 重要な資産での疑い、複数の端末にまたがる横展開の証拠、自分の守備範囲を超える'
focus: どれか1つで上げる
facts:
- F406
- F407
axis: null
base: none
holds: []
```

### ch3-s13

型: `flowchart`

```yaml
# ストーリーライン
id: ch3-s13
chapter: ch3
section: null
question: 迷ったときは、どうするのか
headline: このSOCでは、30分調べても閉じる根拠がなく迷うなら、閉じずに上げる
from:
- Q3.3.1
evidence:
- F005
- F006
- F405
objection:
  claim: C3
  index: 1
source: このSOCの運用。有志の手順書(SOC-SOP「Escalation Matrix」、2026年)も、判断に迷うときは上げる側に倒すとする
# 立証の設計
id: ch3-s13
relation: branching-flow
show: 'S-newbie-ops のうち、調べる(30分まで)から出る2つの道だけを描く: 誤検知と根拠をもって言えた→誤検知として記録して閉じる(案の基準)、30分たっても根拠がない→見たことを付けて上げる'
focus: 根拠がなければ閉じない側に倒すこと
facts:
- F005
- F006
- F405
axis: null
base: none
holds:
- ordered
- connected
real: true
view:
  scenario: S-newbie-ops
  start: A-investigate
  elements:
  - A-investigate
  - A-close
  - A-escalate
```

### ch3-s14

型: `statement`

```yaml
# ストーリーライン
id: ch3-s14
chapter: ch3
section: null
question: 攻撃の試みは閉じてよいのか。全て上げたら溢れないか
headline: このSOCでは、配属から3か月の新人は攻撃の試みも全て上げ、溢れたらリーダーが対処する
from:
- Q3.3
evidence:
- F003
- F207
objection:
  claim: C3
  index: 2
source: このSOCの運用
# 立証の設計
id: ch3-s14
relation: statement
relation_reason: このSOCの運用の規則を1つ述べるスライドで、比べる対象も順序もない
show: 規則の1文と、溢れたときはリーダーが対処することの1文
focus: 配属から3か月は全て上げる
facts:
- F003
- F207
axis: null
base: none
holds: []
```

### ch3-s15

型: `plain-list`

```yaml
# ストーリーライン
id: ch3-s15
chapter: ch3
section: null
question: 上げるときに何を添えるのか
headline: 案として、上げるときは、出どころとID、調べた経過、証拠、判定の仮説、次の手順を添える
from:
- Q3.3.3
evidence:
- F413
- F414
source: Decryption Digest の解説記事(2026年)、Security Scientist の解説(日付なし)。どちらも標準や公的文書ではない
# 立証の設計
id: ch3-s15
relation: list
relation_reason: 添える項目の一覧で、項目の間に順序や比較の関係がない
show: '上げるときに添える5項目(案): 出どころとID、調べた経過、証拠、判定の仮説、次の手順。引き継ぎの書式の形で並べる'
focus: 5項目そろえて渡すこと
facts:
- F413
- F414
axis: null
base: none
holds: []
```

### ch3-s17

型: `flowchart`

```yaml
# ストーリーライン
id: ch3-s17
chapter: ch3
section: null
question: 1件のアラートを受けたら、新人はどう動くのか
headline: 配属から3か月の新人は、重大度 High 以上か攻撃の試みなら上げ、一覧なら閉じ、残りは調べる
from:
- Q2
- Q3
evidence:
- F002
- F003
- F005
- F006
- F007
- F009
source: このSOCの運用(上げる条件から順に確かめる)。調べる中で誤検知と言える基準は案
# 立証の設計
id: ch3-s17
relation: branching-flow
show: 'このSOCの運用の流れ図。新人に届いたアラートを上から順に確かめる: 1 製品の重大度が High 以上→すぐ上げる、2 攻撃の試み→上げる、3 一覧にある→想定内の検知として記録して閉じる、4 どれでもない→調べる(30分まで)。調べる中で、誤検知と根拠をもって言えた→誤検知として記録して閉じる(この分かれ目に「案」の印)、30分たっても根拠がない→見たことを付けて上げる。図の上に「配属から3か月の新人」'
focus: 上げる条件を先に確かめ、閉じるのは一覧にあるか、調べて誤検知と言えたときだけであること
real: true
view:
  scenario: S-newbie-ops
  elements:
  - D-op-alert
  - A-close
  - A-investigate
  - A-escalate
facts:
- F002
- F003
- F005
- F006
- F007
- F008
- F009
axis: null
base: none
holds:
- ordered
- connected
```

## 前後の章の見出し

### ch2 アラートは本物の攻撃とは限らない

- ch2-s1: アラートは、検知の仕組みが探すものを見つけたときの知らせで、本物の攻撃とは限らない
- ch2-s2: SIEMは、最も一般的にはルールで複数のログの記録値を照合し、重要なイベントを特定する
- ch2-s3: EDRは端末の振る舞いの記録を継続して集め、製品の例では脅威を検知するとアラートを作る
- ch2-s4: アラートの詳細はOSのログで確かめることが多く、認証のログは通常、接続元と成否を残す
- ch2-s5: 案として、ATT&CKの戦術で、アラートの活動が攻撃のどの段階かを表し、優先度の材料にする
- ch2-s6: 1つのSOCの実測では、侵害に至った攻撃は0.01%、攻撃の試みは27%以上、想定内は49%以上
- ch2-s7: 「8割が誤検知」に近い値は、調べた範囲ではベンダーの調査の自己申告(83%)だけだった
- ch2-s8: 誤検知の原因には、弱いルールや緩く書かれたルールなど、検知の条件の誤りがある
- ch2-s9: 1つのSOCの実測では、社内の脆弱性スキャンや外部の診断が想定内の検知を起こしていた

### ch4 誤りやすい点

- ch4-s1: 2013年のTargetの侵害では、緊急のアラートが出たが対応がなかったと報告されている
- ch4-s2: 米上院の報告は、アラートが頻繁だったなら、誤検知とみなされた可能性があると推定する
- ch4-s3: ベンダーの調査では、IT専門職の56%が、過去の誤検知を理由にアラートを無視したと答えた

## この章のスライドが使う事実(`01-sources.yaml`、`incoming/`)

```yaml
- id: F303
  statement: NIST SP 800-61r3 は、新しいインシデント報告に対して、インシデントが起きたかを確かめる予備的な確認を行い、その後に深刻度と対応の緊急度を見積もるとする
  kind: fact
  source: 'NIST SP 800-61 Rev. 3 Incident Response Recommendations and Considerations for Cybersecurity Risk Management: A CSF 2.0 Community Profile'
  locator: https://nvlpubs.nist.gov/nistpubs/specialpublications/nist.sp.800-61r3.pdf Table 3, RS.MA-02 R1
  as_of: 2025-04
  quote: Perform a preliminary review of a new incident report to verify that a cybersecurity incident has occurred, then estimate the severity of the incident and the level of urgency needed to respond to it.
  qualifiers:
  - 対象は「インシデント報告」
  - 優先度の区分は High(推奨の度合い)
  - CSF の要素 RS.MA-02 の説明は "Incident reports are triaged and validated"。R1 の本文に "validated" の語はない
  - 表の R1 の文を写した
  origin: NIST SP 800-61r3
  answers:
  - Q2.1
  - Q2.2
  verified: true
  collected_verified: false
  request: R3
  stance:
    H1: supports
    H2: contradicts
    H3: neutral
- id: F312
  statement: 民間の SOC 向け解説は、アラートのトリアージを一つの判断ではなく、意図的な段階の連なりとし、各段階は前の段階の上に成り立ち、どの段階を飛ばしても誤分類の危険が増すとする
  kind: fact
  source: 'CyberDefenders, Alert Triage Process: The Complete SOC Analyst''s Guide'
  locator: https://cyberdefenders.org/blog/alert-triage-process/ The 7-Stage SOC Alert Triage Process
  as_of: 2026-09-15
  quote: The triage workflow isn't a single decision; it's a sequence of deliberate stages. Each stage builds on the previous one, and skipping any step increases the risk of misclassification.
  qualifiers:
  - 訓練事業者のブログで公的機関・標準ではない
  - '7段階の名称と順序は各段の見出しによる: 1 Alert Ingestion and Centralization、2 Categorization、3 Prioritization、4 Investigation and Evidence Gathering、5 True/False Positive Determination、6 Escalation and Incident Response、7 Documentation and Continuous Improvement'
  - 第4段階の確認項目の順序の厳密な指定はない
  origin: CyberDefenders(独自の解説)
  answers:
  - Q2.2
  verified: true
  collected_verified: false
  request: R3
  stance:
    H1: contradicts
    H2: supports
    H3: neutral
- id: F600
  statement: NIST SP 800-61 Rev.3 は、インシデントを宣言するかを決めるときに、分析した活動の既知の特徴と推定される特徴にインシデントの基準を当てはめ、既知の誤検知を考慮するよう推奨している
  kind: fact
  source: 'NIST SP 800-61 Rev. 3, Incident Response Recommendations and Considerations for Cybersecurity Risk Management: A CSF 2.0 Community Profile'
  locator: https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r3.pdf  3.2節 Table 3, DE.AE-08 (p.26)
  as_of: 2025-04
  quote: 'DE.AE-08 Incidents are declared when adverse events meet the defined incident criteria — R1: Apply incident criteria to known and assumed characteristics of analyzed activity, and consider known false positives to determine whether an incident should be declared.'
  qualifiers:
  - CSF 2.0 Community Profile の推奨事項
  - インシデントの宣言の判断
  - 組織が定めた基準(defined incident criteria)が前提
  - 誤検知として閉じる条件そのものは定めていない
  - 表の列(CSF Element、CSF Element Description、R1)を収集セッションが「 — 」で区切って連結した
  origin: NIST
  answers:
  - Q3.1.1
  verified: true
  collected_verified: false
  request: R6
  stance:
    H1: supports
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
- id: F305
  statement: NIST SP 800-61r3 は、資源に限りがあるため、インシデントを到着順に扱わないとし、トリアージ・優先順位付け・エスカレーション・復旧開始の判断をリスク評価の要因の集合に基づけるとする。その集合は組織の必要と成熟度により単純なものから非常に複雑なものまである
  kind: fact
  source: 'NIST SP 800-61 Rev. 3 Incident Response Recommendations and Considerations for Cybersecurity Risk Management: A CSF 2.0 Community Profile'
  locator: https://nvlpubs.nist.gov/nistpubs/specialpublications/nist.sp.800-61r3.pdf Table 3, RS.MA (Incident Management) R1, R2
  as_of: 2025-04
  quote: 'Because of resource limitations, incidents should not be handled on a first-come, first-served basis. R2: Incident triage, prioritization, escalation, and elevation and decisions regarding when to initiate recovery processes should all be based on a set of risk evaluation factors. This set can range from simple to incredibly complex, depending on the needs and maturity of an organization.'
  qualifiers:
  - R1 と R2 を連続して引用した(R1 のラベルは省いた)
  - '要因の例は N2: "Examples of possible risk evaluation factors include asset criticality, functional impact of the incident, data impact of the incident, stage of observed activity, threat actor characterization, and recoverability."'
  - 原文で行末の語の分割を連結して写した
  origin: NIST SP 800-61r3
  answers:
  - Q2.1
  verified: true
  collected_verified: false
  request: R3
  stance:
    H1: neutral
    H2: supports
    H3: neutral
- id: F009
  statement: 依頼者のSOCの運用では、「重大度」は製品(SIEM、EDR)がアラートに付けた重大度を指し、High 以上ならすぐ上げる。新人が自分で重大度を判断しなくてよいように、製品の値で線を引く
  kind: testimony
  source: 依頼者(SOCのリーダー)が、自分のSOCの運用として決めた
  locator: 2026-11-24 の聞き取り(工程6、「重大度」の意味の質問への返事)
  as_of: '2026-11-24'
  superseded_by: null
  quote: A。製品が付けた重大度。言葉は「重大度」にそろえて。うちでは High 以上ならすぐ上げる。新人が自分で重大度を判断しなくていいように、製品の値で線を引く。
  qualifiers:
  - 依頼者のSOCの運用
  - 設計セッションが示した選択肢 A に依頼者が同意したもの
  origin: 依頼者
  answers:
  - Q3.3
  verified: true
  stance:
    H1: neutral
    H2: neutral
    H3: neutral
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
- id: F710
  statement: Microsoft Sentinel の分析ルールで最も一般的な種類であるスケジュールされたルールは、一定の間隔で実行される Kusto の問い合わせで、定めた遡りの期間の生データを調べ、問い合わせの結果の件数がルールに設定した閾値を超えるとアラートを出す
  kind: fact
  source: Microsoft Learn, Threat detection in Microsoft Sentinel
  locator: https://learn.microsoft.com/en-us/azure/sentinel/threat-detection  Types of analytics rules > Scheduled rules
  as_of: 2026-05-14
  quote: By far the most common type of analytics rule, Scheduled rules are based on Kusto queries that are configured to run at regular intervals and examine raw data from a defined "lookback" period. If the number of results captured by the query passes the threshold configured in the rule, the rule produces an alert.
  qualifiers:
  - 製品の定義(Microsoft Sentinel)
  - スケジュールされたルールの記述。ほかの種類(NRT、異常、Microsoft セキュリティのルールなど)は別に記述がある
  origin: Microsoft(製品の公式文書)
  answers: []
  verified: true
  collected_verified: false
  request: R7
  stance:
    H1: neutral
    H2: neutral
    H3: neutral
- id: F605
  statement: Microsoft Sentinel では、インシデントを閉じるときに分類の選択が必須で、選択肢は「True Positive(疑わしい活動)」「Benign Positive(疑わしいが想定内)」「False Positive(アラートの論理が誤り)」「False Positive(データが誤り)」「Undetermined」である
  kind: fact
  source: Microsoft Learn, Navigate, triage, and manage Microsoft Sentinel incidents in the Azure portal
  locator: https://learn.microsoft.com/en-us/azure/sentinel/incident-navigate-triage  節 "Close an incident"
  as_of: 2026-07-02
  quote: 'Once you resolve a particular incident (for example, when your investigation reaches its conclusion), set the incident’s status to Closed. When you do so, you''re asked to classify the incident by specifying the reason you''re closing it. Selecting a classification is mandatory. Select Select classification and choose one of the following from the drop-down list: True Positive – suspicious activity / Benign Positive – suspicious but expected / False Positive – incorrect alert logic / False Positive – incorrect data / Undetermined'
  qualifiers:
  - 製品の定義(Microsoft Sentinel)
  - Azure portal での操作
  - 一覧の区切りの " / " は収集セッションが付けた(原文は箇条)
  origin: Microsoft(製品の公式文書)
  answers:
  - Q3.1.1
  verified: true
  collected_verified: false
  request: R6
  stance:
    H1: neutral
    H2: neutral
    H3: neutral
- id: F609
  statement: Microsoft Defender for Endpoint の文書は、分類や抑制の前に、アラートが正確か、誤検知か、無害かを判断するよう求め、誤検知なら False positive に分類して抑制し、正確だが無害(重要でない)なら True positive に分類して抑制するとしている
  kind: fact
  source: Microsoft Learn, Address false positives/negatives in Microsoft Defender for Endpoint
  locator: 'https://learn.microsoft.com/en-us/defender-endpoint/defender-endpoint-false-positives-negatives  節 "Part 1: Review and classify alerts"'
  as_of: 2026-09-02
  quote: Before you classify or suppress an alert, determine whether the alert is accurate, a false positive, or benign. [...] The alert is accurate — Assign the alert, and then investigate it further. The alert is a false positive — 1. Classify the alert as a false positive. 2. Suppress the alert. 3. Create an indicator for Microsoft Defender for Endpoint. 4. Submit a file to Microsoft for analysis. The alert is accurate, but benign (unimportant) — Classify the alert as a true positive, and then suppress the alert.
  qualifiers:
  - 製品の定義(Microsoft Defender for Endpoint)
  - '[...] は収集セッションによる省略、表の列の区切りの「—」は収集セッションが付けた'
  - 正確だが無害なアラートの分類が F607 の Informational, expected activity と一致しない(同じ会社の製品の文書の間で扱いが異なる)
  origin: Microsoft(製品の公式文書)
  answers:
  - Q3.1.1
  verified: true
  collected_verified: false
  request: R6
  stance:
    H1: neutral
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
- id: F002
  statement: 依頼者のSOCの運用では、新人が自分で閉じてよいのは、誤検知と、リーダーが事前に一覧にした想定内の活動(承認済みのスキャン、委託した診断など)に当てはまるものだけである
  kind: testimony
  source: 依頼者(SOCのリーダー)が、自分のSOCの運用として述べた
  locator: 2026-11-24 の聞き取り
  as_of: '2026-11-24'
  superseded_by: null
  quote: おすすめのが近い。それでいい。
  qualifiers:
  - 依頼者のSOCの運用
  - 設計セッションが示した案に依頼者が同意したもの
  origin: 依頼者
  answers:
  - Q3.1.1
  verified: true
  stance:
    H1: neutral
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
- id: F306
  statement: 民間の SOC 向け解説は、SIEM が自動で付ける深刻度スコアをアナリストが最終判断として扱ってはならず、リスクのスコアは人の判断への入力であって代わりではないとする
  kind: fact
  source: 'CyberDefenders, Alert Triage Process: The Complete SOC Analyst''s Guide'
  locator: https://cyberdefenders.org/blog/alert-triage-process/ Stage 3 - Prioritization
  as_of: 2026-09-15
  quote: Most SIEM platforms assign a severity score to alerts automatically, but analysts should never treat that score as the final word. Risk scoring is an input to human judgment, not a replacement for it.
  qualifiers:
  - セキュリティ訓練事業者のブログで、公的機関・標準ではない
  - 日付は "Last updated" の表示
  - Stage 3 - Prioritization の節
  origin: CyberDefenders(独自の解説)
  answers:
  - Q2.1
  verified: true
  collected_verified: false
  request: R3
  stance:
    H1: neutral
    H2: supports
    H3: neutral
- id: F318
  statement: 民間の SOC 向け解説は、真陽性・偽陽性を問わず、閉じた全てのアラートに文書記録を残すべきだとし、記録には発火した内容、調査したこと、見つかった証拠、下した判断を残すとする
  kind: fact
  source: 'CyberDefenders, Alert Triage Process: The Complete SOC Analyst''s Guide'
  locator: https://cyberdefenders.org/blog/alert-triage-process/ Stage 7 - Documentation and Continuous Improvement
  as_of: 2026-09-15
  quote: Every closed alert, true positive or false positive, should produce a documentation record. This isn't administrative overhead; it's institutional memory. The record should capture what was fired, what was investigated, what evidence was found, and what decision was made.
  qualifiers:
  - 訓練事業者のブログで公的機関・標準ではない
  - 閉じた個々の判断の監査や承認の手順は同ページに記載されていない
  origin: CyberDefenders(独自の解説)
  answers:
  - Q3.1.2
  verified: true
  collected_verified: false
  request: R3
  stance:
    H1: neutral
    H2: neutral
    H3: neutral
- id: F004
  statement: 依頼者のSOCでは、新人が閉じたアラートを、後でリーダーかベテランが見直している(頻度は決まっておらず、およそ週1回)
  kind: testimony
  source: 依頼者(SOCのリーダー)が、自分のSOCの運用として述べた
  locator: 2026-11-24 の聞き取り
  as_of: '2026-11-24'
  superseded_by: null
  quote: うちでは新人が閉じたものは、後で俺かベテランが見直してる(頻度は決まってない、だいたい週1くらいの感覚)。
  qualifiers:
  - 依頼者のSOCの運用
  - 頻度は決まっていない(およそ週1回の感覚)
  - 資料には「閉じたものは後で見直される」程度に書く(依頼者の指定)
  origin: 依頼者
  answers:
  - Q3.1.2
  verified: true
  stance:
    H1: neutral
    H2: neutral
    H3: neutral
- id: F005
  statement: 依頼者のSOCでは、配属から最初の3か月の新人は、1件のアラートを30分まで調べ、過ぎたらそこまでに見たことを付けて上げる。重大度が高いものは30分を待たずにすぐ上げる
  kind: testimony
  source: 依頼者(SOCのリーダー)が、自分のSOCの運用として決めた
  locator: 2026-11-24 の聞き取り(持ち時間の質問への返事)
  as_of: '2026-11-24'
  superseded_by: null
  quote: 最初の3か月は1件30分。過ぎたら、そこまでに見たことを付けて上げる。30分は測って決めた数字じゃない。新人は慣れてないから外の12〜20分より長めに取る、っていう俺の判断。…重大度が高いものは30分を待たずにすぐ上げる、は前と同じ。
  qualifiers:
  - 依頼者のSOCの運用
  - 配属から最初の3か月
  - 測って決めた値ではなく、依頼者の判断(外の目安12〜20分より長めに取った)
  - スライドには「このSOCの運用」として載せる(依頼者の指定)
  origin: 依頼者
  answers:
  - Q3.2
  verified: true
  stance:
    H1: neutral
    H2: neutral
    H3: neutral
- id: F403
  statement: アラート1件あたりのトリアージの持ち時間は、Tier 1では12〜20分が一般的とされる。その時間内に判定に達しなければ、記録した要約を付けてTier 2へ上げる
  value: 12-20
  unit: 分
  kind: fact
  source: 'Decryption Digest「SOC Analyst Alert Triage: A Field Guide to Working the Queue」(Eric Bang)'
  locator: 'https://www.decryptiondigest.com/blog/soc-analyst-alert-triage-guide 節「The Alert Triage Mindset: Verdicts, Not Investigations」'
  as_of: 2026-05-14 公開、2026-07-02 更新
  metric: Tier 1のアラート1件あたりのトリアージ時間の目安
  quote: The critical discipline is time-boxing. Set a per-alert triage budget (12-20 minutes is typical for Tier 1). If you cannot reach a verdict within that window, escalate to Tier 2 with a documented summary, do not extend the investigation in place.
  qualifiers:
  - Tier 1の場合
  - 実務者向けの解説記事で標準や公的文書ではない
  - 出版社は広告やスポンサー募集を掲載している
  - 根拠となる調査や数値の出典は記事中で確認できていない
  origin: Decryption Digest(独自の見解)
  answers:
  - Q3.2
  - Q3.3.1
  verified: true
  collected_verified: false
  request: R4
  stance:
    H1: neutral
    H2: neutral
    H3: neutral
- id: F406
  statement: Tier 1が偽陽性と無害な真陽性を処理し、それ以外は全て上げる。上げる条件の例として、重要資産での真陽性またはその疑い、複数ホストにまたがる横展開の証拠、持ち時間内に判定できないアラートが挙がっている
  kind: fact
  source: 'Decryption Digest「SOC Analyst Alert Triage: A Field Guide to Working the Queue」(Eric Bang)'
  locator: 'https://www.decryptiondigest.com/blog/soc-analyst-alert-triage-guide 節「Escalation Criteria: When Tier 1 Hands Off」'
  as_of: 2026-05-14 公開、2026-07-02 更新
  quote: '"Tier 1 analysts resolve false positives and benign true positives. Everything else escalates. Hard escalation triggers:" / "Any confirmed or likely TP on a Tier 1 asset" / "Evidence of lateral movement (multiple hosts involved)" / "Any alert where the analyst cannot reach a verdict within the time budget"'
  qualifiers:
  - 実務者向けの解説記事で標準や公的文書ではない
  - 出版社は広告やスポンサー募集を掲載している
  - 「Tier 1 asset」は資産の重要度の階層を指す
  - 4つの引用を「 / 」でつないで写している
  origin: Decryption Digest(独自の見解)
  answers:
  - Q3.2
  - Q3.3.1
  verified: true
  collected_verified: false
  request: R4
  stance:
    H1: neutral
    H2: neutral
    H3: neutral
- id: F407
  statement: 上げる条件は、事前に定めた担当者の技術的な守備範囲を超えたとき、または単純な監視で足りる範囲を超えた調査が要るときとされる。調査の権限の限界に達したら、直ちに上げる
  kind: fact
  source: Security Scientist「12 Questions and Answers About escalation to tier 2」(Vincent van Dijk)
  locator: https://www.securityscientist.net/blog/12-questions-and-answers-about-escalation-to-tier-2/ 節「4. When should an incident be escalated?」
  as_of: 不明(ページに日付の表示なし)
  quote: '"You should trigger an escalation when you encounter an incident that exceeds your predefined technical scope or requires deeper investigation than simple monitoring allows" / "Escalate as soon as you hit the limit of your investigative authority."'
  qualifiers:
  - 個人が運営する企業ブログで標準や公的文書ではない
  - 同ページは自社の書籍を宣伝している
  - 時間の目安は書かれていない
  - 1つ目の引用は原文の文の後半の終端記号を省いている
  - 2つの引用を「 / 」でつないで写している
  origin: Security Scientist(独自の見解)
  answers:
  - Q3.2
  - Q3.3.1
  verified: true
  collected_verified: false
  request: R4
  stance:
    H1: neutral
    H2: neutral
    H3: neutral
- id: F006
  statement: 依頼者のSOCの運用では、新人の動きは、一覧にあるか誤検知と言えるなら閉じる、重大度が高いならすぐ上げる、攻撃の試みなら上げる、それ以外は30分調べて根拠がなければ上げる、である
  kind: testimony
  source: 依頼者(SOCのリーダー)が、自分のSOCの運用として述べた
  locator: 2026-11-24 の聞き取り(工程5、見せ方の確認への返事)
  as_of: '2026-11-24'
  superseded_by: null
  quote: 一覧にある/誤検知と言える→閉じる、重大度が高い→すぐ上げる、攻撃の試み→上げる、それ以外→30分調べて、根拠がなければ上げる。これは俺が決めたうちの運用だから、線を引いても「根拠のない線」にはならない。出典は「このSOCの運用」でいい。案の部分が混ざるなら、そこだけ案と分かるようにして。
  qualifiers:
  - 依頼者のSOCの運用
  - 誤検知と言える基準は案(D001)
  - 確かめる順は F007
  origin: 依頼者
  answers:
  - Q3
  verified: true
  stance:
    H1: neutral
    H2: neutral
    H3: neutral
- id: F405
  statement: 同じSOP集は、P1については、「もっと調べる」ために上げるのを遅らせず、先に上げて調査は並行して進めるとしている。また一般の規則として、判断に迷うときは、上げすぎる側に倒すとしている
  kind: fact
  source: SOC-SOP「Escalation Matrix」(IR-SOP-015)
  locator: https://nutthakorn7.github.io/SOC-SOP/05_Incident_Response/Escalation_Matrix.en 節 Escalation Rules(Do's / Don'ts)
  as_of: 2026-02-15 (Version 1.0)
  quote: '"Never delay a P1 escalation to "investigate more" — escalate first, investigate in parallel" / "Over-escalate if unsure — it''s better to escalate and be wrong than to miss a real incident"'
  qualifiers:
  - 1つ目の規則(P1を遅らせない)はP1(最重大)の場合の規則
  - 2つ目の規則(迷うときは上げすぎる側に倒す)は同じ文書の Do's の一般規則で、P1に限らない
  - 有志のSOP集で標準や公的文書ではない
  - 2つの規則を「 / 」でつないで写している
  origin: SOC-SOP(独自の見解)
  answers:
  - Q3.2
  - Q3.3.1
  verified: true
  collected_verified: false
  request: R4
  stance:
    H1: contradicts
    H2: supports
    H3: neutral
- id: F003
  statement: 依頼者のSOCの運用では、配属から最初の3か月の新人には、侵害に至らなかった攻撃の試みを全て上げさせる。上が溢れるかはリーダーの側で対処する
  kind: testimony
  source: 依頼者(SOCのリーダー)が、自分のSOCの運用として述べた
  locator: 2026-11-24 の聞き取り
  as_of: '2026-11-24'
  superseded_by: null
  quote: 攻撃の試みは、最初の3か月は全部上げさせる。上が溢れるかは俺の側で何とかする話で、新人に背負わせることじゃない。
  qualifiers:
  - 依頼者のSOCの運用
  - 配属から最初の3か月
  origin: 依頼者
  answers:
  - Q3.3.1
  verified: true
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
- id: F413
  statement: Tier 2へ上げるときは、アラートの出どころとID、トリアージの経過、集めた証拠、現時点の判定の仮説、次の推奨手順を必ず含める。文脈のない引き継ぎでは、Tier 2がやり直しになる
  kind: fact
  source: 'Decryption Digest「SOC Analyst Alert Triage: A Field Guide to Working the Queue」(Eric Bang)'
  locator: 'https://www.decryptiondigest.com/blog/soc-analyst-alert-triage-guide 節「Escalation Criteria: When Tier 1 Hands Off」'
  as_of: 2026-05-14 公開、2026-07-02 更新
  quote: 'Escalation should always include: alert source and ID, triage timeline, evidence collected, current verdict hypothesis, and recommended next step. Handoffs without context force Tier 2 to start over.'
  qualifiers:
  - 実務者向けの解説記事で標準や公的文書ではない
  - 出版社は広告やスポンサー募集を掲載している
  - 原文は箇条書きではなく1つの段落
  origin: Decryption Digest(独自の見解)
  answers:
  - Q3.3.3
  verified: true
  collected_verified: false
  request: R4
  stance:
    H1: neutral
    H2: neutral
    H3: neutral
- id: F414
  statement: 引き継ぎには、関連するメタデータと初期の所見を全て含める。見落としを防ぐために、標準の書式のテンプレートを使う
  kind: fact
  source: Security Scientist「12 Questions and Answers About escalation to tier 2」(Vincent van Dijk)
  locator: https://www.securityscientist.net/blog/12-questions-and-answers-about-escalation-to-tier-2/ 節「7. Can improper handoffs delay threat response?」
  as_of: 不明(ページに日付の表示なし)
  quote: '"To prevent this, always ensure your handoff includes all relevant metadata and initial findings." / "Use standardized templates for all escalation notes to ensure no critical data is missed during the transition."'
  qualifiers:
  - 個人が運営する企業ブログで標準や公的文書ではない
  - 同ページは自社の書籍を宣伝している
  - 同節の例では送信元IPの記載漏れで、Tier 2が元のイベントデータを探すのに30分を費やしたとある
  - 2つの引用を「 / 」でつないで写している
  origin: Security Scientist(独自の見解)
  answers:
  - Q3.3.3
  verified: true
  collected_verified: false
  request: R4
  stance:
    H1: neutral
    H2: neutral
    H3: neutral
- id: F007
  statement: 依頼者のSOCの運用では、1件のアラートが複数の条件に当たるときは、上げる条件(重大度が高い、攻撃の試み)を先に確かめ、上げる側に倒す。一覧にある作業でも重大度が高く出たものは上げる
  kind: testimony
  source: 依頼者(SOCのリーダー)が、自分のSOCの運用として決めた
  locator: 2026-11-24 の聞き取り(工程5、確かめる順の質問への返事)
  as_of: '2026-11-24'
  superseded_by: null
  quote: A。上げる条件が先。一覧にある作業でも、重大度が高く出たなら一覧の作業に紛れた何かかもしれない。新人が見分けることじゃない。上の確認が増えるのは構わない。
  qualifiers:
  - 依頼者のSOCの運用
  - 設計セッションが示した選択肢 A(重大度が高い→攻撃の試み→一覧/誤検知→それ以外)に依頼者が同意したもの
  origin: 依頼者
  answers:
  - Q3
  verified: true
  stance:
    H1: neutral
    H2: neutral
    H3: neutral
- id: F008
  statement: 依頼者のSOCの運用では、新人が閉じるアラートは、一覧にあるものも誤検知も全て記録して閉じる。後の見直しはその記録を見て行う
  kind: testimony
  source: 依頼者(SOCのリーダー)が、自分のSOCの運用として述べた
  locator: 2026-11-24 の聞き取り(工程5、流れ図の確認への返事)
  as_of: '2026-11-24'
  superseded_by: null
  quote: 閉じるものは全部記録する、って22枚目で言ってるし、後で見直すのもその記録を見る。3も「想定内の検知として記録して閉じる」にして。
  qualifiers:
  - 依頼者のSOCの運用
  - 記録する項目は案(ch3-s9)
  origin: 依頼者
  answers:
  - Q3.1.2
  verified: true
  stance:
    H1: neutral
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
- id: A-investigate
  basis: operation
  kind: action
  name: 調べる(30分まで)
  evidence:
  - F005
  note: このSOCの運用
- id: A-close
  basis: operation
  kind: action
  name: 閉じる
  evidence:
  - F002
  note: このSOCの運用
- id: A-escalate
  basis: operation
  kind: action
  name: 上げる
  evidence:
  - F003
  - F005
  note: このSOCの運用
- id: D-op-alert
  basis: operation
  kind: data
  name: 新人に届いたアラート
  evidence:
  - F002
  note: このSOCの運用
relations:
- id: R-op-severe
  basis: operation
  kind: route
  from: D-op-alert
  to: A-escalate
  label: 30分を待たずにすぐ上げる
  mode: unknown
  condition: 製品が付けた重大度が High 以上
  order: 1
  proposal: ''
  evidence:
  - F005
  - F006
  - F007
  - F009
  note: このSOCの運用
- id: R-op-attempt
  basis: operation
  kind: route
  from: D-op-alert
  to: A-escalate
  label: 上げる
  mode: unknown
  condition: 侵害に至らなかった攻撃の試み(配属から3か月)
  order: 2
  proposal: ''
  evidence:
  - F003
  - F006
  - F007
  note: このSOCの運用
- id: R-op-list
  basis: operation
  kind: route
  from: D-op-alert
  to: A-close
  label: 想定内の検知として記録して閉じる
  mode: unknown
  condition: リーダーの一覧にある活動に当てはまる
  order: 3
  proposal: ''
  evidence:
  - F002
  - F006
  - F007
  - F008
  note: このSOCの運用
- id: R-op-other
  basis: operation
  kind: route
  from: D-op-alert
  to: A-investigate
  label: 調べる(30分まで)
  mode: unknown
  condition: 上の3つのどれにも当たらない
  order: 4
  proposal: ''
  evidence:
  - F005
  - F006
  - F007
  note: このSOCの運用
- id: R-op-fp
  basis: operation
  kind: route
  from: A-investigate
  to: A-close
  label: 誤検知として記録して閉じる
  mode: unknown
  condition: 30分の中で、誤検知と根拠をもって言えた
  order: 1
  proposal: 誤検知と言える基準(ch3-s5)
  evidence:
  - F002
  - F006
  - F008
  note: 誤検知を閉じてよいことはこのSOCの運用(F002)。依頼者は誤検知と言えるものを最初の段で閉じるとしたが、誤検知かどうかは調べて確かめるため、調べる段の中に置いた(D011)
- id: R-op-inv-esc
  basis: operation
  kind: route
  from: A-investigate
  to: A-escalate
  label: 見たことを付けて上げる
  mode: unknown
  condition: 30分たっても閉じる根拠がない
  order: 2
  proposal: ''
  evidence:
  - F005
  - F006
  note: このSOCの運用
scenarios:
- id: S-newbie-ops
  basis: operation
  name: このSOCで、配属から3か月の新人が1件のアラートを扱う流れ
  steps:
  - R-op-severe
  - R-op-attempt
  - R-op-list
  - R-op-other
  - R-op-fp
  - R-op-inv-esc
  evidence:
  - F002
  - F003
  - F005
  - F006
  - F007
  note: 上げる条件を先に確かめ、最初に当たった道に進む(F007)。誤検知と言える基準は案で、調べる段の中に置いた(D011)
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
  - id: T-true-attack-share
    term: 真の攻撃に関連するアラートの割合
    kind: noun
    definition: アラートのうち、侵害に至った実際の攻撃に関連するものの割合
    defined_in: null
    no_definition: 素材台帳の metric の照合に使う指標の名前で、スライドの語ではない
  - id: T-triage-time
    term: Tier 1のアラート1件あたりのトリアージ時間の目安
    kind: noun
    definition: 一次解析の担当が、アラート1件の判定にかける時間の目安
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
  - id: T-timebox
    term: 持ち時間
    kind: noun
    definition: 新人が1件のアラートを調べてよい時間。このSOCでは配属から3か月は1件30分
    defined_in: ch3-s11
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
  - id: T-soc-ops
    term: このSOCの運用
    kind: noun
    definition: リーダーが決めた、このSOCでの新人の扱い方
    not:
    - T-proposal
    defined_in: ch3-s2
    no_definition: null
  - id: T-lateral
    term: 横展開
    kind: noun
    definition: 攻撃者が、入り込んだ端末から別の端末へ広がること。複数の端末にまたがる
    defined_in: ch3-s12
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
  - id: T-severity
    term: 重大度
    kind: noun
    definition: 製品(SIEM、EDR)がアラートに付けた重大度の値(High、Critical など)。このSOCでは High 以上ならすぐ上げる
    not:
    - T-priority
    defined_in: ch3-s16
    no_definition: null
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

### flowchart(`06-samples/flowchart.yaml`、画像は `06-samples/flowchart.png`)

```yaml
# 型の見本のスライド仕様(工程6)。工程7でそのまま使う。
id: ch3-s17
status: done
headline: 配属から3か月の新人は、重大度 High 以上か攻撃の試みなら上げ、一覧なら閉じ、残りは調べる
takeaway: 上げる条件を先に見る。閉じるのは、一覧にあるか、調べて誤検知と言えたときだけ
body:
  type: flowchart
  mark: 運用
  scenario: S-newbie-ops
  proposal_parts:
  - R-op-fp
  labels:
    D-op-alert: "届いた\nアラート"
    R-op-severe:
      condition: "重大度が\nHigh以上?"
      label: すぐ上げる
    R-op-attempt:
      condition: "攻撃の\n試み?"
    R-op-list:
      condition: 一覧にある?
    R-op-fp:
      condition: 誤検知と根拠をもって言えた
    R-op-inv-esc:
      condition: 30分で根拠なし
  highlight:
    ids:
    - R-op-severe
    - R-op-attempt
    label: 先に確かめる
sources:
- F002
- F003
- F005
- F006
- F007
- F008
- F009
notes: 上から順に確かめ、最初に当たった道に進む。重大度は製品が付けた値。一覧にある作業でも重大度が High 以上なら上げる。
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

### step-flow(`06-samples/step-flow.yaml`、画像は `06-samples/step-flow.png`)

```yaml
# 型の見本のスライド仕様(工程6)。工程7でそのまま使う。
id: ch1-s1
status: done
headline: 重大度 High 以上はまず上げ、残りを3つに分けて、閉じる・調べる・上げるを決める
takeaway: 最初に重大度を見る。残りを3つに分け、それから行き先を決める
body:
  type: step-flow
  numbering: 0
  steps:
  - name: 重大度を見る
    description:
    - 製品の重大度が High 以上なら
    - text: まず上げる
      color: 上げる
    next: それ以外
  - name: 3つに分ける
    description:
    - 誤検知
    - 想定内の検知
    - 攻撃の疑い
  - name: 行き先を決める
    description: 閉じる、調べる、上げる
  highlight: steps[0]
sources:
- F009
notes: この順は第3章の最後の流れ図と同じ。区分と行き先は1対1ではなく、どの区分がどの行き先になるかは第3章で扱う。
```

### table(`06-samples/table.yaml`、画像は `06-samples/table.png`)

```yaml
# 型の見本のスライド仕様(工程6)。工程7でそのまま使う。
id: ap-s1
status: done
headline: 扱う量は出典で大きく違い、1つのSOCの実測は1日約13,764件、自己申告は1日平均4,484件
takeaway: 届く量の数字は、調べ方をそろえないと比べられない
body:
  type: table
  columns:
  - 出典
  - 調べ方
  - name: 値
    align: right
  rows:
  - - 1つのSOC(Yangら)
    - 実測(自動遮断の後に解析者が扱った件数)
    - 1日 約{F201:value}件
  - - 実務者の調査(Alahmadiら)
    - 回答(自己申告)
    - '{F202:metric}が{F202}'
  - - ベンダーの調査(Vectra AI)
    - 回答(自己申告)
    - 1日平均 {F203:value}件
  highlight: columns[1]
sources:
- F201
- F202
- F203
notes: 実測と自己申告は、数え方が違う。
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
| `start` | 任意 | 始まりの要素。既定は場面の最初のつながりの `from`。指定すると、そこから届く道だけを描く(例: `start: A-investigate` で、調べるから出る2つの道だけ)。始まりが行き先の要素なら、行き先の札の形と色で描く |
| `labels` | 任意 | 図に載せる短い名前。要素は `ID: 名前`。つながりは `ID: {condition: 分かれ目の問い, label: 行き先の札}`。`\n` で改行を指定できる |
| `proposal_parts` | 任意 | 案の部分のつながり。定義の `proposal` が空でないつながりも案として描く(紫の破線と「案の基準」) |
| `highlight` | 任意 | つながりか要素のID、または `{ids: [ID, ...], label: 枠の上の語}`(隣り合う分かれ目をまとめて1つの枠で囲む) |

描き方: 始まりから出る道を `order` の順に、分かれ目(ひし形)として左から右に並べる。「はい」の行き先は下に出す。最後の道は「いいえ」として次の要素に進む。次の要素がさらに道を持たなければ、最後の道の札(`label`)を行き先として載せる。その要素から出る道は2つまで描ける。1つ目は右(条件の札を通って行き先へ)、2つ目は下。これより深い流れは描けない(診断に出る)。

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
| `placeholder` | スライド仕様がない、または `status: blocked`(保留)(情報)。保留のスライドは body を読まず、立証設計から仮置きを描く。`issue` があれば診断に添える |

`wraps` に、折り返した位置(図の中の文字)を記録する。

