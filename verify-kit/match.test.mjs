/* 文案比對的回歸測試。用法：node verify-kit/match.test.mjs
   不需要 Figma API，秒級。

   為什麼要有這份：這關真正的風險不是漏抓，是為了讓它變綠而一步步放寬。
   下面「必須抓到」那一組，每一條都是 Part 2 真的踩過的錯字類型。
   任何對比對邏輯的放寬，都必須讓那組維持紅色。

   ⚠️ 已知限制：字面值若被包在**另一層** ${} 裡（`${cond ? `文字${x}` : ""}`），
      括號平衡移除會把整段吃掉，工具看不到那段文字。解法是把它抽成獨立 helper
      函式——那本來也是比較好的寫法。實作端已經這樣做（見 app.js 的 stayedLine）。 */
import { createMatcher } from "./match.mjs";

/* 模擬實作端原始碼：含 HTML 標籤、樣板字串、巢狀 ${}、跨行 */
const SOURCE_HTML = `
<p class="t-h4">可預約時段</p>
<span>上午</span><span>星期二</span>
<p>MENU美食客分享</p>
<p>請於預約時段準時到達，逾時10分鐘將取消訂位</p>
<p class="slot-head">組數：\${s.groups}</p>
<p>人數：\${s.people}</p>
`;

/* JS 來源：故意包含 < 與 => ，驗證去標籤沒有被誤用在 JS 上 */
const SOURCE_JS = `
if (names.length < 2) warn.hidden = true;
const fmt = (n) => n + "人";
const item = "預約項目的字數最多有十四個字", subItem = "子項目名稱";
const source = "線上";
const units = ["單位D4", "E2"]; warn = \`已選取 \${names} 尚有顧客或即將有預約\`;
html = \`\${b.item}/\${b.subItem}\`;
html = \`\${b.source} ｜ 最後更新: \${b.updatedAt} ｜ 建立: \${b.createdAt} ｜ 預約代碼: \${b.code}\`;
function stayedLine(b){ return \`<p>累計時間：\${h}小時\${m}分鐘</p>\`; }
trace = \`\${t.seated}入座 - \${t.finished}完成\`;
notice = "請於\${deadline}前完成訂金付款，逾時系統將自動取消預約。";
`;

/* 分成 .html 與 .js 兩份：去標籤只能對 HTML 做，這也是回歸測試要涵蓋的 */
const has = createMatcher([
  { path: "src/template.html", text: SOURCE_HTML },
  { path: "js/app.js", text: SOURCE_JS },
]);

/* 這些**必須通過**：定稿是一個 text node，實作由多個欄位組合而成 */
const MUST_PASS = [
  ["可預約時段", "原文直接命中"],
  ["請於預約時段準時到達，逾時10分鐘將取消訂位", "整句命中"],
  ["組數：2", "值＋標籤（骨架）"],
  ["人數：375", "值＋標籤（骨架）"],
  ["預約項目的字數最多有十四個字/子項目名稱", "兩個欄位組合（分段組裝）"],
  ["線上｜最後更新: 2019-06-21 12:18 ｜", "來源＋時間戳組合，定稿在此換 text node"],
  ["累計時間：2小時28分鐘", "組字（實作已抽成 helper，不是巢狀 ${}）"],
  ["02:17入座", "值＋2 字標籤"],
  ["已選取 單位D4、E2 尚有顧客或即將有預約", "中段是分隔符號串起來的清單，每個元素都有證據"],
  ["請於2026-06-16 22:59前完成訂金付款，逾時系統將自動取消預約。", "句中夾動態值"],
];

/* 這些**必須被抓到**：Part 2 真的踩過的錯字類型。放寬比對時這組會先紅。 */
const MUST_FAIL = [
  ["可預約時間", "單字替換：段→間"],
  ["早上", "2 字整詞替換：上午→早上"],
  ["MENU美食家分享", "單字替換：客→家"],
  ["週二", "2 字整詞替換：星期二→週二"],
  ["請選擇時間", "整句未實作"],
  ["組數：2 人數：375 尚未實作的句子", "拼湊不出來的長句"],
  ["交換", "2 字功能未實作"],
  ["名稱後面被吃掉的字", "去標籤若誤用在 JS 上，這種夾在 < 與 => 之間的字會假性通過"],
  ["已選取 單位X9、Z1 尚有顧客或即將有預約", "清單元素在實作裡不存在，不能因為句型像就放行"],
];

let failed = 0;
console.log("── 必須通過 ──");
for (const [s, why] of MUST_PASS) {
  const ok = has(s);
  if (!ok) failed++;
  console.log(`${ok ? "  ✓" : "  ✗ 應通過卻沒過"}  ${JSON.stringify(s)}  （${why}）`);
}
console.log("── 必須被抓到 ──");
for (const [s, why] of MUST_FAIL) {
  const caught = !has(s);
  if (!caught) failed++;
  console.log(`${caught ? "  ✓" : "  ✗ 放水了！"}  ${JSON.stringify(s)}  （${why}）`);
}

console.log(`\n=== ${failed === 0 ? "比對邏輯正常" : `${failed} 條不符預期`} ===`);
process.exitCode = failed ? 1 : 0;
