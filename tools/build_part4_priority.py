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

作法沿用 Part 4 慣例：以整合版定稿 part4_timeline.html 為基底注入；訂金管理不動。
用法：python3 tools/build_part4_priority.py
"""
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "part4_timeline.html"
OUT = ROOT / "part4_priority.html"

V2_START = "/* ===== Part4 v2 注入：自動排位規則（人數級距） ====="
V1_START = "/* ===== Part4 注入：自動排位規則 v1（2026-08-06 初版，單純照組別排序） ====="
DEP_START = "/* ===== Part4 注入：訂金管理（US4-2） ====="
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

PATCHES = [
    ("  if (h === '#/p4auto') return p4ViewAuto();\n  if (h === '#/p4auto1') return p4v1View();",
     "  if (h === '#/p4auto') return p4cView();"),
    ("const activeNav = (h === '#/p4auto' || h === '#/p4auto1') ? '自動排位規則'",
     "const activeNav = (h === '#/p4auto') ? '自動排位規則'"),
    # 時間軸工具列加入「管理預約單位開放」off 圖示（Figma 的入口）
    ('<button class="ico" title="匯出"',
     '<button class="ico" title="管理預約單位開放" id="p4fEnter">${P4F_ICON}</button>\n'
     '          <button class="ico" title="匯出"'),
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
    if "<title>" in html:
        html = html.replace("<title>", "<title>Part4 整合版（自訂排位順序）｜", 1)
    OUT.write_text(html, encoding="utf-8")
    print(f"OK → {OUT}  ({OUT.stat().st_size:,} bytes)")
    for sym in ("p4ViewAuto", "p4v1View", "p4AutoSwitcher", "#/p4auto1", "#/p4auto2", "p4OpenDrawer", "p4ModeBar", "臨時關閉模式"):
        if sym in html:
            print(f"⚠️ 產出檔仍殘留 {sym}")


if __name__ == "__main__":
    main()
