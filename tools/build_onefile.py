#!/usr/bin/env python3
"""單檔合成器 — 把 Part 1–4 全部 review 內容合成一個 index.html。

2026-09-01 v2（Ian 回饋「還是 Part1-4 分開」後改版）：
- **設計稿不再分 view**：五個 gallery（algo/design/modes/p3/p4）的 nav 與 sections
  直接抽出、依 Part 順序串成同一個滾動長頁（單一側欄導覽、單一 lightbox）。
  各 gallery 的 section id 加前綴避免撞名；CSS 用 p3 版（五份同源，p3 為超集）。
- **互動原型維持浮層**：4 個 app（後台模擬器/例外規則/顧客端流程/排位設計稿版）
  是獨立 JS app 無法攤平，仍以 <iframe srcdoc> 全視窗浮層掛載，從側欄「▶」連結開啟。
  跨頁連結 patch 成 parent.postMessage、?mode= 走 iframe.name（同 v1）。
- 子檔 HTML-escape 存 <textarea hidden>；sessionStorage 與外層同源共享。

用法：python3 tools/build_onefile.py
"""
import html as html_mod
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "index.html"


def esc_ta(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;")


def patch(name: str, src: str, subs) -> str:
    for old, new in subs:
        n = src.count(old)
        if n != 1:
            sys.exit(f"[{name}] 錨點出現 {n} 次（預期 1）：{old[:80]!r}")
        src = src.replace(old, new)
    return src


PM = "parent.postMessage({nav:'%s'},'*')"

# ── 互動原型（浮層 view）──
APPS = {
    "backend": (
        "後台模擬器（Part 1 設定＋Part 3 視圖＋Part 4）",
        "src/part4_priority.html",
        [
            ("onclick=\"location.href='index.html'\">← Review 入口",
             "onclick=\"" + PM % "home" + "\">← 回總覽"),
            ("location.href = 'part4_exception.html?mode=' + (excMap[db.mode] || 'basic');  /* Part4 整合版 */",
             "parent.postMessage({nav:'exception', qs:'mode='+(excMap[db.mode]||'basic')},'*');"),
            ("onclick=\"location.href='hierarchical_booking.html'\"",
             'onclick="' + PM % "hier" + '"'),
            ("onclick=\"location.href='designs.html'\"",
             'onclick="' + PM % "home" + '"'),
        ],
    ),
    "exception": (
        "例外預約規則（Part 1 定稿）",
        "src/exception_rules.html",
        [
            ("new URLSearchParams(window.location.search);",
             "new URLSearchParams(window.location.search||window.name);"),
            ('<a href="sim.html" style=',
             '<a href="#" onclick="parent.postMessage({nav:\'backend\'},\'*\');return false" style='),
        ],
    ),
    "hier": ("顧客端預約流程（階層項目）", "src/hierarchical_booking.html", []),
    "autoseat": (
        "自動排位規則・設計稿版（人數範圍×分配方式）",
        "src/part4_autoseat_design.html",
        [],
    ),
}

# ── 設計稿 gallery 來源（依 Part 排序串接）──
GALLERIES = {
    "algo": ("演算法改版・後台設定", "src/galleries/algo_gallery.html"),
    "design": ("顧客預約頁（基本人數）", "src/galleries/design_gallery.html"),
    "modes": ("顧客預約頁（服務項目＋階層項目）", "src/galleries/modes_gallery.html"),
    "p3": ("Part 3 自建預約", "src/galleries/p3_gallery.html"),
    "p4": ("Part 4 定稿（臨時關閉／自訂排位／多組訂金）", "src/galleries/p4_gallery.html"),
}

# 全部統合的互動版（地圖最上方橫幅＋側欄第一條）
BANNER = ("backend", "後台模擬器 — 全部統合的互動版", "Part 1 後台設定 ＋ Part 3 三視圖與新增修改 ＋ Part 4 訂金／臨時關閉，同一份假資料互通", "", "")

# Part → (標題, [gallery keys], [(app id, 連結文字, 進場 hash, 進場後點擊)], 附註)
PARTS = [
    ("Part 1 · 後台設定與顧客預約頁", ["algo", "design"],
     [("backend", "後台設定（互動）", "#/rules", ""),
      ("exception", "例外預約規則（互動）", "", "")], ""),
    ("Part 2 · 顧客預約頁（服務項目＋階層項目）", ["modes"],
     [("hier", "顧客端預約流程（互動）", "", "")], ""),
    ("Part 3 · 自建預約（時間軸／空間圖／清單）", ["p3"],
     [("backend", "時間軸／空間圖／清單（互動）", "#/book/timeline", "")], ""),
    ("Part 4 · 自動排位・多組訂金・臨時關閉", ["p4"],
     [("autoseat", "自動排位規則（互動・定稿版）", "", ""),
      ("backend", "訂金管理（互動）", "#/p4deposit", ""),
      ("backend", "臨時關閉（互動・時間軸內）", "#/book/timeline", "#p4fEnter")], ""),
]


import struct


def png_size(path: Path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w, h = struct.unpack(">II", head[16:24])
    return w, h


def add_dims(main: str) -> str:
    """lazy 圖注入 width/height（瀏覽器據此預留 aspect-ratio），
    否則 1300+ 張圖邊載邊推版、錨點會跑掉。"""

    def repl(m):
        rel = m.group(1)
        p = ROOT / rel
        if p.exists():
            wh = png_size(p)
            if wh:
                return f'<img loading="lazy" decoding="async" width="{wh[0]}" height="{wh[1]}" src="{rel}"'
        return m.group(0)

    return re.sub(r'<img loading="lazy" src="([^"]+)"', repl, main)


def extract(g: str):
    """抽 gallery 的 nav 與 main 內容，section id 加 g- 前綴。"""
    s = (ROOT / GALLERIES[g][1]).read_text(encoding="utf-8")
    nav = re.search(r'<nav class="side">(.*?)</nav>', s, re.S).group(1)
    main = re.search(r"<main>(.*?)</main>", s, re.S).group(1)
    nav = nav.replace('href="#s-', f'href="#{g}-s-')
    main = main.replace('<section id="s-', f'<section id="{g}-s-')
    main = add_dims(main)
    n = len(re.findall(r'<figure class="card', main))
    return nav, main, n


def build():
    style = re.search(
        r"<style>.*?</style>", (ROOT / GALLERIES["p3"][1]).read_text(encoding="utf-8"), re.S
    ).group(0)

    apps, missing = {}, []
    for aid, (title, rel, subs) in APPS.items():
        p = ROOT / rel
        if not p.exists():
            missing.append(aid)
            continue
        apps[aid] = patch(aid, p.read_text(encoding="utf-8"), subs)
    if missing:
        print(f"（略過不存在的互動原型：{', '.join(missing)}）")

    nav_parts, main_parts, map_cards, total = [], [], [], 0
    gallery_counts = {}
    nav_parts.append('<a class="proto big" href="#backend" data-open="backend" data-hash="" data-click="">▶ 後台模擬器（全部統合）</a>')
    for pi, (ptitle, gkeys, papps, note) in enumerate(PARTS, 1):
        nav_parts.append(f'<div class="pgh"><a href="#part{pi}">{ptitle}</a></div>')
        main_parts.append(f'<h2 class="ph" id="part{pi}">{ptitle}</h2>')
        card = [f'<div class="mp"><a class="mph" href="#part{pi}">{ptitle}</a>']
        for g in gkeys:
            card.append(f'<a class="ml g" href="#gal-{g}">{GALLERIES[g][0]}<b>{{N_{g}}} 張</b></a>')
        for aid, label, hsh, clk in papps:
            if aid in apps:
                card.append(f'<a class="ml i" href="#{aid}" data-open="{aid}" data-hash="{hsh}" data-click="{clk}">▶ {label}</a>')
        if note:
            card.append(f'<div class="mnote">{note}</div>')
        card.append('</div>')
        map_cards.append(''.join(card))
        for aid, label, hsh, clk in papps:
            if aid in apps:
                nav_parts.append(
                    f'<a class="proto" href="#{aid}" data-open="{aid}" data-hash="{hsh}" data-click="{clk}">▶ {label}</a>'
                )
        if note:
            nav_parts.append(f'<div class="pnote">{note}</div>')
        for g in gkeys:
            nav, main, n = extract(g)
            gallery_counts[g] = n
            total += n
            gtitle = GALLERIES[g][0]
            nav_parts.append(f'<a class="ngh2" href="#gal-{g}">{gtitle} <span>{n}</span></a>')
            nav_parts.append(nav)
            main_parts.append(f'<div id="gal-{g}">{main}</div>')

    map_html = ''.join(map_cards)
    for g in GALLERIES:
        map_html = map_html.replace('{N_' + g + '}', str(gallery_counts.get(g, 0)))

    textareas = "\n".join(
        f'<textarea hidden id="doc-{aid}">{esc_ta(doc)}</textarea>'
        for aid, doc in apps.items()
    )
    titles_js = json.dumps(
        {aid: v[0] for aid, v in APPS.items() if aid in apps}, ensure_ascii=False
    )

    extra_css = """
  .pgh{margin:18px 0 2px;padding:10px 12px 4px;border-top:1px solid #eee}
  .pgh:first-child{border-top:none;margin-top:0}
  .pgh a{font-size:13px;font-weight:800;color:#1f7a56;text-decoration:none;padding:0}
  .ngh2{font-size:12px;font-weight:700;color:#29A379;padding:10px 12px 2px;letter-spacing:.5px;display:flex;justify-content:space-between}
  .ngh2 span{color:#9fcdbb;font-weight:500;font-variant-numeric:tabular-nums}
  nav.side a.proto{color:#3E7BFA;font-weight:500}
  nav.side a.proto.big{background:#EEF3FE;border-radius:8px;margin:0 4px 4px;font-weight:700}
  nav.side a.proto:hover{background:#EEF3FE}
  .pnote{font-size:12px;color:#aaa;padding:4px 12px;line-height:1.5}
  .map{background:#fff;border-bottom:1px solid #e5e5e5;padding:18px 24px 22px}
  .maphint{font-size:12px;color:#999;margin-bottom:12px}
  .maphint .dg{color:#8FD6B8}.maphint .di{color:#3E7BFA}
  .mbig{display:flex;align-items:baseline;gap:14px;background:#3E7BFA;color:#fff;border-radius:12px;padding:14px 18px;margin-bottom:14px;max-width:1280px;text-decoration:none}
  .mbig:hover{background:#3069e0}
  .mbig .bt{font-size:15px;font-weight:700;white-space:nowrap}
  .mbig .bd{font-size:13px;color:rgba(255,255,255,.85);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  @media (max-width:700px){ .mbig{flex-direction:column;gap:4px} .mbig .bd{white-space:normal} }
  .mgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px;max-width:1280px}
  .mp{border:1px solid #e8e8e8;border-radius:12px;padding:14px 16px;display:flex;flex-direction:column;gap:2px}
  .mph{font-size:14px;font-weight:700;color:#1f7a56;text-decoration:none;margin-bottom:8px}
  .mph:hover{text-decoration:underline}
  .ml{display:flex;justify-content:space-between;align-items:center;gap:8px;font-size:13px;text-decoration:none;padding:6px 8px;border-radius:8px}
  .ml.g{color:#333}.ml.g b{font-weight:500;font-size:12px;color:#29A379;background:#ECF8F3;border-radius:100px;padding:2px 9px;font-variant-numeric:tabular-nums;white-space:nowrap}
  .ml.i{color:#3E7BFA;font-weight:500}
  .ml:hover{background:#f5f7f6}
  .mnote{font-size:12px;color:#aaa;padding:6px 8px 0;line-height:1.5}
  main .ph{font-size:22px;font-weight:800;color:#1f7a56;margin:44px 0 6px;padding-top:24px;border-top:2px solid #dfe8e4}
  main .ph:first-of-type{margin-top:0;border-top:none;padding-top:0}
  .viewer{position:fixed;inset:0;background:#f4f5f6;display:none;flex-direction:column;z-index:60}
  .viewer.on{display:flex}
  .vbar{height:36px;flex:0 0 36px;display:flex;align-items:center;gap:10px;background:#1f2937;color:#fff;padding:0 12px}
  .vbar button{font:inherit;font-size:13px;color:#fff;background:none;border:0;cursor:pointer;padding:4px 6px;border-radius:6px}
  .vbar button:hover{background:rgba(255,255,255,.14)}
  .vbar .vt{font-size:13px;color:#d1d5db;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .viewer iframe{border:0;width:100%;flex:1}
"""
    style = style.replace("</style>", extra_css + "</style>")

    page = f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MENU店+ 改版 — Design Review</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><text y='13' font-size='13'>🗂️</text></svg>">
{style}</head><body>
<header class="top"><h1>MENU店+ 改版 — Design Review</h1><span class="meta">Part 1–4 全部串接 · {total} 張設計稿＋{len(apps)} 個互動原型 · 照 Figma 原稿渲染</span></header>
<div class="map"><div class="maphint"><span class="dg">●</span> 設計稿＝頁內跳轉　<span class="di">▶</span> 互動原型＝開新畫面（左上角「← 回設計稿」返回）</div>
<a class="mbig" href="#backend" data-open="backend" data-hash="" data-click=""><span class="bt">▶ {BANNER[1]}</span><span class="bd">{BANNER[2]}</span></a>
<div class="mgrid">{map_html}</div></div>
<div class="wrap">
<nav class="side">{''.join(nav_parts)}</nav>
<main>
{''.join(main_parts)}
</main>
</div>
<div id="lb" onclick="this.classList.remove('on')"><img id="lbimg" src=""></div>
<div class="viewer" id="viewer">
  <div class="vbar"><button id="vclose">← 回設計稿</button><span class="vt" id="vtitle"></span></div>
</div>
{textareas}
<script>
document.querySelectorAll('.card img').forEach(function(im){{
  im.addEventListener('click',function(e){{e.stopPropagation();var lb=document.getElementById('lb');document.getElementById('lbimg').src=im.src;lb.classList.add('on');}});
}});
const TITLES = {titles_js};
const viewer = document.getElementById('viewer');
const vtitle = document.getElementById('vtitle');
let frame = null;
function openView(id, qs, hash, clickSel) {{
  const ta = document.getElementById('doc-' + id);
  if (!ta) return;
  closeView(true);
  frame = document.createElement('iframe');
  frame.name = qs || '';
  /* 進場 hash 不能在 load 當下設（會被 app 開機的預設路由蓋掉），延遲到開機完成後 */
  if (hash || clickSel) frame.addEventListener('load', () => setTimeout(() => {{
    try {{
      if (hash) frame.contentWindow.location.hash = hash;
      if (clickSel) setTimeout(() => {{
        const el = frame.contentDocument.querySelector(clickSel);
        if (el) el.click();
      }}, 250);
    }} catch (e) {{}}
  }}, 400), {{ once: true }});
  viewer.appendChild(frame);
  frame.srcdoc = ta.value;
  vtitle.textContent = TITLES[id] || '';
  viewer.classList.add('on');
  document.body.style.overflow = 'hidden';
  if (location.hash !== '#' + id) history.pushState(null, '', '#' + id);
}}
function closeView(keepHash) {{
  if (frame) {{ frame.remove(); frame = null; }}
  viewer.classList.remove('on');
  document.body.style.overflow = '';
  if (!keepHash && location.hash && document.getElementById('doc-' + location.hash.slice(1)))
    history.pushState(null, '', location.pathname);
}}
document.querySelectorAll('[data-open]').forEach(b =>
  b.addEventListener('click', e => {{ e.preventDefault(); openView(b.dataset.open, '', b.dataset.hash || '', b.dataset.click || ''); }}));
document.getElementById('vclose').addEventListener('click', () => closeView());
window.addEventListener('message', e => {{
  const d = e.data || {{}};
  if (d.nav === 'home') closeView();
  else if (d.nav === 'backend') openView('backend');
  else if (d.nav === 'hier') openView('hier');
  else if (d.nav === 'exception') openView('exception', d.qs || '');
  else if (d.nav === 'autoseat') openView('autoseat');
}});
window.addEventListener('popstate', () => {{
  const id = location.hash.slice(1);
  if (id && document.getElementById('doc-' + id)) openView(id); else closeView(true);
}});
if (location.hash && document.getElementById('doc-' + location.hash.slice(1)))
  openView(location.hash.slice(1));
</script>
</body></html>"""

    OUT.write_text(page, encoding="utf-8")
    print(f"OK → {OUT}  ({OUT.stat().st_size:,} bytes, {total} 張, apps: {', '.join(apps)})")


if __name__ == "__main__":
    build()
