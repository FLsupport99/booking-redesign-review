/* Figma 文案稽核：把定稿裡的 UI 文字抓下來，逐一檢查實作有沒有用同一個字。
   會抓到的錯：可預約時段→可預約時間、上午→早上、星期二→週二、美食客→美食家 這類。
   用法：node tools/figma-copy-check.mjs [--json]
   需要 FL-Salesapp/.env 的 FIGMA_TOKEN（唯讀 PAT）。 */
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { homedir } from "node:os";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const FILE_KEY = "AQilb21aXkXybY5c1wDFq8";

/* 稽核範圍：定稿中「畫面文字最完整」的節點，一頁一個。 */
const TARGETS = [
  { id: "871:5340", name: "① 1-1 基本人數預約" },
  { id: "1064:30158", name: "① 1-3 填寫資訊" },
  { id: "1498:33396", name: "① 1-3 預約成功" },
  { id: "1023:24314", name: "① 1-2 其他分店" },
  { id: "1331:25552", name: "① 1-6 查詢預約" },
  { id: "1272:19670", name: "① 1-4 修改預約" },
  { id: "1847:18646", name: "② 1-1 服務項目預約" },
  { id: "1637:65824", name: "③ 1-1 階層項目預約" },
  { id: "1234:46579", name: "① 1-3 待審核" },
  { id: "1122:32909", name: "① 1-3a 待付款" },
  { id: "1225:43754", name: "① 1-3a 付款完成" },
  { id: "1272:18141", name: "① 1-3a 待審核+待付款" },
  { id: "1122:33308", name: "① 1-3b 待綁卡" },
  { id: "1225:43911", name: "① 1-3b 綁卡完成" },
  { id: "1023:25823", name: "① 1-1 未開放預約" },
];

/* 這些是「資料」不是 UI 文案：店家自填內容、假資料、時間數字。不列入稽核。 */
const IGNORE_PATTERNS = [
  /^[\d\s:/年月日()~－–-]+$/,          // 純數字／時間／日期
  /^NT\$/, /^\$/,                       // 金額
  /lorem ipsum/i,
  /^找活燒烤/, /^台北市/, /^02-/, /^每週/,  // 店家資料
  /^[A-Za-z@._-]+$/,                    // email／英數 id
  /^(胖寶|廖文強|答案[A-C]|大人x\d|測項|Sitemap)$/,
  /^(精緻主廚特餐|自助吧吃到飽|星空酒吧|早午時光|精緻午茶|晚安佳餚)$/, // 項目假資料
  /^(已回答問題|備註內容文字|顧客填寫答案|顧客填寫備註內容)$/,          // 表單填寫範例
  /\d+大人|\d+大\d+小/,                                              // 人數摘要（動態組字）
];
/* 已知刻意不同或本輪範圍外，附理由；有理由才准放行。 */
const ACCEPTED = {
  "English": "語言鈕在中文版顯示 EN（定稿另一張圖為 English，取較短者）",
  "答案A、答案Ｂ": "定稿全形Ｂ為筆誤，實作用半形 B",
  "填寫聯絡資訊": "定稿 1-6 內嵌的另一版標題，主線一律用「填寫預約資訊」",
};

const token = readFileSync(resolve(homedir(), "FL-Agent/FL-Salesapp/.env"), "utf8")
  .split("\n").find((l) => l.startsWith("FIGMA_TOKEN="))
  .split("=")[1].split("#")[0].trim();

/* 實作端的文案來源：模板 + 兩支 js（JS 產生的字也算）。
   另備一份「去標籤去空白」版本，這樣被 <a>、<br> 切斷的句子也比得到。 */
const raw = ["src/template.html", "js/app.js", "js/api.js"]
  .map((f) => readFileSync(resolve(ROOT, f), "utf8")).join("\n");
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

function collectText(node, out) {
  if (node.type === "TEXT" && node.characters) {
    node.characters.split("\n").map(norm).filter(Boolean).forEach((t) => out.add(t));
  }
  (node.children || []).forEach((c) => collectText(c, out));
}

const results = [];
for (const t of TARGETS) {
  const res = await fetch(`https://api.figma.com/v1/files/${FILE_KEY}/nodes?ids=${t.id}`, {
    headers: { "X-Figma-Token": token },
  }).then((r) => r.json());
  const doc = res.nodes?.[t.id]?.document;
  if (!doc) { results.push({ ...t, error: "節點讀取失敗" }); continue; }

  const texts = new Set();
  collectText(doc, texts);
  const missing = [...texts].filter((s) => {
    if (s.length > 60) return false;                       // 長內文＝店家資料
    if (IGNORE_PATTERNS.some((re) => re.test(s))) return false;
    if (ACCEPTED[s]) return false;
    return !implHas(s);
  });
  results.push({ ...t, total: texts.size, missing });
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
  }
  console.log(`\n=== ${bad === 0 ? "全部相符" : `${bad} 條與定稿不符或未實作`} ===`);
  process.exitCode = bad ? 1 : 0;
}
