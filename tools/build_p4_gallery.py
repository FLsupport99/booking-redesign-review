#!/usr/bin/env python3
"""產生 src/galleries/p4_gallery.html — Part 4 定稿設計稿總覽。

來源：p4_assets/manifest.json（build 於 2026-09-01，跨兩個 Figma 檔，
`files[]` 依 canvas → section 分組；圖檔為逐 frame REST 匯出、margin 0）。
視覺體系直接沿用 p3_gallery.html 的 <style>（同一套 gallery CSS），
lightbox 同款。手機稿（_M 後綴或寬 ≤430）標「手機」badge。
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "p4_assets" / "manifest.json"
P3 = ROOT / "src" / "galleries" / "p3_gallery.html"
OUT = ROOT / "src" / "galleries" / "p4_gallery.html"


def main():
    man = json.loads(MANIFEST.read_text())
    style = re.search(r"<style>.*?</style>", P3.read_text(), re.S).group(0)

    nav, mains, total = [], [], 0
    for f in man["files"]:
        gh = f["title"]
        nav.append(f'<div class="ngh">{gh}</div>')
        mains.append(f'<h2 class="gh">{gh}</h2>')
        for sec_name, frames in f["sections"].items():
            sid = "s-" + re.sub(r"\W+", "_", sec_name)
            nav.append(f'<a href="#{sid}">{sec_name} <span>{len(frames)}</span></a>')
            cards = []
            for nid, fr in frames.items():
                fn = "p4_assets/" + nid.replace(":", "_") + ".png"
                mobile = fr["name"].endswith("_M") or fr["w"] <= 430
                badge = "手機" if mobile else "桌面"
                klass = "card mob" if mobile else "card desk"
                cards.append(
                    f'<figure class="{klass}"><div class="imwrap">'
                    f'<img loading="lazy" src="{fn}" alt="{fr["name"]}"></div>'
                    f'<figcaption><span class="badge">{badge}</span>{fr["name"]}</figcaption></figure>'
                )
                total += 1
            mains.append(
                f'<section id="{sid}" class="sec"><h3 class="sh">{sec_name} '
                f'<em>{len(frames)} 張</em></h3><div class="grid">\n'
                + "\n".join(cards) + "\n</div></section>"
            )

    html = f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Part 4 定稿 — 設計稿總覽</title>
{style}</head><body>
<header class="top"><h1>Part 4 定稿 — 設計稿總覽</h1><span class="meta">共 {total} 張 · 2026 Aug. 臨時關閉預約單位＋自訂排位順序／多組訂金規則管理 · 照 Figma 原稿渲染</span>
<a class="link" href="index.html">← 回入口</a></header>
<div class="wrap">
<nav class="side">{''.join(nav)}</nav>
<main>
{''.join(mains)}
</main>
</div>
<div id="lb" onclick="this.classList.remove('on')"><img id="lbimg" src=""></div>
<script>
document.querySelectorAll('.card img').forEach(function(im){{
  im.addEventListener('click',function(e){{e.stopPropagation();var lb=document.getElementById('lb');document.getElementById('lbimg').src=im.src;lb.classList.add('on');}});
}});
</script>
</body></html>"""
    OUT.write_text(html, encoding="utf-8")
    print(f"OK → {OUT}  ({total} 張, {OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
