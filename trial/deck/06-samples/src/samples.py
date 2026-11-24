# 工程6の型の見本: スライド仕様(06-samples/<型>.yaml)と、見本の HTML を作る。
# 描画は設計セッションの手書きの HTML/SVG(描画の実装が未定のため)。1280x720。
# 文字の下限(style.yaml common.font_min): 見出し 24pt=32px、出典の行 16pt=22px、本文 18pt=24px、図の中 16pt=22px、注記 14pt=19px。
import sys, yaml, html, math
from pathlib import Path

deck = Path(sys.argv[1]); out_html = Path(sys.argv[2]); out_html.mkdir(parents=True, exist_ok=True)
S = {s['id']: s for s in yaml.safe_load(open(deck / '04-storyline.yaml'))}
C = yaml.safe_load(open(deck / 'style.yaml'))['common']['colors']
E = html.escape
FIG = 22   # 図の中の文字
NOTE = 19  # 注記
INK = '#111827'

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{width:1280px;height:720px;background:#fff;font-family:'IPAPGothic','IPAGothic',sans-serif;color:#111827;position:relative;overflow:hidden}
.top{position:absolute;left:48px;top:26px;width:1184px}
.h{font-size:32px;font-weight:bold;line-height:1.3}
.src{font-size:22px;color:#374151;line-height:1.35;margin-top:6px}
.fig{margin-top:22px}
.tk{position:absolute;left:0;bottom:0;width:1280px;height:72px;background:#F3F4F6;font-size:26px;padding:20px 48px;border-top:2px solid #D1D5DB}
.tag{display:inline-block;font-size:19px;padding:2px 10px;border-radius:12px;color:#fff;margin-right:8px;vertical-align:middle}
"""
TAG_P = f'<span class="tag" style="background:{C["案の印"]}">案</span>'
TAG_O = f'<span class="tag" style="background:{C["このSOCの運用の印"]}">運用</span>'

def page(sid, fig, takeaway):
    s = S[sid]
    src = s.get('source')
    src_html = f'<div class="src">出典: {E(src)}</div>' if src else ''
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="top"><div class="h">{E(s['headline'])}</div>{src_html}<div class="fig">{fig}</div></div>
<div class="tk">{E(takeaway)}</div></body></html>"""

def text(x, y, t, fs=FIG, anchor='start', color='#111827', bold=False):
    return f'<text x="{x}" y="{y}" font-size="{fs}" text-anchor="{anchor}" fill="{color}"{" font-weight=\"bold\"" if bold else ""}>{E(t)}</text>'

def box(x, y, w, h, t, fill='#E5E7EB', stroke='#9CA3AF', sw=2, fs=FIG, bold=False, dash=None, rx=10, color='#111827'):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    lines = t.split('\n')
    ty = y + h / 2 - (len(lines) - 1) * fs * 0.62
    s = ''.join(text(x + w/2, ty + i*fs*1.25 + fs*0.35, l, fs, 'middle', color, bold) for i, l in enumerate(lines))
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>' + s

def dest(x, y, w, h, t, color, fs=FIG):
    """行き先の札(両端の丸い札)。塗らずに色の枠と色の文字で示し、強調より目立たないようにする"""
    lines = t.split('\n')
    ty = y + h / 2 - (len(lines) - 1) * fs * 0.62
    s = ''.join(text(x + w/2, ty + i*fs*1.25 + fs*0.35, l, fs, 'middle', color, True) for i, l in enumerate(lines))
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{min(h/2, 28)}" fill="#fff" stroke="{color}" stroke-width="3"/>' + s

def arrow(x1, y1, x2, y2, label='', w=3, lfs=FIG):
    s = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#374151" stroke-width="{w}" marker-end="url(#a)"/>'
    if label:
        if abs(y2 - y1) < abs(x2 - x1):
            s += text((x1+x2)/2, min(y1, y2) - 10, label, lfs, 'middle', '#374151')
        else:
            s += text(x1 + 10, (y1+y2)/2 + 8, label, lfs, 'start', '#374151')
    return s

def diamond(cx, cy, w, h, t, fs=FIG):
    p = f'{cx},{cy-h/2} {cx+w/2},{cy} {cx},{cy+h/2} {cx-w/2},{cy}'
    lines = t.split('\n')
    s = ''.join(text(cx, cy - (len(lines)-1)*fs*0.62 + i*fs*1.25 + fs*0.35, l, fs, 'middle') for i, l in enumerate(lines))
    return f'<polygon points="{p}" fill="#fff" stroke="#6B7280" stroke-width="2"/>' + s

def svg(w, h, body):
    return f'<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg"><defs><marker id="a" markerUnits="userSpaceOnUse" markerWidth="16" markerHeight="16" refX="14" refY="8" orient="auto"><path d="M0,0 L16,8 L0,16 z" fill="#374151"/></marker></defs>{body}</svg>'

def emph_rect(x, y, w, h):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="none" stroke="{INK}" stroke-width="5"/>'

samples = {}

# 1. statement: ch4-s2(強調は但し書きの1か所。引用の中に太字を使わない)
tk = '見過ごしの原因は確かめられていないが、慣れが見過ごしにつながりうる'
samples['statement'] = dict(spec=dict(id='ch4-s2', status='done', headline=S['ch4-s2']['headline'], takeaway=tk,
    body=dict(type='statement', quote='F501', quote_ja='{F501} の日本語訳', caveat='推定であり、確認された原因ではない', highlight='caveat'),
    sources=['F501'], notes='報告は報道(Bloomberg Businessweek)を引いて推定を述べている。報告自身は原因を確かめていない。'),
    html=page('ch4-s2', '''<div style="border-left:8px solid #9CA3AF;padding:18px 28px;font-size:28px;line-height:1.6;background:#F9FAFB">
「システムが頻繁に警報を鳴らしていたのであれば、職員はこのアラートを誤検知とみなした可能性がある」<div style="font-size:22px;color:#4B5563;margin-top:10px">報告の原文(英語)の日本語訳。報道を引いた記述</div></div>
<div style="margin-top:34px;display:inline-block;border:5px solid #111827;padding:14px 26px;font-size:28px;font-weight:bold">推定であり、確認された原因ではない</div>''', tk))

# 2. plain-list: ch3-s15(囲みを外し、強調は「5項目」の題の1か所)
items = ['アラートの出どころとID', '調べた経過', '集めた証拠', '現時点の判定の仮説', '次に勧める手順']
tk = '文脈のない引き継ぎでは、受けた側が調べ直すことになる'
samples['plain-list'] = dict(spec=dict(id='ch3-s15', status='done', headline=S['ch3-s15']['headline'], takeaway=tk,
    body=dict(type='plain-list', title='上げるときに添える5項目', items=items, highlight='title(5項目そろえること)', mark='案'),
    sources=['F413', 'F414'], notes='送信元のIPアドレスを書き漏らすと、受けた側が元のイベントを探し直すことになる(F414 の例)。'),
    html=page('ch3-s15', TAG_P + '<span style="display:inline-block;border:5px solid #111827;padding:4px 14px;font-size:26px;font-weight:bold;vertical-align:middle">上げるときに添える5項目</span>' +
        '<ul style="margin-top:18px;list-style:none;font-size:28px;line-height:1.75;padding-left:24px">' + ''.join(f'<li>・{E(i)}</li>' for i in items) + '</ul>', tk))

# 3. step-flow: ch1-s1(0. 重大度 → 1. 分ける → 2. 行き先。項目を段どうしで同じ高さに並べない。強調は最初の段)
f = box(0, 60, 270, 230, '', fill='#fff', stroke=INK, sw=5)
f += text(135, 104, '0. 重大度を見る', 26, 'middle', bold=True)
f += text(135, 160, '製品の重大度が', 24, 'middle') + text(135, 192, 'High 以上なら', 24, 'middle')
f += text(135, 246, 'まず上げる', 24, 'middle', C['上げる'], True)
f += arrow(270, 175, 385, 175, 'それ以外')
f += box(390, 20, 310, 310, '', fill='#fff', stroke='#9CA3AF')
f += text(545, 66, '1. 3つに分ける', 26, 'middle', bold=True)
for i, k in enumerate(['誤検知', '想定内の検知', '攻撃の疑い']):
    f += text(545, 132 + i*66, k, 26, 'middle')
f += arrow(700, 175, 760, 175)
f += box(770, 110, 410, 150, '', fill='#fff', stroke='#9CA3AF')
f += text(975, 158, '2. 行き先を決める', 26, 'middle', bold=True)
f += text(975, 218, '閉じる、調べる、上げる', 26, 'middle')
tk = '最初に重大度を見る。残りを3つに分け、それから行き先を決める'
samples['step-flow'] = dict(spec=dict(id='ch1-s1', status='done', headline=S['ch1-s1']['headline'], takeaway=tk,
    body=dict(type='step-flow', steps=[dict(name='重大度を見る', description='製品の重大度が High 以上ならまず上げる(このSOCの運用)'), dict(name='3つに分ける', description='誤検知、想定内の検知、攻撃の疑い'), dict(name='行き先を決める', description='閉じる、調べる、上げる')], highlight='steps[0]'),
    sources=['F009'], notes='この順は第3章の最後の流れ図と同じ。区分と行き先は1対1ではなく、どの区分がどの行き先になるかは第3章で扱う。'),
    html=page('ch1-s1', svg(1184, 350, f), tk))

# 4. flowchart: ch3-s17(行き先は塗らない。強調は先に確かめる2つの分かれ目を囲む1か所)
g = box(0, 130, 130, 76, '届いた\nアラート')
g += arrow(130, 168, 175, 168)
ds = [(250, '重大度が\nHigh以上?'), (470, '攻撃の\n試み?'), (690, '一覧に\nある?')]
nxt = [395, 615, 830]
for (x, lab), n in zip(ds, nxt):
    g += diamond(x, 168, 150, 110, lab)
    g += arrow(x + 75, 168, n, 168, 'いいえ')
    g += arrow(x, 223, x, 300, 'はい')
g += emph_rect(168, 100, 380, 136)
g += text(360, 92, '先に確かめる', FIG, 'middle', INK, True)
g += dest(165, 305, 170, 56, 'すぐ上げる', C['上げる'])
g += dest(385, 305, 170, 56, '上げる', C['上げる'])
g += dest(585, 300, 210, 80, '想定内の検知として\n記録して閉じる', C['閉じる'])
g += dest(830, 130, 150, 76, '調べる\n30分まで', C['調べる'])
g += f'<rect x="1005" y="20" width="175" height="110" rx="8" fill="#fff" stroke="{C["案の印"]}" stroke-width="2" stroke-dasharray="8 6"/>'
g += text(1015, 44, '案の基準', NOTE, 'start', C['案の印'], True)
g += text(1092, 78, '誤検知と根拠を', FIG, 'middle') + text(1092, 106, 'もって言えた', FIG, 'middle')
g += '<polyline points="980,150 992,150 992,75 1003,75" fill="none" stroke="#374151" stroke-width="3" marker-end="url(#a)"/>'
g += arrow(1092, 130, 1092, 166)
g += dest(1005, 168, 175, 80, '誤検知として\n記録して閉じる', C['閉じる'])
g += arrow(905, 206, 905, 298, '30分で根拠なし')
g += dest(820, 300, 175, 80, '見たことを\n付けて上げる', C['上げる'])
tk = '上げる条件を先に見る。閉じるのは、一覧にあるか、調べて誤検知と言えたときだけ'
samples['flowchart'] = dict(spec=dict(id='ch3-s17', status='done', headline=S['ch3-s17']['headline'], takeaway=tk,
    body=dict(type='flowchart', scenario='S-newbie-ops', proposal_parts=['R-op-fp'], highlight='先に確かめる2つの分かれ目(重大度、攻撃の試み)'),
    sources=['F002', 'F003', 'F005', 'F006', 'F007', 'F008', 'F009'], notes='上から順に確かめ、最初に当たった道に進む。重大度は製品が付けた値。一覧にある作業でも重大度が High 以上なら上げる。'),
    html=page('ch3-s17', TAG_O + svg(1184, 390, g), tk))

# 5. architecture-diagram: ch2-s3(「持つ」は矢印でなく内側に置く。記録の一覧はセンサーから離す)
a = text(0, 26, 'EDRの要件の例(NCA)', 24, bold=True)
a += box(14, 54, 140, 68, '端末') + arrow(154, 88, 194, 88) + box(194, 54, 170, 68, 'エージェント') + arrow(364, 88, 404, 88) + box(404, 54, 170, 68, '中央の\nデータベース')
a += emph_rect(0, 42, 590, 92)
a += text(0, 172, 'プロセス、接続、ファイルなどの端末の記録を集める', 24, color='#374151')
a += text(640, 26, '製品の例(Microsoft Defender for Endpoint)', 24, bold=True)
a += box(640, 50, 300, 130, '', fill='#E5E7EB')
a += text(790, 84, 'Defender for Endpoint', FIG, 'middle')
a += box(700, 104, 180, 56, 'センサー', fill='#fff')
a += arrow(790, 180, 790, 240, '作る') + box(700, 242, 180, 56, 'アラート')
a += f'<rect x="980" y="50" width="204" height="250" rx="8" fill="#F9FAFB" stroke="#9CA3AF" stroke-dasharray="4 4"/>'
a += text(992, 78, '製品が集める記録', NOTE, bold=True)
for i, l in enumerate(['プロセス', 'ネットワーク', 'ログオン', 'レジストリと', 'ファイルの変更']):
    a += text(1000, 110 + i*28, l, NOTE)
a += text(992, 262, '製品やアラートとの', NOTE, color='#4B5563') + text(992, 286, '経路は出典にない', NOTE, color='#4B5563')
tk = 'EDRの材料は、端末の振る舞いを集め続けた記録である'
samples['architecture-diagram'] = dict(spec=dict(id='ch2-s3', status='done', headline=S['ch2-s3']['headline'], takeaway=tk,
    body=dict(type='architecture-diagram', elements=['E-endpoint', 'E-edr-agent', 'E-edr-central-db', 'E-mde', 'E-mde-sensor', 'D-mde-telemetry', 'D-mde-alert'],
              relations=['R-endpoint-agent', 'R-agent-central-db', 'R-mde-sensor', 'R-mde-alert'], highlight='左の枠(記録を継続して集める)'),
    sources=['F615', 'F616', 'F618', 'F619'], notes='左は要件の文書、右は製品の文書で、出典が違う。右の記録からアラートへの経路は出典に書かれていないので描かない。'),
    html=page('ch2-s3', svg(1184, 400, a), tk))

# 6. pie-chart: ch2-s6(注記は出典の行と重ねない)
parts = [(27, C['攻撃の試み']), (49, C['想定内の検知']), (24, C['分類できないもの'])]
cx, cy, r = 190, 190, 165; ang = -90; p = ''
for i, (v, c) in enumerate(parts):
    a1 = math.radians(ang); a2 = math.radians(ang + v * 3.6)
    large = 1 if v > 50 else 0
    x1, y1, x2, y2 = cx + r*math.cos(a1), cy + r*math.sin(a1), cx + r*math.cos(a2), cy + r*math.sin(a2)
    em = i == 0
    p += f'<path d="M{cx},{cy} L{x1:.1f},{y1:.1f} A{r},{r} 0 {large} 1 {x2:.1f},{y2:.1f} z" fill="{c}" stroke="{INK if em else "#fff"}" stroke-width="{6 if em else 2}"/>'
    ang += v * 3.6
leg = [('侵害に至った攻撃 0.01%(細すぎて円に出ない)', C['侵害に至った攻撃'], False), ('攻撃の試み 27%以上', C['攻撃の試み'], True), ('想定内の検知 49%以上', C['想定内の検知'], False), ('分類できないもの 約24%', C['分類できないもの'], False)]
for i, (k, c, em) in enumerate(leg):
    p += f'<rect x="420" y="{50 + i*66}" width="34" height="34" fill="{c}"/>'
    p += text(468, 77 + i*66, k, 26, bold=em)
tk = '誤検知でも想定内でもない攻撃の試みが、少なくとも4分の1ある'
samples['pie-chart'] = dict(spec=dict(id='ch2-s6', status='done', headline=S['ch2-s6']['headline'], takeaway=tk,
    body=dict(type='pie-chart', data=[dict(label='侵害に至った攻撃', value='F207'), dict(label='攻撃の試み', value='F207', bound='以上'), dict(label='想定内の検知', value='F207', bound='以上'), dict(label='分類できないもの', value='F207')], highlight='攻撃の試み'),
    sources=['F207'], notes='27%と49%は論文が「少なくとも」とする下限。想定内の検知は明確な証拠があるものだけを数えた。'),
    html=page('ch2-s6', svg(1184, 380, p), tk))

# 7. table: ap-s1(出典の行は出典の名前だけにし、調べ方は表で示す)
rows = [('1つのSOC(Yangら)', '実測(自動遮断の後に解析者が扱った件数)', '1日 約13,764件'), ('実務者20人(Alahmadiら)', '回答(自己申告)', '5,000件未満が45%'), ('ベンダーの調査(Vectra AI)', '回答(自己申告)', '1日平均 4,484件')]
td = 'padding:12px;border-bottom:1px solid #D1D5DB'
tb = '<table style="border-collapse:collapse;font-size:24px;width:1150px"><tr style="background:#F3F4F6">' + \
     f'<th style="text-align:left;{td}">出典</th><th style="text-align:left;{td};border:5px solid #111827;border-bottom:none">調べ方</th><th style="text-align:right;{td}">値</th></tr>'
for i, r in enumerate(rows):
    last = ';border-bottom:5px solid #111827' if i == len(rows) - 1 else ''
    tb += f'<tr><td style="{td}">{E(r[0])}</td><td style="{td};border-left:5px solid #111827;border-right:5px solid #111827{last}">{E(r[1])}</td><td style="{td};text-align:right">{E(r[2])}</td></tr>'
tb += '</table>'
tk = '届く量の数字は、調べ方をそろえないと比べられない'
samples['table'] = dict(spec=dict(id='ap-s1', status='done', headline=S['ap-s1']['headline'], takeaway=tk,
    body=dict(type='table', columns=['出典', '調べ方', '値'], rows=[['Yangら', '実測', 'F201'], ['Alahmadiら', '自己申告', 'F202'], ['Vectra AI', '自己申告', 'F203']], highlight='調べ方の列'),
    sources=['F201', 'F202', 'F203'], notes='実測と自己申告は、数え方が違う。'),
    html=page('ap-s1', tb, tk))

# 8. er-diagram: ch2-s1(問い合わせはルールの上から下へ。流れは左から右)
e = box(0, 170, 210, 80, 'データソース') + arrow(210, 210, 300, 210, '集める') + box(300, 170, 230, 80, '集めたデータ')
e += box(300, 10, 230, 80, '分析ルール') + '<line x1="415" y1="90" x2="415" y2="170" stroke="#374151" stroke-width="2"/>' + text(425, 138, '問い合わせる', FIG, color='#374151')
e += arrow(530, 50, 720, 50, '生成する') + box(720, 10, 240, 90, 'アラート', fs=26, bold=True, sw=5, stroke=INK)
e += text(720, 130, 'ルールが探すものを見つけたときに出る', FIG, color='#374151')
e += text(0, 310, '1つのSOCのネットワークの検知の実測では、侵害に至った攻撃に関連するアラートは 0.01%', 24, color='#374151')
tk = 'アラートは「条件に合った」という知らせで、「攻撃だ」という判定ではない'
samples['er-diagram'] = dict(spec=dict(id='ch2-s1', status='done', headline=S['ch2-s1']['headline'], takeaway=tk,
    body=dict(type='er-diagram', elements=['E-sentinel-source', 'D-sentinel-data', 'E-sentinel-rule', 'D-sentinel-alert'], relations=['R-sentinel-source-data', 'R-sentinel-rule-data', 'R-sentinel-rule-alert'], highlight='D-sentinel-alert'),
    text='1つのSOCのネットワークの検知の実測では、侵害に至った攻撃に関連するアラートは {F207}', sources=['F709', 'F619', 'F207'], notes='製品の例は Microsoft Sentinel。ほかの製品でも、条件に合うと知らせる点は同じだが、仕組みの細部は製品ごとに違う。内訳は ch2-s6 で示す。'),
    html=page('ch2-s1', svg(1184, 330, e), tk))

# 9. tree: ch2-s5(戦術を縦に並べ、左右の並びが時間に読めないようにする)
t = box(0, 150, 200, 64, 'ATT&CK', fs=26, bold=True)
tactics = ['初期アクセス', '実行', '横展開', '持ち出し']
t += text(280, 22, '戦術(なぜ)の例', FIG, color='#374151')
for i, k in enumerate(tactics):
    y = 40 + i * 78
    em = k == '実行'
    t += f'<polyline points="200,182 240,182 240,{y+28} 280,{y+28}" fill="none" stroke="#9CA3AF" stroke-width="2"/>'
    t += box(280, y, 200, 56, k, stroke=INK if em else '#9CA3AF', sw=5 if em else 2, bold=em)
t += text(570, 22, '技術(どのように)の例', FIG, color='#374151')
t += '<line x1="480" y1="146" x2="570" y2="146" stroke="#9CA3AF" stroke-width="2"/>' + box(570, 118, 220, 56, 'コマンドの実行')
t += f'<rect x="820" y="60" width="364" height="190" rx="8" fill="#fff" stroke="{C["案の印"]}" stroke-dasharray="8 6" stroke-width="2"/>'
t += text(834, 88, '案', NOTE, color=C['案の印'], bold=True)
for i, l in enumerate(['架空のアラート', '「見慣れないコマンドが動いた」', 'は戦術「実行」に当たる。', 'これを優先度の要因', '「活動の段階」に使う']):
    t += text(834, 122 + i*28, l, FIG)
tk = '戦術に当てはめると、そのアラートが攻撃のどこにいるかを言える'
samples['tree'] = dict(spec=dict(id='ch2-s5', status='done', headline=S['ch2-s5']['headline'], takeaway=tk,
    body=dict(type='tree', root='ATT&CK', children=[dict(name='戦術(例)', items=tactics), dict(name='技術(例)', items=['コマンドの実行'])], example='架空のアラートを戦術「実行」に当てはめる(案)', highlight='実行'),
    sources=['F114', 'F116', 'F125', 'F610'], notes='戦術と技術の名前は例示で、ATT&CK の全体ではない。当てはめ方と優先度へのつなぎ方は案。'),
    html=page('ch2-s5', svg(1184, 360, t), tk))

# 10. cause-chain: ch2-s8(結果の箱は塗らない。強調は原因の1か所)
cc = box(0, 40, 330, 120, '検知のルールが\n緩く書かれている', fs=24, bold=True, stroke=INK, sw=5, fill='#fff')
cc += '<line x1="330" y1="100" x2="430" y2="100" stroke="#374151" stroke-width="6" marker-end="url(#a)"/>' + text(380, 84, 'ので', FIG, 'middle')
cc += box(440, 40, 330, 120, '無害な通信にも\n条件が合ってしまう', fs=24)
cc += '<line x1="770" y1="100" x2="870" y2="100" stroke="#374151" stroke-width="6" marker-end="url(#a)"/>' + text(820, 84, 'ので', FIG, 'middle')
cc += box(880, 40, 280, 120, '誤検知', fs=28, fill='#fff', stroke=C['誤検知'], sw=3, color=C['誤検知'])
cc += text(0, 220, '架空の例: 「宛先のポートが443」だけを条件にしたルールは、ふつうのWebの閲覧にも合う', 24, color='#374151')
tk = '誤検知の原因は、活動の側ではなく検知の条件の側にある'
samples['cause-chain'] = dict(spec=dict(id='ch2-s8', status='done', headline=S['ch2-s8']['headline'], takeaway=tk,
    body=dict(type='cause-chain', chain=['検知のルールが緩く書かれている', '無害な通信にも条件が合ってしまう', '誤検知'], example='架空の例', highlight='chain[0]'),
    sources=['F208', 'F214'], notes='NIST の文書は弱いシグネチャを原因に挙げ、実務者の一部は緩く書かれたシグネチャを挙げた。資料では「ルール」と呼ぶ。'),
    html=page('ch2-s8', svg(1184, 250, cc), tk))

sd = deck / '06-samples'; sd.mkdir(exist_ok=True)
for k, v in samples.items():
    (sd / f'{k}.yaml').write_text('# 型の見本のスライド仕様(工程6)。工程7でそのまま使う。\n' + yaml.safe_dump(v['spec'], allow_unicode=True, sort_keys=False, width=1000))
    (out_html / f'{k}.html').write_text(v['html'])
print(' '.join(samples))
