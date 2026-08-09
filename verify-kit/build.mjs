/* 共用產生器：從 src/template.html 產出交付檔與逐段落檔。
   常數全部來自專案自己的 verify.config.mjs（以 cwd 為準），本檔不含任何專案設定。

   用法（在專案目錄下）：node ../verify-kit/build.mjs
   指定別的設定檔：VERIFY_CONFIG=other.config.mjs node ../verify-kit/build.mjs

   config 需提供：
     MODES        [{ key, file, label, sections? }]  交付檔；sections 未給則用全域 SECTIONS
     SECTIONS     [{ id, name }]                      逐段落檔（全域預設）
     TITLE_PREFIX string                              交付檔 <title> 前綴
*/
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const CONFIG = resolve(process.cwd(), process.env.VERIFY_CONFIG || "verify.config.mjs");
const ROOT = dirname(CONFIG);
const { MODES, SECTIONS = [], TITLE_PREFIX = "" } = await import(pathToFileURL(CONFIG).href);

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
  const out = render({
    mode: m.key,
    title: [TITLE_PREFIX, m.label].filter(Boolean).join(" "),
    label: m.label,
    depth: 0,
  });
  writeFileSync(resolve(ROOT, m.file), out);
  built.push(m.file);

  for (const { id: sec, name: secName } of (m.sections ?? SECTIONS)) {
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
