#!/usr/bin/env python3
"""點擊式互動原型播放器產生器
用法: build_proto.py <proto.json> <標題> <assets目錄名> <輸出html路徑>
"""
import json, sys, html

proto_path, title, assets, out_path = sys.argv[1:5]
g = json.load(open(proto_path))

# 去重熱區（interactions + 舊欄位會重複）
for s in g["screens"]:
    seen, hs = set(), []
    for h in s["hs"]:
        k = (h["x"], h["y"], h["w"], h["h"], h["t"])
        if k not in seen:
            seen.add(k)
            hs.append(h)
    s["hs"] = hs

data = {
    "assets": assets,
    "start": g["start"],
    "screens": [
        {"id": s["id"], "name": s["name"], "sec": s["sec"], "w": s["w"], "h": s["h"], "hs": s["hs"]}
        for s in g["screens"]
    ],
}
total_hs = sum(len(s["hs"]) for s in data["screens"])

page = """<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ — 互動原型（點擊式）</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:"PingFang TC","Noto Sans TC",sans-serif;background:#e9ebee;height:100vh;display:flex;flex-direction:column;color:#222}
header{background:#fff;border-bottom:1px solid #e2e2e2;padding:10px 16px;display:flex;align-items:center;gap:12px;z-index:20}
header h1{font-size:15px;font-weight:600;white-space:nowrap}
#scname{font-size:13px;color:#666;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1}
.btn{font-size:13px;border:1px solid #d5d5d5;background:#fff;border-radius:8px;padding:6px 12px;cursor:pointer;white-space:nowrap}
.btn:hover{border-color:#3FBA88;color:#29A379}
.btn:disabled{opacity:.4;cursor:default}
a.btn{text-decoration:none;color:#29A379;border-color:#3FBA88}
#wrap{flex:1;display:flex;min-height:0}
nav#side{width:270px;flex:0 0 270px;background:#fff;border-right:1px solid #e2e2e2;overflow:auto;padding:12px 8px;display:none}
nav#side.on{display:block}
nav#side .sg{font-size:12px;font-weight:700;color:#29A379;padding:10px 10px 4px}
nav#side a{display:flex;align-items:center;gap:6px;font-size:12.5px;color:#444;text-decoration:none;padding:6px 10px;border-radius:7px;line-height:1.4}
nav#side a:hover{background:#f0f7f3}
nav#side a.cur{background:#ecf8f3;color:#1d8a63;font-weight:600}
nav#side a .dot{flex:0 0 6px;width:6px;height:6px;border-radius:50%;background:#d9d9d9}
nav#side a .dot.link{background:#3FBA88}
#stage{flex:1;overflow:auto;padding:26px;display:flex;justify-content:center;align-items:flex-start}
#frame{position:relative;background:#fff;box-shadow:0 6px 28px rgba(0,0,0,.14);border-radius:10px;overflow:hidden;height:fit-content}
#frame img{display:block;width:100%;height:auto;-webkit-user-drag:none}
.hs{position:absolute;cursor:pointer;border-radius:6px}
.hs.flash{background:rgba(63,186,136,.28);outline:2px solid rgba(63,186,136,.9);animation:pw 1.1s ease 2}
@keyframes pw{0%,100%{opacity:0}45%{opacity:1}}
footer{background:#fff;border-top:1px solid #e2e2e2;padding:7px 16px;font-size:12px;color:#999;text-align:center}
#deadend{position:fixed;left:50%;bottom:52px;transform:translateX(-50%);background:rgba(40,40,40,.92);color:#fff;font-size:13px;border-radius:100px;padding:9px 18px;opacity:0;pointer-events:none;transition:.25s}
#deadend.on{opacity:1}
</style></head><body>
<header>
  <button class="btn" id="bk" title="返回上一畫面（←）">◀ 返回</button>
  <h1>__TITLE__ · 互動原型</h1>
  <span id="scname"></span>
  <button class="btn" id="sd">☰ 畫面清單</button>
  <a class="btn" href="algo_gallery.html">設計稿總覽</a>
  <a class="btn" href="index.html">回入口</a>
</header>
<div id="wrap">
  <nav id="side"></nav>
  <div id="stage"><div id="frame"><img id="shot" alt=""><div id="hl"></div></div></div>
</div>
<footer>點擊畫面中的按鈕互動 · 點空白處會亮出可點擊區域 · ← 鍵返回 · 綠點＝有串互動的畫面</footer>
<div id="deadend">這個畫面沒有串互動連結——用「◀ 返回」或「☰ 畫面清單」繼續</div>
<script>
const D = __DATA__;
const byId = {}; D.screens.forEach(s => byId[s.id] = s);
const hist = [];
let cur = null;
const $ = id => document.getElementById(id);

function fname(id){ return id.replace(':','_') + '.png'; }

function render(id, push){
  const s = byId[id]; if (!s) return;
  if (push && cur) hist.push(cur);
  cur = id;
  $('bk').disabled = hist.length === 0;
  $('scname').textContent = s.sec + ' › ' + s.name;
  const fr = $('frame');
  fr.style.width = 'min(' + s.w + 'px, 96%)';
  $('shot').src = D.assets + '/' + fname(id);
  const hl = $('hl'); hl.innerHTML = '';
  s.hs.forEach(h => {
    const d = document.createElement('div');
    d.className = 'hs';
    d.style.cssText = 'left:'+h.x+'%;top:'+h.y+'%;width:'+h.w+'%;height:'+h.h+'%';
    d.addEventListener('click', e => { e.stopPropagation(); render(h.t, true); });
    hl.appendChild(d);
  });
  document.querySelectorAll('#side a').forEach(a => a.classList.toggle('cur', a.dataset.id === id));
  const curLink = document.querySelector('#side a.cur');
  if (curLink) curLink.scrollIntoView({block:'nearest'});
  location.hash = id.replace(':','-');
  if (!s.hs.length){ const de=$('deadend'); de.classList.add('on'); setTimeout(()=>de.classList.remove('on'), 2600); }
}

$('frame').addEventListener('click', () => {
  document.querySelectorAll('.hs').forEach(h => { h.classList.remove('flash'); void h.offsetWidth; h.classList.add('flash'); });
});
$('bk').addEventListener('click', () => { if (hist.length) render(hist.pop(), false); });
$('sd').addEventListener('click', () => $('side').classList.toggle('on'));
document.addEventListener('keydown', e => {
  if (e.key === 'ArrowLeft' || e.key === 'Backspace') { if (hist.length){ e.preventDefault(); render(hist.pop(), false); } }
});

// 側欄
(function(){
  const side = $('side');
  let sec = null;
  D.screens.forEach(s => {
    if (s.sec !== sec){ sec = s.sec; const t = document.createElement('div'); t.className='sg'; t.textContent = sec; side.appendChild(t); }
    const a = document.createElement('a'); a.href = 'javascript:void(0)'; a.dataset.id = s.id;
    a.innerHTML = '<span class="dot' + (s.hs.length ? ' link' : '') + '"></span>' + s.name;
    a.addEventListener('click', () => render(s.id, true));
    side.appendChild(a);
  });
})();

const fromHash = location.hash && location.hash.slice(1).replace('-',':');
render(byId[fromHash] ? fromHash : D.start, false);
</script>
</body></html>
"""
page = page.replace("__TITLE__", html.escape(title)).replace("__DATA__", json.dumps(data, ensure_ascii=False))
open(out_path, "w").write(page)
print(f"{out_path}: {len(data['screens'])} screens, {total_hs} hotspots (deduped)")
