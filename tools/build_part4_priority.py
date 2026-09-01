#!/usr/bin/env python3
"""part4_priority.html 產生器 — 自動排位規則 v3（自訂規則優先順序）

2026-08-21 會議方向：把會影響排位的規則攤開，店家自選並排序，形成自己的排位模式。

修訂紀錄（同日三版，Ian 回饋逐輪收斂）：
- 二版：只留 v3（v1/v2 整段移除）；規則收斂四條白話版；多組連續模擬
- 三版：拿掉所有原型附註（只留上線會出現的文案）；排位模式改「儲存收合＋編輯展開」；
  群組列改圓圈數字＋「不可合併／可合併 N」精簡標示；移除排位順序預覽；
  模擬器結果新增「桌位圖」圖像版（與列表版可切換）
- 四版：臨時關閉改用 Figma 定稿「1-1 時間軸_管理預約單位開放」（page 2:32）——
  入口為時間軸工具列 off 圖示、專屬模式（返回／中央說明／儲存）、單位列「整日關閉」、
  暫停區塊＝灰底紅虛線＋✕、儲存 toast「已變更預約單位開放」；方案 C（chip＋抽屜＋操作列）整段移除
- 五版（2026-09-01）：訂金管理整頁改照 2026 Aug Figma 定稿「③ 訂金管理」（p4_assets/
  manifest files[2]）重做——藍新註冊閘門（未註冊空狀態／註冊長表單含錯誤態／註冊成功）、
  規則列表（藍新商店代號卡＋訂金規則 (N)＋注意事項）、行內新增/編輯表單、刪除確認 modal、
  綠/紅頂部 toast。timeline 版的提案式訂金頁（p4ViewDeposit 一族）整段移除，
  DEPOSITS 種子改為定稿的兩筆（id d1/d2 不變，時段規則「要求訂金」選單同步不受影響）。

作法沿用 Part 4 慣例：以整合版定稿 part4_timeline.html 為基底注入。
用法：python3 tools/build_part4_priority.py
"""
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "part4_timeline.html"
OUT = ROOT / "src" / "part4_priority.html"

V2_START = "/* ===== Part4 v2 注入：自動排位規則（人數級距） ====="
V1_START = "/* ===== Part4 注入：自動排位規則 v1（2026-08-06 初版，單純照組別排序） ====="
DEP_START = "/* ===== Part4 注入：訂金管理（US4-2） ====="
DEP_END = "/* =====================================================\n   預約規則 landing（入口示意）"
CLOSE_START = "/* ===== Part4 注入：臨時預約關閉（資料層與時間軸互動） ====="
CLOSE_END = "/* ---------- 時間軸 ---------- */"

V3_JS = r"""
/* ===== Part4 v3 注入：自訂排位順序（規則優先順序） =====
   由 tools/build_part4_priority.py 從 part4_timeline.html 注入產生。
   資料存 db.autoPrio2；自帶所有 helper，不依賴已移除的 v1/v2 程式。 */

const P4C_RULES = {
  group: { name: '群組優先',
    desc: '照你排的群組順序坐，排前面的群組先用。',
    eg: '例：室內排第一，2 人預約就先找室內的桌子。' },
  fit: { name: '人數剛好',
    desc: '桌子大小越貼近人數越好——小組不佔大桌，把大桌留給大團。',
    eg: '例：2 人優先坐 1~2 人桌，而不是 4 人桌。' },
  fewest: { name: '少併桌',
    desc: '能用一張桌就不併桌，減少現場搬桌與服務動線。',
    eg: '例：6 人優先坐單一 6 人桌，而不是 2 人桌＋4 人桌。' },
  unitorder: { name: '桌位順序',
    desc: '同一群組內，照你排的桌位順序坐。',
    eg: '例：室內排 In 1 → In 2，就先坐 In 1。' },
};
const P4C_ALL = ['group', 'fit', 'fewest', 'unitorder'];
const P4C_PRESETS = [
  { name: '填滿群組', rules: ['group', 'fit', 'unitorder', 'fewest'] },
  { name: '先找剛好的桌', rules: ['fewest', 'fit', 'group', 'unitorder'] },
];
const P4C_COLORS = ['#2d6a91', '#4c9f70', '#c2803e', '#8a5fb0', '#b05f6d', '#5f8ab0', '#6d8a3e', '#a05656'];

const P4C_CSS = `
.p4c-headrow{display:flex;align-items:flex-start;gap:12px}
.p4c-headrow .ch-main{flex:1}
.p4c-mfoot{display:flex;justify-content:flex-end;gap:10px;margin-top:14px}
.p4c-viz{display:flex;gap:6px;margin:12px 0 0}
.p4c-viz button.on{background:#2d6a91;color:#fff;border-color:#2d6a91}
.p4c-chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}
.p4c-chip{display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:999px;
  font-size:13px;color:#fff}
.p4c-chip .x{cursor:pointer;opacity:.8;font-weight:700}
.p4c-chip .x:hover{opacity:1}
.p4c-chip.na{background:#fff;color:#b05f6d;border:1px dashed #b05f6d}
.p4c-map{display:flex;flex-direction:column;gap:10px;margin-top:12px}
.p4c-mgroup{border:1px solid var(--border,#e2e5ea);border-radius:10px;padding:10px 12px}
.p4c-mghead{display:flex;align-items:center;gap:8px;margin-bottom:8px;font-size:13px}
.p4c-units{display:flex;flex-wrap:wrap;gap:8px}
.p4c-unit{border:1px solid var(--border,#d4d8de);border-radius:8px;padding:7px 10px;font-size:13px;
  background:#fff;display:flex;flex-direction:column;gap:2px;justify-content:center}
.p4c-unit .cap{font-size:11px;color:var(--text-muted,#8a919c)}
.p4c-unit.occ{color:#fff;border-color:transparent}
.p4c-unit.occ .cap{color:rgba(255,255,255,.75)}
.p4c-unit .tag{font-size:11px;font-weight:700}
.p4c-num{display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;
  border-radius:50%;background:#eef1f4;color:#3a4250;font-size:12px;font-weight:700;flex:none}
`;

function p4cDefaultOrder(gidOrder) {
  const gids = db.groups.map(g => g.id);
  const groups = (gidOrder || []).filter(id => gids.includes(id))
    .concat(gids.filter(id => !(gidOrder || []).includes(id)));
  const units = {};
  gids.forEach(id => { units[id] = db.units.filter(u => u.gid === id).map(u => u.id); });
  return { groups, units };
}
function p4cNormOrder(o) {
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
function p4cCombos(units, size) {
  const out = [];
  (function walk(start, acc) {
    if (acc.length === size) { out.push(acc.slice()); return; }
    for (let i = start; i < units.length; i++) { acc.push(units[i]); walk(i + 1, acc); acc.pop(); }
  })(0, []);
  return out;
}
function p4cEnsure() {
  if (!db.autoPrio2) {
    db.autoPrio2 = {
      rules: P4C_PRESETS[0].rules.slice(),
      order: p4cDefaultOrder(['g_indoor', 'g_bar', 'g_outdoor', 'g_default', 'g_room']),
    };
    persist();
  }
  db.autoPrio2.rules = db.autoPrio2.rules.filter(r => P4C_ALL.includes(r));
  p4cNormOrder(db.autoPrio2.order);
  return db.autoPrio2;
}
function p4cOffRules() { return P4C_ALL.filter(r => !db.autoPrio2.rules.includes(r)); }

/* ── 排位引擎 ───────────────────────────────────────────── */
function p4cLex(a, b) {
  for (let i = 0; i < Math.max(a.length, b.length); i++) {
    const x = a[i] === undefined ? 1e9 : a[i], y = b[i] === undefined ? 1e9 : b[i];
    if (x !== y) return x - y;
  }
  return 0;
}
function p4cCmpRule(r, a, b) {
  if (r === 'unitorder') return p4cLex(a.m.unitorder, b.m.unitorder);
  if (r === 'fit') return (a.m.minGap - b.m.minGap) || (a.m.waste - b.m.waste);
  return a.m[r] - b.m[r];
}
function p4cAssign(people, occupied) {
  const P = p4cEnsure();
  const occ = occupied || new Set();
  const gRank = {}; P.order.groups.forEach((id, i) => { gRank[id] = i; });
  const cands = [];
  db.groups.forEach(g => {
    const cap = g.merge ? Math.max(1, g.mergeMax | 0) : 1;
    const us = (P.order.units[g.id] || []).map(id => db.units.find(u => u.id === id))
      .filter(u => u && !occ.has(u.id));
    for (let size = 1; size <= cap; size++) {
      p4cCombos(us, size).forEach(combo => {
        const sumMax = combo.reduce((a, u) => a + u.max, 0);
        const sumMin = combo.reduce((a, u) => a + u.min, 0);
        if (sumMax < people) return;
        cands.push({
          g, combo, sumMax, sumMin, n: combo.length,
          m: {
            group: gRank[g.id],
            waste: sumMax - people,
            minGap: Math.max(0, sumMin - people),
            fewest: combo.length,
            unitorder: combo.map(u => (P.order.units[g.id] || []).indexOf(u.id)).sort((a, b) => a - b),
          },
        });
      });
    }
  });
  const ids = c => c.combo.map(u => u.id).join(',');
  cands.sort((a, b) => {
    for (const r of P.rules) { const d = p4cCmpRule(r, a, b); if (d) return d; }
    return ids(a) < ids(b) ? -1 : 1;
  });
  return { cands, chosen: cands[0] || null };
}
function p4cComboLabel(c) { return esc(c.g.name) + '／' + c.combo.map(u => esc(u.name)).join(' ＋ '); }

/* ── 頁面 ───────────────────────────────────────────────── */
let P4C_SIM = [];            // 模擬中的預約組（人數），依加入順序連續排位
let P4C_EDIT = false;        // 排位模式是否在編輯狀態
let P4C_SNAP = null;         // 編輯前的規則快照（取消用）
let P4C_VIZ = 'list';        // 模擬結果顯示：list＝列表、map＝桌位圖

function p4cView() {
  setTitle([['預約設定', '#/rules'], ['自動排位規則', '#/p4auto']], '自動排位規則');
  p4cEnsure();
  if (!document.getElementById('p4cStyle')) {
    const st = document.createElement('style'); st.id = 'p4cStyle'; st.textContent = P4C_CSS;
    document.head.appendChild(st);
  }
  $('#content').innerHTML = `
    <div class="card" id="p4cModeCard"></div>
    <div class="card">
      <div class="card-head"><div class="ch-main">
        <div class="ch-title">群組與桌位順序</div>
        <div class="ch-desc">「群組優先」與「桌位順序」依這份順序分配，拖曳調整。</div>
      </div></div>
      <div style="display:flex;flex-direction:column;gap:10px" id="p4cOrder"></div>
    </div>
    <div class="card">
      <div class="card-head"><div class="ch-main">
        <div class="ch-title">排位模擬器</div>
        <div class="ch-desc">模擬同一時段陸續進來的預約——後加入的組，會避開已佔用的桌位。</div>
      </div></div>
      <div class="p4-simbar">
        <span>新增一組</span>
        <div class="input"><input id="p4cSimN" type="number" min="1" value="2" style="width:64px"></div>
        <span style="color:var(--text-muted);font-size:13px">人</span>
        <button class="btn-md primary" id="p4cSimAdd">加入</button>
        <span style="width:8px"></span>
        ${[2, 4, 6, 8].map(v => `<button class="btn-md ghost" data-simadd="${v}">＋${v} 人</button>`).join('')}
        <span style="flex:1"></span>
        <button class="btn-md ghost" id="p4cSimClear">全部清除</button>
      </div>
      <div class="p4c-viz">
        <button class="btn-md ghost" data-viz="list">列表</button>
        <button class="btn-md ghost" data-viz="map">桌位圖</button>
      </div>
      <div id="p4cSimOut"></div>
    </div>`;
  p4cRenderMode(); p4cRenderOrder(); p4cRenderSim();
  $('#p4cSimAdd').onclick = p4cAddGroup;
  $('#p4cSimN').addEventListener('keydown', e => { if (e.key === 'Enter') p4cAddGroup(); });
  document.querySelectorAll('[data-simadd]').forEach(el => {
    el.onclick = () => { P4C_SIM.push(+el.dataset.simadd); p4cRenderSim(); };
  });
  $('#p4cSimClear').onclick = () => { P4C_SIM = []; p4cRenderSim(); };
  document.querySelectorAll('[data-viz]').forEach(el => {
    el.onclick = () => { P4C_VIZ = el.dataset.viz; p4cRenderSim(); };
  });
}
function p4cAddGroup() {
  const n = parseInt($('#p4cSimN').value, 10);
  if (!n || n < 1) { toast('請輸入 1 以上的人數'); return; }
  P4C_SIM.push(n); p4cRenderSim();
}

function p4cChainHtml() {
  return `<div class="p4-algo" style="display:flex;flex-wrap:wrap;gap:6px;align-items:center">
    ${db.autoPrio2.rules.map((r, i) => `<span class="p4-cutchip"><b>${i + 1}</b>　${P4C_RULES[r].name}</span>
      <span style="color:var(--text-muted)">→</span>`).join('')}
    <span class="p4-cutchip" style="opacity:.6">同分：單位 id</span>
  </div>`;
}

/* 排位模式卡：預設收合（摘要＋編輯鈕），編輯時展開（預設鍵＋規則卡＋儲存/取消） */
function p4cRenderMode() {
  const card = $('#p4cModeCard');
  if (!P4C_EDIT) {
    card.innerHTML = `
      <div class="card-head p4c-headrow">
        <div class="ch-main"><div class="ch-title">排位模式</div></div>
        <button class="btn-md ghost" id="p4cEdit">✎ 編輯</button>
      </div>
      ${p4cChainHtml()}`;
    $('#p4cEdit').onclick = () => {
      P4C_SNAP = db.autoPrio2.rules.slice();
      P4C_EDIT = true; p4cRenderMode();
    };
    return;
  }
  card.innerHTML = `
    <div class="card-head"><div class="ch-main">
      <div class="ch-title">編輯排位模式</div>
      <div class="ch-desc">拖曳調整優先順序，前面的規則先比；不需要的規則可停用。</div>
    </div></div>
    <div class="p4-quick" style="margin-bottom:12px">
      <span>快速套用：</span>
      ${P4C_PRESETS.map((p, i) => `<button class="btn-md ghost" data-preset="${i}">${p.name}</button>`).join('')}
    </div>
    ${p4cChainHtml()}
    <div id="p4cRules" style="display:flex;flex-direction:column;gap:8px;margin-top:12px"></div>
    <div id="p4cOff"></div>
    <div class="p4c-mfoot">
      <button class="btn-md ghost" id="p4cCancel">取消</button>
      <button class="btn-md primary" id="p4cSave">儲存</button>
    </div>`;
  p4cRenderRules();
  document.querySelectorAll('[data-preset]').forEach(el => {
    el.onclick = () => {
      db.autoPrio2.rules = P4C_PRESETS[+el.dataset.preset].rules.slice();
      persist(); p4cRenderMode(); p4cRenderOrder(); p4cRenderSim();
    };
  });
  $('#p4cSave').onclick = () => {
    P4C_EDIT = false; P4C_SNAP = null; persist();
    p4cRenderMode(); toast('已儲存排位模式');
  };
  $('#p4cCancel').onclick = () => {
    if (P4C_SNAP) db.autoPrio2.rules = P4C_SNAP;
    P4C_EDIT = false; P4C_SNAP = null; persist();
    p4cRenderMode(); p4cRenderOrder(); p4cRenderSim();
  };
}

function p4cRenderRules() {
  const P = db.autoPrio2;
  $('#p4cRules').innerHTML = P.rules.map((r, i) => `
    <div class="p4-gblock" draggable="true" data-rule="${i}" style="padding:10px 12px">
      <div class="p4-gbhead" style="margin:0">
        <span class="p4-grip">⣿</span>
        <span class="p4c-num">${i + 1}</span>
        <span class="p4-gchip">${P4C_RULES[r].name}</span>
        <span class="ord" style="flex:1">${P4C_RULES[r].desc}<br>
          <span style="color:var(--text-muted)">${P4C_RULES[r].eg}</span></span>
        <button class="btn-md ghost" data-ruleoff="${r}">停用</button>
      </div>
    </div>`).join('');
  const off = p4cOffRules();
  $('#p4cOff').innerHTML = !off.length ? '' : `
    <div class="p4-hint" style="margin-top:12px">已停用：</div>
    <div style="display:flex;flex-direction:column;gap:8px;margin-top:6px">
      ${off.map(r => `<div class="p4-gblock" style="padding:10px 12px;opacity:.55">
        <div class="p4-gbhead" style="margin:0">
          <span class="p4-gchip">${P4C_RULES[r].name}</span>
          <span class="ord" style="flex:1">${P4C_RULES[r].desc}</span>
          <button class="btn-md ghost" data-ruleon="${r}">啟用</button>
        </div>
      </div>`).join('')}
    </div>`;

  let src = null;
  document.querySelectorAll('#p4cRules [data-rule]').forEach(el => {
    el.addEventListener('dragstart', () => { src = el; el.classList.add('dragging'); });
    el.addEventListener('dragend', () => { src = null; p4cRenderMode(); p4cRenderOrder(); p4cRenderSim(); });
    el.addEventListener('dragover', e => { if (src && src !== el) { e.preventDefault(); el.classList.add('over'); } });
    el.addEventListener('dragleave', () => el.classList.remove('over'));
    el.addEventListener('drop', e => {
      e.preventDefault(); if (!src) return;
      const [m] = db.autoPrio2.rules.splice(+src.dataset.rule, 1);
      db.autoPrio2.rules.splice(+el.dataset.rule, 0, m);
      persist();
    });
  });
  document.querySelectorAll('[data-ruleoff]').forEach(el => {
    el.onclick = () => {
      if (db.autoPrio2.rules.length <= 1) { toast('至少要保留一條規則'); return; }
      db.autoPrio2.rules = db.autoPrio2.rules.filter(r => r !== el.dataset.ruleoff);
      persist(); p4cRenderMode(); p4cRenderOrder(); p4cRenderSim();
    };
  });
  document.querySelectorAll('[data-ruleon]').forEach(el => {
    el.onclick = () => {
      db.autoPrio2.rules.push(el.dataset.ruleon);
      persist(); p4cRenderMode(); p4cRenderOrder(); p4cRenderSim();
    };
  });
}

/* 群組／桌位順序：圓圈數字＋「不可合併／可合併 N」 */
function p4cMergeLabel(g) {
  const m = g.merge ? Math.max(1, g.mergeMax | 0) : 1;
  return m === 1 ? '不可合併' : '可合併 ' + m;
}
function p4cRenderOrder() {
  const box = $('#p4cOrder'); if (!box) return;
  const order = db.autoPrio2.order;
  const gs = order.groups.map(id => db.groups.find(g => g.id === id)).filter(Boolean)
    .filter(g => db.units.some(u => u.gid === g.id));
  box.innerHTML = gs.map((g, gi) => {
    const us = (order.units[g.id] || []).map(id => db.units.find(u => u.id === id)).filter(Boolean);
    return `<div class="p4-gblock" draggable="true" data-cg="${gi}">
      <div class="p4-gbhead"><span class="p4-grip">⣿</span>
        <span class="p4c-num">${gi + 1}</span>
        <span class="p4-gchip">${esc(g.name)}</span>
        <span class="ord">${p4cMergeLabel(g)}</span></div>
      ${us.map((u, ui) => `<div class="p4-srow" draggable="true" data-cg="${gi}" data-cu="${ui}">
        <span class="p4-grip">⣿</span><span class="p4-sname">${esc(u.name)}</span>
        <span class="p4-scap">${u.min}~${u.max} 人</span></div>`).join('')}
    </div>`;
  }).join('');

  let src = null;
  document.querySelectorAll('#p4cOrder [data-cg]').forEach(el => {
    const isRow = el.classList.contains('p4-srow');
    el.addEventListener('dragstart', e => {
      if (isRow) e.stopPropagation();
      if (src && !isRow) return;
      src = el; el.classList.add('dragging');
    });
    el.addEventListener('dragend', () => { src = null; p4cRenderOrder(); p4cRenderSim(); });
    el.addEventListener('dragover', e => {
      if (!src || src === el) return;
      if (src.classList.contains('p4-srow') !== isRow) return;
      if (isRow) { e.stopPropagation(); if (src.dataset.cg !== el.dataset.cg) return; }
      e.preventDefault(); el.classList.add('over');
    });
    el.addEventListener('dragleave', () => el.classList.remove('over'));
    el.addEventListener('drop', e => {
      e.preventDefault(); if (!src) return;
      const order = db.autoPrio2.order;
      const gs = order.groups.map(id => db.groups.find(g => g.id === id)).filter(Boolean)
        .filter(g => db.units.some(u => u.gid === g.id));
      if (isRow) {
        e.stopPropagation();
        if (!src.classList.contains('p4-srow')) return;
        if (src.dataset.cg !== el.dataset.cg) { toast('不可跨群組排序'); return; }
        const arr = order.units[gs[+el.dataset.cg].id];
        const [m] = arr.splice(+src.dataset.cu, 1);
        arr.splice(+el.dataset.cu, 0, m);
      } else {
        if (src.classList.contains('p4-srow')) return;
        const from = order.groups.indexOf(gs[+src.dataset.cg].id);
        const to = order.groups.indexOf(gs[+el.dataset.cg].id);
        const [m] = order.groups.splice(from, 1);
        order.groups.splice(to, 0, m);
      }
      persist();
    });
  });
}

/* ── 模擬器 ─────────────────────────────────────────────── */
/* 依加入順序連續排位，回傳每組結果＋單位→組別對照 */
function p4cSimRun() {
  const occ = new Set(); const byUnit = {};
  const res = P4C_SIM.map((people, i) => {
    const r = p4cAssign(people, occ);
    if (r.chosen) r.chosen.combo.forEach(u => { occ.add(u.id); byUnit[u.id] = i; });
    return { people, chosen: r.chosen };
  });
  return { res, byUnit };
}
function p4cRenderSim() {
  const out = $('#p4cSimOut'); if (!out) return;
  document.querySelectorAll('[data-viz]').forEach(el =>
    el.classList.toggle('on', el.dataset.viz === P4C_VIZ));
  if (!P4C_SIM.length) {
    out.innerHTML = '<div class="p4-simnone" style="margin-top:12px">尚無模擬預約，輸入人數後按「加入」。</div>';
    return;
  }
  const { res, byUnit } = p4cSimRun();
  if (P4C_VIZ === 'list') { p4cSimList(out, res); } else { p4cSimMap(out, res, byUnit); }
  out.querySelectorAll('[data-simdel]').forEach(el => {
    el.onclick = () => { P4C_SIM.splice(+el.dataset.simdel, 1); p4cRenderSim(); };
  });
}
/* 版本一：列表 */
function p4cSimList(out, res) {
  out.innerHTML = `<div style="display:flex;flex-direction:column;gap:8px;margin-top:12px">
    ${res.map((r, i) => `<div class="p4-gblock" style="padding:10px 12px">
      <div class="p4-gbhead" style="margin:0">
        <span class="p4c-num" style="background:${P4C_COLORS[i % P4C_COLORS.length]};color:#fff">${i + 1}</span>
        <span style="min-width:52px"><b>${r.people} 人</b></span>
        <span class="ord" style="flex:1">${r.chosen
          ? '→ <b>' + p4cComboLabel(r.chosen) + '</b>（可容納 ' + r.chosen.sumMax + ' 人）'
          : '→ <b>無法安排</b>'}</span>
        <button class="btn-md ghost" data-simdel="${i}">移除</button>
      </div>
    </div>`).join('')}</div>`;
}
/* 版本二：桌位圖——所有桌位畫出來，被哪一組坐掉就上那組的顏色 */
function p4cSimMap(out, res, byUnit) {
  const chips = res.map((r, i) => {
    const col = P4C_COLORS[i % P4C_COLORS.length];
    return r.chosen
      ? `<span class="p4c-chip" style="background:${col}">${i + 1}・${r.people} 人
          <span class="x" data-simdel="${i}">✕</span></span>`
      : `<span class="p4c-chip na">${i + 1}・${r.people} 人 無法安排
          <span class="x" data-simdel="${i}" style="color:inherit">✕</span></span>`;
  }).join('');
  const order = db.autoPrio2.order;
  const gs = order.groups.map(id => db.groups.find(g => g.id === id)).filter(Boolean)
    .filter(g => db.units.some(u => u.gid === g.id));
  const map = gs.map((g, gi) => {
    const us = (order.units[g.id] || []).map(id => db.units.find(u => u.id === id)).filter(Boolean);
    return `<div class="p4c-mgroup">
      <div class="p4c-mghead"><span class="p4c-num">${gi + 1}</span><b>${esc(g.name)}</b>
        <span style="color:var(--text-muted)">${p4cMergeLabel(g)}</span></div>
      <div class="p4c-units">
        ${us.map(u => {
          const gi2 = byUnit[u.id];
          const w = 56 + u.max * 12;
          if (gi2 === undefined) return `<div class="p4c-unit" style="min-width:${w}px">
              <span>${esc(u.name)}</span><span class="cap">${u.min}~${u.max} 人</span></div>`;
          const col = P4C_COLORS[gi2 % P4C_COLORS.length];
          return `<div class="p4c-unit occ" style="min-width:${w}px;background:${col}">
              <span>${esc(u.name)}</span>
              <span class="tag">第 ${gi2 + 1} 組・${res[gi2].people} 人</span></div>`;
        }).join('')}
      </div>
    </div>`;
  }).join('');
  out.innerHTML = `<div class="p4c-chips">${chips}</div><div class="p4c-map">${map}</div>`;
}
"""

P4F_JS = r"""
/* ===== Part4 注入：臨時預約關閉（Figma 定稿「1-1 時間軸_管理預約單位開放」） =====
   由 tools/build_part4_priority.py 注入，取代原方案 C（chip＋抽屜＋操作列）。
   入口：時間軸工具列 off 圖示 → 專屬模式（返回／中央說明／儲存）。
   模式內：點選格子或拖曳框選＝暫停該「單位 × 時段」；單位列可勾「整日關閉」；
   暫停區塊＝灰底紅虛線＋✕ 移除；儲存才寫入，返回＝放棄本次變更。
   資料沿用 sessionStorage p4_closures（{date,start,end,unitIds}），定稿 db 不動。 */
const P4_KEY = 'p4_closures';
const P4F_ICON = '<svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M8 3v4M16 3v4M3 10h18"/><path d="M5 5l15 15"/></svg>';
const P4F_END = () => TL_ORIGIN + TL_COLS * 30;
const P4F_CSS = `
body.p4-mode .bk-chips,body.p4-mode .r3,body.p4-mode .bk-views,body.p4-mode .cl{display:none}
body.p4-mode .tl-chip{opacity:.55;pointer-events:none}
.p4f-bar{display:flex;align-items:center;gap:12px}
.p4f-bar .msg{flex:1;text-align:center;font-size:13px;color:var(--text-body)}
.p4f-closed{position:absolute;top:2px;bottom:2px;border-radius:6px;z-index:3;
  background:rgba(122,128,136,.55);border:1.5px dashed #e05b5b;color:#fff;
  display:flex;align-items:center;justify-content:center;font-size:12px;cursor:default;user-select:none}
.p4f-closed .lb{overflow:hidden;white-space:nowrap;text-overflow:ellipsis;padding:0 12px}
.p4f-closed .x{position:absolute;top:-7px;left:-7px;width:16px;height:16px;border-radius:50%;
  background:#3a4250;color:#fff;display:flex;align-items:center;justify-content:center;
  font-size:10px;line-height:1;cursor:pointer;z-index:4}
.p4-closed{background:#eff1f3;border:1px dashed #b9bec6;color:#8a919c;letter-spacing:0}
body.p4-mode .tl-us div{flex-direction:column;gap:1px;justify-content:center}
.p4f-allday{display:flex;align-items:center;gap:4px;font-size:11px;color:var(--text-muted);cursor:pointer}
.p4f-allday input{accent-color:var(--primary);margin:0}
/* 定稿 64:27016 的模式外觀：左欄與時間列深色、群組欄收起（單位單欄）、chip 只留時間 */
body.p4-mode .tl-side,body.p4-mode .tl-side .sh,body.p4-mode .tl-th{background:#3a4250;border-color:#4a5260}
body.p4-mode .tl-side .sh,body.p4-mode .tl-th span,body.p4-mode .tl-us div{color:#fff}
body.p4-mode .tl-gl{display:none}
body.p4-mode .tl-g{border-color:#4a5260}
body.p4-mode .tl-us{flex-basis:90px}
body.p4-mode .tl-us div{border-color:#4a5260}
body.p4-mode .p4f-allday{color:#cfd4db}
body.p4-mode .tl-chip .p,body.p4-mode .tl-chip .cnt,body.p4-mode .tl-chip .bang,body.p4-mode .tl-chip .n svg,body.p4-mode .tl-chip .nm{display:none}
`;
(function () {
  const st = document.createElement('style'); st.id = 'p4fStyle'; st.textContent = P4F_CSS;
  document.head.appendChild(st);
})();

function p4All() { try { return JSON.parse(sessionStorage.getItem(P4_KEY)) || []; } catch (e) { return []; } }
function p4Save(v) { sessionStorage.setItem(P4_KEY, JSON.stringify(v)); }
function p4Of(date) { return p4All().filter(c => c.date === date); }
function p4RangesOf(date, unitId) {
  return p4Of(date).filter(c => c.unitIds.includes(unitId)).map(c => [toMin(c.start), toMin(c.end)]);
}
/* 方案 C 的 chip／抽屜／空間圖清單提示已移除；保留同名掛勾給定稿層呼叫 */
function p4Chip() { return ''; }
function p4Note() {}
function p4BindChip() {
  const b = document.getElementById('p4fEnter');
  if (b) b.onclick = () => { p4Mode = true; p4WorkDate = null; viewBooking(); };
}

let p4Mode = false;
let p4Work = [];            // 模式中的工作副本：{ u: unitId, s, e }（分鐘）
let p4WorkDate = null;
let p4Sel = null, p4Drag = false, p4Bound = false, p4Ctx = null;

/* 同一單位的區間合併，儲存與顯示都用得到 */
function p4fMerge(list) {
  const byU = {};
  list.forEach(w => { (byU[w.u] = byU[w.u] || []).push([w.s, w.e]); });
  const out = [];
  Object.keys(byU).forEach(u => {
    const rs = byU[u].sort((a, b) => a[0] - b[0]);
    const m = [];
    rs.forEach(([s, e]) => {
      if (m.length && s <= m[m.length - 1][1]) m[m.length - 1][1] = Math.max(m[m.length - 1][1], e);
      else m.push([s, e]);
    });
    m.forEach(([s, e]) => out.push({ u, s, e }));
  });
  return out;
}

function p4Timeline(rows) {
  const inner = document.querySelector('.tl-inner');
  if (!inner) return;
  const rowEls = [...inner.querySelectorAll('.tl-row')];

  if (!p4Mode) {
    document.body.classList.remove('p4-mode');
    /* 一般時間軸：已暫停的時段以灰色虛線區塊顯示 */
    rowEls.forEach((el, i) => {
      const u = rows[i]; if (!u) return;
      p4RangesOf(bk.date, u.id).forEach(([s, e]) => {
        const s2 = Math.max(TL_ORIGIN, s), e2 = Math.min(P4F_END(), e);
        if (e2 <= s2) return;
        const d = document.createElement('div');
        d.className = 'p4-closed';
        d.style.left = (s2 - TL_ORIGIN) / 30 * TL_COLW + 'px';
        d.style.width = (e2 - s2) / 30 * TL_COLW - 2 + 'px';
        d.textContent = '暫停線上預約';
        el.appendChild(d);
      });
    });
    return;
  }

  /* ── 管理預約單位開放模式 ── */
  document.body.classList.add('p4-mode');
  const h1 = document.querySelector('.bk-head h1');
  if (h1) h1.textContent = '管理預約單位開放';
  const shEl = document.querySelector('.tl-side .sh');
  if (shEl) shEl.textContent = '預約單位';   /* 定稿 64:27016 的角落標題 */
  const head = document.querySelector('.bk-head');
  if (head && !head.querySelector('.p4f-bar')) {
    const bar = document.createElement('div');
    bar.className = 'p4f-bar';
    bar.innerHTML = `<button class="btn-md ghost" id="p4fBack">← 返回</button>
      <span class="msg">點選格子，或長按框選欲暫停開放的預約單位與時段</span>
      <button class="btn-md primary" id="p4fSave">儲存</button>`;
    head.appendChild(bar);
    bar.querySelector('#p4fBack').onclick = () => {
      p4Mode = false; p4Work = []; p4WorkDate = null; p4Sel = null; viewBooking();
    };
    bar.querySelector('#p4fSave').onclick = p4fSaveAll;
  }

  /* 換日（或初次進入）時，工作副本從已儲存的設定重建 */
  if (p4WorkDate !== bk.date) {
    p4WorkDate = bk.date;
    p4Work = [];
    p4Of(bk.date).forEach(c => c.unitIds.forEach(id => p4Work.push({ u: id, s: toMin(c.start), e: toMin(c.end) })));
    p4Work = p4fMerge(p4Work);
  }

  /* 單位列加「整日關閉」 */
  const sideCells = [...document.querySelectorAll('.tl-side .tl-us > div')];
  sideCells.forEach((cell, i) => {
    const u = rows[i]; if (!u || cell.querySelector('.p4f-allday')) return;
    const lb = document.createElement('label');
    lb.className = 'p4f-allday';
    lb.innerHTML = `<input type="checkbox" data-u="${u.id}">整日關閉`;
    cell.appendChild(lb);
    lb.querySelector('input').onchange = (ev) => {
      p4Work = p4Work.filter(w => w.u !== u.id);
      if (ev.target.checked) p4Work.push({ u: u.id, s: TL_ORIGIN, e: P4F_END() });
      p4fPaint();
    };
  });

  p4Ctx = { rows, rowEls, inner };
  p4fPaint();

  /* 點選格子＝暫停 30 分鐘；拖曳框選＝暫停整個範圍（可跨多列） */
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
  p4Ctx.cellOf = cellOf;
  inner.addEventListener('mousedown', ev => {
    if (!p4Mode) return;
    if (ev.target.closest('.p4f-closed')) return;   // 已暫停區塊：只有 ✕ 有作用
    const p = cellOf(ev); if (!p) return;
    ev.preventDefault();
    p4Drag = true; p4Sel = { r0: p.r, c0: p.c, r1: p.r, c1: p.c };
    p4fPaintSel();
  });
  if (!p4Bound) {
    p4Bound = true;
    window.addEventListener('mousemove', ev => {
      if (!p4Drag || !p4Ctx || !p4Sel) return;
      const p = p4Ctx.cellOf(ev); if (!p) return;
      if (p.r === p4Sel.r1 && p.c === p4Sel.c1) return;
      p4Sel.r1 = p.r; p4Sel.c1 = p.c;
      p4fPaintSel();
    });
    window.addEventListener('mouseup', () => {
      if (!p4Drag || !p4Sel || !p4Ctx) { p4Drag = false; return; }
      p4Drag = false;
      const R = { r0: Math.min(p4Sel.r0, p4Sel.r1), r1: Math.max(p4Sel.r0, p4Sel.r1),
                  c0: Math.min(p4Sel.c0, p4Sel.c1), c1: Math.max(p4Sel.c0, p4Sel.c1) };
      const s = TL_ORIGIN + R.c0 * 30, e = TL_ORIGIN + (R.c1 + 1) * 30;
      for (let r = R.r0; r <= R.r1; r++) {
        const u = p4Ctx.rows[r]; if (!u) continue;
        p4Work.push({ u: u.id, s, e });
      }
      p4Work = p4fMerge(p4Work);
      p4Sel = null;
      p4fPaint();
    });
  }
}

/* 已暫停區塊（工作副本）＋整日勾選同步 */
function p4fPaint() {
  if (!p4Ctx) return;
  const { rows, rowEls, inner } = p4Ctx;
  inner.querySelectorAll('.p4f-closed, .p4-sel').forEach(e => e.remove());
  rows.forEach((u, i) => {
    const el = rowEls[i]; if (!el) return;
    p4Work.filter(w => w.u === u.id).forEach(w => {
      const s2 = Math.max(TL_ORIGIN, w.s), e2 = Math.min(P4F_END(), w.e);
      if (e2 <= s2) return;
      const d = document.createElement('div');
      d.className = 'p4f-closed';
      d.style.left = (s2 - TL_ORIGIN) / 30 * TL_COLW + 'px';
      d.style.width = (e2 - s2) / 30 * TL_COLW - 2 + 'px';
      d.innerHTML = `<span class="x">✕</span><span class="lb">暫停線上預約</span>`;
      d.querySelector('.x').onclick = (ev) => {
        ev.stopPropagation();
        p4Work = p4Work.filter(x => x !== w);
        p4fPaint();
      };
      el.appendChild(d);
    });
  });
  document.querySelectorAll('.p4f-allday input').forEach(cb => {
    cb.checked = p4Work.some(w => w.u === cb.dataset.u && w.s <= TL_ORIGIN && w.e >= P4F_END());
  });
}
function p4fPaintSel() {
  if (!p4Ctx || !p4Sel) return;
  const { rowEls, inner } = p4Ctx;
  inner.querySelectorAll('.p4-sel').forEach(e => e.remove());
  const R = { r0: Math.min(p4Sel.r0, p4Sel.r1), r1: Math.max(p4Sel.r0, p4Sel.r1),
              c0: Math.min(p4Sel.c0, p4Sel.c1), c1: Math.max(p4Sel.c0, p4Sel.c1) };
  for (let r = R.r0; r <= R.r1; r++) {
    const el = rowEls[r]; if (!el) continue;
    const d = document.createElement('div');
    d.className = 'p4-sel';
    d.style.left = R.c0 * TL_COLW + 'px';
    d.style.width = (R.c1 - R.c0 + 1) * TL_COLW - 2 + 'px';
    d.style.top = '2px'; d.style.bottom = '2px';
    el.appendChild(d);
  }
}

function p4fSaveAll() {
  const recs = p4fMerge(p4Work).map(w => ({
    id: 'p4_' + w.u + '_' + w.s,
    date: bk.date, start: toHHMM(w.s), end: toHHMM(w.e), unitIds: [w.u],
  }));
  p4Save(p4All().filter(c => c.date !== bk.date).concat(recs));
  p4Mode = false; p4Work = []; p4WorkDate = null; p4Sel = null;
  viewBooking();
  toast('已變更預約單位開放');
}
"""

DEP2_JS = r"""
/* ===== Part4 注入：訂金管理（2026 Aug Figma 定稿「③ 訂金管理」多組訂金規則管理） =====
   由 tools/build_part4_priority.py 注入，取代 timeline 版的提案式訂金頁。
   仍直接操作 sim.html 既有的 DEPOSITS 陣列——新增／編輯／刪除後，
   時段規則表單的「要求訂金 → 套用規則」選單會同步（讀同一份資料與 desc 欄位）。
   藍新註冊狀態存 sessionStorage p4_dep_reg：'1'=已註冊（預設）、'new'=剛註冊成功、'0'=未註冊。 */

const P4D_LINK = '<svg viewBox="0 0 24 24"><path d="M14 5h5v5M19 5l-8 8M19 14v5a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/></svg>';
const P4D_CSS = `
.p4d-sub{font-size:14px;line-height:20px;color:var(--text-body)}
.p4d-hr{border:0;border-top:1px solid var(--border-card);margin:16px 0 20px}
.p4d-gray{background:#f0f0f0;border-radius:var(--r-card);padding:18px 20px;display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.p4d-gray .m{flex:1;min-width:220px}
.p4d-gray .t{font-size:17px;line-height:24px;font-weight:700;color:var(--text-strong)}
.p4d-gray .t.ok{color:var(--primary)}
.p4d-gray .d{font-size:13px;line-height:19px;color:var(--text-body);margin-top:6px}
.p4d-gray .btn-md{background:#fff}
.p4d-sechead{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:24px 0 14px}
.p4d-sectitle{font-size:17px;font-weight:700;color:var(--text-strong);font-variant-numeric:tabular-nums}
.p4d-rule{background:#fff;border:1px solid var(--border-card);border-radius:var(--r-card);
  box-shadow:0 1px 2px rgba(0,0,0,.04);padding:14px 18px;display:flex;align-items:center;gap:6px;margin-bottom:12px}
.p4d-rule .m{flex:1;min-width:0}
.p4d-rule .n{font-size:15px;font-weight:700;color:var(--text-strong)}
.p4d-rule .d{font-size:13px;line-height:19px;color:var(--text-body);margin-top:4px}
.p4d-ico{width:34px;height:34px;border-radius:50%;border:0;background:transparent;display:flex;align-items:center;justify-content:center;cursor:pointer;color:var(--text-body);flex:none}
.p4d-ico svg{width:17px;height:17px;stroke:currentColor;stroke-width:1.7;fill:none}
.p4d-ico:hover{background:#ececec}
.p4d-ico.del{color:var(--alert)}
.p4d-ico.del:hover{background:#f9e9e9}
.p4d-null{border:1px dashed #cfcfcf;border-radius:10px;padding:26px 16px;text-align:center;
  font-size:15px;font-weight:700;color:var(--text-strong);margin-bottom:12px}
.p4d-notes{background:#f0f0f0;border-radius:var(--r-card);padding:16px 20px;font-size:13px;line-height:21px;color:var(--text-body);margin-top:18px}
.p4d-notes .nt{font-size:14px;font-weight:700;color:var(--text-strong);margin-bottom:6px}
.p4d-notes ul{margin:0;padding-left:18px;display:flex;flex-direction:column;gap:4px}
.p4d-notes ul ul{margin-top:4px;list-style:none;padding-left:4px}
.p4d-notes ul ul li::before{content:'◦';margin-right:6px}
.p4d-notes ol{margin:4px 0 0;padding-left:22px;display:flex;flex-direction:column;gap:4px}
.p4d-banner{display:flex;align-items:flex-start;gap:8px;margin:20px 0 18px;color:#c94848;font-size:16px;line-height:24px;font-weight:700}
.p4d-banner svg{width:20px;height:20px;stroke:#c94848;stroke-width:1.8;fill:none;flex:none;margin-top:2px}
.p4d-form{margin-bottom:12px}
.p4d-formtitle{font-size:15px;color:var(--text-muted)}
.p4d-grouplabel{font-size:14px;color:var(--text-muted)}
.p4d-div{border:0;border-top:1px solid var(--border-card);margin:2px 0}
.p4d-inline{display:flex;align-items:center;gap:10px;flex-wrap:wrap;font-size:14px;color:var(--text-strong)}
.p4d-inline .input{width:88px}
.p4d-inline .input input{text-align:center}
.p4d-err{display:none;color:var(--alert);font-size:12px;line-height:16px}
.p4d-err.show{display:block}
.input.p4d-bad{border-color:var(--alert)}
.input.p4d-bad input{color:var(--alert)}
.hint.p4d-bad{color:var(--alert)}
sel.p4d-bad,select.p4d-bad{border-color:var(--alert)}
.p4d-toast{position:fixed;top:88px;left:50%;transform:translateX(-50%);min-width:220px;text-align:center;
  padding:10px 24px;border-radius:6px;color:#fff;font-size:14px;line-height:20px;z-index:9999;
  opacity:0;pointer-events:none;transition:opacity .2s}
.p4d-toast.ok{background:#6cc39b}
.p4d-toast.err{background:#d05c5c}
.p4d-toast.show{opacity:1}
.p4d-demo{margin-top:26px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;font-size:12px;color:var(--text-disabled)}
.p4d-demo a{color:var(--text-muted);text-decoration:underline;cursor:pointer}
.p4d-demo a.cur{color:var(--text-body);font-weight:700;text-decoration:none}
.p4d-modal h3{font-weight:700}
.p4d-mbody{margin:0 -24px;padding:20px 24px;background:#f0f0f0;font-size:15px;line-height:24px;color:var(--text-body)}
.btn-md.p4d-danger{background:var(--alert);color:#fff}
.p4d-regsec{display:flex;flex-direction:column;gap:16px}
.p4d-radrow{display:flex;align-items:center;gap:28px;flex-wrap:wrap}
.p4d-radrow .check{align-items:center}
textarea.p4d-ta{min-height:96px;padding:8px 10px;border:1px solid var(--border-field);border-radius:var(--r-input);
  font-size:14px;line-height:20px;font-family:inherit;outline:0;resize:vertical;width:100%}
textarea.p4d-ta:focus{border-color:var(--border-on)}
textarea.p4d-ta::placeholder{color:var(--text-disabled)}
@media (max-width:760px){
  .p4d-gray .btn-md{width:100%;justify-content:center}
  .p4d-rule{flex-wrap:wrap}
}
`;
(function(){ const st=document.createElement('style'); st.id='p4dStyle'; st.textContent=P4D_CSS; document.head.appendChild(st); })();

/* 「重置範例」也把訂金規則與藍新註冊狀態還原（DEPOSITS 是 const，reload 以外要手動回種子） */
(function(){
  const rb = document.getElementById('resetBtn');
  if (rb) rb.addEventListener('click', () => {
    DEPOSITS.splice(0, DEPOSITS.length,
      { id: 'd1', name: '週末晚上', desc: '預先收款：2人以上，每人200元', way: 'prepay', cond: 'people', minPeople: 2, perPerson: 200, fixed: 200 },
      { id: 'd2', name: '特殊節日', desc: '信用卡授權綁定：每組300元', way: 'auth', cond: 'fixed', minPeople: 1, perPerson: 200, fixed: 300 });
    sessionStorage.removeItem('p4_dep_reg');
    P4D_FORM = null;
    if (location.hash.startsWith('#/p4deposit')) p4ViewDeposit();
  });
})();

function p4dReg(){ return sessionStorage.getItem('p4_dep_reg') || '1'; }
function p4dSetReg(v){ sessionStorage.setItem('p4_dep_reg', v); }
let p4dToastTimer;
function p4dToast(msg, kind){
  let t = document.getElementById('p4dToast');
  if (!t){ t = document.createElement('div'); t.id='p4dToast'; document.body.appendChild(t); }
  t.className = 'p4d-toast ' + (kind || 'ok'); t.textContent = msg;
  requestAnimationFrame(() => t.classList.add('show'));
  clearTimeout(p4dToastTimer); p4dToastTimer = setTimeout(() => t.classList.remove('show'), 2200);
}
function p4dDesc(f){
  return (f.way === 'auth' ? '信用卡授權綁定' : '預先收款') + '：' +
    (f.cond === 'fixed' ? `每組${f.fixed}元` : `${f.minPeople}人以上，每人${f.perPerson}元`);
}

/* 表單狀態：null＝關閉；{mode:'add'} 或 {mode:'edit', id} ＋工作值 f ＋錯誤 err */
let P4D_FORM = null;

const P4D_NOTES = `
  <div class="p4d-notes"><div class="nt">注意事項</div><ul>
    <li>若顧客未如期完成付款或信用卡授權之操作，系統將自動取消預約。</li>
    <li>預先收款付款期限：送出預約申請後至隔日晚上22:59。若預約時間為送出預約當日或隔日，期限則為預約時間的前30分鐘。
      <ul><li>範例1：顧客於1月1日送出1月10日中午12:00的預約申請，付款期限為1月2日晚上22:59。</li>
      <li>範例2：顧客於1月1日送出1月2日中午12:00的預約申請，付款期限為1月2日上午11:30。</li></ul></li>
    <li>信用卡授權綁定操作期限：送出預約申請後的30分鐘內。</li>
    <li>信用卡授權完成後，系統僅會保留授權額度，不會自動扣款。如需請款請在授權期限內，於預約清單中找到該筆預約，手動點擊「請款」按鈕，才能執行扣款程序。</li>
    <li>信用卡授權期限為預約日後七日內，若逾期未完成請款，授權將自動失效且無法再進行扣款，系統亦不會保存顧客的信用卡資訊。
      <ul><li>範例：顧客若因故取消1月1日下午13:00的預約，需於1月8日晚上22:59前完成請款操作。</li></ul></li>
  </ul></div>`;

function p4dDemoBar(){
  const r = p4dReg();
  const lk = (v, n) => `<a data-p4dreg="${v}" class="${r === v ? 'cur' : ''}">${n}</a>`;
  return `<div class="p4d-demo">原型展示｜藍新註冊狀態：${lk('1','已註冊')} ${lk('new','剛註冊成功')} ${lk('0','未註冊')}</div>`;
}
function p4dBindDemo(){
  document.querySelectorAll('[data-p4dreg]').forEach(a => a.onclick = () => {
    p4dSetReg(a.dataset.p4dreg); P4D_FORM = null;
    if (location.hash === '#/p4deposit') p4ViewDeposit(); else location.hash = '#/p4deposit';
  });
}

function p4ViewDeposit(){
  P4D_FORM = P4D_FORM || null;
  setTitle([['訂金管理', '#/p4deposit']], '訂金管理');
  const reg = p4dReg();
  let body;
  if (reg === '0'){
    body = `
      <div class="p4d-gray"><div class="m">
        <div class="t">尚未開通訂金功能</div>
        <div class="d">請先透過MENU店+註冊藍新企業會員</div>
      </div><button class="btn-md ghost" id="p4dGoReg">${P4D_LINK} 註冊</button></div>`;
  } else if (reg === 'new'){
    body = `
      <div class="p4d-gray" style="background:#fff;border:1px solid var(--border-card)"><div class="m">
        <div class="t ok">藍新企業會員註冊成功！</div>
        <div class="d">尚需等待藍新金流審核商家資料</div>
      </div><button class="btn-md ghost-green" id="p4dLogin">${P4D_LINK} 登入藍新</button></div>
      <div class="p4d-banner"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7.5v5.5M12 16.5v.01"/></svg>
        <span>請登入藍新金流並上傳必要的文件照片，以完成藍新帳號驗證流程。</span></div>
      <div class="p4d-notes"><div class="nt">藍新金流帳號驗證流程說明</div><ul>
        <li>初始登入資訊、審核進度與補件通知會發送至您的藍新管理者信箱中，請留意信件通知。</li>
        <li>因應《洗錢防制法》與相關法規規定，藍新金流要求需於藍新金流服務平台上傳關於您與您的商店驗證資料，如：營業登記文件、金融帳戶存摺影本、實體店面照片等，才能完成帳號審核。</li>
        <li>您需要準備的資料種類以藍新金流通知為主，請於登入平台後透過下列路徑檢查是否有需要補件或異動的資訊：
          <ol><li>會員中心 &gt; 基本資料設定</li>
          <li>會員中心 &gt; 基本資料設定 &gt; 金融機構帳號設定</li>
          <li>會員中心 &gt; 商店管理 &gt; 詳細資料</li></ol></li>
        <li>上傳所有必要資料後，需約3至4個工作天藍新金流才會完成審核。審核通過後，即可啟用「訂金功能」。</li>
      </ul></div>`;
  } else {
    body = `
      <div class="p4d-gray"><div class="m">
        <div class="t">藍新商店代號：MINU52</div>
        <div class="d">訂金款項由藍新金流代收，如有收付款相關問題，請直接聯繫藍新金流或付款人。</div>
      </div><button class="btn-md ghost" id="p4dLogin">${P4D_LINK} 登入藍新</button></div>
      <div class="p4d-sechead">
        <div class="p4d-sectitle">訂金規則 (${DEPOSITS.length})</div>
        <button class="btn-md primary" id="p4dAdd"><svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg> 規則</button>
      </div>
      <div id="p4dList"></div>
      ${P4D_NOTES}`;
  }
  $('#content').innerHTML = `
    <div class="p4d-sub">您可以設定多組訂金規則，供不同的預約時段選擇套用。</div>
    <hr class="p4d-hr">
    ${body}
    ${p4dDemoBar()}`;
  p4dBindDemo();
  const go = $('#p4dGoReg'); if (go) go.onclick = () => { location.hash = '#/p4deposit/register'; };
  const lg = $('#p4dLogin'); if (lg) lg.onclick = () => p4dToast('原型示意：實際會另開藍新金流登入頁', 'ok');
  const ad = $('#p4dAdd'); if (ad) ad.onclick = () => {
    P4D_FORM = { mode: 'add', f: { name: '', way: 'prepay', cond: 'people', minPeople: 1, perPerson: 200, fixed: 200 }, err: {} };
    p4dRenderList();
  };
  if (reg === '1') p4dRenderList();
}

function p4dFormHtml(){
  const { mode, f, err } = P4D_FORM;
  const numIn = (id, val, on, ph, bad) => `<div class="input${on ? '' : ' disabled'}${on && bad ? ' p4d-bad' : ''}">
    <input id="${id}" type="text" inputmode="numeric" value="${on ? esc(String(val)) : ''}" placeholder="${ph}" ${on ? '' : 'disabled'}></div>`;
  const people = f.cond === 'people', fixed = f.cond === 'fixed';
  return `
  <div class="card p4d-form" id="p4dForm">
    <div class="p4d-formtitle">${mode === 'edit' ? '編輯' : '新增'}訂金規則</div>
    <div class="field">
      <span class="field-label">訂金規則名稱</span>
      <div class="input${err.name ? ' p4d-bad' : ''}"><input id="p4dfName" value="${esc(f.name)}" placeholder="如：特殊節慶"></div>
      <span class="p4d-err${err.name ? ' show' : ''}">${err.name || ''}</span>
    </div>
    <hr class="p4d-div">
    <div class="p4d-grouplabel">收款方式</div>
    <div style="display:flex;flex-direction:column;gap:12px">
      ${[['prepay', '預先收款', '顧客可透過轉帳、信用卡、超商代碼完成訂金支付'],
         ['auth', '信用卡授權綁定', '顧客需完成信用卡授權，若顧客因故爽約，您可於授權期限內請款收取取消金額']]
        .map(([v, n, sub]) => `<label class="check" data-p4dway="${v}"><span class="radio p4-radio"${f.way === v ? ' data-on' : ''}></span>
          <span><span class="ck-label">${n}</span><div class="ck-desc">${sub}</div></span></label>`).join('')}
    </div>
    <hr class="p4d-div">
    <div class="p4d-grouplabel">收款條件</div>
    <div style="display:flex;flex-direction:column;gap:14px">
      <div>
        <label class="check p4d-inline" data-p4dcond="people" style="display:flex"><span class="radio p4-radio"${people ? ' data-on' : ''}></span>
          <span class="ck-label">依據預約人數</span>
          ${numIn('p4dfMin', f.minPeople, people, '1', err.people)}<span>人以上，</span>
          ${numIn('p4dfPer', f.perPerson, people, '200', err.people)}<span>元/人</span></label>
        <span class="p4d-err${err.people ? ' show' : ''}" style="margin:4px 0 0 28px">請輸入大於或等於 1 的人數與金額</span>
      </div>
      <div>
        <label class="check p4d-inline" data-p4dcond="fixed" style="display:flex"><span class="radio p4-radio"${fixed ? ' data-on' : ''}></span>
          <span class="ck-label">固定金額</span>
          ${numIn('p4dfFix', f.fixed, fixed, '200', err.fixed)}<span>元/組</span></label>
        <span class="p4d-err${err.fixed ? ' show' : ''}" style="margin:4px 0 0 28px">請輸入大於或等於 1 的金額</span>
      </div>
    </div>
    <hr class="p4d-div">
    <div class="btn-row">
      <button class="btn-md ghost" id="p4dfCancel">取消</button>
      <button class="btn-md primary" id="p4dfSave">儲存</button>
    </div>
  </div>`;
}

function p4dRenderList(){
  const box = $('#p4dList'); if (!box) return;
  const F = P4D_FORM;
  const ruleCard = d => `
    <div class="p4d-rule"><div class="m">
      <div class="n">${esc(d.name)}</div>
      <div class="d">${esc(d.desc)}</div>
    </div>
    <button class="p4d-ico" data-p4de="${d.id}" title="編輯">${ICONS.edit}</button>
    <button class="p4d-ico del" data-p4dd="${d.id}" title="刪除">${ICONS.trash}</button></div>`;
  let html = '';
  if (F && F.mode === 'add') html += p4dFormHtml();
  if (DEPOSITS.length){
    html += DEPOSITS.map(d => (F && F.mode === 'edit' && F.id === d.id) ? p4dFormHtml() : ruleCard(d)).join('');
  } else if (!F){
    html += `<div class="p4d-null">尚未設定訂金規則</div>`;
  }
  box.innerHTML = html;
  const cnt = document.querySelector('.p4d-sectitle');
  if (cnt) cnt.textContent = `訂金規則 (${DEPOSITS.length})`;
  document.querySelectorAll('[data-p4de]').forEach(b => b.onclick = () => {
    const d = DEPOSITS.find(x => x.id === b.dataset.p4de); if (!d) return;
    P4D_FORM = { mode: 'edit', id: d.id, orig: JSON.stringify([d.name, d.way, d.cond, d.minPeople, d.perPerson, d.fixed]),
      f: { name: d.name, way: d.way, cond: d.cond, minPeople: d.minPeople, perPerson: d.perPerson, fixed: d.fixed }, err: {} };
    p4dRenderList();
  });
  document.querySelectorAll('[data-p4dd]').forEach(b => b.onclick = () => p4dDelete(DEPOSITS.find(x => x.id === b.dataset.p4dd)));
  if (F) p4dBindForm();
}

function p4dGrab(){
  const f = P4D_FORM.f;
  const v = id => { const el = document.getElementById(id); return el && !el.disabled ? el.value : null; };
  const n = v('p4dfName'); if (n !== null) f.name = n;
  if (f.cond === 'people'){ const a = v('p4dfMin'), b = v('p4dfPer'); if (a !== null) f.minPeople = a; if (b !== null) f.perPerson = b; }
  else { const c = v('p4dfFix'); if (c !== null) f.fixed = c; }
}
function p4dDirty(){
  const F = P4D_FORM;
  if (F.mode === 'add') return true;
  return F.orig !== JSON.stringify([F.f.name, F.f.way, F.f.cond, +F.f.minPeople, +F.f.perPerson, +F.f.fixed]);
}
function p4dSyncSave(){
  const btn = $('#p4dfSave'); if (!btn) return;
  const on = String(P4D_FORM.f.name).trim() !== '' && p4dDirty();
  btn.classList.toggle('primary', on);
  btn.classList.toggle('disabled', !on);
}
function p4dBindForm(){
  p4dSyncSave();
  ['p4dfName', 'p4dfMin', 'p4dfPer', 'p4dfFix'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('input', () => { p4dGrab(); p4dSyncSave(); });
  });
  document.querySelectorAll('[data-p4dway]').forEach(el => el.onclick = () => {
    p4dGrab(); P4D_FORM.f.way = el.dataset.p4dway; p4dRenderList();
  });
  document.querySelectorAll('[data-p4dcond]').forEach(el => el.onclick = e => {
    if (e.target.tagName === 'INPUT') return;
    p4dGrab(); P4D_FORM.f.cond = el.dataset.p4dcond; p4dRenderList();
  });
  $('#p4dfCancel').onclick = () => { P4D_FORM = null; p4dRenderList(); };
  $('#p4dfSave').onclick = () => {
    if ($('#p4dfSave').classList.contains('disabled')) return;
    p4dGrab();
    const F = P4D_FORM, f = F.f, err = {};
    const name = String(f.name).trim();
    if (DEPOSITS.some(x => x.name.trim() === name && !(F.mode === 'edit' && x.id === F.id))) err.name = '此名稱已被使用';
    const pos = v => /^\d+$/.test(String(v).trim()) && +v >= 1;
    if (f.cond === 'people' && !(pos(f.minPeople) && pos(f.perPerson))) err.people = 1;
    if (f.cond === 'fixed' && !pos(f.fixed)) err.fixed = 1;
    if (Object.keys(err).length){ F.err = err; p4dRenderList(); return; }
    const rec = { name, way: f.way, cond: f.cond, minPeople: +f.minPeople, perPerson: +f.perPerson, fixed: +f.fixed };
    rec.desc = p4dDesc(rec);
    if (F.mode === 'edit'){
      const d = DEPOSITS.find(x => x.id === F.id); Object.assign(d, rec);
      p4dToast('已儲存變更');
    } else {
      let i = DEPOSITS.length + 1; while (DEPOSITS.some(x => x.id === 'd' + i)) i++;
      DEPOSITS.push(Object.assign({ id: 'd' + i }, rec));
      p4dToast('已新增訂金規則');
    }
    P4D_FORM = null; p4dRenderList();
  };
}

function p4dDelete(d){
  if (!d) return;
  openModal(`
    <div class="p4d-modal" style="display:flex;flex-direction:column;gap:16px">
      <h3>確定刪除嗎？</h3>
      <div class="p4d-mbody">刪除後，已套用此規則的預約時段將不再收取訂金，但不影響已建立的預約。確定刪除「${esc(d.name)}」嗎？</div>
      <div class="btn-row">
        <button class="btn-md ghost" id="p4dDelCancel">取消</button>
        <button class="btn-md p4d-danger" id="p4dDelOk">刪除</button>
      </div>
    </div>`);
  $('#p4dDelCancel').onclick = closeModal;
  $('#p4dDelOk').onclick = () => {
    const i = DEPOSITS.findIndex(x => x.id === d.id);
    if (i >= 0) DEPOSITS.splice(i, 1);
    ['slots', 'svcSlots', 'catSlots', 'capSlots'].forEach(k => (db[k] || []).forEach(s => { if (s.deposit === d.id) s.deposit = null; }));
    persist(); closeModal(); p4dToast('已刪除訂金規則'); p4dRenderList();
  };
}

/* ── 1-1 註冊藍新企業會員（長表單） ─────────────────────── */
const P4D_SEL_CITY = ['Taipei City (台北市)', 'New Taipei City (新北市)', 'Taoyuan City (桃園市)', 'Taichung City (台中市)', 'Tainan City (台南市)', 'Kaohsiung City (高雄市)'];
const P4D_SEL_COUNTY = ['台北市', '新北市', '桃園市', '台中市', '台南市', '高雄市'];
const P4D_SEL_DIST = ['大同區', '中山區', '中正區', '萬華區', '大安區'];
const P4D_SEL_IDPLACE = ['北市', '新北市', '桃市', '中市', '南市', '高市', '基市'];
const P4D_SEL_REISSUE = ['初發', '補發', '換發'];
const P4D_SEL_SHOPCAT = ['網路商店', '實體商店', '網路與實體商店'];
const P4D_SEL_SALECAT = ['服務', '商品', '虛擬商品'];
const P4D_SEL_TRADE = ['5812–餐廳', '5813–酒吧', '5814–速食店'];

function p4dRegView(){
  setTitle([['訂金管理', '#/p4deposit'], ['註冊藍新企業會員', '']], '註冊藍新企業會員');
  const F = (id, label, ph, hint) => `
    <div class="field"><span class="field-label">${label}</span>
      <div class="input" data-in="${id}"><input id="${id}" placeholder="${esc(ph)}"></div>
      ${hint ? `<span class="hint" data-hint="${id}">${hint}</span>` : ''}
      <span class="p4d-err" data-err="${id}"></span></div>`;
  const SEL = (id, label, opts, hint) => `
    <div class="field"><span class="field-label">${label}</span>
      <select class="sel" id="${id}"><option value="">請選擇</option>${opts.map(o => `<option>${o}</option>`).join('')}</select>
      ${hint ? `<span class="hint">${hint}</span>` : ''}
      <span class="p4d-err" data-err="${id}"></span></div>`;
  $('#content').innerHTML = `
    <div class="card p4d-regsec">
      <div class="p4d-formtitle">建立藍新金流會員帳號</div>
      ${F('rAcct', '管理者帳號', '請輸入自訂帳號', '英數混合、最長請勿超過20個字元。可接受「_」「.」「@」三種符號')}
    </div>
    <div class="card p4d-regsec">
      <div class="p4d-formtitle">藍新金流帳號管理者聯絡資訊</div>
      ${F('rCName', '管理者中文姓名', '若無中文姓名，請直接輸入英文姓名')}
      ${F('rEName', '管理者英文姓名', 'First Name,Last Name (e.g., Xiao ming, Wang)')}
      ${F('rPhone', '管理者行動電話號碼', '請輸入手機號碼，如：0912345678')}
      ${F('rMail', '管理者email', '請輸入管理者聯絡信箱')}
    </div>
    <div class="card p4d-regsec">
      <div class="p4d-formtitle">企業登記資料</div>
      ${F('rCoName', '企業名稱（會員名稱）', '請提供與經濟部公司登記所記載相同之企業名稱')}
      ${F('rTaxId', '統一編號（會員證號）', '請提供與經濟部公司登記所記載相同之統一編號')}
      ${F('rRepName', '企業代表人中文姓名', '請輸入姓名')}
      <div class="field"><span class="field-label">企業代表人身分</span>
        <div class="p4d-radrow">
          ${['本國籍', '外國籍', '外國籍（無居留證者）'].map((n, i) => `<label class="check" data-p4nat="${i}">
            <span class="radio p4-radio"${i === 0 ? ' data-on' : ''}></span><span class="ck-label" style="font-weight:400">${n}</span></label>`).join('')}
        </div></div>
      ${F('rRepId', '企業代表人身分證字號', '請輸入身分證字號')}
      ${F('rIdDate', '發證日期', '請輸入民國年份，如：0950101')}
      ${SEL('rIdPlace', '身分證發證地點', P4D_SEL_IDPLACE)}
      ${SEL('rIdReissue', '身分證領補換', P4D_SEL_REISSUE)}
      ${F('rBirth', '企業代表人出生年月日', 'YYYYMMDD，如：19900101')}
      ${F('rCapital', '實收資本額', '請輸入數字')}
      ${F('rFound', '核准設立日期', 'YYYYMMDD，如：19900101')}
      ${F('rCoAddr', '公司登記地址', '請輸入公司登記地址')}
      ${F('rCoAddr2', '公司聯絡地址（會員聯絡地址）', '請輸入公司聯絡地址')}
      ${F('rCoTel', '公司電話（會員電話）', '如：0x–000111或09xx–000111')}
    </div>
    <div class="card p4d-regsec">
      <div class="p4d-formtitle">開立藍新商店資訊</div>
      ${F('rShopCn', '商店中文名稱', '請輸入商店中文名稱')}
      ${F('rShopEn', '商店英文名稱', '請輸入商店英文名稱')}
      <div class="field"><span class="field-label">商店登記營業地</span>
        <div style="display:flex;gap:10px;flex-wrap:wrap">
          <div class="input disabled" style="width:110px"><input value="Taiwan" disabled></div>
          <select class="sel" id="rShopCity" style="width:240px"><option value="">城市</option>${P4D_SEL_CITY.map(o => `<option>${o}</option>`).join('')}</select>
        </div></div>
      <div class="field"><span class="field-label">商店聯絡地址</span>
        <div style="display:flex;gap:10px;flex-wrap:wrap">
          <select class="sel" id="rAddrCounty" style="width:110px"><option value="">縣市</option>${P4D_SEL_COUNTY.map(o => `<option>${o}</option>`).join('')}</select>
          <select class="sel" id="rAddrDist" style="width:120px"><option value="">行政區</option>${P4D_SEL_DIST.map(o => `<option>${o}</option>`).join('')}</select>
          <div class="input disabled" style="width:110px"><input id="rAddrZip" placeholder="郵遞區號" disabled></div>
        </div>
        <span class="p4d-err" data-err="rAddrCounty">此為必填欄位</span>
        <div class="input"><input id="rAddrRest" placeholder="請輸入地址"></div></div>
      ${F('rShopEnAddr', '商店英文聯絡地址', '請輸入商店英文聯絡地址')}
      ${SEL('rShopCat', '商店類別', P4D_SEL_SHOPCAT)}
      ${SEL('rSaleCat', '販售類別', P4D_SEL_SALECAT)}
      ${SEL('rTrade', '行業別', P4D_SEL_TRADE)}
      <div class="field"><span class="field-label">商店簡介</span>
        <textarea class="p4d-ta" id="rIntro" placeholder="請填寫商店簡介，字數為255字以內"></textarea></div>
      ${F('rDispMail', '商店爭議款信箱', '請輸入當發生爭議款項時，藍新專員可連絡您的聯絡信箱')}
      ${F('rCsMail', '商店客服信箱', '可帶入多組信箱，請用「,」分隔，如：test@YYY.com,test2@YYY.com')}
    </div>
    <div class="card p4d-regsec">
      <div class="p4d-formtitle">連結帳戶資訊</div>
      ${F('rBankCode', '金融機構代碼', '請輸入金融機構代碼')}
      ${F('rBranch', '分行代碼', '請輸入分行代碼')}
      <div class="field"><span class="field-label">帳戶戶名</span>
        <div class="input disabled"><input id="rAcctName" disabled></div>
        <span class="hint">帳戶名與企業名稱（會員名稱）需一致，故系統將自動帶入企業名稱以進行身分驗證，請確認名稱是否正確</span></div>
      ${F('rBankAcct', '帳號帳戶', '請輸入帳號帳戶')}
      <div class="p4d-notes" style="margin-top:2px"><div class="nt">注意事項</div><ul>
        <li>此帳戶需經過身分驗證，請務必提供企業帳戶，並請勿填寫與戶名不符的帳戶資料。</li>
        <li>驗證作業約需五個工作天。</li>
      </ul></div>
    </div>
    <div class="card">
      <div class="btn-row">
        <button class="btn-md ghost" id="rCancel">取消</button>
        <button class="btn-md primary" id="rSubmit">註冊</button>
      </div>
    </div>
    <div class="p4d-demo">原型展示：<a id="rFill">填入範例資料</a></div>`;
  document.querySelectorAll('[data-p4nat]').forEach(el => el.onclick = () => {
    document.querySelectorAll('[data-p4nat] .p4-radio').forEach(r => r.removeAttribute('data-on'));
    el.querySelector('.p4-radio').setAttribute('data-on', '');
  });
  $('#rCoName').addEventListener('input', e => { $('#rAcctName').value = e.target.value; });
  $('#rAddrDist').addEventListener('change', e => { $('#rAddrZip').value = e.target.value ? '103' : ''; });
  $('#rCancel').onclick = () => { location.hash = '#/p4deposit'; };
  $('#rFill').onclick = () => {
    const set = (id, v) => { const el = document.getElementById(id); el.value = v; el.dispatchEvent(new Event('input')); el.dispatchEvent(new Event('change')); };
    set('rAcct', 'menushop52'); set('rCName', '楊攸凱'); set('rEName', 'Yo Kai,Yang');
    set('rPhone', '0912345678'); set('rMail', 'kai@mail.com');
    set('rCoName', '找活股份有限公司'); set('rTaxId', '24661780'); set('rRepName', '楊攸凱');
    set('rRepId', 'A123456789'); set('rIdDate', '0950101'); set('rIdPlace', '北市'); set('rIdReissue', '換發');
    set('rBirth', '19870422'); set('rCapital', '99999999'); set('rFound', '20080916');
    set('rCoAddr', '台北市大同區延平北路一段92號'); set('rCoAddr2', '台北市大同區延平北路一段92號'); set('rCoTel', '02-25581234');
    set('rShopCn', 'MENU店+'); set('rShopEn', 'MENU Shop'); set('rShopCity', 'Taipei City (台北市)');
    set('rAddrCounty', '台北市'); set('rAddrDist', '大同區'); set('rAddrRest', '延平北路一段92號');
    set('rShopEnAddr', 'No. 92, Sec. 1, Yanping N. Rd., Datong Dist., Taipei City 103012, Taiwan');
    set('rShopCat', '網路商店'); set('rSaleCat', '服務'); set('rTrade', '5812–餐廳');
    set('rIntro', '商店簡介內容'); set('rDispMail', 'kai@mail.com'); set('rCsMail', 'test@YYY.com,test2@YYY.com');
    set('rBankCode', '013'); set('rBranch', '262'); set('rBankAcct', '00012345678900');
    p4dToast('已填入範例資料');
  };
  $('#rSubmit').onclick = () => {
    const val = id => document.getElementById(id).value.trim();
    const mark = (id, msg) => {
      const box = document.querySelector(`[data-in="${id}"]`) || document.getElementById(id);
      if (box) box.classList.add('p4d-bad');
      const err = document.querySelector(`[data-err="${id}"]`);
      if (err){ if (msg) err.textContent = msg; err.classList.add('show'); }
      const hint = document.querySelector(`[data-hint="${id}"]`);
      if (!msg && hint) hint.classList.add('p4d-bad');
      bad = true;
    };
    document.querySelectorAll('.p4d-bad').forEach(el => el.classList.remove('p4d-bad'));
    document.querySelectorAll('.p4d-err.show').forEach(el => el.classList.remove('show'));
    let bad = false;
    if (!/^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d_.@]{1,20}$/.test(val('rAcct'))) mark('rAcct', '');
    if (!val('rCName')) mark('rCName', '此為必填欄位');
    if (!/^09\d{8}$/.test(val('rPhone'))) mark('rPhone', '請輸入正確的手機號碼');
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val('rMail'))) mark('rMail', '信箱格式錯誤');
    if (!val('rIdPlace')) mark('rIdPlace', '此為必填欄位');
    if (!/^0\d{1,2}[-–]\d{6,8}$/.test(val('rCoTel'))) mark('rCoTel', '請依格式輸入，如：0x–000111 或 09xx–000111');
    if (!val('rAddrCounty')) mark('rAddrCounty');
    if (bad){ p4dToast('表單未正確填寫', 'err'); window.scrollTo({ top: 0, behavior: 'smooth' }); return; }
    p4dSetReg('new'); location.hash = '#/p4deposit';
  };
}
"""

PATCHES = [
    ("  if (h === '#/p4auto') return p4ViewAuto();\n  if (h === '#/p4auto1') return p4v1View();",
     "  if (h === '#/p4auto') return p4cView();"),
    ("const activeNav = (h === '#/p4auto' || h === '#/p4auto1') ? '自動排位規則'",
     "const activeNav = (h === '#/p4auto') ? '自動排位規則'"),
    # 時間軸工具列加入「管理預約單位開放」off 圖示（Figma 的入口）
    ('<button class="ico" title="匯出"',
     '<button class="ico" title="管理預約單位開放" id="p4fEnter">${P4F_ICON}</button>\n'
     '          <button class="ico" title="匯出"'),
    # 訂金管理：加註冊藍新長表單的路由（新頁）
    ("  if (h === '#/p4deposit') return p4ViewDeposit();",
     "  if (h === '#/p4deposit/register') return p4dRegView();\n  if (h === '#/p4deposit') return p4ViewDeposit();"),
    # 側欄高亮：註冊頁也要亮「訂金管理」
    ("h === '#/p4deposit' ? '訂金管理'",
     "h.startsWith('#/p4deposit') ? '訂金管理'"),
    # DEPOSITS 種子改成定稿的兩筆（id 不變，時段規則表單讀 name/desc 同步不受影響）
    ("""const DEPOSITS = [
  { id: 'd1', name: '平日', desc: '預先收款：2人以上，每人200元' },
  { id: 'd2', name: '例假日限定', desc: '信用卡授權綁定：每組300元' },
  { id: 'd3', name: '訂金規則A', desc: '預先收款：2人以上，每人100元' },
];""",
     """const DEPOSITS = [
  { id: 'd1', name: '週末晚上', desc: '預先收款：2人以上，每人200元', way: 'prepay', cond: 'people', minPeople: 2, perPerson: 200, fixed: 200 },
  { id: 'd2', name: '特殊節日', desc: '信用卡授權綁定：每組300元', way: 'auth', cond: 'fixed', minPeople: 1, perPerson: 200, fixed: 300 },
];"""),
]


def cut_block(html: str, start: str, end: str) -> str:
    i = html.index(start)
    j = html.index(end)
    if not (i < j):
        sys.exit(f"區塊順序不符：{start[:40]}…")
    return html[:i] + html[j:]


def main():
    html = SRC.read_text(encoding="utf-8")
    for m in (V2_START, V1_START, DEP_START):
        if html.count(m) != 1:
            sys.exit(f"找不到唯一標記：{m}")
    html = cut_block(html, V1_START, DEP_START)   # 先砍後面的 v1，再砍 v2，位移才不會互相影響
    html = cut_block(html, V2_START, DEP_START)
    # 臨時關閉：整段換成 Figma 定稿版（方案 C 移除）
    if html.count(CLOSE_START) != 1:
        sys.exit(f"找不到唯一標記：{CLOSE_START}")
    i = html.index(CLOSE_START)
    j = html.index(CLOSE_END, i)
    html = html[:i] + P4F_JS + "\n" + html[j:]
    for old, new in PATCHES:
        if html.count(old) != 1:
            sys.exit(f"注入點不唯一或找不到（count={html.count(old)}）：\n{old[:120]}…")
        html = html.replace(old, new)
    html = html.replace(DEP_START, V3_JS + "\n" + DEP_START, 1)
    # 訂金管理：timeline 版提案頁整段換成 2026 Aug Figma 定稿版
    if html.count(DEP_START) != 1:
        sys.exit(f"找不到唯一標記：{DEP_START}")
    i = html.index(DEP_START)
    j = html.index(DEP_END, i)
    html = html[:i] + DEP2_JS + "\n" + html[j:]
    if "<title>" in html:
        html = html.replace("<title>", "<title>Part4 整合版（自訂排位順序）｜", 1)
    OUT.write_text(html, encoding="utf-8")
    print(f"OK → {OUT}  ({OUT.stat().st_size:,} bytes)")
    for sym in ("p4ViewAuto", "p4v1View", "p4AutoSwitcher", "#/p4auto1", "#/p4auto2", "p4OpenDrawer", "p4ModeBar", "臨時關閉模式",
                "p4NormalizeDeposits", "p4DepForm", "p4DepDelete", "p4RenderDepList", "p4DepSw", "訂金預約模式"):
        if sym in html:
            print(f"⚠️ 產出檔仍殘留 {sym}")


if __name__ == "__main__":
    main()
