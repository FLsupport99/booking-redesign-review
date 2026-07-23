/**
 * 抽取 Figma prototype 互動連線 → proto graph JSON
 * 用法: node extract_proto.js <fileKey> <pageNodeId> <manifestPath> <groupKey> <outPath>
 * 讀 FL-Salesapp/.env 的 FIGMA_TOKEN（Ian PAT）
 */
const fs = require("fs");
const path = require("path");
const https = require("https");
const envText = fs.readFileSync(path.resolve(process.env.HOME, "FL-Agent/FL-Salesapp/.env"), "utf8");
process.env.FIGMA_TOKEN = (envText.match(/^FIGMA_TOKEN=(\S+)/m) || [])[1];

const [fileKey, pageId, manifestPath, groupKey, outPath] = process.argv.slice(2);

function get(p) {
  return new Promise((res, rej) => {
    https.get({ hostname: "api.figma.com", path: p, headers: { "X-Figma-Token": process.env.FIGMA_TOKEN } }, (r) => {
      const chunks = [];
      r.on("data", (c) => chunks.push(c));
      r.on("end", () => res({ s: r.statusCode, d: Buffer.concat(chunks).toString("utf8") }));
    }).on("error", rej);
  });
}

(async () => {
  const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  const group = manifest.groups.find((g) => g.key === groupKey);
  if (!group) throw new Error("group not found: " + groupKey);

  // 已有 PNG 的畫面集合（section frames + loose）
  const screens = new Map(); // id -> {id,name,w,h}
  for (const s of group.sections) for (const [id, name, x, y, w, h] of s.fr) screens.set(id, { id, name, w, h, sec: s.name });
  for (const [id, name, w, h] of group.loose) screens.set(id, { id, name, w, h, sec: "其他" });

  const resp = await get(`/v1/files/${fileKey}/nodes?ids=${encodeURIComponent(pageId)}`);
  if (resp.s !== 200) throw new Error("fetch failed " + resp.s);
  const doc = JSON.parse(resp.d).nodes[pageId].document;

  // 走訪：記每個 screen frame 的 absBox；收集互動節點
  const absBox = new Map(); // screenId -> {x,y,w,h}
  const hotspots = []; // {screenId, x,y,w,h(%), target, trigger}
  const stats = { nodesWithInteractions: 0, kept: 0, droppedUnknownTarget: {}, backActions: 0 };

  function destOf(node) {
    const out = []; // {target, trigger, action}
    if (Array.isArray(node.interactions)) {
      for (const it of node.interactions) {
        const trig = it.trigger && it.trigger.type;
        for (const a of it.actions || []) {
          if (a.type === "NODE" && a.destinationId) out.push({ target: a.destinationId, trigger: trig, nav: a.navigation });
          if (a.type === "BACK" || (a.type === "NODE" && a.navigation === "BACK")) out.push({ target: "__BACK__", trigger: trig, nav: "BACK" });
        }
      }
    }
    if (node.transitionNodeID) out.push({ target: node.transitionNodeID, trigger: "ON_CLICK", nav: "NAVIGATE" });
    return out;
  }

  function walk(node, screen) {
    const bb = node.absoluteBoundingBox;
    if (screens.has(node.id)) {
      screen = node.id;
      if (bb) absBox.set(node.id, bb);
    }
    const dests = destOf(node);
    if (dests.length) stats.nodesWithInteractions++;
    if (screen && bb && dests.length && node.id !== screen) {
      for (const d of dests) {
        if (d.target === "__BACK__") { stats.backActions++; hotspots.push({ screen, bb, target: "__BACK__", trigger: d.trigger }); continue; }
        if (screens.has(d.target)) { hotspots.push({ screen, bb, target: d.target, trigger: d.trigger }); }
        else stats.droppedUnknownTarget[d.target] = (stats.droppedUnknownTarget[d.target] || 0) + 1;
      }
    }
    for (const c of node.children || []) walk(c, screen);
  }
  walk(doc, null);

  // 正規化為百分比座標
  const out = { fileKey, page: pageId, group: groupKey, screens: [], start: null };
  const linkCount = new Map();
  for (const h of hotspots) linkCount.set(h.screen, (linkCount.get(h.screen) || 0) + 1);
  for (const [id, sc] of screens) {
    const box = absBox.get(id);
    if (!box) continue; // 不在此頁（不同 page 的 loose）
    const hs = hotspots
      .filter((h) => h.screen === id)
      .map((h) => ({
        x: +(((h.bb.x - box.x) / box.width) * 100).toFixed(3),
        y: +(((h.bb.y - box.y) / box.height) * 100).toFixed(3),
        w: +((h.bb.width / box.width) * 100).toFixed(3),
        h: +((h.bb.height / box.height) * 100).toFixed(3),
        t: h.target, tr: h.trigger || "ON_CLICK",
      }))
      .filter((h) => h.x >= -1 && h.y >= -1 && h.x < 100 && h.y < 100);
    out.screens.push({ id, name: sc.name, sec: sc.sec, w: sc.w, h: sc.h, hs });
  }
  stats.kept = out.screens.reduce((a, s) => a + s.hs.length, 0);
  // start: 名稱含 Start 的第一張，否則第一張
  const st = out.screens.find((s) => /Start/.test(s.name)) || out.screens[0];
  out.start = st && st.id;

  fs.writeFileSync(outPath, JSON.stringify(out, null, 0));
  console.log(JSON.stringify({
    screens: out.screens.length,
    withHotspots: out.screens.filter((s) => s.hs.length).length,
    hotspotsKept: stats.kept,
    nodesWithInteractions: stats.nodesWithInteractions,
    backActions: stats.backActions,
    droppedTargets: Object.keys(stats.droppedUnknownTarget).length,
    start: out.start,
  }, null, 1));
})();
