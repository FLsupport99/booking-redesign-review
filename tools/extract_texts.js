// 抽指定頁面每個 top-level frame 的文字層（含 placeholder 樣式資訊粗略）
const fs = require("fs"), path = require("path"), https = require("https");
const envText = fs.readFileSync(path.resolve(process.env.HOME, "FL-Agent/FL-Salesapp/.env"), "utf8");
const TOKEN = (envText.match(/^FIGMA_TOKEN=(\S+)/m) || [])[1];
const [fileKey, pageId, outPath] = process.argv.slice(2);
https.get({ hostname: "api.figma.com", path: `/v1/files/${fileKey}/nodes?ids=${encodeURIComponent(pageId)}`, headers: { "X-Figma-Token": TOKEN } }, (r) => {
  const chunks = []; r.on("data", (c) => chunks.push(c));
  r.on("end", () => {
    const doc = JSON.parse(Buffer.concat(chunks).toString()).nodes[pageId].document;
    const out = {};
    function texts(n, acc) {
      if (n.type === "TEXT" && n.characters) acc.push(n.characters.replace(/\n/g, "⏎"));
      for (const c of n.children || []) texts(c, acc);
    }
    function walk(n, topFrame) {
      if (!topFrame && n.type === "FRAME") {
        const acc = []; texts(n, acc);
        out[n.name + "|" + n.id] = acc;
        return;
      }
      for (const c of n.children || []) walk(c, topFrame);
    }
    for (const c of doc.children || []) {
      if (c.type === "SECTION") { for (const f of c.children || []) if (f.type === "FRAME") { const acc=[]; texts(f, acc); out[f.name + "|" + f.id] = acc; } }
      else if (c.type === "FRAME") { const acc=[]; texts(c, acc); out[c.name + "|" + c.id] = acc; }
    }
    fs.writeFileSync(outPath, JSON.stringify(out, null, 1));
    console.log("frames:", Object.keys(out).length);
  });
}).on("error", console.error);
