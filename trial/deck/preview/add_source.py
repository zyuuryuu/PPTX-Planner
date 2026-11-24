# 骨組みの資料の HTML に、04-storyline.yaml の source を出典の行として見出しの下に足す(build.py は source を知らないため)
import sys,yaml,re,html
deck,out=sys.argv[1],sys.argv[2]
S={s['id']:s for s in yaml.safe_load(open(deck+'/04-storyline.yaml'))}
t=open(deck+'/build/deck.html').read()
def f(mo):
    sid=mo.group(1); body=mo.group(0); s=S.get(sid)
    if s and s.get('source'):
        body=body.replace('</h2>','</h2>\n<p class="source" style="font-size:1.1em;margin:.2em 0 .8em;color:#333">出典: '+html.escape(s['source'])+'</p>',1)
    return body
t=re.sub(r'<section id="([^"]+)">.*?</section>',f,t,flags=re.S)
open(out,'w').write(t)
