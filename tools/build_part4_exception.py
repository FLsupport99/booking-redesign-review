#!/usr/bin/env python3
"""從 Part 1 定稿版的 exception_rules.html 產生 part4_exception.html。

原則：定稿頁 100% 不動，只「注入」Part 4 的臨時預約關閉——
總覽列多一顆按鈕、月曆多一種標記＋圖例、該日詳情多一種卡片、一個新增 Modal。
資料存獨立的 sessionStorage key（p4_closures，與 part4_timeline.html 共用），
完全不碰定稿頁的資料層。exception_rules.html 更新時重跑本腳本即可同步。

⚠️ 2026-08-09：exception_rules.html 的 L1 已依 Figma ④ 例外預約規則 定稿重刻
（見 tools/relayout_exception_l1.py），本腳本的注入點也隨之改寫。
"""
import pathlib
import sys

root = pathlib.Path(__file__).resolve().parent.parent
src = (root / "exception_rules.html").read_text(encoding="utf-8")

P4_ICON = ('<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/>'
           '<path d="M12 8v4l2 1"/><path d="M5.5 5.5l13 13"/></svg>')


def inject(hay, anchor, addition, before=True, label=""):
    if hay.count(anchor) != 1:
        sys.exit(f"❌ 錨點不唯一或不存在（{label}）：{anchor[:70]!r} count={hay.count(anchor)}")
    return hay.replace(anchor, (addition + anchor) if before else (anchor + addition))


# ── 1) CSS ─────────────────────────────────────────────────────────
# 月曆標記不能沿用 .exc-mark 的橘色驚嘆號（那是「已套用例外規則」的語彙），
# 改藍色時鐘斜線，與灰 CLOSED、橘 ! 三者一眼可辨。
src = inject(src, "</style>", """
/* ===== Part4 注入：臨時預約關閉 ===== */
.cal2 .p4-mark{color:#2d6a91;display:flex;align-items:center;gap:2px;font-size:11px;font-variant-numeric:tabular-nums}
.cal2 .p4-mark svg{width:16px;height:16px;fill:none;stroke:currentColor;stroke-width:1.8}
.legend2.p4{color:#2d6a91;padding-top:6px}
.p4-card{border:1px solid #cfe0eb;border-radius:10px;background:#f7fbfd;margin-bottom:12px}
.p4-card .rh{display:flex;align-items:center;gap:10px;padding:14px 16px}
.p4-card .tag{background:#e3eef6;color:#2d6a91;font-size:12px;line-height:18px;padding:2px 10px;border-radius:999px;white-space:nowrap}
.p4-card .tm{font-size:16px;font-weight:500;font-variant-numeric:tabular-nums}
.p4-card .us{flex:1;font-size:13px;color:var(--text-body);min-width:0}
.p4-card .ov{font-size:12px;color:var(--text-muted)}
.p4-card.covered{opacity:.55}
.p4-um{display:flex;flex-direction:column;gap:6px}
.p4-um .g{font-size:12px;color:var(--text-muted);margin-top:4px}
.p4-um .row{display:flex;gap:6px;flex-wrap:wrap}
.p4-um button{border:1px solid var(--border-field);background:#fff;border-radius:6px;padding:4px 12px;font-size:13px;cursor:pointer;color:var(--text-body)}
.p4-um button.on{border-color:var(--primary);background:var(--primary-l3);color:var(--primary-dark)}
""", label="css")

# ── 2) 總覽列多一顆「臨時預約關閉」按鈕（放在關閉預約與例外規則之間） ──
src = inject(src, '            <button class="btn-md primary" id="addBtn">',
             '''<button class="btn-md ghost" id="p4ClosureBtn">
              ''' + P4_ICON + '''臨時預約關閉
            </button>
            ''', label="btn")

# ── 3) 月曆標記 ────────────────────────────────────────────────────
src = inject(src, "      ${rn && bk!=='all' ? `<span class=\"exc-mark\"",
             """      ${p4ClosuresOf(ymd).length ? `<span class="p4-mark" title="${p4ClosuresOf(ymd).length} 筆臨時預約關閉${bk==='all'?'（被整日不可預約覆蓋）':''}">""" + P4_ICON + """${p4ClosuresOf(ymd).length}</span>` : ''}
""", label="cal-mark")

# ── 4) 圖例 ────────────────────────────────────────────────────────
src = inject(src,
    '''<div class="legend2"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v6M12 16.5v.5"/></svg>已套用例外規則</div>''',
    '''\n            <div class="legend2 p4">''' + P4_ICON + '''臨時預約關閉（Part 4 新增）</div>''',
    before=False, label="legend")

# ── 5) 該日詳情：臨時關閉卡片排在最前（＝優先層級僅次於整日不可預約） ──
src = inject(src, "  if (bk==='all'){ panel.innerHTML = `<div class=\"day-empty\">已關閉預約</div>`; return; }",
    """  /* Part4 注入：整日不可預約時仍列出臨時關閉，但標明被覆蓋 */
  const p4 = p4ClosuresOf(date);
  const p4html = p4.map(c=>`<div class="p4-card${bk==='all'?' covered':''}">
      <div class="rh">
        <span class="tag">臨時關閉</span>
        <span class="tm">${c.start}–${c.end}</span>
        <span class="us">關閉單位：${c.unitIds.join('、')}　<span class="ov">僅擋線上預約，自建預約與既有預約不受影響</span></span>
        ${bk==='all'?'<span class="ov">已被整日不可預約覆蓋</span>':''}
        <button class="icon-btn danger" title="解除" data-p4del="${c.id}"><svg viewBox="0 0 24 24"><path d="M5 7h14M9 7V5h6v2M7 7l1 13h8l1-13"/></svg></button>
      </div></div>`).join('');
  const p4bind = ()=>panel.querySelectorAll('[data-p4del]').forEach(b=>b.addEventListener('click',()=>p4Delete(b.dataset.p4del)));

""", label="daypanel-head")

src = inject(src, "  if (bk==='all'){ panel.innerHTML = `<div class=\"day-empty\">已關閉預約</div>`; return; }",
             "", label="_noop") if False else src
src = src.replace(
    '  if (bk===\'all\'){ panel.innerHTML = `<div class="day-empty">已關閉預約</div>`; return; }',
    '  if (bk===\'all\'){ panel.innerHTML = p4html + `<div class="day-empty">已關閉預約</div>`; p4bind(); return; }', 1)
src = src.replace(
    '  if (!rules.length){ panel.innerHTML = `<div class="day-empty">未建立例外預約規則</div>`; return; }',
    '  if (!rules.length){ panel.innerHTML = p4html + (p4html ? \'\' : `<div class="day-empty">未建立例外預約規則</div>`); p4bind(); return; }', 1)
src = src.replace(
    "  panel.innerHTML = rules.map((r,i)=>ruleCardHTML(r,i)).join('');",
    "  panel.innerHTML = p4html + rules.map((r,i)=>ruleCardHTML(r,i)).join('');\n  p4bind();", 1)

# ── 6) 資料層與新增 Modal ──────────────────────────────────────────
src = inject(src, "function blockOf(date){", """/* ===== Part4 注入：臨時關閉資料層（獨立 key，不動定稿頁的 appData） ===== */
const P4_KEY='p4_closures';
const P4_UNITS=[{g:'群組 G1',ids:['A1','B1','C1','D1','E1']},{g:'群組 G2',ids:['A2','B2','C2','D2','E2']},{g:'預設群組',ids:['Default']}];
function p4All(){ try{ return JSON.parse(sessionStorage.getItem(P4_KEY))||[]; }catch(e){ return []; } }
function p4Save(v){ sessionStorage.setItem(P4_KEY, JSON.stringify(v)); }
function p4ClosuresOf(date){ return p4All().filter(c=>c.date===date); }
function p4Delete(id){ p4Save(p4All().filter(c=>c.id!==id)); renderAll(); }
function p4OpenModal(){
  const date = state.selectedDate;
  const sel = new Set();
  const wrap = document.createElement('div');
  wrap.className='modal-mask show'; wrap.id='p4Modal';
  wrap.innerHTML = `<div class="modal">
    <h3>臨時預約關閉 - ${date}</h3>
    <div class="m-body">
      <p>關閉後，所選預約單位於此時段<b>不再開放線上預約</b>；已存在的預約與後台自建預約不受影響。優先權僅次於整日不可預約。</p>
      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
        <label>開始 <input type="time" id="p4S" value="18:00" class="time-input"></label>〜
        <label>結束 <input type="time" id="p4E" value="20:00" class="time-input"></label>
      </div>
      <div class="p4-um">
        ${P4_UNITS.map(gr=>`<div class="g">${gr.g}</div><div class="row">${gr.ids.map(u=>`<button type="button" data-p4u="${u}">${u}</button>`).join('')}</div>`).join('')}
      </div>
      <div class="err-msg" id="p4Err" style="display:none">請至少選擇一個預約單位，且結束時間需晚於開始時間。</div>
    </div>
    <div class="btn-row" style="display:flex;gap:8px;justify-content:flex-end">
      <button class="btn-md ghost" id="p4Cancel">取消</button>
      <button class="btn-md primary" id="p4Ok">關閉線上預約</button>
    </div></div>`;
  document.body.appendChild(wrap);
  wrap.querySelectorAll('[data-p4u]').forEach(b=>b.addEventListener('click',()=>{
    const u=b.dataset.p4u;
    if(sel.has(u)){ sel.delete(u); b.classList.remove('on'); } else { sel.add(u); b.classList.add('on'); }
  }));
  const close=()=>wrap.remove();
  wrap.addEventListener('click',e=>{ if(e.target===wrap) close(); });
  wrap.querySelector('#p4Cancel').addEventListener('click',close);
  wrap.querySelector('#p4Ok').addEventListener('click',()=>{
    const s=wrap.querySelector('#p4S').value, e=wrap.querySelector('#p4E').value;
    if(!sel.size || !s || !e || e<=s){ wrap.querySelector('#p4Err').style.display='block'; return; }
    p4Save(p4All().concat({ id:'p4_'+date+'_'+s, date, start:s, end:e, unitIds:[...sel] }));
    close(); renderAll();
  });
}

""", label="data-layer")

# ── 7) 綁定按鈕 ────────────────────────────────────────────────────
src = inject(src, "  document.getElementById('blockBtn').addEventListener('click', openClosurePage);",
             "\n  document.getElementById('p4ClosureBtn').addEventListener('click', p4OpenModal);",
             before=False, label="bind")

# 右下角「回後台模擬器」原本指向 sim.html（非整合版），改指方案 C 的整合頁
src = src.replace('<a href="sim.html"', '<a href="part4_timeline.html#/book/timeline"', 1)
src = src.replace('← 回後台模擬器', '→ 方案 C・時間軸整合版', 1)

src = src.replace("<title>", "<title>Part4 整合版｜", 1)
src = src.replace("<!-- Shop-Rebirth Prototype · 例外預約規則 · 維護：FindLife Support -->",
                  "<!-- Part4 整合版：由 tools/build_part4_exception.py 從 exception_rules.html 產生，請勿直接編輯 -->", 1)

out = root / "part4_exception.html"
out.write_text(src, encoding="utf-8")
print(f"part4_exception.html 已產生：{len(src)} chars")
