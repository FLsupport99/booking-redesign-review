#!/usr/bin/env python3
"""從 Part 3 定稿的後台模擬器 sim.html 產生 Part4 v2「自動排位規則」原型 part4_auto.html。

原則同 build_part4_timeline.py／build_part4_exception.py：
定稿頁 100% 不動，只「注入」——本腳本注入的是改版後的「自動排位規則」設定頁，
把現行的「一份全域排序」升級成「人數級距 × 各自一套規則」：
每個級距各有一份完整排序（群組順序 ＋ 群組內單位順序）＋ 該段的併桌上限。

頁面內建「排位模擬器」，輸入人數即可看到候選組合與逐步判斷過程。
資料存獨立 sessionStorage key（p4auto_v2），與 sim.html／part4_timeline.html 互不干擾——
因為本頁需要一組容量更有變化的示範資料（吧台／大桌／包廂），沿用 sim_v4 會看不出級距差異。

2026-08-10：原本另有「方案 B：每個級距只選一個主策略」並陳供 review，Ian 已裁定採本案，
B 整案收掉。B 的便利性保留在每段上方的「快速排序」按鈕——那本來就只是幫店家排出一種順序。

sim.html 更新時重跑本腳本即可同步。
"""
import pathlib
import sys

root = pathlib.Path(__file__).resolve().parent.parent
BASE = (root / "sim.html").read_text(encoding="utf-8")


def inject(hay, anchor, addition, before=True, label=""):
    if hay.count(anchor) != 1:
        sys.exit(f"錨點不唯一或不存在（{label}）：{anchor[:60]!r} count={hay.count(anchor)}")
    return hay.replace(anchor, (addition + anchor) if before else (anchor + addition))


def replace_once(hay, old, new, label=""):
    if hay.count(old) != 1:
        sys.exit(f"錨點不唯一或不存在（{label}）：{old[:60]!r} count={hay.count(old)}")
    return hay.replace(old, new, 1)


# ══════════════════════════════════════════════════════════════════
# 1) CSS
# ══════════════════════════════════════════════════════════════════
CSS = """
/* ===== Part4 v2 注入：自動排位規則（人數級距） ===== */
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
"""


# ══════════════════════════════════════════════════════════════════
# 2) 示範資料：在既有 6 個單位之外補上吧台／大桌／包廂
#    （既有 u1~u6 完全保留，範例預約才不會指到不存在的單位）
# ══════════════════════════════════════════════════════════════════
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


# ══════════════════════════════════════════════════════════════════
# 3) 自動排位規則頁（JS）
# ══════════════════════════════════════════════════════════════════
PAGE_JS = r"""/* ===== Part4 v2 注入：自動排位規則（人數級距） =====
   由 tools/build_part4_auto.py 從 sim.html 產生。 */
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
  $('#content').innerHTML = `
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
"""

def build():
    src = BASE

    # 1) CSS
    src = inject(src, "</style>", CSS, label="css")

    # 2) 獨立 sessionStorage key（示範資料不同，不能與 sim.html 共用）
    src = replace_once(src, "const DB_KEY = 'sim_v4';",
                       "const DB_KEY = 'p4auto_v2';", label="dbkey")

    # 3) 示範資料：補吧台／大桌／包廂
    src = replace_once(src, SEED_GROUPS_OLD, SEED_GROUPS_NEW, label="seed")

    # 4) 自動排位規則頁
    src = inject(src, "/* =====================================================\n   預約規則 landing（入口示意）",
                 PAGE_JS + "\n", label="page")

    # 5) 路由
    src = inject(src, "  if (h === '#/rules' || h === '') return viewRules();",
                 "  if (h === '#/p4auto') return p4ViewAuto();\n", label="routes")

    # 6) 側欄導向
    src = inject(src, "    else if (a.dataset.nav === '顧客預約頁') { location.hash = '#/customer'; }",
                 "\n    else if (a.dataset.nav === '自動排位規則') { location.hash = '#/p4auto'; }",
                 before=False, label="nav")

    # 7) 側欄高亮
    src = replace_once(src,
                       "  const activeNav = h.startsWith('#/customer') ? '顧客預約頁' : '預約規則';",
                       "  const activeNav = h === '#/p4auto' ? '自動排位規則'\n"
                       "    : h.startsWith('#/customer') ? '顧客預約頁' : '預約規則';", label="activeNav")

    # 8) 標題與檔頭註記
    src = replace_once(src, "<title>MENU店+ 後台模擬器</title>",
                       "<title>Part4 自動排位規則｜MENU店+ 後台模擬器</title>", label="title")
    src = replace_once(src, "<!-- MENU店+ 後台模擬器 · 假資料互動 Demo · 維護：FindLife Support -->",
                       "<!-- Part4 自動排位規則：由 tools/build_part4_auto.py 從 sim.html 產生，請勿直接編輯 -->",
                       label="comment")

    out = root / "part4_auto.html"
    out.write_text(src, encoding="utf-8")
    print(f"{out.name} 已產生：{len(src)} chars")


build()
