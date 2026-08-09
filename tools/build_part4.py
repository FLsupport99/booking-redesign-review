#!/usr/bin/env python3
"""把 sim.html 的 <head>（含 design token 與元件 CSS）＋ tools/part4_body.html 組成 part4.html。

sim.html 是後台模擬器的樣式來源；Part4 原型不重複維護一份 CSS，改樣式請改 sim.html 或 part4_body.html 的 <style>。
"""
import pathlib
import re

root = pathlib.Path(__file__).resolve().parent.parent
sim = (root / "sim.html").read_text(encoding="utf-8")
body = (root / "tools" / "part4_body.html").read_text(encoding="utf-8")

m = re.search(r"</style>", sim)
head = sim[: m.end()]
head = head.replace("<title>MENU店+ 後台模擬器</title>", "<title>MENU店+ Part 4 原型・A/B 兩版</title>")
head = head.replace(
    "<!-- MENU店+ 後台模擬器 · 假資料互動 Demo · 維護：FindLife Support -->",
    "<!-- MENU店+ Part 4 原型（自動排位規則／訂金管理／臨時預約關閉）· 假資料互動 Demo -->\n"
    "<!-- 由 tools/build_part4.py 產生：head 取自 sim.html、body 取自 tools/part4_body.html。不要直接改 part4.html -->",
)

out = head + "\n" + body + "\n</body>\n</html>\n"
(root / "part4.html").write_text(out, encoding="utf-8")
print("part4.html 已產生：", len(out), "chars")
