#!/usr/bin/env python3
"""從 Part 3 定稿的後台模擬器 sim.html 產生 part4_timeline.html。

原則同 build_part4_exception.py：定稿頁 100% 不動，只「注入」臨時預約關閉——
時間軸可框選「桌 × 時段」關閉、關閉區塊以斜線呈現、標題列多一顆總覽 chip。
資料存獨立 sessionStorage key（p4_closures，與例外頁整合版共用同一把 key）。
sim.html 更新時重跑本腳本即可同步。
"""
import pathlib
import sys

root = pathlib.Path(__file__).resolve().parent.parent
src = (root / "sim.html").read_text(encoding="utf-8")


def inject(hay, anchor, addition, before=True, label=""):
    if hay.count(anchor) != 1:
        sys.exit(f"錨點不唯一或不存在（{label}）：{anchor[:60]!r} count={hay.count(anchor)}")
    return hay.replace(anchor, (addition + anchor) if before else (anchor + addition))


# ── 1) CSS ──────────────────────────────────────────────────────────
src = inject(src, "</style>", """
/* ===== Part4 注入：臨時預約關閉 ===== */
.tl-row{cursor:crosshair}
.p4-closed{position:absolute;top:2px;bottom:2px;border-radius:4px;pointer-events:none;
  background:repeating-linear-gradient(45deg,#e6eef4,#e6eef4 5px,#f4f8fb 5px,#f4f8fb 10px);
  border:1px solid #c3d8e6;display:flex;align-items:center;justify-content:center;
  font-size:11px;color:#2d6a91;letter-spacing:.5px;z-index:1}
.p4-sel{position:absolute;border-radius:4px;pointer-events:none;z-index:3;
  background:rgba(63,186,136,.18);border:1px solid var(--primary)}
.p4-bar{position:sticky;bottom:0;z-index:6;display:flex;align-items:center;gap:10px;
  background:var(--text-strong);color:#fff;padding:10px 14px;border-radius:var(--r-btn);
  margin:10px 12px 0;font-size:13px}
.p4-bar .btn-md{height:30px}
.bk-chip.p4{background:#e3eef6;color:#2d6a91;cursor:pointer}
.bk-chip.p4 svg{stroke:currentColor}
.p4-note{margin:0 0 10px;padding:8px 12px;border-radius:var(--r-input);
  background:#e3eef6;color:#2d6a91;font-size:13px;line-height:19px}
.p4-drw-mask{position:fixed;inset:0;background:rgba(0,0,0,.25);z-index:500;display:none}
.p4-drw-mask.show{display:block}
.p4-drw{position:fixed;top:0;right:0;bottom:0;width:340px;max-width:92vw;background:#fff;
  z-index:501;transform:translateX(100%);transition:transform .18s;display:flex;flex-direction:column}
.p4-drw.show{transform:none}
.p4-drw h4{padding:18px 20px;border-bottom:1px solid var(--border-card);font-size:16px;font-weight:500;
  display:flex;align-items:center}
.p4-drw .bd{padding:16px 20px;overflow:auto;display:flex;flex-direction:column;gap:14px}
.p4-drw .it{border:1px solid var(--border-card);border-radius:var(--r-input);padding:10px 12px;
  font-size:13px;line-height:19px;display:flex;gap:8px;align-items:flex-start}
.p4-drw .it .x{margin-left:auto;color:var(--alert);cursor:pointer;font-size:12px;white-space:nowrap}
.p4-drw .dy{font-size:12px;color:var(--text-muted);margin-bottom:6px}
""", label="css")

# ── 2) 標題列的總覽 chip ────────────────────────────────────────────
src = inject(src, '      <div class="bk-chips">',
             '\n        ${p4Chip()}', before=False, label="chip")

# ── 3) viewBooking 綁定 chip ───────────────────────────────────────
src = inject(src, "  bindCustomerList();",
             "  p4BindChip();\n", label="bind")

# ── 4) 資料層＋時間軸互動（放在 renderTimeline 之前） ───────────────
src = inject(src, "/* ---------- 時間軸 ---------- */", """/* ===== Part4 注入：臨時預約關閉（資料層與時間軸互動） =====
   與例外頁整合版（part4_exception.html）共用同一把 sessionStorage key，
   定稿頁自己的 db 完全不動。 */
const P4_KEY = 'p4_closures';
const P4_ICON = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 8v4l2 1"/><path d="M5.5 5.5l13 13"/></svg>';
function p4All() { try { return JSON.parse(sessionStorage.getItem(P4_KEY)) || []; } catch (e) { return []; } }
function p4Save(v) { sessionStorage.setItem(P4_KEY, JSON.stringify(v)); }
function p4Of(date) { return p4All().filter(c => c.date === date); }
/* chip 常駐——原本寫成「有資料才顯示」，全新 session 一筆都沒有時，
   整頁看不出 Part 4 加了什麼，reviewer 只會看到一個普通的定稿時間軸 */
function p4Chip() {
  const n = p4All().length;
  return `<span class="bk-chip p4" id="p4Chip">${P4_ICON}臨時關閉 ${n}</span>`;
}
function p4BindChip() {
  const c = document.getElementById('p4Chip');
  if (c) c.onclick = p4OpenDrawer;
}
/* 該日某單位被關閉的分鐘區間 */
function p4RangesOf(date, unitId) {
  return p4Of(date).filter(c => c.unitIds.includes(unitId)).map(c => [toMin(c.start), toMin(c.end)]);
}
let p4Sel = null, p4Drag = false;

function p4Timeline(rows) {
  const inner = document.querySelector('.tl-inner');
  if (!inner) return;
  p4Hint();
  const rowEls = [...inner.querySelectorAll('.tl-row')];

  /* 已關閉區塊 */
  rowEls.forEach((el, i) => {
    const u = rows[i]; if (!u) return;
    p4RangesOf(bk.date, u.id).forEach(([s, e]) => {
      const s2 = Math.max(TL_ORIGIN, s), e2 = Math.min(TL_ORIGIN + TL_COLS * 30, e);
      if (e2 <= s2) return;
      const d = document.createElement('div');
      d.className = 'p4-closed';
      d.style.left = (s2 - TL_ORIGIN) / 30 * TL_COLW + 'px';
      d.style.width = (e2 - s2) / 30 * TL_COLW - 2 + 'px';
      d.textContent = '已關閉線上預約';
      el.appendChild(d);
    });
  });

  /* 框選 */
  const cellOf = (ev) => {
    const el = document.elementFromPoint(ev.clientX, ev.clientY);
    const row = el && el.closest ? el.closest('.tl-row') : null;
    if (!row) return null;
    const r = rowEls.indexOf(row);
    const rect = inner.getBoundingClientRect();
    const c = Math.floor((ev.clientX - rect.left) / TL_COLW);
    if (r < 0 || c < 0 || c >= TL_COLS) return null;
    return { r, c };
  };
  inner.addEventListener('mousedown', ev => {
    if (ev.target.closest('.tl-chip')) return;   // 點預約卡沿用定稿頁的 popover
    const p = cellOf(ev); if (!p) return;
    ev.preventDefault();
    p4Drag = true; p4Sel = { r0: p.r, c0: p.c, r1: p.r, c1: p.c };
    p4Paint(rows, rowEls, inner);
  });
  window.addEventListener('mousemove', ev => {
    if (!p4Drag) return;
    const p = cellOf(ev); if (!p) return;
    if (p.r === p4Sel.r1 && p.c === p4Sel.c1) return;
    p4Sel.r1 = p.r; p4Sel.c1 = p.c;
    p4Paint(rows, rowEls, inner);
  });
  window.addEventListener('mouseup', () => { p4Drag = false; });

  if (p4Sel) p4Paint(rows, rowEls, inner);
}

function p4Rect() {
  if (!p4Sel) return null;
  return { r0: Math.min(p4Sel.r0, p4Sel.r1), r1: Math.max(p4Sel.r0, p4Sel.r1),
           c0: Math.min(p4Sel.c0, p4Sel.c1), c1: Math.max(p4Sel.c0, p4Sel.c1) };
}
function p4Paint(rows, rowEls, inner) {
  inner.querySelectorAll('.p4-sel').forEach(e => e.remove());
  document.querySelectorAll('.p4-bar').forEach(e => e.remove());
  const R = p4Rect(); if (!R) return;
  for (let r = R.r0; r <= R.r1; r++) {
    const el = rowEls[r]; if (!el) continue;
    const d = document.createElement('div');
    d.className = 'p4-sel';
    d.style.left = R.c0 * TL_COLW + 'px';
    d.style.width = (R.c1 - R.c0 + 1) * TL_COLW - 2 + 'px';
    d.style.top = '2px'; d.style.bottom = '2px';
    el.appendChild(d);
  }
  const units = rows.slice(R.r0, R.r1 + 1);
  const start = toHHMM(TL_ORIGIN + R.c0 * 30), end = toHHMM(TL_ORIGIN + (R.c1 + 1) * 30);
  const allClosed = units.every(u => p4RangesOf(bk.date, u.id).some(([s, e]) => s <= TL_ORIGIN + R.c0 * 30 && e >= TL_ORIGIN + (R.c1 + 1) * 30));
  const bar = document.createElement('div');
  bar.className = 'p4-bar';
  bar.innerHTML = `<span>已選 <b>${units.map(u => esc(u.name)).join('、')}</b>　${start}–${end}</span>
    <div style="margin-left:auto;display:flex;gap:8px">
      <button class="btn-md ghost" id="p4Cancel">取消</button>
      <button class="btn-md ${allClosed ? 'ghost-green' : 'primary'}" id="p4Do">${allClosed ? '恢復開放線上預約' : '關閉線上預約'}</button>
    </div>`;
  document.getElementById('bkMain').appendChild(bar);
  bar.querySelector('#p4Cancel').onclick = () => { p4Sel = null; renderTimeline(); };
  bar.querySelector('#p4Do').onclick = () => {
    const ids = units.map(u => u.id);
    if (allClosed) {
      p4Save(p4All().filter(c => !(c.date === bk.date && c.start === start && c.end === end && c.unitIds.some(i => ids.includes(i)))));
      toast('已恢復開放線上預約');
    } else {
      p4Save(p4All().concat({ id: 'p4_' + p4All().length + '_' + start, date: bk.date, start, end, unitIds: ids }));
      toast(`已關閉線上預約：${ids.length} 個單位 ${start}–${end}`);
    }
    p4Sel = null; viewBooking();
  };
}

function p4OpenDrawer() {
  let mask = document.getElementById('p4Mask');
  if (!mask) {
    mask = document.createElement('div'); mask.className = 'p4-drw-mask'; mask.id = 'p4Mask';
    document.body.appendChild(mask);
    mask.onclick = () => { mask.classList.remove('show'); document.getElementById('p4Drw').classList.remove('show'); };
    const d = document.createElement('aside'); d.className = 'p4-drw'; d.id = 'p4Drw';
    document.body.appendChild(d);
  }
  const drw = document.getElementById('p4Drw');
  const byDate = {};
  p4All().forEach(c => (byDate[c.date] = byDate[c.date] || []).push(c));
  const uname = id => (db.units.find(u => u.id === id) || {}).name || id;
  drw.innerHTML = `<h4>臨時關閉中<span style="margin-left:auto"><button class="btn-md ghost" id="p4DrwX">關閉</button></span></h4>
    <div class="bd">
      <div class="p4-note">時間軸一次只看一天，這裡列出<b>所有日期</b>的關閉設定——避免關了忘記恢復，線上預約被默默擋住。</div>
      ${Object.keys(byDate).sort().map(dt => `<div><div class="dy">${dt}${dt === bk.date ? '（今天檢視中）' : ''}</div>
        ${byDate[dt].map(c => `<div class="it"><div>${c.start}–${c.end}<br>${c.unitIds.map(uname).map(esc).join('、')}</div>
          <span class="x" data-p4x="${c.id}">解除</span></div>`).join('')}</div>`).join('') || '<div class="ls-empty">目前沒有臨時關閉的單位</div>'}
    </div>`;
  mask.classList.add('show'); drw.classList.add('show');
  drw.querySelector('#p4DrwX').onclick = () => { mask.classList.remove('show'); drw.classList.remove('show'); };
  drw.querySelectorAll('[data-p4x]').forEach(x => x.onclick = () => {
    p4Save(p4All().filter(c => c.id !== x.dataset.p4x));
    viewBooking(); p4OpenDrawer();
  });
}

/* ---------- 時間軸 ---------- */""", label="p4-core")

# ── 5) renderTimeline 收尾呼叫 ──────────────────────────────────────
src = inject(src, "  document.querySelectorAll('.tl-chip').forEach(c => c.onclick = (e) => openPopover(c.dataset.b, e));",
             "\n  p4Timeline(rows);", before=False, label="tl-hook")

# ── 6) 空間圖／清單：只呈現狀態，不做關閉操作 ──────────────────────
src = inject(src, "  document.querySelectorAll('.sp-u[data-b]').forEach(c => c.onclick = (e) => openPopover(c.dataset.b, e));",
             """  p4Note();\n""", label="space-note")
src = inject(src, '    <div class="ls-body">${body}</div>`;',
             "\n  p4Note();", before=False, label="list-note")
src = inject(src, "function p4OpenDrawer() {",
             """/* 時間軸上方的常駐操作提示：框選是拖曳手勢，沒有提示 reviewer 不會知道要做什麼 */
function p4Hint(){
  const main = document.getElementById('bkMain');
  if (!main || main.querySelector('.p4-hint')) return;
  const cs = p4Of(bk.date);
  const uname = id => (db.units.find(u => u.id === id) || {}).name || id;
  const h = document.createElement('div');
  h.className = 'p4-note p4-hint';
  h.innerHTML = '<b>方案 C・臨時預約關閉</b>：在下方時間軸<b>按住拖曳框選「桌 × 時段」</b>即可關閉線上預約（可跨多列），放開後會浮出操作列。'
    + (cs.length ? '　本日已關閉：' + cs.map(c => `${c.start}–${c.end} ${c.unitIds.map(uname).map(esc).join('、')}`).join('；') : '')
    + '　右上角「臨時關閉」可查看所有日期的關閉並解除。';
  main.insertBefore(h, main.firstChild);
}

/* 空間圖／清單沒有「單位 × 時間」兩個軸，不做關閉操作，只提示狀態 */
function p4Note() {
  const cs = p4Of(bk.date);
  if (!cs.length) return;
  const uname = id => (db.units.find(u => u.id === id) || {}).name || id;
  const main = document.getElementById('bkMain');
  const n = document.createElement('div');
  n.className = 'p4-note';
  n.innerHTML = '本日已臨時關閉：' + cs.map(c => `${c.start}–${c.end} ${c.unitIds.map(uname).map(esc).join('、')}`).join('；') + '（僅擋線上預約，可到時間軸解除）';
  main.insertBefore(n, main.firstChild);
}

""", label="note-fn")

# 側欄「例外預約規則」原本指向 exception_rules.html（非整合版），
# 從 C 版點過去會像掉進 B 版；改指向同為 Part4 整合版的 part4_exception.html
src = inject(src, "      location.href = 'exception_rules.html?mode=' + (excMap[db.mode] || 'basic');",
             "      location.href = 'part4_exception.html?mode=' + (excMap[db.mode] || 'basic');  /* Part4 整合版 */\n",
             before=True, label="exc-nav")
src = src.replace("      location.href = 'exception_rules.html?mode=' + (excMap[db.mode] || 'basic');\n", "", 1)

src = src.replace("<title>MENU店+ 後台模擬器</title>",
                  "<title>Part4 整合版｜MENU店+ 後台模擬器（時間軸臨時關閉）</title>", 1)
src = src.replace("<!-- MENU店+ 後台模擬器 · 假資料互動 Demo · 維護：FindLife Support -->",
                  "<!-- Part4 整合版：由 tools/build_part4_timeline.py 從 sim.html 產生，請勿直接編輯 -->", 1)

out = root / "part4_timeline.html"
out.write_text(src, encoding="utf-8")
print(f"part4_timeline.html 已產生：{len(src)} chars")
