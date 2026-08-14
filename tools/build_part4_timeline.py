#!/usr/bin/env python3
"""從 Part 3 定稿的後台模擬器 sim.html 產生 part4_timeline.html —— Part 4 的完整整合版。

原則同 build_part4_exception.py：定稿頁 100% 不動，只「注入」。這一份包含 Part 4 全部三塊：

  1. 自動排位規則（US4-1 v2）  預約設定 > 自動排位規則
     依預約人數級距分段，每段一份完整排序＋併桌上限，內建排位模擬器
  2. 訂金管理（US4-2）         預約設定 > 訂金管理
     直接操作 sim.html 既有的 DEPOSITS 陣列，時段規則的「要求訂金」選單會同步
  3. 臨時預約關閉 方案 C（US4-3）預約 > 時間軸 > 右上「臨時關閉」
     進入關閉模式後框選「桌 × 時段」，關閉區塊以斜線呈現

2026-08-10：自動排位規則從 v1（單一份全域排序）換成 v2（人數級距分段），
原本獨立的 part4_auto.html 與 build_part4_auto.py 一併退役——Part 4 就是一包，
不要再拆成多個入口。

sessionStorage：主資料 p4_v3（示範資料補了吧台／6 人／8 人桌／包廂，
原本 6 個小單位跑不出級距差異）；臨時關閉另存 p4_closures，與例外頁整合版共用。
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


def replace_once(hay, old, new, label=""):
    if hay.count(old) != 1:
        sys.exit(f"錨點不唯一或不存在（{label}）：{old[:60]!r} count={hay.count(old)}")
    return hay.replace(old, new, 1)


SEED_GROUPS_OLD = """  groups: [
    { id: 'g_indoor',  name: '室內',     isDefault: false, merge: true,  mergeMax: 2 },
    { id: 'g_outdoor', name: '戶外',     isDefault: false, merge: true,  mergeMax: 2 },
    { id: 'g_default', name: '預設群組', isDefault: true,  merge: false, mergeMax: 2 },
  ],
  units: [
    { id: 'u1', gid: 'g_indoor',  name: 'Indoor 1',  min: 1, max: 2 },
    { id: 'u2', gid: 'g_indoor',  name: 'Indoor 2',  min: 2, max: 4 },
    { id: 'u3', gid: 'g_outdoor', name: 'Outdoor 1', min: 1, max: 2 },
    { id: 'u4', gid: 'g_outdoor', name: 'Outdoor 2', min: 2, max: 4 },
    { id: 'u5', gid: 'g_default', name: 'Default 1', min: 1, max: 2 },
    { id: 'u6', gid: 'g_default', name: 'Default 2', min: 2, max: 4 },
  ],"""

SEED_GROUPS_NEW = """  groups: [
    { id: 'g_bar',     name: '吧台',     isDefault: false, merge: false, mergeMax: 1 },
    { id: 'g_indoor',  name: '室內',     isDefault: false, merge: true,  mergeMax: 3 },
    { id: 'g_outdoor', name: '戶外',     isDefault: false, merge: true,  mergeMax: 2 },
    { id: 'g_room',    name: '包廂',     isDefault: false, merge: false, mergeMax: 1 },
    { id: 'g_default', name: '預設群組', isDefault: true,  merge: false, mergeMax: 2 },
  ],
  units: [
    { id: 'ub1', gid: 'g_bar',    name: '吧台 1',    min: 1, max: 2 },
    { id: 'ub2', gid: 'g_bar',    name: '吧台 2',    min: 1, max: 2 },
    { id: 'ub3', gid: 'g_bar',    name: '吧台 3',    min: 1, max: 2 },
    { id: 'u1', gid: 'g_indoor',  name: 'Indoor 1',  min: 1, max: 2 },
    { id: 'u2', gid: 'g_indoor',  name: 'Indoor 2',  min: 2, max: 4 },
    { id: 'u7', gid: 'g_indoor',  name: 'Indoor 3',  min: 2, max: 4 },
    { id: 'u8', gid: 'g_indoor',  name: 'Indoor 6人', min: 4, max: 6 },
    { id: 'u9', gid: 'g_indoor',  name: 'Indoor 8人', min: 5, max: 8 },
    { id: 'u3', gid: 'g_outdoor', name: 'Outdoor 1', min: 1, max: 2 },
    { id: 'u4', gid: 'g_outdoor', name: 'Outdoor 2', min: 2, max: 4 },
    { id: 'ur1', gid: 'g_room',   name: 'VIP 包廂',  min: 8, max: 12 },
    { id: 'u5', gid: 'g_default', name: 'Default 1', min: 1, max: 2 },
    { id: 'u6', gid: 'g_default', name: 'Default 2', min: 2, max: 4 },
  ],"""



# ── 0) 示範資料：補吧台／大桌／包廂，並換獨立 DB_KEY
#      原本 6 個小單位（1–2 人 ×3、2–4 人 ×3）跑不出人數級距的差異
src = replace_once(src, "const DB_KEY = 'sim_v4';", "const DB_KEY = 'p4_v3';", label="dbkey")
src = replace_once(src, SEED_GROUPS_OLD, SEED_GROUPS_NEW, label="seed")

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
.p4-fablabel{align-self:center;font-size:12px;color:#2d6a91;background:#e3eef6;border-radius:8px;padding:7px 10px;box-shadow:0 2px 10px rgba(0,0,0,.15)}
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
.p4-note{margin:0 0 14px;padding:10px 14px;border-radius:var(--r-input);
  background:#e3eef6;color:#2d6a91;font-size:13px;line-height:20px}
.p4-note b{color:#1f4f6d}
.p4-cuts{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:14px}
.p4-cuts .input{width:72px}
.p4-cutchip{display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:var(--r-tag);
  background:var(--bg-tag-on);font-size:13px;font-variant-numeric:tabular-nums;white-space:nowrap}
.p4-cutchip .x{color:var(--alert);cursor:pointer;font-size:12px}
.p4-bandhead{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.p4-bandno{display:inline-flex;align-items:center;justify-content:center;min-width:26px;height:26px;
  padding:0 8px;border-radius:var(--r-tag);background:var(--primary);color:#fff;
  font-size:13px;font-variant-numeric:tabular-nums}
.p4-inline{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:14px;line-height:22px}
.p4-inline .sel{width:auto}
.p4-quick{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:0 0 10px;
  font-size:13px;color:var(--text-muted)}
.p4-quick .btn-md{height:30px}
/* 排序清單（沿用 part4_timeline.html 既有樣式） */
.p4-gblock{display:flex;flex-direction:column;gap:6px;border:1px dashed var(--border-field);
  border-radius:var(--r-card);padding:10px}
.p4-gblock.dragging{opacity:.4}
.p4-gblock.over{border-color:var(--border-on)}
.p4-gbhead{display:flex;align-items:center;gap:8px;font-size:14px;font-weight:500;cursor:grab;user-select:none}
.p4-gbhead .ord{font-size:12px;color:var(--text-muted);margin-left:auto;font-variant-numeric:tabular-nums}
.p4-srow{display:flex;align-items:center;gap:12px;background:#fff;border:1px solid var(--border-card);
  border-radius:var(--r-input);padding:10px 14px;cursor:grab;user-select:none}
.p4-srow.dragging{opacity:.4}
.p4-srow.over{border-color:var(--border-on);background:var(--bg-selected)}
.p4-grip{width:14px;color:var(--text-disabled);letter-spacing:-2px;line-height:1;font-size:15px}
.p4-gchip{font-size:12px;line-height:16px;padding:2px 8px;border-radius:var(--r-tag);
  background:var(--bg-tag-on);color:var(--text-body);white-space:nowrap}
.p4-sname{flex:1;font-size:14px;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.p4-scap{font-size:13px;color:var(--text-muted);font-variant-numeric:tabular-nums}
/* 模擬器 */
.p4-simbar{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:12px;font-size:14px}
.p4-simbar .input{width:88px}
.p4-simout{font-size:13px;line-height:20px}
.p4-simhit{padding:10px 14px;border-radius:var(--r-input);background:var(--bg-selected);
  border:1px solid var(--border-on);margin-bottom:10px;font-size:14px;line-height:21px}
.p4-simhit b{font-size:15px}
.p4-simnone{padding:10px 14px;border-radius:var(--r-input);background:#fdecec;color:#b3261e;
  border:1px solid #f3c2be;margin-bottom:10px;font-size:14px;line-height:21px}
.p4-simtbl{width:100%;border-collapse:collapse;font-size:13px;font-variant-numeric:tabular-nums}
.p4-simtbl th,.p4-simtbl td{padding:7px 10px;border-bottom:1px solid var(--border-card);text-align:left;
  white-space:nowrap}
.p4-simtbl th{color:var(--text-muted);font-weight:400}
.p4-simtbl tr.win td{background:var(--bg-selected);font-weight:500}
.p4-simwrap{overflow-x:auto}
.p4-steps{margin:12px 0 0;padding:10px 14px;border-radius:var(--r-input);background:var(--bg-page);
  font-size:13px;line-height:20px;color:var(--text-body)}
.p4-steps ol{margin:0;padding-left:20px}
.p4-algo{font-size:14px;line-height:23px;color:var(--text-body)}
.p4-algo .k{display:inline-block;min-width:22px;color:var(--text-muted);font-variant-numeric:tabular-nums}
.p4-hint{font-size:12px;line-height:18px;color:var(--text-muted)}
/* 定稿的 .radio 實心點是由時段規則表單的 JS 補的，這裡的卡片走 CSS（同一個視覺） */
.radio-card.on .radio{border-color:var(--primary)}
.radio-card.on .radio::after{content:"";width:10px;height:10px;border-radius:50%;background:var(--primary)}
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
src = inject(src, "/* =====================================================\n   預約規則 landing（入口示意）", """/* ===== Part4 v2 注入：自動排位規則（人數級距） =====
   由 tools/build_part4_timeline.py 從 sim.html 產生。 */
/* 「快速排序」按鈕用的兩種排法；不是持續生效的模式，按下去就把順序算好寫入 */
const P4_STRAT = { exact_fit: '小桌在前', largest_first: '大桌在前' };

/* ── 規則資料 ───────────────────────────────────────────── */
function p4DefaultOrder(gidOrder) {
  const gids = db.groups.map(g => g.id);
  const groups = (gidOrder || []).filter(id => gids.includes(id))
    .concat(gids.filter(id => !(gidOrder || []).includes(id)));
  const units = {};
  gids.forEach(id => { units[id] = db.units.filter(u => u.gid === id).map(u => u.id); });
  return { groups, units };
}
/* 群組／單位有增刪時，把排序表補齊、清掉不存在的（新群組排最後、新單位排該群組最後） */
function p4NormOrder(o) {
  const gids = db.groups.map(g => g.id);
  o.groups = o.groups.filter(id => gids.includes(id)).concat(gids.filter(id => !o.groups.includes(id)));
  o.units = o.units || {};
  gids.forEach(gid => {
    const real = db.units.filter(u => u.gid === gid).map(u => u.id);
    const cur = (o.units[gid] || []).filter(id => real.includes(id));
    o.units[gid] = cur.concat(real.filter(id => !cur.includes(id)));
  });
  return o;
}
function p4Ensure() {
  if (!db.auto || db.auto.v !== 2) {
    db.auto = {
      v: 2,
      cuts: [4, 8],
      bands: [
        /* 1–4 人：先填吧台與小桌，不併桌 */
        { maxUnits: 1, order: p4DefaultOrder(['g_bar', 'g_indoor', 'g_outdoor', 'g_default', 'g_room']) },
        /* 5–8 人：大桌先坐滿，最多併 2 桌 */
        { maxUnits: 2, order: p4DefaultOrder(['g_indoor', 'g_outdoor', 'g_room', 'g_default', 'g_bar']) },
        /* 9 人以上：包廂優先，最多併 3 桌 */
        { maxUnits: 3, order: p4DefaultOrder(['g_room', 'g_indoor', 'g_outdoor', 'g_default', 'g_bar']) },
      ],
    };
    /* 5–8 人這一段示範「大桌排前面」的手排結果 */
    db.auto.bands[1].order.units['g_indoor'] = ['u9', 'u8', 'u2', 'u7', 'u1'];
    persist();
  }
  /* bands 長度必須永遠等於 cuts.length + 1（切點是唯一真相） */
  while (db.auto.bands.length < db.auto.cuts.length + 1) {
    const tail = db.auto.bands[db.auto.bands.length - 1];
    db.auto.bands.push({ maxUnits: tail.maxUnits, order: JSON.parse(JSON.stringify(tail.order)) });
  }
  db.auto.bands.length = db.auto.cuts.length + 1;
  db.auto.bands.forEach(b => p4NormOrder(b.order));
  return db.auto;
}
/* 切點 → 級距的上下界。cuts=[4,8] → [1,4] [5,8] [9,null] */
function p4Bounds(cuts) {
  const out = [];
  let lo = 1;
  cuts.forEach(c => { out.push([lo, c]); lo = c + 1; });
  out.push([lo, null]);
  return out;
}
function p4BandLabel(b) { return b[1] === null ? (b[0] + ' 人以上') : (b[0] + '–' + b[1] + ' 人'); }
function p4BandIndex(people, cuts) {
  for (let i = 0; i < cuts.length; i++) if (people <= cuts[i]) return i;
  return cuts.length;
}

/* ── 排位演算法（與後端規格同一條判斷鏈） ───────────────── */
/* 產生某群組內所有 size 個單位的組合 */
function p4Combos(units, size) {
  const out = [];
  (function walk(start, acc) {
    if (acc.length === size) { out.push(acc.slice()); return; }
    for (let i = start; i < units.length; i++) { acc.push(units[i]); walk(i + 1, acc); acc.pop(); }
  })(0, []);
  return out;
}
/* people：大人＋小孩總數。回傳 { bandIdx, cands, chosen, relaxed, steps } */
function p4Assign(people) {
  const A = p4Ensure();
  const bi = p4BandIndex(people, A.cuts);
  const band = A.bands[bi];
  const order = band.order;
  const gRank = {}; order.groups.forEach((id, i) => { gRank[id] = i; });

  const build = (relaxMin) => {
    const cands = [];
    db.groups.forEach(g => {
      const gMerge = g.merge ? Math.max(1, g.mergeMax | 0) : 1;
      const cap = Math.min(band.maxUnits, gMerge);
      const us = (order.units[g.id] || []).map(id => db.units.find(u => u.id === id)).filter(Boolean);
      for (let size = 1; size <= cap; size++) {
        p4Combos(us, size).forEach(combo => {
          const sumMax = combo.reduce((a, u) => a + u.max, 0);
          const sumMin = combo.reduce((a, u) => a + u.min, 0);
          if (sumMax < people) return;
          if (!relaxMin && sumMin > people) return;
          cands.push({
            g, combo, sumMax, sumMin,
            waste: sumMax - people,
            n: combo.length,
            gRank: gRank[g.id],
            uRank: combo.map(u => (order.units[g.id] || []).indexOf(u.id)).sort((a, b) => a - b),
            effCap: cap,
          });
        });
      }
    });
    return cands;
  };

  let cands = build(false);
  let relaxed = false;
  if (!cands.length) { cands = build(true); relaxed = cands.length > 0; }

  const lex = (a, b) => { for (let i = 0; i < Math.max(a.length, b.length); i++) {
    const x = a[i] === undefined ? 1e9 : a[i], y = b[i] === undefined ? 1e9 : b[i];
    if (x !== y) return x - y; } return 0; };
  const ids = c => c.combo.map(u => u.id).join(',');

  cands.sort((a, b) => {
    if (a.n !== b.n) return a.n - b.n;                                  // ① 單位數少者優先
    if (a.gRank !== b.gRank) return a.gRank - b.gRank;                  // ② 該級距的群組順序
    const l = lex(a.uRank, b.uRank); if (l) return l;                   // ③ 該級距的群組內單位順序
    return ids(a) < ids(b) ? -1 : 1;                                    // ④ 單位 id 升冪（保證唯一解）
  });

  return { bandIdx: bi, band, bounds: p4Bounds(A.cuts)[bi], cands, chosen: cands[0] || null, relaxed };
}

/* ── 頁面 ───────────────────────────────────────────────── */
function p4ViewAuto() {
  setTitle([['預約設定', '#/rules'], ['自動排位規則', '#/p4auto']], '自動排位規則');
  p4Ensure();
  $('#content').innerHTML = p4AutoSwitcher('v2') + `
    <div class="p4-note">這一頁決定<b>「同分時選誰」</b>——系統先求「用最少的預約單位滿足人數」，
      再看你在<b>該人數級距</b>下排的群組順序與單位順序。
      與「後台操作偏好 &gt; 預約單位排序」（扁平、可跨群組、只管畫面顯示）是兩套獨立排序。</div>
    <div class="card">
      <div class="card-head"><div class="ch-main">
        <div class="ch-title">人數級距</div>
        <div class="ch-desc">以「切點」切分預約人數，每一段可以有自己的排位規則。級距一定連續、不重疊，不會有漏接的人數。</div>
      </div></div>
      <div class="p4-cuts" id="p4Cuts"></div>
      <div class="p4-hint" style="margin-top:10px">切點必須由小到大、最多 4 個（5 段）。只有一段時，行為與改版前完全相同。</div>
    </div>
    <div id="p4Bands"></div>
    <div class="card">
      <div class="card-head"><div class="ch-main">
        <div class="ch-title">排位模擬器</div>
        <div class="ch-desc">輸入預約人數，看系統實際會怎麼選——調整上面的設定後可立即重跑，不用等到真的有客人預約。</div>
      </div></div>
      <div class="p4-simbar">
        <span>預約人數</span>
        <div class="input"><input id="p4SimN" type="number" min="1" value="2"></div>
        <span style="color:var(--text-muted);font-size:13px">（大人＋小孩總數）</span>
        <button class="btn-md primary" id="p4SimGo">模擬排位</button>
      </div>
      <div class="p4-simout" id="p4SimOut"></div>
    </div>
    <div class="card">
      <div class="card-head"><div class="ch-main">
        <div class="ch-title">演算法判斷順序</div>
        <div class="ch-desc">建立／修改線上預約，以及「自動分配預約單位」開啟時的自建預約，皆適用。</div>
      </div></div>
      <div class="p4-algo">
        <span class="k">1.</span> 依<b>預約人數</b>決定落在哪一個級距，取出該級距的規則<br>
        <span class="k">2.</span> 列出候選組合：同群組內、單位數 ≤ min(級距上限, 群組最多可合併數)、總容納人數足夠<br>
        <span class="k">3.</span> 優先考慮：如何使用<b>最少</b>的預約單位滿足預約人數需求<br>
        <span class="k">4.</span> 再考慮：<b>該級距</b>的群組排列順序<br>
        <span class="k">5.</span> 再考慮：<b>該級距</b>的群組內單位排列順序<br>
        <span class="k">6.</span> 仍相同時：依單位 id 升冪，保證同一筆預約永遠排到同一個位子
      </div>
    </div>`;
  p4RenderCuts(); p4RenderBands();
  $('#p4SimGo').onclick = p4RunSim;
  $('#p4SimN').addEventListener('keydown', e => { if (e.key === 'Enter') p4RunSim(); });
  p4RunSim();
}

function p4RenderCuts() {
  const A = db.auto;
  $('#p4Cuts').innerHTML =
    p4Bounds(A.cuts).map((b, i) => `<span class="p4-cutchip">第 ${i + 1} 段：${p4BandLabel(b)}</span>`).join('')
    + '<span style="width:100%;height:2px"></span>'
    + A.cuts.map((c, i) => `<span class="p4-cutchip">切點 ${i + 1}
        <span class="input" style="width:64px;display:inline-flex"><input type="number" min="1" value="${c}" data-cut="${i}"></span> 人
        <span class="x" data-delcut="${i}">移除</span></span>`).join('')
    + (A.cuts.length < 4 ? '<button class="btn-md ghost" id="p4AddCut">＋ 新增切點</button>' : '');

  $('#p4Cuts').querySelectorAll('input[data-cut]').forEach(el => {
    el.onchange = () => {
      const i = +el.dataset.cut, v = parseInt(el.value, 10);
      const prev = i > 0 ? db.auto.cuts[i - 1] : 0;
      const next = i < db.auto.cuts.length - 1 ? db.auto.cuts[i + 1] : Infinity;
      if (!v || v <= prev || v >= next) { toast('切點必須由小到大且不可重複'); p4RenderCuts(); return; }
      db.auto.cuts[i] = v; persist(); p4RenderCuts(); p4RenderBands(); p4RunSim();
    };
  });
  $('#p4Cuts').querySelectorAll('[data-delcut]').forEach(el => {
    el.onclick = () => {
      const i = +el.dataset.delcut;
      db.auto.cuts.splice(i, 1);
      db.auto.bands.splice(i, 1);              // 併回下一段：移除切點 i 等於刪掉第 i 段的規則
      persist(); p4RenderCuts(); p4RenderBands(); p4RunSim(); toast('已移除切點');
    };
  });
  const add = $('#p4AddCut');
  if (add) add.onclick = () => {
    const last = db.auto.cuts[db.auto.cuts.length - 1] || 0;
    db.auto.cuts.push(last + 4);
    const tail = db.auto.bands[db.auto.bands.length - 1];
    db.auto.bands.push({ maxUnits: tail.maxUnits, order: JSON.parse(JSON.stringify(tail.order)) });   // 新段複製最後一段，店家再微調
    persist(); p4RenderCuts(); p4RenderBands(); p4RunSim(); toast('已新增切點，新的一段複製自前一段');
  };
}

function p4RenderBands() {
  const A = db.auto;
  const bounds = p4Bounds(A.cuts);
  $('#p4Bands').innerHTML = A.bands.map((band, i) => `
    <div class="card">
      <div class="card-head"><div class="ch-main">
        <div class="ch-title p4-bandhead"><span class="p4-bandno">${i + 1}</span>${p4BandLabel(bounds[i])}</div>
        <div class="ch-desc">預約人數落在這一段時套用以下規則。</div>
      </div></div>
      <div class="p4-inline" style="margin-bottom:14px">
        <span>最多可使用</span>
        <select class="sel" data-mu="${i}">${[1, 2, 3, 4].map(v =>
          `<option value="${v}" ${band.maxUnits === v ? 'selected' : ''}>${v}</option>`).join('')}</select>
        <span>個預約單位</span>
        <span style="color:var(--text-muted);font-size:13px">（1 ＝ 不併桌；實際生效值取本欄與群組「最多可合併數量」的較小值）</span>
      </div>
      <div class="p4-quick">
        <span>快速排序：</span>
        <button class="btn-md ghost" data-qs="${i}" data-st="exact_fit">小桌在前</button>
        <button class="btn-md ghost" data-qs="${i}" data-st="largest_first">大桌在前</button>
        <span>當場算好順序寫入，之後仍可手動拖曳微調。</span>
      </div>
      <div style="display:flex;flex-direction:column;gap:10px">${p4OrderHtml(band.order, String(i))}</div>
      <div class="p4-hint" style="margin-top:10px">拖曳以調整順序。群組可整組移動；單位只能在所屬群組內排序，<b>不可跨組</b>。</div>
    </div>`).join('');

  $('#p4Bands').querySelectorAll('select[data-mu]').forEach(el => {
    el.onchange = () => { db.auto.bands[+el.dataset.mu].maxUnits = +el.value; persist(); p4RunSim(); };
  });
  $('#p4Bands').querySelectorAll('[data-qs]').forEach(el => {
    el.onclick = () => { p4QuickSort(el.dataset.qs, el.dataset.st); p4RenderBands(); p4RunSim();
      toast('已依「' + P4_STRAT[el.dataset.st] + '」重排此級距'); };
  });
  A.bands.forEach((b, i) => p4WireOrder(String(i), () => { p4RenderBands(); p4RunSim(); }));
}

/* 排序清單：key ＝ 級距索引字串 */
function p4OrderHtml(order, key) {
  const gs = order.groups.map(id => db.groups.find(g => g.id === id)).filter(Boolean)
    .filter(g => db.units.some(u => u.gid === g.id));
  return gs.map((g, gi) => {
    const us = (order.units[g.id] || []).map(id => db.units.find(u => u.id === id)).filter(Boolean);
    const gMerge = g.merge ? Math.max(1, g.mergeMax | 0) : 1;
    return `<div class="p4-gblock" draggable="true" data-k="${key}" data-gi="${gi}">
      <div class="p4-gbhead"><span class="p4-grip">⣿</span><span class="p4-gchip">${esc(g.name)}</span>
        <span class="ord">第 ${gi + 1} 順位・${us.length} 個單位・最多可合併 ${gMerge}</span></div>
      ${us.map((u, ui) => `<div class="p4-srow" draggable="true" data-k="${key}" data-gi="${gi}" data-ui="${ui}">
          <span class="p4-grip">⣿</span><span class="p4-sname">${esc(u.name)}</span>
          <span class="p4-scap">${u.min}~${u.max} 人</span></div>`).join('')}
    </div>`;
  }).join('');
}
function p4OrderOf(key) { return db.auto.bands[+key].order; }
function p4WireOrder(key, rerender) {
  const order = p4OrderOf(key);
  const gs = order.groups.map(id => db.groups.find(g => g.id === id)).filter(Boolean)
    .filter(g => db.units.some(u => u.gid === g.id));
  const scope = document.querySelectorAll(`[data-k="${key}"]`);
  let src = null;
  scope.forEach(el => {
    const isRow = el.classList.contains('p4-srow');
    el.addEventListener('dragstart', e => {
      if (isRow) e.stopPropagation();
      if (src && !isRow) return;
      src = el; el.classList.add('dragging');
    });
    el.addEventListener('dragend', () => { src = null; rerender(); });
    el.addEventListener('dragover', e => {
      if (!src || src === el) return;
      if (src.classList.contains('p4-srow') !== isRow) return;
      if (isRow) { e.stopPropagation(); if (src.dataset.gi !== el.dataset.gi) return; }
      e.preventDefault(); el.classList.add('over');
    });
    el.addEventListener('dragleave', () => el.classList.remove('over'));
    el.addEventListener('drop', e => {
      e.preventDefault();
      if (!src) return;
      if (isRow) {
        e.stopPropagation();
        if (!src.classList.contains('p4-srow')) return;
        if (src.dataset.gi !== el.dataset.gi) { toast('不可跨群組排序'); return; }
        const gid = gs[+el.dataset.gi].id;
        const arr = order.units[gid];
        const [m] = arr.splice(+src.dataset.ui, 1);
        arr.splice(+el.dataset.ui, 0, m);
      } else {
        if (src.classList.contains('p4-srow')) return;
        const from = order.groups.indexOf(gs[+src.dataset.gi].id);
        const to = order.groups.indexOf(gs[+el.dataset.gi].id);
        const [m] = order.groups.splice(from, 1);
        order.groups.splice(to, 0, m);
      }
      persist();
    });
  });
}
/* 快速排序按鈕：把該級距的排序一次算好寫入（UI 輔助，不是持續生效的模式） */
function p4QuickSort(key, strategy) {
  const order = p4OrderOf(key);
  db.groups.forEach(g => {
    const us = (order.units[g.id] || []).map(id => db.units.find(u => u.id === id)).filter(Boolean);
    us.sort((a, b) => (strategy === 'largest_first' ? b.max - a.max : a.max - b.max)
      || (a.id < b.id ? -1 : 1));
    order.units[g.id] = us.map(u => u.id);
  });
  const capOf = gid => db.units.filter(u => u.gid === gid).reduce((m, u) => Math.max(m, u.max), 0);
  order.groups.sort((a, b) => (strategy === 'largest_first' ? capOf(b) - capOf(a) : capOf(a) - capOf(b))
    || (a < b ? -1 : 1));
  persist();
}

/* ── 模擬器 ─────────────────────────────────────────────── */
function p4RunSim() {
  const out = $('#p4SimOut'); if (!out) return;
  const n = parseInt($('#p4SimN').value, 10);
  if (!n || n < 1) { out.innerHTML = '<div class="p4-simnone">請輸入 1 以上的預約人數。</div>'; return; }
  const r = p4Assign(n);
  const bandTxt = `第 ${r.bandIdx + 1} 段（${p4BandLabel(r.bounds)}）`;
  const capNote = `最多 ${r.band.maxUnits} 個單位`;

  if (!r.chosen) {
    out.innerHTML = `<div class="p4-simnone"><b>${n} 人</b>落在 ${bandTxt}，${capNote}。<br>
      <b>找不到可用的組合</b>——沒有任何單一群組內的組合能容納這個人數。實際系統此時會回覆「該時段無法接受此人數的預約」。</div>`;
    return;
  }
  const c = r.chosen;
  const top = r.cands.slice(0, 8);
  out.innerHTML = `
    <div class="p4-simhit"><b>${n} 人</b> → 落在 ${bandTxt}，${capNote}<br>
      系統會安排：<b>${esc(c.g.name)}／${c.combo.map(u => esc(u.name)).join(' ＋ ')}</b>
      （${c.n} 個單位・可容納 ${c.sumMax} 人・空位 ${c.waste}）</div>
    ${r.relaxed ? '<div class="p4-simnone">注意：沒有任何組合同時滿足「最低人數」限制，系統已放寬最低人數再排一次。</div>' : ''}
    <div class="p4-simwrap"><table class="p4-simtbl">
      <tr><th>順位</th><th>群組</th><th>單位</th><th>單位數</th><th>可容納</th><th>空位</th>
        <th>群組順位</th><th>單位順位</th></tr>
      ${top.map((x, i) => `<tr class="${i === 0 ? 'win' : ''}">
        <td>${i + 1}</td><td>${esc(x.g.name)}</td><td>${x.combo.map(u => esc(u.name)).join(' ＋ ')}</td>
        <td>${x.n}</td><td>${x.sumMax}</td><td>${x.waste}</td>
        <td>${x.gRank + 1}</td><td>${x.uRank.map(v => v + 1).join(',')}</td></tr>`).join('')}
    </table></div>
    ${r.cands.length > top.length ? `<div class="p4-hint" style="margin-top:8px">另有 ${r.cands.length - top.length} 個候選組合未列出。</div>` : ''}
    <div class="p4-steps"><ol>
      <li>依人數 ${n} 落入 ${bandTxt}，取出該段規則。</li>
      <li>列出所有候選組合：同群組內、單位數 ≤ min(本段上限 ${r.band.maxUnits}, 群組最多可合併數)、總容納人數 ≥ ${n}。共 ${r.cands.length} 組。</li>
      <li>單位數少者優先 → 最少為 ${r.cands[0].n} 個單位。</li>
      <li>再比該級距的群組順序，最後比群組內單位順序。</li>
      <li>仍同分時依單位 id 升冪，保證同樣的輸入永遠得到同樣的結果。</li>
    </ol></div>`;
}


/* 兩版切換列——8/17 週會要並排比較 v1 與 v2 */
function p4AutoSwitcher(cur) {
  return `<div class="p4-note" style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
    <b>自動排位規則有兩版可比較：</b>
    <a href="#/p4auto1" style="padding:4px 12px;border-radius:999px;text-decoration:none;
      ${cur === 'v1' ? 'background:#2d6a91;color:#fff' : 'background:#fff;color:#2d6a91;border:1px solid #cfe0eb'}">v1・單純照組別排序</a>
    <a href="#/p4auto" style="padding:4px 12px;border-radius:999px;text-decoration:none;
      ${cur === 'v2' ? 'background:#2d6a91;color:#fff' : 'background:#fff;color:#2d6a91;border:1px solid #cfe0eb'}">v2・依人數級距分段</a>
    <span style="color:var(--text-muted)">${cur === 'v1'
      ? '這是 2026-08-06 的初版：全店只有一份排序，不分人數。'
      : '這是 2026-08-10 定案版：每個人數級距各有一份排序與併桌上限。'}</span>
  </div>`;
}

/* ===== Part4 注入：自動排位規則 v1（2026-08-06 初版，單純照組別排序） =====
   2026-08-11 Ian 要求把初版留著供 8/17 週會與 v2 對照。與 v2 的差別：
   沒有人數級距，全店只有一份排序；判斷鏈是「最少單位 → 群組順序 → 群組內單位順序」。
   v1 直接改 db.groups / db.units 的順序（與 sim.html 同一份資料），
   v2 另存 sessionStorage p4auto_v2，兩者互不影響。 */
function p4v1View() {
  setTitle([['預約設定', '#/rules'], ['自動排位規則（v1）', '#/p4auto1']], '自動排位規則（v1・單純照組別排序）');
  $('#content').innerHTML = p4AutoSwitcher('v1') + `
    <div class="p4-note">此頁的順序<b>只決定「同分時選誰」</b>——系統先求「用最少的預約單位滿足人數」，再看群組順序、再看群組內單位順序。與「後台操作偏好 &gt; 預約單位排序」（扁平、可跨群組）是兩套獨立排序。</div>
    <div class="card">
      <div class="card-head"><div class="ch-main">
        <div class="ch-title">優先排位順序</div>
        <div class="ch-desc">拖曳以調整順序。群組可整組移動；單位只能在所屬群組內排序，不可跨組。</div>
      </div></div>
      <div id="p4v1List" style="display:flex;flex-direction:column;gap:10px"></div>
      <div class="btn-row" style="display:flex;gap:8px;justify-content:flex-end">
        <button class="btn-md primary" id="p4v1Save">儲存</button>
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
  p4v1Render();
  $('#p4v1Save').onclick = () => { persist(); toast('已儲存排位順序'); };
}
function p4v1Render() {
  const gs = db.groups.filter(g => db.units.some(u => u.gid === g.id));
  $('#p4v1List').innerHTML = gs.map((g, gi) => {
    const us = db.units.filter(u => u.gid === g.id);
    return `<div class="p4-gblock" draggable="true" data-gi="${gi}">
      <div class="p4-gbhead"><span class="p4-grip">⣿</span><span class="p4-gchip">${esc(g.name)}</span>
        <span class="ord">第 ${gi + 1} 順位・${us.length} 個單位</span></div>
      ${us.map((u, ui) => `<div class="p4-srow" draggable="true" data-gi="${gi}" data-ui="${ui}">
          <span class="p4-grip">⣿</span><span class="p4-sname">${esc(u.name)}</span>
          <span class="p4-scap">${u.min}~${u.max} 人</span></div>`).join('')}
    </div>`;
  }).join('');
  p4v1Wire(gs);
}
function p4v1Wire(gs) {
  let src = null;
  document.querySelectorAll('#p4v1List .p4-srow').forEach(el => {
    el.addEventListener('dragstart', e => { e.stopPropagation(); src = el; el.classList.add('dragging'); });
    el.addEventListener('dragend', () => { src = null; p4v1Render(); });
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
  document.querySelectorAll('#p4v1List .p4-gblock').forEach(el => {
    el.addEventListener('dragstart', e => { if (src) return; src = el; el.classList.add('dragging'); });
    el.addEventListener('dragend', () => { src = null; p4v1Render(); });
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
             "  if (h === '#/p4auto') return p4ViewAuto();\n  if (h === '#/p4auto1') return p4v1View();\n  if (h === '#/p4deposit') return p4ViewDeposit();\n", label="routes")

# 側欄導向
src = inject(src, "    else if (a.dataset.nav === '顧客預約頁') { location.hash = '#/customer'; }",
             "\n    else if (a.dataset.nav === '自動排位規則') { location.hash = '#/p4auto'; }\n    else if (a.dataset.nav === '訂金管理') { location.hash = '#/p4deposit'; }",
             before=False, label="nav")

# 側欄高亮
_old_active = "  const activeNav = h.startsWith('#/customer') ? '顧客預約頁' : '預約規則';"
if src.count(_old_active) != 1:
    sys.exit(f"❌ activeNav 錨點命中 {src.count(_old_active)} 次")
src = src.replace(_old_active,
    "  const activeNav = (h === '#/p4auto' || h === '#/p4auto1') ? '自動排位規則' : h === '#/p4deposit' ? '訂金管理'\n"
    "    : h.startsWith('#/customer') ? '顧客預約頁' : '預約規則';", 1)


# ── 8) 讓 Part 4 的三塊功能真的點得到 ────────────────────────────
# ⚠️ sim.html 的落地頁是預約區，而預約區會把整個設定側欄 display:none 隱藏
#    （body.area-book）。直接開這份整合版只會看到時間軸，自動排位與訂金
#    根本沒有入口可點——Ian 兩次反映「網站上看不到」都是這個原因。
#    ①落地頁改成自動排位規則 ②右下角常駐一排 Part 4 導覽鈕（預約區也看得到）
_land_old = "  const h = location.hash || '#/book/timeline';   // 落地頁＝預約（與真實後台一致），設定在 rail 上一鍵可達"
if src.count(_land_old) != 1:
    sys.exit(f"❌ 落地頁錨點命中 {src.count(_land_old)} 次")
src = src.replace(_land_old,
    "  const h = location.hash || '#/p4auto';   // Part4 整合版：落地頁改成自動排位規則（原始為 #/book/timeline）", 1)

_fab_old = '<button class="btn-md ghost" onclick="location.href=\'index.html\'">\u2190 Review 入口</button>'
if src.count(_fab_old) != 1:
    sys.exit(f"❌ demo-fab 錨點命中 {src.count(_fab_old)} 次")
src = src.replace(_fab_old,
    '<span class="p4-fablabel">Part 4</span>\n'
    '  <button class="btn-md ghost" onclick="location.hash=\'#/p4auto\'">排位規則</button>\n'
    '  <button class="btn-md ghost" onclick="location.hash=\'#/p4deposit\'">訂金管理</button>\n'
    '  <button class="btn-md ghost" onclick="location.hash=\'#/book/timeline\'">臨時關閉</button>\n'
    '  ' + _fab_old, 1)


src = src.replace("<title>MENU店+ 後台模擬器</title>",
                  "<title>Part4 整合版｜MENU店+ 後台模擬器（時間軸臨時關閉）</title>", 1)
src = src.replace("<!-- MENU店+ 後台模擬器 · 假資料互動 Demo · 維護：FindLife Support -->",
                  "<!-- Part4 整合版：由 tools/build_part4_timeline.py 從 sim.html 產生，請勿直接編輯 -->", 1)

out = root / "part4_timeline.html"
out.write_text(src, encoding="utf-8")
print(f"part4_timeline.html 已產生：{len(src)} chars")
