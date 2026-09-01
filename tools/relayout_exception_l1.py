#!/usr/bin/env python3
"""把 exception_rules.html 的 L1 重刻成 Figma ④ 例外預約規則 定稿版。

對齊來源：Figma AO8eUsYE6NQuELdiqGrG9E canvas `4245:51499`
  7-1 主畫面 4259:68068｜_展開 4627:72935｜_Null 4627:73837｜_整日關閉 4627:74115
  7-1 查看預約單位 4627:75358｜7-2 關閉預約（年曆子頁）4627:71195

只動 L1（頁首文案、總覽區、月曆、該日詳情、關閉預約流程），L2「新增/編輯例外規則」
表單完全不動。這支是一次性的重排腳本，跑完後 exception_rules.html 即為新版；
保留在 repo 供對照當初改了哪些區塊。
"""
import pathlib
import re
import sys

root = pathlib.Path(__file__).resolve().parent.parent
p = root / "src" / "exception_rules.html"
src = p.read_text(encoding="utf-8")


def sub1(pattern, repl, label, flags=re.S):
    global src
    new, n = re.subn(pattern, lambda m: repl, src, count=1, flags=flags)
    if n != 1:
        sys.exit(f"❌ {label}：命中 {n} 次")
    src = new


def rep1(old, new, label):
    global src
    if src.count(old) != 1:
        sys.exit(f"❌ {label}：命中 {src.count(old)} 次")
    src = src.replace(old, new, 1)


# ── 1) CSS：定稿的月曆格、accordion 規則卡、年曆子頁 ────────────────
rep1("</style>", """
/* ===== 2026-08-09 對齊 Figma 定稿（④ 例外預約規則）新增 ===== */
.sec-bar{display:flex;align-items:center;gap:10px;margin-bottom:14px}
.sec-bar .t{font-size:18px;line-height:24px;font-weight:500;flex:1}
.cal-head2{display:flex;align-items:center;gap:8px;padding:4px 2px 14px}
.cal-head2 .ym{font-size:18px;line-height:24px;font-weight:500;font-variant-numeric:tabular-nums}
.cal-head2 .sp{flex:1}
.cal2{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));border:1px solid var(--border-card);border-radius:8px;overflow:hidden}
.cal2 .wd{font-size:12px;line-height:16px;color:var(--text-body);text-align:center;padding:9px 0;border-bottom:1px solid var(--border-card);background:#fff}
.cal2 .cell{min-height:72px;padding:8px 10px;border-right:1px solid var(--border-card);border-bottom:1px solid var(--border-card);
  background:#fff;cursor:pointer;display:flex;flex-direction:column;align-items:flex-start;gap:6px;position:relative}
.cal2 .cell:nth-child(7n+7){border-right:0}
.cal2 .cell.out{color:var(--text-disabled);cursor:default;background:#fff}
.cal2 .cell .d{font-size:14px;line-height:20px;font-weight:500;font-variant-numeric:tabular-nums}
.cal2 .cell.out .d{font-weight:400;color:var(--text-disabled)}
.cal2 .cell.today .d{background:var(--primary);color:#fff;border-radius:50%;width:24px;height:24px;display:flex;align-items:center;justify-content:center}
.cal2 .cell.sel{background:var(--primary-l3);box-shadow:inset 0 0 0 1.5px var(--primary)}
.cal2 .cell.closed{background:#f5f5f5}
.cal2 .cell.closed .d{color:var(--text-muted)}
.cal2 .closed-mark{display:flex;flex-direction:column;align-items:center;gap:2px;align-self:center;color:var(--text-disabled)}
.cal2 .closed-mark svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.6}
.cal2 .closed-mark span{font-size:11px;letter-spacing:.5px}
.cal2 .exc-mark{color:var(--emphasis-d)}
.cal2 .exc-mark svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.8}
.legend2{display:flex;align-items:center;gap:6px;padding-top:12px;font-size:13px;color:var(--emphasis-d)}
.legend2 svg{width:16px;height:16px;fill:none;stroke:currentColor;stroke-width:1.8}
.day-head{display:flex;align-items:center;gap:12px;font-size:16px;line-height:24px;font-weight:500;margin:26px 0 14px}
.day-head .bar{color:var(--border-field)}
.rule-card{border:1px solid var(--border-card);border-radius:10px;background:#fff;margin-bottom:12px;overflow:hidden}
.rule-card .rh{display:flex;align-items:center;gap:10px;padding:14px 16px}
.rule-card .caret{width:24px;height:24px;border-radius:50%;border:1px solid var(--border-field);display:flex;align-items:center;justify-content:center;cursor:pointer;flex:none;background:#fff}
.rule-card .caret svg{width:12px;height:12px;fill:none;stroke:var(--icon-muted);stroke-width:2;transition:transform .15s}
.rule-card.open .caret svg{transform:rotate(180deg)}
.rule-card .nm{font-size:16px;line-height:24px;font-weight:500;white-space:nowrap}
.rule-card .tchips{display:flex;gap:6px;flex-wrap:wrap;flex:1;min-width:0}
.rule-card .tchip{border:1px solid var(--border-field);border-radius:6px;padding:3px 10px;font-size:13px;line-height:19px;font-variant-numeric:tabular-nums;color:var(--text-strong);background:#fff}
.rule-card .applied{font-size:12px;line-height:18px;color:var(--text-muted);white-space:nowrap}
.rule-card .flags{display:flex;align-items:center;gap:8px}
.rule-card .flags .ic{width:18px;height:18px;display:flex}
.rule-card .flags .ic svg{width:18px;height:18px}
.tag-nounit{font-size:10px;line-height:16px;padding:2px 8px;border-radius:4px;border:1px solid var(--alert);color:var(--alert);white-space:nowrap}
.rule-card .acts{display:flex;align-items:center;gap:4px;padding-left:12px;border-left:1px solid var(--border-card)}
.rule-card .bd{display:none;grid-template-columns:1fr 1fr;gap:24px;padding:0 16px 18px 50px}
.rule-card.open .bd{display:grid}
.rule-card .bd .col+.col{border-left:1px dashed var(--border-card);padding-left:24px}
.rb-h{display:flex;align-items:center;gap:6px;font-size:12px;line-height:18px;color:var(--text-muted);margin:6px 0 8px}
.rb-h svg{width:14px;height:14px;fill:none;stroke:currentColor;stroke-width:1.6}
.rb-yr{display:flex;align-items:flex-start;gap:10px;margin-bottom:8px}
.rb-yr .y{font-size:12px;line-height:26px;color:var(--text-muted);width:34px;flex:none;font-variant-numeric:tabular-nums}
.rb-yr .ds{display:flex;gap:6px;flex-wrap:wrap}
.rb-li{font-size:14px;line-height:22px;color:var(--text-body);display:flex;align-items:flex-start;gap:8px;margin-bottom:4px}
.rb-li>svg{width:16px;height:16px;margin-top:3px;flex:none;fill:none;stroke:var(--icon-muted);stroke-width:1.6}
.rb-li .sub{font-size:12px;color:var(--text-muted)}
.rb-dot{list-style:disc;margin-left:18px;font-size:14px;line-height:22px;color:var(--text-body)}
.link-view{background:none;border:0;color:var(--primary-dark);font-size:12px;text-decoration:underline;cursor:pointer;padding:0}
.day-empty{border:1px solid var(--border-card);border-radius:10px;background:#fff;padding:34px;text-align:center;font-size:16px;font-weight:500;color:var(--text-muted)}
/* 關閉預約日子頁（年曆） */
.crumb2{display:flex;align-items:center;gap:8px;font-size:14px;color:var(--text-muted);margin-bottom:22px}
.crumb2 a{color:var(--text-body);cursor:pointer}
.crumb2 b{color:var(--text-strong);font-weight:500}
.yr-head{display:flex;align-items:center;gap:8px;padding:2px 2px 14px}
.yr-head .y{font-size:18px;font-weight:500;font-variant-numeric:tabular-nums}
.yr-head .sp{flex:1}
.yr-head .lg{font-size:12px;color:var(--text-body);display:flex;align-items:center;gap:6px}
.yr-head .lg i{width:8px;height:8px;border-radius:50%;background:var(--primary);display:inline-block}
.yr-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}
@media(max-width:900px){.yr-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
.mini{border:1px solid var(--border-card);border-radius:8px;padding:12px}
.mini .mh{text-align:center;font-size:13px;color:var(--text-body);padding-bottom:8px}
.mini .mg{display:grid;grid-template-columns:repeat(7,1fr);gap:2px}
.mini .mg span{font-size:10px;color:var(--text-muted);text-align:center;line-height:18px}
.mini .mg button{border:0;background:none;font-size:12px;line-height:24px;height:24px;border-radius:50%;cursor:pointer;color:var(--text-strong);font-variant-numeric:tabular-nums;padding:0}
.mini .mg button.out{color:var(--text-disabled);cursor:default}
.mini .mg button.on{background:var(--primary);color:#fff}
.units-modal .ug{display:flex;flex-direction:column;gap:14px;max-height:420px;overflow:auto}
.units-modal .gh{display:flex;align-items:center;gap:8px;font-size:16px;font-weight:500;cursor:pointer}
.units-modal .gh svg{width:20px;height:20px;fill:none;stroke:var(--icon-muted);stroke-width:2;transition:transform .15s}
.units-modal .gh.open svg{transform:rotate(180deg)}
.units-modal .uu{display:none;gap:8px;flex-wrap:wrap;padding-left:28px}
.units-modal .gh.open+.uu{display:flex}
.units-modal .uu span{border:1px solid var(--border-field);border-radius:6px;padding:3px 10px;font-size:14px;color:var(--text-body)}
</style>""", "css")

# ── 2) L1 標記重排 ──────────────────────────────────────────────────
old_l1_start = """      <div class="page-title">
        <div>
          <h1>例外預約規則</h1>
          <p>針對特定日期（例如節日、特殊活動）設定例外預約規則，例如不同的開放時段、設定不可預約、或是調整訂金。優先級高於一般預約規則。</p>
        </div>
        <hr class="divider" />
      </div>"""
new_l1_start = """      <div class="page-title">
        <div>
          <h1>例外預約規則</h1>
          <p>您可以針對特定日期關閉線上預約，或設定例外的預約時段與規則。</p>
        </div>
        <hr class="divider" />
      </div>"""
rep1(old_l1_start, new_l1_start, "page-title")

old_body = src[src.index('        <!-- 月曆 -->'):src.index('      </div>\n    </div>\n\n    <!-- ====== L2 view ====== -->')]
new_body = """        <!-- 例外預約規則總覽 -->
        <div class="section">
          <div class="sec-bar">
            <span class="t">例外預約規則總覽</span>
            <button class="btn-md ghost-red" id="blockBtn">
              <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M6 6l12 12"/></svg>關閉預約
            </button>
            <button class="btn-md primary" id="addBtn">
              <svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>例外規則
            </button>
          </div>
          <div class="card">
            <div class="cal-head2">
              <button class="nav-btn" id="prevMonth"><svg viewBox="0 0 8 12" width="7" height="10"><path d="M7 1L2 6l5 5" fill="none" stroke="currentColor" stroke-width="1.6"/></svg></button>
              <span class="ym" id="monthLabel">2026-05</span>
              <button class="nav-btn" id="nextMonth"><svg viewBox="0 0 8 12" width="7" height="10"><path d="M1 1l5 5-5 5" fill="none" stroke="currentColor" stroke-width="1.6"/></svg></button>
              <span class="sp"></span>
              <button class="btn-md ghost" id="todayBtn">今天</button>
            </div>
            <div class="cal2" id="calGrid"></div>
            <div class="legend2"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v6M12 16.5v.5"/></svg>已套用例外規則</div>
          </div>
        </div>

        <!-- 該日詳情 -->
        <div class="section">
          <div class="day-head"><span>例外規則</span><span class="bar">｜</span><span id="dayTitle">2026-05-27 星期三</span></div>
          <div id="dayPanel"></div>
        </div>
"""
src = src.replace(old_body, new_body, 1)

# 舊的 blockBtnLabel 已不存在，把依賴它的程式碼改掉（見下方 renderDayPanel 重寫）

# ── 3) renderCalendar 重寫 ─────────────────────────────────────────
cal_start = src.index("function renderCalendar(){")
cal_end = src.index("/* ---------- 4. Render: Day panel ---------- */")
src = src[:cal_start] + """function renderCalendar(){
  const grid = document.getElementById('calGrid');
  const m = state.calMonth;
  document.getElementById('monthLabel').textContent =
    `${m.getFullYear()}-${String(m.getMonth()+1).padStart(2,'0')}`;
  let html = ['日','一','二','三','四','五','六'].map(w=>`<div class="wd">${w}</div>`).join('');
  const first = new Date(m.getFullYear(), m.getMonth(), 1);
  const start = new Date(first); start.setDate(start.getDate()-first.getDay());
  for (let i=0;i<42;i++){
    const d = new Date(start); d.setDate(start.getDate()+i);
    const inMonth = d.getMonth()===m.getMonth();
    const ymd = fmtDate(d);
    const bk = inMonth ? blockKind(ymd) : 'none';
    const rn = inMonth ? rulesOf(ymd).length : 0;
    const cls = ['cell'];
    if (!inMonth) cls.push('out');
    if (inMonth && fmtDate(TODAY)===ymd) cls.push('today');
    if (inMonth && state.selectedDate===ymd) cls.push('sel');
    if (bk==='all') cls.push('closed');
    html += `<div class="${cls.join(' ')}"${inMonth?` data-ymd="${ymd}"`:''}>
      <span class="d">${d.getDate()}</span>
      ${bk==='all' ? `<span class="closed-mark"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M6 6l12 12"/></svg><span>CLOSED</span></span>` : ''}
      ${bk==='partial' ? `<span class="closed-mark" title="部分服務不可預約"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M6 6l12 12"/></svg><span>部分</span></span>` : ''}
      ${rn && bk!=='all' ? `<span class="exc-mark" title="${rn} 條例外規則"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v6M12 16.5v.5"/></svg></span>` : ''}
    </div>`;
  }
  grid.innerHTML = html;
  grid.querySelectorAll('[data-ymd]').forEach(c=>c.addEventListener('click',()=>{
    state.selectedDate = c.dataset.ymd; renderAll();
  }));
}

""" + src[cal_end:]

# ── 4) renderDayPanel 重寫（accordion 規則卡） ─────────────────────
dp_start = src.index("function renderDayPanel(){")
dp_end = src.index("function escapeHtml(s){")
src = src[:dp_start] + """function renderDayPanel(){
  const date = state.selectedDate;
  const block = blockOf(date);
  const rules = rulesOf(date);
  const bk = blockKind(date);
  const w = '日一二三四五六'[ymd2d(date).getDay()];
  document.getElementById('dayTitle').textContent = `${date} 星期${w}`;

  const panel = document.getElementById('dayPanel');

  if (bk==='all'){ panel.innerHTML = `<div class="day-empty">已關閉預約</div>`; return; }
  if (!rules.length){ panel.innerHTML = `<div class="day-empty">未建立例外預約規則</div>`; return; }

  panel.innerHTML = rules.map((r,i)=>ruleCardHTML(r,i)).join('');
  panel.querySelectorAll('.caret').forEach(c=>c.addEventListener('click',()=>{
    c.closest('.rule-card').classList.toggle('open');
  }));
  panel.querySelectorAll('[data-viewunits]').forEach(b=>b.addEventListener('click',()=>openUnitsModal(b.dataset.viewunits)));
}

/* 規則卡：收合＝名稱＋時段 chips＋已套用 N 個日期＋旗標＋操作；展開＝左適用日期/預約時段、右容量與規則 */
function ruleCardHTML(r,i){
  const m = r.meta || {};
  const s = r.summary || '';
  const times = ruleTimeChips(r);
  const noUnit = m.units && m.units.mode==='none';
  const hasDeposit = !!m.deposit || /需訂金|預先收款|信用卡/.test(s);
  const hasApproval = !!m.approval || s.includes('需審核');
  const dates = (r.dates||[]).slice().sort();
  const byYear = {};
  dates.forEach(d=>{ const [y,mm,dd]=d.split('-'); (byYear[y]=byYear[y]||[]).push(`${mm}/${dd}`); });
  const dur = m.time && m.time.dur ? m.time.dur : '2小時0分鐘';
  const slotN = times.length;
  return `<div class="rule-card" data-i="${i}">
    <div class="rh">
      <span class="caret"><svg viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></svg></span>
      <span class="nm">${escapeHtml(r.name)}</span>
      <span class="tchips">${times.slice(0,4).map(t=>`<span class="tchip">${t}</span>`).join('')}${times.length>4?'<span class="tchip">⋯</span>':''}</span>
      <span class="applied">已套用${dates.length}個日期</span>
      <span class="flags">
        ${hasDeposit?`<span class="ic">${ICON_CASH}</span>`:''}
        ${hasApproval?`<span class="ic">${ICON_CHECK}</span>`:''}
        ${noUnit?'<span class="tag-nounit">尚未設定預約單位</span>':''}
      </span>
      <span class="acts">
        <button class="icon-btn" title="編輯" data-action="edit" data-id="${r.id}"><svg viewBox="0 0 24 24"><path d="M4 20l4-1 11-11-3-3L5 16z"/></svg></button>
        <button class="icon-btn" title="複製" data-action="duplicate" data-id="${r.id}"><svg viewBox="0 0 24 24"><rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V6a2 2 0 00-2-2H6a2 2 0 00-2 2v8a2 2 0 002 2h2"/></svg></button>
        <button class="icon-btn danger" title="刪除" data-action="delete" data-id="${r.id}"><svg viewBox="0 0 24 24"><path d="M5 7h14M9 7V5h6v2M7 7l1 13h8l1-13"/></svg></button>
      </span>
    </div>
    <div class="bd">
      <div class="col">
        <div class="rb-h"><svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M8 3v4M16 3v4M3 10h18"/></svg>適用日期</div>
        ${Object.keys(byYear).sort().map(y=>`<div class="rb-yr"><span class="y">${y}</span>
          <span class="ds">${byYear[y].map(d=>`<span class="tchip">${d}</span>`).join('')}</span></div>`).join('')}
        <div class="rb-h" style="margin-top:14px"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>預約時段</div>
        <ul style="margin:0;padding:0">
          <li class="rb-dot">服務時長：${escapeHtml(dur)}</li>
          <li class="rb-dot">線上預約可選時段：${slotN}個</li>
        </ul>
        <div class="ds" style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px">${times.map(t=>`<span class="tchip">${t}</span>`).join('')}</div>
      </div>
      <div class="col">
        <div class="rb-li"><svg viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="2"/><path d="M4 10h16"/></svg>
          <span>開放預約單位：${m.units && m.units.count!=null ? m.units.count : 7}個（最多可承接${m.units && m.units.cap!=null ? m.units.cap : 30}人）<br>
          <button class="link-view" data-viewunits="${escapeHtml(r.name)}">查看預約單位</button></span></div>
        <div class="rb-li"><svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="3.4"/><path d="M5 20c1.3-3 4-4.4 7-4.4s5.7 1.4 7 4.4"/></svg>
          <span>店內總人數上限：${m.limit && m.limit.people!=null ? m.limit.people : 20}人</span></div>
        <div class="rb-li"><svg viewBox="0 0 24 24"><circle cx="9" cy="8" r="3"/><circle cx="16" cy="9" r="2.4"/><path d="M3 20c1-2.6 3.3-3.9 6-3.9s5 1.3 6 3.9"/></svg>
          <span>店內總組數上限：${m.limit && m.limit.groups!=null ? m.limit.groups : 20}組</span></div>
        ${hasDeposit?`<div class="rb-li">${ICON_CASH}<span>${escapeHtml((m.deposit&&m.deposit.name)||'訂金規則名稱')}<br><span class="sub">${escapeHtml((m.deposit&&m.deposit.label)||'預先收款：2人以上，每人200元')}</span></span></div>`:''}
        ${hasApproval?`<div class="rb-li">${ICON_CHECK}<span>預約需審核</span></div>`:''}
      </div>
    </div>
  </div>`;
}

/* 從 meta / summary 取出時段 chips */
function ruleTimeChips(r){
  const m = r.meta || {};
  if (m.time && m.time.mode==='custom' && (m.time.customTimes||[]).length) return m.time.customTimes.slice();
  const s = r.summary || '';
  const mm = s.match(/(\\d{1,2}:\\d{2})\\s*[–\\-]\\s*(\\d{1,2}:\\d{2})(?:.*?間隔\\s*(\\d+)\\s*分鐘)?/);
  if (!mm) return ['09:00'];
  const step = +(mm[3]||30);
  const toM = t=>{const[a,b]=t.split(':').map(Number);return a*60+b;};
  const out=[]; for(let x=toM(mm[1]); x<=toM(mm[2]) && out.length<24; x+=step)
    out.push(String(Math.floor(x/60)).padStart(2,'0')+':'+String(x%60).padStart(2,'0'));
  return out;
}

/* 查看預約單位 Modal（Figma 4627:75358） */
const VIEW_UNITS = [
  { g:'群組 G1', us:['單位A','單位B','單位C','單位D','單位E','單位F','單位G','單位H','單位I','單位J'] },
  { g:'群組 G2', us:['單位A','單位B','單位C','單位D','單位E','單位F','單位G','單位H','單位I','單位J'] },
  { g:'群組 G3', us:['單位A','單位B','單位C','單位D','單位E','單位F','單位G','單位H','單位I','單位J','單位K','單位L','單位M'] },
  { g:'群組 G4', us:['單位A1','單位A2','單位A3','單位A4'] },
  { g:'預設群組', us:['預設A'] },
];
function openUnitsModal(ruleName){
  let el = document.getElementById('unitsModal');
  if (!el){
    el = document.createElement('div');
    el.className='modal-mask units-modal'; el.id='unitsModal';
    document.body.appendChild(el);
    el.addEventListener('click',e=>{ if(e.target===el) el.classList.remove('show'); });
  }
  el.innerHTML = `<div class="modal" style="width:640px">
    <h3 style="text-align:center;font-size:20px">${escapeHtml(ruleName)} - 開放預約單位</h3>
    <div class="ug">
      ${VIEW_UNITS.map((g,i)=>`<div>
        <div class="gh${i>=2?' open':''}"><svg viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></svg>${g.g} (${g.us.length})</div>
        <div class="uu">${g.us.map(u=>`<span>${u}</span>`).join('')}</div></div>`).join('')}
    </div>
    <button class="btn-lg primary" id="umClose" style="width:100%">關閉</button>
  </div>`;
  el.classList.add('show');
  el.querySelectorAll('.gh').forEach(h=>h.addEventListener('click',()=>h.classList.toggle('open')));
  el.querySelector('#umClose').addEventListener('click',()=>el.classList.remove('show'));
}

""" + src[dp_end:]

# ── 5) 關閉預約：改為年曆子頁（取代原本的單日 modal 流程） ──────────
rep1("""  /* E-1-a Block 按鈕：依「模式 × blockKind」四變體 */""", "  /* legacy */", "dead-comment") if "  /* E-1-a Block 按鈕：依「模式 × blockKind」四變體 */" in src else None

src = src.replace("function renderAll(){ renderCalendar(); renderDayPanel(); }",
"""function renderAll(){ renderCalendar(); renderDayPanel(); }

/* ===== 設定關閉預約日：獨立子頁（Figma 7-2 4627:71195） ===== */
let closureYear = null, closurePick = null;
/* 掛在 L1 view 內部、把原本的 page-title/content 藏起來。
   ⚠️ 選擇器一定要用 `div.view.view-l1`——body 本身就掛著 `view-l1` class
   （用來控制哪個 view 顯示），`.view-l1` 會先命中 body，整頁會被塞到底部。 */
function l1Parts(){ const r=document.querySelector('div.view.view-l1'); return [r.querySelector('.page-title'), r.querySelector('.content')]; }
function openClosurePage(){
  closureYear = ymd2d(state.selectedDate).getFullYear();
  closurePick = new Set(data().blocks.map(b=>b.date));
  l1Parts().forEach(e=>{ if(e) e.style.display='none'; });
  let v = document.getElementById('viewClosure');
  if (!v){ v = document.createElement('div'); v.id='viewClosure';
    document.querySelector('div.view.view-l1').appendChild(v); }
  v.style.display='block';
  renderClosurePage();
}
function closeClosurePage(){
  const v=document.getElementById('viewClosure'); if(v) v.style.display='none';
  l1Parts().forEach(e=>{ if(e) e.style.display=''; });
  renderAll();
}
function renderClosurePage(){
  const v = document.getElementById('viewClosure');
  v.innerHTML = `
    <div class="page-title"><div>
      <div class="crumb2"><a id="cbBack">例外預約規則</a><span>›</span><b>設定關閉預約日</b></div>
      <h1>設定關閉預約日</h1></div><hr class="divider"/></div>
    <div class="content"><div class="card">
      <div class="yr-head">
        <span class="sp"></span>
        <button class="nav-btn" id="yrPrev"><svg viewBox="0 0 8 12" width="7" height="10"><path d="M7 1L2 6l5 5" fill="none" stroke="currentColor" stroke-width="1.6"/></svg></button>
        <span class="y">${closureYear}</span>
        <button class="nav-btn" id="yrNext"><svg viewBox="0 0 8 12" width="7" height="10"><path d="M1 1l5 5-5 5" fill="none" stroke="currentColor" stroke-width="1.6"/></svg></button>
        <span class="sp"></span><span class="lg"><i></i>不可預約</span>
      </div>
      <div class="yr-grid">${Array.from({length:12},(_,i)=>miniMonth(closureYear,i)).join('')}</div>
    </div>
    <div class="card" style="margin-top:16px;display:flex;justify-content:flex-end;gap:8px">
      <button class="btn-md ghost" id="clCancel">取消</button>
      <button class="btn-md primary" id="clSave">儲存</button>
    </div></div>`;
  v.querySelector('#cbBack').onclick = closeClosurePage;
  v.querySelector('#clCancel').onclick = closeClosurePage;
  v.querySelector('#yrPrev').onclick = ()=>{ closureYear--; renderClosurePage(); };
  v.querySelector('#yrNext').onclick = ()=>{ closureYear++; renderClosurePage(); };
  v.querySelectorAll('[data-cd]').forEach(b=>b.onclick=()=>{
    const d=b.dataset.cd;
    if (closurePick.has(d)) closurePick.delete(d); else closurePick.add(d);
    renderClosurePage();
  });
  v.querySelector('#clSave').onclick = ()=>{
    const d = data();
    d.blocks = [...closurePick].sort().map(dt=>{ const ex=d.blocks.find(b=>b.date===dt); return ex||{date:dt}; });
    persistData(); closeClosurePage(); toastLike('已儲存關閉預約日');
  };
}
function miniMonth(y,m){
  const first=new Date(y,m,1), start=new Date(first); start.setDate(1-first.getDay());
  let cells='';
  for(let i=0;i<42;i++){
    const d=new Date(start); d.setDate(start.getDate()+i);
    const inM=d.getMonth()===m, ymd=fmtDate(d);
    if(!inM){ cells+=`<button class="out" disabled>${d.getDate()}</button>`; continue; }
    cells+=`<button class="${closurePick.has(ymd)?'on':''}" data-cd="${ymd}">${d.getDate()}</button>`;
  }
  return `<div class="mini"><div class="mh">${m+1}月, ${y}</div>
    <div class="mg">${['日','一','二','三','四','五','六'].map(w=>`<span>${w}</span>`).join('')}${cells}</div></div>`;
}
function toastLike(msg){
  let t=document.getElementById('p1toast');
  if(!t){ t=document.createElement('div'); t.id='p1toast'; document.body.appendChild(t);
    t.style.cssText='position:fixed;left:50%;bottom:32px;transform:translateX(-50%);background:rgba(51,51,51,.92);color:#fff;padding:10px 18px;border-radius:8px;font-size:14px;z-index:900;opacity:0;transition:opacity .2s'; }
  t.textContent=msg; t.style.opacity='1'; clearTimeout(t._h); t._h=setTimeout(()=>t.style.opacity='0',2000);
}""", 1)

# ── 6) 「關閉預約」按鈕改開年曆子頁（原本是單日 Modal 流程） ────────
rep1("  document.getElementById('blockBtn').addEventListener('click', onBlockBtnClick);",
     "  document.getElementById('blockBtn').addEventListener('click', openClosurePage);",
     "blockBtn-wiring")

p.write_text(src, encoding="utf-8")
print(f"exception_rules.html 已重排：{len(src)} chars")
