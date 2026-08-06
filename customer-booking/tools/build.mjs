/* 從 src/template.html 產出：
     根目錄 3 個模式檔（交付物）
     sections/ 21 個單段落檔（1-1 ~ 1-7 × 3 模式，用於逐段比對）
   用法：node tools/build.mjs
*/
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const TPL = readFileSync(resolve(ROOT, "src/template.html"), "utf8");

const MODES = [
  { key: "basic", file: "1-基本人數預約.html", label: "① 基本人數預約" },
  { key: "service", file: "2-服務項目預約.html", label: "② 服務項目預約" },
  { key: "hier", file: "3-階層項目預約.html", label: "③ 階層項目預約" },
];

const SECTIONS = [
  ["1-1", "顧客預約頁"],
  ["1-2", "查看其他分店時段"],
  ["1-3", "填寫資訊"],
  ["1-4", "修改預約"],
  ["1-5", "取消預約"],
  ["1-6", "查詢預約"],
  ["1-7", "中英切換"],
];

function render({ mode, title, label, section, depth }) {
  let html = TPL
    .replace("__TITLE__", title)
    .replace("__MODE__", mode)
    .replace("__LABEL__", label)
    .replace("__SECTION__", section ? ` window.SECTION = "${section}";` : "");
  if (depth > 0) {
    const up = "../".repeat(depth);
    html = html
      .replace(/(href|src)="(css|js|assets)\//g, `$1="${up}$2/`)
      .replace("<script>window.MODE", `<script>window.ASSET_BASE = "${up}";\nwindow.MODE`);
  }
  return html;
}

mkdirSync(resolve(ROOT, "sections"), { recursive: true });
const built = [];

for (const m of MODES) {
  const out = render({ mode: m.key, title: `顧客預約頁 ${m.label}`, label: m.label, depth: 0 });
  writeFileSync(resolve(ROOT, m.file), out);
  built.push(m.file);

  for (const [sec, secName] of SECTIONS) {
    const file = `sections/${m.key}-${sec}.html`;
    writeFileSync(resolve(ROOT, file), render({
      mode: m.key,
      title: `${m.label} ${sec} ${secName}`,
      label: `${m.label} ${sec} ${secName}`,
      section: sec,
      depth: 1,
    }));
    built.push(file);
  }
}

console.log(`built ${built.length} files:\n` + built.map((f) => "  " + f).join("\n"));
