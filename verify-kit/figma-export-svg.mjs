/* 共用圖示匯出：從 Figma REST 批次抓 SVG，寫到專案的 assets/。
   走 REST 而不是 MCP：MCP 有每日額度且不適合批次匯圖。

   用法（在專案目錄下）：node ../verify-kit/figma-export-svg.mjs
   需要 FL-Salesapp/.env 的 FIGMA_TOKEN（唯讀 PAT）。

   config 需提供：
     figma.FILE_KEY
     figma.ICONS  { "檔名": "節點id", ... }   → assets/<檔名>.svg

   預設**不改色**：Figma 已經把 active/inactive 的顏色烘進 SVG，直接用最忠實。

   ⚠️ 只有在你會把 SVG **inline 進 HTML** 時才設 figma.ICONS_CURRENT_COLOR = true。
      透過 <img> 載入的 SVG 無法繼承頁面的 color，currentColor 會解析成預設值；
      帶 <mask fill="white"> 的圖示會因此整張變透明（踩過：顧客／設定兩個圖示消失）。
*/
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { homedir } from "node:os";

const CONFIG = resolve(process.cwd(), process.env.VERIFY_CONFIG || "verify.config.mjs");
const ROOT = dirname(CONFIG);
const { figma } = await import(pathToFileURL(CONFIG).href);
const { FILE_KEY, ICONS, ICONS_CURRENT_COLOR = false } = figma;

if (!ICONS || !Object.keys(ICONS).length) {
  console.log("config 沒有 figma.ICONS，沒有東西要匯出。");
  process.exit(0);
}

const token = readFileSync(resolve(homedir(), "FL-Agent/FL-Salesapp/.env"), "utf8")
  .split("\n").find((l) => l.startsWith("FIGMA_TOKEN="))
  .split("=")[1].split("#")[0].trim();

const names = Object.keys(ICONS);
const ids = names.map((n) => ICONS[n]);

const res = await fetch(
  `https://api.figma.com/v1/images/${FILE_KEY}?ids=${encodeURIComponent(ids.join(","))}&format=svg`,
  { headers: { "X-Figma-Token": token } },
).then((r) => r.json());

if (res.err) { console.error("Figma 匯出失敗：", res.err); process.exit(1); }

mkdirSync(resolve(ROOT, "assets"), { recursive: true });

/* 實色 → currentColor（opt-in，見檔頭警告）。mask 的 fill 一律不動。 */
const recolor = (svg) => (!ICONS_CURRENT_COLOR ? svg : svg
  .replace(/(fill|stroke)="(#[0-9a-fA-F]{3,8}|white|black)"/g, (m, a, c, off) =>
    /<mask[^>]*$/.test(svg.slice(0, off)) ? m : `${a}="currentColor"`));

let ok = 0, fail = [];
for (const name of names) {
  const url = res.images?.[ICONS[name]];
  if (!url) { fail.push(`${name}（${ICONS[name]}）：Figma 沒回圖`); continue; }
  const svg = await fetch(url).then((r) => r.text());
  writeFileSync(resolve(ROOT, `assets/${name}.svg`), recolor(svg));
  ok++;
}

console.log(`匯出 ${ok}/${names.length} 個 SVG → assets/`);
fail.forEach((f) => console.log("  ✗ " + f));
process.exitCode = fail.length ? 1 : 0;
