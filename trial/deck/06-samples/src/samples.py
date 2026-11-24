# 工程6の型の見本: スライド仕様(06-samples/<型>.yaml)と、見本の HTML を作る。
# 描画は設計セッションの手書きの HTML/SVG(描画の実装が未定のため)。1280x720。
import sys, yaml, html
from pathlib import Path

deck = Path(sys.argv[1]); out_html = Path(sys.argv[2]); out_html.mkdir(parents=True, exist_ok=True)
S = {s['id']: s for s in yaml.safe_load(open(deck / '04-storyline.yaml'))}
C = yaml.safe_load(open(deck / 'style.yaml'))['common']['colors']
E = html.escape

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{width:1280px;height:720px;background:#fff;font-family:'IPAPGothic','IPAGothic',sans-serif;color:#111827;position:relative;overflow:hidden}
.h{position:absolute;left:48px;top:28px;width:1184px;font-size:32px;font-weight:bold;line-height:1.3}
.src{position:absolute;left:48px;width:1184px;font-size:22px;color:#374151;line-height:1.35}
.fig{position:absolute;left:48px;width:1184px}
.tk{position:absolute;left:0;bottom:0;width:1280px;height:72px;background:#F3F4F6;font-size:26px;padding:20px 48px;border-top:2px solid #D1D5DB}
.note{position:absolute;left:48px;bottom:84px;font-size:19px;color:#4B5563}
.tag{display:inline-block;font-size:19px;padding:2px 10px;border-radius:12px;color:#fff;margin-right:8px;vertical-align:middle}
"""
TAG_P = f'<span class="tag" style="background:{C["案の印"]}">案</span>'
TAG_O = f'<span class="tag" style="background:{C["このSOCの運用の印"]}">運用</span>'

def page(sid, fig, takeaway, note='', fig_top=None):
    s = S[sid]
    h_lines = -(-len(s['headline']) // 37)
    src_top = 28 + h_lines * 42 + 6
    src = s.get('source')
    src_html = f'<div class="src" style="top:{src_top}px">出典: {E(src)}</div>' if src else ''
    src_lines = 0 if not src else -(-len('出典: ' + src) // 52)
    top = fig_top or (src_top + src_lines * 30 + 18)
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="h">{E(s['headline'])}</div>{src_html}
<div class="fig" style="top:{top}px">{fig}</div>
{f'<div class="note">{note}</div>' if note else ''}
<div class="tk">{E(takeaway)}</div></body></html>"""

def box(x, y, w, h, text, fill='#E5E7EB', stroke='#9CA3AF', sw=2, fs=21, bold=False, dash=None, rx=10, color='#111827'):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    lines = text.split('\n')
    ty = y + h / 2 - (len(lines) - 1) * fs * 0.62
    t = ''.join(f'<text x="{x + w/2}" y="{ty + i*fs*1.25 + fs*0.35}" font-size="{fs}" text-anchor="middle" fill="{color}"{" font-weight=\"bold\"" if bold else ""}>{E(l)}</text>' for i, l in enumerate(lines))
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>' + t

def pill(x, y, w, h, text, color, emph=False):
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2}" fill="{color}" stroke="{"#111827" if emph else color}" stroke-width="{5 if emph else 1}"/>'
    return s + f'<text x="{x+w/2}" y="{y+h/2+8}" font-size="22" text-anchor="middle" fill="#fff" font-weight="bold">{E(text)}</text>'

def arrow(x1, y1, x2, y2, label='', w=3):
    s = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#374151" stroke-width="{w}" marker-end="url(#a)"/>'
    if label:
        if abs(y2 - y1) < abs(x2 - x1):
            s += f'<text x="{(x1+x2)/2}" y="{min(y1,y2) - 10}" font-size="19" text-anchor="middle" fill="#374151">{E(label)}</text>'
        else:
            s += f'<text x="{x1 + 10}" y="{(y1+y2)/2 + 7}" font-size="19" fill="#374151">{E(label)}</text>'
    return s

def diamond(cx, cy, w, h, text, fs=20, emph=False):
    p = f'{cx},{cy-h/2} {cx+w/2},{cy} {cx},{cy+h/2} {cx-w/2},{cy}'
    lines = text.split('\n')
    t = ''.join(f'<text x="{cx}" y="{cy - (len(lines)-1)*fs*0.62 + i*fs*1.25 + fs*0.35}" font-size="{fs}" text-anchor="middle"{" font-weight=\"bold\"" if emph else ""}>{E(l)}</text>' for i, l in enumerate(lines))
    return f'<polygon points="{p}" fill="#fff" stroke="{"#111827" if emph else "#6B7280"}" stroke-width="{5 if emph else 2}"/>' + t

def svg(w, h, body):
    return f'<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg"><defs><marker id="a" markerUnits="userSpaceOnUse" markerWidth="16" markerHeight="16" refX="14" refY="8" orient="auto"><path d="M0,0 L16,8 L0,16 z" fill="#374151"/></marker></defs>{body}</svg>'

samples = {}

# 1. statement: ch4-s2
samples['statement'] = dict(spec=dict(id='ch4-s2', status='done', headline=S['ch4-s2']['headline'],
    takeaway='見過ごしの原因は確かめられていないが、慣れが見過ごしにつながりうる',
    body=dict(type='statement', quote='F501', quote_ja='{F501} の日本語訳: システムが頻繁に警報を鳴らしていたのであれば、職員はこのアラートを誤検知とみなした可能性がある', caveat='推定であり、確認された原因ではない', highlight='caveat'),
    sources=['F501'], notes='報告は報道を引いて推定を述べている。報告自身は原因を確かめていない。'),
    html=page('ch4-s2', f'''<div style="border-left:8px solid #9CA3AF;padding:18px 28px;font-size:28px;line-height:1.6;background:#F9FAFB">
「システムが頻繁に警報を鳴らしていた<b>のであれば</b>、職員はこのアラートを誤検知とみなした<b>可能性がある</b>」<div style="font-size:20px;color:#4B5563;margin-top:10px">報告の原文(英語)の日本語訳。報道(Bloomberg Businessweek)を引いた記述</div></div>
<div style="margin-top:34px;display:inline-block;border:5px solid #111827;padding:14px 26px;font-size:28px;font-weight:bold">推定であり、確認された原因ではない</div>''', '見過ごしの原因は確かめられていないが、慣れが見過ごしにつながりうる'))

# 2. plain-list: ch3-s15
items = ['アラートの出どころとID', '調べた経過', '集めた証拠', '現時点の判定の仮説', '次に勧める手順']
samples['plain-list'] = dict(spec=dict(id='ch3-s15', status='done', headline=S['ch3-s15']['headline'],
    takeaway='文脈のない引き継ぎでは、受けた側が調べ直すことになる',
    body=dict(type='plain-list', items=items, highlight='items(5項目そろえること)', mark='案'),
    sources=['F413', 'F414'], notes='送信元のIPアドレスを書き漏らすと、受けた側が元のイベントを探し直すことになる(F414 の例)。'),
    html=page('ch3-s15', TAG_P + '<span style="font-size:22px;color:#374151">上げるときに添える5項目</span>' +
        '<ul style="margin-top:14px;list-style:none;font-size:28px;line-height:1.75;border:5px solid #111827;padding:10px 24px;width:640px">' + ''.join(f'<li>・{E(i)}</li>' for i in items) + '</ul>',
        '文脈のない引き継ぎでは、受けた側が調べ直すことになる'))

# 3. step-flow: ch1-s1
f = box(0, 30, 430, 300, '', fill='#fff', stroke='#111827', sw=5)
f += '<text x="215" y="70" font-size="26" text-anchor="middle" font-weight="bold">1. 3つに分ける</text>'
for i, (k, c) in enumerate([('誤検知', C['誤検知']), ('想定内の検知', C['想定内の検知']), ('攻撃の疑い', C['攻撃の試み'])]):
    f += box(40, 95 + i*75, 350, 58, k, fill=c, stroke=c, color='#fff', fs=24, bold=True)
f += arrow(450, 180, 600, 180)
f += box(620, 30, 520, 300, '', fill='#fff', stroke='#9CA3AF', sw=2)
f += '<text x="880" y="70" font-size="26" text-anchor="middle" font-weight="bold">2. 行き先を決める</text>'
for i, (k, c) in enumerate([('閉じる', C['閉じる']), ('調べる', C['調べる']), ('上げる', C['上げる'])]):
    f += pill(700, 95 + i*75, 360, 58, k, c)
samples['step-flow'] = dict(spec=dict(id='ch1-s1', status='done', headline=S['ch1-s1']['headline'],
    takeaway='まず3つに分け、それから行き先を決める',
    body=dict(type='step-flow', steps=[dict(name='3つに分ける', description='誤検知、想定内の検知、攻撃の疑い'), dict(name='行き先を決める', description='閉じる、調べる、上げる')], highlight='steps[0]'),
    sources=[], notes='分け方は第2章、行き先の決め方は第3章で扱う。'),
    html=page('ch1-s1', svg(1184, 340, f), 'まず3つに分け、それから行き先を決める', fig_top=150))

# 4. flowchart: ch3-s17
g = '<text x="0" y="22" font-size="22" fill="#374151">配属から3か月の新人</text>'
g += box(0, 150, 130, 76, '届いた\nアラート', fs=21)
g += arrow(130, 188, 175, 188)
ds = [(250, '重大度が\nHigh以上?', True), (470, '攻撃の\n試み?', True), (690, '一覧に\nある?', False)]
nxt = [395, 615, 830]
for (x, lab, em), n in zip(ds, nxt):
    g += diamond(x, 188, 150, 104, lab, emph=em)
    g += arrow(x + 75, 188, n, 188, 'いいえ')
    g += arrow(x, 240, x, 320, 'はい')
g += pill(165, 325, 170, 50, 'すぐ上げる', C['上げる'])
g += pill(385, 325, 170, 50, '上げる', C['上げる'])
g += box(585, 322, 210, 72, '想定内の検知として\n記録して閉じる', fill=C['閉じる'], stroke=C['閉じる'], color='#fff', fs=19, rx=24)
g += box(830, 150, 150, 76, '', fill=C['調べる'], stroke=C['調べる'], rx=38)
g += '<text x="905" y="184" font-size="22" text-anchor="middle" fill="#fff" font-weight="bold">調べる</text><text x="905" y="210" font-size="18" text-anchor="middle" fill="#fff">30分まで</text>'
g += f'<rect x="1005" y="40" width="175" height="104" rx="8" fill="#fff" stroke="{C["案の印"]}" stroke-width="2" stroke-dasharray="8 6"/>'
g += f'<text x="1015" y="64" font-size="17" fill="{C["案の印"]}" font-weight="bold">案の基準</text>'
g += '<text x="1092" y="96" font-size="19" text-anchor="middle">誤検知と根拠を</text><text x="1092" y="122" font-size="19" text-anchor="middle">もって言えた</text>'
g += '<polyline points="980,170 992,170 992,92 1003,92" fill="none" stroke="#374151" stroke-width="3" marker-end="url(#a)"/>'
g += arrow(1092, 144, 1092, 172)
g += box(1005, 174, 175, 64, '誤検知として\n記録して閉じる', fill=C['閉じる'], stroke=C['閉じる'], color='#fff', fs=18, rx=24)
g += arrow(905, 226, 905, 318, '30分で根拠なし')
g += box(820, 322, 170, 72, '見たことを\n付けて上げる', fill=C['上げる'], stroke=C['上げる'], color='#fff', fs=19, rx=24)
samples['flowchart'] = dict(spec=dict(id='ch3-s17', status='done', headline=S['ch3-s17']['headline'],
    takeaway='上げる条件を先に見る。閉じるのは、一覧にあるか、調べて誤検知と言えたときだけ',
    body=dict(type='flowchart', scenario='S-newbie-ops', proposal_parts=['R-op-fp'], highlight='上げる条件の2つの分かれ目(重大度、攻撃の試み)を先に確かめる順'),
    sources=['F002', 'F003', 'F005', 'F006', 'F007', 'F008', 'F009'], notes='上から順に確かめ、最初に当たった道に進む。重大度は製品が付けた値。一覧にある作業でも重大度が High 以上なら上げる。'),
    html=page('ch3-s17', TAG_O + svg(1184, 400, g), '上げる条件を先に見る。閉じるのは、一覧にあるか、調べて誤検知と言えたときだけ'))

# 5. architecture-diagram: ch2-s3
a = '<text x="0" y="24" font-size="22" font-weight="bold">EDRの要件の例(NCA)</text>'
a += box(14, 54, 140, 64, '端末', fs=22) + arrow(154, 86, 194, 86) + box(194, 54, 160, 64, 'エージェント', fs=22) + arrow(354, 86, 394, 86) + box(394, 54, 170, 64, '中央の\nデータベース', fs=20)
a += '<text x="0" y="172" font-size="20" fill="#374151">プロセス、接続、ファイルなどの端末の記録を集める</text>'
a += '<rect x="0" y="40" width="580" height="100" fill="none" stroke="#111827" stroke-width="5" rx="12"/>'
a += '<text x="640" y="24" font-size="22" font-weight="bold">製品の例(Microsoft Defender for Endpoint)</text>'
a += box(640, 50, 230, 70, 'Defender for\nEndpoint', fs=20) + arrow(870, 75, 958, 75, '持つ') + box(960, 50, 180, 50, 'センサー', fs=20)
a += arrow(755, 120, 755, 180, '作る') + box(680, 182, 150, 50, 'アラート', fs=21)
a += f'<rect x="900" y="140" width="284" height="230" rx="8" fill="#F9FAFB" stroke="#9CA3AF" stroke-dasharray="4 4"/>'
a += '<text x="914" y="168" font-size="19" font-weight="bold">集める振る舞いの記録</text>'
for i, t in enumerate(['プロセス', 'ネットワーク', 'ログオン', 'レジストリとファイルの変更']):
    a += f'<text x="924" y="{200 + i*30}" font-size="19">・{t}</text>'
a += '<text x="914" y="336" font-size="17" fill="#4B5563">製品やアラートとの</text><text x="914" y="358" font-size="17" fill="#4B5563">経路は出典にない</text>'
samples['architecture-diagram'] = dict(spec=dict(id='ch2-s3', status='done', headline=S['ch2-s3']['headline'],
    takeaway='EDRの材料は、端末の振る舞いを集め続けた記録である',
    body=dict(type='architecture-diagram', elements=['E-endpoint', 'E-edr-agent', 'E-edr-central-db', 'E-mde', 'E-mde-sensor', 'D-mde-telemetry', 'D-mde-alert'],
              relations=['R-endpoint-agent', 'R-agent-central-db', 'R-mde-sensor', 'R-mde-alert'], highlight='左の枠(記録を継続して集める)'),
    sources=['F615', 'F616', 'F618', 'F619'], notes='左は要件の文書、右は製品の文書で、出典が違う。右の記録からアラートへの経路は出典に書かれていないので描かない。'),
    html=page('ch2-s3', svg(1184, 380, a), 'EDRの材料は、端末の振る舞いを集め続けた記録である'))

# 6. pie-chart: ch2-s6 (円。0.01% は引き出し線)
import math
parts = [('攻撃の試み 27%以上', 27, C['攻撃の試み']), ('想定内の検知 49%以上', 49, C['想定内の検知']), ('分類できないもの 約24%', 24, C['分類できないもの'])]
cx, cy, r = 200, 205, 165; ang = -90; p = ''
for i, (k, v, c) in enumerate(parts):
    a1 = math.radians(ang); a2 = math.radians(ang + v * 3.6)
    large = 1 if v > 50 else 0
    x1, y1, x2, y2 = cx + r*math.cos(a1), cy + r*math.sin(a1), cx + r*math.cos(a2), cy + r*math.sin(a2)
    em = i == 0
    p += f'<path d="M{cx},{cy} L{x1:.1f},{y1:.1f} A{r},{r} 0 {large} 1 {x2:.1f},{y2:.1f} z" fill="{c}" stroke="{"#111827" if em else "#fff"}" stroke-width="{6 if em else 2}"/>'
    ang += v * 3.6
p += f'<line x1="{cx}" y1="{cy-r}" x2="{cx}" y2="{cy-r-14}" stroke="{C["侵害に至った攻撃"]}" stroke-width="3"/><text x="{cx+8}" y="{cy-r-4}" font-size="18" fill="#374151">0.01%(細すぎて見えない)</text>'
leg = [('侵害に至った攻撃 0.01%', C['侵害に至った攻撃'], False), ('攻撃の試み 27%以上(下限)', C['攻撃の試み'], True), ('想定内の検知 49%以上(下限)', C['想定内の検知'], False), ('分類できないもの 約24%', C['分類できないもの'], False)]
for i, (k, c, em) in enumerate(leg):
    p += f'<rect x="460" y="{60 + i*62}" width="34" height="34" fill="{c}"/>'
    p += f'<text x="508" y="{86 + i*62}" font-size="26"{" font-weight=\"bold\"" if em else ""}>{E(k)}</text>'
p += '<text x="460" y="330" font-size="20" fill="#374151">ネットワークの検知のアラート 約1,443万件の内訳(著者らの分類)</text>'
samples['pie-chart'] = dict(spec=dict(id='ch2-s6', status='done', headline=S['ch2-s6']['headline'],
    takeaway='誤検知でも想定内でもない攻撃の試みが、少なくとも4分の1ある',
    body=dict(type='pie-chart', data=[dict(label='侵害に至った攻撃', value='F207'), dict(label='攻撃の試み', value='F207', bound='以上'), dict(label='想定内の検知', value='F207', bound='以上'), dict(label='分類できないもの', value='F207')], highlight='攻撃の試み'),
    sources=['F207'], notes='27%と49%は論文が「少なくとも」とする下限。想定内の検知は明確な証拠があるものだけを数えた。'),
    html=page('ch2-s6', svg(1184, 360, p), '誤検知でも想定内でもない攻撃の試みが、少なくとも4分の1ある'))

# 7. table: ap-s1
rows = [('1つのSOC(Yangら)', '実測(自動遮断の後に解析者が扱った件数)', '1日 約13,764件'), ('実務者20人(Alahmadiら)', '回答(自己申告)', '5,000件未満が45%'), ('ベンダーの調査(Vectra AI)', '回答(自己申告)', '1日平均 4,484件')]
tb = '<table style="border-collapse:collapse;font-size:24px;width:1150px"><tr style="background:#F3F4F6"><th style="text-align:left;padding:12px;border-bottom:2px solid #9CA3AF">出典</th><th style="text-align:left;padding:12px;border-bottom:2px solid #9CA3AF;border:5px solid #111827">調べ方</th><th style="text-align:right;padding:12px;border-bottom:2px solid #9CA3AF">値</th></tr>'
for r in rows:
    tb += f'<tr><td style="padding:12px;border-bottom:1px solid #D1D5DB">{E(r[0])}</td><td style="padding:12px;border-bottom:1px solid #D1D5DB;border-left:5px solid #111827;border-right:5px solid #111827">{E(r[1])}</td><td style="padding:12px;border-bottom:1px solid #D1D5DB;text-align:right">{E(r[2])}</td></tr>'
tb = tb.replace('</table>', '') + '<tr><td></td><td style="border-top:5px solid #111827"></td><td></td></tr></table>'
samples['table'] = dict(spec=dict(id='ap-s1', status='done', headline=S['ap-s1']['headline'],
    takeaway='届く量の数字は、調べ方をそろえないと比べられない',
    body=dict(type='table', columns=['出典', '調べ方', '値'], rows=[['Yangら', '実測', 'F201'], ['Alahmadiら', '自己申告', 'F202'], ['Vectra AI', '自己申告', 'F203']], highlight='調べ方の列'),
    sources=['F201', 'F202', 'F203'], notes='実測と自己申告は、数え方が違う。'),
    html=page('ap-s1', tb, '届く量の数字は、調べ方をそろえないと比べられない'))

# 8. er-diagram: ch2-s1
e = box(0, 60, 210, 80, 'データソース', fs=22) + arrow(210, 100, 300, 100, '集める') + box(300, 60, 210, 80, '集めたデータ', fs=22)
e += box(640, 60, 210, 80, '分析ルール', fs=22) + arrow(640, 100, 512, 100) + '<text x="520" y="88" font-size="20">問い合わせる</text>'
e += arrow(850, 100, 940, 100, '生成する') + box(940, 50, 220, 100, 'アラート', fs=26, bold=True, sw=5, stroke='#111827')
e += '<text x="940" y="180" font-size="20" fill="#374151">ルールが探すものを見つけたときに出る</text>'
e += '<text x="0" y="250" font-size="22" fill="#374151">1つのSOCのネットワークの検知の実測では、侵害に至った攻撃に関連するアラートは 0.01%(10枚目で詳しく)</text>'
samples['er-diagram'] = dict(spec=dict(id='ch2-s1', status='done', headline=S['ch2-s1']['headline'],
    takeaway='アラートは「条件に合った」という知らせで、「攻撃だ」という判定ではない',
    body=dict(type='er-diagram', elements=['E-sentinel-source', 'D-sentinel-data', 'E-sentinel-rule', 'D-sentinel-alert'], relations=['R-sentinel-source-data', 'R-sentinel-rule-data', 'R-sentinel-rule-alert'], highlight='D-sentinel-alert'),
    text='1つのSOCのネットワークの検知の実測では、侵害に至った攻撃に関連するアラートは {F207}', sources=['F709', 'F619', 'F207'], notes='製品の例は Microsoft Sentinel。ほかの製品でも、条件に合うと知らせる点は同じだが、仕組みの細部は製品ごとに違う。'),
    html=page('ch2-s1', svg(1184, 280, e), 'アラートは「条件に合った」という知らせで、「攻撃だ」という判定ではない'))

# 9. tree: ch2-s5 (戦術を縦に並べ、左右の並びが時間に読めないようにする)
t = box(0, 150, 200, 64, 'ATT&CK', fs=24, bold=True)
tactics = ['初期アクセス', '実行', '横展開', '持ち出し']
t += '<text x="280" y="22" font-size="20" fill="#374151">戦術(なぜ)の例</text>'
for i, k in enumerate(tactics):
    y = 40 + i * 78
    em = k == '実行'
    t += f'<polyline points="200,182 240,182 240,{y+28} 280,{y+28}" fill="none" stroke="#9CA3AF" stroke-width="2"/>'
    t += box(280, y, 190, 56, k, fs=21, stroke='#111827' if em else '#9CA3AF', sw=5 if em else 2, bold=em)
t += '<text x="560" y="22" font-size="20" fill="#374151">技術(どのように)の例</text>'
t += '<line x1="470" y1="146" x2="560" y2="146" stroke="#9CA3AF" stroke-width="2"/>' + box(560, 118, 210, 56, 'コマンドの実行', fs=20)
t += f'<rect x="820" y="90" width="364" height="140" rx="8" fill="#fff" stroke="{C["案の印"]}" stroke-dasharray="8 6" stroke-width="2"/>'
t += f'<text x="834" y="118" font-size="18" fill="{C["案の印"]}" font-weight="bold">案</text>'
t += '<text x="834" y="150" font-size="20">架空のアラート</text><text x="834" y="176" font-size="20">「見慣れないコマンドが動いた」は</text><text x="834" y="202" font-size="20">戦術「実行」に当たる。これを</text><text x="834" y="226" font-size="20">優先度の要因「活動の段階」に使う</text>'
samples['tree'] = dict(spec=dict(id='ch2-s5', status='done', headline=S['ch2-s5']['headline'],
    takeaway='戦術に当てはめると、そのアラートが攻撃のどこにいるかを言える',
    body=dict(type='tree', root='ATT&CK', children=[dict(name='戦術(例)', items=tactics), dict(name='技術(例)', items=['コマンドの実行'])], example='架空のアラートを戦術「実行」に当てはめる(案)', highlight='実行'),
    sources=['F114', 'F116', 'F125', 'F610'], notes='戦術と技術の名前は例示で、ATT&CK の全体ではない。当てはめ方と優先度へのつなぎ方は案。'),
    html=page('ch2-s5', svg(1184, 360, t), '戦術に当てはめると、そのアラートが攻撃のどこにいるかを言える'))

# 10. cause-chain: ch2-s8
cc = box(0, 60, 330, 120, '検知のルールが\n緩く書かれている', fs=24, bold=True, stroke='#111827', sw=5)
cc += '<line x1="330" y1="120" x2="430" y2="120" stroke="#374151" stroke-width="6" marker-end="url(#a)"/><text x="355" y="105" font-size="21">ので</text>'
cc += box(440, 60, 330, 120, '無害な通信にも\n条件が合ってしまう', fs=24)
cc += '<line x1="770" y1="120" x2="870" y2="120" stroke="#374151" stroke-width="6" marker-end="url(#a)"/><text x="795" y="105" font-size="21">ので</text>'
cc += box(880, 60, 280, 120, '誤検知', fs=28, bold=True, fill=C['誤検知'], stroke=C['誤検知'], color='#fff')
cc += '<text x="0" y="240" font-size="20" fill="#374151">架空の例: 「宛先のポートが443」だけを条件にしたルールは、ふつうのWebの閲覧にも合う</text>'
samples['cause-chain'] = dict(spec=dict(id='ch2-s8', status='done', headline=S['ch2-s8']['headline'],
    takeaway='誤検知の原因は、活動の側ではなく検知の条件の側にある',
    body=dict(type='cause-chain', chain=['検知のルールが緩く書かれている', '無害な通信にも条件が合ってしまう', '誤検知'], example='架空の例', highlight='chain[0]'),
    sources=['F208', 'F214'], notes='NIST の文書は弱いシグネチャを原因に挙げ、実務者の一部は緩く書かれたシグネチャを挙げた。資料では「ルール」と呼ぶ。'),
    html=page('ch2-s8', svg(1184, 270, cc), '誤検知の原因は、活動の側ではなく検知の条件の側にある'))

sd = deck / '06-samples'; sd.mkdir(exist_ok=True)
for k, v in samples.items():
    (sd / f'{k}.yaml').write_text('# 型の見本のスライド仕様(工程6)。工程7でそのまま使う。\n' + yaml.safe_dump(v['spec'], allow_unicode=True, sort_keys=False, width=1000))
    (out_html / f'{k}.html').write_text(v['html'])
print(' '.join(samples))
