// render.py の補助: 描いた HTML をブラウザ(Playwright の Chromium)で開き、診断を取り、PNG を撮る。
// 使い方: node tools/render_shot.js <jobs.json> <results.json>
// jobs.json: [{id, html, png, min: {role: px}}]。png が null なら撮らない。
const fs = require('fs');
const { chromium } = require('playwright');

const CHECK = (min) => {
  const out = [];
  const BAND_TOP = 648, RIGHT = 1280 - 48 + 2, LEFT = 48 - 2;
  const r = (el) => el.getBoundingClientRect();
  const name = (el) => el.dataset.name || el.dataset.id || (el.textContent || '').trim().slice(0, 24);
  // 1. 文字の大きさの下限
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const seen = new Set();
  while (walker.nextNode()) {
    const t = walker.currentNode;
    if (!t.textContent.trim()) continue;
    const el = t.parentElement;
    if (seen.has(el)) continue;
    seen.add(el);
    const roleEl = el.closest('[data-role]');
    const role = roleEl ? roleEl.dataset.role : null;
    const fs = parseFloat(getComputedStyle(el).fontSize);
    const lim = role && min[role] !== undefined ? min[role] : min.note;
    if (fs < lim - 0.01) out.push({ kind: 'font-too-small', severity: 'error', target: name(el), message: `文字の大きさ ${fs.toFixed(1)}px が下限 ${lim.toFixed(1)}px(${role || '役割なし'})より小さい` });
    if (!role) out.push({ kind: 'unrendered', severity: 'warning', target: name(el), message: '役割(data-role)のない文字がある(描画の実装の誤り)' });
  }
  // 2. 見出しは2行まで、結論1行は1行
  const h = document.querySelector('.h');
  if (h) {
    const lh = parseFloat(getComputedStyle(h).lineHeight);
    const lines = Math.round(r(h).height / lh);
    if (lines > 2) out.push({ kind: 'overflow', severity: 'error', target: 'headline', message: `見出しが ${lines} 行になった(上限は2行)` });
  }
  for (const el of document.querySelectorAll('.fit')) {
    if (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1)
      out.push({ kind: 'overflow', severity: 'error', target: el.dataset.name || name(el), message: '枠に収まらない' });
  }
  // 2b. 語の途中での折り返し(HTML の文。語の区切りは Intl.Segmenter で判定する)
  const seg = new Intl.Segmenter('ja', { granularity: 'word' });
  const inWord = (s, i) => { let p = 0; for (const x of seg.segment(s)) { if (i > p && i < p + x.segment.length && x.isWordLike) return x.segment; p += x.segment.length; } return null; };
  for (const el of document.querySelectorAll('[data-role]')) {
    if (el.closest('svg') || el.closest('.ph')) continue;   // 仮置きの枠は対象外
    const tn = [...el.childNodes].filter((n) => n.nodeType === 3);
    for (const n of tn) {
      const s = n.textContent; let prevTop = null;
      for (let i = 0; i < s.length; i++) {
        if (!s[i].trim()) continue;
        const rg = document.createRange(); rg.setStart(n, i); rg.setEnd(n, i + 1);
        const rc = rg.getClientRects()[0]; if (!rc) continue;
        if (prevTop !== null && rc.top > prevTop + 4) {
          const before = s.slice(0, i).replace(/\u2060/g, ''), after = s.slice(i);
          if (/[A-Za-z0-9]-$/.test(before.trimEnd()) && /^[A-Za-z0-9]/.test(after))
            out.push({ kind: 'overflow', severity: 'warning', target: el.dataset.role, message: `英数字の語の途中(ハイフンの後)で折り返した: (${before.slice(-8)}|${after.slice(0, 6)})` });
          const w = inWord(s, i);
          if (w) out.push({ kind: 'overflow', severity: 'warning', target: el.dataset.role, message: `語の途中で折り返した: 「${w}」(${s.slice(Math.max(0, i - 6), i)}|${s.slice(i, i + 6)})` });
        }
        prevTop = rc.top;
      }
    }
  }
  // SVG: 同じ枠の中の続く行の境目
  const byBox = {};
  for (const t of document.querySelectorAll('text[data-in]')) (byBox[t.dataset.in] = byBox[t.dataset.in] || []).push(t.textContent);
  for (const [box, lines] of Object.entries(byBox)) {
    for (let k = 1; k < lines.length; k++) {
      const asc = /[A-Za-z0-9]$/.test(lines[k - 1]) && /^[A-Za-z0-9]/.test(lines[k]);
      const s = lines[k - 1] + (asc ? ' ' : '') + lines[k], i = lines[k - 1].length + (asc ? 1 : 0);
      const w = inWord(s, i);
      if (w) out.push({ kind: 'overflow', severity: 'warning', target: box, message: `語の途中で折り返した: 「${w}」(${lines[k - 1].slice(-6)}|${lines[k].slice(0, 6)})` });
    }
  }
  // 3. 上の領域(見出しから図の下の文まで)が、結論の帯や右端を越えない
  for (const el of document.querySelectorAll('.top *')) {
    const b = r(el);
    if (b.width === 0 && b.height === 0) continue;
    if (el.closest('svg') && el.tagName !== 'svg' && !el.dataset.ov && el.tagName !== 'text') continue;
    if (b.bottom > BAND_TOP + 0.5 && !el.closest('.tk')) {
      out.push({ kind: 'overflow', severity: 'error', target: name(el), message: `下端 ${b.bottom.toFixed(0)}px が結論の帯(${BAND_TOP}px)に重なる` });
      break;
    }
  }
  for (const el of document.querySelectorAll('.top *')) {
    const b = r(el);
    if (b.width === 0) continue;
    if (b.right > RIGHT || b.left < LEFT) {
      if (el.tagName === 'svg' || el.dataset.ov || el.tagName === 'text' || !el.closest('svg')) {
        out.push({ kind: 'overflow', severity: 'error', target: name(el), message: `横に余白を越える(左 ${b.left.toFixed(0)}px、右 ${b.right.toFixed(0)}px)` });
        break;
      }
    }
  }
  // 4. SVG の文字が、属する図形に収まる
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
  // 5. 要素の重なり(data-ov を持つ図形と文字。入れ子と、自分の枠の中の文字は除く)
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
  return out;
};

(async () => {
  const jobs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
  const results = {};
  for (const j of jobs) {
    await page.goto('file://' + j.html);
    await page.evaluate(() => document.fonts.ready);
    results[j.id] = await page.evaluate(CHECK, j.min);
    if (j.png) await page.screenshot({ path: j.png });
  }
  await browser.close();
  fs.writeFileSync(process.argv[3], JSON.stringify(results, null, 1));
})().catch((e) => { console.error(e); process.exit(1); });
