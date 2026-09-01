#!/usr/bin/env python3
"""單檔合成器 — 把 Part 1–4 全部 review 內容合成一個 index.html。

2026-09 全站收斂：站上只留一個入口檔，其餘頁面全部下架（Ian 2026-09-01 指示）。
- 設計稿 gallery（src/galleries/*.html，由 build_galleries.py 產生）與互動原型
  （src/*.html，由 build_part4_*.py 鏈產生）都以 <iframe srcdoc> 全視窗掛載，
  CSS/JS 完全隔離、原始碼一字不動（僅做下方 PATCHES 的錨定替換）。
- 對 part4_review_lessons「不用 iframe」規則的說明：當年的病因是「窄欄 iframe
  觸發 RWD 斷點＋內外雙側欄打架」；這裡 iframe 是 100vw 全視窗層、外殼只有
  36px 頂條，兩個病因都不存在。srcdoc 是不重寫子 app 就能單檔化的唯一做法。
- 子檔以 HTML-escape 存進 <textarea hidden>，開啟 view 時 textarea.value 直接
  丟給 iframe.srcdoc；query string 依賴（exception_rules 的 ?mode=）改走
  iframe.name（子頁 patch 成 location.search||window.name）。
- 跨頁連結一律 patch 成 parent.postMessage({nav:...})，由外殼路由。

用法：python3 tools/build_onefile.py   （在 repo 任意處執行皆可）
"""
import html as html_mod
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "index.html"


def esc_attr(s: str) -> str:
    """textarea 內容只需擋 & 與 <（避免提前閉合與實體誤解）。"""
    return s.replace("&", "&amp;").replace("<", "&lt;")


def patch(name: str, src: str, subs) -> str:
    """錨定替換；錨點不是恰好 1 次就中止（沿用 build_part4_* 的防呆慣例）。"""
    for old, new in subs:
        n = src.count(old)
        if n != 1:
            sys.exit(f"[{name}] 錨點出現 {n} 次（預期 1）：{old[:80]!r}")
        src = src.replace(old, new)
    return src


PM = "parent.postMessage({nav:'%s'},'*')"
BACKLINK = (
    '<a class="link" href="#" onclick="parent.postMessage({nav:\'home\'},\'*\');'
    "return false\">← 回總覽</a>"
)

# view id → (標題, 來源檔, patches)
VIEWS = {
    "g-design": (
        "設計稿・顧客預約頁（基本人數）",
        "src/galleries/design_gallery.html",
        [(
            '<a class="link" href="hierarchical_booking.html">▶ 互動原型</a>',
            '<a class="link" href="#" onclick="parent.postMessage({nav:\'hier\'},\'*\');return false">▶ 互動原型</a>',
        )],
    ),
    "g-modes": (
        "設計稿・顧客預約頁（服務項目＋階層項目）",
        "src/galleries/modes_gallery.html",
        [('<a class="link" href="index.html">← 回入口</a>', BACKLINK)],
    ),
    "g-algo": (
        "設計稿・演算法改版後台設定",
        "src/galleries/algo_gallery.html",
        [('<a class="link" href="index.html">← 回入口</a>', BACKLINK)],
    ),
    "g-p3": (
        "設計稿・Part 3 自建預約",
        "src/galleries/p3_gallery.html",
        [('<a class="link" href="index.html">← 回入口</a>', BACKLINK)],
    ),
    "g-p4": (
        "設計稿・Part 4 定稿",
        "src/galleries/p4_gallery.html",
        [('<a class="link" href="index.html">← 回入口</a>', BACKLINK)],
    ),
    "backend": (
        "後台模擬器（Part 1 設定＋Part 3 視圖＋Part 4）",
        "src/part4_priority.html",
        [
            (
                "onclick=\"location.href='index.html'\">← Review 入口",
                "onclick=\"" + PM % "home" + "\">← 回總覽",
            ),
            (
                "location.href = 'part4_exception.html?mode=' + (excMap[db.mode] || 'basic');  /* Part4 整合版 */",
                "parent.postMessage({nav:'exception', qs:'mode='+(excMap[db.mode]||'basic')},'*');",
            ),
            (
                "onclick=\"location.href='hierarchical_booking.html'\"",
                'onclick="' + PM % "hier" + '"',
            ),
            (
                "onclick=\"location.href='designs.html'\"",
                'onclick="' + PM % "home" + '"',
            ),
        ],
    ),
    "exception": (
        "例外預約規則（Part 1 定稿）",
        "src/exception_rules.html",
        [
            (
                "new URLSearchParams(window.location.search);",
                "new URLSearchParams(window.location.search||window.name);",
            ),
            (
                '<a href="sim.html" style=',
                '<a href="#" onclick="parent.postMessage({nav:\'backend\'},\'*\');return false" style=',
            ),
        ],
    ),
    "hier": ("顧客端預約流程（階層項目）", "src/hierarchical_booking.html", []),
    "autoseat": (
        "自動排位規則・設計稿版（人數範圍×分配方式）",
        "src/part4_autoseat_design.html",
        [],
    ),
}


def manifest_count(assets_dir: str) -> int:
    p = ROOT / assets_dir / "manifest.json"
    if not p.exists():
        return 0
    d = json.loads(p.read_text())
    secs = d if isinstance(d, list) else d.get("sections", [])
    return sum(len(s.get("frames", [])) for s in secs)


def build():
    docs, missing = {}, []
    for vid, (title, rel, subs) in VIEWS.items():
        p = ROOT / rel
        if not p.exists():
            missing.append(vid)
            continue
        docs[vid] = patch(vid, p.read_text(encoding="utf-8"), subs)
    if missing:
        print(f"（略過不存在的 view：{', '.join(missing)}）")

    counts = {
        "g-design": manifest_count("gallery_assets"),
        "g-modes": manifest_count("modes_assets"),
        "g-algo": manifest_count("algo_assets"),
        "g-p3": manifest_count("p3_assets"),
        "g-p4": manifest_count("p4_assets"),
    }

    def row(vid, kind, desc):
        if vid not in docs:
            return ""
        title = VIEWS[vid][0]
        n = counts.get(vid)
        badge = f'<span class="n">{n} 張</span>' if n else '<span class="n it">互動</span>'
        return (
            f'<button class="row" data-open="{vid}"><span class="k {kind}"></span>'
            f'<span class="t">{title}</span><span class="d">{desc}</span>{badge}</button>'
        )

    parts_html = f"""
<section class="part"><h2>Part 1 · 後台設定與顧客預約頁</h2>
{row('g-algo','g','演算法改版的後台設定全稿：預約模式、預約單位、時段、例外')}
{row('g-design','g','顧客預約頁改版・基本人數模式')}
{row('backend','i','照定稿刻的假資料後台：設定端全模組（時段、單位、模式）＋操作端')}
{row('exception','i','例外預約規則定稿頁，四種預約模式可切換')}
</section>
<section class="part"><h2>Part 2 · 顧客預約頁（服務項目＋階層項目）</h2>
{row('g-modes','g','服務項目與階層項目兩種模式的顧客端全稿')}
{row('hier','i','顧客端階層項目預約完整流程，可實際操作')}
</section>
<section class="part"><h2>Part 3 · 自建預約（時間軸／空間圖／清單）</h2>
{row('g-p3','g','新增／修改預約與三視圖全稿')}
<div class="hint">互動版在「後台模擬器」的預約區——時間軸、空間圖、清單與新增／修改預約。</div>
</section>
<section class="part"><h2>Part 4 · 自動排位・多組訂金・臨時關閉</h2>
{row('g-p4','g','2026 Aug. 定稿：臨時關閉預約單位、自訂排位順序、多組訂金規則')}
{row('autoseat','i','自動排位規則設計稿版：人數範圍 × 分配方式')}
<div class="hint">互動版在「後台模擬器」：自動排位規則、訂金管理兩個設定頁＋時間軸的臨時關閉模式。</div>
</section>"""

    textareas = "\n".join(
        f'<textarea hidden id="doc-{vid}">{esc_attr(doc)}</textarea>'
        for vid, doc in docs.items()
    )
    titles_js = json.dumps({vid: v[0] for vid, v in VIEWS.items() if vid in docs}, ensure_ascii=False)

    page = f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MENU店+ 改版 — Design Review</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><text y='13' font-size='13'>🗂️</text></svg>">
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:"PingFang TC","Noto Sans TC",sans-serif;background:#f4f5f6;color:#222}}
  .home{{max-width:820px;margin:0 auto;padding:48px 24px 80px}}
  .home .hd h1{{font-size:24px;font-weight:700}}
  .home .hd p{{font-size:14px;color:#888;margin-top:8px}}
  .part{{background:#fff;border:1px solid #e5e5e5;border-radius:14px;padding:10px 10px 12px;margin-top:22px}}
  .part h2{{font-size:15px;font-weight:700;color:#29A379;padding:10px 12px 8px}}
  .row{{display:flex;align-items:center;gap:12px;width:100%;text-align:left;background:none;border:0;border-top:1px solid #f0f0f0;padding:12px;font:inherit;cursor:pointer;border-radius:8px}}
  .row:hover{{background:#F3FBF7}}
  .k{{width:8px;height:8px;border-radius:50%;flex:0 0 8px}}
  .k.g{{background:#8FD6B8}} .k.i{{background:#3E7BFA}}
  .t{{font-size:14px;font-weight:600;white-space:nowrap}}
  .d{{font-size:13px;color:#888;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1}}
  .n{{font-size:12px;color:#29A379;background:#ECF8F3;border-radius:100px;padding:3px 10px;white-space:nowrap;font-variant-numeric:tabular-nums}}
  .n.it{{color:#3E7BFA;background:#EEF3FE}}
  .hint{{font-size:13px;color:#999;padding:10px 12px 4px;border-top:1px solid #f0f0f0}}
  footer{{margin-top:36px;font-size:12px;color:#aaa;text-align:center;line-height:1.7}}
  .viewer{{position:fixed;inset:0;background:#f4f5f6;display:none;flex-direction:column;z-index:50}}
  .viewer.on{{display:flex}}
  .vbar{{height:36px;flex:0 0 36px;display:flex;align-items:center;gap:10px;background:#1f2937;color:#fff;padding:0 12px}}
  .vbar button{{font:inherit;font-size:13px;color:#fff;background:none;border:0;cursor:pointer;padding:4px 6px;border-radius:6px}}
  .vbar button:hover{{background:rgba(255,255,255,.14)}}
  .vbar .vt{{font-size:13px;color:#d1d5db;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
  .viewer iframe{{border:0;width:100%;flex:1}}
  @media (max-width:600px){{ .t{{white-space:normal}} .d{{display:none}} }}
</style></head><body>
<div class="home">
  <div class="hd"><h1>MENU店+ 改版 — Design Review</h1>
  <p>Part 1–4 設計稿與互動原型・單一入口。<span style="color:#8FD6B8">●</span> 設計稿　<span style="color:#3E7BFA">●</span> 互動原型</p></div>
  {parts_html}
  <footer>內部 review 用途 · LINE QR 與付款串接為畫面示意<br>© 2026 FindLife Inc.</footer>
</div>
<div class="viewer" id="viewer">
  <div class="vbar"><button id="vclose">← 回總覽</button><span class="vt" id="vtitle"></span></div>
</div>
{textareas}
<script>
const TITLES = {titles_js};
const viewer = document.getElementById('viewer');
const vtitle = document.getElementById('vtitle');
let frame = null;
function openView(id, qs) {{
  const ta = document.getElementById('doc-' + id);
  if (!ta) return;
  closeView(true);
  frame = document.createElement('iframe');
  frame.name = qs || '';
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
  if (!keepHash && location.hash) history.pushState(null, '', location.pathname);
}}
document.querySelectorAll('[data-open]').forEach(b =>
  b.addEventListener('click', () => openView(b.dataset.open)));
document.getElementById('vclose').addEventListener('click', () => closeView());
window.addEventListener('message', e => {{
  const d = e.data || {{}};
  if (d.nav === 'home') closeView();
  else if (d.nav === 'backend') openView('backend');
  else if (d.nav === 'hier') openView('hier');
  else if (d.nav === 'exception') openView('exception', d.qs || '');
}});
window.addEventListener('popstate', () => {{
  const id = location.hash.slice(1);
  if (id && document.getElementById('doc-' + id)) openView(id); else closeView(true);
}});
if (location.hash) {{
  const id = location.hash.slice(1);
  if (document.getElementById('doc-' + id)) openView(id);
}}
</script>
</body></html>"""

    OUT.write_text(page, encoding="utf-8")
    print(f"OK → {OUT}  ({OUT.stat().st_size:,} bytes, views: {', '.join(docs)})")


if __name__ == "__main__":
    build()
