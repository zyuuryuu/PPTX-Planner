#!/usr/bin/env python3
"""確認用の資料(目次と章扉、骨組み、仮置き)をビルドする。

使い方: python3 tools/build.py <資料のディレクトリ> --level toc|skeleton|placeholder [--pdf] [--no-png] [--out 出力先]

描くのは tools/render.py である。完成形と同じ枠(題、要点、中身、脚注)で描く。この道具は、--level を必須にした入口である。
出すもの(既定は <資料のディレクトリ>/build/<level>/): deck.html(1つのファイルで全スライド)、deck.pdf(--pdf)、slides/*.png、diagnostics.json。

| --level     | 読む成果物                                  | 載るもの |
| toc         | 03-chapters.yaml                            | 目次と、章扉(章の題、問い、章の要点、節の題と要点) |
| skeleton    | 加えて 04-storyline.yaml、01-sources.yaml   | 目次、章扉、各スライドの題、要点(要点のないスライドは役割)、根拠の事実の statement、節のまとめ、章のまとめ、出典の一覧 |
| placeholder | 加えて 05-proof.yaml                        | 骨組みの中身の代わりに、図の型の仮置き(見せるもの、注目させる点) |
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description='確認用の資料(目次と章扉、骨組み、仮置き)をビルドする')
    ap.add_argument('deck', help='資料のディレクトリ')
    ap.add_argument('--level', required=True, choices=['toc', 'skeleton', 'placeholder'], help='toc(目次と章扉) / skeleton(骨組み) / placeholder(仮置き)')
    ap.add_argument('--pdf', action='store_true', help='全スライドを1つの PDF(deck.pdf)にまとめて出す')
    ap.add_argument('--no-png', action='store_true', help='PNG を撮らない')
    ap.add_argument('--out', help='出力先。既定は <資料のディレクトリ>/build/<level>')
    ap.add_argument('--show-ids', action='store_true', help='deck.html の見出しに、スライドのIDと診断の件数を出す(作業用)')
    a = ap.parse_args(argv)
    args = [a.deck, '--level', a.level]
    for flag in ('pdf', 'no_png', 'show_ids'):
        if getattr(a, flag):
            args.append('--' + flag.replace('_', '-'))
    if a.out:
        args += ['--out', a.out]
    return render.main(args)


if __name__ == '__main__':
    sys.exit(main())
