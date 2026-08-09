/* 從 src/template.html 產出：
     根目錄 3 個模式檔（交付物）
     sections/ 21 個單段落檔（1-1 ~ 1-7 × 3 模式，用於逐段比對）
   用法：node tools/build.mjs
*/
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { MODES, SECTIONS } from "../verify.config.mjs";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const TPL = readFileSync(resolve(ROOT, "src/template.html"), "utf8");

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

  for (const { id: sec, name: secName } of SECTIONS) {
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
