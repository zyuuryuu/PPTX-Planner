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
