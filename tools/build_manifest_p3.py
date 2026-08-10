#!/usr/bin/env python3
"""Build manifest_p3.json from a get_metadata XML dump of the Part3 canvas."""
import json, re, sys, collections

SRC = sys.argv[1]
OUT = "manifest_p3.json"
FILE_KEY = "XphLPcM7qUdcVO6EwjYJy9"
# 尺寸門檻：原本 200×200 會把 Picker 的 Hover/Pressed（112×292）與
# 「預約項目選單_收合」（318×126）這類窄或矮的狀態圖濾掉，導致稽核靜默漏掃。
MIN_W, MIN_H = 100, 100

txt = "".join(x["text"] for x in json.load(open(SRC)))
NODE = re.compile(r'^(\s*)<(\w+) id="([^"]+)" name="([^"]+)" x="([-\d.]+)" y="([-\d.]+)" width="([\d.]+)" height="([\d.]+)"')

sections, loose = [], []
cur = None
for ln in txt.split("\n"):
    m = NODE.match(ln)
    if not m:
        continue
    ind, kind, nid, name = len(m.group(1)), m.group(2), m.group(3), m.group(4)
    x, y, w, h = (round(float(m.group(i))) for i in (5, 6, 7, 8))
    if ind == 2:
        if kind == "section":
            cur = {"id": nid, "name": name, "w": w, "h": h, "fr": []}
            sections.append(cur)
        else:
            cur = None
            if kind == "frame" and w >= MIN_W and h >= MIN_H:
                loose.append([nid, name, w, h])
    elif ind == 4 and cur is not None:
        if kind in ("frame", "instance", "component") and w >= MIN_W and h >= MIN_H:
            cur["fr"].append([nid, name, x, y, w, h])

# group by the leading "N-" of the section name; 說明 frames go to their own group
def gkey(name):
    m = re.match(r"(\d+)-", name)
    return m.group(1) if m else "x"

GROUPS = {
    "2": ("book", "① 新增／修改預約"),
    "3": ("view", "② 預約管理視圖（時間軸／空間圖／清單）"),
}
buckets = collections.OrderedDict()
for s in sorted(sections, key=lambda s: s["name"]):
    key, title = GROUPS.get(gkey(s["name"]), ("misc", "③ 其他"))
    buckets.setdefault(key, {"key": key, "title": title, "sections": [], "loose": []})["sections"].append(s)
if loose:
    buckets["note"] = {"key": "note", "title": "③ 規格說明卡", "sections": [], "loose": sorted(loose, key=lambda l: l[1])}

man = {"fileKey": FILE_KEY, "groups": list(buckets.values())}
json.dump(man, open(OUT, "w"), ensure_ascii=False)
nf = sum(len(s["fr"]) for g in man["groups"] for s in g["sections"]) + sum(len(g["loose"]) for g in man["groups"])
print(f"{OUT}: {len(man['groups'])} groups, {sum(len(g['sections']) for g in man['groups'])} sections, {nf} frames")
for g in man["groups"]:
    print(" ", g["key"], g["title"], len(g["sections"]), "sections",
          sum(len(s["fr"]) for s in g["sections"]) + len(g["loose"]), "frames")
