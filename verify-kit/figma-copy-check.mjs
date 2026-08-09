/* 共用文案稽核：把定稿裡的 UI 文字抓下來，逐一檢查實作有沒有用同一個字。
   會抓到的錯：可預約時段→可預約時間、上午→早上、星期二→週二、美食客→美食家 這類。

   用法（在專案目錄下）：node ../verify-kit/figma-copy-check.mjs [--json]
   需要 FL-Salesapp/.env 的 FIGMA_TOKEN（唯讀 PAT）。

   config 的 figma 需提供：
     FILE_KEY, TARGETS[{ id, name, frames? }], SOURCE_FILES, IGNORE_PATTERNS, ACCEPTED

   frames：只收集這些 frame id 底下的文字。設計稿畫布上常留有「字太多」「加底色」這類
   **設計自己的修改註記**——它們是 TEXT 節點但不屬於任何畫面，用 frame 白名單直接排除，
   比一條條寫進 IGNORE_PATTERNS 精準。不給 frames 就沿用「整個節點全抓」。
*/
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { homedir } from "node:os";

const CONFIG = resolve(process.cwd(), process.env.VERIFY_CONFIG || "verify.config.mjs");
const ROOT = dirname(CONFIG);
const { figma } = await import(pathToFileURL(CONFIG).href);
const { FILE_KEY, TARGETS, SOURCE_FILES, IGNORE_PATTERNS = [], ACCEPTED = {} } = figma;

const token = readFileSync(resolve(homedir(), "FL-Agent/FL-Salesapp/.env"), "utf8")
  .split("\n").find((l) => l.startsWith("FIGMA_TOKEN="))
  .split("=")[1].split("#")[0].trim();

/* 實作端的文案來源。另備一份「去標籤去空白」版本，這樣被 <a>、<br> 切斷的句子也比得到。 */
const raw = SOURCE_FILES.map((f) => readFileSync(resolve(ROOT, f), "utf8")).join("\n");
const stripped = raw.replace(/<[^>]+>/g, "").replace(/\s+/g, "");
/* 句中帶動態值（金額、期限、倒數）的比對：兩邊都把數字與 ${...} 拿掉再比骨架。
   例：定稿「請於2026-06-16 22:59前完成訂金付款，…」對上實作的
       `請於${b.payment.deadline}前完成訂金付款，…` */
const skeleton = (s) => s.replace(/\$\{[^}]*\}/g, "").replace(/[\d\s:/年月日.-]/g, "");
const strippedSkeleton = skeleton(raw.replace(/<[^>]+>/g, ""));
const implHas = (s) => {
  const flat = s.replace(/\s+/g, "");
  if (raw.includes(s) || stripped.includes(flat)) return true;
  return /\d/.test(s) && strippedSkeleton.includes(skeleton(s));
};

const norm = (s) => s.replace(/\s+/g, " ").trim();
const nodeId = (n) => String(n.id).replace(/-/g, ":");

function collectText(node, out) {
  if (node.type === "TEXT" && node.characters) {
    node.characters.split("\n").map(norm).filter(Boolean).forEach((t) => out.add(t));
  }
  (node.children || []).forEach((c) => collectText(c, out));
}

/* 只走進白名單 frame，進去之後整棵收 */
function collectScoped(node, out, wanted, seen) {
  if (wanted.has(nodeId(node))) {
    seen.add(nodeId(node));
    return collectText(node, out);
  }
  (node.children || []).forEach((c) => collectScoped(c, out, wanted, seen));
}

const results = [];
for (const t of TARGETS) {
  const res = await fetch(`https://api.figma.com/v1/files/${FILE_KEY}/nodes?ids=${t.id}`, {
    headers: { "X-Figma-Token": token },
  }).then((r) => r.json());
  const doc = res.nodes?.[t.id]?.document;
  if (!doc) { results.push({ ...t, error: "節點讀取失敗" }); continue; }

  const texts = new Set();
  let unseen = [];
  if (t.frames?.length) {
    const wanted = new Set(t.frames.map((f) => String(f).replace(/-/g, ":")));
    const seen = new Set();
    collectScoped(doc, texts, wanted, seen);
    unseen = [...wanted].filter((f) => !seen.has(f));
  } else {
    collectText(doc, texts);
  }

  const missing = [...texts].filter((s) => {
    if (s.length > 60) return false;                       // 長內文＝店家自填資料
    if (IGNORE_PATTERNS.some((re) => re.test(s))) return false;
    if (ACCEPTED[s]) return false;
    return !implHas(s);
  });
  results.push({ ...t, total: texts.size, missing, unseen });
}

if (process.argv.includes("--json")) {
  console.log(JSON.stringify(results, null, 1));
} else {
  let bad = 0;
  for (const r of results) {
    if (r.error) { console.log(`ERROR ${r.name}: ${r.error}`); bad++; continue; }
    const n = r.missing.length;
    bad += n;
    console.log(`${n === 0 ? "PASS" : "DIFF"}  ${r.name}  (Figma 文字 ${r.total} 條${n ? `，實作找不到 ${n} 條` : ""})`);
    r.missing.forEach((m) => console.log(`        ✗ ${JSON.stringify(m)}`));
    /* frame 白名單寫錯（節點被改 id／搬走）會讓稽核靜默漏掉整張畫面，一定要出聲 */
    if (r.unseen?.length) {
      bad += r.unseen.length;
      r.unseen.forEach((f) => console.log(`        ⚠️ frame ${f} 不在此節點內，稽核沒掃到`));
    }
  }
  console.log(`\n=== ${bad === 0 ? "全部相符" : `${bad} 條與定稿不符或未實作`} ===`);
  process.exitCode = bad ? 1 : 0;
}
