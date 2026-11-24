# PMの作業の記録(SOC試行、製造の時期)

## 2026-11-24

- 開始。役割の指示(`trial/roles/pm.md`)と、従う文書(organization、07-slide-spec、rework、tools/README、patterns-data)を読んだ。進行役に開始を伝えた。
- graphviz をこの環境に入れた(`apt-get install -y graphviz`)。`python tools/render.py trial/deck` が動くことを確かめた(54枚、エラー0、警告1 = ch5 の章扉の問い)。
- 引き継ぎの検査を `handover.md` に書いた。分からない点3件(ch1-s2 と ch3-s13 の流れ図の場面がない、架空の値の数値、ch5 の章扉の問い)を設計セッションに送った。
- 章の作業票を `work/make_tickets.py` で抜き出した(`work/ch1.md` ほか6件。付録は `ap`)。立証の設計の facts、view、場面、見本の仕様、語彙(章の上流の文に出る語と metric の語)、表現規約、対応表、patterns-data の全文を入れた。
- 見本10枚の仕様を `07-slides/<章>.yaml` に写した(テキストをそのまま、読み込んで見本と同じになることを確かめた)。描いた結果は変わらない。

### 自分で決めた点

- 付録を `ap` の1章として扱う。
- 作業票の事実は、立証の設計の facts とストーリーラインの evidence の和から抜き出す。
- ch5 の章扉の警告は執筆の範囲の外のため、章の受け入れの「診断0件」の対象から外し、警告として記録する(設計セッションの回答で変わりうる)。
- 設計セッションの答え(D013、コミット 2ac8b6e)を受けた。ch1-s2 は statement に、ch3-s13 は S-newbie-ops の start: A-investigate に、架空の数値は例外に、ch5 の章扉の問いは 03-chapters の cover_question に。作業票を作り直した。
- 道具の不足: render.py は cover_question を読まない(ch5 の章扉の警告が残る)。道具のセッションと進行役に伝える。
- 03:36Z 執筆の子セッションを3つ起こした(すべて claude-opus-5-5): ch3 session_01LpWHd2UfjbFvamrmEHXk12、ch2 session_01LpWHd4P3wuqFUvq3qSUj8K、ch4 session_01LpWHd4Wzgiecu46rYkU9tV。1分後に get_session で3つとも RUNNING、起動の失敗なしを確かめた。待ち始め 03:36Z。
- 受け入れの機械的な確かめのスクリプト `work/accept.py` を書いた(見出し、型、sources の範囲、見本の一致、その章の診断のエラーと警告、差分のファイル)。
- 気づいた点: 子セッションの道具の一覧(get_session の turn_handoff.tools)に send_message が見えない。報告が届かない場合は、コミットと get_session で状態を知る。
- 設計セッションの回答のメッセージを受けた(内容は D013 と同じ)。注意点: ch1-s2 を statement に変えたのは依頼者が工程5で同意した見せ方からの変更で、依頼者に示す必要がある(進行役への最終の報告に入れる)。
- 03:37Z 道具のセッションが cover_question の読み込みと flowchart の start を直した(d4b1707)。描き直して ch5-cover の警告が消えたことを確かめた。章の受け入れの診断0件の除外は不要になった。
- 03:38Z ch4 の執筆の報告(f3cee67): ch4-s1 done、ch4-s3 blocked(F506 は56%だけで円グラフの残りの区分の値がない、色の割り当てがない、show の「帯」と型の不一致)。Issue #1 を立て、設計セッションに判断を依頼した。ch4 の執筆のセッションは答えまで待機。
- 道具の挙動: status: blocked のスライドを render.py が描こうとしてエラー2、警告1を出す。道具のセッションに伝えた。
- 03:38Z ch4 が待機に入ったため、ch5 の執筆の子セッションを起こした(session_01LpWHd2V7nKu7ymzEX9btp8)。動いているのは ch3、ch2、ch5 の3つ(ch4 は待機)と数えた。自分で決めた点。
- 03:39Z 設計が Issue #1 を D014 で決めた(ch4-s3 を statement に。8672bca)。ch1-s2 と同じく、依頼者が同意した見せ方からの変更として最終の報告で示す。道具も保留のスライドを仮置きで描くよう直した(f9380d3)。ch4 の作業票を作り直し、執筆のセッションに再開を伝えた。
