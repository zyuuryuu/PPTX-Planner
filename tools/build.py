#!/usr/bin/env python3
"""確認用の資料のビルドの最小版。

使い方: python tools/build.py <資料のディレクトリ> --level toc|skeleton|placeholder [--font フォント名]

<資料のディレクトリ>/build/ に deck.pptx と deck.html を出す。型ごとの描画はしない。
"""
import argparse
import html
import subprocess
import sys
from pathlib import Path

import yaml

RELATION_NAMES = {
    "composition": "構成比", "item-comparison": "項目の比較", "trend": "推移", "distribution": "分布",
    "correlation": "相関", "process": "手順", "structure": "構造・階層", "contrast-options": "2案の対比",
    "contrast-before-after": "前後の対比", "causality": "因果", "positioning": "位置づけ",
    "list": "並列の列挙", "statement": "言い切り", "architecture": "構成", "entity-relation": "要素の関係",
    "interaction": "やり取り", "state-transition": "状態の遷移", "branching-flow": "分岐のある流れ",
    "schedule": "日程", "exhibit": "実物の提示",
}
LEVEL_NAMES = {"toc": "目次と章扉", "skeleton": "骨組み", "placeholder": "仮置き"}
NEEDS = {
    "toc": ["03-chapters.yaml"],
    "skeleton": ["03-chapters.yaml", "04-storyline.yaml", "01-sources.yaml"],
    "placeholder": ["03-chapters.yaml", "04-storyline.yaml", "01-sources.yaml", "05-proof.yaml"],
}
FONT_CANDIDATES = ["Noto Sans CJK JP", "Noto Sans JP", "IPAPGothic", "IPAexGothic", "IPAGothic",
                   "Yu Gothic", "Meiryo", "Hiragino Sans", "TakaoPGothic", "VL PGothic"]
FONT_FALLBACK = "Yu Gothic"


def pick_font():
    """この環境にある日本語のフォントを、候補の順に探す。"""
    try:
        out = subprocess.run(["fc-list", ":lang=ja", "family"], capture_output=True, text=True, timeout=20).stdout
    except (OSError, subprocess.SubprocessError):
        return FONT_FALLBACK
    families = {name.strip() for line in out.splitlines() for name in line.split(",")}
    return next((f for f in FONT_CANDIDATES if f in families), FONT_FALLBACK)


def load(root, name):
    path = root / name
    if not path.is_file():
        sys.exit(f"ビルドできない: {path} がない")
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        mark = getattr(e, "problem_mark", None)
        pos = f"{mark.line + 1}行 {mark.column + 1}列" if mark else "位置不明"
        sys.exit(f"ビルドできない: {name}: {pos}: YAMLとして読めない")


def make_slides(root, level):
    """スライドの一覧を作る。1枚は {id, kind, title, body, placeholder}。内容は書き足さない。"""
    data = {n: load(root, n) for n in NEEDS[level]}
    chapters = [c for c in (data["03-chapters.yaml"] or {}).get("chapters") or [] if isinstance(c, dict)]
    story = [s for s in data.get("04-storyline.yaml") or [] if isinstance(s, dict)]
    facts = {f.get("id"): f for f in data.get("01-sources.yaml") or [] if isinstance(f, dict)}
    proofs = {p.get("id"): p for p in data.get("05-proof.yaml") or [] if isinstance(p, dict)}
    slides = []

    def content(s):
        body = []
        for fid in s.get("evidence") or []:
            f = facts.get(fid)
            body.append(f"{fid}: {f.get('statement')}" if f else f"{fid}: (素材台帳にない)")
        if not body:
            body.append("(根拠の事実の指定なし)")
        slide = {"id": s.get("id"), "kind": "付録" if s.get("chapter") == "appendix" else "本編",
                 "title": s.get("headline") or "(見出しなし)", "body": body, "placeholder": []}
        if level == "placeholder":
            p = proofs.get(s.get("id"))
            if p is None:
                slide["placeholder"] = ["(立証の設計がない)"]
            else:
                rel = p.get("relation")
                slide["placeholder"] = [
                    f"主張の種類: {rel}({RELATION_NAMES.get(rel, '語彙にない')})",
                    f"見せるもの: {p.get('show') or '(空)'}",
                    f"注目させる点: {p.get('focus') or '(空)'}",
                ]
        return slide

    if level == "toc":
        slides.append({"id": "toc", "kind": "目次", "title": "目次", "placeholder": [],
                       "body": [f"{i}. {c.get('title')}" for i, c in enumerate(chapters, 1)]})
    for i, c in enumerate(chapters, 1):
        slides.append({"id": f"{c.get('id')}-cover", "kind": "章扉", "title": f"{i}. {c.get('title')}",
                       "body": [c.get("message") or "(message なし)"], "placeholder": []})
        if level != "toc":
            slides += [content(s) for s in story if s.get("chapter") == c.get("id")]
    if level != "toc":
        known = {c.get("id") for c in chapters}
        appendix = [s for s in story if s.get("chapter") == "appendix"]
        if appendix:
            slides.append({"id": "appendix-cover", "kind": "章扉", "title": "付録", "body": [], "placeholder": []})
            slides += [content(s) for s in appendix]
        stray = [s for s in story if s.get("chapter") not in known and s.get("chapter") != "appendix"]
        slides += [dict(content(s), kind="章が章構成にない") for s in stray]
    for n, s in enumerate(slides, 1):
        s["no"] = n
    return slides


def write_pptx(slides, path, font, level):
    from pptx import Presentation
    from pptx.oxml.ns import qn
    from pptx.util import Inches, Pt

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    blank = prs.slide_layouts[6]

    def text(slide, top, height, lines, size, bold=False):
        box = slide.shapes.add_textbox(Inches(0.6), Inches(top), Inches(12.1), Inches(height))
        tf = box.text_frame
        tf.word_wrap = True
        for i, line in enumerate(lines):
            para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            para.space_after = Pt(size * 0.4)
            run = para.add_run()
            run.text = str(line)
            run.font.size, run.font.bold, run.font.name = Pt(size), bold, font
            rpr = run._r.get_or_add_rPr()
            for tag in ("a:ea", "a:cs"):   # 日本語の文字に使うフォントは、別に指定する
                el = rpr.find(qn(tag))
                if el is None:
                    el = rpr.makeelement(qn(tag), {})
                    rpr.append(el)
                el.set("typeface", font)

    for s in slides:
        slide = prs.slides.add_slide(blank)
        text(slide, 0.4, 1.6, [s["title"]], 32, bold=True)
        if s["body"]:
            text(slide, 2.2, 2.2, s["body"], 20)
        if s["placeholder"]:
            text(slide, 4.5, 2.2, ["【仮置き】"] + s["placeholder"], 20)
        text(slide, 6.9, 0.4, [f"{s['no']} / {len(slides)}  {s['id']}  {s['kind']}  ({LEVEL_NAMES[level]}の資料)"], 10)
    prs.save(str(path))


def write_html(slides, path, font, level, deck):
    e = html.escape
    parts = [f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(deck)}({LEVEL_NAMES[level]}の資料)</title>
<style>
body {{ margin: 0; padding: 16px; background: #fff; color: #000;
  font-family: "{e(font)}", "Noto Sans CJK JP", "Yu Gothic", "Meiryo", "Hiragino Sans", sans-serif; }}
section {{ max-width: 960px; margin: 0 auto 16px; padding: 16px 24px; border: 1px solid #999; }}
.meta {{ font-size: 12px; color: #555; margin: 0 0 8px; }}
h2 {{ font-size: 28px; margin: 0 0 16px; }}
ul {{ font-size: 20px; margin: 0 0 12px; padding-left: 1.2em; }}
.placeholder {{ border: 1px dashed #999; padding: 8px 12px; }}
.placeholder p {{ font-size: 14px; margin: 0 0 4px; }}
</style>
</head>
<body>
<p class="meta">{e(deck)} / {LEVEL_NAMES[level]}の資料 / {len(slides)}枚</p>"""]
    for s in slides:
        parts.append(f'<section id="{e(str(s["id"]))}">')
        parts.append(f'<p class="meta">{s["no"]} / {len(slides)} ・ {e(str(s["id"]))} ・ {e(s["kind"])}</p>')
        parts.append(f"<h2>{e(str(s['title']))}</h2>")
        if s["body"]:
            parts.append("<ul>" + "".join(f"<li>{e(str(x))}</li>" for x in s["body"]) + "</ul>")
        if s["placeholder"]:
            parts.append('<div class="placeholder"><p>仮置き</p><ul>'
                         + "".join(f"<li>{e(str(x))}</li>" for x in s["placeholder"]) + "</ul></div>")
        parts.append("</section>")
    parts.append("</body>\n</html>\n")
    path.write_text("\n".join(parts), encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description="確認用の資料のビルド(最小版)")
    ap.add_argument("deck", help="資料のディレクトリ")
    ap.add_argument("--level", required=True, choices=list(NEEDS), help="toc(目次と章扉) / skeleton(骨組み) / placeholder(仮置き)")
    ap.add_argument("--font", help="フォント名。省くと、この環境にある日本語のフォントを探す")
    args = ap.parse_args(argv)
    root = Path(args.deck)
    if not root.is_dir():
        sys.exit(f"資料のディレクトリがない: {root}")
    font = args.font or pick_font()
    slides = make_slides(root, args.level)
    out = root / "build"
    out.mkdir(exist_ok=True)
    write_pptx(slides, out / "deck.pptx", font, args.level)
    write_html(slides, out / "deck.html", font, args.level, root.resolve().name)
    print(f"{LEVEL_NAMES[args.level]}の資料: {len(slides)}枚、フォント {font}")
    print(out / "deck.pptx")
    print(out / "deck.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
