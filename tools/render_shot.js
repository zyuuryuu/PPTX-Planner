// render.py の補助: 描いた HTML をブラウザ(Playwright の Chromium)で開き、診断を取り、PNG を撮り、PDF を作る。
// 使い方: node tools/render_shot.js <jobs.json> <results.json>
// jobs.json: {min: {役割: px}, contrast: [下限, 大きな文字の下限], slides: [{id, html, png}], pdf: {html, out, width, height} | null}
// png が null なら撮らない。results.json: {スライドのID: {diagnostics, titles, points, text_contrast_min}}
const fs = require('fs');
const { chromium } = require('playwright');

const CHECK = ([min, cmin]) => {
  const out = [];
  const W = 1280, H = 720, RIGHT = W - 48 + 2, LEFT = 48 - 2;
  const r = (el) => el.getBoundingClientRect();
  const name = (el) => el.dataset.name || el.dataset.id || (el.textContent || '').trim().slice(0, 24);
  const slide = document.querySelector('.slide');
  const lines = (el) => Math.round(r(el).height / parseFloat(getComputedStyle(el).lineHeight));
  const own = (el) => { const c = el.cloneNode(true); c.querySelectorAll('.wk').forEach((x) => x.remove()); return c.textContent.trim(); };

  // 1. 文字の大きさの下限と、文字と背景の色の差
  const rgb = (s) => { const m = /rgba?\(([^)]+)\)/.exec(s || ''); if (!m) return null; const v = m[1].split(',').map(parseFloat); return v.length > 3 && v[3] === 0 ? null : v.slice(0, 3); };
  const lum = (c) => { const v = c.map((x) => { x /= 255; return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); }); return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]; };
  const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
  const background = (el) => {
    if (el.closest('svg')) {
      const shape = el.dataset.in ? document.getElementById(el.dataset.in) : null;
      const c = shape ? rgb(getComputedStyle(shape).fill) : null;
      return c || [255, 255, 255];
    }
    for (let p = el; p; p = p.parentElement) { const c = rgb(getComputedStyle(p).backgroundColor); if (c) return c; }
    return [255, 255, 255];
  };
  let cmin_seen = null;
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const seen = new Set();
  while (walker.nextNode()) {
    const t = walker.currentNode;
    if (!t.textContent.trim()) continue;
    const el = t.parentElement;
    if (seen.has(el)) continue;
    seen.add(el);
    const cs = getComputedStyle(el);
    const roleEl = el.closest('[data-role]');
    const role = roleEl ? roleEl.dataset.role : null;
    const size = parseFloat(cs.fontSize);
    const lim = role && min[role] !== undefined ? min[role] : min.note;
    if (size < lim - 0.01) out.push({ kind: 'font-too-small', severity: 'error', target: name(el), message: `文字の大きさ ${size.toFixed(1)}px が下限 ${lim.toFixed(1)}px(${role || '役割なし'})より小さい` });
    if (!role) out.push({ kind: 'role', severity: 'warning', target: name(el), message: '役割(data-role)のない文字がある(描画の実装の誤り)' });
    const fg = rgb(el.closest('svg') ? cs.fill : cs.color);
    if (fg) {
      const c = ratio(fg, background(el));
      const bold = parseInt(cs.fontWeight, 10) >= 600;
      const need = size >= 24 || (bold && size >= 18.66) ? cmin[1] : cmin[0];
      if (cmin_seen === null || c < cmin_seen) cmin_seen = c;
      if (c < need) out.push({ kind: 'contrast', severity: 'error', target: name(el), message: `文字と背景の色の差が小さい(コントラスト比 ${c.toFixed(2)}、下限 ${need})` });
    }
  }

  // 2. 題は1つで1行。要点は1か所で2行まで
  const titles = [...document.querySelectorAll('[data-role="title"]')];
  if (titles.length !== 1) out.push({ kind: 'unrendered', severity: 'error', target: 'title', message: `題が ${titles.length} か所にある(1か所だけに描く)` });
  for (const t of titles) {
    const n = lines(t);
    if (n > 1) out.push({ kind: 'title-lines', severity: 'error', target: 'title', message: `題が1行に収まらない(${n} 行になった)` });
  }
  const points = [...document.querySelectorAll('[data-role="point"]')];
  if (points.length > 1) out.push({ kind: 'duplicate', severity: 'error', target: 'point', message: `要点が ${points.length} か所に描かれている(1か所だけに描く)` });
  for (const p of points) {
    const n = lines(p);
    if (n > 2) out.push({ kind: 'point-lines', severity: 'error', target: 'point', message: `要点が2行を超える(${n} 行になった)` });
  }
  const fn = document.querySelector('.fn');
  if (fn && lines(fn) > 2) out.push({ kind: 'footnote-lines', severity: 'warning', target: 'footnote', message: `脚注が ${lines(fn)} 行になった(目安は2行まで)` });

  // 3. 語の途中での折り返し(HTML の文。語の区切りは Intl.Segmenter で判定する)
  const seg = new Intl.Segmenter('ja', { granularity: 'word' });
  const inWord = (s, i) => { let p = 0; for (const x of seg.segment(s)) { if (i > p && i < p + x.segment.length && x.isWordLike) return x.segment; p += x.segment.length; } return null; };
  const textNodes = (el) => { const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); const a = []; while (w.nextNode()) a.push(w.currentNode); return a; };
  const done = new Set();
  for (const el of document.querySelectorAll('[data-role]')) {
    if (el.closest('svg') || el.closest('.ph')) continue;   // 仮置きの枠は対象外
    for (const n of textNodes(el)) {
      if (done.has(n)) continue;
      done.add(n);
      const s = n.textContent; let prevTop = null;
      for (let i = 0; i < s.length; i++) {
        if (!s[i].trim()) continue;
        const rg = document.createRange(); rg.setStart(n, i); rg.setEnd(n, i + 1);
        const rc = rg.getClientRects()[0]; if (!rc) continue;
        if (prevTop !== null && rc.top > prevTop + 4) {
          const before = s.slice(0, i), after = s.slice(i);
          if (/[A-Za-z0-9]-$/.test(before.trimEnd()) && /^[A-Za-z0-9]/.test(after))
            out.push({ kind: 'word-break', severity: 'warning', target: el.dataset.role, message: `英数字の語の途中(ハイフンの後)で折り返した: (${before.slice(-8)}|${after.slice(0, 6)})` });
          const w = inWord(s, i);
          if (w) out.push({ kind: 'word-break', severity: 'warning', target: el.dataset.role, message: `語の途中で折り返した: 「${w}」(${s.slice(Math.max(0, i - 6), i)}|${s.slice(i, i + 6)})` });
        }
        prevTop = rc.top;
      }
    }
  }
  // SVG: 同じ枠の中の続く行の境目
  const byBox = {};
  for (const t of document.querySelectorAll('text[data-in]')) (byBox[t.dataset.in] = byBox[t.dataset.in] || []).push(t.textContent);
  for (const [box, ls] of Object.entries(byBox)) {
    for (let k = 1; k < ls.length; k++) {
      const asc = /[A-Za-z0-9]$/.test(ls[k - 1]) && /^[A-Za-z0-9]/.test(ls[k]);
      const s = ls[k - 1] + (asc ? ' ' : '') + ls[k], i = ls[k - 1].length + (asc ? 1 : 0);
      const w = inWord(s, i);
      if (w) out.push({ kind: 'word-break', severity: 'warning', target: box, message: `語の途中で折り返した: 「${w}」(${ls[k - 1].slice(-6)}|${ls[k].slice(0, 6)})` });
    }
  }

  // 4. あふれ: 中身が中身の領域に収まる。枠の部分(題、要点、脚注)がスライドに収まる。左右の余白を越えない
  const main = document.querySelector('.main');
  if (main) {
    const m = r(main);
    let over = 0;
    for (const el of main.children) {
      const b = r(el);
      if (b.width === 0 && b.height === 0) continue;
      over = Math.max(over, b.bottom - m.bottom, m.top - b.top);
    }
    if (over > 1) out.push({ kind: 'overflow', severity: 'error', target: 'body', message: `中身が、使える領域(高さ ${m.height.toFixed(0)}px)に収まらない(${over.toFixed(0)}px はみ出す)` });
  }
  for (const el of slide.children) {
    const b = r(el);
    if (b.bottom > H + 0.5) out.push({ kind: 'overflow', severity: 'error', target: el.className, message: `下端 ${b.bottom.toFixed(0)}px がスライドの下端を越える` });
  }
  for (const el of slide.querySelectorAll('*')) {
    const b = r(el);
    if (b.width === 0) continue;
    if (b.right > RIGHT || b.left < LEFT) {
      if (el.tagName === 'svg' || el.dataset.ov || el.tagName === 'text' || !el.closest('svg')) {
        out.push({ kind: 'overflow', severity: 'error', target: name(el), message: `横に余白を越える(左 ${b.left.toFixed(0)}px、右 ${b.right.toFixed(0)}px)` });
        break;
      }
    }
  }

  // 5. SVG の文字が、属する図形に収まる
  for (const t of document.querySelectorAll('text[data-in]')) {
    const shape = document.getElementById(t.dataset.in);
    if (!shape) continue;
    const a = r(t), s = r(shape);
    const pad = 1;
    if (shape.dataset.shape === 'diamond') {
      const cx = (s.left + s.right) / 2, cy = (s.top + s.bottom) / 2, hw = s.width / 2, hh = s.height / 2;
      // 文字の外接矩形の上下は字の余白を含むため、縦は字の大きさの 0.8 倍で見る
      const fsz = parseFloat(getComputedStyle(t).fontSize);
      const my = (a.top + a.bottom) / 2, ah = Math.min(a.height, fsz * 0.8) / 2;
      const corners = [[a.left, my - ah], [a.right, my - ah], [a.left, my + ah], [a.right, my + ah]];
      if (corners.some(([x, y]) => Math.abs(x - cx) / hw + Math.abs(y - cy) / hh > 1.02))
        out.push({ kind: 'overflow', severity: 'error', target: shape.dataset.name || t.textContent, message: `ひし形に文字が収まらない: 「${t.textContent}」` });
    } else if (a.left < s.left - pad || a.right > s.right + pad || a.top < s.top - pad - 4 || a.bottom > s.bottom + pad + 4) {
      out.push({ kind: 'overflow', severity: 'error', target: shape.dataset.name || t.textContent, message: `枠に文字が収まらない: 「${t.textContent}」` });
    }
  }

  // 6. 要素の重なり(data-ov を持つ図形と文字。入れ子と、自分の枠の中の文字は除く)
  const items = [...document.querySelectorAll('[data-ov]')];
  const rects = items.map((el) => r(el));
  const anc = (el) => (el.dataset.anc || '').split(' ').filter(Boolean);
  for (let i = 0; i < items.length; i++) {
    for (let j = i + 1; j < items.length; j++) {
      const A = items[i], B = items[j], a = rects[i], b = rects[j];
      const ix = Math.min(a.right, b.right) - Math.max(a.left, b.left);
      const iy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
      if (ix <= 2 || iy <= 2) continue;
      const ida = A.dataset.ov, idb = B.dataset.ov;
      if (anc(A).includes(idb) || anc(B).includes(ida)) continue;
      if (A.dataset.in === idb || B.dataset.in === ida) continue;
      if (A.dataset.in && A.dataset.in === B.dataset.in) continue;
      // ひし形は外接矩形でなく形で見る: 相手の矩形の角か辺の中点がひし形の中にあるか
      const dia = A.dataset.shape === 'diamond' ? [a, b] : B.dataset.shape === 'diamond' ? [b, a] : null;
      if (dia) {
        const [d, o] = dia;
        const cx = (d.left + d.right) / 2, cy = (d.top + d.bottom) / 2, hw = d.width / 2, hh = d.height / 2;
        const xs = [o.left, (o.left + o.right) / 2, o.right], ys = [o.top, (o.top + o.bottom) / 2, o.bottom];
        let hit = false;
        for (const x of xs) for (const y of ys) if (Math.abs(x - cx) / hw + Math.abs(y - cy) / hh < 0.97) hit = true;
        if (o.left < cx && o.right > cx && o.top < cy && o.bottom > cy) hit = true;
        if (!hit) continue;
      }
      out.push({ kind: 'overlap', severity: 'error', target: `${name(A)} / ${name(B)}`, message: `要素が重なる(${ix.toFixed(0)}x${iy.toFixed(0)}px)` });
    }
  }
  return { diagnostics: out, titles: titles.map(own), points: points.map(own), text_contrast_min: cmin_seen === null ? null : Math.round(cmin_seen * 100) / 100 };
};

(async () => {
  const jobs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
  const results = {};
  for (const j of jobs.slides) {
    await page.goto('file://' + j.html);
    await page.evaluate(() => document.fonts.ready);
    results[j.id] = await page.evaluate(CHECK, [jobs.min, jobs.contrast]);
    if (j.png) await page.screenshot({ path: j.png });
  }
  if (jobs.pdf) {
    await page.goto('file://' + jobs.pdf.html);
    await page.evaluate(() => document.fonts.ready);
    await page.emulateMedia({ media: 'print' });
    await page.pdf({ path: jobs.pdf.out, width: jobs.pdf.width + 'px', height: jobs.pdf.height + 'px', printBackground: true, preferCSSPageSize: true });
  }
  await browser.close();
  fs.writeFileSync(process.argv[3], JSON.stringify(results, null, 1));
})().catch((e) => { console.error(e); process.exit(1); });
