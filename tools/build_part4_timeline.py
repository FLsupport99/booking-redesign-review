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
.p4-modebar{display:flex;align-items:center;gap:10px;margin:0 0 10px;padding:10px 14px;border-radius:var(--r-input);
  background:#2d6a91;color:#fff;font-size:13px;line-height:19px}
.p4-modebar b{color:#fff}
.p4-modebar .btn-md{height:30px}
.tl-row{cursor:default}
.p4-mode .tl-row{cursor:crosshair}
.p4-mode .tl-chip{opacity:.55}
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
/* 自動排位規則 */
.p4-gblock{display:flex;flex-direction:column;gap:6px;border:1px dashed var(--border-field);border-radius:var(--r-card);padding:10px}
.p4-gblock.dragging{opacity:.4}
.p4-gblock.over{border-color:var(--border-on)}
.p4-gbhead{display:flex;align-items:center;gap:8px;font-size:14px;font-weight:500;cursor:grab;user-select:none}
.p4-gbhead .ord{font-size:12px;color:var(--text-muted);margin-left:auto;font-variant-numeric:tabular-nums}
.p4-srow{display:flex;align-items:center;gap:12px;background:#fff;border:1px solid var(--border-card);
  border-radius:var(--r-input);padding:10px 14px;cursor:grab;user-select:none}
.p4-srow.dragging{opacity:.4}
.p4-srow.over{border-color:var(--border-on);background:var(--bg-selected)}
.p4-grip{width:14px;color:var(--text-disabled);letter-spacing:-2px;line-height:1;font-size:15px}
.p4-gchip{font-size:12px;line-height:16px;padding:2px 8px;border-radius:var(--r-tag);background:var(--bg-tag-on);color:var(--text-body);white-space:nowrap}
.p4-sname{flex:1;font-size:14px;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.p4-scap{font-size:13px;color:var(--text-muted);font-variant-numeric:tabular-nums}
/* 訂金管理 */
.p4-depcard{border:1px solid var(--border-card);border-radius:var(--r-card);padding:14px 16px;display:flex;align-items:flex-start;gap:12px}
.p4-depcard .m{flex:1;display:flex;flex-direction:column;gap:4px;min-width:0}
.p4-depcard .n{font-size:15px;font-weight:500}
.p4-depcard .d{font-size:13px;line-height:19px;color:var(--text-body)}
.p4-depcard .u{font-size:12px;color:var(--text-muted)}
.p4-sw{width:40px;height:22px;border-radius:999px;background:var(--btn-disabled);position:relative;cursor:pointer;flex:none;transition:background .15s}
.p4-sw::after{content:"";position:absolute;top:2px;left:2px;width:18px;height:18px;border-radius:50%;background:#fff;transition:left .15s}
.p4-sw.on{background:var(--primary)}
.p4-sw.on::after{left:20px}
.p4-inline{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:14px}
.p4-inline .input{width:auto}
.p4-w80{width:80px}.p4-w110{width:110px}
.p4-radio[data-on]{border-color:var(--primary)}
.p4-radio[data-on]::after{content:"";width:10px;height:10px;border-radius:50%;background:var(--primary)}
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
/* ⚠️ 時間軸的空白區在定稿裡已經是「點擊＝在該時間與桌位快速新增預約」
   （Figma 2-1-1 有 時間軸/清單/空間圖 三個新增預約變體）。同一個位置不能有兩種行為，
   所以臨時關閉改成「模式切換」：預設完全不攔截，進入關閉模式後才啟用框選。 */
let p4Mode = false;
/* ⚠️ window 監聽器只能綁一次。p4Timeline 每次重繪都呼叫，若每次 addEventListener，
   監聽器會越疊越多：舊的（持有失效 DOM 參照）先更新 p4Sel，新的再進來就以為
   「位置沒變」而提早 return，結果框選永遠只有一格。改為綁一次＋共用 p4Ctx。 */
let p4Bound = false, p4Ctx = null;
function p4EnterMode(){ p4Mode = true; p4Sel = null; viewBooking(); }
function p4ExitMode(){ p4Mode = false; p4Sel = null; viewBooking(); }

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
  /* 先看事件目標（拖曳中滑鼠底下的元素會冒泡上來），沒有再用座標反查 */
  const cellOf = (ev) => {
    let row = ev.target && ev.target.closest ? ev.target.closest('.tl-row') : null;
    if (!row) {
      const el = document.elementFromPoint(ev.clientX, ev.clientY);
      row = el && el.closest ? el.closest('.tl-row') : null;
    }
    if (!row) return null;
    const r = rowEls.indexOf(row);
    const rect = inner.getBoundingClientRect();
    const c = Math.floor((ev.clientX - rect.left) / TL_COLW);
    if (r < 0 || c < 0 || c >= TL_COLS) return null;
    return { r, c };
  };
  inner.addEventListener('mousedown', ev => {
    if (ev.target.closest('.tl-chip')) return;   // 點預約卡沿用定稿頁的 popover
    if (!p4Mode) {
      // 非關閉模式：此處是定稿的「新增預約」入口，臨時關閉不搶這個手勢
      if (cellOf(ev)) toast('定稿行為：點空白＝在此時間與桌位快速新增預約。要臨時關閉請按右上「臨時關閉」→ 進入關閉模式');
      return;
    }
    const p = cellOf(ev); if (!p) return;
    ev.preventDefault();
    p4Drag = true; p4Sel = { r0: p.r, c0: p.c, r1: p.r, c1: p.c };
    p4Paint(rows, rowEls, inner);
  });
  p4Ctx = { rows, rowEls, inner, cellOf };
  if (!p4Bound) {
    p4Bound = true;
    window.addEventListener('mousemove', ev => {
      if (!p4Drag || !p4Ctx) return;
      const p = p4Ctx.cellOf(ev); if (!p) return;
      if (p.r === p4Sel.r1 && p.c === p4Sel.c1) return;
      p4Sel.r1 = p.r; p4Sel.c1 = p.c;
      p4Paint(p4Ctx.rows, p4Ctx.rowEls, p4Ctx.inner);
    });
    window.addEventListener('mouseup', () => { p4Drag = false; });
  }

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
    p4Sel = null; viewBooking();   // 留在關閉模式，方便連續關好幾張桌
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
      <button class="btn-md primary" id="p4Enter" style="width:100%">＋ 進入關閉模式，在時間軸上框選</button>
      <div class="p4-note">時間軸一次只看一天，這裡列出<b>所有日期</b>的關閉設定——避免關了忘記恢復，線上預約被默默擋住。</div>
      ${Object.keys(byDate).sort().map(dt => `<div><div class="dy">${dt}${dt === bk.date ? '（今天檢視中）' : ''}</div>
        ${byDate[dt].map(c => `<div class="it"><div>${c.start}–${c.end}<br>${c.unitIds.map(uname).map(esc).join('、')}</div>
          <span class="x" data-p4x="${c.id}">解除</span></div>`).join('')}</div>`).join('') || '<div class="ls-empty">目前沒有臨時關閉的單位</div>'}
    </div>`;
  mask.classList.add('show'); drw.classList.add('show');
  drw.querySelector('#p4DrwX').onclick = () => { mask.classList.remove('show'); drw.classList.remove('show'); };
  drw.querySelector('#p4Enter').onclick = () => { mask.classList.remove('show'); drw.classList.remove('show'); p4EnterMode(); };
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
function p4ModeBar(){
  const main = document.getElementById('bkMain');
  if (!main || !p4Mode || main.querySelector('.p4-modebar')) return;
  document.body.classList.add('p4-mode');
  const b = document.createElement('div');
  b.className = 'p4-modebar';
  b.innerHTML = `<b>臨時關閉模式</b>　在時間軸上拖曳框選要關閉的「桌 × 時段」（可跨多列），放開後會浮出操作列。此模式下不會建立預約。
    <span style="margin-left:auto"><button class="btn-md ghost" id="p4Exit">完成</button></span>`;
  main.insertBefore(b, main.firstChild);
  b.querySelector('#p4Exit').onclick = p4ExitMode;
}
function p4Hint(){
  p4ModeBar();
  if (p4Mode) return;                       // 模式中不重複顯示一般提示
  document.body.classList.remove('p4-mode');
  const main = document.getElementById('bkMain');
  if (!main || main.querySelector('.p4-hint')) return;
  const cs = p4Of(bk.date);
  const uname = id => (db.units.find(u => u.id === id) || {}).name || id;
  const h = document.createElement('div');
  h.className = 'p4-note p4-hint';
  h.innerHTML = '<b>方案 C・臨時預約關閉</b>：時間軸的空白區在定稿裡是<b>「點擊＝快速新增預約」</b>，所以臨時關閉改走<b>模式切換</b>——按右上角「臨時關閉」→ 進入關閉模式後才能框選，退出即恢復。'
    + (cs.length ? '　本日已關閉：' + cs.map(c => `${c.start}–${c.end} ${c.unitIds.map(uname).map(esc).join('、')}`).join('；') : '');
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


# ── 7) 自動排位規則 & 訂金管理：注入兩個設定頁（sim.html 側欄本來就有這兩項，
#      但點下去只跳「尚未做成互動 Demo」）。訂金規則直接操作 sim.html 既有的
#      DEPOSITS 陣列，所以在這裡新增／刪除，時段規則的「要求訂金」選單會同步。
src = inject(src, "/* =====================================================\n   預約規則 landing（入口示意）", """/* ===== Part4 注入：自動排位規則（US4-1） ===== */
function p4ViewAuto() {
  setTitle([['預約設定', '#/rules'], ['自動排位規則', '#/p4auto']], '自動排位規則');
  $('#content').innerHTML = `
    <div class="p4-note">此頁的順序<b>只決定「同分時選誰」</b>——系統先求「用最少的預約單位滿足人數」，再看群組順序、再看群組內單位順序。與「後台操作偏好 &gt; 預約單位排序」（扁平、可跨群組）是兩套獨立排序。</div>
    <div class="card">
      <div class="card-head"><div class="ch-main">
        <div class="ch-title">優先排位順序</div>
        <div class="ch-desc">拖曳以調整順序。群組可整組移動；單位只能在所屬群組內排序，不可跨組。</div>
      </div></div>
      <div id="p4AutoList" style="display:flex;flex-direction:column;gap:10px"></div>
      <div class="btn-row" style="display:flex;gap:8px;justify-content:flex-end">
        <button class="btn-md primary" id="p4AutoSave">儲存</button>
      </div>
    </div>
    <div class="card">
      <div class="card-head"><div class="ch-main">
        <div class="ch-title">演算法判斷順序</div>
        <div class="ch-desc">建立／修改線上預約，以及「自動分配預約單位」開啟時的自建預約，皆適用。</div>
      </div></div>
      <div style="font-size:14px;line-height:22px;color:var(--text-body)">
        1. 優先考慮：如何使用<b>最少</b>的預約單位滿足預約人數需求<br>
        2. 再考慮：群組的排列順序<br>
        3. 再考慮：群組內單位的排列順序
      </div>
    </div>`;
  p4RenderAuto();
  $('#p4AutoSave').onclick = () => { persist(); toast('已儲存排位順序'); };
}
function p4RenderAuto() {
  const gs = db.groups.filter(g => db.units.some(u => u.gid === g.id));
  $('#p4AutoList').innerHTML = gs.map((g, gi) => {
    const us = db.units.filter(u => u.gid === g.id);
    return `<div class="p4-gblock" draggable="true" data-gi="${gi}">
      <div class="p4-gbhead"><span class="p4-grip">⣿</span><span class="p4-gchip">${esc(g.name)}</span>
        <span class="ord">第 ${gi + 1} 順位・${us.length} 個單位</span></div>
      ${us.map((u, ui) => `<div class="p4-srow" draggable="true" data-gi="${gi}" data-ui="${ui}">
          <span class="p4-grip">⣿</span><span class="p4-sname">${esc(u.name)}</span>
          <span class="p4-scap">${u.min}~${u.max} 人</span></div>`).join('')}
    </div>`;
  }).join('');
  p4WireAuto(gs);
}
function p4WireAuto(gs) {
  let src = null;
  document.querySelectorAll('#p4AutoList .p4-srow').forEach(el => {
    el.addEventListener('dragstart', e => { e.stopPropagation(); src = el; el.classList.add('dragging'); });
    el.addEventListener('dragend', () => { src = null; p4RenderAuto(); });
    el.addEventListener('dragover', e => {
      if (!src || !src.classList.contains('p4-srow')) return;
      e.preventDefault(); e.stopPropagation();
      if (src.dataset.gi === el.dataset.gi) el.classList.add('over');
    });
    el.addEventListener('dragleave', () => el.classList.remove('over'));
    el.addEventListener('drop', e => {
      e.preventDefault(); e.stopPropagation();
      if (!src || src.dataset.gi !== el.dataset.gi) { toast('不可跨群組排序'); return; }
      const gid = gs[+el.dataset.gi].id;
      const idx = db.units.map((u, i) => u.gid === gid ? i : -1).filter(i => i >= 0);
      const from = idx[+src.dataset.ui], to = idx[+el.dataset.ui];
      const [m] = db.units.splice(from, 1);
      db.units.splice(to, 0, m);
      persist();
    });
  });
  document.querySelectorAll('#p4AutoList .p4-gblock').forEach(el => {
    el.addEventListener('dragstart', e => { if (src) return; src = el; el.classList.add('dragging'); });
    el.addEventListener('dragend', () => { src = null; p4RenderAuto(); });
    el.addEventListener('dragover', e => { if (src && src.classList.contains('p4-gblock') && src !== el) { e.preventDefault(); el.classList.add('over'); } });
    el.addEventListener('dragleave', () => el.classList.remove('over'));
    el.addEventListener('drop', e => {
      e.preventDefault();
      if (!src || !src.classList.contains('p4-gblock')) return;
      const a = gs[+src.dataset.gi].id, b = gs[+el.dataset.gi].id;
      const ia = db.groups.findIndex(g => g.id === a), ib = db.groups.findIndex(g => g.id === b);
      const [m] = db.groups.splice(ia, 1);
      db.groups.splice(ib, 0, m);
      persist();
    });
  });
}

/* ===== Part4 注入：訂金管理（US4-2） =====
   直接操作 sim.html 既有的 DEPOSITS 陣列——在這裡新增／刪除，時段規則表單的
   「要求訂金 → 套用規則」選單會同步，正好示範「訂金規則是可複用物件」。 */
let p4DepOn = true;
function p4DepDesc(d) {
  const way = d.way === 'auth' ? '信用卡授權綁定' : '預先收款';
  const cond = d.cond === 'fixed' ? `固定金額 ${d.fixed} 元/組` : `${d.minPeople} 人以上，每人 ${d.perPerson} 元`;
  return `${way}：${cond}`;
}
function p4NormalizeDeposits() {
  DEPOSITS.forEach(d => {
    if (d.way) return;                         // 已正規化過
    const s = d.desc || '';
    d.way = /授權|綁卡|綁定/.test(s) ? 'auth' : 'prepay';
    const mFixed = s.match(/每組\\s*(\\d+)/);
    const mPer = s.match(/(\\d+)\\s*人以上.*?每人\\s*(\\d+)/);
    if (mPer) { d.cond = 'people'; d.minPeople = +mPer[1]; d.perPerson = +mPer[2]; d.fixed = 300; }
    else { d.cond = 'fixed'; d.fixed = mFixed ? +mFixed[1] : 300; d.minPeople = 1; d.perPerson = 100; }
  });
}
function p4UsedBy(id) {
  const names = [];
  ['slots', 'svcSlots', 'catSlots', 'capSlots'].forEach(k => (db[k] || []).forEach(s => { if (s.deposit === id) names.push(s.name); }));
  return names;
}
function p4ViewDeposit() {
  p4NormalizeDeposits();
  setTitle([['預約設定', '#/rules'], ['訂金管理', '#/p4deposit']], '訂金管理');
  $('#content').innerHTML = `
    <div class="p4-note">相對現況的改動：原本這頁只有<b>一組</b>「收款方式＋收款條件」，改成可建立<b>多組具名的訂金規則</b>，供時段規則、例外時段規則與服務選項套用。套用優先序：<b>服務選項 &gt; 時段規則</b>；服務選項未設定訂金即為不收，不回落店家層級。</div>
    <div class="card">
      <div class="card-head"><div class="ch-main">
        <div class="ch-title">訂金預約模式</div>
        <div class="ch-desc">開啟後，所有符合條件且透過線上預約的顧客都必須在期限內完成付款或授權信用卡。</div>
      </div><div class="p4-sw${p4DepOn ? ' on' : ''}" id="p4DepSw"></div></div>
      <div style="font-size:14px;color:var(--text-body)">藍新商店代號　<b>MNU00</b></div>
    </div>
    <div class="card">
      <div class="card-head"><div class="ch-main">
        <div class="ch-title">訂金規則</div>
        <div class="ch-desc">建立後可在「預約時段設定」「例外預約日期設定」「服務選項設定」中選用。這裡的異動會同步到時段規則的「要求訂金」選單。</div>
      </div><button class="btn-md ghost-green" id="p4DepAdd">＋ 新增訂金規則</button></div>
      <div id="p4DepList" style="display:flex;flex-direction:column;gap:10px"></div>
    </div>
    <div class="card">
      <div class="card-head"><div class="ch-main"><div class="ch-title">期限與請款規則（沿用現況、不可調整）</div></div></div>
      <div style="font-size:14px;line-height:22px;color:var(--text-body)">
        ・預先收款的付款期限：送出預約申請後至<b>隔日 22:59</b>；若預約時間為送出當日或隔日，期限改為<b>預約時間前 30 分鐘</b><br>
        ・信用卡授權的操作期限：送出預約申請後 <b>30 分鐘</b>內，逾時未授權自動取消預約<br>
        ・授權完成後僅保留額度、不自動扣款；<b>「請款」按鈕僅在預約狀態為「未到店」時出現</b><br>
        ・請款期限：<b>預約日後七日內</b>，逾期授權失效且無法再扣款<br>
        ・逾時未付款／未授權：預約自動轉入「取消預約」
      </div>
    </div>`;
  p4RenderDepList();
  $('#p4DepSw').onclick = () => { p4DepOn = !p4DepOn; p4ViewDeposit(); };
  $('#p4DepAdd').onclick = () => p4DepForm(null);
}
function p4RenderDepList() {
  $('#p4DepList').innerHTML = DEPOSITS.length ? DEPOSITS.map(d => {
    const used = p4UsedBy(d.id);
    return `<div class="p4-depcard">
      <div class="m">
        <div class="n">${esc(d.name)}</div>
        <div class="d">${esc(p4DepDesc(d))}</div>
        <div class="u">${used.length ? '套用中：' + used.map(esc).join('、') : '尚未被任何時段規則套用'}</div>
      </div>
      <button class="btn-md ghost" data-p4de="${d.id}">編輯</button>
      <button class="btn-md ghost-red" data-p4dd="${d.id}">刪除</button>
    </div>`;
  }).join('') : `<div class="empty">目前沒有任何訂金規則</div>`;
  document.querySelectorAll('[data-p4de]').forEach(b => b.onclick = () => p4DepForm(DEPOSITS.find(d => d.id === b.dataset.p4de)));
  document.querySelectorAll('[data-p4dd]').forEach(b => b.onclick = () => p4DepDelete(DEPOSITS.find(d => d.id === b.dataset.p4dd)));
}
function p4DepForm(d) {
  const f = d ? Object.assign({}, d) : { id: 'd' + (DEPOSITS.length + 1) + '_' + DEPOSITS.length, name: '訂金規則 ' + (DEPOSITS.length + 1), way: 'prepay', cond: 'people', minPeople: 1, perPerson: 100, fixed: 200 };
  const grab = () => {
    f.name = $('#p4fName').value;
    f.minPeople = +$('#p4fMin').value || 1; f.perPerson = +$('#p4fPer').value || 0; f.fixed = +$('#p4fFix').value || 0;
  };
  const draw = () => {
    openModal(`
      <h3>${d ? '編輯' : '新增'}訂金規則</h3>
      <div class="m-body">
        <div class="field"><span class="field-label">訂金規則名稱</span>
          <input class="input" id="p4fName" value="${esc(f.name)}"><span class="hint">名稱不得重複</span></div>
        <div class="field"><span class="field-label">收款方式</span>
          <div style="display:flex;flex-direction:column;gap:8px">
            ${[['prepay', '預先收款', '顧客可透過轉帳、信用卡、超商代碼完成訂金支付'],
               ['auth', '信用卡授權綁定', '顧客需完成信用卡授權，若因故爽約，可於授權期限內請款']]
              .map(([v, n, sub]) => `<label class="check" data-p4way="${v}"><span class="radio p4-radio"${f.way === v ? ' data-on' : ''}></span>
                <span><span class="ck-label">${n}</span><div class="ck-desc">${sub}</div></span></label>`).join('')}
          </div></div>
        <div class="field"><span class="field-label">收款條件</span>
          <div style="display:flex;flex-direction:column;gap:10px">
            <label class="check" data-p4cond="people"><span class="radio p4-radio"${f.cond === 'people' ? ' data-on' : ''}></span>
              <span class="p4-inline">依據預約人數 <input class="input p4-w80" id="p4fMin" value="${f.minPeople}"> 人以上，
                <input class="input p4-w80" id="p4fPer" value="${f.perPerson}"> 元/人</span></label>
            <label class="check" data-p4cond="fixed"><span class="radio p4-radio"${f.cond === 'fixed' ? ' data-on' : ''}></span>
              <span class="p4-inline">固定金額 <input class="input p4-w110" id="p4fFix" value="${f.fixed}"> 元/組</span></label>
          </div>
          <span class="hint">人數計算包含大人與小孩。不適用於 Google 預訂；自建預約由店員逐筆輸入金額。</span></div>
      </div>
      <div class="btn-row" style="display:flex;gap:8px;justify-content:flex-end">
        <button class="btn-md ghost" id="p4fCancel">取消</button>
        <button class="btn-md primary" id="p4fSave">儲存</button>
      </div>`);
    document.querySelectorAll('[data-p4way]').forEach(el => el.onclick = () => { grab(); f.way = el.dataset.p4way; draw(); });
    document.querySelectorAll('[data-p4cond]').forEach(el => el.onclick = e => {
      if (e.target.tagName === 'INPUT') return; grab(); f.cond = el.dataset.p4cond; draw();
    });
    $('#p4fCancel').onclick = closeModal;
    $('#p4fSave').onclick = () => {
      grab();
      if (!f.name.trim()) return toast('請輸入訂金規則名稱');
      if (DEPOSITS.some(x => x.name.trim() === f.name.trim() && x.id !== f.id)) return toast('名稱不得重複');
      f.desc = p4DepDesc(f);
      const i = DEPOSITS.findIndex(x => x.id === f.id);
      if (i >= 0) DEPOSITS[i] = f; else DEPOSITS.push(f);
      closeModal(); p4RenderDepList(); toast('已儲存');
    };
  };
  draw();
}
function p4DepDelete(d) {
  const used = p4UsedBy(d.id);
  openModal(`
    <h3>刪除訂金規則</h3>
    <div class="m-body">確定要刪除「${esc(d.name)}」嗎？
      ${used.length ? `<div class="p4-note">此規則目前被 <b>${used.length}</b> 條時段規則套用中：${used.map(esc).join('、')}。<br>刪除後這些規則會變成<b>「不需要訂金」</b>。已處於「待付款/綁卡」的既有預約不受影響。</div>` : ''}
    </div>
    <div class="btn-row" style="display:flex;gap:8px;justify-content:flex-end">
      <button class="btn-md ghost" id="p4dCancel">取消</button>
      <button class="btn-md ghost-red" id="p4dOk">刪除</button>
    </div>`);
  $('#p4dCancel').onclick = closeModal;
  $('#p4dOk').onclick = () => {
    const i = DEPOSITS.findIndex(x => x.id === d.id);
    if (i >= 0) DEPOSITS.splice(i, 1);
    ['slots', 'svcSlots', 'catSlots', 'capSlots'].forEach(k => (db[k] || []).forEach(s => { if (s.deposit === d.id) s.deposit = null; }));
    persist(); closeModal(); p4RenderDepList(); toast('已刪除');
  };
}

/* =====================================================
   預約規則 landing（入口示意）""", label="p4-settings")

# 路由
src = inject(src, "  if (h === '#/rules' || h === '') return viewRules();",
             "  if (h === '#/p4auto') return p4ViewAuto();\n  if (h === '#/p4deposit') return p4ViewDeposit();\n", label="routes")

# 側欄導向
src = inject(src, "    else if (a.dataset.nav === '顧客預約頁') { location.hash = '#/customer'; }",
             "\n    else if (a.dataset.nav === '自動排位規則') { location.hash = '#/p4auto'; }\n    else if (a.dataset.nav === '訂金管理') { location.hash = '#/p4deposit'; }",
             before=False, label="nav")

# 側欄高亮
_old_active = "  const activeNav = h.startsWith('#/customer') ? '顧客預約頁' : '預約規則';"
if src.count(_old_active) != 1:
    sys.exit(f"❌ activeNav 錨點命中 {src.count(_old_active)} 次")
src = src.replace(_old_active,
    "  const activeNav = h === '#/p4auto' ? '自動排位規則' : h === '#/p4deposit' ? '訂金管理'\n"
    "    : h.startsWith('#/customer') ? '顧客預約頁' : '預約規則';", 1)


src = src.replace("<title>MENU店+ 後台模擬器</title>",
                  "<title>Part4 整合版｜MENU店+ 後台模擬器（時間軸臨時關閉）</title>", 1)
src = src.replace("<!-- MENU店+ 後台模擬器 · 假資料互動 Demo · 維護：FindLife Support -->",
                  "<!-- Part4 整合版：由 tools/build_part4_timeline.py 從 sim.html 產生，請勿直接編輯 -->", 1)

out = root / "part4_timeline.html"
out.write_text(src, encoding="utf-8")
print(f"part4_timeline.html 已產生：{len(src)} chars")
