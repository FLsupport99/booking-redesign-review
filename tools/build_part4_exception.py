#!/usr/bin/env python3
"""從 Part 1 定稿的 exception_rules.html 產生 part4_exception.html。

原則：定稿頁 100% 不動，只「注入」Part 4 的臨時預約關閉——
月曆多一種 pill、該日詳情多一種列、標題列多一顆按鈕、一個新增 modal。
資料存獨立的 sessionStorage key（p4_closures），完全不碰原頁的資料層。
Part 1 原型（exception_rules.html）更新時，重跑本腳本即可同步。
"""
import pathlib
import sys

root = pathlib.Path(__file__).resolve().parent.parent
src = (root / "exception_rules.html").read_text(encoding="utf-8")

def inject(hay, anchor, addition, before=True, label=""):
    if hay.count(anchor) != 1:
        sys.exit(f"錨點不唯一或不存在（{label}）：{anchor[:60]!r} count={hay.count(anchor)}")
    return hay.replace(anchor, (addition + anchor) if before else (anchor + addition))

# 1) CSS：臨時關閉 pill 與列 tag（沿用定稿的視覺語言，只是換橘色系）
src = inject(src, "</style>", """
/* ===== Part4 注入：臨時預約關閉 ===== */
.cal-pill.p4cl{background:#fdeee0;color:#a35a1f}
.tag.p4cl{background:#fdeee0;color:#a35a1f}
.p4-banner{margin:0 0 12px;background:#f3faf6;border:1px solid #bfe6d4;border-radius:10px;padding:10px 14px;font-size:13px;line-height:19px;color:#456}
""", label="css")

# 2) 頁首說明（讓 review 的人知道這頁是什麼）
src = inject(src, '<body class="mode-basic view-l1 dev-desktop">', "", label="body-check")  # 僅驗證錨點
src = inject(
    src,
    '<button class="btn-md ghost" id="todayBtn">今天</button>',
    "",
    label="todaybtn-check",
)

banner_anchor = '<span class="cal-pill exc">N</span>已套用例外預約規則</span>'
src = inject(src, banner_anchor,
    '''\n              <span><span class="cal-pill p4cl">N</span>臨時預約關閉（Part 4 注入）</span>''',
    before=False, label="legend")

# 3) 標題列：blockBtn 與 addBtn 之間加「臨時預約關閉」按鈕
src = inject(src, '<button class="btn-md primary anno" id="addBtn">',
    '''<button class="btn-md ghost" id="p4ClosureBtn">
              <svg viewBox="0 0 24 24"><rect x="4" y="5" width="16" height="16" rx="2"/><path d="M8 3v4M16 3v4M9 12l6 6M15 12l-6 6"/></svg>
              臨時預約關閉
            </button>
            ''', label="closure-btn")

# 4) 月曆 pill
src = inject(src, "      const rn = rulesOf(ymd).length;",
    '''      const p4n = p4ClosuresOf(ymd).length;
      if (p4n) icons.innerHTML += `<span class="cal-pill p4cl" title="${p4n} 筆臨時預約關閉${bk==='all'?'（被整日不可預約覆蓋）':''}">${p4n}</span>`;
''', label="cal-pill")

# 5) 該日詳情：空狀態條件納入 closures、block 卡後插入臨時關閉列
src = inject(src, "  if (rules.length===0 && !block){",
    '''  /* Part4 注入：臨時關閉列（排在 Block 卡之後、例外規則之前＝優先層級順序） */
  p4ClosuresOf(date).forEach(c=>{
    const row = document.createElement('div');
    row.className='list-row anno';
    if (bk==='all') row.style.opacity='.5';
    row.innerHTML = `
      <div class="lr-main">
        <div class="lr-title"><span class="tag p4cl">臨時關閉</span><span>${c.start}–${c.end}</span>${bk==='all'?'<span class="lr-apply">已被整日不可預約覆蓋</span>':''}</div>
        <div class="lr-sub">關閉單位：${c.unitIds.join('、')}（僅擋線上預約，自建預約與既有預約不受影響）</div>
      </div>
      <div class="lr-tools">
        <button class="icon-btn danger" title="解除" data-p4del="${c.id}"><svg viewBox="0 0 24 24"><path d="M5 7h14M9 7V5h6v2M7 7l1 13h8l1-13"/></svg></button>
      </div>`;
    panel.appendChild(row);
  });
  panel.querySelectorAll('[data-p4del]').forEach(b=>b.addEventListener('click',()=>{ p4Delete(b.dataset.p4del); }));

''', label="daypanel")

# 空狀態條件改寫：沒有規則、沒有 block、也沒有臨時關閉，才顯示空狀態
old_empty = "if (rules.length===0 && !block){"
new_empty = "if (rules.length===0 && !block && p4ClosuresOf(date).length===0){"
if src.count(old_empty) != 1:
    sys.exit(f"空狀態條件錨點異常 count={src.count(old_empty)}")
src = src.replace(old_empty, new_empty, 1)

# 6) 資料層與 modal（獨立 sessionStorage key，不碰原頁 appData）
src = inject(src, "function blockOf(date){",
    '''/* ===== Part4 注入：臨時關閉資料層（獨立 key，不動原頁資料） ===== */
const P4_KEY='p4_closures';
const P4_UNITS=[{g:'群組 G1',ids:['A1','B1','C1','D1','E1']},{g:'群組 G2',ids:['A2','B2','C2','D2','E2']},{g:'預設群組',ids:['Default']}];
function p4All(){ try{ return JSON.parse(sessionStorage.getItem(P4_KEY))||[]; }catch(e){ return []; } }
function p4Save(v){ sessionStorage.setItem(P4_KEY, JSON.stringify(v)); }
function p4ClosuresOf(date){ return p4All().filter(c=>c.date===date); }
function p4Delete(id){ p4Save(p4All().filter(c=>c.id!==id)); renderAll(); }
function p4OpenModal(){
  const date = state.selectedDate;
  let sel = new Set();
  const wrap = document.createElement('div');
  wrap.className='modal-mask show'; wrap.id='p4Modal';
  wrap.innerHTML = `<div class="modal">
    <h3>臨時預約關閉 - ${zhDate(date)}</h3>
    <div class="m-body">
      <p>關閉後，所選單位於此時段<b>不再開放線上預約</b>；已存在的預約與後台自建預約不受影響。優先權僅次於整日不可預約。</p>
      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
        <label>開始 <input type="time" id="p4S" value="18:00" class="time-input"></label>〜
        <label>結束 <input type="time" id="p4E" value="20:00" class="time-input"></label>
      </div>
      <div id="p4Units" style="display:flex;flex-direction:column;gap:6px">
        ${P4_UNITS.map(gr=>`<div><div style="font-size:12px;color:#888;margin:4px 0">${gr.g}</div>
          <div style="display:flex;gap:6px;flex-wrap:wrap">${gr.ids.map(u=>`<button type="button" class="btn-md ghost" data-p4u="${u}">${u}</button>`).join('')}</div></div>`).join('')}
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
    if(sel.has(u)){ sel.delete(u); b.classList.remove('ghost-green'); }
    else{ sel.add(u); b.classList.add('ghost-green'); }
  }));
  const close=()=>wrap.remove();
  wrap.addEventListener('click',e=>{ if(e.target===wrap) close(); });
  wrap.querySelector('#p4Cancel').addEventListener('click',close);
  wrap.querySelector('#p4Ok').addEventListener('click',()=>{
    const s=wrap.querySelector('#p4S').value, e=wrap.querySelector('#p4E').value;
    if(!sel.size || !s || !e || e<=s){ wrap.querySelector('#p4Err').style.display='block'; return; }
    const all=p4All();
    all.push({ id:'p4_'+Date.now(), date, start:s, end:e, unitIds:[...sel] });
    p4Save(all); close(); renderAll();
  });
}
document.addEventListener('DOMContentLoaded',()=>{
  const b=document.getElementById('p4ClosureBtn');
  if(b) b.addEventListener('click',p4OpenModal);
});

''', label="data-layer")

# 7) 頁首 banner（放在月曆 section 前的第一個 section 標題附近——直接放 body 開頭浮動說明較安全）
src = inject(src, '<body class="mode-basic view-l1 dev-desktop">',
    '''
<!-- Part4 注入版：由 tools/build_part4_exception.py 從 exception_rules.html 產生，請勿直接編輯 -->''',
    before=False, label="banner-comment")

src = src.replace("<title>", "<title>Part4 整合版｜", 1)

out = root / "part4_exception.html"
out.write_text(src, encoding="utf-8")
print(f"part4_exception.html 已產生：{len(src)} chars")
