#!/usr/bin/env python3
"""Crop Figma section exports into per-frame PNGs and generate gallery HTML pages.

Inputs (scratchpad):
  manifest_modes.json / manifest_algo.json  — section/frame inventory with coords
  exports/sections/<id>.png                 — section-level exports (scale 1 or 0.5)
  exports/loose/<id>.png                    — loose frame exports

Outputs (site repo):
  <site>/modes_assets/*.png + manifest.json
  <site>/algo_assets/*.png  + manifest.json
  <site>/modes_gallery.html, <site>/algo_gallery.html
"""
import json, os, sys, datetime
from PIL import Image

Image.MAX_IMAGE_PIXELS = None  # sections up to 107 MP

SCRATCH = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.expanduser("~/FL-Agent/booking-redesign-site")

PAGES = [
    {
        "manifest": "manifest_modes.json",
        "html": "modes_gallery.html",
        "assets": "modes_assets",
        "title": "服務項目＋階層項目預約 — 設計稿總覽",
        "subtitle": "2026 May. 顧客預約頁改版（頁②③）· 照 Figma 原稿渲染",
    },
    {
        "manifest": "manifest_algo.json",
        "html": "algo_gallery.html",
        "assets": "algo_assets",
        "title": "演算法改版・後台設定 — 設計稿總覽",
        "subtitle": "2025 Oct. 系統架構演算法優化 · 照 Figma 原稿渲染",
    },
]

CSS = """  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:"PingFang TC","Noto Sans TC",sans-serif;color:#222;background:#f4f5f6}
  header.top{position:sticky;top:0;z-index:10;background:#fff;border-bottom:1px solid #e5e5e5;padding:14px 24px;display:flex;align-items:center;gap:14px}
  header.top h1{font-size:17px;font-weight:600}
  header.top .meta{font-size:13px;color:#888}
  header.top .link{margin-left:auto;font-size:13px;color:#29A379;text-decoration:none;border:1px solid #3FBA88;border-radius:100px;padding:6px 14px}
  .wrap{display:flex;align-items:flex-start}
  nav.side{position:sticky;top:56px;width:250px;flex:0 0 250px;height:calc(100vh - 56px);overflow:auto;padding:16px 10px;background:#fff;border-right:1px solid #e5e5e5}
  nav.side .ngh{font-size:12px;font-weight:700;color:#29A379;padding:12px 12px 4px;letter-spacing:.5px}
  nav.side a{display:flex;justify-content:space-between;gap:8px;font-size:13px;color:#444;text-decoration:none;padding:7px 12px;border-radius:8px}
  nav.side a:hover{background:#f0f7f3}
  nav.side a span{color:#aaa;font-size:12px}
  main{flex:1;min-width:0;padding:22px 28px 80px}
  .gh{font-size:15px;font-weight:700;color:#29A379;margin:26px 0 6px;letter-spacing:.5px}
  .sec{margin-bottom:14px}
  .sh{font-size:16px;font-weight:600;margin:18px 0 12px;padding-bottom:8px;border-bottom:1px solid #e5e5e5}
  .sh em{font-style:normal;font-size:12px;color:#999;font-weight:400;margin-left:8px}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:18px}
  .card{background:#fff;border:1px solid #e5e5e5;border-radius:10px;overflow:hidden;cursor:zoom-in}
  .card .imwrap{background:#fafafa;max-height:420px;overflow:auto;display:flex;justify-content:center}
  .card img{width:100%;height:auto;display:block}
  .card.mob .imwrap{padding:10px}
  .card.mob img{max-width:230px;margin:0 auto}
  figcaption{font-size:12px;color:#555;padding:9px 11px;display:flex;align-items:center;gap:7px;border-top:1px solid #eee;line-height:1.4}
  .badge{flex:0 0 auto;font-size:10px;color:#fff;background:#9aa;border-radius:4px;padding:2px 6px}
  .card.mob .badge{background:#E4924B}
  .card.desk .badge{background:#5B8DEF}
  #lb{display:none;position:fixed;inset:0;background:rgba(0,0,0,.85);z-index:99;align-items:flex-start;justify-content:center;overflow:auto;padding:30px;cursor:zoom-out}
  #lb.on{display:flex}
  #lb img{max-width:1024px;width:100%;height:auto;border-radius:6px}"""


def anchor(sec_id):
    return "s-" + sec_id.replace(":", "_")


MARGIN = 40  # get_screenshot renders sections/frames with a 40px margin on each side


def render_geometry(im_w, node_w):
    """Return (scale, offset) for a rendered PNG vs the node's natural width."""
    if abs(im_w - (node_w + 2 * MARGIN)) <= 3:
        return 1.0, MARGIN
    if abs(im_w - node_w) <= 3:
        return 1.0, 0
    r = im_w / (node_w + 2 * MARGIN)
    return r, MARGIN * r


def crop_sections(manifest, assets_dir, report):
    for g in manifest["groups"]:
        for s in g["sections"]:
            src = os.path.join(SCRATCH, "exports2", "sections", s["id"].replace(":", "_") + ".png")
            if not os.path.exists(src):
                report["missing_sections"].append((g["key"], s["id"], s["name"]))
                continue
            im = Image.open(src)
            r, off = render_geometry(im.width, s["w"])
            if abs(r - 1.0) > 0.02:
                report["scaled"].append((s["id"], round(r, 3)))
            for fid, name, x, y, w, h in s["fr"]:
                out = os.path.join(assets_dir, fid.replace(":", "_") + ".png")
                box = (round(x * r + off), round(y * r + off), round((x + w) * r + off), round((y + h) * r + off))
                box = (max(0, box[0]), max(0, box[1]), min(im.width, box[2]), min(im.height, box[3]))
                if box[2] <= box[0] or box[3] <= box[1]:
                    report["bad_crops"].append((s["id"], fid, name))
                    continue
                im.crop(box).save(out, optimize=True)
            im.close()


def copy_loose(manifest, assets_dir, report):
    for g in manifest["groups"]:
        for l in g["loose"]:
            fid, w, h = l[0], l[2], l[3]
            src = os.path.join(SCRATCH, "exports2", "loose", fid.replace(":", "_") + ".png")
            out = os.path.join(assets_dir, fid.replace(":", "_") + ".png")
            if not os.path.exists(src):
                report["missing_loose"].append((g["key"], fid, l[1]))
                continue
            im = Image.open(src)
            r, off = render_geometry(im.width, w)
            if off:
                im = im.crop((round(off), round(off), round(off + w * r), round(off + h * r)))
            im.save(out, optimize=True)


def fig_html(assets, fid, name, w):
    cls = "mob" if w <= 500 else "desk"
    badge = "手機" if cls == "mob" else "桌面"
    fn = fid.replace(":", "_") + ".png"
    return (f'<figure class="card {cls}"><div class="imwrap"><img loading="lazy" src="{assets}/{fn}" alt="{name}"></div>'
            f'<figcaption><span class="badge">{badge}</span>{name}</figcaption></figure>')


def build_page(page):
    manifest = json.load(open(os.path.join(SCRATCH, page["manifest"])))
    assets_dir = os.path.join(SITE, page["assets"])
    os.makedirs(assets_dir, exist_ok=True)
    report = {"missing_sections": [], "missing_loose": [], "bad_crops": [], "scaled": []}

    crop_sections(manifest, assets_dir, report)
    copy_loose(manifest, assets_dir, report)

    nav, body, total = [], [], 0
    for g in manifest["groups"]:
        multi = len(manifest["groups"]) > 1
        if multi:
            nav.append(f'<div class="ngh">{g["title"]}</div>')
            body.append(f'<h2 class="gh">{g["title"]}</h2>')
        for s in g["sections"]:
            present = [f for f in s["fr"] if os.path.exists(os.path.join(assets_dir, f[0].replace(":", "_") + ".png"))]
            if not present:
                continue
            # desktop first, then mobile, preserving manifest order within each
            ordered = [f for f in present if f[4] > 500] + [f for f in present if f[4] <= 500]
            aid = anchor(s["id"])
            nav.append(f'<a href="#{aid}">{s["name"]} <span>{len(ordered)}</span></a>')
            cards = "\n".join(fig_html(page["assets"], f[0], f[1], f[4]) for f in ordered)
            body.append(f'<section id="{aid}" class="sec"><h3 class="sh">{s["name"]} <em>{len(ordered)} 張</em></h3><div class="grid">\n{cards}\n</div></section>')
            total += len(ordered)
        loose_present = [l for l in g["loose"] if os.path.exists(os.path.join(assets_dir, l[0].replace(":", "_") + ".png"))]
        if loose_present:
            aid = f's-{g["key"]}-notes'
            nav.append(f'<a href="#{aid}">📋 說明卡與其他 <span>{len(loose_present)}</span></a>')
            cards = "\n".join(fig_html(page["assets"], l[0], l[1], l[2]) for l in loose_present)
            body.append(f'<section id="{aid}" class="sec"><h3 class="sh">📋 說明卡與其他 <em>{len(loose_present)} 張</em></h3><div class="grid">\n{cards}\n</div></section>')
            total += len(loose_present)

    html = f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{page["title"]}</title>
<style>
{CSS}
</style></head><body>
<header class="top"><h1>{page["title"]}</h1><span class="meta">共 {total} 張 · {page["subtitle"]}</span>
<a class="link" href="index.html">← 回入口</a></header>
<div class="wrap">
<nav class="side">{"".join(nav)}</nav>
<main>
{chr(10).join(body)}
</main>
</div>
<div id="lb" onclick="this.classList.remove('on')"><img id="lbimg" src=""></div>
<script>
document.querySelectorAll('.card img').forEach(function(im){{
  im.addEventListener('click',function(e){{e.stopPropagation();var lb=document.getElementById('lb');document.getElementById('lbimg').src=im.src;lb.classList.add('on');}});
}});
</script>
</body></html>"""
    open(os.path.join(SITE, page["html"]), "w").write(html)

    # asset manifest for future incremental updates
    am = {"generated": datetime.date.today().isoformat(), "fileKey": manifest["fileKey"], "frames": {}}
    for g in manifest["groups"]:
        for s in g["sections"]:
            for f in s["fr"]:
                am["frames"][f[0]] = f[1]
        for l in g["loose"]:
            am["frames"][l[0]] = l[1]
    json.dump(am, open(os.path.join(assets_dir, "manifest.json"), "w"), ensure_ascii=False, indent=1)
    return page["html"], total, report


if __name__ == "__main__":
    for page in PAGES:
        name, total, rep = build_page(page)
        print(f"== {name}: {total} 張")
        for k, v in rep.items():
            if v:
                print(f"   {k}: {v if len(v) <= 8 else str(v[:8]) + f' …(+{len(v)-8})'}")
